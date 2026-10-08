# A certified resource ledger shows where ZX rewriting pays on Quantinuum H2

Team Learned ZX Rewriting. Quantinuum Singapore Grand Challenge, submission 1, draft v5 (8 October 2026).

Tags: `[F]` marks a statement verifiable from an artifact in the repository or from the cited source. `[O]` marks a judgement or a plan. Every number in a results table of Section 3 is produced by `report/make_tables.py` from `results/*.csv`. Items marked `[PENDING: emulator]` wait for emulator data that is not yet measured.

## Scoring map

`[F]` The four criteria and their weights are those of the track rubric, read from the Aqora GraphQL API on 8 October 2026 and stored in `docs/rubric.md`. `[O]` The table assigns the evidence for each criterion to a section of this report.

| Criterion | Weight | Where the evidence is |
|---|---|---|
| Problem & Value | 30 % | Section 1, Section 6 |
| Technical Performance & Hardware Use | 30 % | Section 3 (count tables A1 to B2 and the count-only table B1x, proxy tables A4 and A5, Selene tables S1 and S2, H2-Emulator table E1, H2-2E table E2), Section 2.6 and `results/selene.md` for the Selene runs, Sections 3.7 and 3.7.1 and `results/emulator_jobs.csv` for the platform jobs, notebook `report/notebook_skeleton.py` |
| Scientific Merit | 20 % | Section 2.5 (certificate), Section 3.4 and `results/certificates.md`, the two manuscripts in `papers/` |
| Engineering & Reproducibility | 20 % | Section 5 (environment, seeds, script table, test table, verification reports), `README.md`, the tests under `bench/`, `noise/`, `barrier/`, `pipelines/`, `selene/`, `model/`, `submit/` and `value/`, Section 4.7 for the refit command |

## 1. Problem and value

`[F]` The HQC, shot and T-count numbers below come from the script outputs `value/value_ledger.md` and `value/value_by_application.md`. The noise parameters come from `docs/platform_notes.md` section 3.3. The manuscript line numbers refer to `papers/barrier/main.tex`. P0 is pytket's Quantinuum pass at level 2. P2 runs PyZX teleport_reduce before that pass. HQC figures are for 1000 shots.

- `[O]` User. A team that runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget and will later price them on a fault-tolerant Helios.
- `[O]` Decision. Should this circuit go through ZX rewriting before pytket's Quantinuum pass?
- `[F]` H2 cost. On the 15 checked B1 circuits P2 costs 14,772.8 HQC against 15,516.0 for P0. The saving is 743.2 HQC or 4.8 %. The median per-circuit saving is 3.9 %.
- `[F]` Fault-tolerant cost. ZX removes 2,862 of 7,048 T gates on B1. Each T gate is one magic state, so the saving is 40.6 %. On the 20 synthesised B2 circuits 0.997 of the remaining T-count is certified incompressible.
- `[F]` Algorithms. Every circuit except hwb6, hwb8 and the two ham15 circuits is an adder, multiplier, Fourier transform, oracle, search instance or multi-controlled Toffoli. The adders, multipliers and the Fourier transform come from factoring and discrete-log circuits. grover_5 and mod5_4 come from search (Section 1.4). `[O]` The Toffoli circuits are placed in search as oracle and diffusion parts.

### 1.1 The user and the decision

`[O]` The user pays each H2 run in HQC from a fixed budget. On a fault-tolerant machine the same subroutines are priced in T gates. `[F]` The track budget is 10,000 HQC per team on H2-1E and H2-2E (Section 3.7).

`[O]` The decision is made per circuit: run P0 alone or insert the ZX stage first. The ledger answers it in HQC and in magic states. It also says when the answer is no.

`[F]` No user interview or survey is part of this submission. `[O]` The need rests on the H2 cost formula and on the algorithm literature of Section 1.4. We know of no published comparison of ZX rewriting against pytket's own Quantinuum pass on the native H2 gate set.

### 1.2 What the pipeline saves on H2 today

`[F]` The organisers' sample code prices an H2 program as HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_M) / 5000. N_1q counts PhasedX gates. N_2q counts ZZPhase and ZZMax gates. N_M counts initialisations, measurements and resets. Rz gates are free. The source is `estimate_cost` in `src/python/pytket_cost_estimation.py` of `Quantinuum/sg_grand_challenge`. `pipelines/compile.py:hqc` reproduces that function. `[O]` We take this as the H2 price. The Helios costing page gives the same form in its equation (1). See Reference 6 and `docs/platform_notes.md` section 3.4.

`[F]` Two-qubit gates also carry the dominant error. The H2-2E emulator parameters are p2 = 1.29e-3 and p1 = 7.3e-5 per gate, readout flips 9e-4 and 1.8e-3 for states 0 and 1 and p_init = 4e-5 (`docs/platform_notes.md` section 3.3).

`[F]` Table 1.1. HQC at 1000 shots by application area. B1 is checked. B1x is count-only and is never merged with B1. Saved % is computed on the area sums. Source: `value/value_by_application.md`.

| Area | Family | Circuits | HQC P0 | HQC P2 | HQC saved | Saved % | Median per-circuit % |
|---|---|---|---|---|---|---|---|
| Integer factoring (Shor) | B1 | 4 | 592.2 | 545.6 | 46.6 | 7.9 | 4.2 |
| Elliptic-curve discrete log, GF(2^m) | B1 | 1 | 216.2 | 215.2 | 1.0 | 0.5 | 0.5 |
| Unstructured search (Grover) | B1 | 8 | 1,183.6 | 1,127.0 | 56.6 | 4.8 | 3.0 |
| Reversible logic, no sourced algorithm | B1 | 2 | 13,524.0 | 12,885.0 | 639.0 | 4.7 | 4.5 |
| All areas | B1 | 15 | 15,516.0 | 14,772.8 | 743.2 | 4.8 | 3.9 |
| Integer factoring (Shor) | B1x | 2 | 386.2 | 380.2 | 6.0 | 1.6 | 1.4 |
| Elliptic-curve discrete log, GF(2^m) | B1x | 2 | 783.0 | 776.4 | 6.6 | 0.8 | 0.9 |
| Unstructured search (Grover) | B1x | 2 | 632.0 | 610.0 | 22.0 | 3.5 | 3.7 |
| Reversible logic, no sourced algorithm | B1x | 2 | 1,487.6 | 1,374.4 | 113.2 | 7.6 | 6.2 |
| All areas | B1x | 8 | 3,288.8 | 3,141.0 | 147.8 | 4.5 | 2.4 |

`[F]` P2 is cheaper than P0 in HQC on 14 of the 15 B1 circuits. hwb8 alone accounts for 84.6 % of the B1 saving but serves no sourced quantum algorithm. Without hwb8 the B1 saving is 114.6 HQC. `[O]` The median of 3.9 % is the better guide for a single circuit.

`[F]` Saved HQC buys shots. The following figures assume one job that pays the 5 HQC job fee once. At the 10,000 HQC team budget P0 affords 68,178 shots of vbe_adder_3 and P2 affords 87,675. That is 19,497 extra shots or 28.6 % more. On the Grover oracle mod5_4 the gain is 11,757 shots or 7.5 %.

`[F]` The H2 hardware guide limits a job to 10,000 shots (`docs/platform_notes.md` section 3.4). With that limit and one fee per job P0 affords 67,974 shots of vbe_adder_3 and P2 affords 87,324. That is 19,350 extra shots or 28.5 % more. On mod5_4 the gain is 11,584 shots or 7.4 % (`value/value_by_application.md`). Whether the per-job limit applies on H2-2E is Unverifiable from the repository.

`[F]` The ledger also says when not to run ZX. On the 180 Trotter circuits of family A P2 costs 17,453.0 HQC against 16,422.6 for P0. That is 1,030.4 HQC or 6.3 % more. P2 is dearer on 108 circuits and cheaper on 57. On the 60 XXZ circuits P2 is dearer on every circuit and the total rises by 12.3 %. `[O]` A user with a Trotter circuit should skip the ZX stage.

### 1.3 What it saves on the fault-tolerant layer

`[F]` In a surface-code machine each T gate consumes one magic state (Litinski, Quantum 3, 128 (2019), arXiv:1808.02892). Magic-state counts below therefore equal T-counts. On H2 a T gate is a free Rz and changes no H2 cost.

`[F]` Table 1.2. T-count written and after the ZX stage of P2, by application area. Source: `value/value_by_application.md`.

| Area | Family | T written | T after ZX | Magic states saved | Saved % |
|---|---|---|---|---|---|
| Integer factoring (Shor) | B1 | 307 | 199 | 108 | 35.2 |
| Elliptic-curve discrete log, GF(2^m) | B1 | 112 | 68 | 44 | 39.3 |
| Unstructured search (Grover) | B1 | 637 | 327 | 310 | 48.7 |
| Reversible logic, no sourced algorithm | B1 | 5,992 | 3,592 | 2,400 | 40.1 |
| All areas | B1 | 7,048 | 4,186 | 2,862 | 40.6 |
| Integer factoring (Shor) | B1x | 147 | 109 | 38 | 25.9 |
| Elliptic-curve discrete log, GF(2^m) | B1x | 427 | 265 | 162 | 37.9 |
| Unstructured search (Grover) | B1x | 343 | 171 | 172 | 50.1 |
| Reversible logic, no sourced algorithm | B1x | 735 | 309 | 426 | 58.0 |
| All areas | B1x | 1,652 | 854 | 798 | 48.3 |

`[F]` The exactness-barrier manuscript gives a per-instance floor (Kam, arXiv:2608.22801). The least denominator exponent of the exact Pauli channel of a Clifford+T circuit over Z[sqrt 2] is a lower bound on the T-count of every semantics-exact rewrite. The statements are Theorem B at line 1813, Corollary cert at line 2568 and Theorem C at line 2662 of `papers/barrier/main.tex`.

`[F]` On the 20 synthesised Haar circuits of family B2 the ZX stage removes 862 of 42,396 T gates or 2.0 %. The certified floor is 41,414 against 41,534 T gates after ZX. The certified-incompressible fraction is 0.997. Further exact T optimisation of these instances can gain at most 0.3 % of the remaining T-count. On the worst single instance the bound is 0.7 %.

`[F]` On the four certified B1 circuits the floor is 47 against 106 T gates after ZX. The fraction is 0.443. `[O]` The certificate does not say whether this gap is headroom for a better rewrite or slack in the bound (Section 3.4).

`[F]` Converting magic states into Helios time or cost needs factory and logical-cycle figures that Quantinuum has not published in any source we found. No conversion is made. As context only, Dasu et al. report a logical magic state on H1-1 with infidelity 7(+3/-1) x 10^-5 (arXiv:2506.14688).

### 1.4 Where these circuits sit in real algorithms

`[F]` Table 1.3. All B1 and B1x circuits appear in Table II of Amy and Mosca (arXiv:1601.07363). Each circuit is counted in the first area of the summary table of `docs/applications.md` that lists it.

| Area | Our circuits | Role | Citation | Status |
|---|---|---|---|---|
| Integer factoring (Shor) | vbe_adder_3, mod_mult_55, mod_red_21, qft_4 (B1). rc_adder_6, csla_mux_3 (B1x) | Adders and modular arithmetic of modular exponentiation. Fourier transform | arXiv:quant-ph/9511018, arXiv:1202.6614, arXiv:1710.07345, arXiv:quant-ph/0201067 | `[F]` |
| Elliptic-curve discrete log, GF(2^m) | gf2_pow_4_mult (B1). gf2_pow_5_mult, gf2_pow_6_mult (B1x) | Binary-field multiplier | arXiv:0710.1093 | `[F]` |
| Unstructured search (Grover) | grover_5, mod5_4 (B1) | Full search instance. Divisibility-by-5 oracle | arXiv:quant-ph/9605043, arXiv:1601.07363, reversiblebenchmarks.github.io/mod5.html | `[F]` |
| Unstructured search (Grover) | tof_3..5, barenco_tof_3..5 (B1). tof_10, barenco_tof_10 (B1x) | Multi-controlled Toffoli in oracle and diffusion | arXiv:1703.10535, arXiv:quant-ph/9503016 | `[O]` placement |
| Reversible logic, no sourced algorithm | hwb6, hwb8 (B1). ham15-low, ham15-med (B1x) | Reversible-logic stress tests | reversiblebenchmarks.github.io hwbs and ham15 pages | `[F]` no algorithm role found |

`[O]` The three adders also fit arithmetic oracles for chemistry and simulation (arXiv:1805.12445, arXiv:1807.03206). They are counted once under factoring.

`[F]` Unverifiable items. The function computed by mod_red_21 beyond its name is Unverifiable. Whether arXiv:0710.1093 is the exact work Amy, Maslov and Mosca cite for the field multipliers is Unverifiable.

### 1.5 Value statement and scope of claims

`[O]` For an H2 user the ledger is a reproducible answer to "should I run ZX before pytket" in HQC per area. `[F]` P2 saves 7.9 % on the checked factoring circuits and 4.8 % on the checked search circuits. `[O]` On Trotter circuits the answer is no. For the fault-tolerant programme the ledger gives certified magic-state counts per subroutine.

