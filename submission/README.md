# sgc-zx

Team Learned ZX Rewriting, Quantinuum Singapore Grand Challenge. A resource-certification benchmark for Quantinuum H2 with two cost layers: the NISQ layer (ZZPhase count, two-qubit depth, HQC, emulated fidelity) and the fault-tolerant layer of T-counts. A per-instance certified T-count floor exists for the 24 circuits of `results/certificates.csv`. The main submission report is `report/report_short.md` (`submission/report.pdf`); the full report `report/report_v5.md` is its technical appendix (`submission/report_full.pdf`). The executable companion is `report/notebook_skeleton.py`.

## Running the solution

```
pip install -r requirements.txt                                   # Python 3.13, pinned versions
python3 pipelines/pass_select.py bench/family_B1/vbe_adder_3.qasm # PSEL on one circuit: P0, P2 and the pick with HQC
bash run_tests.sh                                                 # all 22 test files, about 4 to 6 min, logs in submission/build_logs/
marimo edit report/notebook_skeleton.py                           # notebook: tables, figures, live compilation
python3 submit/evidence_index.py                                  # rebuilds results/EVIDENCE.md from the stored job payloads
```

Configuration. No configuration file is needed to compile or to rebuild tables. Submitting a job needs aqora team credentials (`aqora login`), which are not in the repository; the notebook's submission cell only sends to platforms whose name ends in `SC`. The emulator jobs behind the report are listed with their job IDs in `results/EVIDENCE.md`.

## Layout

| Path | Content |
|---|---|
| `bench/gen_trotter.py` | Family A generator: Trotter circuits for TFIM, XXZ (from the Neel state) and the TFIM ladder, n in {4, 6, 8, 10, 12}, r in {1, 2, 4}, seed 20261006. Writes `bench/family_A/`. |
| `bench/build_family_B1.py` | Family B1 builder: 15 Clifford+T benchmark circuits (n <= 12) from the Quantinuum pyzx fork, Toffolis expanded to the 7-T decomposition. Writes `bench/family_B1/` and its manifest. |
| `bench/gen_haar_b2.py` | Family B2 generator: QSD + gridsynth synthesis of Haar unitaries, n in {2, 3}, eps in {1e-3, 1e-5}, seed 20261006. Writes `bench/family_B2/`. |
| `bench/sv.py` | Independent numpy statevector simulator used for the `.npy` references. |
| `pipelines/compile.py` | The pipelines P0ref, P0, P0L1, P1, P2, P3, P4, the metrics (n_2q, depth_2q, HQC, ...) and the exactness checks. P0 reproduces pytket-quantinuum 0.59.3 `default_compilation_pass(optimisation_level=2)` with line references. |
| `pipelines/run_bench.py` | Family A: every pipeline on every circuit. Writes `results/family_A_counts.csv`, `results/family_A_summary.csv`, `results/compiled/<pipeline>/`. |
| `pipelines/run_bench_B.py` | Manifest-driven runner (family B1). Writes `results/family_B1_counts.csv`, `results/family_B1_summary.csv`. |
| `pipelines/run_b2.py` | Family B2 runner. Writes `results/family_B2_counts.csv`. |
| `noise/dm_sim.py`, `noise/h2_params.py`, `noise/run_proxy.py` | Local density-matrix noise proxy for family A (n <= 8). Writes `results/family_A_proxy.csv` and `results/fig_proxy_fidelity_vs_n2q.{pdf,png}`. Compared with the emulator runs in Sections 3.7 and 3.7.1 of the report. |
| `barrier/certificate.py`, `barrier/NOTES.md` | Exact-arithmetic implementation of the T-count floor of the exactness-barrier manuscript (arXiv:2608.22801), with a line-by-line map to the manuscript. |
| `report/make_tables.py` | Generates every table and figure of the report from `results/*.csv` and injects the tables into `report/report_v1.md` to `report/report_v5.md` at their `<!-- TABLE:name -->` markers. |
| `report/report_v5.md` | Full report v5, the technical appendix of the submission (`report/report_short.md` is the main report). Section 1 is kept identical to `report/sec1_v5.md`. Drafts v1 to v4 are kept. |
| `value/value_ledger.py` | HQC and magic-state ledger, P2 against P0 at 1000 shots. Writes `value/value_ledger.csv` and `value/value_ledger.md`. |
| `value/value_by_application.py` | Regroups the ledger by application area from `docs/applications.md`. Writes `value/value_by_application.csv` and `value/value_by_application.md`, the sources of Section 1. |
| `submit/syntax_check.py`, `submit/run_emulator.py`, `submit/fetch_job.py` | Platform jobs through `aqora`. Every job is recorded in `results/emulator_jobs.csv`. |
| `submit/h22e_stats.py` | Recomputes the H2-2E statistics of Table E2 from the stored counts. |
| `report/notebook_skeleton.py` | Marimo notebook: tables, figures, live compilation of one circuit through P0 and P2, gated submission to the free syntax checker `nexus:H2-2SC` through `aqora.QPU`. |
| `report/tables/`, `report/figures/` | Outputs of `make_tables.py`. |
| `results/` | All CSVs, logs and compiled QASM (hqslib1 header, measure-all appended). |
| `docs/platform_notes.md` | aqora API, emulator tiers, H2-2E noise parameters, HQC formula, with sources. |
| `papers/barrier/`, `papers/skzx/` | TeX sources of the two team manuscripts. |
| `third_party/pyzx-fork/` | Quantinuum pyzx fork at commit e695d6d7, source of the B1 circuits. |

## Reproducing every table

Two directories are not in git. `third_party/pyzx-fork/` is obtained with

```
git clone https://github.com/Quantinuum/pyzx.git third_party/pyzx-fork
git -C third_party/pyzx-fork checkout e695d6d711e67b2b7223417c4714b6b1fcc09191
```

