#!/usr/bin/env bash
# Rebuilds the submission package from the repository at HEAD. Nothing is uploaded.
# Usage: submission/build.sh [--tests]   (--tests also reruns every test file, about 3 min)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=submission
LOG=$OUT/build_logs
SRC_MAIN=report/report_short.md
SRC_FULL=report/report_v5.md
mkdir -p "$LOG"
: > "$LOG/build.log"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG/build.log"; }

# 0. every number of the short report must occur in its sources
if ! python3 report/check_short_numbers.py "$SRC_MAIN" | tee -a "$LOG/build.log"; then
  log "SHORT REPORT NUMBER CHECK FAILED"; exit 1
fi
log "check_short_numbers.py: every number of $SRC_MAIN found in its sources"

# 1. markdown sources of the two PDFs.
# report.md = report_short.md, the main judge-facing report (copied unchanged).
# report_full.md = report_v5.md without the changelog sections (judges flagged them as noise),
# attached as the technical appendix. The filter leaves report/report_v5.md untouched.
# Figures are copied next to the markdown so each file renders on its own.
cp "$SRC_MAIN" "$OUT/report.md"
log "report.md copied from $SRC_MAIN"
python3 "$OUT/strip_changelog.py" "$SRC_FULL" "$OUT/report_full.md" | tee -a "$LOG/build.log"
mkdir -p "$OUT/figures"
for md in "$OUT/report.md" "$OUT/report_full.md"; do
  for f in $(grep -o '](figures/[^)]*)' "$md" | sed 's/^](//; s/)$//'); do cp "report/$f" "$OUT/$f"; done
  if grep -n -E '\[PENDING|TBD' "$md"; then log "PENDING/TBD CHECK FAILED in $md"; exit 1; fi
  log "$(basename "$md"): no [PENDING or TBD"
done

# 2. PDFs from the markdown (pandoc -> HTML -> wkhtmltopdf).
# pandoc runs with --resource-path=$OUT and --embed-resources, which inlines every image into the intermediate HTML.
log "pandoc $(pandoc --version | head -1 | cut -d' ' -f2), wkhtmltopdf $(wkhtmltopdf --version | cut -d' ' -f2)"
# build_pdf <md> <pdf> <table set of check_pdf_tables.py>
build_pdf() {
  local md="$1" pdf="$2" set="$3"
  local title stem html txt
  title=$(grep -m1 '^# ' "$md" | sed 's/^# //')
  stem=$(basename "$pdf" .pdf)
  html="$LOG/$stem.html"
  pandoc "$md" -f gfm -t html5 --standalone --embed-resources \
    --resource-path="$OUT" --css="$OUT/report.css" \
    --metadata title="$title" --metadata pagetitle="$stem" \
    -o "$html" 2>>"$LOG/build.log"
  # drop the duplicated H1 that --metadata title adds
  python3 - "$html" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r'<header id="title-block-header">.*?</header>', '', s, flags=re.S)
# keep each table caption paragraph, and a heading directly above it, on the same page as its table (see .keep in report.css)
s = re.sub(r'((?:<h[234][^>]*>(?:(?!</h[234]>).)*</h[234]>\s*)?<p>(?:(?!<p>|</p>).)*</p>\s*<table.*?</table>)', r'<div class="keep">\1</div>', s, flags=re.S)
# a section heading directly above a kept block moves into it
s = re.sub(r'(<h[234][^>]*>(?:(?!</h[234]>).)*</h[234]>\s*)<div class="keep">', r'<div class="keep">\1', s, flags=re.S)
# any other heading stays with the paragraph below it
s = re.sub(r'(<h[234][^>]*>(?:(?!</h[234]>).)*</h[234]>\s*<p>(?:(?!</p>).)*</p>)', r'<div class="keep">\1</div>', s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
PY
  wkhtmltopdf --quiet --enable-local-file-access --page-size A4 \
    --margin-top 15mm --margin-bottom 15mm --margin-left 14mm --margin-right 14mm \
    "$html" "$pdf" 2>>"$LOG/build.log" || true
  rm -f "$html"
  test -s "$pdf"
  log "$(basename "$pdf") written from $(basename "$md"), title \"$title\" ($(stat -c %s "$pdf") bytes, $(pdfinfo "$pdf" | awk '/^Pages:/{print $2}') pages)"
  txt=$(mktemp)
  pdftotext -layout "$pdf" "$txt"
  if grep -n -E '\[PENDING|TBD|Changelog' "$txt"; then
    log "PDF TEXT CHECK FAILED ([PENDING, TBD or Changelog in $(basename "$pdf"))"; rm -f "$txt"; exit 1
  fi
  log "$(basename "$pdf") text: no [PENDING, TBD or Changelog"
  if ! python3 "$OUT/check_pdf_tables.py" "$md" "$txt" --set "$set" | tee -a "$LOG/build.log"; then
    log "TABLE ROW CHECK FAILED in $(basename "$pdf")"; rm -f "$txt"; exit 1
  fi
  rm -f "$txt"
}
build_pdf "$OUT/report.md" "$OUT/report.pdf" short
build_pdf "$OUT/report_full.md" "$OUT/report_full.pdf" full

