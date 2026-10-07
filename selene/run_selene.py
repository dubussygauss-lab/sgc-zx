"""Run the compiled circuits of families A (n <= 10) and B1 (n <= 10) on the
local Selene emulator (selene-sim, Quest statevector backend) and compare the
sampled distribution with the exact one.

Route (the one that works, see results/selene.md):
    results/compiled/<pipe>/<file>.qasm  (hqslib1: rz, U1q, RZZ, measure)
    -> pytket.qasm.circuit_from_qasm       (OpType.Rz, PhasedX, ZZPhase, Measure)
    -> guppylang.guppy.load_pytket         (array[qubit, n] -> array[bool, n])
    -> guppy main(): allocate n qubits, call, discard_array, result("c", bits)
    -> selene_sim.build(main.compile()).run_shots(Quest(seed), ...)
The returned array "c" is in classical-bit order c[0..n-1]; the bitstring
"".join(c) therefore has c[0] as its most significant bit, which is the
convention of bench/family_A/*.npy and of compile.probs_from_measured_qasm.
Verified by selene/test_selene.py (Bell test and a measure-map permutation test).

Modes
    noiseless    every circuit, IdealErrorModel, SHOTS shots, seeded
                 -> results/selene_noiseless.csv
    depolarizing a subset (DEPOL_SUBSET below), DepolarizingErrorModel with the
                 H2-2E p1 / p2 (and optionally p_meas / p_init), compared with
                 the local density-matrix proxy (results/family_*_proxy_h22e.csv)
                 -> results/selene_depolarizing.csv

Usage (every proxy variable must be unset, otherwise selene's local TCP result
stream is routed through the proxy and hangs):
    HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= \
        python3 selene/run_selene.py [--mode noiseless|depolarizing|both] [--procs 2] [--shots 2000]
"""
import argparse
import csv
import hashlib
import math
import multiprocessing as mp
import os
import re
import sys
import time
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipelines"))
sys.path.insert(0, os.path.join(ROOT, "noise"))

COMPILED = os.path.join(ROOT, "results", "compiled")
BENCH_A = os.path.join(ROOT, "bench", "family_A")
BENCH_B1 = os.path.join(ROOT, "bench", "family_B1")
RESULTS = os.path.join(ROOT, "results")
OUT_NOISELESS = os.path.join(RESULTS, "selene_noiseless.csv")
OUT_DEPOL = os.path.join(RESULTS, "selene_depolarizing.csv")

PIPELINES = ["P0", "P1", "P2"]
MAX_N = 10
SHOTS = 2000
SUPPORT_TOL = 1e-12       # p_i > SUPPORT_TOL counts as support (same as noise/run_proxy.py)
CHI2_MAX_SUPPORT = 64
FLAG_FACTOR = 4.0
BOOT = 400                # Monte-Carlo resamples for the expected sampled F_H

# H2-2E emulator defaults, docs/platform_notes.md section 3.3 / noise/h2_params.py
P1_H22E = 7.3e-5
P2_H22E = 1.29e-3
P_MEAS_H22E = (9e-4, 1.8e-3)       # asymmetric (0 read as 1, 1 read as 0)
P_INIT_H22E = 4e-5
# selene's DepolarizingErrorModel has a single symmetric p_meas; the mean of
# the two H2-2E rates is used (ASSUMPTION, stated in results/selene.md)
P_MEAS_SYM = 0.5 * (P_MEAS_H22E[0] + P_MEAS_H22E[1])

DEPOL_VARIANTS = {
    "gates_only": dict(p_1q=P1_H22E, p_2q=P2_H22E),
    "gates_meas_init": dict(p_1q=P1_H22E, p_2q=P2_H22E, p_meas=P_MEAS_SYM, p_init=P_INIT_H22E),
}