`papers/` holds the team's manuscripts and is not distributed. The exactness-barrier manuscript is arXiv:2608.22801. A clean-clone run of these steps is recorded in `results/repro_2026-10-08/repro_log.md`.

Run from the repository root. Steps 1 to 3 regenerate the benchmark circuits (deterministic), steps 4 to 7 compile them, step 8 builds the tables.

```
# 1-3  circuits
python bench/gen_trotter.py
python bench/build_family_B1.py
python bench/gen_haar_b2.py

# 4-6  compilation (results/*_counts.csv, results/compiled/)
python pipelines/run_bench.py --workers 2
python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900
python pipelines/run_b2.py --workers 2

# 7    noise proxy (provisional, family A n <= 8)
python noise/run_proxy.py --workers 2                     # results/family_A_proxy.csv (typical noise)
python noise/run_proxy.py --workers 2 --noise h22e       # results/family_A_proxy_h22e.csv, source of Table A4

# 7b   published T-counts of Table C2 (reads results/family_B1_counts.csv and results/family_B1x_counts.csv)
python report/build_literature_tcounts.py results/literature_tcounts.csv

# 8    tables and figures, injected into report/report_v1.md to report/report_v5.md
#      (--no-fig skips the figures, --no-inject writes report/tables/ only)
python report/make_tables.py
```

Table A1 to A3 and the family A figure come from `results/family_A_counts.csv`. Table A4 comes from `results/family_A_proxy_h22e.csv`. Table B1 and its figure come from `results/family_B1_counts.csv`. Table B2 and its figure come from `results/family_B2_counts.csv`.

Status on 9 October 2026:

- Certificates done. `python barrier/run_certificates.py` writes `results/certificates.csv` with 24 rows (20 family B2 circuits at n = 2 and 3, four family B1 circuits at n = 5). Report Table C1.
- Selene done. 468 noiseless and 468 full depolarising runs plus a 68-run comparison. Report Tables S1 and S2 and `results/selene.md`.
- H2-Emulator done. Three jobs with 22 circuit rows. Report Table E1, `results/emulator_nexus_H2-Emulator.csv`.
- H2-2E done. 20 jobs with an HQC estimate of 6598.0 in total. The two jobs of 9 October ran the 22-qubit family C adder vbe_adder_7 (`results/h22e_famC.md`, Table E4, `submit/h22e_famC.py`). The first 18 jobs total 5933.2. Six single runs are in Report Table E2 and `results/emulator_nexus_H2-2E.csv`. Three repeat runs of vbe_adder_3 and grover_5 under P0 and P2 are in `results/emulator_nexus_H2-2E_r2.csv` to `_r4.csv`, pooled by `submit/h22e_pooled.py` into Table E3. Repeat runs set `EMU_RUN_TAG` so they do not overwrite the first run.
- The submission cell of `report/notebook_skeleton.py` was executed once on the free H2-2SC syntax checker (job `AFByb3ZpZGVySm9iAaEdzTywfrOWhGbnlXxd-w`, export `report/notebook_executed.html`). It refuses any platform whose name does not end in SC. The emulator jobs were submitted by the `submit/` scripts.

Value ledger, run after the compilation steps:

```
python value/value_ledger.py
python value/value_by_application.py
```

Tests. `bash run_tests.sh` runs all 22 test files: seven as scripts and fifteen under pytest, with the Selene tests run with the proxy variables cleared (see the proxy note below). One log per file and `tests_summary.txt` go to `submission/build_logs/` or to `$TEST_LOG_DIR`. The list of files and the results of the last run are in `submission/REPRODUCE.md`.

## Notebook

```
marimo edit report/notebook_skeleton.py          # interactive
marimo export html report/notebook_skeleton.py -o notebook.html   # runs every cell up to the submission gate
```

Before submitting, set the environment variable `AQORA_TEAM_ORG` to the team's aqora organization username (read into `TEAM_ORG` in the setup cell). The submission cell is gated behind its **Submit to the H2-2SC syntax checker** button and sends nothing until it is pressed, or until the notebook is run with `SGC_NOTEBOOK_SUBMIT_SC=1`. It submits the PSEL pick of the chosen circuit to the free syntax checker `nexus:H2-2SC` only; any platform whose name does not end in `SC` raises an error. Emulator jobs on H2-2E and H2-Emulator were submitted with `submit/run_emulator.py` and are listed in `results/EVIDENCE.md`.

## Environment

Python 3.13, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, selene-sim 0.3.4, marimo 0.25.1. Full list in `report/report_v5.md`, section 5.

```
pip install -r requirements.txt
```

`requirements.txt` pins every package above and also guppylang, hugr, scikit-learn, sympy, networkx, mqt-qcec and pytest.

Proxy note. In the development container outbound HTTPS goes through an agent proxy. pip installs were run with the proxy variables cleared for that one command: `NO_PROXY= no_proxy= pip install --break-system-packages <package>`. Local Selene runs also need every proxy variable unset (`HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= python ...`). aqora job submission needs the team credentials. The jobs submitted from this container on 8 October 2026 are listed in `results/emulator_jobs.csv`.

## Pass selector

`pipelines/pass_select.py` compiles a circuit with P0 and P2 through `compile_pipeline` (unchanged), drops a candidate that raises, leaves the native gate set or fails `compile.check` (no check above 20 qubits, marked `ok-unchecked`), and keeps the lower HQC at 1000 shots. Ties go to the lower n_2q (ZZPhase + ZZMax), then to P0. `compile_select(circ)` returns the compiled circuit and a per-candidate record. `python3 pipelines/pass_select.py <qasm files...>` prints one row per file. Tests: `python3 pipelines/test_pass_select.py`.
