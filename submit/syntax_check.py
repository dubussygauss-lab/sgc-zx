"""Submit compiled circuits to the Quantinuum syntax checker nexus:H2-2SC.

One job per circuit (so any cost the checker reports is per circuit), 1000
shots, families A (n <= 8), B1, B2, pipelines P0 P1 P2 by default.  The
syntax checker costs no HQC (docs/platform_notes.md 3.4).  The raw job
payload and result object are dumped to
results/emulator/nexus_H2-2SC/<pipeline>/<file>.json and every job is
written to results/emulator_jobs.csv.

    python3 submit/syntax_check.py --dry-run
    AQORA_TEAM_ORG=<org> python3 submit/syntax_check.py [--families A,B1,B2]
        [--pipelines P0,P1,P2] [--shots 1000] [--max-jobs N] [--select REGEX]
        [--force] [--timeout 600]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

PLATFORM = "nexus:H2-2SC"
MAX_N = {"A": 8, "B1": None, "B2": None}


def plan(families, pipelines, shots, select=None, max_jobs=None):
    """List of dicts (family, file, pipeline, path, exists, n, hqc) and the
    missing-file list.  hqc = compile.hqc of the compiled circuit at `shots`."""
    rx = re.compile(select) if select else None
    items, missing = [], []
    for fam in families:
        for meta in common.list_family(fam, max_n=MAX_N[fam]):
            if rx and not rx.search(meta["file"]):
                continue
            for pipe in pipelines:
                p = common.compiled_path(pipe, meta["file"])
                it = dict(family=fam, file=meta["file"], pipeline=pipe, path=str(p),
                          n=meta["n"], exists=p.is_file(), hqc=None, native=None)
                if it["exists"]:
                    try:
                        circ = common.load_compiled(pipe, meta["file"])
                        it["hqc"] = common.hqc_estimate(circ, shots)
                        it["native"] = True
                    except ValueError as e:
                        it["native"] = False
                        it["error"] = str(e)
                    items.append(it)
                else:
                    missing.append(it)
    if max_jobs is not None:
        items = items[:max_jobs]
    return items, missing


def print_plan(items, missing, shots):
    tot = 0.0
    by_fam = {}
    for it in items:
        print("%-3s %-5s %-40s n=%-3d hqc=%s%s" % (
            it["family"], it["pipeline"], it["file"], it["n"],
            "%.2f" % it["hqc"] if it["hqc"] is not None else "n/a",
            "" if it["native"] else "  NON-NATIVE: " + it.get("error", "")))
        if it["hqc"] is not None:
            tot += it["hqc"]
            by_fam[it["family"]] = by_fam.get(it["family"], 0.0) + it["hqc"]
    print("\njobs planned: %d (one circuit per job, %d shots, platform %s)" % (len(items), shots, PLATFORM))
    for fam, v in sorted(by_fam.items()):
        print("  family %-2s  jobs %3d  sum HQC estimate %.2f" % (
            fam, sum(1 for i in items if i["family"] == fam), v))
    print("  total HQC estimate (would be charged on H2-2E at the same shots; the syntax checker is free): %.2f" % tot)
    if missing:
        print("\nmissing compiled files (skipped): %d" % len(missing))
        for it in missing:
            print("  ", it["path"])


def submit_one(qpu, it, shots, timeout, poll):
    circ = common.load_compiled(it["pipeline"], it["file"])
    key = common.append_ledger(dict(platform=PLATFORM, family=it["family"], file=it["file"],
                                    pipeline=it["pipeline"], shots=shots, options="{}",
                                    status="SUBMITTING"))
    key = {k: key[k] for k in ("timestamp", "platform", "file", "pipeline")}
    try:
        job = qpu.run(circ, shots=shots)
    except Exception as e:  # noqa: BLE001
        common.update_ledger(key, status="SUBMIT_ERROR:" + repr(e)[:200])
        raise
    common.update_ledger(key, job_id=job.job_id, status="SUBMITTED")
    out = dict(platform=PLATFORM, family=it["family"], file=it["file"], pipeline=it["pipeline"],
               shots=shots, job_id=job.job_id, hqc_estimate=it["hqc"])
    try:
        counts, t_wall = common.wait_counts(job, timeout=timeout, poll=poll)
        out["counts"] = counts
        out["t_wait"] = t_wall
        out["results"] = [common.result_raw(r) for r in job.results(raise_on_item_error=False)]
        status = "COMPLETED"
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)
        status = "FAILED:" + repr(e)[:200]
    raw = common.job_raw(job)
    out["job"] = raw
    cost = common.cost_fields(raw.get("payload", {}))
    out["cost_fields"] = cost
    path = common.save_result(PLATFORM, it["pipeline"], it["file"], out)
    common.update_ledger(key, status=status, hqc_or_seconds=json.dumps(cost, default=str) if cost else "",
                         result_path=str(path.relative_to(common.ROOT)))
    print("%-5s %-40s job %s status %s cost %s" % (it["pipeline"], it["file"], job.job_id, status, cost))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--families", default="A,B1,B2")
    ap.add_argument("--pipelines", default="P0,P1,P2")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--max-jobs", type=int, default=None)
    ap.add_argument("--select", default=None, help="regex on the file name")
    ap.add_argument("--force", action="store_true", help="resubmit even if a result JSON exists")
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("--allow-personal", action="store_true", help="submit without AQORA_TEAM_ORG")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    families = [f.strip() for f in args.families.split(",") if f.strip()]
    pipelines = [p.strip() for p in args.pipelines.split(",") if p.strip()]
    items, missing = plan(families, pipelines, args.shots, args.select, args.max_jobs)
    if not args.force:
        items = [it for it in items if not common.result_path(PLATFORM, it["pipeline"], it["file"]).is_file()]
    if args.dry_run:
        print_plan(items, missing, args.shots)
        print("credentials:", common.credential_source() or "NONE", " team org:", common.team_org(required=False))
        return 0
    bad = [it for it in items if not it["native"]]
    if bad:
        raise SystemExit("non-native circuits in plan: %s" % [i["file"] for i in bad])
    qpu = common.make_qpu(PLATFORM, allow_personal=args.allow_personal)
    for it in items:
        submit_one(qpu, it, args.shots, args.timeout, args.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
