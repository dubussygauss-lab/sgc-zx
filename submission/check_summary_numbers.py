#!/usr/bin/env python3
"""Check every number of submission/SUMMARY.md against its sources, plus the style rules.

Usage: python3 submission/check_summary_numbers.py

Sources: report/report_v5.md (changelog sections excluded), value/*.md, value/*.csv,
docs/hqc_pricing.md and docs/applications_value.md. Dotted versions such as 2.18.5 are
matched as whole tokens.
A number is a token such as 743.2, 14,772.8, +0.0050 or 20462 outside code spans,
arXiv identifiers and alphanumeric names (B1, P0, H2-2E, hwb8, GF(2^m)). Each number must
occur in a source with no digit, comma-digit or decimal continuing it on either side.
Style rules checked: no semicolon, no em-dash, no "rather than", no hedge adverb, at most
two commas per sentence outside lists ("A, B and C") and thousands separators.
"""
import glob
import re
import sys

ROOT = __file__.rsplit("/submission/", 1)[0] if "/submission/" in __file__ else "."
summ = open(f"{ROOT}/submission/SUMMARY.md", encoding="utf-8").read()
rep = open(f"{ROOT}/report/report_v5.md", encoding="utf-8").read()
rep = re.split(r"^## Changelog", rep, flags=re.M)[0]
srcs = {"report_v5.md": rep}
for p in sorted(glob.glob(f"{ROOT}/value/*.md") + glob.glob(f"{ROOT}/value/*.csv")):
    srcs[p.split("/submission/")[-1].replace(ROOT + "/", "")] = open(p, encoding="utf-8").read()
for p in ["docs/hqc_pricing.md", "docs/applications_value.md"]:
    srcs[p] = open(f"{ROOT}/{p}", encoding="utf-8").read()

# body text only: drop the files table and code spans, arXiv ids and alphanumeric names
body = summ.split("## Files in this package")[0]
text = re.sub(r"`[^`]*`", " ", body)
text = re.sub(r"arXiv:\S+", " ", text)
text = re.sub(r"GF\(2\^m\)|F_H\(P\d\)", " ", text)
text = re.sub(r"\b[A-Za-z_][\w-]*\d[\w-]*\b", " ", text)  # B1, P0, H2-2E, hwb8, mod5_4, 2-sd
text = re.sub(r"\b\d+-sd\b", " ", text)
versions = sorted(set(re.findall(r"(?<![\w.])\d+\.\d+\.\d+(?![\w.])", text)))
text = re.sub(r"(?<![\w.])\d+\.\d+\.\d+(?![\w.])", " ", text)
nums = re.findall(r"(?<![\w.])[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])[+-]?\d+(?:\.\d+)?(?![\w])", text)

fail = 0
seen = []
for v in versions:
    seen.append(v)
    hits = [k for k, src in srcs.items() if re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])(?!\.\d)", src)]
    if hits:
        print(f"ok    {v:>10}  {hits[0]}" + (f" (+{len(hits)-1})" if len(hits) > 1 else ""))
    else:
        print(f"MISS  {v:>10}  not found in sources")
        fail += 1
for n in nums:
    if n in seen:
        continue
    seen.append(n)
    pat = re.compile(r"(?<![\d.])(?<!\d,)" + re.escape(n) + r"(?![\d])(?!\.\d)(?!,\d{3})")
    hits = [k for k, s in srcs.items() if pat.search(s)]
    if hits:
        print(f"ok    {n:>10}  {hits[0]}" + (f" (+{len(hits)-1})" if len(hits) > 1 else ""))
    else:
        print(f"MISS  {n:>10}  not found in report_v5.md or value/")
        fail += 1

# style checks on the prose (headings and table excluded)
prose = "\n".join(l for l in body.splitlines() if l and not l.startswith(("#", "|")))
style = []
if ";" in prose: style.append("semicolon")
if "—" in prose: style.append("em-dash")
if re.search(r"rather than", prose, re.I): style.append("'rather than'")
for w in ["usually", "in general", "generally", "typically", "roughly", "approximately", "largely", "mostly", "arguably", "somewhat", "relatively", "fairly"]:
    if re.search(rf"\b{w}\b", prose, re.I): style.append(f"hedge '{w}'")
for s in re.split(r"(?<=[.?])\s+", re.sub(r"`[^`]*`", "X", prose)):
    s2 = re.sub(r"\d,\d", "dd", s)
    c = s2.count(",")
    is_list = bool(re.search(r",[^,]* and [^,]*$", s2)) or bool(re.search(r",[^,]* and ", s2))
    if c > 2 and not is_list:
        style.append(f"{c} commas: {s[:70]}")
for x in style:
    print("STYLE ", x)
print(f"{len(seen)} distinct numbers, {len(seen) - fail} found, {fail} missing, {len(style)} style issues")
sys.exit(1 if fail or style else 0)
