# sgc-zx

Team Learned ZX Rewriting, Quantinuum Singapore Grand Challenge. PSEL4, a cost-aware auto level that compiles each circuit four ways and keeps the cheapest checked result, is a drop-in replacement for pytket-quantinuum's default compile on Quantinuum H2. It is never costlier than the default compile on our 217-circuit benchmark and needs 15.7 % less HQC in total (`value/policy_compare.md`). A team that spends the Standard Plan's 10,000 HQC a month on this mix frees 1,573.3 HQC a month, worth USD 19,666 at the Standard Plan average (workload assumption, `value/usd_psel4.md`). The four candidates are pytket-quantinuum level 2 (P0), level 3 (L3), PyZX teleport_reduce then level 2 (P2) and teleport_reduce then level 3 (P2L3).

- Cost: level 3 adoption made safe. PSEL4 totals 49,580.6 HQC against 58,837.2 for always level 2 and 50,632.2 for always level 3. Always level 3 gives 13.95 points of the 15.73 % saving and per-circuit selection plus ZX give 1.79 points. Against the per-circuit cheaper of level 2 and level 3 PSEL4 saves 679.6 HQC, 1.35 %. Always level 3 costs more than level 2 on 45 of the 217 circuits and loses 372.0 HQC there. PSEL4 costs more on none (`value/policy_compare.md`, `value/usd_psel4.md`).
- Correctness. Each candidate is checked against its input as a full unitary up to 8 qubits and on 64 random computational basis inputs (including all-zero) from 9 to 20 qubits. Above 20 qubits family C relies on PyZX miter proofs, which prove the PSEL4 output on 17 of 20 circuits. MQT QCEC proved none of the other three and returned no counterexample (`results/family_C_equivalence_qcec.md`).
- Basis-input check: all 83 PSEL4 picks with 9 to 20 qubits pass on 64 basis inputs, as do 187 of 187 required and 142 of 142 other candidates, and the negative controls fail (`value/psel4_basis_check.md`, `value/test_psel4_basis_check.py`).
- Conservative variant: the cheapest verified candidate, else the default level 2 output flagged "default, unverified" (only hrs_mult_5), saves 12.25 % against level 2 and costs more than level 2 on 0 circuits (`value/psel4_conservative.md`).
- H2-2E emulator. The HQC-cheapest compile is not the most accurate. In five pre-registered H2-2E comparisons of the PSEL4 pick against level 2 on non-zero inputs the pick was significantly less accurate on 2 (cdkm_adder_10 under level 3, 0.8267 against 0.8692, z = -2.90, `results/h22e_multi.md`, and hwb6 under ZX then level 3, 0.8883 against 0.9200, z = -2.64, Holm p = 0.017, `results/h22e_b1.md`), not different on 2 (modadd_2n_10 z = -0.22, vbe_adder_3 z = +0.51) and not significantly better on 1 (vbe_adder_7 z = +1.30, `results/h22e_famC_nz.md`). No pick was significantly more accurate. The HQC saving still exceeds the accuracy loss. HQC per correct answer is lower for the pick in 5 of 5 pairs, and in 8 of 8 including three earlier pairs of the two-candidate selector, pooled 18.1 % lower (R = 0.8192, bootstrap 95 % interval 0.8132 to 0.8254, HQC ratio 0.8170 over accuracy ratio 0.9973, `value/hqc_per_correct.md`). PSEL4 serves cost-bound users. Accuracy-bound users need a fidelity-aware choice, which is the finals deliverable: a learned selector trained on this ledger and these emulator labels (48 H2-2E jobs, 9971.8 HQC, every job ID in `results/EVIDENCE.md`).
- Mechanism. Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp. ZX phase teleportation adds little on top of level 3 (`value/mechanism_zx_l3.md`).

The main submission report is `report/report_short.md` (`submission/report.pdf`). The full report `report/report_v5.md` is its technical appendix (`submission/report_full.pdf`). The executable companion is `report/notebook_skeleton.py`.

A secondary component is a per-instance certified T-count floor for the 24 circuits of `results/certificates.csv` (`barrier/certificate.py`, report Table C1).

## Running the solution

