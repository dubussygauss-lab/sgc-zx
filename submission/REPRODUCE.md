# Reproduction record

Team Learned ZX Rewriting. Recorded 8 October 2026 in the development container and updated 9 October 2026. `code.zip` is `git archive` of commit `2cc92ced9919b7fa7027ae54aab04b2a9ac00870`. The main report is `report.pdf`, built from `report/report_short.md`. The technical appendix is `report_full.pdf`, built from `report/report_v5.md` without its changelog sections. Run every command from the repository root. This page follows `README.md` and report Section 5. A clean-clone run of these steps is recorded in `results/repro_2026-10-08/repro_log.md`.

## Environment

Versions from `pip show` (report Section 5): Python 3.13.16, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, selene-sim 0.3.4, guppylang 1.1.2, hugr 0.18.8, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, marimo 0.25.1, pytest 9.1.1.

```
pip install pytket==2.18.4 pytket-quantinuum==0.59.3 pyzx==0.10.7 qiskit==2.5.2 pygridsynth==2.0.0 \
  selene-sim==0.3.4 guppylang==1.1.2 numpy==2.5.3 pandas==2.3.3 scipy==1.18.1 scikit-learn==1.9.1 \
  matplotlib==3.11.2 aqora==0.35.1 qnexus==0.51.1 marimo==0.25.1 pytest
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
- `results/proxy_h22e_fits.log` is tracked (an exception to the `*.log` rule of `.gitignore`). `value/value_ledger.py` and `submit/h22e_stats.py` read its line 77.

## Seeds

- `numpy.random.default_rng(20261006)`: family A couplings (`bench/gen_trotter.py`, `SEED`) and family B2 Haar targets (`bench/gen_haar_b2.py`, `SEED`). `seed_transpiler=0` in the B2 qiskit transpile.
- `noise/run_proxy.py`: `default_rng(0)` for the parser self-check only.
- `selene/run_selene.py`: per run `sha256("<pipeline>/<file>/<tag>")[:4]`, stored in column `seed`.
- `model/cost_model.py`: fold seed 0 and `random_state=0` for gradient boosting.
- Bootstrap sd of F_H in Tables E1 and E2: 4000 resamples, seed 20261008.

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
| Table 1.1a, pass selector PSEL totals | `python value/selector_ledger.py` (reads `value/value_ledger.csv` and `results/family_B2_counts.csv`) |
| Pass selector PSEL on new circuits | `python pipelines/pass_select.py [--shots N] [--candidates P0,P2] <qasm files>` |
| Table E2 statistics | `python submit/h22e_stats.py` (offline, reads the stored counts) |
| All report tables and figures | `python report/make_tables.py` |
| Emulator jobs (Tables E1, E2) | `submit/syntax_check.py`, `submit/run_emulator.py` and `submit/fetch_job.py`. They need the team credentials and spend quota. Every job is recorded in `results/emulator_jobs.csv` |

## Tests (logs in `build_logs/`)

Rerun all twenty with `bash submission/run_tests.sh`. Seven run as scripts and thirteen under pytest. The results below are from the run of 9 October 2026 stored in `build_logs/tests_summary.txt`.

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

## Rebuilding this package

`bash submission/build.sh` (add `--tests` to rerun the tests). The script first runs `report/check_short_numbers.py` on `report/report_short.md`. It copies that file to `report.md` and renders `report.pdf`. It writes `report_full.md` from `report/report_v5.md` without the changelog sections and renders `report_full.pdf`. For each PDF it checks that no `[PENDING`, `TBD` or `Changelog` remains and that the main tables render every row (`check_pdf_tables.py --set short` for Tables 1 to 4b, the official-baseline, use-case and finals-plan tables, `--set full` for Tables 1.1a, 1.1, C2, E1 and E2). It rebuilds `code.zip` with `git archive HEAD` and checks that this page names HEAD as the `code.zip` commit. It checks the archive for credential files and token strings, runs `check_summary_numbers.py` and writes `MANIFEST.txt`. Nothing is uploaded.

## Rubric evidence map (Engineering and Reproducibility)

| Evidence | File |
|---|---|
| Repository | `code.zip` |
| README | `README.md` in `code.zip` |
| Test results | this page, `build_logs/tests_summary.txt`, `build_logs/test_*.log` |
| Reproduction record | this page, report Section 5, `results/repro_2026-10-08/repro_log.md` in `code.zip` |

## Known gaps

1. The clean-clone run reduced the long compilation steps and skipped the Selene runs, the hwb8 long run and the platform jobs for time and credentials. `results/repro_2026-10-08/repro_log.md` lists each reduction and its comparison with the committed files.
2. The platform jobs need the team credentials and spend quota. They cannot be rerun from `code.zip` alone.
