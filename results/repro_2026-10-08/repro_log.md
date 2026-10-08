# Clean-clone reproduction log, 8 October 2026

## Setup

- `[F]` Source: `git clone /home/claude/sgc-zx` into a scratch directory. Commit `0958ca9273d1492f24cca18c3cf0a547b9e8f2da` ("Report v5: apply verification fixes to Table C2 and Section 3.4", 2026-10-08 22:00:48 +0200).
- `[F]` Environment: Python 3.13.16, Linux 6.18.44, 2 cores. Key packages in `pip_freeze_key.txt`: pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, numpy 2.5.3, selene-sim 0.3.4, guppylang 1.1.2, aqora 0.35.1, qiskit 2.5.2, pygridsynth 2.0.0, pandas 2.3.3, scipy 1.18.1, qnexus 0.51.1. All match the versions in `README.md` and `submission/REPRODUCE.md`. Nothing was installed.
- `[F]` Every command ran in the foreground from the clone root under `timeout 575` (`step.sh`). Raw stdout per step in `stdout/<step>.txt`. Exit codes and wall times in `steps.tsv`. Comparison script `compare.py`, output `compare_out.txt`.

## Deviations

1. `[F]` `third_party/` is in `.gitignore` and absent from the clone. README states only that it holds the pyzx fork at commit e695d6d7, with no fetch instruction. Copied from `/home/claude/sgc-zx/third_party` (82 MB). Its HEAD is `e695d6d711e67b2b7223417c4714b6b1fcc09191`.
2. `[F]` `results/proxy_h22e_fits.log` is ignored by the `*.log` rule of `.gitignore`, so it is absent from a clean clone. `value/value_ledger.py` reads it (line 35, `FIT_LOG`) and fails with `FileNotFoundError`. `value/test_value_ledger.py` therefore fails on a clean clone (step T10, 5 errors). The file is the stdout of `python noise/run_proxy.py --figure-h22e` (report Section 5 table). Recovered by running step 11 and copying its stdout to `results/proxy_h22e_fits.log`. After this T10b passes 5 of 5. The regenerated log equals the uncommitted copy in `/home/claude/sgc-zx/results/` apart from the `total time` and `figure:` lines.
3. `[F]` `barrier/run_certificates.py` (step 12) was run concurrently with steps 07 to 11 to fit the time budget. It hit the 575 s timeout (rc 124) after 22 of 24 circuits, so `results/certificates.csv` was not rewritten. The 22 printed rows were compared instead.
4. `[F]` Reduced variants were used for the long compilation steps (table below). The B2 subset run overwrites `results/family_B2_counts.csv`. Its output was copied aside and the committed file restored with `git checkout` before `make_tables.py`.

## Steps

`[F]` Estimates come from the sums of `t_wall` / `t_sim` / `wall_s` in the committed CSVs divided by the worker count. README gives no explicit time estimates.

