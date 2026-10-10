"""Why the ZX stage (PyZX teleport_reduce) adds little on top of pytket level 3.

Hypothesis under test: pytket-quantinuum optimisation level 3 runs GreedyPauliSimp,
which resynthesises the circuit from Pauli gadgets with phase folding, so it already
merges the phases that PyZX phase teleportation merges, and the two-qubit and
non-Clifford rotation counts after L3 already match or beat P2.

Circuits: the 180 family A, 15 B1 and 20 family C circuits of value/psel4_ledger.csv.
Pipelines (all end in the H2 native set Rz, PhasedX, ZZPhase, ZZMax):
  IN       compile.P0ref (rebase + squash only), the input in the native gate set
  L2       optimisation level 2 (= P0). Stored QASM results/compiled/P0/<file> is reused
           when its HQC equals hqc_P0 of the ledger, else recompiled.
  P2       teleport_reduce then level 2. Stored results/compiled/P2/<file> reused on the
           same rule, else recompiled.
  L3       optimisation level 3 (strong_baselines.compile_variant), recompiled. With
           run --use-stored, results/compiled/L3/<file> is read when its HQC equals
           hqc_L3 of the ledger (used for jobs that timed out under CPU contention).
  P2L3     teleport_reduce then level 3, recompiled (same --use-stored rule).
  L3noGPS  the level 3 pass list with GreedyPauliSimp removed. GreedyPauliSimp runs
           with only_reduce=True, so it is kept only when it lowers the two-qubit
           count. gps_used(L3) = n_2q(L3) < n_2q(L3noGPS).
  P2L3noGPS  the same on the teleport_reduce output.
Per row: n_2q, n_1q (PhasedX), n_rz, and the number of non-Clifford rotations:
  Rz(a), ZZPhase(a) non-Clifford iff a (half-turns) is not a multiple of 1/2.
  PhasedX(a, b) Clifford iff a = 0 mod 2, or a = 1 mod 2 and b = 0 mod 1/4, or
  a = 1/2 mod 1 and b = 0 mod 1/2.
Input columns: T-count and non-Clifford count (phase not a multiple of pi/2) of the
input read by PyZX (to_basic_gates), and the same after teleport_reduce (the ZX stage
of P2, compile.zx_teleport_reduce_pz).
HQC = 5 + (N_1q + 10 N_2q + 5 * 2n) / 5 at 1000 shots (compile.hqc, n_measure = n).

Usage
  python3 value/mechanism_zx_l3.py run [--workers 2] [--timeout 300]   (only missing rows)
  python3 value/mechanism_zx_l3.py report
Writes value/mechanism_zx_l3.csv (run) and value/mechanism_zx_l3.md (report).
"""
import argparse
import math
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
sys.path.insert(0, str(ROOT / "value"))
import strong_baselines as SB  # noqa: E402  (patches compile._tket_to_pyzx for sci-notation angles)
import compile as C  # noqa: E402
from pytket import OpType  # noqa: E402
from pytket.passes import (AutoRebase, AutoSquash, DecomposeBoxes, DecomposeTK2,  # noqa: E402
                           FlattenRelabelRegistersPass, NormaliseTK2, RemoveBarriers,
                           RemovePhaseOps, RemoveRedundancies, SequencePass)
from pytket.qasm import circuit_from_qasm  # noqa: E402

OUT_CSV = ROOT / "value/mechanism_zx_l3.csv"
OUT_MD = ROOT / "value/mechanism_zx_l3.md"
LEDGER = ROOT / "value/psel4_ledger.csv"
DIRS = {"A": ROOT / "bench/family_A", "B1": ROOT / "bench/family_B1",
        "C": ROOT / "bench/family_C"}
STORED = {"L2": ("P0", "hqc_P0"), "P2": ("P2", "hqc_P2")}
HEAVY = ["L3", "P2L3"]
PIPES = ["IN", "L2", "P2", "L3", "P2L3", "L3noGPS", "P2L3noGPS"]
TOL = 1e-6


