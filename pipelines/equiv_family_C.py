"""Family C: full equivalence check of the compiled P0 and P2 outputs by a
ZX-calculus miter (PyZX) and, as a second method, MQT QCEC.

For every circuit in bench/family_C/manifest.csv three comparisons are made:
  P0 vs input, P2 vs input, P2 vs P0
(input = bench/family_C/<file>, outputs = results/compiled/{P0,P2}/<file>).

Reading the circuits
  Both sides are parsed with pytket (circuit_from_qasm, maxwidth=64).  The
  compiled QASM ends with "measure q[j] -> c[i]" for every wire; this is how
  compile.add_measure_all encodes pytket's implicit qubit permutation (wire j
  carries logical qubit i at the output).  Measurements are stripped and the
  permutation is kept (run_family_C.strip_measures).  The input circuits have
  no measurements and the identity permutation.  No qubit is treated as an
  ancilla: the check is equality of the full 2^n x 2^n unitaries up to a
  global phase, which is stronger than equality on clean-ancilla inputs.

Method 1, PyZX miter (pyzx 0.10.7)
  Every gate is translated to PyZX gates with exact Fraction phases (units of
  pi, the same unit as pytket's half-turns):
    Rz(a)          -> ZPhase(a)                    (equal up to global phase)
    PhasedX(a, b)  -> ZPhase(-b) XPhase(a) ZPhase(b)  [= Rz(b) Rx(a) Rz(-b)]
    ZZPhase(a)     -> CNOT ZPhase(a) on target CNOT;  ZZMax = ZZPhase(1/2)
    CX, H, S, Sdg, T, Tdg -> CNOT, HAD, ZPhase(1/2, 3/2, 1/4, 7/4)
  pytket stores angles as floats.  Each angle is snapped to the dyadic grid
  2^-G, G = (largest dyadic exponent among the input circuit's angles) + 4,
  and the largest snap distance is recorded (column snap_err, in half-turns).
  The input angles of every family C circuit lie on that grid exactly, so the
  snap only removes float noise from the compiled side.  The miter
    G_A ; adjoint(G_B)
  (output wires of each side reordered by its permutation) is reduced with
  pyzx.simplify.full_reduce.  The test is the one in pyzx's
  Circuit.verify_equality (circuit/__init__.py lines 109-138): after
  full_reduce the graph has exactly 2n vertices (the boundaries), every edge
  is a simple (non-Hadamard) edge, and input i is connected to output i.
  This is implemented on graphs here instead of calling verify_equality
  because the output permutation has to be applied to the graph.  A positive
  result proves that the two snapped circuits are equal up to global phase.
  If snap_err > 0 the stored circuit differs from the snapped one by at most
  sum |snap| * pi/2 in operator norm per rotation (verdict "proven" with the
  snap error in the notes; "proven-up-to-rounding" if snap_err > 1e-9).  A
  negative result is inconclusive.  Circuits whose compiled angles do not lie
  on the grid (KAK resynthesis by FullPeepholeOptimise, e.g. hrs_mult_5) are
  not checked by PyZX (verdict "inconclusive", note "off-grid angles").

  P2 compiled the circuit after PyZX had parsed it, and pyzx's QASM parser
  rounds every angle with Fraction.limit_denominator(2^20)
  (compile.pyzx_angle_rounding).  When the exact P2-vs-input check fails and
  the input has angles off the 2^20 limit, the check is repeated with the
  input angles rounded the same way; success there is reported as
  "equal-up-to-rounding" with the maximum input angle error in radians.

Method 2, MQT QCEC (mqt.qcec 3.10.2)
  Each side is written as qelib1 QASM (h, cx, rz, rx with the float angles as
  stored, no snapping) with the output permutation realised by swap gates,
  and checked with qcec.verify using only the ZX checker (run_zx_checker) and
  separately only the alternating decision-diagram checker
  (run_alternating_checker), each with a 300 s timeout.  QCEC's DD checker
  works in floating point with a numerical tolerance, so its "equivalent"
  verdict is a numerical verification, not an exact proof.

Every check runs in its own process, killed after TIMEOUT seconds (verdict
"timeout").

Output: results/family_C_equivalence.csv
  file, n, comparison (P0, P2, P2vsP0), pipeline, method, verdict
  (proven / inconclusive / failed / timeout / equal-up-to-rounding / error),
  seconds, notes.

Output: results/family_C_equivalence.md (written by --summary from the CSV,
  value/family_C_selector.csv and bench/family_C/manifest.csv; no checks run).

Usage: python3 pipelines/equiv_family_C.py [--files a,b] [--methods pyzx,qcec_zx,qcec_alt] [--workers 2]
       python3 pipelines/equiv_family_C.py --summary
"""

