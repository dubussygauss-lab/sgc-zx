# Verification 2026-10-09i: fixes of verification 2026-10-09h

Independent verifier. Repository `/home/claude/sgc-zx`, HEAD `40342bf`, working tree clean before this file was written. Fix commit `05ebd46`, package rebuild `40342bf`. No tracked file was edited. `[F]` = checked against files or recomputed, `[O]` = judgement.

## Verdict

**PASS WITH ISSUES.**

`[F]` All twelve findings F1 to F12 of `results/verification_2026-10-09h.md` are resolved. All 21 test files return rc=0 from a fresh unzip of `submission/code.zip`. `code.zip` equals `git archive 05ebd46` minus `submission/` (2431 files, identical names and contents). The six emulator and fetch logs are in the zip and hold no token or secret. All 20 pins in `requirements.txt` equal `pip list`, mqt-qcec 3.10.2 included. `one_page_summary.pdf` is one A4 page, and every changed sentence matches its source.

`[O]` No new finding blocks submission. One residual instance of the F5 rounding remains in the technical appendix (N1). The other new items are Low or informational.

## F1 to F12

| ID | Resolved | Evidence |
|---|---|---|
| F1 run_tests.sh not in zip | yes | `[F]` `05ebd46` moves `submission/run_tests.sh` to `run_tests.sh` and changes it to `cd "$(dirname "$0")"` and `LOG="${TEST_LOG_DIR:-submission/build_logs}"`. The README line 10 command is now `bash run_tests.sh`. Run from a fresh unzip with `TEST_LOG_DIR=$PWD/tlogs`: 21 of 21 files rc=0, script rc=0, summed wall 254 s (table below). |
| F2 logs cited but not shipped | yes | `[F]` `.gitignore` gains `!results/emu_*.log` and `!results/fetch_*.log`. `emu_A.log` (94 lines), `emu_B1.log` (42), `emu_B1_rest.log` (31), `emu_h22e.log` (19), `fetch_A_job1.log` (2) and `fetch_B1_job1.log` (2) are tracked and in `code.zip`, byte-identical to the repo (`diff -r`). They hold only job IDs, platforms, circuit names, HQC estimates and statuses. A grep for `token|secret|password|bearer|authorization|api_key|cookie|credential`, JWT, `ghp_`, `sk-` and `AKIA` patterns finds nothing in them. `results/EVIDENCE.md` line 94 now points to files that exist. |
| F3 README notebook row says H2-2E | yes | `[F]` README line 37 now reads "gated submission to the free syntax checker `nexus:H2-2SC`". This matches `PLATFORM = "nexus:H2-2SC"` (notebook line 131) and `require_free_checker` (line 474). |
| F4 mqt-qcec not pinned | yes | `[F]` `requirements.txt` line 13 is `mqt-qcec==3.10.2`. `pip list` gives 3.10.2. All 20 pins match (list under Commands). `submission/requirements.txt` is identical. |
| F5 bound rounded favourably | yes in the four files named. One residual (N1) | `[F]` 1 − 2478/2496 = 0.0072115, i.e. 0.721 %. `report_short.md` lines 99 and 248, `report_v5.md` lines 124 and 176, `sec1_v5.md` lines 107 and 159 and `submission/SUMMARY.md` line 39 now say "0.72 %", and say "at least 2478 of its 2496 T gates" or "99.28 % ... (2478 of 2496, rounded to two decimals)". 2478/2496 = 0.992788 rounds to 99.28 % and is now labelled as rounded, not as a lower bound. haar_n3_eps1e-03_s5 is the minimum-ratio row of `results/certificates.csv`. No "at least 99.28 %" and no "0.7 %" bound remains in these files. |
| F6 README stale test counts and notebook details | yes | `[F]` The "Six run as scripts" and "Five run under pytest" blocks are replaced by line 96: 21 files, seven scripts, fourteen pytest. `run_tests.sh` has 21 `run` lines: 7 `python <file>` and 14 `python -m pytest`. `TEAM_ORG` is "in the setup cell", which is the imports-and-constants cell at notebook lines 96 to 132. `SGC_NOTEBOOK_SUBMIT_SC=1` is stated and matches line 604. The button label matches line 592. The unpinned `pip install` is replaced by `pip install -r requirements.txt`. Line 115 is correct: requirements.txt pins every package in line 109 and also guppylang, hugr, scikit-learn, sympy, networkx, mqt-qcec and pytest. |
| F7 0.997 ambiguous, n missing | yes | `[F]` `one_page_summary.md` line 19 now reads "On 20 synthesised Haar circuits of 2 and 3 qubits the certified floor is 0.997 of the T-count left after ZX, pooled". Recomputed from the B2 rows of `results/certificates.csv`: floor 41,414 over t_zx 41,534 = 0.99711, and the n values are {2, 3}. t_zx_P1 equals t_zx_P2 on all 20 rows. The pooled gain bound is 0.2889 % ≤ 0.3 %. |
| F8 snapped angles not stated | yes | `[F]` Line 11 now adds "three of them after snapping angles by at most 5.27e-12 half-turns (App. 3.8)". From `results/family_C_equivalence.csv` (PyZX, proven, comparison = PSEL pick in `value/family_C_selector.csv`), 18 circuits are proven. Three have a nonzero snap: draper_adder_10 (P0, 4.35e-14), draper_adder_16 (P0, 5.27e-12) and rgqft_mult_6 (P2, 8.88e-16). All three have `continuous_angles` True. The other 15 have snap 0. The maximum over all 54 proven PyZX rows is also 5.27e-12. |
| F9 "saves most on" holds for family C only | yes | `[F]` Line 24 now begins "On family C PSEL saves most on arithmetic subroutines". Recomputed from `value/family_C_selector.csv`: total 4104.4 HQC. Multipliers give 3356.0 (rgqft_mult_6 2239.0, hrs_mult_5 1117.0) and adders 745.6, together 99.93 %. The MCX oracles give 2.8 and the QFT adders 0. See N3 for the anchors of the rest of the sentence. |
| F10 HQC estimate and power assumption | yes | `[F]` Line 20 reads "5933.2 HQC by the cost formula". Line 28 is now tagged `[O]` and reads "power 0.80 if the emulator gain holds on hardware". |
| F11 REPRODUCE omits the exclusion | yes | `[F]` `submission/REPRODUCE.md` line 3 reads "`git archive` of commit `05ebd46cb49e4a6bfb18c9cdd05cb575ce17cba4` with `submission/` excluded". `MANIFEST.txt` line 1 and the zip comment (`05ebd46cb49e4a6bfb18c9cdd05cb575ce17cba4`) agree. The zip file list equals `git ls-tree -r 05ebd46` minus the 44 `submission/` paths (2431 = 2431, symmetric difference empty), and `diff -r` against the extracted `git archive 05ebd46` shows only `Only in arch: submission` plus the `__pycache__` and `tlogs` the test run created. `git diff 05ebd46 40342bf` outside `submission/` is empty. |
| F12 tag on "not established" | yes | `[F]` Line 20 now keeps the sentence under the bullet's `[F]` tag, as "The fidelity gain is therefore not established at 0.05 after correction". `report_short.md` was not changed, which the earlier report called optional. |

