"""Fetch the Grand Challenge track's scoring criteria and submission preamble
(docs/platform_notes.md section 2.3) and write docs/rubric.md.

    python3 submit/read_rubric.py --dry-run          # print the query only
    AQORA_TOKEN=... python3 submit/read_rubric.py [--slug quantinuum-sg-grand-challenge]

Field names were verified by schema introspection on 2026-10-06; the event
slug is unverified.  `noCode` and `validUntil` (submission deadline of the
stage) are requested from `currentStage`; if the server rejects a field the
error is written to the report instead of guessed around.
"""

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

DEFAULT_SLUG = "quantinuum-sg-grand-challenge"
OUT = common.ROOT / "docs" / "rubric.md"

QUERY = """query Rubric($slug: String!) {
  eventBySlug(slug: $slug) {
    id
    title
    competitions(first: 10) {
      nodes {
        competition {
          id
          slug
          title
          currentStage {
            noCode
            requiresApproval
            submissionPreamble
            validUntil
            scoringCriteria { title weight description }
          }
        }
      }
    }
  }
}"""


def run_query(slug):
    from aqora._provider.client import _run_sync
    client = common.get_client()
    _run_sync(client.authenticate)
    return _run_sync(lambda: client.send(QUERY, slug=slug))


def render(slug, data, error=None):
    lines = ["# Grand Challenge track rubric", "",
             "Fetched %s UTC by `submit/read_rubric.py` from `https://aqora.io/graphql`, "
             "`eventBySlug(slug: \"%s\")`. [F] unless marked." % (
                 _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), slug), ""]
    if error:
        lines += ["**Query failed**: `%s`" % error, ""]
        return "\n".join(lines)
    ev = (data or {}).get("eventBySlug")
    if not ev:
        lines += ["`eventBySlug` returned null: the slug is wrong or the account cannot see the event.", ""]
        return "\n".join(lines)
    lines += ["Event: **%s** (id `%s`)" % (ev.get("title"), ev.get("id")), ""]
    for node in ev.get("competitions", {}).get("nodes", []):
        c = node.get("competition") or {}
        st = c.get("currentStage") or {}
        lines += ["## Track: %s (`%s`, id `%s`)" % (c.get("title"), c.get("slug"), c.get("id")), "",
                  "- noCode: `%s`" % st.get("noCode"),
                  "- requiresApproval: `%s`" % st.get("requiresApproval"),
                  "- validUntil (stage deadline): `%s`" % st.get("validUntil"), ""]
        crit = st.get("scoringCriteria") or []
        if crit:
            lines += ["### Scoring criteria", "", "| # | title | weight | description |", "|---|---|---|---|"]
            for i, cr in enumerate(crit, 1):
                desc = (cr.get("description") or "").replace("\n", " ").replace("|", "\\|")
                lines.append("| %d | %s | %s | %s |" % (i, cr.get("title"), cr.get("weight"), desc))
            lines.append("")
        else:
            lines += ["No scoring criteria on the current stage.", ""]
        pre = st.get("submissionPreamble")
        lines += ["### Submission preamble", "", pre if pre else "(empty)", ""]
    lines += ["## Raw response", "", "```json", json.dumps(data, indent=1, sort_keys=True), "```", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", default=DEFAULT_SLUG)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.dry_run:
        print(QUERY)
        print("\nvariables:", json.dumps({"slug": args.slug}))
        print("output:", args.out)
        print("credentials:", common.credential_source() or "NONE")
        return 0
    data, err = None, None
    try:
        data = run_query(args.slug)
    except Exception as e:  # noqa: BLE001
        err = repr(e)
    text = render(args.slug, data, err)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text)
    print(text)
    return 0 if err is None else 1


if __name__ == "__main__":
    sys.exit(main())