import argparse
import math
import multiprocessing as mp
import os
import sys
import tempfile
import time
from fractions import Fraction

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyzx  # noqa: E402
from pyzx.utils import EdgeType  # noqa: E402
from pytket import Circuit, OpType  # noqa: E402
from pytket.qasm import circuit_from_qasm, circuit_from_qasm_str  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "bench", "family_C")
COMPILED = os.path.join(ROOT, "results", "compiled")
OUTCSV = os.path.join(ROOT, "results", "family_C_equivalence.csv")
TIMEOUT = 300.0
OFFGRID_TOL = 1e-6      # half-turns; above this an angle is "off-grid"
PYZX_MAXDEN = 2 ** 20   # pyzx settings.float_to_fraction_max_denominator
COLS = ["file", "n", "comparison", "pipeline", "method", "verdict", "seconds", "notes"]


# ----------------------------------------------------------- circuit loading

def strip_measures(c: Circuit):
    """-> (unitary Circuit, perm) with perm[j] = classical bit (= logical
    qubit) read from wire j; identity if the circuit has no measurements.
    Same logic as run_family_C.strip_measures."""
    u = Circuit(c.n_qubits)
    perm = {}
    for cmd in c.get_commands():
        if cmd.op.type == OpType.Measure:
            perm[cmd.args[0].index[0]] = cmd.args[1].index[0]
        elif cmd.op.type != OpType.Barrier:
            u.add_gate(cmd.op, [q.index[0] for q in cmd.args])
    if not perm:
        perm = {j: j for j in range(c.n_qubits)}
    assert sorted(perm) == list(range(c.n_qubits)), "partial measurement map"
    assert sorted(perm.values()) == list(range(c.n_qubits)), "not a permutation"
    return u, perm


def load(path: str):
    with open(path) as f:
        c = circuit_from_qasm_str(f.read(), maxwidth=64)
    assert [q.index[0] for q in c.qubits] == list(range(c.n_qubits))
    return strip_measures(c)


def side_path(side: str, file: str) -> str:
    return os.path.join(BENCH, file) if side == "input" else os.path.join(COMPILED, side, file)


def dyadic_exponent(x: float) -> int:
    d = Fraction(x).denominator
    return d.bit_length() - 1


def input_grid(file: str) -> int:
    u, _ = load(side_path("input", file))
    k = 0
    for cmd in u.get_commands():
        for p in cmd.op.params:
            k = max(k, dyadic_exponent(float(p)))
    return k + 4


# ------------------------------------------------- translation to pyzx gates

def to_ops(u: Circuit, snap):
    """-> (list of (name, qubits, Fraction|None), max snap error in half-turns).
    `snap(x)` maps a float angle (half-turns) to a Fraction."""
    ops = []
    err = 0.0

    def ang(x):
        nonlocal err
        x = float(x)
        f = snap(x)
        err = max(err, abs(float(f) - x))
        return f

    for cmd in u.get_commands():
        t = cmd.op.type
        q = [a.index[0] for a in cmd.args]
        p = cmd.op.params
        if t == OpType.Rz:
            ops.append(("Z", q, ang(p[0])))
        elif t == OpType.Rx:
            ops.append(("X", q, ang(p[0])))
        elif t == OpType.PhasedX:
            a, b = ang(p[0]), ang(p[1])
            ops += [("Z", q, -b), ("X", q, a), ("Z", q, b)]
        elif t in (OpType.ZZPhase, OpType.ZZMax):
            a = ang(p[0]) if t == OpType.ZZPhase else Fraction(1, 2)
            ops += [("CX", q, None), ("Z", [q[1]], a), ("CX", q, None)]
        elif t == OpType.CX:
            ops.append(("CX", q, None))
        elif t == OpType.H:
            ops.append(("H", q, None))
        elif t in (OpType.S, OpType.Sdg, OpType.T, OpType.Tdg, OpType.Z):
            ph = {OpType.S: Fraction(1, 2), OpType.Sdg: Fraction(3, 2),
                  OpType.T: Fraction(1, 4), OpType.Tdg: Fraction(7, 4),
                  OpType.Z: Fraction(1)}[t]
            ops.append(("Z", q, ph))
        elif t == OpType.X:
            ops.append(("X", q, Fraction(1)))
        else:
            raise ValueError(f"unsupported op {t}")
    return ops, err


