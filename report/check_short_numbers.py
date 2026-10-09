"""Check that every number in report/report_short.md appears in the sources it cites.

Usage: python report/check_short_numbers.py [report/report_short.md]

Sources: report/report_v5.md, value/*.md, results/*.md, results/repro_2026-10-08/repro_log.md,
docs/*.md and bench/family_C/manifest.csv. A number is a token of digits with optional
thousands commas, decimals, dotted parts (versions, section numbers) or an exponent.
Tokens glued to letters or underscores (P0, H2, tof_3, mod5_4) are identifiers and are skipped.
Commas are removed before matching. Matching is exact on the remaining string, so 0.10 and 0.1
are different numbers. Exit code 1 if any number is missing.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)*(?:e[-+]?\d+)?)(?!\w)")
SOURCES = (
    ["report/report_v5.md"]
    + sorted(glob.glob("value/*.md", root_dir=ROOT))
    + sorted(glob.glob("results/*.md", root_dir=ROOT))
    + ["results/repro_2026-10-08/repro_log.md"]
    + sorted(glob.glob("docs/*.md", root_dir=ROOT))
    + ["bench/family_C/manifest.csv"]
)


def numbers(text):
    return [m.group(1).replace(",", "") for m in NUM.finditer(text)]


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "report", "report_short.md")
    found = {}
    for rel in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"source missing: {rel}")
            continue
        for n in set(numbers(open(path, encoding="utf-8").read())):
            found.setdefault(n, rel)
    lines = open(target, encoding="utf-8").read().splitlines()
    missing = []
    total = set()
    for i, line in enumerate(lines, 1):
        for n in numbers(line):
            total.add(n)
            if n not in found:
                missing.append((i, n, line.strip()[:100]))
    print(f"{len(total)} distinct numbers in {os.path.relpath(target, ROOT)}, "
          f"{len(total) - len({n for _, n, _ in missing})} found in sources, "
          f"{len({n for _, n, _ in missing})} missing")
    for i, n, ctx in missing:
        print(f"MISSING line {i}: {n}  | {ctx}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