# ----------------------------------------------------------------- counting

def _is_mult(x: float, m: float) -> bool:
    r = math.fmod(float(x), m)
    if r < 0:
        r += m
    return min(r, m - r) < TOL


def px_is_clifford(a: float, b: float) -> bool:
    if _is_mult(a, 2.0):
        return True
    if _is_mult(a - 1.0, 2.0):
        return _is_mult(b, 0.25)
    if _is_mult(a - 0.5, 1.0):
        return _is_mult(b, 0.5)
    return False


def native_counts(comp) -> dict:
    n2 = n1 = nrz = ncrz = nczz = ncpx = 0
    other = set()
    for cmd in comp.get_commands():
        t, p = cmd.op.type, cmd.op.params
        if t == OpType.Rz:
            nrz += 1
            ncrz += not _is_mult(p[0], 0.5)
        elif t == OpType.ZZPhase:
            n2 += 1
            nczz += not _is_mult(p[0], 0.5)
        elif t == OpType.ZZMax:
            n2 += 1
        elif t == OpType.PhasedX:
            n1 += 1
            ncpx += not px_is_clifford(p[0], p[1])
        elif t not in (OpType.Measure, OpType.Barrier, OpType.Reset):
            other.add(t.name)
    n = comp.n_qubits
    return {"n_qubits": n, "n_2q": n2, "n_1q": n1, "n_rz": nrz, "nc_rz": ncrz,
            "nc_zz": nczz, "nc_px": ncpx, "nc_total": ncrz + nczz + ncpx,
            "hqc": 5 + (n1 + 10 * n2 + 5 * 2 * n) * C.SHOTS / 5000,
            "non_native": ",".join(sorted(other))}


def pz_counts(pz) -> tuple:
    """(T-count, non-Clifford count) of a pyzx circuit: phases with denominator 4,
    and phases not a multiple of 1/2 (units of pi)."""
    t = nc = 0
    for g in pz.gates:
        if isinstance(g, (C.pyzx.circuit.gates.ZPhase, C.pyzx.circuit.gates.XPhase)):
            d = (Fraction(g.phase) % 2).denominator
            t += d == 4
            nc += d > 2
    return t, nc


# ----------------------------------------------------------------- passes

def l3_no_gps_pass():
    """pytket-quantinuum 0.59.3 default_compilation_pass level-3 branch (quantinuum.py
    lines 622-668) with the GreedyPauliSimp entry removed."""
    rebase = AutoRebase({OpType.Rz, OpType.PhasedX, OpType.ZZPhase, OpType.Measure,
                         OpType.Reset, OpType.Barrier}, allow_swaps=True)
    pre = AutoRebase({OpType.Z, OpType.X, OpType.Y, OpType.S, OpType.Sdg, OpType.V,
                      OpType.Vdg, OpType.H, OpType.CX, OpType.CY, OpType.CZ, OpType.SWAP,
                      OpType.Rz, OpType.Rx, OpType.Ry, OpType.T, OpType.Tdg, OpType.ZZMax,
                      OpType.ZZPhase, OpType.XXPhase, OpType.YYPhase, OpType.PhasedX})
    return SequencePass([
        DecomposeBoxes(), RemoveBarriers(), pre,
        NormaliseTK2(), DecomposeTK2(allow_swaps=True, ZZPhase_fidelity=1.0),
        rebase, RemoveRedundancies(), AutoSquash({OpType.PhasedX, OpType.Rz}),
        RemoveRedundancies(), RemovePhaseOps(), FlattenRelabelRegistersPass("q")])


# ----------------------------------------------------------------- jobs

def ledger() -> pd.DataFrame:
    d = pd.read_csv(LEDGER)
    return d[d.family.isin(list(DIRS))].reset_index(drop=True)


def _row(fam, file, pipe, comp, source, t):
    r = {"family": fam, "file": file, "pipeline": pipe, "status": "ok", "source": source,
         "t_compile": t}
    r.update(native_counts(comp))
    return r


