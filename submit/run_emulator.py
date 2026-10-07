"""Run compiled circuits on a Nexus H2 emulator through aqora and score them.

    python3 submit/run_emulator.py --platform nexus:H2-2E --family A
        --pipelines P0,P2 --shots 1000 --noisy true --max-jobs 5 --select 'n4_'
        [--batch-size 10] [--timeout 1800] [--dry-run]

Circuits are batched: QPU.run takes a list of programs and counts() returns
one mapping per program in submission order (aqora/qpu.py docstrings).  For
every circuit the counts are saved to
results/emulator/<platform>/<pipeline>/<file>.json, F_H and TVD are computed
against the reference distribution (family A: bench .npy of the circuit as
written; B1/B2: P0ref compilation, both as noise/run_proxy.py), and a row
with the proxy-CSV columns + job_id, shots is appended to
results/emulator_<platform>.csv so model/cost_model.py reruns unchanged.
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

PLATFORMS = ("nexus:H2-Emulator", "nexus:H2-2E")
HQC_PLATFORMS = ("nexus:H2-2E",)   # costed in HQC; H2-Emulator is costed in seconds


def csv_path(platform):
    return common.RESULTS / ("emulator_%s.csv" % common.platform_dir(platform))


def plan(platform, family, pipelines, shots, noisy, select=None, max_jobs=None,
         batch_size=10, skip_done=True):
    rx = re.compile(select) if select else None
    items, missing = [], []
    for meta in common.list_family(family):
        if rx and not rx.search(meta["file"]):
            continue
        for pipe in pipelines:
            p = common.compiled_path(pipe, meta["file"])
            if not p.is_file():
                missing.append(str(p))
                continue
            if skip_done and common.result_path(platform, pipe, meta["file"]).is_file():
                continue
            circ = common.load_compiled(pipe, meta["file"])
            items.append(dict(meta=meta, file=meta["file"], pipeline=pipe, n=meta["n"],
                              hqc=common.hqc_estimate(circ, shots), circ=circ))
    jobs = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    if max_jobs is not None:
        jobs = jobs[:max_jobs]
    options = {"noisy_simulation": noisy}
    return jobs, missing, options


def print_plan(platform, family, jobs, missing, shots, options):
    total = 0.0
    for j, batch in enumerate(jobs):
        h = sum(it["hqc"] for it in batch)
        total += h
        print("job %d: %d circuits, HQC estimate %.2f" % (j + 1, len(batch), h))
        for it in batch:
            print("   %-5s %-40s n=%-3d hqc=%.2f" % (it["pipeline"], it["file"], it["n"], it["hqc"]))
    n_circ = sum(len(b) for b in jobs)
    print("\nplatform %s family %s shots %d options %s" % (platform, family, shots, json.dumps(options)))
    print("jobs: %d  circuits: %d  total HQC estimate: %.2f%s" % (
        len(jobs), n_circ, total,
        "" if platform in HQC_PLATFORMS else "  (platform costed in seconds, HQC is the H2-2E-equivalent)"))
    if missing:
        print("missing compiled files (skipped): %d" % len(missing))
        for m in missing:
            print("  ", m)
    return total


def score(family, pipeline, file, counts, meta, shots, job_id, t_sim):
    st = common.circuit_stats(pipeline, file)
    nq = st.pop("n_qubits")
    ref = common.reference_probs(family, file)
    ideal = common.exact_probs(pipeline, file)
    emp = common.counts_to_probs(counts, nq)
    row = dict(file=file, model=meta["model"], n=meta["n"], r=meta["r"], disorder=meta["disorder"],
               instance=meta["instance"], pipeline=pipeline, n_qubits=nq, **st,
               ideal_vs_ref_maxdiff=float(np.max(np.abs(ideal - ref))),
               F_H=common.hellinger_fidelity(ref, emp), TVD=common.total_variation(ref, emp),
               support_size=int((ref > common.run_proxy.SUPPORT_TOL).sum()), t_sim=t_sim,
               job_id=job_id, shots=shots)
    return row


def append_rows(path, rows):
    new = not Path(path).is_file()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=common.EMULATOR_COLUMNS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in common.EMULATOR_COLUMNS})


def run_job(qpu, platform, family, batch, shots, options, timeout, poll):
    keys = []
    for it in batch:
        k = common.append_ledger(dict(platform=platform, family=family, file=it["file"],
                                      pipeline=it["pipeline"], shots=shots, options=options,
                                      status="SUBMITTING"))
        keys.append({c: k[c] for c in ("timestamp", "platform", "file", "pipeline")})
    try:
        job = qpu.run([it["circ"] for it in batch], shots=shots, options=options)
    except Exception as e:  # noqa: BLE001
        for k in keys:
            common.update_ledger(k, status="SUBMIT_ERROR:" + repr(e)[:200])
        raise
    for k in keys:
        common.update_ledger(k, job_id=job.job_id, status="SUBMITTED")
    print("submitted job %s with %d circuits" % (job.job_id, len(batch)))
    t0 = time.perf_counter()
    try:
        counts_list, t_wall = common.wait_counts(job, timeout=timeout, poll=poll)
        status = "COMPLETED"
        err = None
    except Exception as e:  # noqa: BLE001
        counts_list, t_wall, status, err = None, time.perf_counter() - t0, "FAILED:" + repr(e)[:200], repr(e)
    raw = common.job_raw(job)
    cost = common.cost_fields(raw.get("payload", {}))
    rows = []
    for i, (it, k) in enumerate(zip(batch, keys)):
        out = dict(platform=platform, family=family, file=it["file"], pipeline=it["pipeline"],
                   shots=shots, options=options, job_id=job.job_id, index=i, hqc_estimate=it["hqc"],
                   job=raw, cost_fields=cost, t_wait=t_wall)
        if counts_list is not None and i < len(counts_list):
            out["counts"] = counts_list[i]
            try:
                rows.append(score(family, it["pipeline"], it["file"], counts_list[i], it["meta"],
                                  shots, job.job_id, t_wall))
                out["F_H"], out["TVD"] = rows[-1]["F_H"], rows[-1]["TVD"]
            except Exception as e:  # noqa: BLE001
                out["score_error"] = repr(e)
        else:
            out["error"] = err
        path = common.save_result(platform, it["pipeline"], it["file"], out)
        common.update_ledger(k, status=status, hqc_or_seconds=json.dumps(cost, default=str) if cost else "",
                             result_path=str(path.relative_to(common.ROOT)))
    if rows:
        append_rows(csv_path(platform), rows)
    print("job %s %s cost %s rows %d" % (job.job_id, status, cost, len(rows)))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", choices=PLATFORMS, required=True)
    ap.add_argument("--family", choices=common.FAMILIES, required=True)
    ap.add_argument("--pipelines", default="P0,P2")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--noisy", choices=("true", "false"), default="true")
    ap.add_argument("--max-jobs", type=int, default=None)
    ap.add_argument("--select", default=None, help="regex on the file name")
    ap.add_argument("--batch-size", type=int, default=10, help="circuits per aqora job")
    ap.add_argument("--force", action="store_true", help="rerun circuits that already have a result JSON")
    ap.add_argument("--timeout", type=float, default=1800.0)
    ap.add_argument("--poll", type=float, default=10.0)
    ap.add_argument("--allow-personal", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    pipelines = [p.strip() for p in args.pipelines.split(",") if p.strip()]
    noisy = args.noisy == "true"
    jobs, missing, options = plan(args.platform, args.family, pipelines, args.shots, noisy,
                                  args.select, args.max_jobs, args.batch_size, skip_done=not args.force)
    print_plan(args.platform, args.family, jobs, missing, args.shots, options)
    if args.dry_run:
        print("credentials:", common.credential_source() or "NONE", " team org:", common.team_org(required=False))
        print("output csv:", csv_path(args.platform))
        return 0
    qpu = common.make_qpu(args.platform, allow_personal=args.allow_personal)
    for batch in jobs:
        run_job(qpu, args.platform, args.family, batch, args.shots, options, args.timeout, args.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
