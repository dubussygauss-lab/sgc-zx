# Reproduction record

Team Learned ZX Rewriting. Recorded 8 October 2026 in the development container and updated 9 October 2026. `code.zip` is `git archive` of commit `537c353b62ace863622a614dddd95e26fd61cac2` with `submission/` excluded. The main report is `report.pdf`, built from `report/report_short.md`. The technical appendix is `report_full.pdf`, built from `report/report_v5.md` without its changelog sections. Run every command from the repository root. This page follows `README.md` and report Section 5. A clean-clone run of these steps is recorded in `results/repro_2026-10-08/repro_log.md`.

## Environment

Versions from `pip show` (report Section 5): Python 3.13.16, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, selene-sim 0.3.4, guppylang 1.1.2, hugr 0.18.8, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, marimo 0.25.1, pytest 9.1.1.

`pip install -r requirements.txt` installs the same pinned versions. Equivalent explicit command:

```
pip install pytket==2.18.4 pytket-quantinuum==0.59.3 pyzx==0.10.7 qiskit==2.5.2 pygridsynth==2.0.0 \
  selene-sim==0.3.4 guppylang==1.1.2 numpy==2.5.3 pandas==2.3.3 scipy==1.18.1 scikit-learn==1.9.1 \
  matplotlib==3.11.2 aqora==0.35.1 qnexus==0.51.1 marimo==0.25.1 pytest \
  sympy==1.14.0 networkx==3.6.1 mqt-qcec==3.10.2 hugr==0.18.8
```

Selene runs and `selene/test_selene.py` need every proxy variable unset, because Selene streams results over a local TCP socket (report Section 5).

## Directories not in the archive

`third_party/` and `papers/` are in `.gitignore` and are not in `code.zip`.

- `third_party/pyzx-fork/` is the source of the family B1 and B1x circuits. Clone it before the B1 and B1x builders:

```
git clone https://github.com/Quantinuum/pyzx.git third_party/pyzx-fork
git -C third_party/pyzx-fork checkout e695d6d711e67b2b7223417c4714b6b1fcc09191
```

- `papers/` holds the team's manuscripts and is not distributed. The exactness-barrier manuscript is arXiv:2608.22801. The line numbers in `barrier/NOTES.md` refer to its TeX source. The report cites the manuscript by theorem and table labels.
- `results/proxy_h22e_fits.log` is tracked (an exception to the `*.log` rule of `.gitignore`, as are the emulator logs `results/emu_*.log` and `results/fetch_*.log`). `value/value_ledger.py` and `submit/h22e_stats.py` read its line 77.

## Seeds

- `numpy.random.default_rng(20261006)`: family A couplings (`bench/gen_trotter.py`, `SEED`) and family B2 Haar targets (`bench/gen_haar_b2.py`, `SEED`). `seed_transpiler=0` in the B2 qiskit transpile.
- `noise/run_proxy.py`: `default_rng(0)` for the parser self-check only.
- `selene/run_selene.py`: per run `sha256("<pipeline>/<file>/<tag>")[:4]`, stored in column `seed`.
- `model/cost_model.py`: fold seed 0 and `random_state=0` for gradient boosting.
- Bootstrap sd of F_H in Tables E1 and E2: 4000 resamples, seed 20261008.
- Basis-input check (`pipelines/pass_select.py`, `value/psel4_basis_check.py`): `basis_inputs(n, 64, 20261010)`, the all-zero input plus 63 distinct nonzero inputs from `numpy.random.default_rng(20261010)`.

## Commands, in order (report Section 5, README)