# circuits for the depolarising comparison: all 7 B1 circuits covered by the
# proxy (n <= 7) and 10 family-A circuits covered by the proxy (n <= 8)
DEPOL_SUBSET_B1 = ["barenco_tof_3.qasm", "mod5_4.qasm", "qft_4.qasm", "tof_3.qasm",
                   "barenco_tof_4.qasm", "hwb6.qasm", "tof_4.qasm"]
DEPOL_SUBSET_A = ["ladder_n4_r1_disorder_s1.qasm", "ladder_n6_r2_disorder_s1.qasm",
                  "ladder_n8_r4_disorder_s1.qasm", "tfim_n4_r2_uniform_s1.qasm",
                  "tfim_n6_r4_disorder_s2.qasm", "tfim_n8_r1_disorder_s1.qasm",
                  "xxz_n4_r4_disorder_s1.qasm", "xxz_n6_r1_uniform_s1.qasm",
                  "xxz_n8_r2_disorder_s3.qasm", "xxz_n8_r4_disorder_s2.qasm"]

_NAME = re.compile(r"^(?P<model>[a-z]+)_n(?P<n>\d+)_r(?P<r>\d+)_(?P<dis>[a-z]+)_s(?P<s>\d+)\.qasm$")


# ------------------------------------------------------------------ circuits

def list_circuits():
    """(family, file, model, n) for every family-A and B1 circuit with n <= MAX_N."""
    out = []
    for f in sorted(os.listdir(os.path.join(COMPILED, "P0"))):
        m = _NAME.match(f)
        if m and int(m.group("n")) <= MAX_N:
            out.append(("A", f, m.group("model"), int(m.group("n"))))
    with open(os.path.join(BENCH_B1, "manifest.csv")) as fh:
        for row in csv.DictReader(fh):
            if int(row["n"]) <= MAX_N:
                out.append(("B1", row["file"], row["file"][:-5], int(row["n"])))
    return out


def seed_for(pipe, f, tag):
    h = hashlib.sha256(f"{pipe}/{f}/{tag}".encode()).digest()
    return int.from_bytes(h[:4], "little") & 0x7FFFFFFF


# ------------------------------------------------------------------ metrics

def hellinger_fidelity(p, q):
    return float(np.sum(np.sqrt(p * q)) ** 2)


def tvd(p, q):
    return float(0.5 * np.sum(np.abs(p - q)))


def expected_tvd_support(k, shots):
    """Scale stated in the brief: sqrt(k / (2 pi N)); exact asymptotic mean of
    the TVD of an N-shot sample from the uniform distribution on k outcomes."""
    return math.sqrt(k / (2 * math.pi * shots))


def expected_tvd_exact(p, shots):
    """Asymptotic (normal-approximation) mean of the sampling TVD for the
    actual distribution p: 0.5 sqrt(2/(pi N)) sum_i sqrt(p_i (1 - p_i))."""
    return float(0.5 * math.sqrt(2 / (math.pi * shots)) * np.sum(np.sqrt(p * (1 - p))))


def chi2_pvalue(counts, p, shots):
    """Chi-square goodness of fit against the exact multinomial on the support.
    Returns (p-value, n_cells_expected_below_5, shots_outside_support,
    pooled p-value).  Any shot outside the support is impossible under p and
    gives p-value 0.  Support of size 1 has no degrees of freedom: p-value 1 if
    every shot is on the support, 0 otherwise.  The pooled p-value merges every
    support cell with expected count < 5 into one cell (and, if that pooled
    cell is itself below 5, into the smallest remaining cell), which is the
    textbook remedy for sparse cells."""
    from scipy.stats import chisquare
    supp = p > SUPPORT_TOL
    outside = int(counts[~supp].sum())
    if outside > 0:
        return 0.0, int((p[supp] * shots < 5).sum()), outside, 0.0
    exp = p[supp] * shots
    if supp.sum() == 1:
        return 1.0, 0, 0, 1.0
    obs = counts[supp].astype(float)
    exp = exp * obs.sum() / exp.sum()
    stat, pv = chisquare(obs, exp)
    low = exp < 5
    if low.sum() == 0:
        pooled = float(pv)
    else:
        big = ~low
        cells = [(e, o) for e, o in zip(exp[big], obs[big])] + [(exp[low].sum(), obs[low].sum())]
        cells.sort()
        while len(cells) > 1 and cells[0][0] < 5:
            (e0, o0), (e1, o1) = cells[0], cells[1]
            cells = [(e0 + e1, o0 + o1)] + cells[2:]
            cells.sort()
        if len(cells) == 1:
            pooled = 1.0
        else:
            exp_p = np.array([c[0] for c in cells])
            obs_p = np.array([c[1] for c in cells])
            pooled = float(chisquare(obs_p, exp_p)[1])
    return float(pv), int(low.sum()), 0, pooled


