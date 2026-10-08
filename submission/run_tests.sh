#!/usr/bin/env bash
# Runs every test file once from the repository root and writes one log per file
# plus a summary to submission/build_logs/. Rerunnable.
cd "$(dirname "$0")/.."
# 16 test files: 7 run as scripts, 9 under pytest. See REPRODUCE.md (Tests).
LOG=submission/build_logs
mkdir -p "$LOG"
: > "$LOG/tests_summary.txt"
run() {
  name="$1"; shift
  start=$(date +%s)
  "$@" > "$LOG/test_${name}.log" 2>&1
  rc=$?
  end=$(date +%s)
  echo "$name | rc=$rc | wall=$((end-start))s | cmd: $*" >> "$LOG/tests_summary.txt"
}
run gen_trotter   python bench/test_gen_trotter.py
run dm_sim        python noise/test_dm_sim.py
run certificate   python barrier/test_certificate.py
run compile       python pipelines/test_compile.py
run pass_select   python pipelines/test_pass_select.py
run selene        env HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python -m pytest selene/test_selene.py -q
run cost_model    python model/test_cost_model.py
run submit        python -m pytest submit/test_submit.py -q
run h22e_stats    python -m pytest submit/test_h22e_stats.py -q
run h22e_pooled   python -m pytest submit/test_h22e_pooled.py -q
run value_ledger  python -m pytest value/test_value_ledger.py -q
run value_by_app  python -m pytest value/test_value_by_application.py -q
run selector_ledger python -m pytest value/test_selector_ledger.py -q
run c2_literature python report/test_c2_literature.py
run notebook_submit python -m pytest report/test_notebook_submit.py -q
run finals_plan   python -m pytest value/test_finals_plan.py -q
echo done >> "$LOG/tests_summary.txt"