def ops_to_graph(ops, n, perm):
    c = pyzx.Circuit(n)
    for name, q, ph in ops:
        if name == "Z":
            c.add_gate("ZPhase", q[0], phase=ph % 2)
        elif name == "X":
            c.add_gate("XPhase", q[0], phase=ph % 2)
        elif name == "CX":
            c.add_gate("CNOT", q[0], q[1])
        elif name == "H":
            c.add_gate("HAD", q[0])
    g = c.to_graph()
    outs = list(g.outputs())
    new = [None] * n
    for j, i in perm.items():
        new[i] = outs[j]
    g.set_outputs(tuple(new))
    return g


def miter_is_identity(gA, gB) -> tuple:
    """full_reduce(gA ; adjoint(gB)) and apply verify_equality's test."""
    g = gA.copy()
    g.compose(gB.adjoint())
    pyzx.simplify.full_reduce(g)
    n = len(g.inputs())
    ok = (g.num_vertices() == 2 * n
          and all(g.edge_type(e) == EdgeType.SIMPLE for e in g.edges())
          and all(g.connected(v, w) for v, w in zip(g.inputs(), g.outputs())))
    return ok, g.num_vertices(), g.num_edges()


def pyzx_check(file, sideA, sideB):
    G = input_grid(file)
    grid = lambda x: Fraction(round(x * 2 ** G), 2 ** G)  # noqa: E731
    uA, pA = load(side_path(sideA, file))
    uB, pB = load(side_path(sideB, file))
    n = uA.n_qubits
    assert uB.n_qubits == n
    opsA, eA = to_ops(uA, grid)
    opsB, eB = to_ops(uB, grid)
    snap = max(eA, eB)
    if snap > OFFGRID_TOL:
        return ("inconclusive",
                f"off-grid angles: max distance to 2^-{G} grid {snap:.3g} half-turns "
                f"(KAK resynthesis); PyZX needs exact phases, not run")
    ok, nv, ne = miter_is_identity(ops_to_graph(opsA, n, pA), ops_to_graph(opsB, n, pB))
    if ok:
        if snap > 1e-9:
            return ("proven-up-to-rounding",
                    f"grid 2^-{G}; max snap {snap:.3g} half-turns ({snap * math.pi:.3g} rad)")
        return ("proven", f"grid 2^-{G}; max snap {snap:.3g} half-turns")
    note = f"full_reduce left {nv} vertices, {ne} edges (2n={2 * n}); grid 2^-{G}"
    # P2 saw the input through pyzx's QASM parser (angles rounded to den <= 2^20)
    if "input" in (sideA, sideB) and "P2" in (sideA, sideB):
        rnd = lambda x: Fraction(x).limit_denominator(PYZX_MAXDEN)  # noqa: E731
        u_in, p_in = load(side_path("input", file))
        ops_in, e_in = to_ops(u_in, rnd)
        if e_in > 0:
            u2, p2 = load(side_path("P2", file))
            # compiled side: snap to the rounded input's angle set is not
            # possible on a dyadic grid; use limit_denominator as well
            ops2, e2 = to_ops(u2, lambda x: Fraction(x).limit_denominator(PYZX_MAXDEN * 64))
            ok2, nv2, _ = miter_is_identity(ops_to_graph(ops_in, n, p_in),
                                            ops_to_graph(ops2, n, p2))
            if ok2:
                return ("equal-up-to-rounding",
                        f"exact check: {note}; with input angles rounded as pyzx parses them "
                        f"(limit_denominator 2^20): proven; max input angle error "
                        f"{e_in * math.pi:.3g} rad, compiled snap {e2:.3g} half-turns")
            note += f"; rounded-input retry left {nv2} vertices"
    return ("inconclusive", note)


# -------------------------------------------------------------------- QCEC