### Test run from the fresh unzip (`tlogs/tests_summary.txt`)

| File | rc | Result in log | Wall |
|---|---|---|---|
| bench/test_gen_trotter.py | 0 | 12/12 passed | 66 s |
| noise/test_dm_sim.py | 0 | 17/17 passed | 6 s |
| barrier/test_certificate.py | 0 | 69/69 checks passed | 44 s |
| pipelines/test_compile.py | 0 | 6 ok, all tests passed | 4 s |
| pipelines/test_pass_select.py | 0 | 3 ok, all tests passed | 6 s |
| selene/test_selene.py (proxy cleared) | 0 | 6 passed | 9 s |
| model/test_cost_model.py | 0 | 7 ok | 1 s |
| submit/test_submit.py | 0 | 11 passed | 5 s |
| submit/test_h22e_stats.py | 0 | 7 passed | 5 s |
| submit/test_h22e_pooled.py | 0 | 10 passed | 11 s |
| value/test_value_ledger.py | 0 | 5 passed | 4 s |
| value/test_value_by_application.py | 0 | 5 passed | 2 s |
| value/test_selector_ledger.py | 0 | 4 passed | 1 s |
| report/test_c2_literature.py | 0 | all checks passed | 1 s |
| report/test_notebook_submit.py | 0 | 20 passed | 2 s |
| value/test_finals_plan.py | 0 | 5 passed | 9 s |
| pipelines/test_official_baseline.py | 0 | 10 passed | 17 s |
| value/test_family_C_selector.py | 0 | 5 passed | 2 s |
| value/test_usecase.py | 0 | 7 passed | 54 s |
| pipelines/test_equiv_family_C.py | 0 | 2 passed | 3 s |
| submit/test_evidence_index.py | 0 | 3 passed | 2 s |