def job_light(fam, file, hqc_ref):
    """IN, L2/P2 (stored if HQC matches), noGPS variants, input and teleport counts."""
    circ = circuit_from_qasm(str(DIRS[fam] / file))
    rows = []
    t0 = time.perf_counter()
    pz = C._tket_to_pyzx(circ).to_basic_gates()
    t_in, nc_in = pz_counts(pz)
    pzt = C.zx_teleport_reduce_pz(circ)
    t_tr, nc_tr = pz_counts(pzt)
    tr = C._pyzx_to_tket(pzt)
    inp = {"n_gates_in": circ.n_gates, "n_2q_in": circ.n_2qb_gates(), "t_in": t_in,
           "nc_in": nc_in, "t_tr": t_tr, "nc_tr": nc_tr,
           "t_teleport": time.perf_counter() - t0}
    t0 = time.perf_counter()
    ref, _ = C.compile_pipeline("P0ref", circ)
    rows.append(_row(fam, file, "IN", ref, "compiled", time.perf_counter() - t0))
    for pipe, (sub, col) in STORED.items():
        f = ROOT / "results/compiled" / sub / file
        ok = False
        if f.exists():
            comp = circuit_from_qasm(str(f), maxwidth=64)
            r = _row(fam, file, pipe, comp, "stored", float("nan"))
            ok = abs(r["hqc"] - hqc_ref[col]) < 1e-6
        if not ok:
            t0 = time.perf_counter()
            comp, _ = C.compile_pipeline("P0" if pipe == "L2" else "P2", circ)
            r = _row(fam, file, pipe, comp, "recompiled", time.perf_counter() - t0)
        rows.append(r)
    for pipe, c in (("L3noGPS", circ), ("P2L3noGPS", tr)):
        c = c.copy()
        t0 = time.perf_counter()
        l3_no_gps_pass().apply(c)
        rows.append(_row(fam, file, pipe, c, "compiled", time.perf_counter() - t0))
    for r in rows:
        r.update(inp)
    return rows


def job_heavy(fam, file, pipe, hqc_ref=None, use_stored=False):
    """Recompile L3 / P2L3.  With use_stored, a results/compiled/<pipe>/<file> whose HQC
    equals the ledger value hqc_ref is read instead (fallback for jobs that timed out
    under CPU contention)."""
    f = ROOT / "results/compiled" / pipe / file
    if use_stored and hqc_ref is not None and f.exists():
        r = _row(fam, file, pipe, circuit_from_qasm(str(f), maxwidth=64), "stored", float("nan"))
        if abs(r["hqc"] - hqc_ref) < 1e-6:
            return [r]
    circ = circuit_from_qasm(str(DIRS[fam] / file))
    comp, tm = SB.compile_variant(pipe, circ)
    return [_row(fam, file, pipe, comp, "recompiled", tm["t_total"])]


def _child(args, conn):
    try:
        kind = args[0]
        conn.send(job_light(*args[1:]) if kind == "light" else job_heavy(*args[1:]))
    except Exception as e:  # noqa: BLE001
        conn.send([{"family": args[1], "file": args[2],
                    "pipeline": "LIGHT" if args[0] == "light" else args[3],
                    "status": "error", "error": repr(e)[:300]}])


def run_with_timeout(job):
    args, timeout = job
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=(args, child))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(timeout):
        rows = parent.recv()
    else:
        p.kill()
        rows = [{"family": args[1], "file": args[2],
                 "pipeline": "LIGHT" if args[0] == "light" else args[3],
                 "status": "timeout"}]
    p.join()
    for r in rows:
        r["t_wall_job"] = time.perf_counter() - t0
        r["timeout_s"] = timeout
    return rows


