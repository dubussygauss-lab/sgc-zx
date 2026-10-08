# Summary for the judges

Team Learned ZX Rewriting. Quantinuum Singapore Grand Challenge, submission 1. Package draft of 8 October 2026, built from `report/report_v3.md`.

Tags. `[F]` marks a statement taken from the report or checkable in the repository. `[O]` marks a judgement. Every number below is quoted from `report.pdf` (rendered from `report/report_v3.md`) with its section. No number here is new.

## What the submission is

`[O]` A two-layer resource ledger for Quantinuum H2. The NISQ layer scores ZZPhase count, two-qubit depth, HQC and fidelity under the H2-2E noise parameters. The fault-tolerant layer scores the T-count after ZX rewriting against a per-instance certified floor. `[F]` Seven compilation pipelines are compared against pytket-quantinuum 0.59.3 `default_compilation_pass(optimisation_level=2)` as the baseline P0 (Section 2.2).

## Criterion 1. Problem and value (weight 0.3)

Report: Section 1 and Section 6. Artifacts: `docs/platform_notes.md` (sections 3.3 and 3.4), `pipelines/compile.py:hqc`.

- `[F]` The H2 price is HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_M) / 5000, so a two-qubit gate costs ten single-qubit gates (Section 1).
- `[F]` The H2-2E two-qubit error rate is p2 = 1.29e-3 against p1 = 7.3e-5 for a single-qubit gate (Section 1).
- `[O]` The ZZPhase count is therefore the one number a compiler for H2 has to minimise today (Section 1).
- `[O]` The user question answered is "should I run PyZX before pytket on H2", split by circuit family with the HQC consequence stated (Section 1).
- `[O]` The certified T-count floor prices the fault-tolerant layer that Helios credits will be spent on (Section 1).

## Criterion 2. Technical performance and hardware use (weight 0.3)

Report: Section 2.4, Section 2.6, Section 3 (Tables A1 to A5, B1, B1x, B2, S1, S2). Artifacts: `results/family_A_counts.csv`, `results/family_B1_counts.csv`, `results/family_B1x_counts.csv`, `results/family_B2_counts.csv`, `results/selene.md`, `results/selene_noiseless.csv`, `results/selene_depolarizing_full.csv`, `report/notebook_skeleton.py`.

- `[F]` Correctness. All 1260 family A rows, all 105 family B1 rows and all 100 family B2 rows pass the exactness check at tolerance 1e-8 (Section 2.4).
- `[F]` Benchmark gain. On the 15 checked family B1 circuits P2 is below P0 on 13 and equal on 2. The mean reduction is 6.9 % and the largest is vbe_adder_3 at 26.8 % (Section 3.2).
- `[F]` Scalability. On the 8 count-only family B1x circuits with 14 to 19 qubits P2 is below P0 on 5 and equal on 3. The aggregate ZZPhase count falls from 1329 to 1256, a reduction of 5.5 % (Section 3.2.1). These rows carry no exactness check.
- `[F]` Control family. P0 reaches one ZZPhase per two-body term on 180 of 180 Trotter circuits and no pipeline goes below it (Section 3.1).
- `[F]` Quantinuum tooling. 468 noiseless Selene runs on 156 compiled circuits flag no run and put no shot outside the exact support (Section 3.6, Table S1).
- `[F]` Noisy runs. In the 468-run Selene depolarising set at H2-2E rates the mean Hellinger fidelity is 0.9716 for P0, 0.9459 for P1 and 0.9702 for P2 (Section 3.6, Table S2).
- `[F]` Hardware status. Report v3 records no job on `H2-Emulator`, `H2-2E` or `H2-2SC` (Section 2.6, Section 3.7).

## Criterion 3. Scientific merit (weight 0.2)

Report: Section 2.5, Section 3.4, Section 4, Section 6. Artifacts: `barrier/certificate.py`, `barrier/NOTES.md`, `results/certificates.csv`, `results/certificates.md`, `model/cost_model.py`, `results/cost_model.md`, `results/cost_model_selene.md`, `papers/barrier/`, `papers/skzx/`.

- `[F]` Algorithm rationale. The floor is the least denominator exponent of the exact Pauli channel over Z[sqrt 2]. It bounds the T-count of every semantics-exact rewrite from below (Section 2.5).
- `[F]` Validation against the source. The certificate tests reproduce the manuscript's finite counts 24, 1536 and 18384 (Section 2.5).
- `[F]` Certified result. On the 20 family B2 circuits the floor is at least 99.28 % of the post-ZX T-count on every instance (Section 3.4).
- `[F]` Error analysis. On the four family B1 circuits at n = 5 the floor is 25.00 % to 55.22 % of the post-ZX T-count, so the bound is loose there (Section 3.4).
- `[F]` Literature check. The post-ZX T-counts match Table 1 of Kissinger and van de Wetering (arXiv:1903.10477) on all 13 family B1 circuits it lists (Section 3.2).
- `[F]` Learned cost model. Trained on family A the boosted model predicts family B1 with R^2 0.805 against 0.785 for the unfitted physics baseline. Trained on family B1 no model predicts family A and the best R^2 is 0.326 (Section 4.5).
- `[O]` What the data support across families is the physics baseline plus a support correction (Section 4.5).

## Criterion 4. Engineering and reproducibility (weight 0.2)

Report: Section 5. Artifacts: see the table.

| Rubric evidence | File |
|---|---|
| Repository | `code.zip` (git archive of the repository at the commit named in `REPRODUCE.md`) |
| README | `README.md` inside `code.zip` |
| Test results | `REPRODUCE.md` (Tests), `build_logs/tests_summary.txt`, `build_logs/test_*.log` |
| Reproduction record | `REPRODUCE.md`, report Section 5 |

- `[F]` Seven test files ran on 8 October 2026 and their pass counts are in `REPRODUCE.md`.
- `[F]` Two verification reports by agents that did not produce the results are in `results/verification_2026-10-07.md` and `results/verification_2026-10-07b.md` (Section 5).
- `[F]` Every table of Section 3 is generated by `report/make_tables.py` from `results/*.csv` (report preamble).

## Files in this package

| File | Content |
|---|---|
| `report.pdf` | The report, rendered from `report/report_v3.md` |
| `code.zip` | The repository at the recorded commit |
| `REPRODUCE.md` | Environment, commands, tests and seeds |
| `SUMMARY.md` | This page |
| `MANIFEST.txt` | Size and sha256 of every file |
| `build.sh`, `run_tests.sh`, `report.css` | Scripts that rebuild this package |
| `build_logs/` | Build log and test logs |