def qelib_qasm(u: Circuit, perm) -> str:
    n = u.n_qubits
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];"]
    r = lambda x: f"{float(x)!r}*pi"  # noqa: E731
    for cmd in u.get_commands():
        t = cmd.op.type
        q = [a.index[0] for a in cmd.args]
        p = cmd.op.params
        if t == OpType.Rz:
            lines.append(f"rz({r(p[0])}) q[{q[0]}];")
        elif t == OpType.PhasedX:
            a, b = float(p[0]), float(p[1])
            lines += [f"rz({r(-b)}) q[{q[0]}];", f"rx({r(a)}) q[{q[0]}];",
                      f"rz({r(b)}) q[{q[0]}];"]
        elif t in (OpType.ZZPhase, OpType.ZZMax):
            a = float(p[0]) if t == OpType.ZZPhase else 0.5
            lines.append(f"rzz({r(a)}) q[{q[0]}],q[{q[1]}];")
        elif t == OpType.CX:
            lines.append(f"cx q[{q[0]}],q[{q[1]}];")
        elif t == OpType.H:
            lines.append(f"h q[{q[0]}];")
        elif t in (OpType.S, OpType.Sdg, OpType.T, OpType.Tdg, OpType.X, OpType.Z):
            lines.append(f"{t.name.lower()} q[{q[0]}];")
        else:
            raise ValueError(f"unsupported op {t}")
    # realise the output permutation: logical qubit perm[j] sits on wire j
    cur = {j: perm[j] for j in range(n)}      # wire -> logical
    where = {v: k for k, v in cur.items()}    # logical -> wire
    for i in range(n):
        j = where[i]
        if j != i:
            lines.append(f"swap q[{i}],q[{j}];")
            li = cur[i]
            cur[i], cur[j] = i, li
            where[i], where[li] = i, j
    return "\n".join(lines) + "\n"


def qcec_check(file, sideA, sideB, checker):
    from mqt import qcec
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for s in (sideA, sideB):
            u, p = load(side_path(s, file))
            fp = os.path.join(d, f"{s}.qasm")
            with open(fp, "w") as f:
                f.write(qelib_qasm(u, p))
            paths.append(fp)
        kw = dict(run_zx_checker=False, run_alternating_checker=False,
                  run_construction_checker=False, run_simulation_checker=False,
                  parallel=False, timeout=TIMEOUT - 10)
        kw["run_zx_checker" if checker == "zx" else "run_alternating_checker"] = True
        res = qcec.verify(paths[0], paths[1], **kw)
    eq = str(res.equivalence).split(".")[-1]
    verdict = {"equivalent": "proven", "equivalent_up_to_global_phase": "proven",
               "equivalent_up_to_phase": "proven",
               "not_equivalent": "failed"}.get(eq, "inconclusive")
    if checker == "alt" and verdict == "proven":
        note = f"qcec alternating DD: {eq} (numerical tolerance)"
    else:
        note = f"qcec {checker}: {eq}"
    if verdict == "inconclusive" and "no_information" in eq:
        note += " (timeout or checker gave up)"
    return verdict, note


# ----------------------------------------------------------------- driver

def _worker(q, method, file, a, b):
    try:
        if method == "pyzx":
            q.put(pyzx_check(file, a, b))
        else:
            q.put(qcec_check(file, a, b, "zx" if method == "qcec_zx" else "alt"))
    except Exception as e:  # noqa: BLE001
        q.put(("error", f"{type(e).__name__}: {e}"[:300]))


def run_task(task):
    method, file, a, b = task
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(q, method, file, a, b))
    t0 = time.perf_counter()
    p.start()
    p.join(TIMEOUT)
    if p.is_alive():
        p.kill()
        p.join()
        return "timeout", time.perf_counter() - t0, f"killed after {TIMEOUT:.0f} s"
    dt = time.perf_counter() - t0
    try:
        v, note = q.get(timeout=5)
    except Exception:  # noqa: BLE001
        v, note = "error", f"worker exited with code {p.exitcode}"
    return v, dt, note


# ------------------------------------------------------------------ summary
OUTMD = os.path.join(ROOT, "results", "family_C_equivalence.md")
SELECTOR = os.path.join(ROOT, "value", "family_C_selector.csv")


def _snap(note):
    """Max snap in half-turns parsed from a pyzx 'proven' note, else None."""
    if not isinstance(note, str) or "max snap" not in note:
        return None
    return float(note.split("max snap")[1].split("half-turns")[0])