def cmd_run(a):
    SB.backend()
    led = ledger()
    have = pd.read_csv(OUT_CSV) if OUT_CSV.exists() else pd.DataFrame(
        columns=["family", "file", "pipeline", "status"])
    done = {(r.family, r.file, r.pipeline) for r in have.itertuples() if r.status == "ok"}
    jobs = []
    want = {f for f in a.files.split(",") if f}
    for r in led.itertuples():
        if want and r.file not in want:
            continue
        size = os.path.getsize(DIRS[r.family] / r.file)
        if not all((r.family, r.file, p) in done for p in ["IN", "L2", "P2", "L3noGPS", "P2L3noGPS"]):
            jobs.append((size, (("light", r.family, r.file,
                                 {"hqc_P0": r.hqc_P0, "hqc_P2": r.hqc_P2}), a.timeout)))
        for p in HEAVY:
            if (r.family, r.file, p) not in done:
                ref = r.hqc_L3 if p == "L3" else r.hqc_P2L3
                jobs.append((size, (("heavy", r.family, r.file, p, ref, a.use_stored),
                                    a.timeout)))
    # smallest first, so a time-limited run completes the most circuits
    jobs = [j for _, j in sorted(jobs, key=lambda x: x[0])]
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    rows, t0 = [], time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, rs in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.extend(rs)
            r = rs[0]
            print(f"{i + 1}/{len(jobs)} {r['family']} {r['file']} {r['pipeline']} "
                  f"{r['status']} [{time.perf_counter() - t0:.0f}s]", flush=True)
            if (i + 1) % 20 == 0 or i + 1 == len(jobs):
                _merge_write(have, rows)
    _merge_write(have, rows)


def _merge_write(have, rows):
    new = pd.DataFrame(rows)
    if len(have):
        key = set(zip(new.family, new.file, new.pipeline))
        # a failed light job is stored as pipeline LIGHT, drop it once IN is rewritten
        fk = {(f, fi) for f, fi, p in key if p == "IN"}
        old = have[[(r.family, r.file, r.pipeline) not in key
                    and not (r.pipeline == "LIGHT" and (r.family, r.file) in fk)
                    for r in have.itertuples()]]
        new = pd.concat([old, new], ignore_index=True)
    # input columns are written on the light rows only, copy them to every row
    inc = ["n_gates_in", "n_2q_in", "t_in", "nc_in", "t_tr", "nc_tr"]
    if all(c in new for c in inc):
        src = new.dropna(subset=["t_in"]).drop_duplicates(["family", "file"])[["family", "file"] + inc]
        new = new.drop(columns=inc + (["t_teleport"] if "t_teleport" in new else []),
                       errors="ignore").merge(src, on=["family", "file"], how="left")
    new.sort_values(["family", "file", "pipeline"]).to_csv(OUT_CSV, index=False)


# ----------------------------------------------------------------- analysis

def load():
    d = pd.read_csv(OUT_CSV)
    d = d[d.status == "ok"]
    led = ledger()
    w = led[["family", "file", "hqc_P0", "hqc_P2", "hqc_L3", "hqc_P2L3", "hqc_PSEL4",
             "pick_PSEL4", "status_P2L3"]].copy()
    w.columns = ["family", "file", "led_P0", "led_P2", "led_L3", "led_P2L3", "led_PSEL4",
                 "pick_PSEL4", "led_status_P2L3"]
    for col in ["n_2q", "n_1q", "n_rz", "nc_total", "nc_rz", "nc_zz", "nc_px", "hqc"]:
        p = d.pivot_table(index=["family", "file"], columns="pipeline", values=col,
                          aggfunc="first")
        p.columns = [f"{col}_{c}" for c in p.columns]
        w = w.merge(p.reset_index(), on=["family", "file"], how="left")
    inp = d.drop_duplicates(["family", "file"])[["family", "file", "n_gates_in", "n_2q_in",
                                                  "t_in", "nc_in", "t_tr", "nc_tr"]]
    w = w.merge(inp, on=["family", "file"], how="left")
    src = d[d.pipeline.isin(["L2", "P2"])].pivot_table(index=["family", "file"],
                                                       columns="pipeline", values="source",
                                                       aggfunc="first")
    src.columns = [f"src_{c}" for c in src.columns]
    w = w.merge(src.reset_index(), on=["family", "file"], how="left")
    try:
        import psel4_proven
        v = psel4_proven.verdicts()
        w["proven_C"] = [fam == "C" and v.get((f, p)) == "proven"
                         for fam, f, p in zip(w.family, w.file, w.pick_PSEL4)]
    except Exception:  # noqa: BLE001
        w["proven_C"] = False
    w["min_L2_L3"] = w[["led_P0", "led_L3"]].min(axis=1)
    w["zx_gain"] = w["min_L2_L3"] - w["led_PSEL4"]
    w["zx_gain_pct"] = 100 * w["zx_gain"] / w["min_L2_L3"]
    w["t_density"] = w["t_in"] / w["n_gates_in"]
    w["nc_density"] = w["nc_in"] / w["n_gates_in"]
    w["gps_L3"] = w["n_2q_L3"] < w["n_2q_L3noGPS"]
    w["gps_P2L3"] = w["n_2q_P2L3"] < w["n_2q_P2L3noGPS"]
    return d, w


