# A certified resource ledger shows where ZX rewriting pays on Quantinuum H2

Team Learned ZX Rewriting. Quantinuum Singapore Grand Challenge, submission 1, draft v2 (7 October 2026).

Tags: `[F]` marks a statement verifiable from an artifact in the repository or from the cited source. `[O]` marks a judgement or a plan. Every number in a results table of Section 3 is produced by `report/make_tables.py` from `results/*.csv`. Items marked `[PENDING: emulator]` wait for the team's Aqora credentials and are not yet measured.

## Scoring map

`[O]` The table assigns the evidence for each criterion to a section of this report.

| Criterion | Weight | Where the evidence is |
|---|---|---|
| Problem and value | 30 % | Section 1, Section 6 |
| Technical performance and hardware use | 30 % | Section 3 (count tables A1 to B2 and the proxy table A4), Section 2.6 and `results/selene.md` for the Selene runs, Section 5, notebook `report/notebook_skeleton.py` |
| Scientific merit | 20 % | Section 2.5 (certificate), Section 3.3 and `results/certificates.md`, the two manuscripts in `papers/` |
| Fourth criterion | 20 % | The fourth criterion and the exact rubric wording are in the organisers' scoring brief (`sgc_scoring_brief.pdf`), not reproduced here. Section 4 and Section 7 are the candidates. |

## 1. Problem and value

`[F]` On Quantinuum H2 the price of a program is set by the HQC formula HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_M) / 5000. Here N_shots is the shot count and N_1q the PhasedX count. N_2q counts ZZPhase and ZZMax gates and N_M counts initialisations, measurements and resets. Rz gates are free and a two-qubit gate costs ten single-qubit gates. The first source is equation (1) of the Helios costing page, quoted in `docs/platform_notes.md` section 3.4. The second is the organisers' sample code `src/python/pytket_cost_estimation.py` in the `Quantinuum/sg_grand_challenge` repository, whose function `estimate_cost` implements exactly this formula for H2 targets. `pipelines/compile.py:hqc` reproduces that function.

`[O]` The Helios page writes the three counts as maxima over ten simulated shots, and for a static H2 circuit each maximum equals the gate count of the compiled circuit. The H2-2SC syntax checker returns the official HQC cost of a circuit at no charge (`docs/platform_notes.md`, section 3.4), and the team will run it on every compiled circuit once credentials are available.

`[F]` Two-qubit gates also carry the dominant error. The published H2-2E emulator parameters are p2 = 1.29e-3 per two-qubit gate and p1 = 7.3e-5 per single-qubit gate (`docs/platform_notes.md`, section 3.3). The readout flip rate p_meas is 9e-4 for a qubit read in state 0 and 1.8e-3 for a qubit read in state 1, with mean 1.35e-3, and the initialisation error is p_init = 4e-5.

`[O]` A compiler for H2 therefore has one number to minimise today, the ZZPhase count, and the HQC and the emulated fidelity both follow from it. ZX-calculus rewriting is advertised as a general circuit optimiser. The question a team using H2 needs answered before spending HQCs is whether it lowers the ZZPhase count below what pytket already achieves, on which circuits and by how much. We know of no published comparison with pytket's own Quantinuum pass as the baseline and the native gate set as the target.

`[O]` The second cost layer is invisible on H2. In a fault-tolerant machine a Clifford gate is cheap and a T gate is paid for with a distilled magic state, so the T-count becomes the resource. On H2 a single-qubit T gate compiles to an Rz, which is free in HQC and has no error entry in the noise model. A benchmark that scores only ZZPhase count will reward a rewrite that trades T gates for two-qubit gates and will punish the opposite trade, so the ledger needs both columns. The T column needs a floor as well, because a T-count reduction of a few percent is only meaningful once the maximum possible reduction is known.

`[F]` The team's manuscript on the exactness barrier gives that floor per instance (Kam, arXiv:2608.22801). The statements are in `papers/barrier/main.tex` at line 1813 (Theorem B), line 2568 (Corollary cert) and line 2662 (Theorem C). For any Clifford+T circuit the least denominator exponent of its exact Pauli-channel representation over Z[sqrt 2] is a lower bound on the T-count of every semantics-exact rewrite of it. The bound is computed by one exact channel multiplication per gate.

`[O]` The floor prices the fault-tolerant layer. It is the magic-state cost that no exact optimiser can remove from the instance, so a resource estimate built on it carries a provable lower bound instead of a best-effort number. Quantinuum's Helios roadmap targets fault tolerance and the finals' prize is credits on that programme, so the certified T column prices the layer those credits will be spent on.