def as_distribution(p):
    """Float distribution with round-off removed: entries of order -1e-17 or
    1 + 1e-15 (statevector / density-matrix arithmetic) are clipped to [0, 1]
    and the vector renormalised, so numpy's multinomial accepts it."""
    p = np.asarray(p, dtype=float)
    assert p.min() > -1e-9 and p.max() < 1 + 1e-9 and abs(p.sum() - 1) < 1e-9, (p.min(), p.max(), p.sum())
    p = np.clip(p, 0.0, 1.0)
    return p / p.sum()


def exact_probs(pipe, f):
    import compile as C
    with open(os.path.join(COMPILED, pipe, f)) as fh:
        return as_distribution(C.probs_from_measured_qasm(fh.read()))


def reference_probs(family, f):
    if family == "A":
        return as_distribution(np.load(os.path.join(BENCH_A, f[:-5] + ".npy")))
    return exact_probs("P0ref", f)


# ------------------------------------------------------------------ selene

_PROXY_VARS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy")


def _unset_proxies():
    for v in _PROXY_VARS:
        os.environ.pop(v, None)


def build_runner(circ, name):
    from guppylang import guppy
    from guppylang.std.builtins import array, result
    from guppylang.std.quantum import qubit, discard_array
    from selene_sim import build
    n = circ.n_qubits
    fn = guppy.load_pytket(name, circ)

    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(n))
        c = fn(qs)
        discard_array(qs)
        result("c", c)

    return build(main.compile())


def sample(runner, n, shots, seed, error_model=None):
    """Counts as a length-2^n integer array indexed by int("".join(c), 2)."""
    from selene_sim import Quest, IdealErrorModel
    em = IdealErrorModel() if error_model is None else error_model
    counts = np.zeros(2 ** n, dtype=np.int64)
    for shot in runner.run_shots(Quest(random_seed=seed), n_qubits=n, n_shots=shots,
                                 error_model=em, random_seed=seed):
        bits = dict(shot)["c"]
        idx = 0
        for b in bits:
            idx = (idx << 1) | int(b)
        counts[idx] += 1
    assert counts.sum() == shots
    return counts


def circuit_stats(circ):
    from pytket import OpType
    n2 = n1 = nrz = 0
    for cmd in circ.get_commands():
        t = cmd.op.type
        if t == OpType.Measure or t == OpType.Barrier:
            continue
        if len(cmd.args) == 2:
            n2 += 1
        elif t == OpType.Rz:
            nrz += 1
        else:
            n1 += 1
    return dict(n_2q=n2, n_1q=n1, n_rz=nrz)


# ------------------------------------------------------------------ workers