def groups(w):
    return [("A", w[w.family == "A"]), ("B1", w[w.family == "B1"]),
            ("C", w[w.family == "C"]), ("C17", w[(w.family == "C") & w.proven_C])]


def dsplit(x, a, b):
    """HQC difference a - b split into 2q part (2 per gate) and 1q part (0.2 per gate)."""
    d2 = (x[f"n_2q_{a}"] - x[f"n_2q_{b}"]).sum()
    d1 = (x[f"n_1q_{a}"] - x[f"n_1q_{b}"]).sum()
    return {"n": len(x), "dhqc": (x[f"hqc_{a}"] - x[f"hqc_{b}"]).sum(), "d2q": d2,
            "d1q": d1, "dhqc_2q": 2 * d2, "dhqc_1q": 0.2 * d1,
            "dnc": (x[f"nc_total_{a}"] - x[f"nc_total_{b}"]).sum()}


def compute():
    d, w = load()
    out = {"w": w, "d": d}
    # consistency with the ledger
    cons = {}
    for p, col in [("L2", "led_P0"), ("P2", "led_P2"), ("L3", "led_L3"), ("P2L3", "led_P2L3")]:
        m = w[f"hqc_{p}"].notna() & w[col].notna()
        cons[p] = {"n": int(m.sum()),
                   "match": int(((w.loc[m, f"hqc_{p}"] - w.loc[m, col]).abs() < 1e-6).sum()),
                   "missing": int(w[f"hqc_{p}"].isna().sum())}
    out["cons"] = cons
    out["src"] = {p: w[f"src_{p}"].value_counts().to_dict() for p in ["L2", "P2"]}
    pipes = ["IN", "L2", "P2", "L3", "P2L3"]
    fam = {}
    for name, x in groups(w):
        full = x.dropna(subset=[f"hqc_{p}" for p in pipes])
        r = {"n": len(x), "n_full": len(full)}
        for p in pipes:
            for c in ["n_2q", "n_1q", "nc_total", "hqc"]:
                r[f"{c}_{p}"] = full[f"{c}_{p}"].sum()
        for c in ["t_in", "t_tr", "nc_in", "nc_tr"]:
            r[c] = full[c].sum()
        r["t_red_pct"] = 100 * (r["t_in"] - r["t_tr"]) / r["t_in"] if r["t_in"] else float("nan")
        r["nctr_red_pct"] = 100 * (r["nc_in"] - r["nc_tr"]) / r["nc_in"] if r["nc_in"] else float("nan")
        for p in ["L2", "P2", "L3", "P2L3"]:
            base = r["nc_total_IN"]
            r[f"ncred_{p}"] = 100 * (base - r[f"nc_total_{p}"]) / base if base else float("nan")
        # Q1 per circuit: non-Clifford count L3 vs P2
        r["q1_L3_lt_P2"] = int((full.nc_total_L3 < full.nc_total_P2).sum())
        r["q1_L3_eq_P2"] = int((full.nc_total_L3 == full.nc_total_P2).sum())
        r["q1_L3_gt_P2"] = int((full.nc_total_L3 > full.nc_total_P2).sum())
        r["q1_P2L3_lt_L3"] = int((full.nc_total_P2L3 < full.nc_total_L3).sum())
        r["q1_P2L3_gt_L3"] = int((full.nc_total_P2L3 > full.nc_total_L3).sum())
        r["q1_2q_L3_le_P2"] = int((full.n_2q_L3 <= full.n_2q_P2).sum())
        r["gps_L3"] = int(full.gps_L3.sum())
        r["gps_P2L3"] = int(full.gps_P2L3.sum())
        # Q2 / Q3
        r["q2"] = dsplit(full[full.hqc_P2L3 < full.hqc_L3 - 1e-9], "L3", "P2L3")
        r["q2_rev"] = dsplit(full[full.hqc_P2L3 > full.hqc_L3 + 1e-9], "P2L3", "L3")
        r["q3"] = dsplit(full[full.hqc_L3 < full.hqc_P2 - 1e-9], "P2", "L3")
        r["q3_rev"] = dsplit(full[full.hqc_L3 > full.hqc_P2 + 1e-9], "L3", "P2")
        # ZX-only gain (ledger)
        r["zx_gain"] = x.zx_gain.sum()
        r["zx_gain_pct"] = 100 * x.zx_gain.sum() / x.min_L2_L3.sum()
        r["zx_gain_circuits"] = int((x.zx_gain > 1e-9).sum())
        fam[name] = r
    out["fam"] = fam
    # Q4 correlation over B1 + C
    from scipy.stats import spearmanr
    q4 = {}
    bc = w[w.family.isin(["B1", "C"])].dropna(subset=["t_density", "zx_gain_pct"])
    for name, x in [("B1+C", bc), ("B1", bc[bc.family == "B1"]), ("C", bc[bc.family == "C"])]:
        rho, p = spearmanr(x.t_density, x.zx_gain_pct)
        rho2, p2 = spearmanr(x.nc_density, x.zx_gain_pct)
        q4[name] = {"n": len(x), "rho_t": rho, "p_t": p, "rho_nc": rho2, "p_nc": p2,
                    "mean_gain_pct": x.zx_gain_pct.mean(),
                    "median_t_density": x.t_density.median()}
    hi = bc[bc.t_density >= bc.t_density.median()]
    lo = bc[bc.t_density < bc.t_density.median()]
    q4["split"] = {"median": bc.t_density.median(), "n_hi": len(hi), "n_lo": len(lo),
                   "gain_hi_pct": 100 * hi.zx_gain.sum() / hi.min_L2_L3.sum(),
                   "gain_lo_pct": 100 * lo.zx_gain.sum() / lo.min_L2_L3.sum(),
                   "nz_hi": int((hi.zx_gain > 1e-9).sum()),
                   "nz_lo": int((lo.zx_gain > 1e-9).sum())}
    out["q4"] = q4
    return out