# 3. code.zip = git archive of HEAD (tracked files only, so ignored paths such as
# third_party/, papers/ and any local credentials are excluded).
rm -f "$OUT/code.zip"
# submission/ itself is excluded so a rerun after this folder is committed does not nest the old package
git archive --format=zip HEAD -o "$OUT/code.zip" -- . ':(exclude)submission'
log "code.zip from HEAD $(git rev-parse HEAD), $(stat -c %s $OUT/code.zip) bytes, $(unzip -Z1 $OUT/code.zip | wc -l) entries"
# the code.zip commit is the hash right after "`git archive` of commit" (not the pyzx fork hash)
REPRO_HASH=$(grep -o -E '`git archive` of commit `[0-9a-f]{40}`' "$OUT/REPRODUCE.md" | head -1 | grep -o -E '[0-9a-f]{40}' || true)
if [[ "$REPRO_HASH" != "$(git rev-parse HEAD)" ]]; then
  log "REPRODUCE.md names code.zip commit '${REPRO_HASH}', HEAD is $(git rev-parse HEAD), update its first paragraph"; exit 1
fi
log "REPRODUCE.md names HEAD as the code.zip commit"
if unzip -Z1 "$OUT/code.zip" | grep -E -i '(^|/)credentials\.json$|\.token$|aqora-home|\.local/share/aqora|\.env$|(^|/)\.env' ; then
  log "CREDENTIAL CHECK FAILED (file names)"; exit 1
fi
log "credential check 1: no credentials.json, *.token, *.env, aqora-home in archive listing"
if unzip -Z1 "$OUT/code.zip" | grep -E '^(papers|third_party)/' ; then
  log "EXCLUSION CHECK FAILED (papers/ or third_party/ in archive)"; exit 1
fi
log "exclusion check: no papers/ or third_party/ in archive"
# token strings: grep every member's content (unzip -p streams all members)
if unzip -p "$OUT/code.zip" | grep -a -c -E 'refresh_token|access_token' > "$LOG/token_grep_count.txt"; then
  log "TOKEN STRING CHECK: $(cat $LOG/token_grep_count.txt) lines with refresh_token or access_token, listed below"
  ZT=$(mktemp -d); unzip -q "$OUT/code.zip" -d "$ZT"
  grep -r -n -a -E 'refresh_token|access_token' "$ZT" | sed "s|$ZT/||" | tee -a "$LOG/build.log"
  # a match is a leak only if it carries a value (a long token-like string), not a key name in code or docs
  if grep -r -a -h -E '"?(refresh_token|access_token)"?\s*[:=]\s*"[A-Za-z0-9._-]{20,}"' "$ZT"; then
    rm -rf "$ZT"; log "TOKEN STRING CHECK FAILED (token value present)"; exit 1
  fi
  rm -rf "$ZT"
  log "token string check: matches above are key names only, no token value of 20 or more characters"
else
  log "token string check: no refresh_token or access_token in any archive member"
fi
rm -f "$LOG/token_grep_count.txt"

# 4. optional test rerun
if [[ "${1:-}" == "--tests" ]]; then bash run_tests.sh; log "tests rerun, see $LOG/tests_summary.txt"; fi

# 5. SUMMARY.md number check
RC=0; python3 "$OUT/check_summary_numbers.py" > "$LOG/summary_check.txt" || RC=$?
tail -3 "$LOG/summary_check.txt" | tee -a "$LOG/build.log"; rm -f "$LOG/summary_check.txt"
if [[ $RC -ne 0 ]]; then log "SUMMARY NUMBER CHECK FAILED"; exit 1; fi

# 5b. one-page summary (submission checklist): numbers checked, exactly one A4 page
if ! python3 report/check_short_numbers.py report/one_page_summary.md | tee -a "$LOG/build.log"; then
  log "ONE-PAGE SUMMARY NUMBER CHECK FAILED"; exit 1
fi
pandoc report/one_page_summary.md -f gfm -t html5 --standalone --embed-resources --resource-path=report --css="$OUT/summary.css" \
  --metadata pagetitle=one_page_summary -o "$LOG/one_page_summary.html" 2>>"$LOG/build.log"
wkhtmltopdf --quiet --enable-local-file-access --page-size A4 --margin-top 10mm --margin-bottom 10mm --margin-left 12mm --margin-right 12mm \
  "$LOG/one_page_summary.html" "$OUT/one_page_summary.pdf" 2>>"$LOG/build.log" || true
rm -f "$LOG/one_page_summary.html"
NP=$(pdfinfo "$OUT/one_page_summary.pdf" | awk '/^Pages:/{print $2}')
if [[ "$NP" != "1" ]]; then log "ONE-PAGE SUMMARY HAS $NP PAGES"; exit 1; fi
log "one_page_summary.pdf written, 1 page"
# 5c. README, requirements and execution evidence index next to the reports
python3 submit/evidence_index.py | tee -a "$LOG/build.log"
if ! git diff --quiet -- results/EVIDENCE.md; then log "results/EVIDENCE.md changed on rebuild, commit it first"; exit 1; fi
cp README.md requirements.txt "$OUT/"
cp report/presentation/presentation.pdf report/presentation/presentation.tex "$OUT/"
cp results/EVIDENCE.md "$OUT/EVIDENCE.md"
log "README.md, requirements.txt and EVIDENCE.md copied"

TMPM=$(mktemp)
# 6. manifest (every file under submission/ except MANIFEST.txt itself)
( cd "$OUT" && find . -type f ! -name MANIFEST.txt | sed 's|^\./||' | LC_ALL=C sort | while read -r f; do
    printf '%s  %10d  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c %s "$f")" "$f"; done ) > "$TMPM"
{ echo "# code.zip = git archive of commit $(git rev-parse HEAD) (submission/ excluded)"
  echo "# report.pdf and report.md (main report) built from $SRC_MAIN at that commit"
  echo "# report_full.pdf and report_full.md (technical appendix) built from $SRC_FULL at that commit, changelog sections removed"
  echo "# sha256  size_bytes  path (relative to submission/), generated $(date -u +%FT%TZ)"
  cat "$TMPM"; } > "$OUT/MANIFEST.txt"
rm -f "$TMPM"
log "MANIFEST.txt written"