| Step | Command | Status | Exit | Wall (s) |
|---|---|---|---|---|
| 01 | `python bench/gen_trotter.py` | run | 0 | 1.3 |
| 02 | `python bench/build_family_B1.py` | run | 0 | 4.6 |
| 03 | `python bench/build_family_B1x.py` | run | 0 | 2.6 |
| 04 | `python bench/gen_haar_b2.py` | run | 0 | 72.5 |
| 05 | `python pipelines/run_bench.py --workers 2` | reduced: `--model tfim --merge` (full est. 760 s, tfim est. 160 s) | 0 | 229.3 |
| 06 | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900` | reduced: the 14 circuits other than hwb8 via `--files`, `--prefix family_B1_repro` (full est. 1650 s, hwb8 alone 3190 s) | 0 | 70.5 |
| - | hwb8 long run, `--timeout 5400` | skipped (886 s and 844 s wall per pipeline) | - | - |
| 07 | `python pipelines/run_bench_B.py --manifest bench/family_B1x/manifest.csv --prefix family_B1x --pipelines P0ref,P0,P2 --no-check` | run | 0 | 50.3 |
| 08 | `python pipelines/run_b2.py --workers 2` | reduced: `--pipelines P0ref,P0,P3` (full est. 935 s, P1 and P2 are 1506 s of the 1871 s total) | 0 | 122.7 |
| - | `python noise/run_proxy.py --workers 2` (README step 7, typical noise, Figure `fig_proxy_fidelity_vs_n2q`) | skipped for time budget (est. 390 s), not a > 10 min skip | - | - |
| 09 | `python noise/run_proxy.py --noise h22e --family A --workers 2` | run | 0 | 154.9 |
| 10 | `python noise/run_proxy.py --noise h22e --family B1 --workers 2` | run | 0 | 8.3 |
| 11 | `python noise/run_proxy.py --figure-h22e` | run, stdout saved as `results/proxy_h22e_fits.log` | 0 | 3.5 |
| - | `python report/build_literature_tcounts.py results/literature_tcounts.csv` (README 7b) | not run (omitted in error, est. under 10 s) | - | - |
| 12 | `python barrier/run_certificates.py` | run, timed out after 22 of 24 rows (concurrent with 07 to 11) | 124 | 575.0 |
| - | `selene/run_selene.py --mode both`, `selene/run_selene_depol_full.py` (Tables S1, S2) | skipped (465 s plus 1437 s summed per-run wall, > 10 min). Only `--limit` exists, documented as debug, not as a reduced variant | - | - |
| 13 | `python value/value_ledger.py` | run (after deviation 2) | 0 | 0.9 |
| 14 | `python value/value_by_application.py` | run | 0 | 0.7 |
| 15 | `python model/cost_model.py` | run | 0 | 11.3 |
| - | Section 4.7 cost-model chain (`model/build_selene_cost_inputs.py` ...) | skipped (needs the Selene CSVs regenerated, known gap 1 of REPRODUCE.md) | - | - |
| 16 | `python report/make_tables.py --no-fig` | run | 0 | 4.5 |
| - | `submit/syntax_check.py`, `submit/run_emulator.py`, `submit/fetch_job.py`, notebook submission cell | skipped (need team credentials and HQC) | - | - |

## Tests

| Step | Command | Exit | Result | Wall (s) |
|---|---|---|---|---|
| T01 | `python bench/test_gen_trotter.py` | 0 | 12/12 passed | 75.6 |
| T02 | `python pipelines/test_compile.py` | 0 | all passed | 3.4 |
| T03 | `python noise/test_dm_sim.py` | 0 | 17/17 passed | 6.4 |
| T04 | `python barrier/test_certificate.py` | 0 | 69/69 checks passed | 47.8 |
| T05 | `python model/test_cost_model.py` | 0 | all passed | 0.6 |
| T06 | `python report/test_c2_literature.py` | 0 | all checks passed | 0.7 |
| T07 | proxy cleared, `python -m pytest selene/test_selene.py -q` | 0 | 6 passed | 11.6 |
| T08 | `python -m pytest submit/test_submit.py -q` | 0 | 11 passed (offline) | 5.3 |
| T09 | `python -m pytest submit/test_h22e_stats.py -q` | 0 | 7 passed | 5.3 |
| T10 | `python -m pytest value/test_value_ledger.py -q` | 1 | 5 errors, `FileNotFoundError: results/proxy_h22e_fits.log` | 3.0 |
| T10b | same, after step 11 restored the log | 0 | 5 passed | 3.1 |
| T11 | `python -m pytest value/test_value_by_application.py -q` | 0 | 5 passed | 2.0 |

`[F]` T09 passed before the fits log existed although `report/report_v5.md` line 614 says `submit/h22e_stats.py` checks the slope against line 77 of that log. `[O]` The test probably skips that check when the file is absent. Not inspected.

## Comparison with the committed files

`[F]` Byte-identical (`git status` clean after the step): every tracked file under `bench/` after steps 01 to 04 (577 tracked files), every file under `results/compiled/`, `value/*.csv`, `value/*.md`, `results/cost_model_metrics.csv`, `results/cost_model_coefficients.csv`, `results/fig_cost_model.png`, `results/fig_proxy_h22e.png`, all of `report/tables/*.md`, and `report/report_v1.md` to `report/report_v5.md` after `make_tables.py --no-fig`. `diff report/report_v5.md` against the committed file is empty.

`[F]` Non-empty diffs (from `compare_out.txt`, rows joined on file and pipeline):

| File | Rows compared | Non-timing columns differing | Timing columns |
|---|---|---|---|
| `family_A_counts.csv` (tfim rows rerun, merged) | 1260 | `check_dev`, `ref_dev` max abs 3.2e-30, `dist_maxdiff`, `qasm_dist_maxdiff` max 6.5e-27, `pyzx_angle_err` max 1.3e-26. All integer counts identical | `t_*` up to 3.9 s |
| `family_A_summary.csv` | 630 | `max_check_dev` max abs 3.2e-30 | `t_total` up to 2.9 s |
| `family_B1x_counts.csv`, `family_B1x_summary.csv` | 24, 8 | none | `t_*` up to 12.4 s |
| `family_B1_repro_counts.csv` against `family_B1_counts.csv` | 98 | `check_dev`, `dist_maxdiff` max 7.9e-31, `ref_dev`, `qasm_dist_maxdiff` max 3.9e-31 | `t_*` up to 2.0 s |
| B2 subset against `family_B2_counts.csv` | 60 | none | `t_*` up to 7.5 s |
| `family_A_proxy_h22e.csv` | 540 | none (F_H and all fidelity columns identical) | `t_sim` up to 4.1 s |
| `family_B1_proxy_h22e.csv` | 35 | none | `t_sim` up to 0.50 s |
| `certificates.csv` (22 printed rows) | 22 | fraction columns max abs 1.1e-16 (printed-repr against CSV round trip). Integer columns (`lde_floor`, `t_written`, `t_zx_P1/P2`, `collapse_count`) and booleans identical | `wall_s` up to 61 s (contention) |
| `fig_cost_model.pdf`, `fig_proxy_h22e.pdf` | - | PDF bytes differ, PNGs identical | - |

`[O]` Every non-timing difference is at or below 1e-16 absolute on quantities that are themselves numerical noise (deviations near 1e-15 to 1e-13). No count, T-count, HQC, fidelity or table cell changed.

## Not reproduced

`[F]` hwb8 under all pipelines, family B2 under P1, P2 and P4, family A xxz and ladder rows, the typical-noise proxy, Selene Tables S1 and S2, two certificate rows, `build_literature_tcounts.py`, and the figures (`--no-fig`). Platform jobs (Tables E1, E2) were not rerun.

## Reproduction failures

1. `[F]` Clean clone cannot run `value/value_ledger.py` or pass `value/test_value_ledger.py` until `results/proxy_h22e_fits.log` is regenerated. Neither README nor REPRODUCE.md lists that redirect. Proposed fix for the team: whitelist the file in `.gitignore` (`!results/proxy_h22e_fits.log`) and commit it, or have `run_proxy.py --figure-h22e` write it itself.
2. `[F]` `third_party/pyzx-fork` is not obtainable from the repository. Proposed fix: add a fetch command with the commit hash to README (or a submodule).
