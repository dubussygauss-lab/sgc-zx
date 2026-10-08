#!/usr/bin/env python3
"""Write a copy of the report without its changelog sections. The source file is not modified.

Usage: python3 submission/strip_changelog.py report/report_v5.md submission/report.md

A changelog section starts at a level-2 heading whose text begins with "Changelog" and
runs to the next level-2 heading that is not a changelog, or to the end of the file.
The script fails if a "## Changelog" heading survives or if no section was removed.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").read().splitlines(keepends=True)
out, skipping, removed = [], False, 0
in_fence = False
for line in lines:
    if line.startswith("```"):
        in_fence = not in_fence
    if not in_fence and line.startswith("## "):
        skipping = bool(re.match(r"## Changelog\b", line))
        removed += skipping
    if not skipping:
        out.append(line)
text = "".join(out).rstrip("\n") + "\n"
assert removed > 0, "no changelog section found"
assert not re.search(r"^## Changelog", text, flags=re.M), "changelog heading survived"
open(dst, "w", encoding="utf-8").write(text)
print(f"{src}: {len(lines)} lines -> {dst}: {len(text.splitlines())} lines, {removed} changelog sections removed")