def noiseless_job(job):
    family, f, model, n, pipe, shots, idx = job
    _unset_proxies()
    from pytket.qasm import circuit_from_qasm
    t0 = time.perf_counter()
    circ = circuit_from_qasm(os.path.join(COMPILED, pipe, f))
    assert circ.n_qubits == n, (f, circ.n_qubits, n)
    p = exact_probs(pipe, f)
    ref = reference_probs(family, f)
    st = circuit_stats(circ)
    t1 = time.perf_counter()
    runner = build_runner(circ, f"c{idx}")
    t2 = time.perf_counter()
    seed = seed_for(pipe, f, "noiseless")
    counts = sample(runner, n, shots, seed)
    t3 = time.perf_counter()
    q = counts / shots
    k = int((p > SUPPORT_TOL).sum())
    tv = tvd(p, q)
    scale = expected_tvd_support(k, shots)
    e_exact = expected_tvd_exact(p, shots)
    if k <= CHI2_MAX_SUPPORT:
        pv, low, outside, pv_pooled = chi2_pvalue(counts, p, shots)
    else:
        pv, low, outside, pv_pooled = float("nan"), -1, int(counts[p <= SUPPORT_TOL].sum()), float("nan")
    nz = np.nonzero(counts)[0]
    counts_str = ";".join(f"{int(i)}:{int(counts[i])}" for i in nz)   # sparse "index:count", index = int(bitstring, 2)
    return dict(family=family, file=f, model=model, n=n, pipeline=pipe, **st,
                shots=shots, seed=seed, support_size=k,
                exact_vs_ref_maxdiff=float(np.max(np.abs(p - ref))),
                F_H=hellinger_fidelity(p, q), TVD=tv,
                TVD_scale=scale, TVD_over_scale=tv / scale,
                TVD_expected_exact=e_exact, TVD_over_expected=tv / e_exact if e_exact > 0 else float("nan"),
                flag=int(tv > FLAG_FACTOR * scale),
                shots_outside_support=outside,
                chi2_p=pv, chi2_cells_below_5=low, chi2_p_pooled=pv_pooled,
                t_load=t1 - t0, t_build=t2 - t1, t_run=t3 - t2, t_total=t3 - t0,
                counts=counts_str)


def proxy_noisy_probs(family, f, pipe):
    """Noisy output distribution of the density-matrix proxy with the H2-2E
    parameter set (noise/run_proxy.py NOISE_H22E), in classical-bit order."""
    import dm_sim
    import run_proxy as RP
    from dm_sim import NoiseModel
    with open(os.path.join(COMPILED, pipe, f)) as fh:
        gates, nq, bit_of = RP.parse_hqslib1(fh.read())
    noisy, _, _ = dm_sim.simulate(gates, NoiseModel(**RP.NOISE_H22E), nq)
    return as_distribution(RP.probs_to_bits(noisy, nq, bit_of))


def depol_job(job):
    family, f, model, n, pipe, shots, idx, variant = job
    _unset_proxies()
    from pytket.qasm import circuit_from_qasm
    from selene_sim import DepolarizingErrorModel
    t0 = time.perf_counter()
    circ = circuit_from_qasm(os.path.join(COMPILED, pipe, f))
    ref = reference_probs(family, f)
    st = circuit_stats(circ)
    runner = build_runner(circ, f"d{idx}")
    seed = seed_for(pipe, f, "depol")
    params = DEPOL_VARIANTS[variant]
    em = DepolarizingErrorModel(random_seed=seed, **params)
    t1 = time.perf_counter()
    counts = sample(runner, n, shots, seed, error_model=em)
    t2 = time.perf_counter()
    q = counts / shots
    counts0 = sample(runner, n, shots, seed)      # same seed, no noise: sampling-only baseline
    q0 = counts0 / shots
    # proxy noisy distribution and the expected sampled F_H under it
    pn = proxy_noisy_probs(family, f, pipe)
    rng = np.random.default_rng(seed)
    fh_mc = np.array([hellinger_fidelity(ref, rng.multinomial(shots, pn) / shots) for _ in range(BOOT)])
    fh_mc_ideal = np.array([hellinger_fidelity(ref, rng.multinomial(shots, ref) / shots) for _ in range(BOOT)])
    fh_sel = hellinger_fidelity(ref, q)
    e, sd = float(fh_mc.mean()), float(fh_mc.std(ddof=1))
    z = (fh_sel - e) / sd if sd > 0 else float("nan")
    return dict(family=family, file=f, model=model, n=n, pipeline=pipe, variant=variant, **st,
                shots=shots, seed=seed, support_size=int((ref > SUPPORT_TOL).sum()),
                p_1q=params["p_1q"], p_2q=params["p_2q"],
                p_meas=params.get("p_meas", 0.0), p_init=params.get("p_init", 0.0),
                F_H_selene_depol=fh_sel,
                F_H_selene_noiseless_sameseed=hellinger_fidelity(ref, q0),
                F_H_proxy_exact=hellinger_fidelity(ref, pn),
                F_H_proxy_sampled_mean=e, F_H_proxy_sampled_sd=sd,
                F_H_ideal_sampled_mean=float(fh_mc_ideal.mean()),
                z=z, agree_2sd=int(abs(z) <= 2) if not math.isnan(z) else -1,
                TVD_selene_vs_proxy=tvd(pn, q), TVD_selene_vs_ideal=tvd(ref, q),
                TVD_expected_sampling=expected_tvd_exact(pn, shots),
                t_run_depol=t2 - t1, t_total=time.perf_counter() - t0)