`[F]` The pass counts equal the Result column of `submission/REPRODUCE.md` for all 21 files.

### Other checks with no finding

- `[F]` `one_page_summary.pdf`: `pdfinfo` gives Pages: 1, A4. Rendered at 70 dpi, nothing is clipped. Every changed phrase of `one_page_summary.md` is in the PDF text. `report/check_short_numbers.py report/one_page_summary.md` finds 67 of 67 numbers. `submission/check_summary_numbers.py` finds 138 of 138.
- `[F]` `report/sec1_v5.md` is a verbatim substring of `report/report_v5.md` (Python `in`, 28,768 characters).
- `[F]` `submission/report.md` and `submission/report_full.md` carry the same reworded sentences as their sources.
- `[F]` `code.zip` credential scan: there is no `.env`, `credentials*`, `*.pem`, `*.key` or `*.token` file. The only JWT-prefix hit is base64 PNG data in `report/notebook_executed.html` and `report/__marimo__/session/notebook_skeleton.py.json`. No `eyJ….eyJ…` JWT exists. `AQORA_TOKEN` appears only as an environment-variable name in `submit/common.py` and `submit/read_rubric.py`, and as the placeholder `"abc"` in `submit/test_submit.py` line 136.
- `[F]` README against the notebook and `run_tests.sh`: no remaining contradiction found in lines 10, 15, 37, 87, 96 or 105. README line 10 says the logs go to `submission/build_logs/`. Inside the unzipped tree that folder does not exist beforehand, and `run_tests.sh` creates it with `mkdir -p`.

## New findings

Ordered by severity, then by document order.

**N1. Low. `report/report_v5.md` line 1062 (Section 7 Limitations, = `submission/report_full.md` line 1062).** `[F]` "On family B2 the floor is at least 99.28 % of the post-ZX T-count on every instance." The minimum is 2478/2496 = 99.2788 %. This is the same favourable rounding of a lower bound as F5, left in the technical appendix. Proposed fix: "at least 99.27 %", or "at least 2478 of 2496 (99.28 % rounded) on the worst instance".

**N2. Low. `report/report_v5.md` line 977 and the Section 5 test table.** `[F]` "Seven files run as scripts. Twelve files run under pytest." The Section 5 table lists 19 files. `run_tests.sh`, README line 96 and `REPRODUCE.md` line 78 list 21. `report/test_notebook_submit.py` and `submit/test_evidence_index.py` are missing from Section 5. `report_short.md` line 291 ("The test table of Appendix 5 lists 19 test files") describes Appendix 5 correctly but inherits the gap. Proposed fix: add the two files to Section 5 and change the counts to 14 and 21.

**N3. Low, PLAUSIBLE. `report/one_page_summary.md` line 24, Relevance sentence.** `[F]` The first clause is correct (see F9). The anchors of the second clause do not fully carry it.
- App. 1.3 ("What it saves on the fault-tolerant layer") places no circuit in an application.
- Derivative pricing is placed in App. 1.5 (report_v5 line 160), which the sentence does not cite.
- App. 1.4 (Table 1.3) places B1 and B1x circuits. Its elliptic-curve entry is the GF(2^m) multipliers, and family C contains none of them.
- The two family C multipliers that carry 81.8 % of the saving are integer multipliers (Häner et al., Ruiz-Perez and Garcia-Escartin). App. 1.4 places the Häner et al. arithmetic under chemistry and simulation oracles.

`[O]` The sentence holds at the level of "adders and multipliers in general". Its ECDLP placement for family C is not supported by the cited sections. Proposed fix: cite "App. 1.4, 1.5", and either drop "elliptic-curve discrete log" or say "the same kinds of subroutines that the cited literature places in ...".

**N4. Low. `submission/REPRODUCE.md` lines 7 to 15.** `[F]` The "Equivalent explicit command" leaves out mqt-qcec, sympy, networkx and hugr, and leaves pytest unpinned. It is therefore not equivalent to `requirements.txt`, and a run of `pipelines/equiv_family_C.py` with its default `--methods` fails in an environment built from it (the F4 problem). The version list on line 7 also omits mqt-qcec, sympy and networkx. Proposed fix: delete the explicit command, or make it match `requirements.txt`.

