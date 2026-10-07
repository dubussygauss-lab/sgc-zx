"""Run P0ref, P0, P1, P2, P3 on family B2 (QSD+gridsynth Haar circuits).

Writes results/family_B2_counts.csv, one row per circuit x pipeline, with
  n_2q etc. from compile.metrics on the compiled native circuit,
  t_count_written    T-count of the input QASM (t + tdg),
  t_count_after_zx   T-count after the pipeline's ZX stage alone
                     (compile.zx_full_reduce for P1, compile.zx_teleport_reduce
                     for P2, AutoRebase+ZXGraphlikeOptimisation for P3, as in
                     compile.compile_pipeline; equal to t_count_written for
                     P0ref/P0 which have no ZX stage), counted as gates of
                     type T/Tdg plus Rz/U1 with phase (half-turns) congruent
                     to 1/4, 3/4, 5/4 or 7/4 mod 2 within 1e-9,
  check_* from compile.check(compiled, P0ref(circuit)) (unitary, n <= 8),
  target_dev = 1 - |tr(U_target^dag U_compiled)|/2^n against the Haar target
  (pytket ILO-BE unitary reordered to qiskit little-endian).
Usage: python pipelines/run_b2.py [--workers N] [--timeout S] [--pipelines ..]
"""

import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
from pytket import OpType  # noqa: E402
from pytket.passes import AutoRebase, ZXGraphlikeOptimisation  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "bench", "family_B2")
RESULTS = os.path.join(ROOT, "results")
PIPELINES = ["P0ref", "P0", "P1", "P2", "P3"]


def t_count(circ) -> int:
    k = 0
    for cmd in circ.get_commands():
        t = cmd.op.type
        if t in (OpType.T, OpType.Tdg):
            k += 1
        elif t in (OpType.Rz, OpType.U1):
            p = float(cmd.op.params[0]) % 2
            if min(abs(p - q) for q in (0.25, 0.75, 1.25, 1.75)) < 1e-9:
                k += 1
    return k


def zx_stage(name, circ):
    if name == "P1":
        return C.zx_full_reduce(circ)
    if name == "P2":
        return C.zx_teleport_reduce(circ)
    if name == "P3":
        c = circ.copy()
        AutoRebase({OpType.CX, OpType.Rz, OpType.Rx, OpType.H}).apply(c)
        ZXGraphlikeOptimisation().apply(c)
        return c
    return circ


def bigendian_to_little(U, n):
    """pytket get_unitary (q[0] most significant) -> qiskit (q[0] least)."""
    t = U.reshape((2,) * (2 * n))
    perm = list(range(n))[::-1]
    t = np.transpose(t, perm + [n + p for p in perm])
    return t.reshape(2 ** n, 2 ** n)


def run_one(file, pipeline):
    row = {"file": file, "pipeline": pipeline}
    circ = circuit_from_qasm(os.path.join(BENCH, file))
    n = circ.n_qubits
    row["t_count_written"] = t_count(circ)
    ref, _ = C.compile_pipeline("P0ref", circ)
    row["ref_dev"] = C.check(ref, circ)["check_dev"]

    t0 = time.perf_counter()
    zc = zx_stage(pipeline, circ)
    row["t_zx_stage"] = time.perf_counter() - t0
    row["t_count_after_zx"] = t_count(zc)
    row["zx_stage_dev"] = C.unitary_deviation(circ.get_unitary(), zc.get_unitary())

    comp, times = C.compile_pipeline(pipeline, circ)
    row.update(times)
    row.update(C.metrics(comp, n_measure=n))
    row.update(C.check(comp, ref))
    U = np.load(os.path.join(BENCH, file.replace(".qasm", "_target.npy")))
    row["target_dev"] = C.unitary_deviation(U, bigendian_to_little(comp.get_unitary(), n))
    row["status"] = "ok" if row["check_ok"] and row["native"] else "FLAGGED"
    return row


def _child(file, pipeline, conn):
    try:
        conn.send(run_one(file, pipeline))
    except Exception as e:  # noqa: BLE001
        conn.send({"file": file, "pipeline": pipeline, "status": "error",
                   "error": repr(e)[:300]})


def run_with_timeout(args):
    file, pipeline, timeout = args
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=(file, pipeline, child))
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
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--pipelines", default=",".join(PIPELINES))
    a = ap.parse_args()
    pipelines = a.pipelines.split(",")
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    jobs = [(f, p, a.timeout) for f in man["file"] for p in pipelines]
    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            print(f"{i + 1}/{len(jobs)} {row['file']} {row['pipeline']} "
                  f"{row['status']} {time.perf_counter() - t0:.0f}s", flush=True)
    counts = pd.DataFrame(rows)
    meta = man[["file", "n", "eps", "instance", "n_gates", "t_count", "n_cx",
                "n_rz_synthesised", "operator_norm_error", "bound"]]
    counts = meta.merge(counts, on="file", how="right")
    counts = counts.sort_values(["n", "eps", "instance", "pipeline"])
    counts.to_csv(os.path.join(RESULTS, "family_B2_counts.csv"), index=False)
    print(counts.pivot_table(index=["n", "eps"], columns="pipeline",
                             values=["n_2q", "t_count_after_zx"], aggfunc="mean").round(1))
    print(counts.groupby(["pipeline", "status"]).size())


if __name__ == "__main__":
    main()