`[F]` The winner of the finals receives credits on the on-premise Helios machine in Singapore (organisers' timeline email, 25 Aug 2026). `[O]` Quantinuum's Helios roadmap targets fault tolerance. The certified T column prices the layer those credits will be spent on.

`[F]` Model prediction. A proxy fit of 1.18e-3 per ZZ gate predicts a relative fidelity gain of 1.79 % for P2 on vbe_adder_3 and a median relative gain of 0.24 % over B1. `[O]` These are model predictions and not measurements.

`[F]` The six H2-2E jobs of vbe_adder_3, hwb6 and grover_5 under P0 and P2 carry HQC estimates that sum to 1,840 HQC. At 1000 shots the emulator does not resolve P2 against P0 on any of the three. On vbe_adder_3 the measured F_H was 0.954 under P0 and 0.959 under P2 (Section 3.7.1).

`[F]` The ledger states value in HQC, shots and magic states and makes no claim in currency. The learned component of this submission is a cost model that predicts fidelity from compile-time features (Section 4). Learned rewriting is future work and is not claimed here.

## 2. Method

### 2.1 Circuit families

`[F]` Family A consists of 180 Trotter spin-chain circuits generated by `bench/gen_trotter.py`. Three models: the transverse-field Ising chain with open boundary, the XXZ chain started from the Neel state, and the transverse-field Ising ladder. Sizes n in {4, 6, 8, 10, 12}. Trotter steps r in {1, 2, 4} with dt = 0.1. Couplings are uniform (one instance per group) or drawn from [0.5, 1.5] with `numpy.random.default_rng(20261006)` (three instances per group). Every two-body Pauli exponential is written as a cx-rz-cx block with basis changes. The circuit as written therefore has n_cx = 2 x (number of ZZ-type terms). Ideal output distributions for n <= 10 are stored as `.npy` references.

`[F]` Family B1, 15 standard Clifford+T benchmark circuits with n <= 12 from the Quantinuum pyzx fork at commit e695d6d7 (`third_party/pyzx-fork/circuits/qasm`), built by `bench/build_family_B1.py`. Every Toffoli is expanded into the 7-T decomposition by pyzx so that the file as written is Clifford+T. The manifest `bench/family_B1/manifest.csv` records the source file, its commit and the counts before and after expansion, for example a T-count as written of 21 for tof_3 and 28 for mod5_4.

`[F]` Family B1x consists of 8 further Clifford+T benchmark circuits from the same pyzx fork at commit e695d6d7, selected by `bench/build_family_B1x.py` with the window 13 <= n <= 20 and at most 3000 gates after Toffoli expansion. The circuits are rc_adder_6 (n = 14), csla_mux_3 (15), gf2_pow_5_mult (15), ham15-low (17), ham15-med (17), gf2_pow_6_mult (18), barenco_tof_10 (19) and tof_10 (19). The qubit numbers reached run from 14 to 19 and the largest circuit is ham15-med with 1600 gates after expansion. The conversion and the manifest columns are those of family B1 (`bench/family_B1x/manifest.csv`). These circuits are compiled count-only under P0ref, P0 and P2 with the `--no-check` flag of `pipelines/run_bench_B.py`. No unitary, statevector or distribution check was run on them at this size and only the gate-set check applies. Every row of `results/family_B1x_counts.csv` therefore carries the status `ok-unchecked` and the family is reported separately from the checked families in Section 3.2.1.

`[F]` Family B2 consists of 20 Clifford+T circuits synthesised from Haar-random unitaries by `bench/gen_haar_b2.py`. There are five targets at n = 2 and five at n = 3 drawn with the same seed. Each target is synthesised at eps = 1e-3 and at eps = 1e-5. The construction is qiskit `qs_decomposition` followed by `transpile` to the basis {rz, sx, x, cx} with `seed_transpiler=0`. Every rz angle that is not a multiple of pi/4 is then replaced by a pygridsynth (Ross-Selinger) approximation to precision eps. The operator-norm error of each written circuit against its target is stored in the manifest, with the triangle-inequality bound n_rz x eps. This family reproduces the construction of Table E6 in the barrier manuscript.

### 2.2 Pipelines

`[F]` All pipelines are in `pipelines/compile.py` and target the H2 gate set {Rz, PhasedX, ZZPhase, ZZMax, Measure, Reset} with all-to-all connectivity. Seven pipelines run on families A and B1, five (P0ref, P0, P1, P2, P3) on family B2 and three (P0ref, P0, P2) on the count-only family B1x.

| Name | Stages |
|---|---|
| P0ref | DecomposeBoxes, AutoRebase to the native set, SquashRzPhasedX, RemoveRedundancies. The circuit as written, in native gates, with no optimisation. |
| P0 | pytket-quantinuum 0.59.3 `default_compilation_pass(optimisation_level=2)`, reproduced pass by pass from the installed source without a backend object (FullPeepholeOptimise to TK2, NormaliseTK2, DecomposeTK2 to ZZPhase, AutoRebase, squash, RemoveRedundancies). P0 is the baseline. |
| P0L1 | The same at optimisation level 1. |
| P1 | PyZX `full_reduce`, `extract_circuit`, `basic_optimization`, then P0. |
| P2 | PyZX `teleport_reduce`, `Circuit.from_graph`, `basic_optimization`, then P0. |
| P3 | pytket `ZXGraphlikeOptimisation`, then P0. |
| P4 | The ZX stage of P1, then P0 without FullPeepholeOptimise. |

`[F]` The ZX stages run on the circuit as written, in the gate set the ZX tools accept, and the pytket pass runs afterwards on the result. Angles are passed to PyZX through QASM, and the rounding introduced by PyZX's float-to-fraction conversion is recorded per circuit in the column `pyzx_angle_err` of `results/family_A_counts.csv`. Its maximum over the 1260 family A rows is 1.48e-10 rad, which is 4.7e-11 x pi.

### 2.3 Metrics

`[F]` For every compiled circuit `pipelines/compile.py:metrics` records n_2q (ZZPhase plus ZZMax count), the two-qubit depth, the PhasedX and Rz counts and the total gate count and depth. It also records the HQC at N_shots = 1000 with N_M = 2 n_qubits, one initialisation and one terminal measurement per qubit. The T-count after the ZX stage is counted on the PyZX circuit before any pytket pass, as the number of phase gates with angle an odd multiple of pi/4. After rebasing to the H2 gate set the T-count is undefined and is not reported.

`[F]` The fidelity metrics are the Hellinger fidelity F_H = (sum_i sqrt(p_i q_i))^2 and the total variation distance TVD = 0.5 sum_i |p_i - q_i| between a noisy or measured distribution q and the ideal distribution p from the `.npy` references. Both are reported for the local density-matrix proxy and for the Selene runs of Section 2.6.

`[F]` Both metrics are reported for the H2-Emulator output in Section 3.7. F_H is reported for the H2-2E output in Section 3.7.1, and TVD is in `results/emulator_nexus_H2-2E.csv`.

### 2.4 Exactness checks

`[F]` Every compiled circuit is checked against the P0ref compilation of the same input. The check is the unitary deviation 1 - |tr(U^dagger V)| / 2^n for n <= 8 and the statevector infidelity on |0...0> beyond, with tolerance 1e-8. Where a `.npy` reference exists, the maximum difference between the compiled output distribution and that reference is recorded as well. The measured QASM written for submission is re-simulated independently (`qasm_dist_maxdiff`). All 1260 family A rows, all 100 family B2 rows and all 105 family B1 rows pass. The two hwb8 rows under P1 and P2 come from the 5400 s run of Section 5 and have `check_dev` at most 1.7e-13. The 24 rows of family B1x were compiled with `--no-check` and carry no such check (Section 3.2.1).

`[F]` Family B2 is additionally checked against the Haar target it approximates. The largest deviation 1 - |tr(U_target^dagger U_compiled)| / 2^n over all 100 rows is 7.1e-6, within the gridsynth bound.

### 2.5 The certificate

`[F]` The barrier manuscript (arXiv:2608.22801) gives the floor in Theorem B(a), Corollary cert and Theorem C(c). The three statements are at lines 1813, 2568 and 2662 of `papers/barrier/main.tex`. Let C be an n-qubit Clifford+T circuit and let O be any optimiser that preserves its unitary exactly. Then the T-count of O(C) is at least lde(C^). Here C^ is the exact 4^n x 4^n Pauli-channel matrix of C with entries in Z[sqrt 2]. lde(C^) is the least e such that C^ = (P + Q sqrt 2) / sqrt 2^e with integer matrices P and Q. The fraction of T-count that any exact optimiser can remove is at most 1 - lde(C^) / t(C). The floor is computed from any word realising C, in one exact channel multiplication per gate, and does not depend on the word chosen.

`[F]` `barrier/certificate.py` implements the floor in exact integer arithmetic, with the single-qubit linkage procedure and the residue automaton of the manuscript as cross-checks. `barrier/test_certificate.py` reproduces the manuscript's finite verifications. These are the Clifford group order 24, the residue automaton with 24 states and 1536 transitions and the 18384 Matsumoto-Amano words with t <= 8. `barrier/NOTES.md` maps every implemented quantity to the line of the manuscript it comes from.

`[F]` The certificate was computed for the 20 family B2 circuits and for the four family B1 circuits at n = 5, where the 4^n x 4^n channel is small. The output per circuit is the floor, the T-count after the ZX stage of P1 and of P2 and the ratio floor / T_zx. The 24 rows are in `results/certificates.csv` and `results/certificates.md`. The invariant floor <= T_zx holds on all 24 rows, and P1 and P2 give the same T_zx on every row. Section 3.4 reports the rows.

`[F]` The manuscript is not re-derived here, with one exception that needs stating. While implementing the per-step bookkeeping of Lemma mqval(b), the implementation found that the "reduction fires exactly once" half of that lemma fails on the word T T (`barrier/NOTES.md`, section 8). The floor of Corollary cert does not use that half, and the manuscript's own text says nothing downstream depends on it. The correction is being made in the manuscript.

### 2.6 Hardware use

`[F]` Two emulator tiers exist (`docs/platform_notes.md`, section 3.1). `H2-Emulator` is hosted by Nexus and costed in seconds. `H2-2E` is a hardware-tier emulator costed in HQCs with the published H2-2E noise parameters. The syntax checker `H2-2SC` returns the HQC cost of a circuit without charge.

`[F]` Quantinuum's local emulator Selene (`selene-sim` 0.3.4 with `guppylang` 1.1.2) ran 468 noiseless runs, 68 depolarising runs in a first comparison and 468 depolarising runs on the full set on the team's container. The route reads `results/compiled/<pipeline>/<file>.qasm` with `pytket.qasm.circuit_from_qasm` and loads the circuit into a guppy program with `guppylang.guppy.load_pytket`. The program is built by `selene_sim.build` and run by `run_shots` on the Quest statevector backend at 2000 shots. `load_pytket` accepted the PhasedX, Rz, ZZPhase and Measure gates of every compiled circuit without rebase. The noiseless runs cover 144 family A circuits with n <= 10 and 12 family B1 circuits with n <= 10 under P0, P1 and P2. No run was flagged by the criterion TVD > 4 x sqrt(support / (2 pi N_shots)) and no shot landed outside the exact support. Scripts are in `selene/`, data in `results/selene_noiseless.csv` and `results/selene_depolarizing.csv`, and the summary in `results/selene.md`.

`[F]` The 68 depolarising runs use Selene's `DepolarizingErrorModel` at the H2-2E rates p_1q = 7.3e-5 and p_2q = 1.29e-3 on 17 circuits under P0 and P2, in two variants of 34 runs. The variant `gates_meas_init` adds p_meas = 1.35e-3 and p_init = 4e-5, where 1.35e-3 is the mean of the two H2-2E readout rates because Selene takes one symmetric rate. In that variant 32 of 34 runs agree with the local density-matrix proxy within two sampling standard deviations. The variant `gates_only` leaves readout and initialisation noiseless and is not the like-for-like comparison.

`[F]` The full depolarising run has 468 runs on the same 156 circuits under P0, P1 and P2 with the `gates_meas_init` rates at 2000 shots. Section 3.6 and Table S2 report it.

`[F]` The local proxy `noise/dm_sim.py` is a density-matrix simulator. It applies a depolarising channel after every PhasedX and ZZPhase gate and adds an asymmetric readout flip and an initialisation flip. The parameters are the published H2-2E values p1, p2, p_meas and p_init from `noise/h2_params.py:H2_2E_EMULATOR`. The emission, crosstalk, dephasing and angle-scaling entries of the H2-2E model are not modelled. `noise/run_proxy.py` produced `results/family_A_proxy_h22e.csv` (540 rows, 108 circuits x 5 pipelines) and `results/family_B1_proxy_h22e.csv` (35 rows, 7 circuits x 5 pipelines). The two files feed Tables A4 and A5 and the cost model of Section 4.

`[F]` Platform jobs started on 8 October 2026 through `aqora` 0.35.1 as team `learned_zx_rewriting`. The scripts `submit/syntax_check.py` and `submit/run_emulator.py` submit the compiled and measured QASM files in `results/compiled/<pipeline>/` at 1000 shots with `options={"noisy_simulation": True}`. One H2-2SC syntax check and three H2-Emulator jobs with 22 circuit rows completed. Section 3.7 and Table E1 report them. Six H2-2E jobs completed with an HQC estimate of 1840.0 in total. Section 3.7.1 and Table E2 report them.

`[O]` The planned emulator budget is one job per (circuit, pipeline) on family A for n <= 8 and family B1 for n <= 9, on P0 and P2 only. The count tables of Section 3 show that P1, P3 and P4 are above P0 on ZZPhase count on every family A circuit and on 14 of 15, 14 of 15 and 15 of 15 family B1 circuits. Emulating them would spend HQCs to confirm a lower fidelity.

## 3. Results

### 3.1 Family A, Trotter spin chains

`[F]` Table A1. Mean ZZPhase count by n and pipeline, 36 circuits per n. "ZZ terms" is n_cx / 2 of the circuit as written, the number of two-body Pauli exponentials in the Trotter formula.

<!-- TABLE:A1_zz_by_n -->
| n | circuits | ZZ terms | P0ref | P0 | P0L1 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 36 | 12.4 | 24.9 | 12.4 | 24.9 | 25.9 | 12.9 | 26.1 | 31.4 |
| 6 | 36 | 21.0 | 42.0 | 21.0 | 42.0 | 62.0 | 22.7 | 58.9 | 71.0 |
| 8 | 36 | 29.6 | 59.1 | 29.6 | 59.1 | 107.6 | 32.2 | 108.2 | 119.9 |
| 10 | 36 | 38.1 | 76.2 | 38.1 | 76.2 | 173.7 | 41.7 | 157.2 | 189.8 |
| 12 | 36 | 46.7 | 93.3 | 46.7 | 93.3 | 246.1 | 50.7 | 233.4 | 262.6 |
<!-- /TABLE:A1_zz_by_n -->

`[F]` Table A2. Each pipeline against P0 on the same circuit, 180 circuits. Ratios are averaged over circuits.

<!-- TABLE:A2_vs_P0 -->
| pipeline | better than P0 | equal to P0 | worse than P0 | mean ZZ ratio | min ZZ ratio | max ZZ ratio | mean 2q-depth ratio | mean HQC ratio |
|---|---|---|---|---|---|---|---|---|
| P0ref | 0 | 0 | 180 | 2.00 | 2.00 | 2.00 | 2.00 | 1.63 |
| P0L1 | 0 | 0 | 180 | 2.00 | 2.00 | 2.00 | 2.00 | 1.63 |
| P1 | 0 | 0 | 180 | 4.43 | 1.28 | 10.32 | 10.92 | 3.03 |
| P2 | 0 | 120 | 60 | 1.04 | 1.00 | 1.19 | 1.25 | 1.03 |
| P3 | 0 | 0 | 180 | 3.79 | 1.31 | 7.91 | 10.29 | 2.76 |
| P4 | 0 | 0 | 180 | 4.90 | 1.44 | 10.36 | 11.88 | 3.33 |
<!-- /TABLE:A2_vs_P0 -->

`[F]` Table A3. P0 against the ZZ term count, by model and Trotter steps.

<!-- TABLE:A3_floor -->
| model | r | circuits | mean ZZ terms | mean n_2q P0 | circuits with n_2q = ZZ terms |
|---|---|---|---|---|---|
| ladder | 1 | 20 | 10.0 | 10.0 | 20 |
| ladder | 2 | 20 | 20.0 | 20.0 | 20 |
| ladder | 4 | 20 | 40.0 | 40.0 | 20 |
| tfim | 1 | 20 | 7.0 | 7.0 | 20 |
| tfim | 2 | 20 | 14.0 | 14.0 | 20 |
| tfim | 4 | 20 | 28.0 | 28.0 | 20 |
| xxz | 1 | 20 | 21.0 | 21.0 | 20 |
| xxz | 2 | 20 | 42.0 | 42.0 | 20 |
| xxz | 4 | 20 | 84.0 | 84.0 | 20 |
<!-- /TABLE:A3_floor -->

![Family A ZZPhase ratio](figures/fig_A_zz_ratio.png)

Figure 1. Family A. ZZPhase count of each pipeline divided by the P0 count on the same circuit, mean over the 36 circuits at each n with the min-max band shaded. The dashed line is P0 itself. Data: Table A2 and `results/family_A_counts.csv`.

`[F]` P0 compiles every one of the 180 circuits to exactly one ZZPhase per two-body term. No pipeline goes below that count on any circuit. P2 equals P0 on 120 circuits and is worse on 60, by at most a factor 1.19. P1, P3 and P4 are worse than P0 on all 180 circuits. The ratio to P0 runs from 1.28 to 10.32 for P1, from 1.31 to 7.91 for P3 and from 1.44 to 10.36 for P4. The mean ratio grows with n for each of the three, from 2.39 at n = 4 to 6.53 at n = 12 for P1, from 2.49 to 5.18 for P3 and from 2.92 to 6.92 for P4.

`[O]` One ZZPhase per two-body exponential is the natural count for this family and P0 reaches it. A rewrite that preserves the unitary has no room to remove entangling gates here. The ZX extraction pipelines add them because `extract_circuit` resynthesises the graph with CNOTs that no longer follow the Trotter term structure.

### 3.2 Family B1, Clifford+T benchmarks

`[F]` Table B1. ZZPhase count per circuit and pipeline. "T after ZX" is the T-count of the PyZX circuit after the ZX stage of P1 and P2, which agree on every circuit. The hwb8 rows under P1 and P2 come from the 5400 s run described below.

<!-- TABLE:B1_per_circuit -->
| circuit | n | T written | ZZ P0ref | ZZ P0 | ZZ P0L1 | ZZ P1 | ZZ P2 | ZZ P3 | ZZ P4 | P2 vs P0 % | T after ZX | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tof_3 | 5 | 21 | 18 | 15 | 18 | 22 | 14 | 25 | 25 | 6.7 | 15 |  |
| barenco_tof_3 | 5 | 28 | 24 | 20 | 24 | 23 | 19 | 27 | 27 | 5.0 | 16 |  |
| mod5_4 | 5 | 28 | 28 | 24 | 28 | 25 | 22 | 20 | 29 | 8.3 | 8 |  |
| qft_4 | 5 | 69 | 46 | 36 | 46 | 43 | 36 | 64 | 57 | 0.0 | 67 |  |
| tof_4 | 7 | 35 | 30 | 25 | 30 | 31 | 23 | 40 | 38 | 8.0 | 23 |  |
| barenco_tof_4 | 7 | 56 | 48 | 40 | 48 | 41 | 38 | 54 | 54 | 5.0 | 28 |  |
| hwb6 | 7 | 105 | 116 | 99 | 116 | 130 | 94 | 189 | 144 | 5.1 | 75 |  |
| mod_mult_55 | 9 | 49 | 48 | 41 | 48 | 71 | 39 | 85 | 90 | 4.9 | 35 |  |
| tof_5 | 9 | 49 | 42 | 35 | 42 | 48 | 32 | 56 | 66 | 8.6 | 31 |  |
| barenco_tof_5 | 9 | 84 | 72 | 60 | 72 | 70 | 57 | 90 | 87 | 5.0 | 40 |  |
| grover_5 | 9 | 336 | 288 | 240 | 288 | 256 | 218 | 322 | 278 | 9.2 | 166 |  |
| vbe_adder_3 | 10 | 70 | 66 | 56 | 66 | 55 | 41 | 61 | 67 | 26.8 | 24 |  |
| mod_red_21 | 11 | 119 | 105 | 88 | 105 | 107 | 83 | 140 | 132 | 5.7 | 73 |  |
| gf2_pow_4_mult | 12 | 112 | 99 | 83 | 99 | 260 | 83 | 277 | 290 | 0.0 | 68 |  |
| hwb8 | 12 | 5887 | 7118 | 5912 | 7118 | 8305 | 5587 | 11537 | 8461 | 5.5 | 3517 |  |
<!-- /TABLE:B1_per_circuit -->

![Family B1 ZZPhase count](figures/fig_B1_zz.png)

Figure 2. Family B1. ZZPhase count per circuit for P0ref, P0 and P2 on a log scale. Circuits are ordered by qubit number and then by T-count. hwb8 (5912 under P0) is omitted. Data: Table B1.

`[F]` On the 15 circuits P2 is below P0 on 13, equal on 2 (qft_4 and gf2_pow_4_mult) and above on none. The mean reduction against P0 is 6.9 %. The largest is vbe_adder_3, 56 to 41 ZZPhase gates, 26.8 %. P1 is above P0 on 14 of 15 and below on one (vbe_adder_3). P3 is above P0 on 14 of 15 and below on one (mod5_4). P4 is above P0 on 15 of 15.

`[F]` The hwb8 rows under P1 and P2 come from a separate run with a 5400 s limit (`results/family_B1_hwb8_long_counts.csv`, run log `results/family_B1_hwb8_long_run.log`), which completed P1 in 886 s and P2 in 844 s of wall time. P1 gives 8305 ZZPhase gates against 5912 under P0 and P2 gives 5587, a reduction of 5.5 %. Both leave the T-count at 3517, the P4 value. The two rows are merged into `results/family_B1_counts.csv`, and Table B1 and the counts in the previous paragraph include them. The pre-merge file is kept as `results/family_B1_counts_before_hwb8_merge.csv`.

`[F]` The T-counts after the ZX stage equal the PyZX column of Table 1 in Kissinger and van de Wetering, "Reducing the number of non-Clifford gates in quantum circuits", Phys. Rev. A 102, 022406 (2020), arXiv:1903.10477 (arXiv title "Reducing T-count with the ZX-calculus"), for all 13 family B1 circuits that table lists, both for the T-count as written and for the T-count after phase teleportation (checked against arXiv:1903.10477v3 on 7 October, results/literature_tcount_check.md). grover_5 and qft_4 are not in that table. Their values 166 and 67 equal the T-counts of the optimised circuits shipped in the PyZX repository (circuits/optimized/grover_5_pyzx.qc and qft_4_pyzx.qc, commit e695d6d7).

- tof_3: 21 to 15
- mod5_4: 28 to 8
- vbe_adder_3: 70 to 24
- grover_5: 336 to 166

`[O]` Teleport reduction keeps the circuit skeleton and only moves phases, so the pytket pass that follows sees a circuit of the same shape with fewer non-Clifford phases and can merge more. Full reduction with extraction replaces the skeleton, and the extracted CNOT structure costs more two-qubit gates on H2 than the original.

`[F]` The certified T-count floors for the four n = 5 circuits are in Table C1 of Section 3.4. The floor is at or below the T-count after the ZX stage on all four, and the ratio floor / T after ZX is 25.00 % for barenco_tof_3 and mod5_4, 26.67 % for tof_3 and 55.22 % for qft_4.

`[F]` Neither the H2-Emulator rows of Section 3.7 nor the H2-2E rows of Section 3.7.1 resolve P2 against P0 on a single circuit at 1000 shots.

#### 3.2.1 Family B1x, 13 to 20 qubits, count-only

`[F]` The 8 circuits of family B1x are unchecked. No unitary, statevector or distribution check was run on them and only the gate-set check applies. Every row of `results/family_B1x_counts.csv` carries the status `ok-unchecked`. `[O]` Their counts are reported here as a separate block and are not merged into the family B1 totals above. `[F]` Table B1x. ZZPhase count and two-qubit depth per circuit under P0ref, P0 and P2, with the T-count as written and the T-count after the ZX stage of P2. Circuits are ordered by n and then by T-count as written.

<!-- TABLE:B1x_per_circuit -->
Count-only rows, status ok-unchecked on every row: no unitary, statevector or distribution check was run at this size, only the gate-set check. P2 vs P0 % = 100 (1 - ZZ P2 / ZZ P0).

| file | n | ZZ P0ref | ZZ P0 | ZZ P2 | P2 vs P0 % | depth_2q P0 | depth_2q P2 | T written | T after ZX P2 |
|---|---|---|---|---|---|---|---|---|---|
| rc_adder_6 | 14 | 88 | 76 | 73 | 3.9 | 48 | 43 | 77 | 47 |
| csla_mux_3 | 15 | 76 | 63 | 63 | 0.0 | 31 | 32 | 70 | 62 |
| gf2_pow_5_mult | 15 | 154 | 129 | 129 | 0.0 | 68 | 84 | 175 | 115 |
| ham15-low | 17 | 236 | 204 | 198 | 2.9 | 145 | 124 | 161 | 97 |
| ham15-med | 17 | 534 | 427 | 379 | 11.2 | 344 | 266 | 574 | 212 |
| gf2_pow_6_mult | 18 | 221 | 185 | 185 | 0.0 | 86 | 90 | 252 | 150 |
| tof_10 | 19 | 102 | 85 | 77 | 9.4 | 77 | 68 | 119 | 71 |
| barenco_tof_10 | 19 | 192 | 160 | 152 | 5.0 | 145 | 130 | 224 | 100 |
<!-- /TABLE:B1x_per_circuit -->

`[F]` On the 8 circuits P2 is below P0 on 5, equal on 3 (csla_mux_3, gf2_pow_5_mult and gf2_pow_6_mult) and above on none. The aggregate ZZPhase count over the 8 circuits is 1329 under P0 and 1256 under P2, a reduction of 5.5 %. The mean of the per-circuit reductions is 4.1 %. The largest reduction is ham15-med, 427 to 379 ZZPhase gates, 11.2 %. P0 is below P0ref on 8 of 8, with an aggregate of 1603 under P0ref against 1329 under P0. The two-qubit depth under P2 is below P0 on the 5 circuits where the count is below and above P0 on the 3 circuits where the count is equal. The ZX stage of P2 leaves no phase outside the pi/4 grid on any circuit and lowers the T-count from 1652 written to 854 over the 8 circuits.

`[F]` On rc_adder_6 the circuit as written has 93 CX gates and the P0ref compilation has 88 ZZPhase gates, so the rebase-only pipeline already removes 5 two-qubit gates before any optimisation. The same happens on csla_mux_3, 80 CX as written against 76 under P0ref. On the other 6 circuits the P0ref count equals the CX count as written. `[F]` pytket `RemoveRedundancies` applied alone to the written circuit leaves 91 CX on rc_adder_6 and 72 on csla_mux_3 (recomputed on 8 October), so the P0ref figures come from the whole stage sequence of P0ref and not from one cancellation rule. `[O]` The P0ref count is the right reference for the P0 and P2 reductions on these two circuits, and the CX count as written is not.

`[O]` The combined statement for the Clifford+T benchmarks is: checked family B1, 15 circuits, P2 below P0 on 13 and equal on 2. Count-only family B1x, 8 circuits, P2 below P0 on 5 and equal on 3. The two totals stay separate because the B1x rows have no exactness check.

### 3.3 Family B2, synthesised Haar unitaries

`[F]` Table B2. Means over 5 circuits per row. "T red. %" is the T-count reduction by the ZX stage against the circuit as written. "max target dev." is the largest 1 - |tr(U_target^dagger U_compiled)| / 2^n in the row.

<!-- TABLE:B2_summary -->
| n | eps | circuits | mean T written | T after ZX P1 | T red. % P1 | T after ZX P2 | T red. % P2 | T after ZX P3 | T red. % P3 | ZZ P0 | ZZ P2 | HQC P0 | max target dev. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 1e-05 | 5 | 1048.4 | 1024.4 | 2.3 | 1024.4 | 2.3 | 1037.6 | 1.0 | 3 | 3 | 16.6 | 3.2e-10 |
| 2 | 0.001 | 5 | 638.4 | 624.4 | 2.2 | 624.4 | 2.2 | 628.4 | 1.6 | 3 | 3 | 16.6 | 1.9e-06 |
| 3 | 1e-05 | 5 | 4220.8 | 4167.2 | 1.3 | 4167.2 | 1.3 | 4189.6 | 0.7 | 19 | 19 | 56.4 | 9.4e-10 |
| 3 | 0.001 | 5 | 2571.6 | 2490.8 | 3.1 | 2490.8 | 3.1 | 2522.8 | 1.9 | 19 | 19 | 56.4 | 7.1e-06 |
<!-- /TABLE:B2_summary -->

![Family B2 T-count reduction](figures/fig_B2_t.png)

Figure 3. Family B2. Percentage of the written T-count removed by the ZX stage of P1, P2 and P3, mean over the 5 circuits in each (n, eps) group. P1 and P2 give the same T-count on every circuit. Data: Table B2.

`[F]` The mean raw T-counts match the barrier manuscript's Table E6 for the two rows it reports: n = 2 at eps = 1e-3 gives 638.4 here against 644 there, and n = 3 at eps = 1e-3 gives 2571.6 against 2570. The manuscript rows are means over 50 and 8 instances, this table over 5.

`[F]` The ZX stage removes between 1.3 % and 3.1 % of the T-count under P1 and P2, and between 0.7 % and 1.9 % under P3. The ZZPhase count after P0 is 3 at n = 2 and 19 at n = 3 for every circuit, and P2 leaves it unchanged.

`[O]` Synthesised circuits are the case where the fault-tolerant layer matters and the NISQ layer does not. The two-qubit count is fixed by the KAK or QSD skeleton. The whole cost is in the gridsynth words, which are near their floors by construction, and the certificate measures how near.

`[F]` The certified floor of every one of the 20 circuits is in Table C1 of Section 3.4. The floor divided by the T-count after the ZX stage averages 99.84, 99.79, 99.57 and 99.76 % over the four (n, eps) configurations in the row order of Table C1. The minimum over the 20 circuits is 99.28 %.

### 3.4 Certificates

`[F]` Table C1. The exactness-barrier certificate (`barrier/certificate.py`, Section 2.5) on the 20 family B2 circuits and the four family B1 circuits with n = 5, from `results/certificates.csv`. The 4^n x 4^n channel is small at these sizes. The floor is the least denominator exponent of the exact Pauli channel of the circuit as written. "T after ZX" is the T-count after PyZX teleport_reduce, which equals the full_reduce value on every row.

<!-- TABLE:C1_certificates -->
Per circuit. floor = lde of the exact Pauli channel (Corollary cert, Theorem C(c)), T after ZX = T-count after PyZX teleport_reduce (P2, equal to the full_reduce value on every row), achieved % = 100 (1 - T after ZX / T written).

| family | file | n | T written | floor | T after ZX | floor / T after ZX % | achieved % |
|---|---|---|---|---|---|---|---|
| B2 | haar_n2_eps1e-03_s1 | 2 | 662 | 651 | 652 | 99.85 | 1.51 |
| B2 | haar_n2_eps1e-03_s2 | 2 | 628 | 611 | 612 | 99.84 | 2.55 |
| B2 | haar_n2_eps1e-03_s3 | 2 | 638 | 630 | 630 | 100.00 | 1.25 |
| B2 | haar_n2_eps1e-03_s4 | 2 | 622 | 613 | 614 | 99.84 | 1.29 |
| B2 | haar_n2_eps1e-03_s5 | 2 | 642 | 612 | 614 | 99.67 | 4.36 |
| B2 | haar_n2_eps1e-05_s1 | 2 | 1046 | 1021 | 1022 | 99.90 | 2.29 |
| B2 | haar_n2_eps1e-05_s2 | 2 | 1046 | 1025 | 1026 | 99.90 | 1.91 |
| B2 | haar_n2_eps1e-05_s3 | 2 | 1038 | 1002 | 1004 | 99.80 | 3.28 |
| B2 | haar_n2_eps1e-05_s4 | 2 | 1052 | 1030 | 1036 | 99.42 | 1.52 |
| B2 | haar_n2_eps1e-05_s5 | 2 | 1060 | 1033 | 1034 | 99.90 | 2.45 |
| B2 | haar_n3_eps1e-03_s1 | 3 | 2566 | 2483 | 2496 | 99.48 | 2.73 |
| B2 | haar_n3_eps1e-03_s2 | 3 | 2544 | 2442 | 2452 | 99.59 | 3.62 |
| B2 | haar_n3_eps1e-03_s3 | 3 | 2570 | 2486 | 2490 | 99.84 | 3.11 |
| B2 | haar_n3_eps1e-03_s4 | 3 | 2588 | 2511 | 2520 | 99.64 | 2.63 |
| B2 | haar_n3_eps1e-03_s5 | 3 | 2590 | 2478 | 2496 | 99.28 | 3.63 |
| B2 | haar_n3_eps1e-05_s1 | 3 | 4208 | 4132 | 4144 | 99.71 | 1.52 |
| B2 | haar_n3_eps1e-05_s2 | 3 | 4218 | 4158 | 4162 | 99.90 | 1.33 |
| B2 | haar_n3_eps1e-05_s3 | 3 | 4224 | 4179 | 4188 | 99.79 | 0.85 |
| B2 | haar_n3_eps1e-05_s4 | 3 | 4248 | 4184 | 4192 | 99.81 | 1.32 |
| B2 | haar_n3_eps1e-05_s5 | 3 | 4206 | 4133 | 4150 | 99.59 | 1.33 |
| B1 | barenco_tof_3 | 5 | 28 | 4 | 16 | 25.00 | 42.86 |
| B1 | mod5_4 | 5 | 28 | 2 | 8 | 25.00 | 71.43 |
| B1 | qft_4 | 5 | 69 | 37 | 67 | 55.22 | 2.90 |
| B1 | tof_3 | 5 | 21 | 4 | 15 | 26.67 | 28.57 |

Family B2 by configuration, 5 circuits each.

| n | eps | circuits | mean T written | mean floor / T after ZX % | min floor / T after ZX % | mean achieved % | mean collapse rate % |
|---|---|---|---|---|---|---|---|
| 2 | 1e-03 | 5 | 638.4 | 99.84 | 99.67 | 2.19 | 1.25 |
| 2 | 1e-05 | 5 | 1048.4 | 99.79 | 99.42 | 2.29 | 1.34 |
| 3 | 1e-03 | 5 | 2571.6 | 99.57 | 99.28 | 3.14 | 1.86 |
| 3 | 1e-05 | 5 | 4220.8 | 99.76 | 99.59 | 1.27 | 0.80 |
<!-- /TABLE:C1_certificates -->

`[F]` The invariant floor <= T after ZX holds on 24 of 24 rows, for the full_reduce and the teleport_reduce T-counts alike, and the two T-counts are equal on 24 of 24 rows. The certificate ran in at most 0.4 s per circuit at n = 2, at most 36.4 s at n = 3 and at most 38.5 s on the n = 5 family B1 circuits (`wall_s` in the CSV).

`[F]` On family B2 the configuration means of the floor divided by the T-count after the ZX stage are 99.84, 99.79, 99.57 and 99.76 % in the row order of Table C1. The minimum over the 20 circuits is 99.28 % (haar_n3_eps1e-03_s5, floor 2478 against 2496 after ZX) and the maximum is 100.00 % (haar_n2_eps1e-03_s3). The barrier manuscript calls this quantity lde / T_tel (caption of Table tab:e6, `papers/barrier/main.tex` line 3066). Its Table tab:e6 (lines 3076 and 3079) reports 99.79 +/- 0.30 with minimum 98.6 at (2, 1e-3) over 50 instances and 99.55 +/- 0.20 with minimum 99.3 at (3, 1e-3) over 8 instances. Line 3108 states that the quantity averages 99.4 to 99.9 % and never falls below 96.9 % on any instance. All four configuration means here lie inside 99.4 to 99.9 % and every instance is above 96.9 %. The (n, eps) = (2, 1e-5) and (3, 1e-5) configurations have no counterpart in that table. The manuscript's line 3118 gives the collapse rate as 1.0 to 2.3 %. The collapse rate here is 1.25, 1.34, 1.86 and 0.80 % in the same row order. The last configuration sits below that range.

`[O]` The number a user reads from Table C1 is the gap between the two percentages. On family B2 the ZX stage removes 1.3 to 3.1 % of the written T-count. The certificate shows that at most 0.16 to 0.43 % of the remaining count is removable by any semantics-exact rewrite on the configuration means and at most 0.72 % on any single instance. The gridsynth words are within a fraction of a percent of their floor and no further optimiser effort on them is worth paying for.

`[F]` On the four family B1 circuits the floor is loose. For mod5_4 the floor is 2 while the ZX stage leaves 8 T gates, so the floor is 25.00 % of the achieved count, and the denominator exponent collapses at 19 of the 28 T gates in the certificate's step record (`collapse_count` in the CSV). The ratios on barenco_tof_3 and tof_3 are 25.00 % and 26.67 % and on qft_4 it is 55.22 %.

`[O]` The B1 floors are loose because these circuits are hand-written Toffoli networks, not synthesised ring elements. The theorem bounds the T-count of every exact rewrite from below by the denominator exponent of the channel, and on a gridsynth word the exponent grows by one at all but 0.5 to 2.5 % of the T gates (the per-instance `collapse_rate` in the CSV), so the bound is tight there. In a Toffoli network most T gates cancel in the channel and the exponent stays small, so the bound stays well below what any known rewrite reaches. The gap between 2 and 8 on mod5_4 is either headroom for a better rewrite or slack in the bound, and the certificate does not say which. The manuscript's percentages are stated for synthesised circuits only and the B1 rows are not covered by them.

### 3.5 Noise proxy with H2-2E parameters

`[F]` Table A4. Local density-matrix proxy on family A at n <= 8 with 36 circuits per (n, pipeline) cell and 540 rows in `results/family_A_proxy_h22e.csv`. The simulator is `noise/dm_sim.py` with the published H2-2E emulator parameters from `noise/h2_params.py` (p1 = 7.3e-5, p2 = 1.29e-3, readout flips 9e-4 and 1.8e-3, p_init = 4e-5). The ideal distribution is the family reference `bench/family_A/<stem>.npy`.

<!-- TABLE:A4_proxy -->
Provisional local proxy. Density-matrix simulation with the published H2-2E emulator parameters (p1 = 7.3e-5, p2 = 1.29e-3, readout 9e-4 and 1.8e-3, p_init = 4e-5) and no leakage, crosstalk or dephasing, to be replaced by emulator runs. Mean Hellinger fidelity F_H of the noisy output distribution against the ideal one.

| n | circuits per pipeline | F_H P0ref | F_H P0 | F_H P1 | F_H P2 | F_H P3 |
|---|---|---|---|---|---|---|
| 4 | 36 | 0.9867 | 0.9922 | 0.9893 | 0.9919 | 0.9893 |
| 6 | 36 | 0.9785 | 0.9874 | 0.9735 | 0.9862 | 0.9743 |
| 8 | 36 | 0.9704 | 0.9826 | 0.9504 | 0.9807 | 0.9514 |

| pipeline | mean F_H | mean TVD | mean n_2q | mean n_1q |
|---|---|---|---|---|
| P0ref | 0.9785 | 0.0352 | 42.0 | 57.7 |
| P0 | 0.9874 | 0.0210 | 21.0 | 40.1 |
| P1 | 0.9710 | 0.0494 | 65.1 | 62.8 |
| P2 | 0.9863 | 0.0221 | 22.6 | 42.0 |
| P3 | 0.9717 | 0.0482 | 64.4 | 72.9 |
<!-- /TABLE:A4_proxy -->

`[F]` P0 and P2 have the highest fidelity in every one of the nine (model, n) cells of family A and P0 is above P0ref on 108 of 108 circuits. P0 and P2 differ by at most 0.0056 in any cell (xxz at n = 8), and per circuit P2 is above P0 on 43 and below on 65. P1 and P3 are below P0 and below P2 in every cell. The position of P0ref depends on the model. On ladder and tfim P0ref is above P1 and P3 in all six cells and on 36 of 36 circuits each. On xxz P0ref is below P1 in all three cells and below P3 at n = 4 and n = 6, because on xxz the extraction pipelines leave a ZZPhase count close to the P0ref count (30.3 against 42.0 at n = 4 under P1) while on ladder and tfim they leave 1.4 to 3.2 times the P0ref count. Over the 36 circuits at each n the ordering is P0 ~ P2 > P0ref > P1 ~ P3 at n = 6 and n = 8, and at n = 4 P1 and P3 (both 0.9893) sit above P0ref (0.9867).

`[F]` Table A5. The same proxy on the seven family B1 circuits with n <= 7, 35 rows in `results/family_B1_proxy_h22e.csv`. The ideal distribution is the noise-free output of the P0ref circuit. "support" is the number of outcomes with probability above 1e-12.

<!-- TABLE:A5_proxy_b1 -->
| circuit | n | support | F_H P0ref | F_H P0 | F_H P1 | F_H P2 | F_H P3 | ZZ P0 | ZZ P2 |
|---|---|---|---|---|---|---|---|---|---|
| barenco_tof_3 | 5 | 1 | 0.9696 | 0.9739 | 0.9692 | 0.9747 | 0.9644 | 20 | 19 |
| mod5_4 | 5 | 1 | 0.9647 | 0.9689 | 0.9661 | 0.9710 | 0.9705 | 24 | 22 |
| qft_4 | 5 | 16 | 0.9641 | 0.9704 | 0.9623 | 0.9706 | 0.9527 | 36 | 36 |
| tof_3 | 5 | 1 | 0.9759 | 0.9791 | 0.9691 | 0.9800 | 0.9655 | 15 | 14 |
| barenco_tof_4 | 7 | 1 | 0.9430 | 0.9513 | 0.9451 | 0.9528 | 0.9316 | 40 | 38 |
| hwb6 | 7 | 1 | 0.8751 | 0.8915 | 0.8521 | 0.8962 | 0.7977 | 99 | 94 |
| tof_4 | 7 | 1 | 0.9614 | 0.9667 | 0.9567 | 0.9684 | 0.9464 | 25 | 23 |
<!-- /TABLE:A5_proxy_b1 -->

`[F]` On family B1 P2 is above P0 on 7 of 7 circuits and P0 is above P0ref on 7 of 7. P1 is below P0 on 7 of 7 and P3 on 6 of 7. The exception is mod5_4, where P3 has the fewest ZZPhase gates of any pipeline (20 against 24 under P0). The largest fidelity gain of P2 over P0 is hwb6, 0.8915 to 0.8962 with 99 to 94 ZZPhase gates.

`[F]` A fit of -ln F_H = a n_2q with no intercept gives a = 1.18e-3 +/- 2.3e-5 on the 35 family B1 rows, with centred R^2 0.968, against the two-qubit error rate p2 = 1.29e-3 of the noise model. On the 540 family A rows the same fit gives a = 5.14e-4 +/- 1.3e-5 with centred R^2 0.612. Per model the slope is 2.28e-4 on ladder, 2.26e-4 on tfim and 7.58e-4 on xxz. The standard errors are from the residual variance and the R^2 is centred, 1 - SS_res / SS_tot about the mean of -ln F_H (`results/proxy_h22e_fits.log`, Section 4).

`[F]` The family B1 circuits have a single-outcome ideal distribution on 6 of 7 circuits (support 16 on qft_4), the xxz circuits have mean support 29.8 and the ladder and tfim circuits have mean support 107.8 out of 2^n. Adding a support term to the family A fit, -ln F_H = a n_2q + b n_1q + u support, gives u = -7.9e-5 per outcome and raises the centred R^2 from 0.714 to 0.784.

`[O]` The slope follows the support of the ideal distribution. A depolarising error after a two-qubit gate moves probability off the ideal outcomes, and the Hellinger fidelity pays for it in full when the ideal distribution is a single outcome and only in part when the ideal distribution already covers most strings. The B1 slope close to p2 is the first case and the ladder and tfim slopes near 0.18 p2 are the second. A cost model that predicts F_H from gate counts therefore needs the support as a feature, which is the reason it enters Section 4.

`[O]` The proxy contains no leakage, crosstalk, idle dephasing or the RZZ angle scaling of the published H2-2E model, so it ranks pipelines by their ZZPhase count under the H2-2E gate rates and does not predict the emulator's absolute fidelity. The emulator runs of Section 3.7 replace it.

### 3.6 Selene runs

`[F]` Tables S1 and S2. Runs of the compiled circuits on Quantinuum's local emulator Selene (`selene-sim` 0.3.4, route in Section 2.6), from `results/selene_noiseless.csv` (468 rows), `results/selene_depolarizing.csv` (68 rows) and `results/selene_depolarizing_full.csv` (468 rows). The noiseless runs cover the 144 family A circuits with n <= 10 and the 12 family B1 circuits with n <= 10 under P0, P1 and P2 at 2000 shots. The full depolarising run covers the same 156 circuits under P0, P1 and P2 at 2000 shots with `DepolarizingErrorModel` at the H2-2E rates p_1q = 7.3e-5, p_2q = 1.29e-3, p_meas = 1.35e-3 and p_init = 4e-5.

<!-- TABLE:S1_selene -->
Noiseless runs (IdealErrorModel, Quest backend). TVD is against the exact output distribution of the compiled QASM, TVD_scale = sqrt(support / (2 pi shots)).

| family | circuits | pipelines | runs | shots per run | max TVD | max TVD / TVD_scale | flagged (TVD > 4 TVD_scale) | shots outside support |
|---|---|---|---|---|---|---|---|---|
| A | 144 | P0, P1, P2 | 432 | 2000 | 0.117 | 1.111 | 0 | 0 |
| B1 | 12 | P0, P1, P2 | 36 | 2000 | 0.080 | 1.121 | 0 | 0 |

Depolarising runs (DepolarizingErrorModel, p_1q = 7.3e-5, p_2q = 1.29e-3) against the density-matrix proxy, pipelines P0 and P2. z = (F_H Selene - mean F_H of 400 2000-shot samples of the proxy distribution) / their sd. gates_meas_init adds p_meas = 1.35e-3 and p_init = 4e-5, gates_only sets both to 0.

| family | variant | runs | abs z <= 2 | mean z | sd z | max abs z | mean F_H Selene - proxy exact | mean F_H Selene - proxy sampled |
|---|---|---|---|---|---|---|---|---|
| A | gates_meas_init | 20 | 20 | -0.13 | 0.82 | 1.73 | -0.0075 | -0.0007 |
| A | gates_only | 20 | 17 | 0.83 | 1.17 | 3.52 | -0.0035 | 0.0033 |
| B1 | gates_meas_init | 14 | 12 | -0.50 | 1.18 | 2.81 | -0.0029 | -0.0027 |
| B1 | gates_only | 14 | 10 | 1.24 | 1.11 | 2.43 | 0.0045 | 0.0046 |
<!-- /TABLE:S1_selene -->

`[F]` In the 468 noiseless runs the largest TVD between the sampled and the exact distribution is 0.117 and the largest ratio of TVD to its sampling scale sqrt(support / (2 pi N_shots)) is 1.121, so no run reaches the flag threshold of 4. No shot landed outside the exact support in any of the 468 runs. The support is smaller than 2^n on 276 runs, so a shot could have landed outside it there. The exact distribution of each compiled QASM file agrees with the family reference to 5.7e-11. The TVD divided by its asymptotic expectation for the actual distribution has median 0.93 and maximum 2.26 over the 468 runs. A pooled chi-square test against the exact multinomial on the 234 runs with support between 2 and 64 gives p < 0.01 on 4 runs and p < 0.05 on 13, against 2.3 and 11.7 expected under the null. The 4 runs were resampled with fresh seeds at 20000 shots (`results/selene_recheck.txt`) and none of the deviations persists.

`[O]` A wrong measure map or a wrong gate in the compiled QASM would put shots on zero-probability strings or push the TVD above its sampling scale. Neither happened on any of the 156 circuits under any of the three pipelines, so the compiled files run on Quantinuum's own toolchain and reproduce the distributions the local checks computed.

<!-- TABLE:S2_selene_depol -->
Depolarising runs on the full set (DepolarizingErrorModel, p_1q = 7.3e-5, p_2q = 1.29e-3, p_meas = 1.35e-3, p_init = 4e-5, 2000 shots). F_H is the Hellinger fidelity of the Selene samples to the ideal distribution. P0 > P1 and P2 > P1 count circuits with a strictly higher F_H.

| family | n | circuits | mean F_H P0 | mean F_H P1 | mean F_H P2 | P0 > P1 | P2 > P1 |
|---|---|---|---|---|---|---|---|
| A | 4 | 36 | 0.9914 | 0.9880 | 0.9902 | 33 | 29 |
| A | 6 | 36 | 0.9832 | 0.9706 | 0.9820 | 35 | 32 |
| A | 8 | 36 | 0.9705 | 0.9410 | 0.9691 | 36 | 34 |
| A | 10 | 36 | 0.9517 | 0.8918 | 0.9501 | 36 | 36 |
| B1 | 5 | 4 | 0.9722 | 0.9638 | 0.9739 | 4 | 3 |
| B1 | 7 | 3 | 0.9328 | 0.9210 | 0.9308 | 2 | 2 |
| B1 | 9 | 4 | 0.9121 | 0.8816 | 0.9109 | 4 | 4 |
| B1 | 10 | 1 | 0.9410 | 0.9260 | 0.9350 | 1 | 1 |
| all |  | 156 | 0.9716 | 0.9459 | 0.9702 | 151 | 141 |
<!-- /TABLE:S2_selene_depol -->

`[F]` Table S2. The full depolarising run has 468 runs on 156 circuits. The mean F_H over the 156 circuits is 0.9716 for P0, 0.9459 for P1 and 0.9702 for P2. P0 is strictly above P1 on 151 circuits and P2 is strictly above P1 on 141. Both P0 and P2 are strictly above P1 on 140 of the 156 circuits. The 16 exceptions are 14 family A circuits with n <= 8 and the B1 circuits barenco_tof_3 and barenco_tof_4.

`[F]` The mean of F_H(P2) minus F_H(P0) over the 156 circuits is -0.0013 and P2 is strictly above P0 on 67 circuits. The single-run sampling sd of F_H at 2000 shots has mean 0.0028 over the 345 runs with a proxy row. The mean difference is therefore 0.47 single-run sampling sd. The standard error of the mean difference over the 156 circuits is 0.0004.

`[O]` A single circuit's ordering of P2 against P0 is not resolved at 2000 shots. The ensemble mean favours P0 by 0.0013 in F_H, which is small next to the P1 deficit of 0.0256 against P0.

`[F]` 345 of the 468 runs have a density-matrix proxy row. The 123 runs without one are the family A circuits with n = 10 and the family B1 circuits with n = 9 and n = 10. On the 345 runs |z| <= 2 holds for 335, which is 97.1 %. The mean z is -0.001 and the population sd of z is 0.957 with largest |z| 2.82. Independent draws from the proxy's sampling distribution give mean 0, sd 1 and 95.4 % within two sd. The mean of F_H under Selene minus the exact proxy F_H is -0.0051 and falls to +0.0002 against the proxy's F_H evaluated on 2000-shot samples.

`[F]` An earlier 68-run comparison on 17 circuits under P0 and P2 agreed within two sd on 32 of 34 runs in `gates_meas_init` and on 27 of 34 runs in `gates_only`, which leaves readout and initialisation noiseless.

`[F]` Selene's `DepolarizingErrorModel` was probed at p = 0.3 with 20000 shots per probe (`selene/calibrate_error_model.py`, `results/selene_calibration.txt`). Rz gates receive no noise. A single-qubit gate flips with probability 0.2051 +/- 0.0029 against 2p / 3 = 0.200 for a uniformly random non-identity Pauli. A ZZPhase leaves the 00 state with probability 0.2442 +/- 0.0030 against 12p / 15 = 0.240. Readout flips symmetrically at 0.306 and 0.304 and initialisation flips at 0.298. The conventions match `noise/dm_sim.py`, except that the proxy's readout flip is asymmetric and Selene's is one rate.

`[O]` Selene's `DepolarizingErrorModel` and the proxy share one gate-level convention, so their agreement checks the proxy's implementation and its handling of the measure map. The agreement does not test fidelity to H2-2E. Neither model contains the emission and leakage branch, the crosstalk or the duration-based dephasing of the published H2-2E model. The Selene runs are the first use of Quantinuum tooling in this submission and the emulator runs of Section 3.7 are the second.

`[F]` Wall time on the 2-core container was 465 s for the 468 noiseless runs and 68 s for the 68-run comparison, both with two processes. The per-run wall times of the 468 full depolarising runs sum to 1437 s. Every TVD and F_H value of the noiseless runs and the 68-run comparison was bit-identical between two complete runs of the driver. `results/selene.md` records one execution of the full depolarising run.

### 3.7 Emulator runs

`[F]` Access. The team reached the Quantinuum platforms on 8 October 2026 through `aqora` 0.35.1 as team `learned_zx_rewriting`.

`[F]` Quotas. The Aqora forum topic "Emulator Cost" by Irfan Khan of Quantinuum sets 2 hours of H2-Emulator time per team and 10,000 HQC per team on H2-1E and H2-2E. The syntax checkers are free. The same topic states that teams have no usage tracking.

`[F]` Syntax check. The H2-2SC syntax check of tof_3 under P0 completed as job `AFByb3ZpZGVySm9iAaEcdqFKfvGiVyt1pWCaEQ`. All 1000 shots returned the all-zero string and the job returned no cost. The raw payload is `results/emulator/nexus_H2-2SC/P0/tof_3.json`.

`[F]` Table E1. Nexus H2-Emulator runs with noise at 1000 shots, from `results/emulator_nexus_H2-Emulator.csv` (22 rows) and the counts in `results/emulator/nexus_H2-Emulator/`. Three jobs completed. The first ran tof_3 under P0 and P2 with a reported duration of 167 s. The second ran barenco_tof_3, barenco_tof_4 and barenco_tof_5 under P0, P1 and P2 and grover_5 under P0 in 953 s. The third ran ladder_n4_r1, ladder_n4_r2 and ladder_n4_r4 under P0, P1 and P2 and ladder_n6_r1 under P0 in 309 s. The job ledger is `results/emulator_jobs.csv`. `report/make_tables.py` recomputes every F_H from the stored counts and asserts agreement with the CSV to 1e-9.

<!-- TABLE:E1_h2emulator -->
Nexus H2-Emulator, noisy_simulation = True, 1000 shots per row. F_H is the Hellinger fidelity of the returned counts to the ideal distribution. sd F_H emulator is the sd of F_H over 4000 multinomial bootstrap resamples of the counts (seed 20261008). F_H proxy is the exact density-matrix proxy value of Section 3.5 and is empty where the proxy has no row. F_H Selene depol is the 2000-shot Selene DepolarizingErrorModel value of Section 3.6.

| file | n | pipeline | n_2q | F_H emulator | sd F_H emulator | F_H proxy | F_H Selene depol |
|---|---|---|---|---|---|---|---|
| tof_3 | 5 | P0 | 15 | 0.9860 | 0.0037 | 0.9791 | 0.9785 |
| tof_3 | 5 | P2 | 14 | 0.9810 | 0.0044 | 0.9800 | 0.9810 |
| barenco_tof_3 | 5 | P0 | 20 | 0.9770 | 0.0048 | 0.9739 | 0.9740 |
| barenco_tof_3 | 5 | P1 | 23 | 0.9760 | 0.0049 | 0.9692 | 0.9700 |
| barenco_tof_3 | 5 | P2 | 19 | 0.9660 | 0.0057 | 0.9747 | 0.9655 |
| barenco_tof_4 | 7 | P0 | 40 | 0.9500 | 0.0068 | 0.9513 | 0.9470 |
| barenco_tof_4 | 7 | P1 | 41 | 0.9420 | 0.0073 | 0.9451 | 0.9490 |
| barenco_tof_4 | 7 | P2 | 38 | 0.9660 | 0.0057 | 0.9528 | 0.9450 |
| barenco_tof_5 | 9 | P0 | 60 | 0.9280 | 0.0080 |  | 0.9305 |
| barenco_tof_5 | 9 | P1 | 70 | 0.9160 | 0.0088 |  | 0.9120 |
| barenco_tof_5 | 9 | P2 | 57 | 0.9130 | 0.0088 |  | 0.9255 |
| grover_5 | 9 | P0 | 240 | 0.7898 | 0.0131 |  | 0.8245 |
| ladder_n4_r1_uniform_s1 | 4 | P0 | 4 | 0.9993 | 0.0009 | 0.9992 | 0.9984 |
| ladder_n4_r1_uniform_s1 | 4 | P1 | 11 | 0.9927 | 0.0027 | 0.9954 | 0.9948 |
| ladder_n4_r1_uniform_s1 | 4 | P2 | 4 | 0.9981 | 0.0014 | 0.9992 | 0.9978 |
| ladder_n4_r2_uniform_s1 | 4 | P0 | 8 | 0.9993 | 0.0017 | 0.9995 | 0.9975 |
| ladder_n4_r2_uniform_s1 | 4 | P1 | 25 | 0.9901 | 0.0033 | 0.9933 | 0.9899 |
| ladder_n4_r2_uniform_s1 | 4 | P2 | 8 | 0.9947 | 0.0018 | 0.9995 | 0.9970 |
| ladder_n4_r4_uniform_s1 | 4 | P0 | 16 | 0.9957 | 0.0026 | 0.9998 | 0.9987 |
| ladder_n4_r4_uniform_s1 | 4 | P1 | 42 | 0.9912 | 0.0032 | 0.9970 | 0.9950 |
| ladder_n4_r4_uniform_s1 | 4 | P2 | 16 | 0.9924 | 0.0029 | 0.9998 | 0.9975 |
| ladder_n6_r1_uniform_s1 | 6 | P0 | 7 | 0.9963 | 0.0018 | 0.9986 | 0.9962 |
<!-- /TABLE:E1_h2emulator -->

`[F]` Quota event. A fourth job of 10 family B1 circuits was rejected with `QuotaExceedException: Quota 'simulation' would be exceeded`. It held grover_5 under P1 and P2, hwb6 and mod5_4 under P0, P1 and P2 and mod_mult_55 under P0 and P1. The three completed jobs had reported 1429 s, which is 19.8 % of the 7200 s quota. The ledger records a duration of 823 s for the rejected job. `[O]` The cause of the gap between 1429 s and 7200 s is not known. One hypothesis is that the platform charges each circuit of a batch separately. The other is that it rejects a job on a duration pre-estimate before running it.

`[F]` Sampling error. The bootstrap sd of F_H at 1000 shots is 0.0037 to 0.0088 on the 11 B1 rows with a single ideal outcome and agrees with the binomial value sqrt(F_H (1 - F_H) / 1000) to 2.2 %. It is 0.0009 to 0.0033 on the 10 family A rows and 0.0131 on grover_5. The no-intercept fit of -ln F_H on n_2q over the B1 proxy rows gives 1.18e-3 per ZZ gate. P2 removes 1 to 3 ZZ gates against P0 on tof_3, barenco_tof_3, barenco_tof_4 and barenco_tof_5. The F_H gain expected from that slope is 0.0012 to 0.0033 on those four circuits. The sd of the measured P2 minus P0 difference is 0.0057 to 0.0119 on the same circuits. The expected gain is therefore 0.15 to 0.28 of one sd. The measured differences are -0.005, -0.011, +0.016 and -0.015 with z = -0.87, -1.48, +1.81 and -1.26 in the order above. All four lie within two sd of zero. At F_H = 0.955, the mean over the 11 single-outcome B1 rows, a one-gate gain reaches two sd of the difference only at 2.7e5 shots per pipeline.

`[O]` At 1000 shots the sampling error of F_H exceeds the fidelity difference expected from 1 to 3 fewer ZZ gates. The emulator data establish that the compiled circuits run correctly on the Quantinuum platform and that the team has used it. They do not resolve P2 against P0 on any single circuit. That comparison rests on the ZZ counts of Section 3.2 and the ensemble means of Table S2.

`[F]` Comparison with the proxy. On the 18 rows with a proxy value the mean of F_H emulator minus F_H proxy is -0.0007 and the mean absolute difference is 0.0042. The mean is -0.0031 on the 10 family A rows and +0.0022 on the 8 B1 rows. 15 of the 18 rows lie within two emulator sd of the proxy. The three rows outside are barenco_tof_4, ladder_n4_r2 and ladder_n4_r4, all under P2.

`[F]` Comparison with Selene. On all 22 rows the mean of F_H emulator minus F_H Selene is -0.0011 and the mean absolute difference is 0.0055. The sd of the difference combines the emulator sd with a Selene sd taken as the emulator sd times sqrt(1000 / 2000). 20 of the 22 rows lie within two sd. The two rows outside are barenco_tof_4 under P2 and grover_5 under P0.

`[F]` On ladder_n4_r1, ladder_n4_r2 and ladder_n4_r4 the P2 circuit has the same ZZ count and two-qubit depth as P0 and no more PhasedX gates. The emulator F_H of P2 is below P0 on all three with z = -0.68, -1.88 and -0.83. `[O]` The proxy predicts equal F_H for these pairs. The published H2-2E noise model has angle-dependent two-qubit errors and dephasing that the proxy lacks. This report does not establish whether the H2-Emulator uses that model, and the difference is not resolved at 1000 shots.

#### 3.7.1 H2-2E

`[F]` Runs. vbe_adder_3, hwb6 and grover_5 ran on the Nexus H2-2E emulator under P0 and P2 with `noisy_simulation = True` at 1000 shots. Each of the six circuits went in its own job. All six jobs completed on 8 October 2026 and are the `nexus:H2-2E` rows of `results/emulator_jobs.csv`. The job ids in the order P0 then P2 are the following.

- `[F]` vbe_adder_3: `AFByb3ZpZGVySm9iAaEcwoXVdfGm_ordi_7h5w`, `AFByb3ZpZGVySm9iAaEcyAXPe_KMnSd2cLrgKg`
- `[F]` hwb6: `AFByb3ZpZGVySm9iAaEczGiEcIO6R60fhgRfMw`, `AFByb3ZpZGVySm9iAaEc2Kp3dxCmIno2DMeWtA`
- `[F]` grover_5: `AFByb3ZpZGVySm9iAaEc31OVdBG5qZ8C3KUGnQ`, `AFByb3ZpZGVySm9iAaEc47DrcSKGODVcQ3R9uw`

`[F]` Cost. The HQC estimates stored with the six jobs sum to 1840.0 HQC. That is 18.4 % of the 10,000 HQC quota per team on H2-1E and H2-2E. The cost fields returned by the platform hold a duration and no HQC value. The charged amount is therefore not recorded in the repository.

`[F]` Table E2. The six rows of `results/emulator_nexus_H2-2E.csv` with the counts in `results/emulator/nexus_H2-2E/`. `submit/h22e_stats.py` recomputes every F_H from the counts. `report/make_tables.py` asserts agreement with the CSV and with the JSON payloads to 1e-9.

<!-- TABLE:E2_h22e -->
`[F]` Nexus H2-2E, noisy_simulation = True, 1000 shots per row, one job per row. F_H is the Hellinger fidelity of the returned counts to the ideal distribution. sd F_H is the binomial value sqrt(F_H (1 - F_H) / 1000) on vbe_adder_3 and hwb6, whose ideal output is a single bit string. On grover_5 it is the sd over 4000 multinomial bootstrap resamples of the counts (seed 20261008). HQC estimate is the formula value stored with each job. F_H proxy is the exact density-matrix proxy value of Section 3.5 and is empty where the proxy has no row (n > 7). F_H Selene depol is the 2000-shot Selene DepolarizingErrorModel value of Section 3.6.

| file | n | pipeline | n_2q | HQC estimate | F_H | sd F_H | F_H proxy | F_H Selene depol |
|---|---|---|---|---|---|---|---|---|
| vbe_adder_3 | 10 | P0 | 56 | 151.6 | 0.9540 | 0.0066 |  | 0.9410 |
| vbe_adder_3 | 10 | P2 | 41 | 119.0 | 0.9590 | 0.0063 |  | 0.9350 |
| hwb6 | 7 | P0 | 99 | 243.0 | 0.9240 | 0.0084 | 0.8915 | 0.8845 |
| hwb6 | 7 | P2 | 94 | 232.6 | 0.9090 | 0.0091 | 0.8962 | 0.8805 |
| grover_5 | 9 | P0 | 240 | 565.6 | 0.8652 | 0.0114 |  | 0.8245 |
| grover_5 | 9 | P2 | 218 | 528.2 | 0.8728 | 0.0112 |  | 0.8315 |
<!-- /TABLE:E2_h22e -->

`[F]` Paired differences. F_H(P2) minus F_H(P0) is +0.0050 with sd 0.0091 and z = +0.55 on vbe_adder_3. It is -0.0150 with sd 0.0124 and z = -1.21 on hwb6. It is +0.0076 with sd 0.0160 and z = +0.48 on grover_5. All three lie within two sd of zero.

`[F]` Predicted gain. The no-intercept fit of -ln F_H on n_2q over the 35 family B1 proxy rows gives a = 1.1801e-3 per ZZ gate. `submit/h22e_stats.py` refits it and checks it against line 77 of `results/proxy_h22e_fits.log`. P2 removes 15, 5 and 22 ZZ gates against P0 on vbe_adder_3, hwb6 and grover_5. The predicted F ratio exp(a dN_2q) is 1.0179, 1.0059 and 1.0263 on the three circuits. Applied to the measured P0 value it gives predicted gains of 0.0170, 0.0055 and 0.0228. These are 1.87, 0.44 and 1.42 sd of the measured difference. The measured differences lie below the predicted gains by 1.32, 1.66 and 0.95 sd.

`[F]` Shots for a 2-sd resolution. The sd of the difference scales as one over the square root of the shot count. The predicted gain equals two sd of the difference at 1147 shots per pipeline on vbe_adder_3, 20462 on hwb6 and 1974 on grover_5.

`[F]` Comparison with the proxy. Only hwb6 has a proxy row because the proxy stops at n = 7. The emulator F_H of hwb6 lies 3.88 sd above the proxy under P0 and 1.41 sd above it under P2. The proxy predicts a P2 gain of +0.0047 on hwb6.

`[F]` Comparison with Selene. The emulator F_H exceeds the 2000-shot Selene depolarising value on all six rows. The excess runs from 0.0130 to 0.0413 with z from 1.60 to 3.85. Five of the six rows lie more than two sd above Selene. The sd combines the emulator sd with a Selene sd taken as the emulator sd times sqrt(1000 / 2000) as in Section 3.7.

`[F]` Comparison with the H2-Emulator. grover_5 under P0 also ran on the H2-Emulator in Table E1 with F_H 0.7898. Its H2-2E value 0.8652 is 4.33 sd higher. The sd combines the Table E1 sd 0.0131 with the Table E2 sd 0.0114. `submit/h22e_stats.py` prints this z.

`[F]` The H2-2E runs do not resolve P2 against P0 at 1000 shots on any of the three circuits. They agree with the proxy within sampling error on hwb6 under P2 and not under P0. The emulator F_H lies above the proxy and above Selene on every row where either exists. At the predicted gains a 2-sd resolution needs 1147 shots per pipeline on vbe_adder_3 and 1974 on grover_5. On hwb6 it needs 20462.

`[O]` The H2-2E runs confirm execution and HQC accounting on the Quantinuum H2-2E emulator. One reading is that H2-2E applies less error to these B1 circuits than the depolarising model at the published rates. This report does not test that reading.

## 4. Learned cost model

`[F]` Version 1 of this section was a protocol with no trained model. Version 2 trains the model on the local proxy fidelities of Section 3 and reports its validation. Every number in Tables M1 and M2 is produced by `report/make_tables.py` from `results/cost_model_metrics.csv` and `results/cost_model_coefficients.csv`, which are written by `model/cost_model.py`.

`[F]` Data. The training set is the proxy output of `noise/run_proxy.py` with the published H2-2E emulator defaults p1 = 7.3e-5, p2 = 1.29e-3, readout flip rates 9e-4 and 1.8e-3 and p_init = 4e-5. Family A contributes 540 rows, the 108 Trotter circuits with n in {4, 6, 8} under the five pipelines P0ref, P0, P1, P2 and P3. Family B1 contributes 35 rows, the 7 benchmark circuits with n in {5, 7} under the same five pipelines. F_H is the Hellinger fidelity of the exact noisy output distribution against the ideal one, with no shot sampling. `[O]` These are proxy numbers from a density-matrix model that omits leakage, crosstalk and duration-based dephasing. The script reruns unchanged on emulator CSVs with the same columns, and every table of this section will be refit on emulator data `[PENDING: emulator]`.

### 4.1 Target and features

`[F]` The target is y = -ln F_H. For a product of independent small error channels F_H is close to exp(-sum_k p_k N_k), so y is linear in the gate counts to first order. The seven features are read from the compiled circuit: n_2q, the ZZPhase and ZZMax count, which carries the dominant fault probability p2. n_1q, the PhasedX count, which carries p1. Rz is virtual and noiseless and is not counted. n_qubits, the number of measured qubits, which carries one readout and one initialisation fault each. depth_2q, the two-qubit depth, which stands in for idle error since the proxy has no duration model. support_size, the number of bitstrings with ideal probability above 1e-12, and log2_support. The seventh feature is the interaction n_2q_offsupport = n_2q (1 - support_size / 2^n). `[O]` The interaction is justified by the metric. A Pauli fault after a gate moves a fraction of the output mass to other bitstrings. When the ideal distribution covers most of the 2^n strings the displaced mass lands on strings that already carry ideal weight and the Hellinger overlap barely changes. When the ideal output is one string every fault removes its mass from the support and the full per-gate error appears in y. The factor (1 - support_size / 2^n) is the fraction of the output space outside the support and is the first-order estimate of the lost mass. `[F]` The two families sit at opposite ends of this factor. The mean support fraction support_size / 2^n is 0.758 in family A and 280 of its 540 rows have full support. In family B1 the mean support fraction is 0.088 and the three values that occur are 0.0078, 0.031 and 0.5.

### 4.2 Models

`[F]` Four models are fitted to y on the same feature matrix. The physics baseline y = p2 n_2q + p1 n_1q + (p_meas_avg + p_init) n_qubits has no fitted parameter, with p_meas_avg + p_init = 1.39e-3 the mean of the two readout flip rates plus the initialisation fault. The OLS model is least squares on the seven features without intercept, since an empty circuit has y = 0 and the n_qubits column carries the SPAM floor. The ridge model scales each column to unit RMS on the training set and applies penalty lambda = 1 to the scaled coefficients, again without intercept. The gradient-boosted model is sklearn `GradientBoostingRegressor` with 300 trees of depth 3, learning rate 0.05, subsample 0.8 and `random_state=0`. `[O]` The three fitted models are ordered by capacity. OLS tests whether a linear correction of the physics baseline is enough. Ridge tests whether the OLS coefficients are stable under shrinkage. The boosted model is the learned component and tests whether a nonlinear fit buys anything beyond the linear one.

### 4.3 Validation splits

`[F]` Three kinds of split are reported. Leave-one-family-out trains on A and tests on B1 and the reverse. Leave-one-model-out trains on two of the three Trotter models of A and tests on the third. Five-fold cross-validation on the pooled 575 rows is run twice. In the plain split cv5 the rows are shuffled into folds with seed 0. In the grouped split cv5g the folds are drawn over circuit classes, where a class is the file name with the disorder-seed suffix removed, so that all pipelines and all seeds of a class are in the same fold.

`[F]` The grouped split exists because the seeds of one circuit class are near-duplicate rows. 27 of the 54 classes of A have three disorder seeds. Within one class and one pipeline the three seeds have identical n_2q, identical depth_2q and identical support_size in 130 of the 135 three-seed class-pipeline groups, and their F_H values lie within 0.0056 of each other. A random fold therefore places a near-copy of almost every test row in the training set and its score measures interpolation between pipelines and seeds of a circuit already seen. `[F]` The effect is visible in Table M1. The boosted model scores R^2 0.990 on cv5 and 0.971 on cv5g on the pooled rows, and 0.923 against 0.830 on the B1 rows. `[O]` The grouped split is the one that answers the question a user asks, which is the fidelity of a circuit the model has not seen, and it is the split used for the calibration figure and the permutation importance.

### 4.4 Results

`[F]` Table M1. R^2 of y and mean absolute error of F_H on the test set of each split, one cell per model. R^2 is taken about the mean of the test y and is negative for a model worse than that mean. n is the number of test rows.

<!-- TABLE:M1_cost_metrics -->
| split | train | test | n | physics | ols | ridge | gbr |
|---|---|---|---|---|---|---|---|
| lofo | A | B1 | 35 | 0.785 / 0.0151 | 0.560 / 0.0252 | 0.840 / 0.0150 | 0.805 / 0.0083 |
| lofo | B1 | A | 540 | -3.513 / 0.0430 | -261.894 / 0.1971 | -0.605 / 0.0259 | 0.326 / 0.0184 |
| lomo | A minus ladder | A ladder | 180 | -34.797 / 0.0489 | 0.399 / 0.0058 | 0.410 / 0.0060 | 0.751 / 0.0030 |
| lomo | A minus tfim | A tfim | 180 | -33.455 / 0.0424 | 0.637 / 0.0044 | 0.522 / 0.0047 | 0.843 / 0.0023 |
| lomo | A minus xxz | A xxz | 180 | -2.061 / 0.0376 | -1.272 / 0.0350 | 0.541 / 0.0159 | -1.035 / 0.0353 |
| cv5 | A+B1 (4/5) | A+B1 (1/5) | 575 | -2.739 / 0.0413 | 0.944 / 0.0050 | 0.944 / 0.0050 | 0.990 / 0.0009 |
| cv5g | A+B1 (4/5) | A+B1 (1/5) | 575 | -2.739 / 0.0413 | 0.938 / 0.0051 | 0.938 / 0.0052 | 0.971 / 0.0017 |
| cv5g | A+B1 (4/5) | A rows of fold | 540 | -3.513 / 0.0430 | 0.937 / 0.0049 | 0.935 / 0.0050 | 0.990 / 0.0014 |
| cv5g | A+B1 (4/5) | B1 rows of fold | 35 | 0.785 / 0.0151 | 0.918 / 0.0090 | 0.926 / 0.0079 | 0.830 / 0.0074 |
<!-- /TABLE:M1_cost_metrics -->

`[F]` Table M2. Coefficients of y per unit of each feature. The physics column is fixed by the emulator parameters. The OLS columns give the coefficient and its t statistic for the three training sets. The ridge column is the shrunk coefficient on the pooled set. The last column is the permutation importance of the boosted model, the mean increase of out-of-fold mean squared error of y when that feature is shuffled in the test fold of cv5g, with the standard deviation over 5 folds times 10 shuffles. `[O]` The OLS standard errors assume independent homoscedastic residuals. The five pipeline rows of one circuit are not independent, so the t statistics are optimistic and only their ranking is used below.

<!-- TABLE:M2_cost_coefficients -->
| feature | physics | OLS A (t) | OLS B1 (t) | OLS A+B1 (t) | ridge A+B1 | GBR importance (sd) |
|---|---|---|---|---|---|---|
| n_2q | 1.29e-03 | 3.73e-04 (11.8) | -4.77e-05 (-0.2) | 2.89e-04 (8.2) | 2.56e-04 | 5.95e-05 (1.2e-05) |
| n_1q | 7.30e-05 | 7.38e-06 (0.4) | 8.08e-05 (0.9) | 4.65e-05 (2.2) | 5.86e-05 | 2.91e-05 (4.0e-05) |
| n_qubits | 1.39e-03 | 8.69e-03 (17.0) | -5.57e-05 (-0.1) | 3.81e-03 (15.0) | 3.49e-03 | 2.89e-06 (1.6e-06) |
| depth_2q |  | -1.90e-04 (-6.2) | 1.68e-04 (1.0) | -1.40e-04 (-4.2) | -1.10e-04 | 4.13e-05 (2.2e-05) |
| support_size |  | 2.85e-06 (0.6) | 4.57e-03 (1.4) | -5.03e-06 (-0.9) | -4.99e-06 | 2.70e-06 (2.3e-06) |
| log2_support |  | -9.12e-03 (-16.2) | -1.71e-02 (-1.4) | -3.91e-03 (-13.6) | -3.57e-03 | 1.91e-06 (2.1e-06) |
| n_2q_offsupport |  | 4.97e-04 (24.7) | 9.81e-04 (4.1) | 6.19e-04 (30.3) | 6.27e-04 | 1.47e-03 (7.0e-04) |
<!-- /TABLE:M2_cost_coefficients -->

![Cost model calibration and coefficients](figures/fig_cost_model.png)

Figure 4. Learned cost model on the proxy data. Left, predicted F_H = exp(-y_hat) against actual F_H. Filled points are the out-of-fold cv5g predictions of the OLS model for family A in blue and family B1 in orange. Hollow squares are the B1 predictions of the OLS model trained on A only and hollow triangles those of the boosted model trained on A only. The dotted line is the identity. Right, the OLS coefficients on the pooled set multiplied by the standard deviation of each feature with 1 SE bars on the lower axis, and the permutation importance of the boosted model as diamonds on the upper axis. Data: Tables M1 and M2, `results/fig_cost_model.png`.

`[F]` In the left panel the hollow squares for the B1 circuits with actual F_H between 0.94 and 0.98 lie below the identity line, so the A-trained OLS model under-predicts their fidelity. The hollow triangles of the A-trained boosted model lie closer to the line on the same circuits. The filled B1 points of the grouped cross-validation lie on or near the line over the full range from 0.80 to 0.98.

### 4.5 What the data support

`[F]` Across families the transfer is one-directional. Trained on A, the boosted model predicts B1 with R^2 0.805 and MAE(F_H) 0.0083. The unfitted physics baseline gives R^2 0.785 and MAE(F_H) 0.0151 on the same 35 rows. Ridge reaches R^2 0.840 with MAE(F_H) 0.0150 and OLS reaches 0.560 with 0.0252. Fitting on A lowers the B1 error of the best model by 0.0067 in MAE(F_H), a factor 1.81 below the baseline. Trained on B1, no model predicts A. The best R^2 in that direction is 0.326 for the boosted model and the other three are negative. `[O]` Seven circuits under five pipelines are 35 rows spanning three support fractions and cannot pin down seven coefficients, which the OLS B1 column of Table M2 shows directly. The only coefficient with |t| above 2 on B1 is n_2q_offsupport at 4.1. `[O]` The one direction that works rests on 7 test circuits and does not establish generalisation.

`[F]` Within family A the models interpolate across circuit classes. On the grouped split the A rows score R^2 0.937 for OLS and 0.990 for the boosted model. Holding out a whole Trotter model is harder. The boosted model reaches R^2 0.751 on ladder and 0.843 on tfim and fails on xxz at -1.035, where ridge is the only model above zero at 0.541. `[F]` The xxz circuits have the largest mean n_2q of the three models, 60.7 against 37.3 for ladder and 31.0 for tfim, and 4 of the 180 xxz rows exceed the largest n_2q of the other two. `[O]` The cause of the failure on xxz is not identified.

`[F]` The physics baseline fails on A in every split. Its R^2 on the 540 A rows is -3.513 with MAE(F_H) 0.0430, against 0.785 and 0.0151 on B1. `[O]` The baseline charges the full p2 per two-qubit gate. On A, where 280 of 540 rows have full support, a fault displaces mass onto strings that already carry ideal weight and the Hellinger fidelity loses far less than p2 per gate. On B1, where the support is a few strings, nearly every fault leaves the support and the baseline is close to right.

`[F]` The dominant term in every fitted model is n_2q_offsupport. On the pooled set its OLS t statistic is 30.3, the largest in Table M2, and the next are n_qubits at 15.0 and log2_support at -13.6. Its permutation importance for the boosted model is 1.47e-3, and the second largest is n_2q at 5.95e-5, a factor 24.6 lower. In the right panel of Figure 4 its bar is the longest and its diamond is the only one away from zero. `[F]` The pooled OLS coefficients give a per-gate cost of n_2q that moves from 2.89e-4 at full support to 2.89e-4 + 6.19e-4 = 9.08e-4 at a one-string output, against the emulator value p2 = 1.29e-3.

`[O]` Verdict. What the data support across families is the physics baseline plus a support correction, not a learned model. The one quantity that transfers is the per-two-qubit-gate cost scaled by the fraction of the output space outside the ideal support. `[F]` The boosted model trained on A cuts the B1 error of the baseline by a factor 1.8 and OLS on the same features does worse than the baseline. `[O]` On these 35 rows the gain comes from the nonlinear fit and not from the feature set alone. `[F]` The gain does not survive the reverse direction. The grouped cross-validation ranks ridge above the boosted model on the B1 rows at 0.926 against 0.830 and the leave-one-model-out split on xxz ranks ridge first as well. The form these data support is y = a n_2q (1 - support_size / 2^n) + b n_2q + SPAM with two fitted parameters. The refit on emulator data will score that form beside the boosted model on held-out circuits, and the boosted model stays in the submission as the learned component only if it wins there.

### 4.6 Status and use

`[F]` All numbers in this section come from the local proxy with the published H2-2E parameters. The proxy has no shot noise, no leakage, no crosstalk and no duration-based dephasing. The emulator F_H will be measured at 1000 shots. `[O]` Shot noise adds a floor to y that none of the seven features carries, so the refit on emulator data will need either an intercept or a shot-count term, and the coefficients of Table M2 will change.

`[O]` The model has two uses in this submission. Before HQCs are spent it ranks the five pipelines of a circuit by predicted F_H from their compiled counts, so that only the pipeline the model prefers is run. The rank correlation between predicted and measured F_H across the pipelines of a circuit is the metric that matters for that use and will be reported once emulator rows exist `[PENDING: emulator]`. After the run it predicts the fidelity of any further circuit from its compiled counts and support size, which is what a user who has not yet run the circuit can supply. The support size is computed from the ideal distribution and is available for every circuit in this benchmark because the ideal outputs are stored, and it is not available for a circuit too large to simulate. A cost signal for a rewriting search is future work and is not claimed here.

### 4.7 Refit on Selene depolarising data

[F] The cost model of Sections 4.1 to 4.3 was refitted without code changes on the Selene depolarising runs of Section 3.6. [F] The Selene layer has 432 family A rows with n = 4, 6, 8 and 10 and 36 B1 rows from 12 circuits. [F] The proxy fit used 540 A rows with n up to 8 and 35 B1 rows from 7 circuits. [F] The target is the depolarised sampled F_H divided by the noiseless sampled F_H at the same seed. [F] On the 345 rows with a proxy value this ratio differs from the exact proxy F_H by 0.0022 in mean absolute value, and the raw sampled F_H differs by 0.0058. [O] The ratio is the closest available match to the exact fidelity that the proxy fit used.

[F] Under circuit-grouped cross-validation the refit matches the proxy fit, with pooled R^2 = 0.935 for OLS and 0.974 for GBR. [F] Training on A and testing on B1 gives R^2 = 0.859 for ridge and 0.848 for GBR. [F] The unfitted physics baseline drops on B1 from R^2 = 0.785 on the proxy to 0.216 on Selene. [F] Training on B1 and testing on A still fails, with R^2 = 0.327 for GBR and negative R^2 for all other models. [F] The largest OLS terms on A remain n_qubits, log2_support and n_2q_offsupport with t = 14.7, -14.9 and 15.9. [O] The Selene layer confirms the two proxy conclusions. Transfer runs from A to B1 only, and within a family the fitted models interpolate.

| model | split | R^2 proxy | R^2 Selene | MAE(F_H) proxy | MAE(F_H) Selene |
|---|---|---|---|---|---|
| physics | A to B1 | 0.785 | 0.216 | 0.0151 | 0.0201 |
| ols | A to B1 | 0.560 | 0.356 | 0.0252 | 0.0333 |
| ridge | A to B1 | 0.840 | 0.859 | 0.0150 | 0.0154 |
| gbr | A to B1 | 0.805 | 0.848 | 0.0083 | 0.0140 |
| physics | B1 to A | -3.513 | -3.760 | 0.0430 | 0.0464 |
| ols | B1 to A | -261.894 | -313.944 | 0.1971 | 0.6838 |
| ridge | B1 to A | -0.605 | -98.831 | 0.0259 | 0.2673 |
| gbr | B1 to A | 0.326 | 0.327 | 0.0184 | 0.0234 |
| physics | cv5g pooled | -2.739 | -2.773 | 0.0413 | 0.0444 |
| ols | cv5g pooled | 0.938 | 0.935 | 0.0051 | 0.0065 |
| ridge | cv5g pooled | 0.938 | 0.936 | 0.0052 | 0.0065 |
| gbr | cv5g pooled | 0.971 | 0.974 | 0.0017 | 0.0035 |

[F] Test rows: A to B1 35 proxy and 36 Selene, B1 to A 540 and 432, cv5g pooled 575 and 468. Source: `results/cost_model_selene.md`.

[F] The refit is reproduced by the three Selene cost-model rows of the script table in Section 5. `model/cost_model.py --prefix selene_` writes `results/cost_model_selene_metrics.csv` and `results/cost_model_selene_coefficients.csv` directly. A rerun on 8 October 2026 reproduced both files byte for byte.

## 5. Reproducibility

`[F]` Environment, confirmed with `pip show` on 7 October 2026 in the development container:

| Package | Version |
|---|---|
| Python | 3.13.16 |
| pytket | 2.18.4 |
| pytket-quantinuum | 0.59.3 |
| pyzx (PyPI) | 0.10.7 |
| Quantinuum pyzx fork (family B1 sources only, `third_party/pyzx-fork/`) | commit e695d6d7 |
| qiskit | 2.5.2 |
| pygridsynth | 2.0.0 |
| selene-sim | 0.3.4 |
| guppylang | 1.1.2 |
| hugr | 0.18.8 |
| numpy | 2.5.3 |
| pandas | 2.3.3 |
| scipy | 1.18.1 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| aqora | 0.35.1 |
| qnexus | 0.51.1 |
| marimo | 0.25.1 |

`[F]` Seeds. `numpy.random.default_rng(20261006)` generates the family A couplings (`bench/gen_trotter.py`, `SEED`) and the family B2 Haar targets (`bench/gen_haar_b2.py`, `SEED`), with `seed_transpiler=0` in the qiskit transpile call of B2. Each generator draws from one stream in a fixed order, so the instance set does not depend on the order of writing. `noise/run_proxy.py` uses `default_rng(0)` only to pick the circuits of its parser self-check. `selene/run_selene.py` seeds every Selene run with `sha256("<pipeline>/<file>/<tag>")[:4]` and stores the value in the column `seed`. `model/cost_model.py` uses seed 0 for the fold assignment and `random_state=0` for the gradient-boosting model.

`[F]` Scripts, all run from the repository root. Inputs and outputs are the paths each script reads and writes.

| Step | Command | Inputs | Outputs |
|---|---|---|---|
| Family A circuits | `python bench/gen_trotter.py` | none (seed 20261006) | `bench/family_A/*.qasm`, `*_meas.qasm`, `*.npy`, `manifest.csv` |
| Family B1 circuits | `python bench/build_family_B1.py` | `third_party/pyzx-fork/circuits/` | `bench/family_B1/*.qasm`, `manifest.csv` |
| Family B1x circuits | `python bench/build_family_B1x.py` (defaults `--min-qubits 13 --max-qubits 20 --max-gates 3000`) | `third_party/pyzx-fork/circuits/` | `bench/family_B1x/*.qasm`, `manifest.csv` |
| Family B2 circuits | `python bench/gen_haar_b2.py` | none (seed 20261006) | `bench/family_B2/*.qasm`, `*_target.npy`, `manifest.csv` |
| Family A compilation | `python pipelines/run_bench.py --workers 2` | `bench/family_A/` | `results/family_A_counts.csv`, `results/family_A_summary.csv`, `results/compiled/<pipeline>/*.qasm` |
| Family B1 compilation | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900` | `bench/family_B1/` | `results/family_B1_counts.csv`, `results/family_B1_summary.csv`, `results/compiled/<pipeline>/*.qasm` |
| hwb8 long run | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --files hwb8 --pipelines P1,P2 --prefix family_B1_hwb8_long --timeout 5400 --workers 2` | `bench/family_B1/hwb8.qasm` | `results/family_B1_hwb8_long_counts.csv`, `results/family_B1_hwb8_long_summary.csv`, `results/family_B1_hwb8_long_run.log` |
| Family B1x compilation, count-only | `python pipelines/run_bench_B.py --manifest bench/family_B1x/manifest.csv --prefix family_B1x --pipelines P0ref,P0,P2 --no-check` | `bench/family_B1x/` | `results/family_B1x_counts.csv`, `results/family_B1x_summary.csv`, `results/family_B1x_run.log`, `results/compiled/{P0ref,P0,P2}/<file>.qasm` |
| Family B2 compilation | `python pipelines/run_b2.py --workers 2` | `bench/family_B2/` | `results/family_B2_counts.csv` |
| Noise proxy, family A | `python noise/run_proxy.py --noise h22e --family A --workers 2` | `results/compiled/{P0ref,P0,P1,P2,P3}/`, `bench/family_A/*.npy` | `results/family_A_proxy_h22e.csv` |
| Noise proxy, family B1 | `python noise/run_proxy.py --noise h22e --family B1 --workers 2` | `results/compiled/{P0ref,P0,P1,P2,P3}/`, `bench/family_B1/manifest.csv` | `results/family_B1_proxy_h22e.csv` |
| Proxy figure | `python noise/run_proxy.py --figure-h22e` | the two proxy CSVs | `results/fig_proxy_h22e.{pdf,png}`, `results/proxy_h22e_fits.log` |
| Certificates | `python barrier/run_certificates.py` | `bench/family_B2/*.qasm`, `bench/family_B1/{barenco_tof_3,mod5_4,qft_4,tof_3}.qasm`, `results/family_B2_counts.csv`, `results/family_B1_counts.csv` | `results/certificates.csv`, `results/certificates.md` |
| Selene runs | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene.py --mode both --procs 2 --shots 2000` | `results/compiled/{P0,P1,P2}/`, `bench/family_A/*.npy`, `bench/family_B1/manifest.csv`, the two proxy CSVs | `results/selene_noiseless.csv`, `results/selene_depolarizing.csv`, `results/selene_run.log` |
| Selene summary | `python selene/make_summary.py` | the two Selene CSVs, `results/selene_calibration.txt`, `results/selene_recheck.txt` | `results/selene.md` |
| Cost model | `python model/cost_model.py` | `results/family_A_proxy_h22e.csv`, `results/family_B1_proxy_h22e.csv` | `results/cost_model_metrics.csv`, `results/cost_model_coefficients.csv`, `results/cost_model.md`, `results/fig_cost_model.{pdf,png}` |
| Selene cost-model inputs | `python model/build_selene_cost_inputs.py` | `results/selene_depolarizing_full.csv`, `results/family_A_counts.csv`, `results/family_B1_counts.csv` | `results/cost_model_selene_input_A.csv`, `results/cost_model_selene_input_B1.csv` |
| Selene cost-model refit | `python model/cost_model.py --family-a results/cost_model_selene_input_A.csv --family-b results/cost_model_selene_input_B1.csv --prefix selene_` | the two Selene input CSVs | `results/cost_model_selene_metrics.csv`, `results/cost_model_selene_coefficients.csv`, `results/cost_model_selene_fig.{pdf,png}`, `results/cost_model_selene_autoreport.md` |
| Selene cost-model summary | `python model/report_selene_cost.py` | the Selene and proxy metric and coefficient CSVs, the two Selene input CSVs, `results/selene_depolarizing_full.csv` | `results/cost_model_selene.md` |
| Tables and figures | `python report/make_tables.py` | `results/*.csv` | `report/tables/*.md`, `report/figures/*.png`, injected into the report |
| Emulator jobs | `python3 submit/syntax_check.py` and `python3 submit/run_emulator.py`, with platform, shots and options of each job recorded in `results/emulator_jobs.csv` | `results/compiled/<pipeline>/` | `results/emulator_jobs.csv`, `results/emulator_nexus_H2-Emulator.csv`, `results/emulator/<platform>/<pipeline>/<file>.json` |

`[F]` The Selene command clears every proxy variable because Selene streams its results over a local TCP socket that the container proxy intercepts (`results/selene.md`, section 1).

`[F]` Tests. Each file was run once with the versions above, on 7 October 2026 unless the table gives 8 October. Five files run as scripts. `selene/test_selene.py` and `submit/test_submit.py` run under pytest.

| File | Command | Result | Wall time |
|---|---|---|---|
| `bench/test_gen_trotter.py` | `python bench/test_gen_trotter.py` | 12 of 12 passed | 58 s |
| `noise/test_dm_sim.py` | `python noise/test_dm_sim.py` | 17 of 17 passed | 3 s |
| `barrier/test_certificate.py` | `python barrier/test_certificate.py` | 69 of 69 checks passed | 29 s (44 s in `results/verification_2026-10-07.md`) |
| `pipelines/test_compile.py` | `python pipelines/test_compile.py` | 6 of 6 passed | 2 s |
| `selene/test_selene.py` | proxy variables cleared, `python -m pytest selene/test_selene.py -q` | 6 of 6 passed (5 functions, one parametrised twice) | 7 s |
| `model/test_cost_model.py` | `python model/test_cost_model.py` | 7 of 7 passed, rerun 8 October after the `--prefix` change | under 1 s |
| `submit/test_submit.py` | `python -m pytest submit/test_submit.py -q` | 11 of 11 passed, 8 October, offline with no credentials | 4 s |

`[F]` The compile tests check every pipeline against the unitary of the input and check that the measured QASM encodes the implicit qubit permutation left by `allow_swaps=True`. The certificate tests reproduce the finite verifications of the barrier manuscript (the counts 24, 1536 and 18384). The Selene tests check the bit order of the returned array with a permuted measure map and check that a seed reproduces the counts. The cost-model tests check that OLS recovers a known law without noise and that the physics baseline is exact on its own law. The submit tests run offline. They check the native gate set, the HQC formula, the bit order of returned counts, F_H and TVD, the job ledger, the job plans, the credential detection and the rubric rendering.

`[F]` Checks recorded per row in every counts CSV: `check_kind` and `check_dev`, `dist_maxdiff` and `qasm_dist_maxdiff`, `check_ok` and `status`, `pyzx_angle_err`, and the timings `t_zx`, `t_tket` and `t_total`. `[F]` The flag `--no-check` of `pipelines/run_bench_B.py` skips the unitary, statevector and distribution checks and keeps the gate-set check. Under it `check_kind` is `none`, the check columns are NaN and `status` is `ok-unchecked` for a native circuit and `FLAGGED-unchecked` otherwise. Family B1x is the only family compiled under it, and all 24 of its rows are `ok-unchecked` with a total wall time of 36.8 s.

`[F]` Timeouts. `pipelines/run_bench.py` and `pipelines/run_bench_B.py` default to 600 s per (circuit, pipeline) and `pipelines/run_b2.py` to 900 s. The family B1 run used 900 s, under which hwb8 timed out under P1 and P2, so the first `results/family_B1_counts.csv` carried `status = timeout` on those two rows (103 of 105 rows `ok`). A rerun with `--timeout 5400` on P1 and P2 only started on 7 October at 21:37 and completed both. P1 finished in 885.6 s wall with 8305 ZZPhase gates and P2 in 843.8 s wall with 5587 ZZPhase gates. Both rows have `status = ok` with `check_dev` at most 1.7e-13 and a T-count after the ZX stage of 3517 (`results/family_B1_hwb8_long_run.log`, `results/family_B1_hwb8_long_counts.csv`). `[F]` The two rows replaced the timeout rows in `results/family_B1_counts.csv`, `results/family_B1_summary.csv` was regenerated with `summarise` from `pipelines/run_bench_B.py` and `python report/make_tables.py` was rerun, so every table built from the main CSV shows hwb8 under all seven pipelines and all 105 rows are `ok`. The file before the merge is kept as `results/family_B1_counts_before_hwb8_merge.csv`. `[O]` Both wall times lie under the earlier 900 s limit, so the earlier timeouts came from two workers sharing the two cores with the other 13 circuits, not from the circuit itself.

`[F]` Verification. Two reports by agents that did not produce the results are in the repository. `results/verification_2026-10-07.md` recomputed the seven claims of `claude/status-2026-10-06.md` from the raw CSVs and QASM files. Six were confirmed and one mismatched: the status document said P2 beats P0 on 13 of 14 completed B1 circuits and the recomputation gives 12 of 14 with two ties. One figure was unverifiable, a 1064-gate SK word length that depends on an unstated approximation depth. `results/verification_2026-10-07b.md` recomputed six further claims (family A files and manifest, `family_A_counts.csv`, the H2-2E proxy CSVs and their no-intercept fits, four proxy rows rerun, `certificates.csv` against a direct recomputation, ten report table cells): all confirmed, none mismatched. That report also diagnosed the crash of the first hwb8 rerun, in which `--files hwb8` matched against `hwb8.qasm` selected zero jobs, and fixed `pipelines/run_bench_B.py` before the 5400 s run above was started.

## 6. Limitations

`[F]` ZX extraction worsens the ZZPhase count. On family A the pipelines P1, P3 and P4 are above P0 on 180 of 180 circuits, with ZZ ratios from 1.28 to 10.32 (P1), 1.31 to 7.91 (P3) and 1.44 to 10.36 (P4). On family B1 (`results/family_B1_counts.csv`) P1 is above P0 on 14 of 15, P3 on 14 of 15 and P4 on 15 of 15. Only teleport reduction, which does not extract, helps on H2.

`[F]` The Trotter family sits at its ZZPhase floor. Under P0 alone the ZZPhase count equals one gate per two-body term on 180 of 180 circuits, where `n_2q` equals `n_cx / 2` of the manifest. No pipeline has fewer ZZPhase gates than P0 on any family A circuit, 0 of 180 for each of P0ref, P0L1, P1, P2, P3 and P4. The family measures the cost of a rewrite instead of its benefit. `[O]` The Trotter family is the right control, because a Trotter circuit is what an H2 user runs most, and a method that damages it has to be caught.

`[F]` A single-qubit T gate is an Rz on H2, which is free in HQC and absent from the gate-noise model. The T-count layer of the ledger has no effect on any H2 number in this report. Its value is for a fault-tolerant target.

`[F]` The noise proxy is a density-matrix simulation with the published H2-2E default parameters (p1 = 7.3e-5, p2 = 1.29e-3, p_meas = (9e-4, 1.8e-3), p_init = 4e-5) and depolarising gate channels only. The published H2-2E model has in addition a spontaneous-emission branch that applies leakage half of the time, measurement and initialisation crosstalk, quadratic and linear dephasing during transport and idling, and a two-qubit fault probability that scales with the RZZ angle (`docs/platform_notes.md`, section 3.2). The proxy has none of these. The Selene cross-check in `results/selene.md` compares two depolarising models that share the same per-gate convention, so the agreement of 32 of 34 runs within two standard deviations for the like-for-like variant confirms the implementation of the proxy and its measure-map handling, not its fidelity to H2-2E. `[O]` On the family B1 circuits, whose ZZPhase angles are multiples of pi/2, the angle scaling changes little. The angles of family A are small, so the published scaling lowers the two-qubit fault probability below p2 and the proxy is pessimistic there.

`[F]` Nothing in this report has run on hardware. The 22 H2-Emulator rows of Section 3.7 and the six H2-2E rows of Section 3.7.1 are emulator runs. The 468 noiseless, the 68 depolarising and the 468 full depolarising Selene runs are local. They use the Quest statevector backend and do not contain the H2-2E noise model. The emulator cell of the notebook has not been executed. `[PENDING: emulator]`

`[F]` The cost model is fitted on proxy fidelities, not on emulator output. Held-out whole circuit classes within the pooled data give R^2 = 0.990 on family A rows and 0.830 on family B1 rows (gradient boosting, `cv5g`), which measures interpolation within the families. Across families the evidence is one direction: trained on family A the best model predicts the 7 family B1 circuits with R^2 = 0.805 against 0.785 for the unfitted physics baseline, and trained on the 35 family B1 rows no model predicts family A (best R^2 = 0.326). `[O]` Seven B1 circuits do not establish generalisation, and learned rewriting itself is not attempted in this submission.

`[F]` The certificate bounds the T-count of exact rewrites and is computed on the channel of size 4^n x 4^n. It is applied to family B2 at n = 2 and n = 3 and to four family B1 circuits at n = 5. On family B2 the floor is at least 99.28 % of the post-ZX T-count on every instance. On the four B1 circuits the floor is 25.0 % (barenco_tof_3), 25.0 % (mod5_4), 55.2 % (qft_4) and 26.7 % (tof_3) of the post-ZX T-count, so there the certificate leaves most of the remaining T-count unaccounted for. `[O]` The B1 floors are loose because those circuits are hand-written with many Clifford collapses, not synthesised words, and the manuscript's near-rigidity result covers synthesised words only. An approximate resynthesis to a new precision is outside the scope of the certificate.

`[F]` hwb8 under P1 and P2 completed only in the 5400 s run of Section 5 (P1 8305, P2 5587 ZZPhase gates), and those two rows are the ones in `results/family_B1_counts.csv` and Table B1. P2 is below P0 on hwb8 by 5.50 % (5912 to 5587) and P2 is below P0 on 13 of 15 family B1 circuits with two ties. `[F]` The 8 circuits of family B1x (Section 3.2.1) were compiled with `--no-check` and have no unitary, statevector or distribution check. Their counts are not evidence of exactness and are kept apart from the family B1 totals.

`[F]` The implementation of the per-step bookkeeping of Lemma mqval(b) of the barrier manuscript found that the "reduction fires exactly once" half of that lemma fails on the word T T (`barrier/NOTES.md`, section 8), and the floor of Corollary cert does not use that half.

`[F]` Table B2 has five circuits per row against 50 and 8 in the manuscript. The agreement of the means is a consistency check, not a statistical result.

## 7. Team and roles

| Name | Role |
|---|---|
| C.-F. Kam | `[TBD]` |
| A. Mahasinghe | `[TBD]` |
| D. De Silva | `[TBD]` |
| Karunarathne | `[TBD]` |
| F. Cadet | `[TBD]` |
| Bessafi | `[TBD]` |
| K. De Silva | `[TBD]` |

## References

1. C.-F. Kam et al., An Exactness Barrier for ZX-Calculus Optimization of Synthesized Clifford+T Circuits, arXiv:2608.22801. Source in `papers/barrier/main.tex`. `[F]` arXiv:2608.22801 resolves to this title with Kam as first author (`results/verification_2026-10-08b.md`, claim 15).
2. D. De Silva et al., Numerical Evaluation of ZX-Calculus Optimization for Solovay-Kitaev Quantum Circuit Synthesis, arXiv:2608.22810. Source in `papers/skzx/DeSilva-SK-ZX-QIP.tex`. `[O: the arXiv number is not in the repository, audit item A10]`
3. A. Kissinger and J. van de Wetering, Reducing the number of non-Clifford gates in quantum circuits, Phys. Rev. A 102, 022406 (2020), arXiv:1903.10477. Table 1 checked on 7 October 2026 (results/literature_tcount_check.md).
4. Quantinuum, H2 Product Data Sheet, version 4.00, 17 September 2025, https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf.
5. Quantinuum, H2 emulators (H2-2E default noise parameters), https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/h2_emulators.html, and the emulator noise model page, https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/noise_model.html.
6. Quantinuum, Helios costing (HQC formula, equation 1), https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html. `[O: the H2 form of the formula is inferred from this page, docs/platform_notes.md section 3.4]`
7. Quantinuum, Singapore Grand Challenge code samples, https://github.com/Quantinuum/sg_grand_challenge.
8. Quantinuum, Selene emulation framework, https://docs.quantinuum.com/selene/ and https://github.com/quantinuum/selene.
9. pytket-quantinuum 0.59.3, `QuantinuumBackend.default_compilation_pass`, reproduced in `pipelines/compile.py:quantinuum_default_pass` with line references.
10. PyZX 0.10.7 and the Quantinuum pyzx fork, commit e695d6d7, for the family B1 sources.

## Changelog from v1

### Part 1

- A1 (HQC formula source): formula kept, now cited to equation (1) of the Helios costing page and to `src/python/pytket_cost_estimation.py` (`estimate_cost`) in `Quantinuum/sg_grand_challenge`, tagged `[F]` for the sample-code form. The "maxima over ten shots" collapse and the plan to run the H2-2SC syntax checker are a separate `[O]` paragraph.
- A2 ("three circuit families and five compilation pipelines"): replaced by "Seven compilation pipelines run on families A and B1 and five on family B2" in Section 1, and the same count added to Section 2.2.
- A3 ("at most 2.2e-16 x pi on family A"): replaced by the recomputed maximum of `pyzx_angle_err` over the 1260 rows of `results/family_A_counts.csv`, 1.48e-10 rad = 4.7e-11 x pi.
- A9 (remaining 20 %): scoring-map row now reads "The fourth criterion and the exact rubric wording are in the organisers' scoring brief (`sgc_scoring_brief.pdf`), not reproduced here."
- A10, A12 (arXiv numbers): arXiv:2608.22801 kept as given by the author. Theorem B, Corollary cert and Theorem C anchored to `papers/barrier/main.tex` lines 1813, 2568 and 2662 in Section 1 and Section 2.5. arXiv:2608.22810 does not occur in Sections 1 to 2.
- A13 (symbol clash): shot count renamed N_shots in Section 1, Section 2.3 and Section 2.6, so C is only a circuit.
- A14: the fidelity-metric paragraph of Section 2.3 split into an `[F]` definition (reported now for the proxy and Selene) and an `[O]` plan for the emulator.
- A15: Section 2.5 paragraph 3 retagged `[F]` and rewritten as a description of the computation performed (24 rows, floor <= T_zx on all 24, P1 and P2 equal T_zx).
- A16: p_meas defined at first use in Section 1 (9e-4 for a 0 outcome, 1.8e-3 for a 1 outcome, mean 1.35e-3) with p_init = 4e-5.
- A4 (within Part 1): `[PENDING: certificates]` removed from Section 2.5 and from the preamble. The Lemma mqval(b) paragraph is unchanged from v1.
- A19 (minor, within Part 1): "its T-count is the literature value" replaced by the manifest's "T-count as written", which the manifest supports.
- Section 1: new `[O]` paragraph on the fault-tolerant value of the floor (incompressible magic-state cost, Helios roadmap, finals' prize in credits).
- Section 2.6 rewritten to the current state: Selene noiseless (468 runs) and depolarising (68 runs) done locally with the route and the agreement count from `results/selene.md`, the density-matrix proxy at the H2-2E parameters (540 + 35 rows), and the Nexus-tier, H2-2E and H2-2SC runs pending credentials. The budget paragraph now carries the recomputed 13 of 14, 14 of 15 and 15 of 15 counts from `results/family_B1_counts.csv` (A8).
- Scoring map rows for technical performance and scientific merit now point at `results/selene.md` and `results/certificates.md`.

### Part 2

Changelog, part 2 (Section 3), 7 October 2026.

- A4: the two `[PENDING: certificates]` markers of 3.2 and 3.3 replaced by the certificate results, and a new 3.4 written with Table C1 (`<!-- TABLE:C1_certificates -->`, generated by `certificates()` in `report/make_tables.py` from `results/certificates.csv`). B2 configuration means 99.84, 99.79, 99.57, 99.76 %, minimum 99.28 %, floor <= T_zx on 24 of 24, mod5_4 floor 2 against T_zx 8 with 19 collapses, all recomputed. Manuscript comparison anchored at `papers/barrier/main.tex` lines 3066, 3076, 3079, 3108, 3118.
- A5: the provisional proxy paragraph of 3.1 removed. New 3.5 holds Table A4 (block moved from 3.1, content unchanged, already generated from `family_A_proxy_h22e.csv`), the new Table A5 (`<!-- TABLE:A5_proxy_b1 -->`, `family_b1_proxy()` from `results/family_B1_proxy_h22e.csv`), the B1 slope 1.18e-3 +/- 2.3e-5 (centred R^2 0.968) against p2 = 1.29e-3, the family A slope 5.14e-4 +/- 1.3e-5, the per-model slopes and the support term. The ordering P0 ~ P2 > P0ref > P1 ~ P3 requested for every cell does not hold in the data: P0ref is below P1 in the three xxz cells and below P3 in two of them, and at n = 4 over all models P1 = P3 = 0.9893 is above P0ref = 0.9867. The text states what the CSV gives.
- A6: "factors between 1.19 and 10.36" replaced by the per-pipeline ranges 1.28 to 10.32 (P1), 1.31 to 7.91 (P3), 1.44 to 10.36 (P4), and the mean ratio by n added.
- A7: citation added as instructed with the `[O: to be checked against the paper's table before submission]` marker. A web fetch of arXiv:1903.10477v3 on 7 October gave tof_3 15, mod5_4 8, vbe-adder_3 24 in the PyZX column and no grover_5 row. The arXiv title is "Reducing T-count with the ZX-calculus" and the DOI on the abstract page is 10.1103/PhysRevA.102.022406.
- A8: "P1 is above P0 on 13 of 14 completed, P3 on 14 of 15, P4 on 15 of 15" recomputed and stated in 3.2. The hwb8 long run (`results/family_B1_hwb8_long_counts.csv`, P1 8305, P2 5587, both ok) is reported in a separate paragraph with the note that it is not merged into `results/family_B1_counts.csv`.
- New 3.6 with Table S1 (`<!-- TABLE:S1_selene -->`, `selene()` from `results/selene_noiseless.csv` and `results/selene_depolarizing.csv`). New 3.7 placeholder.
- `report/make_tables.py`: three functions added (`family_b1_proxy`, `certificates`, `selene`), called from `main()`, with a console summary line each. INT_COLUMNS extended. `python report/make_tables.py --no-fig` run: 11 tables written, `report/report_v1.md` byte-identical before and after injection (checked with `cmp`).
- Recomputation commands run from the repository root: `python report/recompute_part2_check.py` (family A ratios and counts, proxy means per cell and per circuit, no-intercept fits and the support fit, B1 counts and T-counts, hwb8 long rows, certificate ratios and minima, Selene noiseless and depolarising summaries) and `python report/make_tables.py --no-fig`. The script prints every number quoted in this section and is kept in the repository.

### Part 3

- 2026-10-07. Section 4 rewritten from the v1 protocol to a trained-and-validated section on the proxy data. Added `cost_model_metrics()` and `cost_model_coefficients()` to `report/make_tables.py`, writing `report/tables/M1_cost_metrics.md` and `report/tables/M2_cost_coefficients.md` from the two CSVs and copying `results/fig_cost_model.png` to `report/figures/`. Marker injection now also runs on `report/v2/part*.md`. Existing tables unchanged, checked by checksum.
- Numbers recomputed from `results/cost_model_metrics.csv`, `results/cost_model_coefficients.csv` and the two proxy CSVs, not copied from `results/cost_model.md`.
- Discrepancy flagged: the docstring of `model/cost_model.py` says the seeds of one class have "identical gate counts and F_H within 3e-3". Recomputed on `results/family_A_proxy_h22e.csv`: n_2q and depth_2q are identical in all 270 class-pipeline groups, n_1q differs in 70 of them, support_size differs in 5, and the maximum F_H spread within a group is 0.0056. The text above uses the recomputed values.
- Unresolved: the v1 protocol named a rank-correlation metric across pipelines of a circuit as the figure of merit for pipeline choice. `model/cost_model.py` does not compute it. Left as `[PENDING: emulator]` in 4.6.
- Unresolved: the v1 protocol named a size-extrapolation split (train n <= 6, test n = 8). Not run. The leave-one-model-out split on xxz is the only extrapolation reported.

### Part 4

- Section 5: every version re-confirmed with `pip show` on 7 Oct (all match the brief). hugr 0.18.8 and scikit-learn 1.9.1 added because `selene/run_selene.py` and `model/cost_model.py` import them.
- Section 5: scripts table extended with the hwb8 long run, the two `run_proxy.py --noise h22e` family runs and the figure call, `barrier/run_certificates.py`, `selene/run_selene.py`, `selene/make_summary.py` and `model/cost_model.py`, each with inputs and outputs read from the script docstrings and `add_argument` calls.
- Section 5: test table with counts from one run of each file (12, 17, 69, 6, 6, 7). `selene/test_selene.py` is a pytest file, not a script.
- Section 5: hwb8 paragraph rewritten from `results/family_B1_hwb8_long_run.log` (completed, 886 s and 844 s under the 5400 s limit, not merged into the main CSV).
- Section 5: verification paragraph added for `results/verification_2026-10-07.md` and `_2026-10-07b.md`.
- Section 6, paragraph 1: audit item A8 fixed, "13 or 14 of the 15" replaced by the recomputed per-pipeline counts with the correct denominators (P1 13 of 14, P3 14 of 15, P4 15 of 15) and the hwb8 long-run count (P1 14 of 15).
- Section 6, proxy paragraph: audit item A5 fixed, "data-sheet parameters" and "being rerun" replaced by the H2-2E parameters now in `results/family_A_proxy_h22e.csv`. The omitted noise mechanisms are listed from `docs/platform_notes.md` section 3.2.
- Section 6: new paragraphs for the Selene local runs, the cost model, the loose B1 floors (25.0, 25.0, 55.2, 26.7 %), and the Lemma mqval(b) sentence moved here from Section 2.5 of v1.
- Section 6: the certificate application range corrected from "n <= 5" to "n = 2 and 3 (B2), n = 5 (B1)".
- References: items 3 to 8 added as instructed. arXiv numbers kept as given and flagged per audit item A10.
- Open: the hwb8 rows need merging into `results/family_B1_counts.csv` and `python report/make_tables.py` rerun before Table B1 and the Section 6 counts that depend on it are final.
### Integration of the four parts (7 October 2026)

- hwb8 rows under P1 and P2 from `results/family_B1_hwb8_long_counts.csv` merged into `results/family_B1_counts.csv` (old file kept as `results/family_B1_counts_before_hwb8_merge.csv`), `results/family_B1_summary.csv` regenerated with `summarise` from `pipelines/run_bench_B.py`, `python report/make_tables.py` rerun. Recomputed on the 15 circuits: P2 below P0 on 13, equal on 2, above on 0, mean P2 reduction 6.9 %; P1 above P0 on 14 of 15, P3 on 14 of 15, P4 on 15 of 15; hwb8 P2 reduction 5.5 %. Sections 2.4, 2.6, 3.2, 5 and 6 updated to these counts and the "not merged" sentences removed. The "Open" item of the Part 4 changelog is closed.
- Cross-references fixed: scoring map "Section 3.3" to "Section 3.4" for the certificates and the proxy tables listed as A4 and A5 with S1; Section 2.5 "Section 3.3 reports the rows" to "Section 3.4"; Section 2.6 "feed Table A4" to "feed Tables A4 and A5".
- Section 1: the finals' prize retagged `[F]` with the organisers' timeline email of 25 Aug 2026 as source, the roadmap inference kept `[O]`.
- Table A4 caption in `report/make_tables.py`: the semicolon inside the parameter parenthesis removed. Three sentences in Sections 5 and 6 with more than two commas or a one-clause beat rewritten without number changes.
- `report/make_tables.py` now injects into `report/report_v2.md` as well.

## Changelog v2 to v3

- Section 3.6 rewritten with the full Selene depolarising run (468 runs, Table S2). Section 4.7 added: cost model refit on Selene data (results/cost_model_selene.md).

- 8 October 2026. `report/report_v3.md` copied from `report/report_v2.md`, which is left unchanged (md5 7fa05ebc2da26bcd084c2f9310ca52d2 before and after this edit and after the table injection). `REPORT_V3` added to the injector list of `report/make_tables.py`.
- Family B1x added. Section 2.1 gains one paragraph listing the 8 circuits with n (rc_adder_6 14, csla_mux_3 15, gf2_pow_5_mult 15, ham15-low 17, ham15-med 17, gf2_pow_6_mult 18, barenco_tof_10 19, tof_10 19) from `bench/family_B1x/manifest.csv`, the selection window of `bench/build_family_B1x.py` (13 <= n <= 20, at most 3000 gates after expansion) and the count-only status. Section 1 and Section 2.2 state the three pipelines run on B1x. Section 2.4 states that the 24 B1x rows carry no check.
- New Section 3.2.1 with Table B1x (`<!-- TABLE:B1x_per_circuit -->`, generated by `family_b1x()` in `report/make_tables.py` from `results/family_B1x_counts.csv`). Columns: file, n, ZZ P0ref, ZZ P0, ZZ P2, P2 vs P0 %, depth_2q P0, depth_2q P2, T written, T after ZX P2. The function asserts `native` and `status == ok-unchecked` on every row.
- Every B1x number in Sections 1, 2.1, 3.2.1, 5 and 6 recomputed by `python report/recompute_b1x_check.py` from `results/family_B1x_counts.csv`, `results/family_B1x_summary.csv` and `bench/family_B1x/manifest.csv`: 24 rows, 8 circuits, pipelines P0ref, P0, P2, status `ok-unchecked` on 24 of 24, check columns NaN on 24 of 24, n from 14 to 19, P2 below P0 on 5, equal on 3 (csla_mux_3, gf2_pow_5_mult, gf2_pow_6_mult), above on 0, aggregate ZZ P0ref 1603, P0 1329, P2 1256, P2 vs P0 5.5 %, P0 vs P0ref 17.1 %, mean per-circuit P2 reduction 4.1 %, largest ham15-med 427 to 379 (11.2 %), P0 below P0ref on 8 of 8, depth_2q P2 below P0 on 5 and above on 3, P0ref ZZ equal to CX as written on 6 of 8 (rc_adder_6 93 to 88, csla_mux_3 80 to 76, and `RemoveRedundancies` alone gives 91 and 72), T written 1652 against T after ZX 854, `n_non_cliffordT_zx` 0 on every row, total `t_wall` 36.8 s, summary CSV n_2q columns equal to the counts pivot.
- Section 5: scripts table gains the rows `python bench/build_family_B1x.py` and the count-only compilation command with `--no-check`, and the Checks paragraph gains the definition of `--no-check` from the docstring and `run_one` of `pipelines/run_bench_B.py`. The worker count of the B1x run is not recorded in `results/family_B1x_run.log`, so the command is given without `--workers`.
- Section 6: one sentence on B1x being unchecked, appended to the hwb8 paragraph.
- Combined statement (Section 1, Section 3.2.1): checked family B1, 15 circuits, P2 below P0 on 13 and equal on 2. Count-only family B1x, 8 circuits, below on 5 and equal on 3. The two totals are never merged.
- Scoring map: the technical-performance row now names table B1x.
- `python report/make_tables.py` run after the edits: table block injected into `report/report_v3.md`, `report/report_v2.md` byte-identical before and after (md5 above).

## Changelog v3 to v4

- 8 October 2026. `report/report_v4.md` copied from `report/report_v3.md`, which is left unchanged. Its md5 is eb2bac44de481063e694d0a82e83ea54 before and after the table injection. `REPORT_V4` added to the injector list of `report/make_tables.py`.
- Section 3.7 rewritten from the H2-2SC syntax check, the H2-Emulator jobs and the quota event. New Table E1 (`<!-- TABLE:E1_h2emulator -->`) generated by `emulator_h2e()` in `report/make_tables.py` from `results/emulator_nexus_H2-Emulator.csv`, the counts in `results/emulator/nexus_H2-Emulator/`, the two proxy CSVs and `results/selene_depolarizing_full.csv`. The function recomputes F_H from the counts and gives the bootstrap sd of F_H per row with 4000 resamples and seed 20261008. It also returns the proxy and Selene comparisons and the P2 against P0 differences quoted in the text. New Section 3.7.1 is the `[PENDING: H2-2E]` placeholder.
- Scoring map. The fourth row now reads Engineering & Reproducibility with weight 20 % from `docs/rubric.md`, which replaces the reference to `sgc_scoring_brief.pdf`. The criterion names follow the rubric. The weights 30, 30, 20 and 20 % were already those of the rubric. The technical row names Tables S2 and E1 and Section 3.7.
- Section 2.3 states that F_H and TVD are reported for the H2-Emulator output. Section 2.6 counts the 468 full depolarising Selene runs of Section 3.6 and Table S2 and replaces the paragraph that said no job had been submitted. Section 3.2 changes its marker to `[PENDING: H2-2E]`. The preamble no longer says the credentials are missing.
- Section 4.7 gains the refit command note. `model/cost_model.py` gains `--prefix` with the empty default, which keeps the original output names. A default run into a scratch directory reproduced `results/cost_model_metrics.csv` and `results/cost_model_coefficients.csv` byte for byte. `--prefix selene_` reproduced `results/cost_model_selene_metrics.csv`, `results/cost_model_selene_coefficients.csv` and `results/cost_model_selene_fig.png` byte for byte. The regenerated `results/cost_model_selene_fig.pdf` differed only in its CreationDate and the committed file was kept. The run also wrote `results/cost_model_selene_autoreport.md`. `model/report_selene_cost.py` now prints the three commands and an updated note into `results/cost_model_selene.md`, which was regenerated with no other change. `model/test_cost_model.py` passed 7 of 7 after the change.
- Section 5. The script table gains the three Selene cost-model rows and the emulator-job row names `submit/syntax_check.py`, `submit/run_emulator.py` and their outputs. The test table gains `submit/test_submit.py` with 11 of 11 passed under pytest. The sentence on test runners now reads five script files and two pytest files.
- `README.md` points to `report/report_v4.md`, lists the five script tests and the two pytest tests and describes the injection into v1 to v4.

## Changelog v4 to v5

- [F] Section 1 rewritten from `report/sec1_v5.md`. It states the user and the decision, HQC saved per application area (`value/value_by_application.md`), magic states saved and the certified incompressible fraction, and an application map of the benchmark circuits (`docs/applications.md`). The H2-2SC paragraph and the pipeline-scope paragraph moved out of Section 1.
- [F] 8 October 2026. `report/report_v5.md` copied from `report/report_v4.md`. `REPORT_V5` added to the injector list of `report/make_tables.py`. The header now reads draft v5.
- [F] Section 3.7.1 rewritten from the six H2-2E jobs. New Table E2 (`<!-- TABLE:E2_h22e -->`) generated by `emulator_h22e()` in `report/make_tables.py` from `submit/h22e_stats.py`. The script reads `results/emulator_nexus_H2-2E.csv`, the counts in `results/emulator/nexus_H2-2E/`, the ledger, `results/family_B1_proxy_h22e.csv` and `results/selene_depolarizing_full.csv`. It recomputes F_H from the counts and gives the binomial sd on the single-outcome circuits and the bootstrap sd on grover_5 with 4000 resamples and seed 20261008. It also gives the paired differences, the predicted gains from the refitted slope a = 1.1801e-3, the shots for a 2-sd resolution and the HQC total of 1840.0. The scratch copy `results/h22e_stats.py` was removed.
- [F] `submit/test_h22e_stats.py` added. It checks the F_H recomputation, the sd rule, the HQC total and the slope.
- [F] `[PENDING: H2-2E]` markers removed from the Tags paragraph and from Sections 2.3, 2.6 and 3.2. The scoring map technical row names H2-2E table E2 and Section 3.7.1. The Section 6 sentence that said nothing had run on the H2-2E emulator now says nothing has run on hardware.
- [F] The requested conclusion that the H2-2E rows agree with the proxy within sampling error holds on hwb6 under P2 only. Under P0 the emulator lies 3.88 sd above the proxy. Section 3.7.1 states this.
- [F] `value/value_ledger.py` and `value/value_by_application.py` added with `value/test_value_ledger.py` and `value/test_value_by_application.py`. Their outputs feed Section 1. The scoring map lists `value/` among the test directories.
- [F] Fixes F1 to F12 of `results/verification_2026-10-08b.md` applied to Sections 1, 3.7.1 and 6, the scoring map and this changelog. Section 1 stays identical to `report/sec1_v5.md`.
- [F] `value/value_by_application.py` gains `shots_affordable_capped()` and a second shots table with at most 10,000 shots per job. Section 1.2 quotes both tables. `value/test_value_by_application.py` gains a brute-force test of the capped count.
- [F] `submit/h22e_stats.py` gains `h2emulator_sd()`, which reproduces the bootstrap stream of Table E1. The grover_5 cross-emulator z now uses the Table E1 sd and reads 4.33 in place of 4.29. `report/make_tables.py` asserts that this sd equals the Table E1 value and prefixes the Table E2 caption with `[F]`. `submit/test_h22e_stats.py` gains a test of the cross-emulator sd.
- [F] Reference 1 no longer carries the audit item A10 marker.
