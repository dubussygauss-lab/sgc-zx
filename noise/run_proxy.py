"""Provisional noisy-fidelity proxy for families A and B1.

Parses the compiled hqslib1 QASM files in results/compiled/<pipeline>/ into
dm_sim gate tuples, verifies the parser against compile.probs_from_measured_qasm
and the bench/family_A/*.npy references, then runs the density-matrix noise
proxy for every circuit with n <= 8 and writes a CSV, a fit of F_H against
gate counts, and a figure.

Noise sets (--noise)
  typical  H2 data-sheet typical values (h2_params.H2_TYPICAL), symmetric
           SPAM, p_idle = 0 and a second p_idle = 5e-4 column set (F_H_idle)
           -> results/family_A_proxy.csv, fig_proxy_fidelity_vs_n2q.{pdf,png}
  h22e     H2-2E emulator defaults (h2_params.H2_2E_EMULATOR): p1, p2,
           asymmetric readout p_meas_0 / p_meas_1, p_init; p_idle = 0 only
           (no gate-duration model, see dm_sim docstring)
           -> results/family_<fam>_proxy_h22e.csv ; the three-panel figure
           results/fig_proxy_h22e.{pdf,png} is made with --figure-h22e from
           both CSVs.

Families (--family)
  A   bench/family_A, n <= 8 (108 circuits); the ideal reference is the
      bench/family_A/<stem>.npy distribution of the circuit as written.
  B1  bench/family_B1/manifest.csv, n <= 8 (7 circuits).  B1 has no .npy
      references: the ideal reference is the NOISE-FREE dm_sim distribution of
      the P0ref compilation of the same circuit (through its measure map), and
      every pipeline's noise-free distribution is checked against it
      (ideal_vs_ref_maxdiff).  So for B1 "F_H" is fidelity to the P0ref
      noise-free output, which equals the circuit's ideal output only if P0ref
      is correct (checked separately by pipelines/run_family_B1.py check_dev).

support_size = number of bitstrings with reference probability > 1e-12.

hqslib1 conventions (pytket 2.18.4, pytket/qasm/qasm.py)
--------------------------------------------------------
Writer `_make_params_str` emits every parameter p (pytket half-turns) as the
literal "p*pi", so the QASM angle is in RADIANS and half-turns = angle/pi
(the reader divides by pi again: "({par})/pi").  Gate names (NOQASM_COMMANDS /
PARAM_COMMANDS): "U1q" -> PhasedX(a, b), "RZZ" -> ZZPhase(a), "ZZ" -> ZZMax,
"rz"/"Rz" -> Rz(a).  "measure q[j] -> c[i]" sends the physical wire j to
classical bit i, which encodes the implicit qubit permutation left by
allow_swaps=True (compile.add_measure_all).

Usage: python noise/run_proxy.py [--workers N] [--verify-only] [--from-csv]
                                 [--noise typical|h22e] [--family A|B1]
                                 [--figure-h22e]
"""

import argparse
import csv
import math
import os
import re
import sys
import time
from multiprocessing import Pool

# One BLAS thread per process: the (2,)*16 tensordots are tiny and OpenBLAS
# thread spawning made each gate ~25x slower on a shared 2-core box.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "noise"))
sys.path.insert(0, os.path.join(ROOT, "pipelines"))

import dm_sim  # noqa: E402
from dm_sim import NoiseModel, hellinger_fidelity, total_variation  # noqa: E402
from h2_params import H2_TYPICAL, H2_2E_EMULATOR  # noqa: E402

PIPELINES = ["P0ref", "P0", "P1", "P2", "P3"]
MAX_N = 8
COMPILED = os.path.join(ROOT, "results", "compiled")
BENCH = os.path.join(ROOT, "bench", "family_A")
BENCH_B1 = os.path.join(ROOT, "bench", "family_B1")
RESULTS = os.path.join(ROOT, "results")
OUT_CSV = os.path.join(RESULTS, "family_A_proxy.csv")
OUT_FIG = os.path.join(RESULTS, "fig_proxy_fidelity_vs_n2q")
OUT_FIG_H22E = os.path.join(RESULTS, "fig_proxy_h22e")
SUPPORT_TOL = 1e-12