**N5. Low. `submission/REPRODUCE.md` lines 78 to 102, Wall column.** `[F]` The text says the results come from the run "stored in `build_logs/tests_summary.txt`". The Wall column differs from that file on 19 of 21 rows, for example certificate 30 s against 47 s, selene 23 s against 10 s, usecase 36 s against 55 s. The pass counts match. Proposed fix: regenerate the Wall column from `tests_summary.txt`, or drop it.

**N6. Low. `README.md` lines 3 and 32 (= `submission/README.md`).** `[F]` "The current submission report is `report/report_v5.md`" and "Submission report, draft v5 (current)". `REPRODUCE.md` line 3 and the package say the main report is `report.pdf`, built from `report/report_short.md`, and that report_v5 is the technical appendix. Proposed fix: "The main report is `report/report_short.md`; `report/report_v5.md` is the technical appendix."

**N7. Low. `README.md` lines 68 to 69 against line 79.** `[F]` Step 7, `python noise/run_proxy.py --workers 2`, runs with the default `--noise typical` and writes `results/family_A_proxy.csv` (`noise/run_proxy.py` lines 501 and 517). Line 79 says Table A4 comes from `results/family_A_proxy_h22e.csv`. That file needs `--noise h22e --family A`, as `REPRODUCE.md` gives it. This finding predates 05ebd46. Proposed fix: use the REPRODUCE commands in step 7.

**N8. Info. "at most 0.72 %" (all files of F5).** `[F]` The exact worst-instance bound is 18/2496 = 0.7212 %. Two-decimal rounding still understates the upper bound by 0.0012 percentage points. `[O]` This is the fix proposed in 09h and is negligible. If exactness matters, "0.73 %" or "18 of 2496" removes it.

**N9. Info. `submission/REPRODUCE.md` line 31.** `[F]` It describes `results/proxy_h22e_fits.log` as "an exception to the `*.log` rule". It is now one of three exception patterns, with `emu_*.log` and `fetch_*.log`. The statement is incomplete, not wrong.

## Commands run

```
git log --oneline -5; git status --short; git show --stat 05ebd46 40342bf
git show 05ebd46 -- .gitignore README.md report/ requirements.txt run_tests.sh submission/run_tests.sh
git show 40342bf -- submission/REPRODUCE.md submission/build.sh submission/SUMMARY.md
unzip -q submission/code.zip -d scratchpad/vi/unz; unzip -z submission/code.zip
(cd scratchpad/vi/unz && TEST_LOG_DIR=$PWD/tlogs bash run_tests.sh)      # rc=0, 21/21 rc=0
grep result lines of tlogs/test_*.log; grep -c '^ok ' for script tests
git archive 05ebd46 | tar -x -C scratchpad/vi/arch; diff -r -q arch unz
python3 (zipfile) zip file list vs git ls-tree -r 05ebd46 minus submission/
git diff --stat 05ebd46 40342bf -- . ':(exclude)submission'
grep -inE secret/token patterns in results/emu_*.log results/fetch_*.log and the unzipped tree
python3 (pip list --format=json) vs requirements.txt pins
grep -nE in report/notebook_skeleton.py for TEAM_ORG, PLATFORM, SGC_NOTEBOOK_SUBMIT_SC, run_button
pdfinfo, pdftotext -layout, pdftoppm -r 70 on submission/one_page_summary.pdf
python3 (csv) results/certificates.csv B2 pooled and worst-instance ratios; 1 - 2478/2496
python3 (csv) results/family_C_equivalence.csv x value/family_C_selector.csv x bench/family_C/manifest.csv snap per PSEL pick
python3 (csv) value/family_C_selector.csv savings ranking
python3 -c "open('report/sec1_v5.md').read() in open('report/report_v5.md').read()"
grep -nE '0\.7 %|0\.72 %|99\.28|2478' across report_short, report_v5, sec1_v5, SUMMARY, one_page_summary, submission/report*.md
python3 report/check_short_numbers.py report/one_page_summary.md      # 67/67
python3 submission/check_summary_numbers.py                           # 138/138
python3 REPRODUCE Wall column vs submission/build_logs/tests_summary.txt
grep add_argument noise/run_proxy.py; sed report_v5.md sections 1.3, 1.4, 3.8, 5
```