```
pip install -r requirements.txt                                   # Python 3.13, pinned versions
python3 pipelines/pass_select.py --psel4 bench/family_B1/vbe_adder_3.qasm  # PSEL4 on one circuit: P0, P2, L3, P2L3 and the pick with HQC
python3 pipelines/pass_select.py bench/family_B1/vbe_adder_3.qasm          # the earlier two-candidate selector PSEL (P0, P2)
bash run_tests.sh                                                 # all 38 test files (8 scripts, 30 pytest), about 5 to 7 min, logs in submission/build_logs/
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
| `report/notebook_skeleton.py` | Marimo notebook: tables, figures, live compilation of one circuit with the four-candidate selector PSEL4 (P0, L3, P2, P2L3) checked against `value/psel4_ledger.csv`, gated submission to the free syntax checker `nexus:H2-2SC` through `aqora.QPU`. |
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

Status on 10 October 2026:

- Certificates done. `python barrier/run_certificates.py` writes `results/certificates.csv` with 24 rows (20 family B2 circuits at n = 2 and 3, four family B1 circuits at n = 5). Report Table C1.
- Selene done. 468 noiseless and 468 full depolarising runs plus a 68-run comparison. Report Tables S1 and S2 and `results/selene.md`.
- H2-Emulator done. Three jobs with 22 circuit rows. Report Table E1, `results/emulator_nexus_H2-Emulator.csv`.
- H2-2E done. 48 jobs with an HQC estimate of 9971.8 in total, which leaves 28.2 of the 10,000 HQC quota. The fourteen pre-registered jobs of 10 October ran vbe_adder_3 (P0 against L3) on four non-zero inputs and hwb6 (P0 against P2L3) on three non-zero inputs at 400 shots each (`results/h22e_b1_prereg.md`, `results/h22e_b1.md`, report Section 3.7.6, `submit/h22e_b1_run.py` submits and `submit/h22e_b1.py` scores, test `submit/test_h22e_b1.py`). On hwb6 the pick P2L3 succeeds less often than P0, 0.8883 against 0.9200 pooled with z = -2.64 and Holm p = 0.017. On vbe_adder_3 the difference has z = +0.51. The twelve pre-registered jobs earlier on 10 October ran cdkm_adder_10 (P0 against L3) and modadd_2n_10 (P0 against P2L3) on three non-zero inputs each (`results/h22e_multi_prereg.md`, `results/h22e_multi.md`, Table E6, `submit/h22e_multi_run.py` submits and `submit/h22e_multi.py` scores). On cdkm_adder_10 the PSEL4 pick L3 succeeds less often than P0, 0.8267 against 0.8692 pooled with z = -2.90. On modadd_2n_10 the difference has z = -0.22. Two earlier jobs of 10 October ran vbe_adder_7 on the non-zero input a = 28, b = 111 under P0 and L3 (`results/h22e_famC_nz.md`, Table E5). The two jobs of 9 October ran the 22-qubit family C adder vbe_adder_7 (`results/h22e_famC.md`, Table E4, `submit/h22e_famC.py`). The first 18 jobs total 5933.2. Six single runs are in Report Table E2 and `results/emulator_nexus_H2-2E.csv`. Three repeat runs of vbe_adder_3 and grover_5 under P0 and P2 are in `results/emulator_nexus_H2-2E_r2.csv` to `_r4.csv`, pooled by `submit/h22e_pooled.py` into Table E3. Repeat runs set `EMU_RUN_TAG` so they do not overwrite the first run.
- PSEL4 policy comparison done. `python3 value/policy_compare.py` writes `value/policy_compare.md`. Over 217 circuits PSEL4 needs 15.7 % less HQC than always using level 2 and costs more than level 2 on 0 circuits. Always using level 3 saves 13.9 % and costs more than level 2 on 45 circuits. Report Section 3.8.4.
- Level 3 equivalence on family C done. `python3 pipelines/equiv_L3_C.py` writes `results/family_C_equivalence_L3.md`. The PyZX miter proves the level 3 output equal to its input on 18 of 20 circuits. Report Section 3.8.3.
- Mechanism done. `python3 value/mechanism_zx_l3.py report` writes `value/mechanism_zx_l3.md`. Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp. Six circuits are missing because their level 3 or P2L3 compile did not fit the CPU budget. Report Section 3.8.5.
- Tests. `run_tests.sh` lists 38 test files (8 as scripts, 30 under pytest). The logged run of 10 October covered 37 of them and all returned rc=0 (`submission/build_logs/tests_summary.txt`). `submit/test_h22e_b1.py` was added after that run and passed 14 of 14.
- Independent verification. 26 reports `results/verification_2026-10-*.md`, 7 to 10 October.
- The submission cell of `report/notebook_skeleton.py` was executed on the free H2-2SC syntax checker twice: on 9 October 2026 with the earlier two-candidate selector PSEL (job `AFByb3ZpZGVySm9iAaEdzTywfrOWhGbnlXxd-w`) and on 10 October 2026 with PSEL4 (pick L3 for tof_3, job `AFByb3ZpZGVySm9iAaElTNS7cyOY831oDA3xZg`, export `report/notebook_executed.html`). It refuses any platform whose name does not end in SC. The emulator jobs were submitted by the `submit/` scripts.

Value ledger, run after the compilation steps:

```
python value/value_ledger.py
python value/value_by_application.py
```

Tests. `bash run_tests.sh` runs all 38 test files: eight as scripts and thirty under pytest, with the Selene tests run with the proxy variables cleared (see the proxy note below). One log per file and `tests_summary.txt` go to `submission/build_logs/` or to `$TEST_LOG_DIR`. The list of files and the results of the last run are in `submission/REPRODUCE.md`.

## Notebook

```
marimo edit report/notebook_skeleton.py          # interactive
marimo export html report/notebook_skeleton.py -o notebook.html   # runs every cell up to the submission gate
```

Before submitting, set the environment variable `AQORA_TEAM_ORG` to the team's aqora organization username (read into `TEAM_ORG` in the setup cell). The submission cell is gated behind its **Submit to the H2-2SC syntax checker** button and sends nothing until it is pressed, or until the notebook is run with `SGC_NOTEBOOK_SUBMIT_SC=1`. It submits the pick of the four-candidate selector PSEL4 for tof_3 to the free syntax checker `nexus:H2-2SC` only; any platform whose name does not end in `SC` raises an error. Emulator jobs on H2-2E and H2-Emulator were submitted with `submit/run_emulator.py` and are listed in `results/EVIDENCE.md`.

## Environment

Python 3.13, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, selene-sim 0.3.4, marimo 0.25.1. Full list in `report/report_v5.md`, section 5.

```
pip install -r requirements.txt
```

`requirements.txt` pins every package above and also guppylang, hugr, scikit-learn, sympy, networkx, mqt-qcec and pytest.

Proxy note. In the development container outbound HTTPS goes through an agent proxy. pip installs were run with the proxy variables cleared for that one command: `NO_PROXY= no_proxy= pip install --break-system-packages <package>`. Local Selene runs also need every proxy variable unset (`HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= python ...`). aqora job submission needs the team credentials. The jobs submitted from this container on 8 October 2026 are listed in `results/emulator_jobs.csv`.

## Pass selector

`python3 pipelines/pass_select.py --psel4 <qasm files...>` runs PSEL4, the submitted tool, and prints one row per file. The candidates are P0, P2, L3 (official pass at optimisation level 3) and P2L3 (teleport_reduce then L3), tie order P0, L3, P2, P2L3 (`value/psel4_ledger.md`, `pipelines/test_psel4.py`). Each candidate is compiled through `compile_pipeline` (unchanged). The selector drops a candidate that raises, leaves the native gate set or fails its exactness check, and keeps the lowest HQC at 1000 shots. The check is the full unitary up to 8 qubits and 64 computational basis inputs (seed 20261010, all-zero included, one common global phase) from 9 to 20 qubits. Above 20 qubits no check is run and the candidate is marked `ok-unchecked`. `--check-zero` restores the earlier check on |0...0> alone. Ties go to the lower n_2q (ZZPhase + ZZMax), then by the tie order. `compile_select(circ, candidates=PSEL4_CANDIDATES)` returns the compiled circuit and a per-candidate record. Without `--psel4`, and in `compile_select(circ)` with its default candidates, `--psel4` the script runs the earlier two-candidate selector PSEL (P0 and P2, ties to P0). Tests: `python3 pipelines/test_pass_select.py`.