# Noise settings.  p_idle = 0 is the data-sheet reading; the second setting
# (p_idle = 5e-4 per ASAP layer) is an ASSUMPTION: the data sheet quotes the
# memory error per reference time, not per circuit layer.
NOISE_A = dict(p1=H2_TYPICAL["p1"], p2=H2_TYPICAL["p2"], p_spam=H2_TYPICAL["p_spam"],
               p_idle=0.0, rz_virtual=True)
NOISE_B = dict(NOISE_A, p_idle=H2_TYPICAL["p_memory"])
# H2-2E emulator defaults; p_idle = 0 (no duration model for the dephasing rates)
NOISE_H22E = dict(p1=H2_2E_EMULATOR["p1"], p2=H2_2E_EMULATOR["p2"],
                  p_meas_0=H2_2E_EMULATOR["p_meas_0"], p_meas_1=H2_2E_EMULATOR["p_meas_1"],
                  p_init=H2_2E_EMULATOR["p_init"], p_idle=0.0, rz_virtual=True)
NOISE_SETS = {"typical": NOISE_A, "h22e": NOISE_H22E}

# run configuration (set by main and passed in every job tuple to the pool workers)
CFG = {"noise": "typical", "family": "A"}

_NAME = re.compile(r"^(?P<model>[a-z]+)_n(?P<n>\d+)_r(?P<r>\d+)_(?P<dis>[a-z]+)_s(?P<s>\d+)\.qasm$")


# ------------------------------------------------------------------ parser

def parse_hqslib1(text):
    """hqslib1 QASM (as written by pytket) -> (gates, n, bit_of).

    gates: dm_sim tuples with half-turn angles; bit_of: {qubit j: classical
    bit i} from `measure q[j] -> c[i]`.  Angles in the file are radians
    ("x*pi"); they are divided by pi."""
    gates, n, bit_of = [], 0, {}
    body = re.sub(r"//.*", "", text)
    for stmt in body.split(";"):
        s = stmt.strip()
        if not s or s.startswith("OPENQASM") or s.startswith("include"):
            continue
        m = re.match(r"^(\w+)\s*(\(([^)]*)\))?\s*(.*)$", s, re.S)
        if not m:
            raise ValueError("cannot parse %r" % s)
        op, params, args = m.group(1), m.group(3), m.group(4)
        if op == "qreg":
            n = int(dm_sim._ARG.match(args).group(2))
            continue
        if op in ("creg", "barrier"):
            continue
        if op == "measure":
            left, right = [t.strip() for t in args.split("->")]
            q = dm_sim._qidx(left)
            bit_of[q] = dm_sim._qidx(right)
            gates.append(("Measure", q))
            continue
        qs = [dm_sim._qidx(t) for t in args.split(",")]
        ps = [dm_sim._eval_angle(p) / math.pi for p in params.split(",")] if params else []
        if op in ("rz", "Rz"):
            gates.append(("Rz", qs[0], ps[0]))
        elif op == "U1q":
            gates.append(("PhasedX", qs[0], ps[0], ps[1]))
        elif op == "RZZ":
            gates.append(("ZZPhase", qs[0], qs[1], ps[0]))
        elif op == "ZZ":
            gates.append(("ZZMax", qs[0], qs[1]))
        else:
            raise ValueError("unsupported hqslib1 op %r" % op)
    if n == 0:
        n = dm_sim.infer_n(gates)
    return gates, n, bit_of


def probs_to_bits(probs, n, bit_of):
    """Reorder a dm_sim probability array (axes = ascending qubit index) into
    the classical-bit order c[0] most significant."""
    assert len(bit_of) == n
    t = probs.reshape((2,) * n)
    order = [None] * n
    for j, b in bit_of.items():
        order[b] = j
    return np.transpose(t, order).reshape(-1)