def f1(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1f}"


def f2(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}"


def cmd_report(_a):
    o = compute()
    w, fam, q4 = o["w"], o["fam"], o["q4"]
    L = ["# Mechanism: why teleport_reduce adds little on top of pytket level 3", "",
         "Generated by `python3 value/mechanism_zx_l3.py report` from "
         "`value/mechanism_zx_l3.csv` (one row per circuit and pipeline) and "
         "`value/psel4_ledger.csv` (HQC of L2, L3, PSEL4 for the ZX-only gain). "
         "Definitions are in the docstring of `value/mechanism_zx_l3.py`. "
         "Non-Clifford rotation = Rz or ZZPhase angle not a multiple of pi/2, or a "
         "non-Clifford PhasedX. T-count = phases that are odd multiples of pi/4 in the "
         "PyZX reading of the circuit. HQC at 1000 shots. Family C17 = the 17 family C "
         "circuits whose PSEL4 output is proven equivalent (value/psel4_proven.py). "
         "pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7.", ""]
    L += ["## Sources and consistency", ""]
    for p, c in o["cons"].items():
        L.append(f"- {p}: HQC equals the ledger on {c['match']} of {c['n']} circuits, "
                 f"missing rows {c['missing']}.")
    for p, s in o["src"].items():
        L.append(f"- {p} source: " + ", ".join(f"{k} {v}" for k, v in sorted(s.items())) + ".")
    bad = o["d"]
    L.append("")
    raw = pd.read_csv(OUT_CSV)
    nok = raw[raw.status != "ok"]
    if len(nok):
        L.append("Rows not ok: " + ", ".join(f"{r.family} `{r.file}` {r.pipeline} {r.status}"
                                             for r in nok.itertuples()) + ".")
    else:
        L.append("All rows ok.")
    L.append("")

    L += ["## Totals per family (circuits with all five pipelines)", "",
          "| Set | Circuits | Pipeline | n_2q | n_1q (PhasedX) | non-Clifford rotations | "
          "non-Clifford reduced vs IN % | HQC |", "|---|---|---|---|---|---|---|---|"]
    for name, r in fam.items():
        for p in ["IN", "L2", "P2", "L3", "P2L3"]:
            red = "" if p == "IN" else f2(r[f"ncred_{p}"])
            L.append(f"| {name} | {r['n_full']} | {p} | {r[f'n_2q_{p}']:.0f} | "
                     f"{r[f'n_1q_{p}']:.0f} | {r[f'nc_total_{p}']:.0f} | {red} | "
                     f"{r[f'hqc_{p}']:.1f} |")
    L.append("")
    L += ["## Input T-count and teleport_reduce (PyZX reading)", "",
          "| Set | T-count input | T-count after teleport_reduce | T reduced % | "
          "non-Clifford input | non-Clifford after teleport_reduce | reduced % |",
          "|---|---|---|---|---|---|---|"]
    for name, r in fam.items():
        L.append(f"| {name} | {r['t_in']:.0f} | {r['t_tr']:.0f} | {f2(r['t_red_pct'])} | "
                 f"{r['nc_in']:.0f} | {r['nc_tr']:.0f} | {f2(r['nctr_red_pct'])} |")
    L.append("")
    L += ["## Q1. Does L3 cut non-Clifford rotations as far as teleport_reduce (P2)?", "",
          "| Set | Circuits | L3 < P2 | L3 = P2 | L3 > P2 | P2L3 < L3 | P2L3 > L3 | "
          "n_2q L3 <= P2 | GreedyPauliSimp kept in L3 | kept in P2L3 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in fam.items():
        L.append(f"| {name} | {r['n_full']} | {r['q1_L3_lt_P2']} | {r['q1_L3_eq_P2']} | "
                 f"{r['q1_L3_gt_P2']} | {r['q1_P2L3_lt_L3']} | {r['q1_P2L3_gt_L3']} | "
                 f"{r['q1_2q_L3_le_P2']} | {r['gps_L3']} | {r['gps_P2L3']} |")
    L += ["", "Counts are per circuit, non-Clifford rotations unless the column says n_2q. "
          "GreedyPauliSimp kept = n_2q after level 3 is below n_2q of the same pass list "
          "without GreedyPauliSimp (only_reduce=True discards it otherwise).", ""]

    def qtab(title, key, a, b):
        L.extend([title, "", "| Set | Circuits | HQC gap | from n_2q (2 per gate) | "
                  f"from n_1q (0.2 per gate) | n_2q gap | n_1q gap | non-Clifford gap |",
                  "|---|---|---|---|---|---|---|---|"])
        for name, r in fam.items():
            q = r[key]
            L.append(f"| {name} | {q['n']} | {q['dhqc']:.1f} | {q['dhqc_2q']:.1f} | "
                     f"{q['dhqc_1q']:.1f} | {q['d2q']:.0f} | {q['d1q']:.0f} | {q['dnc']:.0f} |")
        L.append(f"\nGaps are {a} minus {b}, summed over the circuits of the row.\n")

    qtab("## Q2. Circuits where P2L3 beats L3", "q2", "L3", "P2L3")
    qtab("### Q2 converse. Circuits where L3 beats P2L3", "q2_rev", "P2L3", "L3")
    qtab("## Q3. Circuits where L3 beats P2", "q3", "P2", "L3")
    qtab("### Q3 converse. Circuits where P2 beats L3", "q3_rev", "L3", "P2")

    L += ["## Q4. ZX-only gain against T-density and family", "",
          "ZX-only gain per circuit = min(L2, L3) - PSEL4 (HQC, ledger values). "
          "T-density = input T-count / input gate count.", "",
          "| Set | Circuits | ZX-only gain HQC | ZX-only gain % | circuits with gain > 0 |",
          "|---|---|---|---|---|"]
    for name, r in fam.items():
        L.append(f"| {name} | {r['n']} | {r['zx_gain']:.1f} | {f2(r['zx_gain_pct'])} | "
                 f"{r['zx_gain_circuits']} |")
    L += ["", "| Set | Circuits | Spearman rho (gain %, T-density) | p | "
          "Spearman rho (gain %, non-Clifford density) | p | mean gain % |",
          "|---|---|---|---|---|---|---|"]
    for name in ["B1+C", "B1", "C"]:
        q = q4[name]
        L.append(f"| {name} | {q['n']} | {q['rho_t']:.2f} | {q['p_t']:.3f} | "
                 f"{q['rho_nc']:.2f} | {q['p_nc']:.3f} | {q['mean_gain_pct']:.2f} |")
    s = q4["split"]
    L += ["", f"Median split of B1+C at T-density {s['median']:.3f}: the {s['n_hi']} circuits "
          f"at or above it have ZX-only gain {s['gain_hi_pct']:.2f} % ({s['nz_hi']} with gain "
          f"> 0), the {s['n_lo']} below it {s['gain_lo_pct']:.2f} % ({s['nz_lo']} with gain > 0).",
          ""]

    L += ["## Per circuit (B1 and C)", "",
          "| family | file | T in | T after TR | nc L2 | nc P2 | nc L3 | nc P2L3 | n_2q L2 | "
          "n_2q P2 | n_2q L3 | n_2q P2L3 | n_1q L3 | n_1q P2L3 | GPS L3 | ZX-only gain % |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]

    def i(v):
        return "n/a" if pd.isna(v) else f"{v:.0f}"
    for r in w[w.family.isin(["B1", "C"])].itertuples():
        L.append(f"| {r.family} | {r.file} | {i(r.t_in)} | {i(r.t_tr)} | {i(r.nc_total_L2)} | "
                 f"{i(r.nc_total_P2)} | {i(r.nc_total_L3)} | {i(r.nc_total_P2L3)} | "
                 f"{i(r.n_2q_L2)} | {i(r.n_2q_P2)} | {i(r.n_2q_L3)} | {i(r.n_2q_P2L3)} | "
                 f"{i(r.n_1q_L3)} | {i(r.n_1q_P2L3)} | {r.gps_L3} | {r.zx_gain_pct:.2f} |")
    L.append("")
    L.append("<!-- CONCLUSION -->")
    OUT_MD.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT_MD}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--timeout", type=float, default=300.0)
    r.add_argument("--files", default="", help="comma-separated subset of files")
    r.add_argument("--use-stored", action="store_true",
                   help="read results/compiled/{L3,P2L3}/<file> when its HQC equals the ledger")
    r.set_defaults(func=cmd_run)
    p = sub.add_parser("report")
    p.set_defaults(func=cmd_report)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