| Output | Command |
|---|---|
| Family A circuits | `python bench/gen_trotter.py` |
| Family B1 circuits | `python bench/build_family_B1.py` |
| Family B1x circuits | `python bench/build_family_B1x.py` |
| Family B2 circuits | `python bench/gen_haar_b2.py` |
| Tables A1 to A3, Figure 1 data | `python pipelines/run_bench.py --workers 2` |
| Table B1, Figure 2 data | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900` |
| hwb8 rows of Table B1 | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --files hwb8 --pipelines P1,P2 --prefix family_B1_hwb8_long --timeout 5400 --workers 2` |
| Table B1x | `python pipelines/run_bench_B.py --manifest bench/family_B1x/manifest.csv --prefix family_B1x --pipelines P0ref,P0,P2 --no-check` |
| Table B2, Figure 3 data | `python pipelines/run_b2.py --workers 2` |
| Table A4 | `python noise/run_proxy.py --noise h22e --family A --workers 2` |
| Table A5 | `python noise/run_proxy.py --noise h22e --family B1 --workers 2` |
| Proxy fits (Section 3.5), `results/proxy_h22e_fits.log` | `python noise/run_proxy.py --figure-h22e > results/proxy_h22e_fits.log` |
| Table C1 | `python barrier/run_certificates.py` |
| Table C2 inputs | `python report/build_literature_tcounts.py results/literature_tcounts.csv` |
| Table S1 | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene.py --mode both --procs 2 --shots 2000`, then `python selene/make_summary.py` |
| Table S2 | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene_depol_full.py --procs 2 --shots 2000`, then `python selene/summarise_depol_full.py` |
| Tables M1, M2, Figure 4 | `python model/cost_model.py` |
| Section 4.7 table | `python model/build_selene_cost_inputs.py`, `python model/cost_model.py --family-a results/cost_model_selene_input_A.csv --family-b results/cost_model_selene_input_B1.csv --prefix selene_`, then `python model/report_selene_cost.py` |
| Family C selector, Tables 1.1b and C3 | `python value/family_C_selector.py` |
| Grover use case, Table U1 | `python value/usecase.py` |
| Family C circuits, compilation and basis check | `python bench/build_family_C.py`, `python pipelines/run_family_C.py --workers 2`, then `python pipelines/run_family_C.py --check` |
| Family C equivalence proof by PyZX miter | `python pipelines/equiv_family_C.py --methods pyzx` (36 min of summed check time), then `python pipelines/equiv_family_C.py --summary` |
| Use-case circuits | `python bench/usecase/build_usecase.py` |
| Official baseline comparison | `python pipelines/official_baseline.py run`, then `python pipelines/official_baseline.py report` |
| Section 1 value ledger, Tables 1.1 and 1.2 | `python value/value_ledger.py`, then `python value/value_by_application.py` |
| Table 1.1a, totals of the earlier two-candidate selector PSEL | `python value/selector_ledger.py` (reads `value/value_ledger.csv` and `results/family_B2_counts.csv`) |
| PSEL4 ledger, `value/psel4_ledger.csv` and `.md` | `python3 value/psel4_ledger.py run`, then `python3 value/psel4_ledger.py report` |
| PSEL4 policy comparison, `value/policy_compare.md` | `python3 value/policy_compare.py` |
| HQC per correct answer on H2-2E, `value/hqc_per_correct.md` (report Table HPC, appendix Table E7) | `python3 value/hqc_per_correct.py` (offline, reads the stored H2-2E payloads) |
| USD value of the PSEL4 saving, `value/usd_psel4.md` (appendix Tables 1.5a and 1.5b) | `python3 value/usd_psel4.py` (reads `value/psel4_ledger.csv`) |
| 64-basis-input check of every PSEL4 candidate with 9 to 20 qubits, `value/psel4_basis_check.csv` and `.md` (report Section 2.4) | `python3 value/psel4_basis_check.py run` (recompiles the candidates, 1537 s summed over circuits), then `python3 value/psel4_basis_check.py report`. Does not change `value/psel4_ledger.csv` |
| Conservative PSEL4 variant, `value/psel4_conservative.csv` and `.md` (report Table CV) | `python3 value/psel4_conservative.py` (offline, reads `value/psel4_ledger.csv` and `results/family_C_equivalence*.csv`) |
| PSEL4 (the submitted tool) on new circuits | `python pipelines/pass_select.py --psel4 [--shots N] <qasm files>` |
| The earlier two-candidate selector PSEL on new circuits | `python pipelines/pass_select.py [--shots N] [--candidates P0,P2] <qasm files>` |
| Table E2 statistics | `python submit/h22e_stats.py` (offline, reads the stored counts) |
| Pre-registered B1 run on H2-2E (report Table B1, appendix Section 3.7.6): input-prepared circuits, compilation, checks, submission and fetch | `python3 submit/h22e_b1_run.py --prepare`, `--compile`, `--check`, then `--submit` (needs the team credentials and `EMU_RUN_TAG=famB1_multi`, 14 jobs, 988.32 HQC) and `--fetch-all`. Pre-registration `results/h22e_b1_prereg.md` |
| Statistics of that run, `results/h22e_b1.md` | `python3 submit/h22e_b1.py --md results/h22e_b1.md` (offline, reads the stored payloads under `results/emulator/nexus_H2-2E_famB1_multi/`) |
| Figure PC of the main report, `report/figures/fig_policy.png` and `.pdf` | `python3 value/fig_policy.py` (reads `value/psel4_ledger.csv`) |
| All report tables and figures | `python report/make_tables.py` |
| Emulator jobs (Tables E1, E2) | `submit/syntax_check.py`, `submit/run_emulator.py` and `submit/fetch_job.py`. They need the team credentials and spend quota. Every job is recorded in `results/emulator_jobs.csv` |

