"""Run every pipeline on every circuit of a manifest-described family (B1, ...)
and write the count tables.  Generalisation of run_bench.py.

Outputs (for --prefix family_B1)
  results/family_B1_counts.csv      one row per circuit x pipeline
  results/family_B1_summary.csv     one row per circuit: n_2q, depth_2q, hqc,
                                    T-counts per pipeline, reductions vs
                                    P0ref and P0 in percent, status
  results/compiled/<pipeline>/<file>.qasm   compiled circuit + measure-all

Extra columns relative to run_bench.py
  t_count_written    T-count of the input as written: T, Tdg and Rz with
                     angle an odd multiple of pi/4
  t_count_zx         T-count of the pyzx circuit after the ZX stage of P1,
                     P2 and P4, before any pytket pass (ZPhase/XPhase gates
                     with phase an odd multiple of pi/4); NaN for the other
                     pipelines.  After the H2 rebase the T-count is undefined
                     and is not reported.
  n_non_cliffordT_zx phase gates after the ZX stage whose angle is not a
                     multiple of pi/4 (expected 0 for Clifford+T input)
  n_2q_zx, n_gates_zx  2-qubit / total gate counts of the ZX-stage circuit

Reductions (per circuit and pipeline p):
  red_vs_X_pct = 100 * (1 - n_2q[p] / n_2q[X]),  X in {P0ref, P0}

Usage: python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv
           --prefix family_B1 [--workers N] [--timeout S] [--pipelines ...]
"""

import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
from pytket import OpType  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

NAN_METRICS = ["n_qubits", "n_2q", "n_zzphase", "n_zzmax", "depth_2q",
               "n_phasedx", "n_rz", "n_total", "depth", "hqc",
               "t_zx", "t_tket", "t_total", "check_dev", "dist_maxdiff",
               "qasm_dist_maxdiff", "ref_dev", "pyzx_angle_err",
               "t_count_written", "t_count_zx", "n_non_cliffordT_zx",
               "n_2q_zx", "n_gates_zx"]
ZX_PIPELINES = {"P1", "P2", "P4"}


def t_count_written(circ) -> int:
    n = 0
    for cmd in circ.get_commands():
        t = cmd.op.type
        if t in (OpType.T, OpType.Tdg):
            n += 1
        elif t == OpType.Rz:
            f = Fraction(float(cmd.op.params[0])).limit_denominator(2 ** 20) % 2
            if f.denominator == 4:
                n += 1
    return n


def run_one(bench: str, file: str, pipeline: str) -> dict:
    """Compile one circuit with one pipeline, check it, save its QASM."""
    row = {"file": file, "pipeline": pipeline}
    circ = circuit_from_qasm(os.path.join(bench, file))
    npy = os.path.join(bench, file.replace(".qasm", ".npy"))
    ref_probs = np.load(npy) if os.path.exists(npy) else None
    row["t_count_written"] = t_count_written(circ)

    ref, _ = C.compile_pipeline("P0ref", circ)
    ref_ck = C.check(ref, circ, None)
    row["ref_dev"] = ref_ck["check_dev"]
    row["pyzx_angle_err"] = C.pyzx_angle_rounding(circ)
    if ref_probs is None:
        # no stored reference distribution: use P0ref's
        ref_probs = C.probs(ref)

    zx_out = {} if pipeline in ZX_PIPELINES else None
    comp, times = C.compile_pipeline(pipeline, circ, zx_out)
    row.update(times)
    if zx_out:
        pz = zx_out["pyzx"]
        row["t_count_zx"] = C.pyzx_tcount(pz)
        row["n_non_cliffordT_zx"] = C.pyzx_non_cliffordT(pz)
        row["n_2q_zx"] = pz.twoqubitcount()
        row["n_gates_zx"] = len(pz.gates)
    row.update(C.metrics(comp, n_measure=comp.n_qubits))
    row.update(C.check(comp, ref, ref_probs))

    qasm = C.to_qasm(C.add_measure_all(comp))
    outdir = os.path.join(RESULTS, "compiled", pipeline)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, file), "w") as f:
        f.write(qasm)
    row["qasm_dist_maxdiff"] = float(np.max(np.abs(
        C.probs_from_measured_qasm(qasm) - ref_probs)))
    qasm_ok = row["qasm_dist_maxdiff"] <= C.CHECK_TOL
    row["status"] = "ok" if row["check_ok"] and row["native"] and qasm_ok else "FLAGGED"
    return row


def _child(bench, file, pipeline, conn):
    try:
        conn.send(run_one(bench, file, pipeline))
    except Exception as e:  # noqa: BLE001
        conn.send({"file": file, "pipeline": pipeline, "status": "error",
                   "error": repr(e)[:300]})