`[O]` This submission delivers a resource-certification benchmark with two layers. The NISQ layer measures ZZPhase count, two-qubit depth, HQC and fidelity under the H2-2E noise parameters on three circuit families. Seven compilation pipelines run on families A and B1 and five on family B2. The fault-tolerant layer measures the T-count after ZX rewriting against the certified floor. The learned component is a cost model that predicts fidelity from compile-time features, trained on the noisy data available (Section 4). Learned rewriting itself is future work and is not claimed here.

`[O]` Value for Quantinuum users now: a reproducible answer to "should I run PyZX before pytket on H2", split by circuit family, with the HQC consequence stated. Value for the fault-tolerant programme later: a per-instance certificate that separates the T-count a rewrite removed from the T-count no exact rewrite can remove.

## 2. Method

### 2.1 Circuit families

`[F]` Family A consists of 180 Trotter spin-chain circuits generated by `bench/gen_trotter.py`. Three models: the transverse-field Ising chain with open boundary, the XXZ chain started from the Neel state, and the transverse-field Ising ladder. Sizes n in {4, 6, 8, 10, 12}. Trotter steps r in {1, 2, 4} with dt = 0.1. Couplings are uniform (one instance per group) or drawn from [0.5, 1.5] with `numpy.random.default_rng(20261006)` (three instances per group). Every two-body Pauli exponential is written as a cx-rz-cx block with basis changes. The circuit as written therefore has n_cx = 2 x (number of ZZ-type terms). Ideal output distributions for n <= 10 are stored as `.npy` references.

`[F]` Family B1, 15 standard Clifford+T benchmark circuits with n <= 12 from the Quantinuum pyzx fork at commit e695d6d7 (`third_party/pyzx-fork/circuits/qasm`), built by `bench/build_family_B1.py`. Every Toffoli is expanded into the 7-T decomposition by pyzx so that the file as written is Clifford+T. The manifest `bench/family_B1/manifest.csv` records the source file, its commit and the counts before and after expansion, for example a T-count as written of 21 for tof_3 and 28 for mod5_4.

`[F]` Family B2 consists of 20 Clifford+T circuits synthesised from Haar-random unitaries by `bench/gen_haar_b2.py`. There are five targets at n = 2 and five at n = 3 drawn with the same seed. Each target is synthesised at eps = 1e-3 and at eps = 1e-5. The construction is qiskit `qs_decomposition` followed by `transpile` to the basis {rz, sx, x, cx} with `seed_transpiler=0`. Every rz angle that is not a multiple of pi/4 is then replaced by a pygridsynth (Ross-Selinger) approximation to precision eps. The operator-norm error of each written circuit against its target is stored in the manifest, with the triangle-inequality bound n_rz x eps. This family reproduces the construction of Table E6 in the barrier manuscript.

### 2.2 Pipelines

`[F]` All pipelines are in `pipelines/compile.py` and target the H2 gate set {Rz, PhasedX, ZZPhase, ZZMax, Measure, Reset} with all-to-all connectivity. Seven pipelines run on families A and B1 and five (P0ref, P0, P1, P2, P3) on family B2.

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

`[O]` The same two metrics will be reported for the H2-2E emulator output once jobs run. `[PENDING: emulator]`

### 2.4 Exactness checks

`[F]` Every compiled circuit is checked against the P0ref compilation of the same input. The check is the unitary deviation 1 - |tr(U^dagger V)| / 2^n for n <= 8 and the statevector infidelity on |0...0> beyond, with tolerance 1e-8. Where a `.npy` reference exists, the maximum difference between the compiled output distribution and that reference is recorded as well. The measured QASM written for submission is re-simulated independently (`qasm_dist_maxdiff`). All 1260 family A rows and all 100 family B2 rows pass. In family B1, 103 of 105 rows pass. The remaining two are the hwb8 timeouts under P1 and P2 at 900 s, not failures.

`[F]` Family B2 is additionally checked against the Haar target it approximates. The largest deviation 1 - |tr(U_target^dagger U_compiled)| / 2^n over all 100 rows is 7.1e-6, within the gridsynth bound.

### 2.5 The certificate

`[F]` The barrier manuscript (arXiv:2608.22801) gives the floor in Theorem B(a), Corollary cert and Theorem C(c). The three statements are at lines 1813, 2568 and 2662 of `papers/barrier/main.tex`. Let C be an n-qubit Clifford+T circuit and let O be any optimiser that preserves its unitary exactly. Then the T-count of O(C) is at least lde(C^). Here C^ is the exact 4^n x 4^n Pauli-channel matrix of C with entries in Z[sqrt 2]. lde(C^) is the least e such that C^ = (P + Q sqrt 2) / sqrt 2^e with integer matrices P and Q. The fraction of T-count that any exact optimiser can remove is at most 1 - lde(C^) / t(C). The floor is computed from any word realising C, in one exact channel multiplication per gate, and does not depend on the word chosen.