## Tests (logs in `build_logs/`)

Rerun all 39 (thirty-nine) test files with `bash run_tests.sh` (repository root, also inside an unzipped `code.zip`). Eight run as scripts and thirty-one under pytest. The logged run of 10 October 2026 covers the first 37, all with rc=0 (`build_logs/tests_summary.txt`). `submit/test_h22e_b1.py` and `value/test_fig_policy.py` were added after that run and passed when run on their own on 10 October 2026. The per-file results below are from the runs of 9 and 10 October 2026. Wall times vary between runs. Those of the latest run are in `build_logs/tests_summary.txt`.

| File | Command | Result | Wall |
|---|---|---|---|
| `bench/test_gen_trotter.py` | `python bench/test_gen_trotter.py` | 12/12 passed | 55 s |
| `noise/test_dm_sim.py` | `python noise/test_dm_sim.py` | 17/17 passed | 4 s |
| `barrier/test_certificate.py` | `python barrier/test_certificate.py` | 69/69 checks passed | 30 s |
| `pipelines/test_compile.py` | `python pipelines/test_compile.py` | 6/6 passed | 2 s |
| `pipelines/test_pass_select.py` | `python pipelines/test_pass_select.py` | 3/3 passed | 4 s |
| `model/test_cost_model.py` | `python model/test_cost_model.py` | 7/7 passed | under 1 s |
| `report/test_c2_literature.py` | `python report/test_c2_literature.py` | all checks passed | 1 s |
| `selene/test_selene.py` | proxy variables cleared, `python -m pytest selene/test_selene.py -q` | 6 passed | 23 s |
| `submit/test_submit.py` | `python -m pytest submit/test_submit.py -q` | 11 passed (offline, no credentials) | 4 s |
| `submit/test_h22e_stats.py` | `python -m pytest submit/test_h22e_stats.py -q` | 7 passed | 3 s |
| `submit/test_h22e_pooled.py` | `python -m pytest submit/test_h22e_pooled.py -q` | 10 passed | 8 s |
| `value/test_value_ledger.py` | `python -m pytest value/test_value_ledger.py -q` | 5 passed | 2 s |
| `value/test_value_by_application.py` | `python -m pytest value/test_value_by_application.py -q` | 5 passed | 1 s |
| `value/test_selector_ledger.py` | `python -m pytest value/test_selector_ledger.py -q` | 4 passed | 1 s |
| `report/test_notebook_submit.py` | `python -m pytest report/test_notebook_submit.py -q` | 20 passed | 1 s |
| `value/test_finals_plan.py` | `python -m pytest value/test_finals_plan.py -q` | 5 passed | 7 s |
| `pipelines/test_official_baseline.py` | `python -m pytest pipelines/test_official_baseline.py -q` | 10 passed | 12 s |
| `value/test_family_C_selector.py` | `python -m pytest value/test_family_C_selector.py -q` | 5 passed | 2 s |
| `value/test_usecase.py` | `python -m pytest value/test_usecase.py -q` | 7 passed | 36 s |
| `pipelines/test_equiv_family_C.py` | `python -m pytest pipelines/test_equiv_family_C.py -q` | 2 passed | 2 s |
| `submit/test_evidence_index.py` | `python -m pytest submit/test_evidence_index.py -q` | 3 passed | under 1 s |
| `submit/test_famC_h22e.py` | `python -m pytest submit/test_famC_h22e.py -q` | 6 passed | 32 s |
| `submit/test_h22e_confirmatory.py` | `python -m pytest submit/test_h22e_confirmatory.py -q` | 10 passed | see `build_logs/tests_summary.txt` |
| `pipelines/test_strong_baselines.py` | `python -m pytest pipelines/test_strong_baselines.py -q` | 17 passed | see `build_logs/tests_summary.txt` |
| `pipelines/test_psel4.py` | `python pipelines/test_psel4.py` | all tests passed | see `build_logs/tests_summary.txt` |
| `pipelines/test_equiv_psel4_C.py` | `python -m pytest pipelines/test_equiv_psel4_C.py -q` | 3 passed | see `build_logs/tests_summary.txt` |
| `value/test_zx_classifier.py` | `python -m pytest value/test_zx_classifier.py -q` | 5 passed | see `build_logs/tests_summary.txt` |
| `submit/test_h22e_famC_nz.py` | `python -m pytest submit/test_h22e_famC_nz.py -q` | 6 passed | see `build_logs/tests_summary.txt` |
| `pipelines/test_equiv_L3_C.py` | `python -m pytest pipelines/test_equiv_L3_C.py -q` | 4 passed | see `build_logs/tests_summary.txt` |
| `value/test_policy_compare.py` | `python -m pytest value/test_policy_compare.py -q` | 6 passed | see `build_logs/tests_summary.txt` |
| `value/test_mechanism_zx_l3.py` | `python -m pytest value/test_mechanism_zx_l3.py -q` | 7 passed | see `build_logs/tests_summary.txt` |
| `submit/test_h22e_multi.py` | `python -m pytest submit/test_h22e_multi.py -q` | 9 passed | see `build_logs/tests_summary.txt` |
| `submit/test_h22e_multi_depth.py` | `python -m pytest submit/test_h22e_multi_depth.py -q` | 2 passed | see `build_logs/tests_summary.txt` |
| `value/test_hqc_per_correct.py` | `python -m pytest value/test_hqc_per_correct.py -q` | 6 passed | 44 s |
| `value/test_usd_psel4.py` | `python -m pytest value/test_usd_psel4.py -q` | 4 passed | under 1 s |
| `value/test_psel4_conservative.py` | `python -m pytest value/test_psel4_conservative.py -q` | 9 passed | 4 s |
| `value/test_psel4_basis_check.py` | `python -m pytest value/test_psel4_basis_check.py -q` | 5 passed (includes the negative controls: reversed CX, extra X, extra Z) | 6 s |
| `submit/test_h22e_b1.py` | `python -m pytest submit/test_h22e_b1.py -q` | 14 passed (offline, checks `submit/h22e_b1_run.py` and `submit/h22e_b1.py` against the pre-registration and the stored payloads) | 4 s |
| `value/test_fig_policy.py` | `python -m pytest value/test_fig_policy.py -q` | 2 passed (the 45 and 0 regression counts of Figure PC against `value/psel4_ledger.csv`, and that both figure files are written) | 3 s |

