# sgc-zx

Team Learned ZX Rewriting, Quantinuum Singapore Grand Challenge. A resource-certification benchmark for Quantinuum H2 with two cost layers: the NISQ layer (ZZPhase count, two-qubit depth, HQC, emulated fidelity) and the fault-tolerant layer (T-count against a per-instance certified floor). The submission report is `report/report_v1.md`, the executable companion is `report/notebook_skeleton.py`.

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
| `noise/dm_sim.py`, `noise/h2_params.py`, `noise/run_proxy.py` | Local density-matrix noise proxy for family A (n <= 8). Writes `results/family_A_proxy.csv` and `results/fig_proxy_fidelity_vs_n2q.{pdf,png}`. Provisional until emulator runs exist. |
| `barrier/certificate.py`, `barrier/NOTES.md` | Exact-arithmetic implementation of the T-count floor of the exactness-barrier manuscript (arXiv:2608.22801), with a line-by-line map to the manuscript. |
| `report/make_tables.py` | Generates every table and figure of the report from `results/*.csv` and injects the tables into `report/report_v1.md`. |
| `report/report_v1.md` | Submission report, draft v1. |
| `report/notebook_skeleton.py` | Marimo notebook: tables, figures, live compilation of one circuit through P0 and P2, gated submission to `nexus:H2-2E` through `aqora.QPU`. |
| `report/tables/`, `report/figures/` | Outputs of `make_tables.py`. |
| `results/` | All CSVs, logs and compiled QASM (hqslib1 header, measure-all appended). |
| `docs/platform_notes.md` | aqora API, emulator tiers, H2-2E noise parameters, HQC formula, with sources. |
| `papers/barrier/`, `papers/skzx/` | TeX sources of the two team manuscripts. |
| `third_party/pyzx-fork/` | Quantinuum pyzx fork at commit e695d6d7, source of the B1 circuits. |

## Reproducing every table

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
python noise/run_proxy.py --workers 2

# 8    tables and figures, injected into report/report_v1.md
python report/make_tables.py
```

Table A1 to A3 and the family A figure come from `results/family_A_counts.csv`. Table A4 comes from `results/family_A_proxy.csv`. Table B1 and its figure come from `results/family_B1_counts.csv`. Table B2 and its figure come from `results/family_B2_counts.csv`.

Pending steps: certificates (`barrier/certificate.py` on family B1 n = 5 and family B2) and emulator jobs (notebook section 3). Both are marked `[PENDING: ...]` in the report.

Tests, each runs as a script:

```
python bench/test_gen_trotter.py
python pipelines/test_compile.py
python noise/test_dm_sim.py
python barrier/test_certificate.py
```

## Notebook

```
marimo edit report/notebook_skeleton.py          # interactive
marimo export html report/notebook_skeleton.py -o notebook.html   # runs every cell up to the submission gate
```

Before submitting, set `TEAM_ORG` in the second cell to the team's aqora organization username. The submission cell is gated behind the **Submit to QPU** button and sends nothing until it is pressed. It submits the P0 and P2 compilations of the chosen circuit to `nexus:H2-2E` with `options={"noisy_simulation": ...}`.

## Environment

Python 3.13, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, selene-sim 0.3.4, marimo 0.25.1. Full list in `report/report_v1.md`, section 5.

```
pip install pytket==2.18.4 pytket-quantinuum==0.59.3 pyzx==0.10.7 qiskit==2.5.2 pygridsynth==2.0.0 aqora==0.35.1 marimo==0.25.1 numpy pandas scipy matplotlib
```

Proxy note. In the development container outbound HTTPS goes through an agent proxy. pip installs were run with the proxy variables cleared for that one command: `NO_PROXY= no_proxy= pip install --break-system-packages <package>`. Local Selene runs also need every proxy variable unset (`HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= python ...`). aqora job submission needs the team credentials and has not been exercised from this container.
