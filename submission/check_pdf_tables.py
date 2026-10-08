#!/usr/bin/env python3
"""Check that report.pdf renders the data rows of Tables 1.1, C2, E1 and E2 of report.md.

Usage: python3 submission/check_pdf_tables.py submission/report.md <pdftotext -layout output>

For each table the script takes the data rows from the markdown and builds a signature per row
from a run of short adjacent cells (numbers and names that do not wrap in the PDF). It then
searches the whitespace-collapsed PDF text for every signature. The check fails if any row is
missing, so the PDF row count equals the markdown row count.
"""
import re
import sys

md_path, txt_path = sys.argv[1], sys.argv[2]
md = open(md_path, encoding="utf-8").read().splitlines()
pdf = re.sub(r"\s+", " ", open(txt_path, encoding="utf-8").read())

# anchor text, cell indices used for the signature
TABLES = {
    "1.1": ("`[F]` Table 1.1.", range(1, 8)),
    "C2": ("<!-- TABLE:C2_literature -->", range(1, 5)),
    "E1": ("<!-- TABLE:E1_h2emulator -->", range(1, 6)),
    "E2": ("<!-- TABLE:E2_h22e -->", range(1, 7)),
}


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
        sig = " ".join(r[c] for c in cols)
        if sig in pdf:
            found += 1
        else:
            print(f"  Table {name}: row not found in PDF text: {sig!r}")
    status = "ok" if found == len(rows) else "FAILED"
    fail |= found != len(rows)
    print(f"Table {name}: markdown rows {len(rows)}, rows found in PDF {found}: {status}")
sys.exit(1 if fail else 0)