`[F]` `barrier/certificate.py` implements the floor in exact integer arithmetic, with the single-qubit linkage procedure and the residue automaton of the manuscript as cross-checks. `barrier/test_certificate.py` reproduces the manuscript's finite verifications. These are the Clifford group order 24, the residue automaton with 24 states and 1536 transitions and the 18384 Matsumoto-Amano words with t <= 8. `barrier/NOTES.md` maps every implemented quantity to the line of the manuscript it comes from.

`[F]` The certificate was computed for the 20 family B2 circuits and for the four family B1 circuits at n = 5, where the 4^n x 4^n channel is small. The output per circuit is the floor, the T-count after the ZX stage of P1 and of P2 and the ratio floor / T_zx. The 24 rows are in `results/certificates.csv` and `results/certificates.md`. The invariant floor <= T_zx holds on all 24 rows, and P1 and P2 give the same T_zx on every row. Section 3.3 reports the rows.

`[F]` The manuscript is not re-derived here, with one exception that needs stating. While implementing the per-step bookkeeping of Lemma mqval(b), the implementation found that the "reduction fires exactly once" half of that lemma fails on the word T T (`barrier/NOTES.md`, section 8). The floor of Corollary cert does not use that half, and the manuscript's own text says nothing downstream depends on it. The correction is being made in the manuscript.

### 2.6 Hardware use

`[F]` Two emulator tiers exist (`docs/platform_notes.md`, section 3.1). `H2-Emulator` is hosted by Nexus and costed in seconds. `H2-2E` is a hardware-tier emulator costed in HQCs with the published H2-2E noise parameters. The syntax checker `H2-2SC` returns the HQC cost of a circuit without charge.

`[F]` Quantinuum's local emulator Selene (`selene-sim` 0.3.4 with `guppylang` 1.1.2) ran 468 noiseless runs and 68 depolarising runs on the team's container. The route reads `results/compiled/<pipeline>/<file>.qasm` with `pytket.qasm.circuit_from_qasm` and loads the circuit into a guppy program with `guppylang.guppy.load_pytket`. The program is built by `selene_sim.build` and run by `run_shots` on the Quest statevector backend at 2000 shots. `load_pytket` accepted the PhasedX, Rz, ZZPhase and Measure gates of every compiled circuit without rebase. The noiseless runs cover 144 family A circuits with n <= 10 and 12 family B1 circuits with n <= 10 under P0, P1 and P2. No run was flagged by the criterion TVD > 4 x sqrt(support / (2 pi N_shots)) and no shot landed outside the exact support. Scripts are in `selene/`, data in `results/selene_noiseless.csv` and `results/selene_depolarizing.csv`, and the summary in `results/selene.md`.

`[F]` The 68 depolarising runs use Selene's `DepolarizingErrorModel` at the H2-2E rates p_1q = 7.3e-5 and p_2q = 1.29e-3 on 17 circuits under P0 and P2, in two variants of 34 runs. The variant `gates_meas_init` adds p_meas = 1.35e-3 and p_init = 4e-5, where 1.35e-3 is the mean of the two H2-2E readout rates because Selene takes one symmetric rate. In that variant 32 of 34 runs agree with the local density-matrix proxy within two sampling standard deviations. The variant `gates_only` leaves readout and initialisation noiseless and is not the like-for-like comparison.

`[F]` The local proxy `noise/dm_sim.py` is a density-matrix simulator. It applies a depolarising channel after every PhasedX and ZZPhase gate and adds an asymmetric readout flip and an initialisation flip. The parameters are the published H2-2E values p1, p2, p_meas and p_init from `noise/h2_params.py:H2_2E_EMULATOR`. The emission, crosstalk, dephasing and angle-scaling entries of the H2-2E model are not modelled. `noise/run_proxy.py` produced `results/family_A_proxy_h22e.csv` (540 rows, 108 circuits x 5 pipelines) and `results/family_B1_proxy_h22e.csv` (35 rows, 7 circuits x 5 pipelines). Both files feed Table A4 and the cost model of Section 4.

`[F]` No job has been submitted to the Nexus-tier `H2-Emulator`, to `H2-2E` or to `H2-2SC`, because the team's Aqora credentials are not in the workspace. The submission path is `aqora.QPU(platform="nexus:H2-2E", as_entity=<team>)` with `options={"noisy_simulation": True}` and 1000 shots, from the compiled and measured QASM files in `results/compiled/<pipeline>/`. `[PENDING: emulator]`

`[O]` The planned emulator budget is one job per (circuit, pipeline) on family A for n <= 8 and family B1 for n <= 9, on P0 and P2 only. The count tables of Section 3 show that P1, P3 and P4 are above P0 on ZZPhase count on every family A circuit and on 13 of 14, 14 of 15 and 15 of 15 family B1 circuits. Emulating them would spend HQCs to confirm a lower fidelity.

<!-- CHANGELOG part1 -->

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