def circuit_stats(gates):
    n_2q = sum(1 for g in gates if g[0] in ("ZZPhase", "ZZMax"))
    n_1q = sum(1 for g in gates if g[0] == "PhasedX")
    n_rz = sum(1 for g in gates if g[0] == "Rz")
    # 2q depth: ASAP layering over 2q gates only
    last, d = {}, 0
    for g in gates:
        if g[0] in ("ZZPhase", "ZZMax"):
            L = max(last.get(g[1], 0), last.get(g[2], 0)) + 1
            last[g[1]] = last[g[2]] = L
            d = max(d, L)
    layers = dm_sim.assign_layers(gates, rz_virtual=True)
    return dict(n_2q=n_2q, n_1q=n_1q, n_rz=n_rz, depth_2q=d,
                n_layers=max(layers) if layers else 0)


# ------------------------------------------------------------------- work

def list_circuits(family="A"):
    """(file, model, n, r, disorder, instance) for every circuit with n <= MAX_N.
    For B1: model = file stem, r / disorder / instance empty."""
    out = []
    if family == "B1":
        with open(os.path.join(BENCH_B1, "manifest.csv")) as fh:
            for row in csv.DictReader(fh):
                n = int(row["n"])
                if n <= MAX_N:
                    out.append((row["file"], row["file"][:-5], n, "", "", ""))
        return out
    for f in sorted(os.listdir(os.path.join(COMPILED, "P0"))):
        m = _NAME.match(f)
        if not m:
            continue
        n = int(m.group("n"))
        if n <= MAX_N:
            out.append((f, m.group("model"), n, int(m.group("r")), m.group("dis"), int(m.group("s"))))
    return out


def reference_probs(f, family="A"):
    """Ideal reference distribution in classical-bit order (c[0] MSB)."""
    if family == "A":
        return np.load(os.path.join(BENCH, f[:-5] + ".npy"))
    with open(os.path.join(COMPILED, "P0ref", f)) as fh:
        gates, nq, bit_of = parse_hqslib1(fh.read())
    p, _, _ = dm_sim.simulate(gates, dm_sim.NOISE_OFF, nq)
    return probs_to_bits(p, nq, bit_of)


def one_run(job):
    f, model, n, r, dis, s, pipe = job[:7]
    if len(job) > 7:
        CFG["noise"], CFG["family"] = job[7], job[8]
    t0 = time.perf_counter()
    with open(os.path.join(COMPILED, pipe, f)) as fh:
        gates, nq, bit_of = parse_hqslib1(fh.read())
    ref = reference_probs(f, CFG["family"])
    st = circuit_stats(gates)
    ideal, _, _ = dm_sim.simulate(gates, dm_sim.NOISE_OFF, nq)
    ideal = probs_to_bits(ideal, nq, bit_of)
    ideal_vs_ref = float(np.max(np.abs(ideal - ref)))
    row = dict(file=f, model=model, n=n, r=r, disorder=dis, instance=s, pipeline=pipe,
               n_qubits=nq, **st, ideal_vs_ref_maxdiff=ideal_vs_ref)
    if CFG["noise"] == "typical":
        noisyA, _, _ = dm_sim.simulate(gates, NoiseModel(**NOISE_A), nq)
        noisyA = probs_to_bits(noisyA, nq, bit_of)
        noisyB, _, _ = dm_sim.simulate(gates, NoiseModel(**NOISE_B), nq)
        noisyB = probs_to_bits(noisyB, nq, bit_of)
        row.update(F_H=hellinger_fidelity(ref, noisyA), TVD=total_variation(ref, noisyA),
                   F_H_idle=hellinger_fidelity(ref, noisyB), TVD_idle=total_variation(ref, noisyB))
    else:
        noisy, _, _ = dm_sim.simulate(gates, NoiseModel(**NOISE_H22E), nq)
        noisy = probs_to_bits(noisy, nq, bit_of)
        row.update(F_H=hellinger_fidelity(ref, noisy), TVD=total_variation(ref, noisy),
                   support_size=int((ref > SUPPORT_TOL).sum()))
    row["t_sim"] = time.perf_counter() - t0
    return row


