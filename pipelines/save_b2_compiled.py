"""Recompile family B2 and save results/compiled/<pipeline>/<file>.qasm.

run_b2.py computed the B2 counts (results/family_B2_counts.csv) but never
wrote the compiled circuits, so submit/syntax_check.py and
submit/run_emulator.py could not find them.  This script compiles every
bench/family_B2/*.qasm through P0ref, P0, P1, P2, P3 with
compile.compile_pipeline (the call run_b2.run_one makes, deterministic) and
saves the result exactly as run_bench.run_one does:
    compile.to_qasm(compile.add_measure_all(compiled))  -> hqslib1 header,
    measure-all appended, implicit qubit permutation encoded in the measure map.

Per (file, pipeline) it then checks the SAVED file, re-read from disk:
  (a) metrics_match   n_2q, n_phasedx, n_rz of the re-read circuit equal the
                      row of results/family_B2_counts.csv (counts_* columns
                      hold the CSV values, n_* the re-read values)
  (b) reread_native   submit.common.load_compiled accepts the file (pytket
                      parses it, every op in compile.NATIVE, one Measure per
                      qubit)
  (c) dist_ok         compile.probs_from_measured_qasm(saved) agrees with
                      compile.probs(uncompiled bench circuit) on |0..0> to
                      compile.CHECK_TOL (1e-8); dist_maxdiff is the max
                      absolute difference
Output: results/family_B2_compiled_check.csv, one row per (file, pipeline),
status = "ok" iff (a), (b) and (c) hold.

Usage: python pipelines/save_b2_compiled.py [--workers N] [--timeout S]
                                            [--pipelines P0ref,P0,P1,P2,P3]
"""

import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "submit"))
import compile as C  # noqa: E402
import common  # noqa: E402  (submit/common.py)
from pytket.qasm import circuit_from_qasm  # noqa: E402

BENCH = os.path.join(ROOT, "bench", "family_B2")
RESULTS = os.path.join(ROOT, "results")
COUNTS = os.path.join(RESULTS, "family_B2_counts.csv")
OUT = os.path.join(RESULTS, "family_B2_compiled_check.csv")
PIPELINES = ["P0ref", "P0", "P1", "P2", "P3"]
METRIC_KEYS = ["n_2q", "n_phasedx", "n_rz"]


def run_one(file, pipeline, counts_row):
    row = {"file": file, "pipeline": pipeline}
    circ = circuit_from_qasm(os.path.join(BENCH, file))
    n = circ.n_qubits
    row["n_qubits"] = n

    t0 = time.perf_counter()
    comp, times = C.compile_pipeline(pipeline, circ)
    row["t_compile"] = time.perf_counter() - t0
    row.update({"t_zx": times["t_zx"], "t_tket": times["t_tket"]})

    # save exactly as run_bench.run_one
    qasm = C.to_qasm(C.add_measure_all(comp))
    outdir = os.path.join(RESULTS, "compiled", pipeline)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, file)
    with open(path, "w") as f:
        f.write(qasm)
    row["path"] = os.path.relpath(path, ROOT)

    # metrics of the in-memory compiled circuit (what run_b2 recorded)
    m_mem = C.metrics(comp, n_measure=n)
    for k in METRIC_KEYS:
        row["mem_" + k] = m_mem[k]

    # (b) re-read through the submission loader
    try:
        saved = common.load_compiled(pipeline, file, check_native=True)
        row["reread_native"] = True
        row["reread_error"] = ""
    except Exception as e:  # noqa: BLE001
        row["reread_native"] = False
        row["reread_error"] = repr(e)[:300]
        saved = circuit_from_qasm(path)

    # (a) metrics of the re-read saved circuit vs the counts CSV
    m_saved = C.metrics(saved)
    match = True
    for k in METRIC_KEYS:
        row[k] = int(m_saved[k])
        row["counts_" + k] = int(counts_row[k])
        match = match and row[k] == row["counts_" + k]
    row["metrics_match"] = bool(match)
    row["mem_vs_saved_match"] = all(m_saved[k] == m_mem[k] for k in METRIC_KEYS)

    # (c) measured-bit distribution of the saved file vs the uncompiled circuit
    p_saved = C.probs_from_measured_qasm(qasm)
    p_exact = C.probs(circ)
    row["dist_maxdiff"] = float(np.max(np.abs(p_saved - p_exact)))
    row["dist_ok"] = bool(row["dist_maxdiff"] <= C.CHECK_TOL)

    row["status"] = "ok" if (row["metrics_match"] and row["reread_native"]
                             and row["dist_ok"]) else "FLAGGED"
    return row


def _child(file, pipeline, counts_row, conn):
    try:
        conn.send(run_one(file, pipeline, counts_row))
    except Exception as e:  # noqa: BLE001
        conn.send({"file": file, "pipeline": pipeline, "status": "error",
                   "error": repr(e)[:300]})


def run_with_timeout(args):
    file, pipeline, counts_row, timeout = args
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=(file, pipeline, counts_row, child))
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
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--pipelines", default=",".join(PIPELINES))
    a = ap.parse_args()
    pipelines = a.pipelines.split(",")

    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    counts = pd.read_csv(COUNTS).set_index(["file", "pipeline"])
    jobs = []
    for f in man["file"]:
        for p in pipelines:
            crow = counts.loc[(f, p)]
            jobs.append((f, p, {k: int(crow[k]) for k in METRIC_KEYS}, a.timeout))
    print(f"{len(man)} circuits x {len(pipelines)} pipelines, {a.workers} workers", flush=True)

    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            print(f"{i + 1}/{len(jobs)} {row['file']} {row['pipeline']} "
                  f"{row['status']} {time.perf_counter() - t0:.0f}s", flush=True)
    total = time.perf_counter() - t0

    df = pd.DataFrame(rows)
    meta = man[["file", "n", "eps", "instance"]]
    df = meta.merge(df, on="file", how="right")
    df = df.sort_values(["n", "eps", "instance", "pipeline"])
    df.to_csv(OUT, index=False)

    print(f"\nwrote {os.path.relpath(OUT, ROOT)} ({len(df)} rows), wall {total:.0f}s")
    print(df.groupby(["pipeline", "status"]).size())
    for col in ("metrics_match", "reread_native", "dist_ok"):
        if col in df:
            print(f"{col}: {int(df[col].fillna(False).astype(bool).sum())}/{len(df)} true")
    if "dist_maxdiff" in df:
        print(f"max dist_maxdiff: {df['dist_maxdiff'].max():.3e}")
    bad = df[df["status"] != "ok"]
    if len(bad):
        print("\nFLAGGED / error rows:")
        print(bad[["file", "pipeline", "status"] +
                  [c for c in ("metrics_match", "reread_native", "dist_ok", "error",
                               "reread_error") if c in bad]].to_string())


if __name__ == "__main__":
    main()