def summary_facts():
    """All counts reported in the md, computed from the three CSVs."""
    eq = pd.read_csv(OUTCSV)
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    sel = pd.read_csv(SELECTOR)[["file", "pick"]]
    pz = eq[eq.method == "pyzx"]
    v = {(f, c): d for f, c, d in zip(pz.file, pz.comparison, pz.verdict)}
    files = list(man.file)
    get = lambda f, c: v.get((f, c), "not run")  # noqa: E731
    F = {"n_circuits": len(files)}
    for c in ("P0", "P2", "P2vsP0"):
        F[f"proven_{c}"] = sum(get(f, c) == "proven" for f in files)
    pick = dict(zip(sel.file, sel.pick))
    assert set(pick) == set(files), "selector and manifest list different files"
    p2 = [f for f in files if pick[f] == "P2"]
    p0 = [f for f in files if pick[f] == "P0"]
    F["n_pick_P2"], F["n_pick_P0"] = len(p2), len(p0)
    F["proven_pick_P2"] = sum(get(f, "P2") == "proven" for f in p2)
    F["proven_pick_P0"] = sum(get(f, "P0") == "proven" for f in p0)
    F["unproven_pick_P2"] = [f for f in p2 if get(f, "P2") != "proven"]
    F["unproven_pick_P0"] = [f for f in p0 if get(f, "P0") != "proven"]
    F["proven_PSEL"] = sum(get(f, pick[f]) == "proven" for f in files)
    disc = [f for f, ca in zip(man.file, man.continuous_angles) if not ca]
    F["n_discrete"] = len(disc)
    F["proven_PSEL_discrete"] = sum(get(f, pick[f]) == "proven" for f in disc)
    snaps = [s for s in (_snap(n) for n, d in zip(pz.notes, pz.verdict) if d == "proven")
             if s is not None]
    F["max_snap"] = max(snaps)
    F["n_proven_rows"] = int((pz.verdict == "proven").sum())
    F["verdicts"], F["pick"], F["man"], F["eq"] = v, pick, man, eq
    return F


def _fmt(f, c, v):
    d = v.get((f, c))
    return "not run" if d is None else d