def verify(circuits, k=10, family="A"):
    """Noise-free dm_sim through the measure map vs compile.probs_from_measured_qasm
    and vs the reference (.npy for A, P0ref noise-free for B1), on k random
    circuits of every pipeline."""
    import compile as cp  # pipelines/compile.py
    worst = []
    rng = np.random.default_rng(0)
    idx = rng.choice(len(circuits), size=min(k, len(circuits)), replace=False)
    for pipe in PIPELINES:
        for i in idx:
            f = circuits[i][0]
            with open(os.path.join(COMPILED, pipe, f)) as fh:
                txt = fh.read()
            gates, nq, bit_of = parse_hqslib1(txt)
            p_dm, _, _ = dm_sim.simulate(gates, dm_sim.NOISE_OFF, nq)
            p_dm = probs_to_bits(p_dm, nq, bit_of)
            p_tk = cp.probs_from_measured_qasm(txt)
            p_ref = reference_probs(f, family)
            worst.append((pipe, f, float(np.max(np.abs(p_dm - p_tk))), float(np.max(np.abs(p_dm - p_ref)))))
    return worst


# -------------------------------------------------------------------- fit

def fit_loglinear(X, y):
    """Least squares y = X beta (no intercept unless a column of ones is in X).
    Returns beta, standard errors (OLS, homoscedastic), residual std, R^2."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    dof = len(y) - X.shape[1]
    s2 = float(res @ res) / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(res @ res) / ss_tot if ss_tot > 0 else float("nan")
    return beta, se, math.sqrt(s2), r2


def do_fits(rows, col="F_H", per_model=True):
    n2 = np.array([r["n_2q"] for r in rows], float)
    n1 = np.array([r["n_1q"] for r in rows], float)
    d2 = np.array([r["depth_2q"] for r in rows], float)
    nn = np.array([r["n"] for r in rows], float)
    y = -np.log(np.array([r[col] for r in rows], float))
    fits = {}
    fits["a n_2q + b n_1q"] = (["a", "b"],) + fit_loglinear(np.c_[n2, n1], y)
    fits["a n_2q + b n_1q + c depth_2q"] = (["a", "b", "c"],) + fit_loglinear(np.c_[n2, n1, d2], y)
    fits["a n_2q + b n_1q + s n  (s: SPAM per measured qubit)"] = (["a", "b", "s"],) + fit_loglinear(np.c_[n2, n1, nn], y)
    fits["a n_2q only"] = (["a"],) + fit_loglinear(np.c_[n2], y)
    if "support_size" in rows[0]:
        sup = np.array([r["support_size"] for r in rows], float)
        fits["a n_2q + b n_1q + u support_size"] = (["a", "b", "u"],) + fit_loglinear(np.c_[n2, n1, sup], y)
        fits["a n_2q + b n_1q + s n + u support_size"] = (["a", "b", "s", "u"],) + fit_loglinear(np.c_[n2, n1, nn, sup], y)
        fits["a n_2q + b n_1q + v log2(support_size)"] = (["a", "b", "v"],) + fit_loglinear(np.c_[n2, n1, np.log2(sup)], y)
    if per_model:
        for model in sorted({r["model"] for r in rows}):
            m = np.array([r["model"] == model for r in rows])
            if m.sum() > 3:
                fits["a n_2q + s n, model = %s only" % model] = (["a", "s"],) + fit_loglinear(np.c_[n2[m], nn[m]], y[m])
    return fits


def report_fits(fits, col):
    lines = ["Fits of -ln %s (least squares, OLS standard errors):" % col]
    for name, (names, beta, se, sig, r2) in fits.items():
        terms = ", ".join("%s = %.4e +/- %.1e" % (nm, b, e) for nm, b, e in zip(names, beta, se))
        lines.append("  %-50s %s ; resid sd %.2e ; R^2 %.4f" % (name, terms, sig, r2))
    return "\n".join(lines)


# ------------------------------------------------------------------ figure

def make_figure(rows, fits):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    colours = {"P0ref": "#777777", "P0": "#1f77b4", "P1": "#d62728", "P2": "#2ca02c", "P3": "#9467bd"}
    markers = {4: "o", 6: "s", 8: "^"}
    for pipe in PIPELINES:
        for n in (4, 6, 8):
            sub = [r for r in rows if r["pipeline"] == pipe and r["n"] == n]
            ax1.scatter([r["n_2q"] for r in sub], [r["F_H"] for r in sub], s=18, alpha=0.75,
                        c=colours[pipe], marker=markers[n],
                        label=pipe if n == 4 else None)
    names, beta, se, _, _ = fits["a n_2q + b n_1q"]
    a, b = beta
    # fit line drawn at the mean n_1q/n_2q ratio of the data
    ratio = np.mean([r["n_1q"] for r in rows]) / np.mean([r["n_2q"] for r in rows])
    xs = np.linspace(0, max(r["n_2q"] for r in rows) * 1.02, 200)
    ax1.plot(xs, np.exp(-(a + b * ratio) * xs), "k--", lw=1,
             label="fit exp(-(a n2q + b n1q)), n1q = %.2f n2q" % ratio)
    a1 = fits["a n_2q only"][1][0]
    ax1.plot(xs, np.exp(-a1 * xs), "k-", lw=1, label="fit exp(-a n2q), a = %.2e" % a1)
    ax1.set_xlabel("n_2q (ZZPhase count)")
    ax1.set_ylabel("Hellinger fidelity F_H (ideal vs noisy)")
    ax1.set_title("H2 typical, p_idle = 0; marker: o n=4, s n=6, ^ n=8")
    ax1.legend(fontsize=7, loc="lower left")
    ax1.grid(alpha=0.3)

    by = {(r["file"], r["pipeline"]): r for r in rows}
    files = sorted({r["file"] for r in rows})
    x = [by[(f, "P0")]["F_H"] for f in files]
    yv = [by[(f, "P1")]["F_H"] for f in files]
    ns = [by[(f, "P0")]["n"] for f in files]
    for n in (4, 6, 8):
        ax2.scatter([xi for xi, ni in zip(x, ns) if ni == n], [yi for yi, ni in zip(yv, ns) if ni == n],
                    s=20, marker=markers[n], label="n = %d" % n, alpha=0.8)
    lo = min(min(x), min(yv)) * 0.98
    ax2.plot([lo, 1], [lo, 1], "k:", lw=1)
    ax2.set_xlabel("F_H (P0, pytket level 2)")
    ax2.set_ylabel("F_H (P1, PyZX full_reduce + P0)")
    ax2.set_title("per circuit, same noise")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIG + ".pdf")
    fig.savefig(OUT_FIG + ".png", dpi=160)


# ---------------------------------------------------------- figure (h22e)

# fixed categorical order, one hue per pipeline (Okabe-Ito, colour-blind safe)
PIPE_COLOURS = {"P0ref": "#999999", "P0": "#0072B2", "P1": "#D55E00",
                "P2": "#009E73", "P3": "#CC79A7"}
N_MARKERS = {4: "o", 6: "s", 8: "^", 5: "D", 7: "v"}


def load_csv(path):
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            for k in ("n", "n_qubits", "n_2q", "n_1q", "n_rz", "depth_2q", "n_layers", "support_size"):
                if k in r:
                    r[k] = int(r[k])
            for k in ("r", "instance"):
                if k in r and r[k] != "":
                    r[k] = int(r[k])
            for k in ("ideal_vs_ref_maxdiff", "F_H", "TVD", "F_H_idle", "TVD_idle", "t_sim"):
                if k in r:
                    r[k] = float(r[k])
            rows.append(r)
    return rows


def make_figure_h22e(rows_a, rows_b, fits_a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5.4))
    # panel A: family A, F_H vs n_2q
    for pipe in PIPELINES:
        for n in (4, 6, 8):
            sub = [r for r in rows_a if r["pipeline"] == pipe and r["n"] == n]
            ax1.scatter([r["n_2q"] for r in sub], [r["F_H"] for r in sub], s=16, alpha=0.75,
                        c=PIPE_COLOURS[pipe], marker=N_MARKERS[n], linewidths=0,
                        label=pipe if n == 4 else None)
    names, beta, se, _, _ = fits_a["a n_2q + b n_1q"]
    a, b = beta
    ratio = np.mean([r["n_1q"] for r in rows_a]) / np.mean([r["n_2q"] for r in rows_a])
    xs = np.linspace(0, max(r["n_2q"] for r in rows_a) * 1.02, 200)
    ax1.plot(xs, np.exp(-(a + b * ratio) * xs), "k--", lw=1,
             label="fit exp(-(a n2q + b n1q)), n1q = %.2f n2q" % ratio)
    a1 = fits_a["a n_2q only"][1][0]
    ax1.plot(xs, np.exp(-a1 * xs), "k-", lw=1, label="fit exp(-a n2q), a = %.2e" % a1)
    ax1.set_xlabel("n_2q (ZZPhase count)")
    ax1.set_ylabel("Hellinger fidelity F_H (ideal vs noisy)")
    ax1.set_title("Family A, H2-2E defaults, p_idle = 0\nmarker: o n=4, s n=6, ^ n=8", fontsize=9)
    ax1.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False)
    ax1.grid(alpha=0.3)

    # panel B: family B1, F_H vs n_2q, one point per (circuit, pipeline), labelled
    files_b = sorted({r["file"] for r in rows_b}, key=lambda f: (next(r["n"] for r in rows_b if r["file"] == f), f))
    for pipe in PIPELINES:
        sub = [r for r in rows_b if r["pipeline"] == pipe]
        ax2.scatter([r["n_2q"] for r in sub], [r["F_H"] for r in sub], s=28, alpha=0.85,
                    c=PIPE_COLOURS[pipe], marker="o", linewidths=0, label=pipe)
    for i, f in enumerate(files_b):
        sub = [r for r in rows_b if r["file"] == f]
        xs_ = [r["n_2q"] for r in sub]
        ys_ = [r["F_H"] for r in sub]
        ax2.plot(xs_, ys_, "-", color="#bbbbbb", lw=0.8, zorder=0)
        j = ys_.index(min(ys_))
        ax2.annotate(f[:-5], (xs_[j], ys_[j]), fontsize=6, xytext=(4, -9 if i % 2 else 5),
                     textcoords="offset points", color="#444444")
    ax2.set_xlabel("n_2q (ZZPhase count)")
    ax2.set_ylabel("F_H (vs P0ref noise-free output)")
    ax2.set_title("Family B1 (n <= 8), H2-2E defaults, p_idle = 0\ngrey line joins the pipelines of one circuit", fontsize=9)
    ax2.legend(fontsize=7, loc="lower left")
    ax2.grid(alpha=0.3)

    # panel C: F_H(P2) vs F_H(P0) per circuit, both families
    by_a = {(r["file"], r["pipeline"]): r for r in rows_a}
    by_b = {(r["file"], r["pipeline"]): r for r in rows_b}
    pts = []
    for n in (4, 6, 8):
        fs = sorted({r["file"] for r in rows_a if r["n"] == n})
        x = [by_a[(f, "P0")]["F_H"] for f in fs]
        y = [by_a[(f, "P2")]["F_H"] for f in fs]
        pts += list(zip(x, y))
        ax3.scatter(x, y, s=18, marker=N_MARKERS[n], c="#0072B2", alpha=0.75, linewidths=0, label="A, n = %d" % n)
    fs = sorted({r["file"] for r in rows_b})
    x = [by_b[(f, "P0")]["F_H"] for f in fs]
    y = [by_b[(f, "P2")]["F_H"] for f in fs]
    pts += list(zip(x, y))
    ax3.scatter(x, y, s=34, marker="*", c="#D55E00", alpha=0.9, linewidths=0, label="B1 (n = 5, 7)")
    for f, xi, yi in zip(fs, x, y):
        ax3.annotate(f[:-5], (xi, yi), fontsize=6, xytext=(3, 3), textcoords="offset points", color="#444444")
    lo = min(min(p) for p in pts) * 0.98
    ax3.plot([lo, 1], [lo, 1], "k:", lw=1)
    ax3.set_xlabel("F_H (P0, pytket level 2)")
    ax3.set_ylabel("F_H (P2, PyZX teleport_reduce + P0)")
    ax3.set_title("per circuit, same noise; dotted = equal", fontsize=9)
    ax3.legend(fontsize=7, loc="upper left")
    ax3.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_FIG_H22E + ".pdf")
    fig.savefig(OUT_FIG_H22E + ".png", dpi=160)


def print_table(rows, cols=("F_H", "TVD")):
    print("%4s %6s %9s %9s %8s %8s %9s %8s" % ("n", "pipe", "F_H", "TVD", "n_2q", "n_1q", "depth_2q", "support"))
    for n in sorted({r["n"] for r in rows}):
        for p in PIPELINES:
            sub = [r for r in rows if r["n"] == n and r["pipeline"] == p]
            print("%4d %6s %9.5f %9.5f %8.2f %8.2f %9.2f %8.1f" % (
                n, p, np.mean([r["F_H"] for r in sub]), np.mean([r["TVD"] for r in sub]),
                np.mean([r["n_2q"] for r in sub]), np.mean([r["n_1q"] for r in sub]),
                np.mean([r["depth_2q"] for r in sub]), np.mean([r["support_size"] for r in sub])))


def figure_h22e():
    rows_a = load_csv(os.path.join(RESULTS, "family_A_proxy_h22e.csv"))
    rows_b = load_csv(os.path.join(RESULTS, "family_B1_proxy_h22e.csv"))
    print("family A rows: %d ; family B1 rows: %d" % (len(rows_a), len(rows_b)))
    print("\nfamily A, mean over circuits per (n, pipeline):")
    print_table(rows_a)
    print("\nfamily B1, per circuit:")
    print("%-16s %2s %6s %9s %9s %6s %6s %8s %8s" % ("file", "n", "pipe", "F_H", "TVD", "n_2q", "n_1q", "depth_2q", "support"))
    for r in sorted(rows_b, key=lambda r: (r["n"], r["file"], PIPELINES.index(r["pipeline"]))):
        print("%-16s %2d %6s %9.5f %9.5f %6d %6d %8d %8d" % (
            r["file"][:-5], r["n"], r["pipeline"], r["F_H"], r["TVD"], r["n_2q"], r["n_1q"], r["depth_2q"], r["support_size"]))
    fits_a = do_fits(rows_a, "F_H")
    print("\nFamily A:\n" + report_fits(fits_a, "F_H"))
    fits_b = do_fits(rows_b, "F_H", per_model=False)
    print("\nFamily B1 (35 rows):\n" + report_fits(fits_b, "F_H"))
    fits_ab = do_fits(rows_a + rows_b, "F_H", per_model=False)
    print("\nA + B1 pooled:\n" + report_fits(fits_ab, "F_H"))
    make_figure_h22e(rows_a, rows_b, fits_a)
    print("figure:", OUT_FIG_H22E + ".pdf", OUT_FIG_H22E + ".png")


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--from-csv", action="store_true", help="redo fits and figure from the saved CSV")
    ap.add_argument("--noise", choices=sorted(NOISE_SETS), default="typical")
    ap.add_argument("--family", choices=["A", "B1"], default="A")
    ap.add_argument("--figure-h22e", action="store_true",
                    help="only remake fits/figure from family_A_proxy_h22e.csv and family_B1_proxy_h22e.csv")
    args = ap.parse_args()
    t_start = time.perf_counter()
    if args.figure_h22e:
        figure_h22e()
        print("total time %.1f s" % (time.perf_counter() - t_start))
        return
    CFG["noise"] = args.noise
    CFG["family"] = args.family
    out_csv = OUT_CSV
    if args.noise == "h22e":
        out_csv = os.path.join(RESULTS, "family_%s_proxy_h22e.csv" % args.family)
    elif args.family != "A":
        out_csv = os.path.join(RESULTS, "family_%s_proxy.csv" % args.family)
    print("noise set %s: %s" % (args.noise, NOISE_SETS[args.noise]))

    circuits = list_circuits(args.family)
    print("family %s circuits with n <= %d: %d ; pipelines: %s" % (args.family, MAX_N, len(circuits), PIPELINES))

    checks = verify(circuits, k=10, family=args.family)
    worst_tk = max(c[2] for c in checks)
    worst_ref = max(c[3] for c in checks)
    print("verify (10 circuits x %d pipelines): max |dm_sim - probs_from_measured_qasm| = %.2e, "
          "max |dm_sim - reference (%s)| = %.2e" % (len(PIPELINES), worst_tk, "npy" if args.family == "A" else "P0ref noise-free", worst_ref))
    bad = [c for c in checks if c[2] > 1e-10 or c[3] > 1e-10]
    if bad:
        print("FAILED checks:", bad)
        if not args.verify_only:
            raise SystemExit("parser verification failed")
    if args.verify_only:
        return

    if args.from_csv:
        rows = load_csv(out_csv)
        print("loaded %d rows from %s" % (len(rows), out_csv))
    else:
        jobs = [c + (p, args.noise, args.family) for p in PIPELINES for c in circuits]
        t0 = time.perf_counter()
        with Pool(args.workers) as pool:
            rows = pool.map(one_run, jobs, chunksize=4)
        t_sim = time.perf_counter() - t0
        bad = [r for r in rows if r["ideal_vs_ref_maxdiff"] > 1e-10]
        print("runs: %d in %.1f s wall (%d workers); noise-free-vs-npy failures: %d"
              % (len(rows), t_sim, args.workers, len(bad)))

        cols = list(rows[0].keys())
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        with open(out_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print("wrote", out_csv)

    if args.noise == "h22e":
        print("\nmean over circuits of F_H / TVD / n_2q / n_1q / depth_2q / support_size (p_idle = 0):")
        print_table(rows)
        fits = do_fits(rows, "F_H", per_model=(args.family == "A"))
        print("\n" + report_fits(fits, "F_H"))
        print("total time %.1f s" % (time.perf_counter() - t_start))
        return

    # mean F_H by (n, pipeline)
    print("\nmean over circuits (36 per cell) of F_H [p_idle=0] / F_H_idle [p_idle=5e-4 per layer, ASSUMPTION] / n_2q / n_1q:")
    print("%4s %6s %9s %9s %8s %8s %9s" % ("n", "pipe", "F_H", "F_H_idle", "n_2q", "n_1q", "depth_2q"))
    for n in sorted({r["n"] for r in rows}):
        for p in PIPELINES:
            sub = [r for r in rows if r["n"] == n and r["pipeline"] == p]
            print("%4d %6s %9.5f %9.5f %8.2f %8.2f %9.2f" % (
                n, p, np.mean([r["F_H"] for r in sub]), np.mean([r["F_H_idle"] for r in sub]),
                np.mean([r["n_2q"] for r in sub]), np.mean([r["n_1q"] for r in sub]),
                np.mean([r["depth_2q"] for r in sub])))

    fits = do_fits(rows, "F_H")
    print("\n" + report_fits(fits, "F_H"))
    fits_idle = do_fits(rows, "F_H_idle")
    print("\n" + report_fits(fits_idle, "F_H_idle"))
    p2 = NOISE_A["p2"]
    print("\nreference values from p2 = %.2e: p2 = %.3e (Pauli-error probability per 2q gate, "
          "= 1 - entanglement fidelity); 16 p2 / 15 = %.3e (full-depolarisation probability); "
          "4 p2 / 5 = %.3e (average gate infidelity)" % (p2, p2, 16 * p2 / 15, 4 * p2 / 5))

    make_figure(rows, fits)
    print("figure:", OUT_FIG + ".pdf", OUT_FIG + ".png")
    print("total time %.1f s" % (time.perf_counter() - t_start))


if __name__ == "__main__":
    main()
