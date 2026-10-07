"""Run every pipeline on every family_A circuit and write the count tables.

Outputs
  results/family_A_counts.csv      one row per circuit x pipeline
  results/family_A_summary.csv     mean n_2q, depth_2q, hqc per
                                   (model, n, r, disorder, pipeline) plus the
                                   reduction vs P0ref and vs P0 in percent
  results/compiled/<pipeline>/<file>.qasm   compiled circuit + measure-all
                                   (hqslib1 header, for emulator submission)

Reduction formula (per group g and pipeline p):
  red_vs_X_pct = 100 * (1 - mean_n2q[g, p] / mean_n2q[g, X]),  X in {P0ref, P0}
Same for depth_2q (red_depth_vs_X_pct) and hqc (red_hqc_vs_X_pct).

Usage: python pipelines/run_bench.py [--workers N] [--timeout S]
                                     [--pipelines P0,P1,...] [--limit K]
                                     [--model xxz] [--files a.qasm,b.qasm]
                                     [--merge]

--model / --files restrict the run to a subset of the manifest.  With
--merge the new rows replace the rows with the same (file, pipeline) in an
existing results/family_A_counts.csv (other rows are kept) and the summary
is recomputed from the merged table; without --merge both CSVs are
overwritten with the subset only.
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
from pytket.qasm import circuit_from_qasm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "bench", "family_A")
RESULTS = os.path.join(ROOT, "results")

NAN_METRICS = ["n_qubits", "n_2q", "n_zzphase", "n_zzmax", "depth_2q",
               "n_phasedx", "n_rz", "n_total", "depth", "hqc",
               "t_zx", "t_tket", "t_total", "check_dev", "dist_maxdiff",
               "qasm_dist_maxdiff", "ref_dev", "pyzx_angle_err"]


def run_one(file: str, pipeline: str) -> dict:
    """Compile one circuit with one pipeline, check it, save its QASM."""
    row = {"file": file, "pipeline": pipeline}
    circ = circuit_from_qasm(os.path.join(BENCH, file))
    npy = os.path.join(BENCH, file.replace(".qasm", ".npy"))
    ref_probs = np.load(npy) if os.path.exists(npy) else None

    ref, _ = C.compile_pipeline("P0ref", circ)
    # P0ref itself against the circuit as written
    ref_ck = C.check(ref, circ, None)
    row["ref_dev"] = ref_ck["check_dev"]
    row["pyzx_angle_err"] = C.pyzx_angle_rounding(circ)

    comp, times = C.compile_pipeline(pipeline, circ)
    row.update(times)
    row.update(C.metrics(comp, n_measure=comp.n_qubits))
    row.update(C.check(comp, ref, ref_probs))

    qasm = C.to_qasm(C.add_measure_all(comp))
    outdir = os.path.join(RESULTS, "compiled", pipeline)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, file), "w") as f:
        f.write(qasm)
    # the saved artefact, re-read: measured-bit distribution vs reference
    if ref_probs is not None:
        row["qasm_dist_maxdiff"] = float(np.max(np.abs(
            C.probs_from_measured_qasm(qasm) - ref_probs)))
    else:
        row["qasm_dist_maxdiff"] = float("nan")
    qasm_ok = np.isnan(row["qasm_dist_maxdiff"]) or row["qasm_dist_maxdiff"] <= C.CHECK_TOL
    row["status"] = "ok" if row["check_ok"] and row["native"] and qasm_ok else "FLAGGED"
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
    for k in NAN_METRICS:
        row.setdefault(k, float("nan"))
    row.setdefault("check_ok", False)
    row.setdefault("native", False)
    return row


def summarise(counts: pd.DataFrame) -> pd.DataFrame:
    keys = ["model", "n", "r", "disorder", "pipeline"]
    g = counts.groupby(keys).agg(
        n_circuits=("file", "count"),
        n_ok=("status", lambda s: int((s == "ok").sum())),
        n_2q=("n_2q", "mean"),
        depth_2q=("depth_2q", "mean"),
        hqc=("hqc", "mean"),
        n_phasedx=("n_phasedx", "mean"),
        t_total=("t_total", "mean"),
        max_check_dev=("check_dev", "max"),
    ).reset_index()
    base = ["model", "n", "r", "disorder"]
    for X in ("P0ref", "P0"):
        ref = g[g.pipeline == X][base + ["n_2q", "depth_2q", "hqc"]]
        ref = ref.rename(columns={"n_2q": "_n", "depth_2q": "_d", "hqc": "_h"})
        g = g.merge(ref, on=base, how="left")
        g[f"red_vs_{X}_pct"] = 100 * (1 - g["n_2q"] / g["_n"])
        g[f"red_depth_vs_{X}_pct"] = 100 * (1 - g["depth_2q"] / g["_d"])
        g[f"red_hqc_vs_{X}_pct"] = 100 * (1 - g["hqc"] / g["_h"])
        g = g.drop(columns=["_n", "_d", "_h"])
    return g.sort_values(keys).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--pipelines", default=",".join(C.PIPELINES))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default="", help="only circuits of this model")
    ap.add_argument("--files", default="", help="comma-separated manifest file names")
    ap.add_argument("--merge", action="store_true",
                    help="replace matching (file, pipeline) rows in the existing counts CSV")
    a = ap.parse_args()
    pipelines = a.pipelines.split(",")

    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    if a.model:
        man = man[man["model"] == a.model]
    if a.files:
        want = a.files.split(",")
        man = man[man["file"].isin(want)]
    if a.limit:
        man = man.head(a.limit)
    print(f"{len(man)} circuits x {len(pipelines)} pipelines", flush=True)
    os.makedirs(RESULTS, exist_ok=True)

    jobs = [(f, p, a.timeout) for f in man["file"] for p in pipelines]
    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                print(f"{i + 1}/{len(jobs)} done, {time.perf_counter() - t0:.0f}s",
                      flush=True)
    counts = pd.DataFrame(rows)
    meta = man[["file", "model", "n", "r", "disorder", "instance", "n_cx"]]
    counts = meta.merge(counts, on="file", how="right")
    counts_path = os.path.join(RESULTS, "family_A_counts.csv")
    if a.merge and os.path.exists(counts_path):
        old = pd.read_csv(counts_path)
        key = set(zip(counts["file"], counts["pipeline"]))
        keep = old[[(f, p) not in key for f, p in zip(old["file"], old["pipeline"])]]
        print(f"merge: {len(old)} old rows, {len(old) - len(keep)} replaced, {len(counts)} new")
        counts = pd.concat([keep, counts], ignore_index=True)
    counts = counts.sort_values(["model", "n", "r", "disorder", "instance", "pipeline"])
    counts.to_csv(counts_path, index=False)

    summ = summarise(counts)
    summ.to_csv(os.path.join(RESULTS, "family_A_summary.csv"), index=False)

    print("\nstatus counts:")
    print(counts.groupby(["pipeline", "status"]).size().unstack(fill_value=0))
    print("\nmax check_dev per pipeline:")
    print(counts.groupby("pipeline")[["check_dev", "dist_maxdiff", "qasm_dist_maxdiff"]].max())
    print("\nmean n_2q by n and pipeline:")
    print(counts.pivot_table(index="n", columns="pipeline", values="n_2q", aggfunc="mean").round(1))
    print(f"\ntotal wall {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
