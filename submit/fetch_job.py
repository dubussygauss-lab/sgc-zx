#!/usr/bin/env python3
"""Fetch the results of an already submitted emulator job by its id.

Used when the local process that submitted a job stopped before the job
finished. The circuits of the job and their order are read from
results/emulator_jobs.csv (rows with that job_id, in ledger order, which is
the order they were passed to QPU.run). Results are saved and scored exactly
as run_emulator.run_job does.

    AQORA_TEAM_ORG=learned_zx_rewriting python3 submit/fetch_job.py \
        --job-id <id> --family B1 [--timeout 3600]
"""
import argparse
import json
import time

import aqora

import common
import run_emulator as RE


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--family", choices=common.FAMILIES, required=True)
    ap.add_argument("--timeout", type=float, default=3600)
    ap.add_argument("--poll", type=float, default=15)
    a = ap.parse_args(argv)

    rows_ledger = [r for r in common.read_ledger() if r.get("job_id") == a.job_id]
    if not rows_ledger:
        raise SystemExit("job id %s not in the ledger" % a.job_id)
    platform = rows_ledger[0]["platform"]
    shots = int(rows_ledger[0]["shots"])
    options = json.loads(rows_ledger[0]["options"]) if rows_ledger[0]["options"] else {}
    metas = {m["file"]: m for m in common.list_family(a.family)}
    batch = [dict(file=r["file"], pipeline=r["pipeline"], meta=metas[r["file"]],
                  hqc=common.hqc_estimate(common.load_compiled(r["pipeline"], r["file"]), shots))
             for r in rows_ledger]
    keys = [{c: r[c] for c in ("timestamp", "platform", "file", "pipeline")} for r in rows_ledger]
    print("job %s: %d circuits on %s, shots %d" % (a.job_id, len(batch), platform, shots))

    common.get_client()  # fails loudly if no credentials
    job = aqora.QPUJob.from_id(a.job_id)
    t0 = time.perf_counter()
    try:
        counts_list, t_wall = common.wait_counts(job, timeout=a.timeout, poll=a.poll)
        status, err = "COMPLETED", None
    except Exception as e:  # noqa: BLE001
        counts_list, t_wall, status, err = None, time.perf_counter() - t0, "FAILED:" + repr(e)[:200], repr(e)
    raw = common.job_raw(job)
    cost = common.cost_fields(raw.get("payload", {}))
    rows = []
    for i, (it, k) in enumerate(zip(batch, keys)):
        out = dict(platform=platform, family=a.family, file=it["file"], pipeline=it["pipeline"],
                   shots=shots, options=options, job_id=a.job_id, index=i, hqc_estimate=it["hqc"],
                   job=raw, cost_fields=cost, t_wait=t_wall, fetched_by_id=True)
        if counts_list is not None and i < len(counts_list):
            out["counts"] = counts_list[i]
            try:
                rows.append(RE.score(a.family, it["pipeline"], it["file"], counts_list[i], it["meta"],
                                     shots, a.job_id, t_wall))
                out["F_H"], out["TVD"] = rows[-1]["F_H"], rows[-1]["TVD"]
            except Exception as e:  # noqa: BLE001
                out["score_error"] = repr(e)
        else:
            out["error"] = err
        path = common.save_result(platform, it["pipeline"], it["file"], out)
        common.update_ledger(k, status=status, hqc_or_seconds=json.dumps(cost, default=str) if cost else "",
                             result_path=str(path.relative_to(common.ROOT)))
    if rows:
        RE.append_rows(RE.csv_path(platform), rows)
    print("job %s %s cost %s rows %d" % (a.job_id, status, cost, len(rows)))


if __name__ == "__main__":
    main()