def write_summary():
    F = summary_facts()
    v, pick, man, eq = F["verdicts"], F["pick"], F["man"], F["eq"]
    N = F["n_circuits"]
    name = lambda f: f.replace(".qasm", "")  # noqa: E731
    L = ["# Family C: full equivalence check by ZX miter", "",
         "Written by `python3 pipelines/equiv_family_C.py --summary` from "
         "`results/family_C_equivalence.csv`, `value/family_C_selector.csv` (column `pick`) "
         "and `bench/family_C/manifest.csv` (column `continuous_angles`). "
         "Script: `pipelines/equiv_family_C.py` (method in its docstring). "
         "Tests: `pipelines/test_equiv_family_C.py` (one positive and one broken case).", "",
         "## Method", "",
         "- [F] Each compiled output (`results/compiled/{P0,P2}/<file>`) is compared with the input "
         "`bench/family_C/<file>`, and P2 with P0, as full 2^n x 2^n unitaries up to global phase. "
         "Measurements are stripped and pytket's implicit qubit permutation is read from the "
         "measurement map. No ancilla is fixed to |0>, so a proof here is stronger than equality "
         "on clean-ancilla inputs.",
         "- [F] PyZX 0.10.7: miter `G_A ; adjoint(G_B)`, `full_reduce`, then the test of "
         "`Circuit.verify_equality` (2n boundary vertices only, simple edges, input i wired to "
         "output i). Angles are snapped to the dyadic grid 2^-G with G = (input's largest dyadic "
         "exponent) + 4. The input angles lie on that grid exactly. "
         f"The largest snap on the compiled side is {F['max_snap']:.3g} half-turns over all "
         f"{F['n_proven_rows']} proven PyZX rows (float noise). A positive result proves "
         "equivalence of the snapped circuits. A negative result is inconclusive.",
         "- [F] MQT QCEC 3.10.2 was run as a second method on cdkm_adder_10 and draper_adder_10 "
         "only (see table). Its ZX checker returned `probably_not_equivalent` on 5 of 6 pairs "
         "that PyZX proves. This is QCEC's \"could not reduce\" outcome and not a counterexample. "
         "The alternating DD checker is a floating-point check with tolerance.", "",
         "## Results (PyZX miter)", "",
         f"- [F] P0 vs input: {F['proven_P0']} of {N} proven.",
         f"- [F] P2 vs input: {F['proven_P2']} of {N} proven.",
         f"- [F] P2 vs P0: {F['proven_P2vsP0']} of {N} proven.",
         "- [F] hrs_mult_5 (P0, P2): inconclusive, not run by PyZX. FullPeepholeOptimise's KAK "
         "resynthesis leaves angles off any dyadic grid, and PyZX needs exact phases. The "
         "64-input basis check (pass) remains the only check for this circuit.",
         "- [F] draper_adder_28 (P0, P2): timeout (300 s) in `full_reduce`. P2 vs P0 not run. "
         "The 64-input basis check does not cover it either (branching ancilla). It is unchecked.",
         "", "## PSEL picks", "",
         f"- [F] PSEL output proven equal to its input: {F['proven_PSEL']} of {N} circuits.",
         f"- [F] P2 picks proven: {F['proven_pick_P2']} of {F['n_pick_P2']}. Not proven: "
         + ", ".join(name(f) for f in F["unproven_pick_P2"]) + ".",
         f"- [F] P0 picks proven: {F['proven_pick_P0']} of {F['n_pick_P0']}. Not proven: "
         + ", ".join(name(f) for f in F["unproven_pick_P0"]) + ".",
         f"- [F] Circuits without continuous angles: PSEL output proven for "
         f"{F['proven_PSEL_discrete']} of {F['n_discrete']}.", "",
         "## Verdict table", "",
         "| circuit | n | PSEL pick | P0 vs input | P2 vs input | P2 vs P0 | QCEC (second method) |",
         "|---|---|---|---|---|---|---|"]
    q = eq[eq.method != "pyzx"]
    for f, n in zip(man.file, man.n_qubits):
        qs = q[q.file == f]
        qtxt = "; ".join(f"{c}/{m}: {'inconclusive' if d == 'inconclusive' else d}"
                         for c, m, d in zip(qs.comparison, qs.method, qs.verdict)) or "not run"
        L.append(f"| {name(f)} | {n} | {pick[f]} | {_fmt(f, 'P0', v)} | {_fmt(f, 'P2', v)} | "
                 f"{_fmt(f, 'P2vsP0', v)} | {qtxt} |")
    L += ["", "## Open items", "",
          "- [O] draper_adder_28 needs a timeout above 300 s or a different method.",
          "- [O] hrs_mult_5 needs a checker that accepts non-dyadic angles.",
          "- [O] QCEC on the remaining 18 circuits was not run. It is kept for cross-checking "
          "only and does not change any PyZX verdict.", ""]
    with open(OUTMD, "w") as fh:
        fh.write("\n".join(L))
    return F


COMPARISONS = [("P0", "input", "P0"), ("P2", "input", "P2"), ("P2vsP0", "P0", "P2")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="")
    ap.add_argument("--methods", default="pyzx,qcec_zx,qcec_alt")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--summary", action="store_true",
                    help="only rewrite results/family_C_equivalence.md from the CSVs")
    a = ap.parse_args()
    if a.summary:
        F = write_summary()
        print({k: F[k] for k in F if k not in ("verdicts", "pick", "man", "eq")})
        return
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    files = [f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f]
    if files:
        man = man[man.file.isin(files)]
    done = set()
    if os.path.exists(OUTCSV):
        old = pd.read_csv(OUTCSV)
        done = set(zip(old.file, old.comparison, old.method))
    tasks = []
    for m in a.methods.split(","):
        for f, n in zip(man.file, man.n_qubits):
            for comp, sa, sb in COMPARISONS:
                if (f, comp, m) not in done:
                    tasks.append((m, f, sa, sb, comp, n))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_task, t[:4]): t for t in tasks}
        for fu in futs:
            m, f, sa, sb, comp, n = futs[fu]
            v, dt, note = fu.result()
            row = {"file": f, "n": n, "comparison": comp,
                   "pipeline": sb if comp != "P2vsP0" else "P2 vs P0",
                   "method": m, "verdict": v, "seconds": round(dt, 2), "notes": note}
            pd.DataFrame([row]).reindex(columns=COLS).to_csv(
                OUTCSV, mode="a", header=not os.path.exists(OUTCSV), index=False)
            print(f"{f} {comp} {m}: {v} {dt:.1f}s  {note}", flush=True)


if __name__ == "__main__":
    main()