## Rebuilding this package

`bash submission/build.sh` (add `--tests` to rerun the tests with `run_tests.sh`). The script first runs `report/check_short_numbers.py` on `report/report_short.md`. It copies that file to `report.md` and renders `report.pdf`. It writes `report_full.md` from `report/report_v5.md` without the changelog sections and renders `report_full.pdf`. For each PDF it checks that no `[PENDING`, `TBD` or `Changelog` remains and that the main tables render every row (`check_pdf_tables.py --set short` for Tables PC, 1c, 3a, 3b, HPC, 4a and 4b, the official-baseline, use-case and finals-plan tables, `--set full` for Tables 1.1a, 1.1, C2, E1 and E2). It rebuilds `code.zip` with `git archive HEAD` and checks that this page names HEAD as the `code.zip` commit. It checks the archive for credential files and token strings, runs `check_summary_numbers.py`, builds `one_page_summary.pdf` from `report/one_page_summary.md` (number check, exactly one page), copies `README.md`, `requirements.txt` and `EVIDENCE.md` (job IDs, from `submit/evidence_index.py`) and writes `MANIFEST.txt`. Nothing is uploaded.

## Rubric evidence map (Engineering and Reproducibility)

| Evidence | File |
|---|---|
| Repository | `code.zip` |
| README | `README.md` in `code.zip` |
| Test results | this page, `build_logs/tests_summary.txt`, `build_logs/test_*.log` |
| Reproduction record | this page, report Section 5, `results/repro_2026-10-08/repro_log.md` in `code.zip` |
| Independent verification | 24 reports `results/verification_2026-10-*.md` (7 to 10 October) in `code.zip` |

## Known gaps

1. The clean-clone run reduced the long compilation steps and skipped the Selene runs, the hwb8 long run and the platform jobs for time and credentials. `results/repro_2026-10-08/repro_log.md` lists each reduction and its comparison with the committed files.
2. The platform jobs need the team credentials and spend quota. They cannot be rerun from `code.zip` alone.