# ------------------------------------------------------------------ driver

def write_csv(path, rows):
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_pool(jobs, fn, procs):
    if procs <= 1:
        return [fn(j) for j in jobs]
    ctx = mp.get_context("spawn")
    with ctx.Pool(procs) as pool:
        return list(pool.imap(fn, jobs, chunksize=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="both", choices=["noiseless", "depolarizing", "both"])
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--shots", type=int, default=SHOTS)
    ap.add_argument("--limit", type=int, default=0, help="debug: only the first k jobs")
    a = ap.parse_args()
    _unset_proxies()
    circuits = list_circuits()
    print(f"{len(circuits)} circuits (A: {sum(c[0] == 'A' for c in circuits)}, B1: {sum(c[0] == 'B1' for c in circuits)})")
    t_all = time.perf_counter()
    if a.mode in ("noiseless", "both"):
        jobs = []
        for pipe in PIPELINES:
            for fam, f, model, n in circuits:
                if os.path.exists(os.path.join(COMPILED, pipe, f)):
                    jobs.append((fam, f, model, n, pipe, a.shots, len(jobs)))
                else:
                    print(f"missing: {pipe}/{f}")
        if a.limit:
            jobs = jobs[:a.limit]
        print(f"noiseless: {len(jobs)} runs x {a.shots} shots, {a.procs} processes")
        t0 = time.perf_counter()
        rows = run_pool(jobs, noiseless_job, a.procs)
        dt = time.perf_counter() - t0
        write_csv(OUT_NOISELESS, rows)
        flagged = [r for r in rows if r["flag"]]
        print(f"noiseless done in {dt:.1f} s; max TVD/scale = {max(r['TVD_over_scale'] for r in rows):.3f}; "
              f"flagged = {len(flagged)}; wrote {OUT_NOISELESS}")
        for r in flagged:
            print("  FLAG", r["pipeline"], r["file"], r["TVD"], r["TVD_scale"])
    if a.mode in ("depolarizing", "both"):
        by_file = {c[1]: c for c in circuits}
        jobs = []
        for variant in DEPOL_VARIANTS:
            for f in DEPOL_SUBSET_B1 + DEPOL_SUBSET_A:
                fam, _, model, n = by_file[f]
                for pipe in ("P0", "P2"):
                    jobs.append((fam, f, model, n, pipe, a.shots, len(jobs), variant))
        if a.limit:
            jobs = jobs[:a.limit]
        print(f"depolarizing: {len(jobs)} runs x {a.shots} shots, {a.procs} processes")
        t0 = time.perf_counter()
        rows = run_pool(jobs, depol_job, a.procs)
        dt = time.perf_counter() - t0
        write_csv(OUT_DEPOL, rows)
        print(f"depolarizing done in {dt:.1f} s; agree (|z|<=2): {sum(r['agree_2sd'] == 1 for r in rows)}/{len(rows)}; wrote {OUT_DEPOL}")
    print(f"total wall time {time.perf_counter() - t_all:.1f} s")


if __name__ == "__main__":
    main()
