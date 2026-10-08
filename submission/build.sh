#!/usr/bin/env bash
# Rebuilds the submission package from the repository at HEAD. Nothing is uploaded.
# Usage: submission/build.sh [--tests]   (--tests also reruns every test file, about 2 min)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=submission
LOG=$OUT/build_logs
mkdir -p "$LOG"
: > "$LOG/build.log"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG/build.log"; }

# 1. report.pdf from report/report_v3.md (pandoc -> HTML -> wkhtmltopdf).
# Figures are referenced as figures/*.png relative to report/, so pandoc runs with --resource-path=report
# and --embed-resources, which inlines every image into the intermediate HTML.
log "pandoc $(pandoc --version | head -1 | cut -d' ' -f2), wkhtmltopdf $(wkhtmltopdf --version | cut -d' ' -f2)"
pandoc report/report_v3.md -f gfm -t html5 --standalone --embed-resources \
  --resource-path=report --css="$OUT/report.css" \
  --metadata title="A certified resource ledger shows where ZX rewriting pays on Quantinuum H2" \
  --metadata pagetitle="report_v3" \
  -o "$OUT/build_logs/report_v3.html" 2>>"$LOG/build.log"
# drop the duplicated H1 that --metadata title adds
python3 - "$OUT/build_logs/report_v3.html" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r'<header id="title-block-header">.*?</header>', '', s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
PY
wkhtmltopdf --quiet --enable-local-file-access --page-size A4 \
  --margin-top 15mm --margin-bottom 15mm --margin-left 14mm --margin-right 14mm \
  "$OUT/build_logs/report_v3.html" "$OUT/report.pdf" 2>>"$LOG/build.log" || true
test -s "$OUT/report.pdf" && log "report.pdf written ($(stat -c %s $OUT/report.pdf) bytes)"
rm -f "$OUT/build_logs/report_v3.html"

# 2. code.zip = git archive of HEAD (tracked files only).
rm -f "$OUT/code.zip"
# submission/ itself is excluded so a rerun after this folder is committed does not nest the old package
git archive --format=zip HEAD -o "$OUT/code.zip" -- . ':(exclude)submission'
log "code.zip from HEAD $(git rev-parse --short HEAD), $(stat -c %s $OUT/code.zip) bytes, $(unzip -Z1 $OUT/code.zip | wc -l) entries"
if unzip -Z1 "$OUT/code.zip" | grep -E -i 'credentials\.json|\.token$|aqora-home|\.local/share/aqora|\.env$' ; then
  log "CREDENTIAL CHECK FAILED"; exit 1
else
  log "credential check: no credentials.json, *.token, aqora-home, .env in archive listing"
fi

# 3. optional test rerun
if [[ "${1:-}" == "--tests" ]]; then bash "$OUT/run_tests.sh"; log "tests rerun, see $LOG/tests_summary.txt"; fi

TMPM=$(mktemp)
# 4. manifest (every file under submission/ except MANIFEST.txt itself)
( cd "$OUT" && find . -type f ! -name MANIFEST.txt | sed 's|^\./||' | LC_ALL=C sort | while read -r f; do
    printf '%s  %10d  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c %s "$f")" "$f"; done ) > "$TMPM"
{ echo "# sha256  size_bytes  path (relative to submission/), generated $(date -u +%FT%TZ) from HEAD $(git rev-parse --short HEAD)"; cat "$TMPM"; } > "$OUT/MANIFEST.txt"
rm -f "$TMPM"
log "MANIFEST.txt written"
