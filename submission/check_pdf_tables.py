#!/usr/bin/env python3
"""Check that a PDF renders every data row of the main tables of its markdown source.

Usage: python3 submission/check_pdf_tables.py <report md> <pdftotext -layout output> [--set full|short]

--set full (default) checks Tables 1.1a, 1.1, C2, E1 and E2 of the full report
(submission/report_full.md). --set short checks Tables 1, 1b, 1c, 2, 2b, 3a, 3b, 4a and 4b,
the official-baseline table, the use-case table and the finals-plan table of the short
report (submission/report.md).

For each table the script takes the data rows from the markdown and builds a signature per row
from a run of short adjacent cells (numbers and names that do not wrap in the PDF). It then
searches the whitespace-collapsed PDF text for every signature. The check fails if any row is
missing, so the PDF row count equals the markdown row count.
"""
import re
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--set")]
which = "full"
for i, a in enumerate(sys.argv):
    if a == "--set":
        which = sys.argv[i + 1]
        args.remove(which)
    elif a.startswith("--set="):
        which = a.split("=", 1)[1]
md_path, txt_path = args[0], args[1]
md = open(md_path, encoding="utf-8").read().splitlines()
pdf = re.sub(r"\s+", " ", open(txt_path, encoding="utf-8").read())

# anchor text, cell indices used for the signature (short cells that do not wrap)
SETS = {
    "full": {
        "1.1a": ("`[F]` Table 1.1a.", range(1, 10)),
        "1.1": ("`[F]` Table 1.1.", range(1, 8)),
        "C2": ("<!-- TABLE:C2_literature -->", range(1, 5)),
        "E1": ("<!-- TABLE:E1_h2emulator -->", range(1, 6)),
        "E2": ("<!-- TABLE:E2_h22e -->", range(1, 7)),
    },
    "short": {
        "1": ("`[F]` Table 1.", range(2, 9)),
        "1b": ("`[F]` Table 1b.", range(1, 6)),
        "1c": ("`[F]` Table 1c.", range(1, 5)),
        "official baseline": ("`[F]` Our P0 reproduces the pass", range(0, 3)),
        "2": ("`[F]` Table 2.", range(5, 10)),
        "2b": ("`[F]` Table 2b.", range(3, 9)),
        "3a": ("`[F]` Table 3a.", range(0, 6)),
        "3b": ("`[F]` Table 3b.", range(0, 5)),
        "4a": ("`[F]` Table 4a.", range(0, 6)),
        "4b": ("`[F]` Table 4b.", range(0, 6)),
        "use case": ("`[F]` Two complete Grover searches", range(0, 9)),
        "finals plan": ("`[F]` `value/finals_plan.py` sizes", range(2, 5)),
    },
}
TABLES = SETS[which]


def table_rows(anchor):
    i = next(k for k, l in enumerate(md) if l.startswith(anchor))
    while not md[i].startswith("|"):
        i += 1
    rows = []
    while i < len(md) and md[i].startswith("|"):
        rows.append([c.strip() for c in md[i].strip().strip("|").split("|")])
        i += 1
    return rows[2:]  # drop header and separator


fail = False
for name, (anchor, cols) in TABLES.items():
    rows = table_rows(anchor)
    found = 0
    for r in rows:
        sig = re.sub(r"\s+", " ", " ".join(r[c] for c in cols)).strip()
        if sig in pdf:
            found += 1
        else:
            print(f"  Table {name}: row not found in PDF text: {sig!r}")
    status = "ok" if found == len(rows) else "FAILED"
    fail |= found != len(rows)
    print(f"Table {name}: markdown rows {len(rows)}, rows found in PDF {found}: {status}")
sys.exit(1 if fail else 0)
