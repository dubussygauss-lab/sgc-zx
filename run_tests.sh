#!/usr/bin/env bash
# Runs every test file once from the repository root and writes one log per file
# plus a summary to submission/build_logs/ (or $TEST_LOG_DIR). Rerunnable from the repository root or from an unzipped code.zip.
cd "$(dirname "$0")"
# 28 test files: 8 run as scripts, 20 under pytest. See REPRODUCE.md (Tests).
LOG="${TEST_LOG_DIR:-submission/build_logs}"
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
run official_baseline python -m pytest pipelines/test_official_baseline.py -q
run family_C_selector python -m pytest value/test_family_C_selector.py -q
run usecase       python -m pytest value/test_usecase.py -q
run equiv_family_C python -m pytest pipelines/test_equiv_family_C.py -q
run evidence_index python -m pytest submit/test_evidence_index.py -q
run famC_h22e   python -m pytest submit/test_famC_h22e.py -q
run h22e_confirmatory python -m pytest submit/test_h22e_confirmatory.py -q
run strong_baselines python -m pytest pipelines/test_strong_baselines.py -q
run psel4         python pipelines/test_psel4.py
run equiv_psel4_C python -m pytest pipelines/test_equiv_psel4_C.py -q
run zx_classifier python -m pytest value/test_zx_classifier.py -q
run h22e_famC_nz python -m pytest submit/test_h22e_famC_nz.py -q
echo done >> "$LOG/tests_summary.txt"
