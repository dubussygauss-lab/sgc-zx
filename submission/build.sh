#!/usr/bin/env bash
# Rebuilds the submission package from the repository at HEAD. Nothing is uploaded.
# Usage: submission/build.sh [--tests]   (--tests also reruns every test file, about 3 min)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=submission
LOG=$OUT/build_logs
SRC=report/report_v5.md
mkdir -p "$LOG"
: > "$LOG/build.log"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG/build.log"; }

# 1. report.md = report_v5.md without the changelog sections (judges flagged them as noise).
# The filter writes a stripped copy and leaves report/report_v5.md untouched.
# Figures are copied next to report.md so the markdown renders on its own.
python3 "$OUT/strip_changelog.py" "$SRC" "$OUT/report.md" | tee -a "$LOG/build.log"
mkdir -p "$OUT/figures"
for f in $(grep -o '](figures/[^)]*)' "$OUT/report.md" | sed 's/^](//; s/)$//'); do cp "report/$f" "$OUT/$f"; done
if grep -n -E '\[PENDING|TBD' "$OUT/report.md"; then log "PENDING/TBD CHECK FAILED in report.md"; exit 1; fi
log "report.md: no [PENDING or TBD"

# 2. report.pdf from report.md (pandoc -> HTML -> wkhtmltopdf).
# pandoc runs with --resource-path=$OUT and --embed-resources, which inlines every image into the intermediate HTML.
log "pandoc $(pandoc --version | head -1 | cut -d' ' -f2), wkhtmltopdf $(wkhtmltopdf --version | cut -d' ' -f2)"
HTML="$LOG/report_v5.html"
pandoc "$OUT/report.md" -f gfm -t html5 --standalone --embed-resources \
  --resource-path="$OUT" --css="$OUT/report.css" \
  --metadata title="A pass selector keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2" \
  --metadata pagetitle="report_v5" \
  -o "$HTML" 2>>"$LOG/build.log"
# drop the duplicated H1 that --metadata title adds
python3 - "$HTML" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r'<header id="title-block-header">.*?</header>', '', s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
PY
wkhtmltopdf --quiet --enable-local-file-access --page-size A4 \
  --margin-top 15mm --margin-bottom 15mm --margin-left 14mm --margin-right 14mm \
  "$HTML" "$OUT/report.pdf" 2>>"$LOG/build.log" || true
rm -f "$HTML"
test -s "$OUT/report.pdf"
log "report.pdf written ($(stat -c %s $OUT/report.pdf) bytes, $(pdfinfo $OUT/report.pdf | awk '/^Pages:/{print $2}') pages)"
PDFTXT=$(mktemp)
pdftotext -layout "$OUT/report.pdf" "$PDFTXT"
if grep -n -E '\[PENDING|TBD|Changelog' "$PDFTXT"; then log "PDF TEXT CHECK FAILED ([PENDING, TBD or Changelog in report.pdf)"; rm -f "$PDFTXT"; exit 1; fi
log "report.pdf text: no [PENDING, TBD or Changelog"
python3 "$OUT/check_pdf_tables.py" "$OUT/report.md" "$PDFTXT" | tee -a "$LOG/build.log"
rm -f "$PDFTXT"

# 3. code.zip = git archive of HEAD (tracked files only, so ignored paths such as
# third_party/, papers/ and any local credentials are excluded).
rm -f "$OUT/code.zip"
# submission/ itself is excluded so a rerun after this folder is committed does not nest the old package
git archive --format=zip HEAD -o "$OUT/code.zip" -- . ':(exclude)submission'
log "code.zip from HEAD $(git rev-parse HEAD), $(stat -c %s $OUT/code.zip) bytes, $(unzip -Z1 $OUT/code.zip | wc -l) entries"
if ! grep -q "$(git rev-parse HEAD)" "$OUT/REPRODUCE.md"; then
  log "REPRODUCE.md does not name HEAD $(git rev-parse HEAD), update its first paragraph"; exit 1
fi
log "REPRODUCE.md names HEAD"
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
if [[ "${1:-}" == "--tests" ]]; then bash "$OUT/run_tests.sh"; log "tests rerun, see $LOG/tests_summary.txt"; fi

# 5. SUMMARY.md number check
python3 "$OUT/check_summary_numbers.py" | tail -3 | tee -a "$LOG/build.log"

TMPM=$(mktemp)
# 6. manifest (every file under submission/ except MANIFEST.txt itself)
( cd "$OUT" && find . -type f ! -name MANIFEST.txt | sed 's|^\./||' | LC_ALL=C sort | while read -r f; do
    printf '%s  %10d  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c %s "$f")" "$f"; done ) > "$TMPM"
{ echo "# code.zip = git archive of commit $(git rev-parse HEAD) (submission/ excluded)"
  echo "# report.pdf and report.md built from $SRC at that commit, changelog sections removed"
  echo "# sha256  size_bytes  path (relative to submission/), generated $(date -u +%FT%TZ)"
  cat "$TMPM"; } > "$OUT/MANIFEST.txt"
rm -f "$TMPM"
log "MANIFEST.txt written"