def run_with_timeout(args):
    bench, file, pipeline, timeout = args
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=(bench, file, pipeline, child))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(timeout):
        row = parent.recv()
    else:
        p.terminate()
        row = {"file": file, "pipeline": pipeline, "status": "timeout"}
    p.join()
    row.setdefault("t_wall", time.perf_counter() - t0)
    for k in NAN_METRICS:
        row.setdefault(k, float("nan"))
    row.setdefault("check_ok", False)
    row.setdefault("native", False)
    return row


def summarise(counts: pd.DataFrame, man: pd.DataFrame) -> pd.DataFrame:
    """One row per circuit, pipelines across columns."""
    base = man[["file", "n", "n_gates", "t_count_as_written", "n_cx_as_written"]].copy()
    piv = counts.pivot(index="file", columns="pipeline")
    out = base.set_index("file")
    pipes = [p for p in C.PIPELINES if p in counts["pipeline"].unique()]
    for p in pipes:
        out[f"n_2q_{p}"] = piv["n_2q"][p]
    for p in pipes:
        out[f"depth_2q_{p}"] = piv["depth_2q"][p]
    for p in pipes:
        out[f"hqc_{p}"] = piv["hqc"][p]
    for p in pipes:
        if p in ZX_PIPELINES:
            out[f"t_count_zx_{p}"] = piv["t_count_zx"][p]
    for p in pipes:
        for X in ("P0ref", "P0"):
            if X in pipes:
                out[f"red_vs_{X}_pct_{p}"] = 100 * (1 - piv["n_2q"][p] / piv["n_2q"][X])
    for p in pipes:
        out[f"t_total_{p}"] = piv["t_total"][p]
    for p in pipes:
        out[f"status_{p}"] = piv["status"][p]
    out["max_check_dev"] = piv["check_dev"].max(axis=1)
    return out.reset_index().sort_values(["n", "file"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--pipelines", default=",".join(C.PIPELINES))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--files", default="", help="comma-separated subset of files")
    a = ap.parse_args()
    pipelines = a.pipelines.split(",")

    man = pd.read_csv(a.manifest)
    bench = os.path.dirname(os.path.abspath(a.manifest))
    if a.files:
        # accept "hwb8" as well as "hwb8.qasm"
        wanted = {f if f.endswith(".qasm") else f + ".qasm"
                  for f in a.files.split(",") if f}
        man = man[man["file"].isin(wanted)]
        missing = sorted(wanted - set(man["file"]))
        if missing:
            print(f"warning: not in manifest: {missing}", file=sys.stderr)
    if a.limit:
        man = man.head(a.limit)
    if man.empty:
        sys.exit("error: no circuits selected (check --files / --limit)")
    os.makedirs(RESULTS, exist_ok=True)

    # biggest circuits first so the long jobs do not trail at the end
    order = man.sort_values("n_gates", ascending=False)["file"]
    jobs = [(bench, f, p, a.timeout) for f in order for p in pipelines]
    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            print(f"{i + 1}/{len(jobs)} {row['file']} {row['pipeline']} "
                  f"{row['status']} n_2q={row.get('n_2q')} "
                  f"{row['t_wall']:.1f}s  [{time.perf_counter() - t0:.0f}s]", flush=True)
    counts = pd.DataFrame(rows)
    if counts.empty or "file" not in counts.columns:
        sys.exit("error: no results produced")
    meta = man[["file", "n", "n_gates", "t_count_as_written", "n_cx_as_written"]]
    counts = meta.merge(counts, on="file", how="right")
    # keep only the pipelines actually run so the summary never indexes a
    # missing pivot column on a --pipelines subset
    counts["pipeline"] = pd.Categorical(
        counts["pipeline"], [p for p in C.PIPELINES if p in pipelines])
    counts = counts.sort_values(["n", "file", "pipeline"])
    counts.to_csv(os.path.join(RESULTS, f"{a.prefix}_counts.csv"), index=False)

    summ = summarise(counts, man)
    summ.to_csv(os.path.join(RESULTS, f"{a.prefix}_summary.csv"), index=False)

    print("\nstatus counts:")
    print(counts.groupby(["pipeline", "status"], observed=True).size().unstack(fill_value=0))
    print("\nmax check_dev per pipeline:")
    print(counts.groupby("pipeline", observed=True)[["check_dev", "dist_maxdiff", "qasm_dist_maxdiff"]].max())
    print("\nn_2q by circuit and pipeline:")
    print(counts.pivot_table(index="file", columns="pipeline", values="n_2q", observed=True))
    print(f"\ntotal wall {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
