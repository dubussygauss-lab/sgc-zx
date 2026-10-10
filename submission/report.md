# PSEL4 compiles each H2 circuit four ways and keeps the cheapest

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi and K. De Silva. Quantinuum Singapore Grand Challenge, submission 1, judge-facing report. The full report v5 is attached as the technical appendix `report_full.pdf` and is cited below as "Appendix" with its section numbers.

`[F]` Tags. `[F]` marks a statement that can be checked against a file in the repository or a cited source. `[O]` marks a judgement or a plan. Every number in this report appears in the full report or in the script outputs it names under `value/` and `results/`. `report/check_short_numbers.py` checks this.

| Rubric criterion | Weight | Section here | Appendix |
|---|---|---|---|
| Problem & Value | 30 % | 1 | 1, 1.1 to 1.5, 3.8, 3.9 |
| Technical Performance & Hardware Use | 30 % | 3, 6 | 2.2, 3, 3.6, 3.7, 3.7.1, 3.8, 3.9, 6 |
| Scientific Merit | 20 % | 2.5, 4 | 2.5, 3.4 |
| Engineering & Reproducibility | 20 % | 5 | 5 |

## Summary

`[F]` PSEL4 is a drop-in replacement for pytket-quantinuum's default compile on Quantinuum H2. It compiles each circuit four ways and keeps the result with the lowest HQC. The four candidates are level 2 (pytket's default, P0), level 3 (L3), PyZX teleport_reduce before level 2 (P2) and teleport_reduce before level 3 (P2L3). Level 2 and level 3 are always candidates. PSEL4 therefore never costs more HQC than level 2 or level 3 on a circuit where both pass its checks. This holds by construction and is not a measured result.

`[F]` Against level 2 (pytket's default) PSEL4 saves 10.22 % HQC on the 17 arithmetic and oracle circuits of family C with 20 to 56 qubits whose output a PyZX miter proves equal to the input. On all 20 family C circuits it saves 25.85 %. This figure includes 3 picks without a proof. PSEL4 saves 10.65 % on the 15 B1 benchmarks, 2.88 % on the 180 Trotter circuits of family A and 33.36 % on the Grover use case (Table P4). `[F]` Most of this saving comes from choosing level 3 where it is cheaper. On top of the per-circuit best pytket level the ZX candidates add 0.26 % on the 17 proven family C circuits and 3.21 % on all 20. They add 0.49 % on B1, nothing on the Trotter circuits and 0.44 % on the use case (`value/psel4_zx_only.md`).

`[F]` Guard. Blind ZX rewriting raises HQC. Run on every circuit before level 2, the ZX stage costs 6.27 % more HQC on the 180 Trotter circuits and 22.1 % more on the 3 QFT adders of family C. pytket's own ZXGraphlikeOptimisation followed by level 2 costs 59.22 % more than level 2 on 14 B1 circuits. Qiskit level 3 rebased to H2 also costs more than level 2 on B1 and on family C (Table SB). PSEL4 never pays these losses.

`[F]` Correctness. Outputs up to 8 qubits are checked as full unitaries. From 9 to 20 qubits the check compares the output state on the all-zero input only. In the PSEL4 ledger runs the check of the level 3 candidates stopped at 12 qubits. A PyZX miter proves the PSEL4 output equal to its input on 17 of the 20 family C circuits of 20 to 56 qubits. Our P0 and P2 give the same counts as the official pytket-quantinuum pass on all 445 compiled rows of families A, B1, B1x and B2.

`[F]` Emulator. The submission holds 22 H2-2E jobs with valid counts. The input of the 22-qubit adder vbe_adder_7 was non-zero and was fixed and committed in advance. On it the adder returns the correct sum 139 in 0.883 of the shots under level 2. Under level 3, the PSEL4 pick, it does so in 0.901 of the shots. The difference has z = 1.30 and is not resolved at 1000 shots (Section 3.2).

`[O]` Learned ZX rewriting is the roadmap for the finals. `[F]` A first classifier on input-circuit features does not beat constant choices on held-out families (Section 4.4). `[O]` The finals model needs structural features.

`[F]` Limitations (Section 7). No user interview supports the need. The gain of the ZX candidates alone is small. Three family C picks have no proof. Two of them, hrs_mult_5 and draper_adder_28, give 87.6 % of the family C saving against level 3. On vbe_adder_3 the H2-2E fidelity gain of P2 over P0 has a pooled Holm-adjusted p of 0.052 over the three H2-2E circuits. A repeats-only test gives 0.030 over the two repeated circuits and was chosen after the pooled result. The earlier emulator inputs were all-zero. HQC is the formula estimate and nothing has run on H2 hardware. The T-count floor is the known bound of Gosset et al. evaluated on 24 circuits of at most 5 qubits. `[O]` The selector is the PassSelector pattern of pytket and not a new selection mechanism.

## 1. Problem and value

### 1.1 User, decision and tool

- `[O]` User. A team that runs Clifford+T subroutines on Quantinuum H2 from a fixed HQC budget and will later price the same subroutines on a fault-tolerant machine.
- `[O]` Decision. Should this circuit go through ZX rewriting before pytket's Quantinuum pass?
- `[F]` Tool. PSEL4 takes this decision per circuit. It compiles the circuit with all four candidates and keeps the result with the lowest HQC (`pipelines/pass_select.py --psel4`, `value/psel4_ledger.md`). An HQC tie goes to the lower two-qubit count n_2q. A remaining tie goes to the first of P0, L3, P2 and P2L3. A candidate that fails the exactness check is dropped. PSEL is the earlier two-candidate selector and keeps the cheaper of P0 and P2. In PSEL an HQC tie goes to the lower n_2q and a further tie to P0 (Appendix 2.2).
- `[F]` Guarantee. Level 2 (P0) and level 3 (L3) are always candidates of PSEL4. PSEL4 therefore costs no more HQC than level 2 or level 3 whenever both pass its checks. In the same way PSEL costs no more HQC than P0 whenever P0 passes its checks. This holds by construction and is not a measured result. The exactness check runs up to 20 qubits only. In the PSEL4 ledger runs the check of the level 3 candidates stopped at 12 qubits. All 20 family C PSEL4 outputs therefore rest on separate PyZX miter proofs. These prove the PSEL4 output equal to its input on 17 of the 20 family C circuits and the PSEL pick on 18 of them (Appendix Section 3.8).
- `[F]` Need for a selector. Running P2 on every circuit is not safe. On the 180 Trotter circuits of family A P2 alone would cost 1,030.4 HQC or 6.27 % more than P0. On the 60 XXZ circuits it would raise the total by 12.33 %. The earlier two-candidate selector PSEL keeps P0 on all 60 of them.
- `[F]` User validation. No user interview or survey is part of this submission. `[O]` The need rests on the H2 cost formula and on the algorithm literature cited in Appendix 1.4.

### 1.2 Savings by application on H2

`[F]` The PSEL4 savings by family are in Table P4 (Section 3.4). Table 1 shows the earlier two-candidate selector against level 2. Table 1b shows its ZX stage P2 against level 2.

`[F]` Table 1. Earlier two-candidate selector against level 2. HQC at 1000 shots of P0 (level 2, pytket's default) and PSEL. Family C is count-only above 20 qubits, apart from the H2-2E runs of vbe_adder_7 (Tables 3c and 3d), and is reported per application (`value/family_C_selector.md`, Appendix Table 1.1b). B1 is the checked Clifford+T benchmark set with n <= 12 (`value/selector_ledger.md`, Appendix Table 1.1a). The two multipliers and the three QFT adders carry continuous rotation angles. The row without continuous angles holds the 9 adders and the 6 MCX oracles.

| Application | Family | Circuits | Qubits | PSEL picks P2 | HQC P0 | HQC PSEL | Saved | Saved % |
|---|---|---|---|---|---|---|---|---|
| Adder | C | 9 | 20-56 | 9 | 5777.0 | 5031.4 | 745.6 | 12.9 |
| Grover oracle (MCX) | C | 6 | 21-56 | 3 | 4242.6 | 4239.8 | 2.8 | 0.1 |
| Family C without continuous angles | C | 15 | 20-56 | 12 | 10019.6 | 9271.2 | 748.4 | 7.47 |
| Multiplier, continuous angles | C | 2 | 21-24 | 2 | 9737.0 | 6381.0 | 3356.0 | 34.5 |
| QFT adder, continuous angles | C | 3 | 20-56 | 0 | 4778.4 | 4778.4 | 0.0 | 0.0 |
| All of family C | C | 20 | 20-56 | 14 | 24535.0 | 20430.6 | 4104.4 | 16.7 |
| Clifford+T benchmarks | B1 | 15 | 5-12 | 14 | 15,516.0 | 14,772.4 | 743.6 | 4.79 |

`[F]` Shots. On family C PSEL affords between 0 and 7,159 more shots per circuit with one 10,000 HQC budget per circuit. The H2 hardware guide limits a job to 10,000 shots and each job pays 5 HQC. On family C vbe_adder_7 gains the most. Shot gains belong to single circuits and are not summed.

`[F]` Table 1b. P2 against P0 on the checked B1 circuits by application area (Appendix Table 1.1, `value/value_by_application.md`). PSEL equals P2 on every B1 circuit except qft_4, where P2 costs 0.4 HQC more and PSEL keeps P0.

| Area | Circuits | HQC P0 | HQC P2 | Saved % | Median per-circuit % |
|---|---|---|---|---|---|
| Integer factoring (Shor) | 4 | 592.2 | 545.6 | 7.9 | 4.2 |
| Elliptic-curve discrete log | 1 | 216.2 | 215.2 | 0.5 | 0.5 |
| Unstructured search (Grover) | 8 | 1,183.6 | 1,127.0 | 4.8 | 3.0 |
| Reversible logic, no sourced algorithm | 2 | 13,524.0 | 12,885.0 | 4.7 | 4.5 |

- `[F]` Multipliers. rgqft_mult_6 drops from 4445.6 to 2206.6 HQC, a saving of 50.4 %. Its two-qubit count falls from 1994 to 990. Both multipliers carry continuous rotation angles and supply 3356.0 of the 4104.4 HQC saved on family C.
- `[F]` Adders. PSEL picks P2 on all 9 adders. The three VBE adders save 20.5 %, 20.9 % and 23.6 %. The four CDKM adders save 10.2 % to 10.5 %.
- `[F]` Where ZX does not pay. On the three QFT adders P2 is dearer than P0 and PSEL keeps P0. On the MCX oracles the saving is 2.8 HQC in total. A fixed choice of P2 would cost 21487.8 HQC on family C against 20430.6 for PSEL. `[O]` These rows show the selector at work.
- `[F]` hwb8 caveat. On B1 the circuit hwb8 alone accounts for 84.5 % of the PSEL saving and serves no sourced quantum algorithm. Without hwb8 the B1 saving is 115.0 HQC. The median per-circuit saving on B1 is 3.94 %. `[O]` The median is the better guide for a single small circuit.

### 1.3 Use case: Grover search within the 10,000 HQC budget

`[F]` Two complete Grover searches with one marked item were built from Grover 1996 and the multi-controlled gate of Barenco et al. 1995 (`value/usecase.md`, Appendix 3.9 and Table U1). They are small enough for an exact check. Both pass it under P0 and P2 with a deviation of at most 2.7e-14 in magnitude.

| Instance | Qubits | Ideal success | HQC P0 | HQC PSEL | Saving % | Shots in 10,000 HQC, P0 | Shots, PSEL | Extra shots |
|---|---|---|---|---|---|---|---|---|
| grover_d5 | 7 | 0.999182 | 734.2 | 694.4 | 5.42 | 13699 | 14490 | 791 |
| grover_d6 | 9 | 0.996586 | 1629.4 | 1548.6 | 4.96 | 6153 | 6475 | 322 |

- `[F]` The shot counts respect the H2 limit of 10,000 shots per job and charge 5 HQC per job. PSEL buys 5.77 % more shots on grover_d5 and 5.23 % more on grover_d6.
- `[F]` The expected number of marked-item hits within the budget rises from 13687.8 to 14478.2 on grover_d5 at the ideal success probability.
- `[O]` A slope model fitted on B1 proxy data predicts a fidelity ratio of 1.0287 and 1.0583 in favour of PSEL as a model prediction. No platform job ran these instances.

### 1.4 Magic states on a fault-tolerant machine

- `[F]` Each T gate of a surface-code machine consumes one magic state (Litinski 2019). On H2 a T gate is a free Rz and changes no HQC.
- `[F]` On B1 the ZX stage removes 2,862 of 7,048 T gates of the written circuits, or 40.6 %. On family C the ZX stage removes 1110 T gates from the 9 adders and 30 from the 3 MCX oracles where PSEL picks P2. The two multipliers lose 1,408 more but keep 600 and 507 rotations outside the pi/4 grid, so T-count is not their non-Clifford cost. On the Grover instances the T-count falls from 448 to 210 and from 1008 to 436. `[O]` This T-count drop comes from Toffolis that the Barenco construction repeats on the same qubits. It is not a general ZX gain.

`[F]` Table 1c. T-count as written and after the ZX stage of P2 by application area (Appendix Table 1.2). Each saved T gate is one magic state.

| Area | Family | T written | T after ZX | Saved % |
|---|---|---|---|---|
| Integer factoring (Shor) | B1 | 307 | 199 | 35.2 |
| Elliptic-curve discrete log | B1 | 112 | 68 | 39.3 |
| Unstructured search (Grover) | B1 | 637 | 327 | 48.7 |
| Reversible logic, no sourced algorithm | B1 | 5,992 | 3,592 | 40.1 |
| All areas | B1 | 7,048 | 4,186 | 40.6 |
| All B1x circuits, count-only | B1x | 1,652 | 854 | 48.3 |

- `[F]` These savings are against the written circuits. Against six published optimisers our T-count after ZX equals the best ancilla-free value on 14 of 22 comparable circuits (Section 4).
- `[F]` Scope of the certificate. The certified floor covers only the 24 circuits of `results/certificates.csv`, all with n at most 5. It covers no circuit of family C and no Grover instance.
- `[F]` No conversion of magic states into Helios time or cost is made. Quantinuum has not published the factory and logical-cycle figures in any source we found.

### 1.5 Value in USD, finance use, guard and fault-tolerant effort map

- `[F]` Plan prices. Azure Quantum lists the Quantinuum H2 Standard Plan at USD 125,000 per month with 10,000 HQC and the Premium Plan at USD 175,000 per month with 17,000 HQC (Reference 10). The page was last updated on 2025-12-23. The implied plan-average price is USD 12.50 per HQC on Standard and USD 10.29 on Premium.
- `[O]` At these averages the family C saving of 748.4 HQC on the 15 circuits without continuous angles is worth about USD 7,700 to 9,400. The family A avoided loss of 1,076.4 HQC is worth about USD 11,100 to 13,500. Both figures count 1000 shots of each circuit once. They use the plan average and not a marginal price. They ignore the bundled eHQCs and the Azure infrastructure costs.
- `[F]` Finance users. In the derivative-pricing methods of Chakrabarti et al. both path-loading schemes and the payoff calculation need quantum arithmetic. Chakrabarti et al. state this in Appendix C and write that "the T-count dominates the computational requirements" (Reference 12). PSEL saves 12.9 % HQC on the 9 adders and 7.47 % on the 15 family C circuits without continuous angles. `[O]` These adders are the kind of arithmetic such circuits call. A claim that arithmetic dominates the cost of derivative pricing is Unverifiable.
- `[O]` Do-no-harm guard for pytket users. A pytket user can add a ZX stage in front of the Quantinuum pass without knowing whether it pays. `[F]` pytket 2.18.4 ships one such pass, `ZXGraphlikeOptimisation`. Its documentation warns that it "may increase the cost of the circuit" (Reference 9, pytket 2.18.5 documentation, same docstring in the installed 2.18.4). We measured the PyZX stage of P2 and not that pass. Added blindly, the P2 stage costs 6.27 % more HQC than P0 on the 180 Trotter circuits of family A and 22.1 % more on the three QFT adders of family C. On draper_adder_16 it costs 1,385.0 HQC against 906.8 or 52.7 % more. A PyZX miter proves its P0 and P2 outputs equal to its input (Appendix Section 3.8).
- `[F]` PSEL costs no more HQC than P0 whenever P0 passes PSEL's checks and still keeps the 4.79 % saving on B1 and the 7.47 % saving on family C without continuous angles. `[O]` A pytket user can try ZX rewriting on every circuit for the price of a second compilation.
- `[O]` Where not to spend fault-tolerant compiler effort. `[F]` On the 20 B2 circuits with gridsynth-synthesised rotations the ZX stage removes 2.0 % of the T gates. The certified floor shows that every Clifford+T circuit with the same unitary on the same qubits keeps at least 99.7 % of the pooled remaining T-count and on the worst single circuit, haar_n3_eps1e-03_s5, at least 2478 of its 2496 T gates. Further exact T optimisation can gain at most 0.3 % of the pooled count and 0.72 % on the worst instance. The floor bounds the T-count of every Clifford+T circuit that realises the same unitary up to global phase on the same n qubits with no ancilla and no measurement. It covers 24 circuits with n at most 5. T gates compile to Rz on H2 and the HQC formula charges no Rz gate. The certificate therefore addresses the fault-tolerant layer only.
- `[F]` Reiher et al. write of the rotations in their FeMoco simulation that "These rotations dominate the cost of the quantum simulation". Beverland et al. call non-Clifford rotations "among the most resource intensive operations". Ross and Selinger approximate a z-rotation with T-count 3 log2(1/eps) plus lower-order terms in the typical case (Reference 11). `[O]` The certificate tells a team that plans fault-tolerant chemistry or phase-estimation workloads per instance how much exact T optimisation of these rotations can still gain.

## 2. Method

### 2.1 Pipelines and selector

`[F]` All pipelines are in `pipelines/compile.py` and target the H2 gate set of Rz, PhasedX, ZZPhase, ZZMax, Measure and Reset with all-to-all connectivity (Appendix 2.2).

| Name | Stages |
|---|---|
| P0ref | Rebase to the native set with no optimisation. Reference for the exactness check. |
| P0 | pytket-quantinuum 0.59.3 default pass at optimisation level 2. The baseline. |
| P2 | PyZX teleport_reduce, then P0. |
| P1, P3, P4 | ZX extraction variants, then P0. Kept as controls. |
| PSEL | Selector over P0 and P2. Adds no compilation stage. |

![Family A ZZPhase ratio](figures/fig_A_zz_ratio.png)

`[F]` Figure 1. Family A. ZZPhase count of each pipeline divided by the P0 count on the same circuit, mean over the 36 circuits at each n with the min-max band shaded. Data: Appendix Table A2 and `results/family_A_counts.csv`.

`[F]` P1, P3 and P4 are above P0 in ZZPhase count on all 180 family A circuits. On B1 they are above P0 on 14, 14 and 15 of the 15 circuits. `[O]` Only teleport reduction keeps the circuit skeleton and helps on H2. PSEL therefore selects between P0 and P2 only.

`[F]` pytket documents `PassSelector`, which returns "the best circuit as selected by a given metric" from a list of passes (Reference 9). `pipelines/pass_select.py` does not call it. `[O]` PSEL is this PassSelector pattern applied to P0 and P2 with HQC as the metric. The contribution is the measured ledger and the guard result and not a new selection mechanism.

### 2.2 Official baseline check

`[F]` Our P0 reproduces the pass from the pytket-quantinuum source. `results/official_baseline.md` compares it with `QuantinuumBackend("H2-1").get_compiled_circuit(circ, optimisation_level=2)` built offline from the device list in the package. The two passes have the same stages in the same order. The one parameter difference is a set of classical op types that no benchmark input contains. On all 445 compiled rows of families A, B1, B1x and B2 the official pass gives the same n_2q, n_1q, two-qubit depth and HQC as our P0 and P2. The PSEL savings against the official P0 are therefore identical to ours. This holds on families A, B1, B1x and B2. Family C was not compiled with the official pass.

| Family | Official P0 rows identical | Official P2 rows identical | Exactness of official output |
|---|---|---|---|
| A | 180 of 180 | 180 of 180 | 180 and 180 checked, all ok |
| B1 | 15 of 15 | 14 of 14 | 15 and 14 checked, all ok |
| B1x | 8 of 8 | 8 of 8 | unchecked |
| B2 | 20 of 20 | 20 of 20 | 20 and 20 checked, all ok |
 The one missing row is hwb8 under the official P2, which timed out at 565 s.

### 2.3 HQC formula

`[F]` The organisers' sample code prices an H2 program as HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. N_1q counts PhasedX gates. N_2q counts ZZPhase and ZZMax gates. N_SPAM counts initialisations, measurements and resets. `estimate_cost` starts N_SPAM at the number of qubits and adds one per measurement and reset. A circuit with every qubit measured once has N_SPAM = 2n. Rz gates are free. `pipelines/compile.py:hqc` reproduces the function `estimate_cost` of `Quantinuum/sg_grand_challenge` (Appendix 1.2). All HQC figures are at 1000 shots unless a row states otherwise.

### 2.4 Exactness checks

- `[F]` Families A, B1 and B2. Every compiled circuit is checked against P0ref. The check is the unitary deviation for n <= 8 and the statevector infidelity beyond, with tolerance 1e-8. All 1260 family A rows, all 105 B1 rows and all 100 B2 rows pass (Appendix 2.4).
- `[F]` Family C. A PyZX miter reduction proves the PSEL output of every one of the 15 circuits without continuous angles equal to its input as a full unitary up to global phase (Appendix 2.4 and 3.8). The miter joins the compiled circuit to the adjoint of the input. After `full_reduce` only wires from input i to output i may remain as in the `verify_equality` test of PyZX. No ancilla is assumed to start in |0>. Compiled angles are snapped to a dyadic grid with a largest snap of 5.27e-12 half-turns. Over all 20 circuits the PSEL output is proven on 18. The compiled angles of hrs_mult_5 lie off the dyadic grid. It keeps only a check on 64 random basis inputs. The miter of the P0 pick of draper_adder_28 timed out after 300 s. PSEL itself runs no exactness check above 20 qubits. The proof is a separate offline run.
- `[F]` Continuous angles. The Draper adders and the two multipliers carry rotation angles off the pi/4 grid (`bench/family_C/manifest.csv`). PyZX rounds angles to fractions. On draper_adder_28 this changes the P2 input by at most 1.50e-06 rad per angle. PSEL keeps P0 on that circuit.
- `[F]` Family B1x has 8 circuits with 14 to 19 qubits and is count-only. Its rows carry no exactness check and are never merged with B1.

### 2.5 The certificate

`[F]` The per-instance floor is the channel-representation bound of Gosset, Kliuchnikov, Mosca and Russo (Reference 13). Corollary cert and Theorem C(c) of the exactness-barrier manuscript of Kam et al. restate it for n qubits and as a bound on the removable fraction (arXiv:2608.22801, Corollary 2 and Theorem 6(c) in the PDF). Let C be a Clifford+T circuit. Its exact Pauli channel is a 4^n x 4^n matrix over Z[sqrt 2]. The least denominator exponent of that matrix bounds from below the T-count of every rewrite that preserves C exactly. `[F]` Gosset et al. call this exponent the smallest denominator exponent and prove that it equals the T-count for one qubit (Reference 13, Theorem 1). For n qubits the bound follows in one step from their Proposition 1. It is not tight on every gate. The Toffoli gate has exponent 2 and T-count 7 (their Section 6). `barrier/certificate.py` computes it in exact integer arithmetic. `barrier/test_certificate.py` reproduces the finite checks of the manuscript with 69 of 69 checks passed (Appendix 2.5).

## 3. Results on Quantinuum platforms

`[F]` The Quantinuum tools used are Nexus through `aqora` on the H2-Emulator (3 jobs, 22 rows) and on H2-2E (22 jobs, 7202.4 HQC), the free H2-2SC syntax checker (2 completed jobs), Selene with circuits loaded by guppy `load_pytket` (468 noiseless, 68 depolarising and 468 full depolarising runs) and the official pytket-quantinuum pass (445 compiled rows, Appendix 2.2).

### 3.1 Count results by family

`[F]` Table 2. PSEL against P0 and P2 per family at 1000 shots (`value/selector_ledger.md`, `value/family_C_selector.md`, Appendix Tables 1.1a and 1.1b). The PSEL column never exceeds the P0 column. On family C the 15 circuits without continuous angles save 7.47 %.

| Family | Content | Circuits | Qubits | Check | Picks P2 | HQC P0 | HQC P2 | HQC PSEL | Saved vs P0 % |
|---|---|---|---|---|---|---|---|---|---|
| A | Trotter TFIM, XXZ, ladder | 180 | 4-12 | exact | 57 | 16,422.6 | 17,453.0 | 16,376.6 | 0.28 |
| B1 | Clifford+T benchmarks | 15 | 5-12 | exact | 14 | 15,516.0 | 14,772.8 | 14,772.4 | 4.79 |
| B1x | Clifford+T benchmarks | 8 | 14-19 | none | 7 | 3,288.8 | 3,141.0 | 3,141.0 | 4.49 |
| B2 | Synthesised Haar unitaries | 20 | 2-3 | exact | 0 | 730.0 | 731.6 | 730.0 | 0.00 |
| C | Arithmetic and oracles | 20 | 20-56 | proof on 18 | 14 | 24535.0 | 21487.8 | 20430.6 | 16.7 |

`[F]` Table 2b. Family C per circuit (`value/family_C_selector.md`, Appendix Section 3.8 and Table C3). Proof gives the PyZX miter verdict for the PSEL output against the input. hrs_mult_5 is inconclusive because its compiled angles lie off the dyadic grid. It passes the 64-input basis check.

| Circuit | Qubits | Application | HQC P0 | HQC PSEL | Pick | Saved % | n_2q P0 | n_2q PSEL | Proof |
|---|---|---|---|---|---|---|---|---|---|
| mcx_clean_11 | 21 | Grover oracle (MCX) | 180.8 | 180.8 | P0 | 0.0 | 59 | 59 | proven |
| mcx_b95_20 | 22 | Grover oracle (MCX) | 693.4 | 693.0 | P2 | 0.1 | 292 | 292 | proven |
| mcx_clean_20 | 39 | Grover oracle (MCX) | 339.2 | 339.2 | P0 | 0.0 | 113 | 113 | proven |
| mcx_clean_28 | 55 | Grover oracle (MCX) | 480.0 | 480.0 | P0 | 0.0 | 161 | 161 | proven |
| mcx_dirty_28 | 55 | Grover oracle (MCX) | 591.0 | 589.0 | P2 | 0.3 | 216 | 215 | proven |
| mcx_b95_54 | 56 | Grover oracle (MCX) | 1958.2 | 1957.8 | P2 | 0.0 | 836 | 836 | proven |
| draper_adder_10 | 20 | QFT adder | 370.4 | 370.4 | P0 | 0.0 | 145 | 145 | proven |
| draper_adder_16 | 32 | QFT adder | 906.8 | 906.8 | P0 | 0.0 | 376 | 376 | proven |
| draper_adder_28 | 56 | QFT adder | 3501.2 | 3501.2 | P0 | 0.0 | 1483 | 1483 | timeout |
| modadd_2n_10 | 20 | adder | 388.2 | 371.6 | P2 | 4.3 | 147 | 142 | proven |
| cdkm_adder_10 | 22 | adder | 371.6 | 333.8 | P2 | 10.2 | 141 | 121 | proven |
| vbe_adder_7 | 22 | adder | 370.4 | 294.4 | P2 | 20.5 | 142 | 107 | proven |
| cdkm_adder_15 | 32 | adder | 551.6 | 494.4 | P2 | 10.4 | 211 | 181 | proven |
| vbe_adder_11 | 34 | adder | 593.6 | 469.4 | P2 | 20.9 | 230 | 173 | proven |
| modadd_2n_20 | 40 | adder | 802.2 | 779.6 | P2 | 2.8 | 307 | 302 | proven |
| cdkm_adder_20 | 42 | adder | 731.6 | 655.8 | P2 | 10.4 | 281 | 241 | proven |
| vbe_adder_18 | 55 | adder | 984.2 | 751.6 | P2 | 23.6 | 384 | 279 | proven |
| cdkm_adder_27 | 56 | adder | 983.6 | 880.8 | P2 | 10.5 | 379 | 325 | proven |
| hrs_mult_5 | 21 | multiplier | 5291.4 | 4174.4 | P2 | 21.1 | 2335 | 1807 | inconclusive |
| rgqft_mult_6 | 24 | multiplier | 4445.6 | 2206.6 | P2 | 50.4 | 1994 | 990 | proven |

- `[F]` On family A PSEL avoids 1,076.4 HQC against always running P2 and still saves 46.0 HQC against P0. This avoided loss is what PSEL adds over P2 on Trotter circuits.
- `[F]` PSEL never raises n_2q against P0 on any of the 223 circuits of families A, B1, B1x and B2. On family C it lowers n_2q by 1884 in total.
- `[F]` Family A by model. PSEL picks P2 on 32 of the 60 TFIM circuits and saves 0.62 % against P0. On the 60 ladder circuits it picks P2 on 25 and saves 0.52 %. On the 60 XXZ circuits it keeps P0 throughout.

![Family B1 ZZPhase count](figures/fig_B1_zz.png)

`[F]` Figure 2. Family B1. ZZPhase count per circuit for P0ref, P0 and P2 on a log scale, ordered by qubit number and then by T-count. hwb8 is omitted. Data: Appendix Table B1.

- `[F]` The best single B1 circuit is vbe_adder_3. P2 cuts its ZZPhase count from 56 to 41, a reduction of 26.8 %. At a 10,000 HQC budget PSEL buys 28.5 % more shots of it.
- `[F]` Scalability. Family C reaches 56 qubits. Its largest circuit under P0 has 2335 two-qubit gates. The largest B1 circuit hwb8 took 815.7 s under P2 in the stored run. `[O]` The ZX stage is the time cost of PSEL. It runs once per circuit before any shot is paid.

### 3.2 H2-Emulator and H2-2E

`[F]` Access. The team reached the platforms on 8 October 2026 through `aqora` 0.35.1 as team `learned_zx_rewriting`. Every job is a row of `results/emulator_jobs.csv` with its job id (Appendix 3.7).

- `[F]` H2-Emulator. Three jobs with 22 circuit rows completed at 1000 shots with noise. At this shot count no P2 against P0 difference is resolved on a single circuit. A fourth job was rejected by the platform quota.
- `[F]` H2-2E. 18 jobs completed on 8 and 9 October for Tables 3a and 3b. Six ran vbe_adder_3, hwb6 and grover_5 under P0 and P2 at 1000 shots. Twelve repeated vbe_adder_3 and grover_5 three more times. Their HQC estimates sum to 5933.2 of the 10,000 HQC team quota, or 59.3 %. Two more jobs ran the 22-qubit family C adder vbe_adder_7 for Table 3c. Two more ran it on a non-zero input for Table 3d. All 22 jobs total 7202.4 HQC.

`[F]` Table 3a. Single H2-2E runs at 1000 shots, one job per row (Appendix Table E2). The HQC estimate is the formula value stored with each job.

| Circuit | Pipeline | n_2q | HQC estimate | F_H | sd F_H |
|---|---|---|---|---|---|
| vbe_adder_3 | P0 | 56 | 151.6 | 0.9540 | 0.0066 |
| vbe_adder_3 | P2 | 41 | 119.0 | 0.9590 | 0.0063 |
| hwb6 | P0 | 99 | 243.0 | 0.9240 | 0.0084 |
| hwb6 | P2 | 94 | 232.6 | 0.9090 | 0.0091 |
| grover_5 | P0 | 240 | 565.6 | 0.8652 | 0.0114 |
| grover_5 | P2 | 218 | 528.2 | 0.8728 | 0.0112 |

`[F]` All three single-run differences lie within two sd of zero. Their z values are +0.55, -1.21 and +0.48 in the row order above.

`[F]` Table 3b. Pooled H2-2E runs at 4000 shots per pipeline (Appendix Table E3). F_H is the Hellinger fidelity of the summed counts to the ideal distribution.

| Circuit | Pipeline | n_2q | Pooled F_H | sd | Per-run F_H range |
|---|---|---|---|---|---|
| vbe_adder_3 | P0 | 56 | 0.9520 | 0.0034 | 0.9470 to 0.9560 |
| vbe_adder_3 | P2 | 41 | 0.9628 | 0.0030 | 0.9590 to 0.9680 |
| grover_5 | P0 | 240 | 0.8704 | 0.0053 | 0.8482 to 0.8652 |
| grover_5 | P2 | 218 | 0.8711 | 0.0053 | 0.8400 to 0.8728 |

- `[F]` vbe_adder_3. F_H(P2) minus F_H(P0) is +0.0108 with sd 0.0045. The z is +2.38 and the two-sided p is 0.017.
- `[F]` Multiplicity. The two repeated circuits were chosen after the single runs. The pooled Holm-adjusted p is 0.035 over the two repeated circuits and 0.052 over all three H2-2E circuits. `[O]` The gain is significant before correction and after correction over two circuits. It is not significant at 0.05 after correction over all three.
- `[F]` grover_5. The difference is +0.0007 with sd 0.0075 and z = +0.10 and is not resolved. It lies 2.94 sd below the gain of 0.0229 predicted by the slope model.
- `[F]` No cell rejects homogeneity of its four runs at the 0.05 level.
- `[F]` Confirmatory test. The repeats r2 to r4 were submitted after the two circuits were chosen, so a test on them alone carries no selection on its own data. At 3000 shots per pipeline the vbe_adder_3 difference is +0.0127 with sd 0.0052, z = +2.44 and two-sided p = 0.015. The repeats-only Holm-adjusted p over the two repeated circuits is 0.030. grover_5 gives +0.0004 with z = +0.04. Every circuit ran on the all-zero input. The choice to report the repeats alone was made after the pooled result was known. `[O]` The vbe_adder_3 gain holds on data that did not select it.

`[F]` Table 3c. One family C circuit on H2-2E at 1000 shots per job, all-zero input (Appendix Section 3.7.2, Table E4). The ideal output is one basis state, so the sd of F_H is binomial.

| Circuit | Qubits | Pipeline | n_2q | HQC estimate | F_H | sd F_H |
|---|---|---|---|---|---|---|
| vbe_adder_7 | 22 | P0 | 142 | 370.4 | 0.886 | 0.0101 |
| vbe_adder_7 | 22 | P2 | 107 | 294.4 | 0.897 | 0.0096 |

- `[F]` The difference F_H(P2) minus F_H(P0) is +0.0110 with sd 0.0139 and z = 0.79. It is not resolved at 1000 shots. `[O]` The run shows that a 22-qubit PSEL output executes on a Quantinuum emulator.

`[F]` Table 3d. The same adder on the non-zero input a = 28, b = 111, fixed and committed before submission (Appendix Section 3.7.3, Table E5). Success probability is the share of shots that return the correct sum 139.

| Circuit | Qubits | Pipeline | n_2q | HQC estimate | Success probability | sd |
|---|---|---|---|---|---|---|
| vbe_adder_7 | 22 | P0 | 142 | 372.2 | 0.883 | 0.0102 |
| vbe_adder_7 | 22 | L3 | 79 | 232.2 | 0.901 | 0.0094 |

- `[F]` L3 is the PSEL4 pick. Its success probability is higher by 0.0180 with sd 0.0139 and z = 1.30, not resolved at 1000 shots. `[O]` The 22-qubit adder computes a non-zero sum correctly in most shots on a Quantinuum emulator.
- `[O]` The H2-2E runs confirm execution and HQC accounting on a Quantinuum emulator. They give one fidelity gain and one unmet prediction, and this report states both.

### 3.3 Selene

`[F]` Quantinuum's local emulator Selene ran every compiled circuit of families A and B1 with n <= 10 under P0, P1 and P2 (Appendix 3.6). In 468 noiseless runs no shot landed outside the exact support and no run was flagged. In 468 depolarising runs at the H2-2E rates the mean F_H over 156 circuits is 0.9716 for P0, 0.9459 for P1 and 0.9702 for P2. `[O]` The compiled files run on Quantinuum's own toolchain and reproduce the distributions the local checks computed. `[F]` Selene does not contain the full H2-2E noise model.

### 3.4 Stronger baselines

`[F]` Table SB. HQC at 1000 shots against further compilers (Appendix Section 3.8.1, `results/strong_baselines.md`). L2 is the official pass at level 2, the default and our P0. L3 is level 3. ZXG is ZXGraphlikeOptimisation followed by L2. QK3 is Qiskit at optimization level 3 rebased to H2 natives. PSEL3 keeps the cheaper of L3 and teleport_reduce followed by L3. A negative saved % means the compiler costs more.

| family (circuits) | L2 | L3 | ZXG | QK3 | PSEL | PSEL saved vs L2 (%) | PSEL saved vs L3 (%) | BEST = min(L2, L3, ZXG, QK3) | PSEL saved vs BEST (%) | PSEL3 saved vs L3 (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 (14, hwb8 excluded) | 2235.0 | 1928.6 | 3558.6 | 2799.2 | 2120.0 | 5.15 | -9.92 | 1894.8 | -11.89 | 3.49 |
| C (20) | 24535.0 | 18853.2 | 53115.6 | 30707.2 | 20430.6 | 16.73 | -8.37 | 18797.2 | -8.69 | 2.34 |

`[F]` The official pytket-quantinuum compilation at optimisation level 3 (L3) is a stronger baseline than level 2 (L2), the default level and our P0. Its total HQC is 13.71 % below L2 on B1 and 23.16 % below L2 on family C. PSEL beats L2 but loses to L3 in total, with saved -9.92 % on B1 and -8.37 % on family C. Among L2, L3, ZXG, QK3 and PSEL, PSEL alone gives the lowest HQC on 3 of 14 B1 circuits and 6 of 20 family C circuits. ZXGraphlikeOptimisation followed by L2 (ZXG) and Qiskit optimization level 3 rebased to H2 natives (QK3) both cost more than L2 in total on both families. Applying teleport_reduce before L3 and keeping the cheaper of the two (PSEL3) saves 3.49 % against L3 on B1 and 2.34 % against L3 on family C. hwb8 is left out of the B1 totals because its ZXG and P2L3 runs timed out at 180 s. Family C outputs are above 12 qubits and are not checked for exactness here. All B1 outputs pass the unitary or statevector check.

`[O]` The HQC savings stated elsewhere in this report are against L2. Against L3 the PSEL saving does not hold. The ZX stage still pays on top of L3, by 3.49 % and 2.34 %.

`[F]` Table P4. HQC at 1000 shots of the level-3-aware selector PSEL4 (`value/psel4_ledger.md`). Totals are over the circuits where L2 and L3 both passed.

| Family | Circuits | HQC L2 | HQC L3 | HQC PSEL4 | PSEL4 saved vs L2 (%) | PSEL4 saved vs L3 (%) | Picks P0 / L3 / P2 / P2L3 |
|---|---|---|---|---|---|---|---|
| A, Trotter | 180 | 16422.6 | 16231.2 | 15949.0 | 2.88 | 1.74 | 35 / 145 / 0 / 0 |
| B1 | 15 | 15516.0 | 13965.8 | 13863.4 | 10.65 | 0.73 | 0 / 10 / 2 / 3 |
| B1 without hwb8 | 14 | 2235.0 | 1928.6 | 1826.2 | 18.29 | 5.31 | 0 / 9 / 2 / 3 |
| C | 20 | 24535.0 | 18853.2 | 18193.2 | 25.85 | 3.50 | 5 / 8 / 4 / 3 |
| C without continuous angles | 15 | 10019.6 | 8922.4 | 8865.0 | 11.52 | 0.64 | 3 / 7 / 3 / 2 |
| Grover use case | 2 | 2363.6 | 1582.0 | 1575.0 | 33.36 | 0.44 | 0 / 0 / 0 / 2 |

`[F]` PSEL4 adds L3 and P2L3 (teleport_reduce followed by L3) to the candidates of PSEL and keeps the lowest HQC of P0, P2, L3 and P2L3 (`pipelines/pass_select.py --psel4`, `value/psel4_ledger.md`). By construction it costs no more than the cheaper of level 2 and level 3. The ledger confirms this on all 217 circuits where both compiled within the time limit. In these ledger runs exactness is checked up to 12 qubits. The selector itself checks up to 20 qubits. Family C outputs rest on the separate miter proofs. Against level 3 it saves 3.50 % on family C, 0.73 % on B1, 1.74 % on the Trotter circuits of family A and 0.44 % on the two Grover instances. Against the default level 2 it saves 25.85 %, 10.65 %, 2.88 % and 33.36 %. On family A PSEL4 never picks a ZX candidate, so its gain there comes from the choice between the two levels. A PyZX miter proves the PSEL4 output equal to its input on 17 of the 20 family C circuits (`results/family_C_equivalence_psel4.md`). hrs_mult_5 has off-grid angles and the miters of rgqft_mult_6 and draper_adder_28 timed out. On the 17 proven circuits PSEL4 saves 10.22 % against level 2 and 0.80 % against level 3. Of the 660.0 HQC saved against level 3 on all 20 circuits, 87.6 % comes from 2 unproven picks, hrs_mult_5 and draper_adder_28 (`value/psel4_proven.md`). `[O]` Most of the saving against level 2 comes from level 3 itself. On B1, family C and the use case the ZX stage supplies the part against level 3. On family A it supplies none.

## 4. Scientific contribution

### 4.1 The certificate on real circuits

`[F]` The certificate ran on 24 circuits. These are the 20 synthesised Haar circuits of B2 at n = 2 and 3 and the four B1 circuits at n = 5. The floor is at or below the T-count after ZX on all 24 rows. `[F]` The bound is that of Gosset et al. (Reference 13). `[O]` The contribution here is its exact evaluation on synthesised circuits with up to 4248 T gates and the measured gap to the PyZX output. The bound itself is not new.

- `[F]` Synthesised circuits. On B2 the floor is 99.28 % of the T-count after ZX on the worst circuit (2478 of 2496, rounded to two decimals). The pooled certified fraction is 0.997. Further exact T optimisation of these instances can gain at most 0.3 % of the pooled remaining T-count and at most 0.72 % on any one circuit. All four configuration means lie inside the range of 99.4 to 99.9 % stated in the manuscript.

`[F]` Table 4a. Certificate on family B2 by configuration, 5 circuits each (Appendix Table C1).

| n | eps | Mean T written | Mean floor / T after ZX % | Min floor / T after ZX % | Mean achieved by ZX % |
|---|---|---|---|---|---|
| 2 | 1e-03 | 638.4 | 99.84 | 99.67 | 2.19 |
| 2 | 1e-05 | 1048.4 | 99.79 | 99.42 | 2.29 |
| 3 | 1e-03 | 2571.6 | 99.57 | 99.28 | 3.14 |
| 3 | 1e-05 | 4220.8 | 99.76 | 99.59 | 1.27 |

- `[F]` Hand-written circuits. On barenco_tof_3, mod5_4, qft_4 and tof_3 the floor is 47 against 106 T gates after ZX, a fraction of 0.443.
- `[O]` For a user the certificate turns the question whether a better optimiser can help into a number. The answer is no on synthesised words and open on Toffoli networks.

### 4.2 Comparison with six published optimisers

`[F]` Table 4b. Excerpt of Appendix Table C2 for the four certified circuits. "Best ancilla-free" is the smallest T-count on the same qubits in six papers fetched from arXiv on 8 October 2026. These are Amy, Maslov and Mosca 2014, Amy and Mosca 2016, Nam et al. 2018, TODD 2018, Kissinger and van de Wetering 2020 and AlphaTensor-Quantum 2024.

| Circuit | T written | T after ZX | Best ancilla-free | Best with ancillas | Certified floor |
|---|---|---|---|---|---|
| barenco_tof_3 | 28 | 16 | 16 | 13 | 4 |
| mod5_4 | 28 | 8 | 7 | 16 | 2 |
| qft_4 | 69 | 67 | 67 | 53 | 37 |
| tof_3 | 21 | 15 | 15 | 13 | 4 |

- `[F]` On the 22 comparable circuits of B1 and B1x our T-count after ZX equals the best published ancilla-free value on 14. On four of the other eight TODD after PyZX is better. On the three Galois-field multipliers the best ancilla-free values in Table C2 come from AlphaTensor-Quantum. On hwb6 a T-par entry is better.
- `[F]` On the four certified circuits the published optimisers close 1 of the 59 gates between our count and the floor. The other 58 gates lie between the best published count and the floor.
- `[O]` What it shows. The floor is tight on synthesised circuits and loose on Toffoli networks. Published optimisers add one gate beyond PyZX on the certified circuits. What it does not show. The certificate cannot tell whether the 58 open gates are headroom for a better rewrite or slack in the bound. It covers no circuit with more than 5 qubits.
- `[F]` Novelty. None of the six papers of Appendix Section 3.4 compares ZX rewriting against pytket's Quantinuum pass on the native H2 gate set. `[O]` This submission pairs that comparison in HQC with the known per-instance lower bound of Gosset et al. on the T-count, evaluated on 24 circuits.

### 4.3 Related work

`[F]` ZX-calculus optimisation rests on the graph-theoretic simplification of Duncan et al. (Reference 14) and on the phase teleportation of Kissinger and van de Wetering (Reference 3), which our P2 stage runs as PyZX teleport_reduce. `[F]` Staudacher et al. (Reference 15) and Chen et al. (Reference 16) change the ZX simplification to lower the two-qubit gate count. `[F]` Nägele and Marquardt train a graph-neural-network agent whose reward is the drop in the number of ZX-diagram nodes (Reference 17). `[F]` Riu et al. train an agent on the total or the two-qubit gate count of Clifford+T circuits and compare it with ZX heuristics (Reference 18). `[F]` Quarl learns rewrite sequences that cut the total and CNOT gate counts on the Nam and IBM gate sets (Reference 19), and Kremer et al. apply reinforcement learning to Clifford synthesis and routing (Reference 20). `[F]` AlphaTensor-Quantum minimises the T-count and can use gadgets (Reference 4). `[O]` In the parts of these works that we read, none prices its output with the H2 HQC formula or runs the pytket-quantinuum pass as a baseline. `[O]` This submission adds no new rewriting method. It adds a measured HQC ledger on H2 against the official pytket-quantinuum pass at optimisation levels 2 and 3. `[F]` Every output of families A, B1 and B2 passes an exactness check and a PyZX miter proves 18 of the 20 family C picks equal to their inputs.

### 4.4 A learned gate for the selector

`[F]` `value/zx_classifier.py` trains logistic regression and boosted trees on features of the input circuit only (qubit, gate, CX, T and continuous-rotation counts, depth and densities, the PyZX spider count) to predict whether P2 is cheaper than P0 in HQC. The data are 245 circuits of families A, B1, B1x, B2, C and the use case. The family label is not a feature. Evaluation holds out a whole family or uses grouped 5-fold cross-validation over 38 construction groups (`value/zx_classifier.md`).

| split (pooled, held out) | policy | balanced accuracy | regret (HQC) | gated regret (HQC) | P2 compilations skipped |
|---|---|---|---|---|---|
| leave one family out | always P0 | 0.500 | 5162.4 | 5162.4 | 245 |
| leave one family out | always P2 | 0.500 | 2135.6 | 0.0 | 0 |
| leave one family out | training majority | 0.396 | 6192.8 | 5116.4 | 65 |
| leave one family out | logistic regression | 0.433 | 2139.6 | 46.6 | 123 |
| leave one family out | boosted trees | 0.398 | 5420.2 | 3517.0 | 157 |
| grouped 5-fold | logistic regression | 0.749 | 3345.8 | 2244.8 | 109 |
| grouped 5-fold | boosted trees | 0.686 | 1237.8 | 139.0 | 137 |

`[F]` With a whole family held out, neither model beats the constant choices: pooled balanced accuracy is 0.433 for logistic regression and 0.398 for boosted trees against 0.500 for always P0 and always P2, and no model has lower regret than the better constant choice on any held-out family. `[F]` Under grouped 5-fold cross-validation over 38 construction groups, boosted trees reach a pooled regret of 1237.8 HQC against 2135.6 for always P2 and 5162.4 for always P0, but within each family their regret is never below the better constant choice. `[O]` The pooled gain therefore comes from telling family types apart from gate statistics, not from predicting which circuit inside a family benefits from ZX. `[F]` As a gate, the leave-one-family-out logistic regression skips 123 of 245 second compilations at a cost of 46.6 HQC (0.081 % of the oracle total). A random gate with the same number of skips in each family is the fair comparator. On family A the model is worse than that comparator. `[F]` On family A alone that gate costs 37.0 HQC against 27.6 HQC expected for a random gate with the same 108 skips. `[O]` The gate saves compile time cheaply because it skips circuits where the possible saving is small, and the two models disagree strongly, so this is a small honest learned component and not evidence that the benefit of ZX can be predicted.

## 5. Engineering and reproducibility

`[F]` Repository layout (Appendix 5 and `README.md`).

| Path | Content |
|---|---|
| `bench/` | Generators and builders of families A, B1, B1x, B2, C and the use case, with manifests |
| `pipelines/` | Pipelines, metrics, exactness checks, PSEL and the official baseline comparison |
| `barrier/` | Exact certificate with a line map to the manuscript in `barrier/NOTES.md` |
| `noise/`, `selene/`, `submit/` | Density-matrix proxy, Selene runs, platform jobs and their statistics |
| `value/` | Ledgers behind Sections 1, 3 and 6, each script with a test file |
| `results/` | Every CSV, log, compiled QASM file, job payload and verification report |

- `[F]` Tests. The test table of Appendix 5 lists 19 test files with their commands, results and dates. Examples are `pipelines/test_pass_select.py` with 3 of 3 passed and `value/test_selector_ledger.py` with 4 of 4 passed. Family C and the use case have their own test files `value/test_family_C_selector.py` and `value/test_usecase.py`. The family C proof has `pipelines/test_equiv_family_C.py` with 2 of 2 passed.
- `[F]` Generated numbers. Every results table of the full report is produced by `report/make_tables.py` from `results/*.csv`. The value tables are produced by the scripts under `value/` and carry no number typed by hand.
- `[F]` Clean-clone run. On 8 October the repository was cloned into a scratch directory and the pipeline was rerun with reduced variants of the long compilation steps (`results/repro_2026-10-08/repro_log.md`). The log reports no change in any count, T-count, HQC, fidelity or table cell. The run found two gaps. A fits log was ignored by git and the pyzx fork had no fetch command. `README.md` now gives the fetch command with the commit hash.
- `[F]` Independent verification. Twelve verification reports by agents that did not produce the results are in `results/verification_2026-10-0*.md`. Each recomputes claims from the raw files and lists mismatches.
- `[F]` Notebook. The submission cell of `report/notebook_skeleton.py` was executed against the free H2-2SC syntax checker. It compiled tof_3 with PSEL and returned job `AFByb3ZpZGVySm9iAaEdzTywfrOWhGbnlXxd-w` with status COMPLETED. The executed export is `report/notebook_executed.html`. The cell refuses any platform whose name does not end in SC.
- `[F]` Seeds and versions. The circuit generators use seed 20261006. The environment table of Appendix 5 pins pytket 2.18.4, pytket-quantinuum 0.59.3 and pyzx 0.10.7.

## 6. Plan for H2 hardware in the finals

`[F]` `value/finals_plan.py` sizes the runs from the measured H2-2E gain and not from the model prediction (`value/finals_plan.md`, Appendix 6).

| Test | Circuit | Shots per pipeline | Power | HQC |
|---|---|---|---|---|
| Primary, recommended | vbe_adder_3, P0 and P2 | 4364 | 0.80 | 1147.3 |
| Primary, minimum | vbe_adder_3, P0 and P2 | 2900 | 0.65 | 765.7 |
| Secondary | grover_5, P0 and P2 | 1900 | 0.65 | 2069.2 |
| Total, recommended | four jobs | | | 3216.5 |
| Total, minimum | four jobs | | | 2835.0 |

- `[O]` Primary rule, fixed before any hardware data. The test is one-sided at alpha 0.05. A z of 1.645 or more confirms that P2 raises F_H over P0 on H2 hardware. A z of -1.645 or less refutes it. Any other z gives no hardware claim.
- `[O]` Secondary rule. grover_5 tests whether the shortfall against the slope model recurs on hardware. It does not enter the primary decision.
- `[O]` Recommended design. The primary test runs at 4364 shots per pipeline for power 0.80 at the measured gain. 2900 shots per pipeline is the minimum design with power 0.65.
- `[O]` If the finals budget is below 3216.5 HQC the primary test runs alone at 4364 shots for 1147.3 HQC. Below 1147.3 HQC it runs at the minimum of 2900 shots for 765.7 HQC.

## 7. Limitations

- `[F]` PSEL4 saving split. Most of the PSEL4 saving against level 2 comes from choosing level 3. The ZX candidates add 0.26 % on the 17 proven family C circuits and 3.21 % on all 20 (`value/psel4_zx_only.md`). Three family C picks have no proof, and 87.6 % of the family C saving against level 3 comes from two of them, hrs_mult_5 and draper_adder_28. The non-zero-input vbe_adder_7 difference has z = 1.30 and is not resolved. The selector's exactness check uses full unitaries up to 8 qubits and the all-zero input state from 9 to 20 qubits.
- `[F]` Nothing in this report has run on H2 hardware. All platform results are emulator runs.
- `[F]` The HQC savings are stated against pytket-quantinuum at optimisation level 2, the default. Against level 3 PSEL costs 9.92 % more on B1 and 8.37 % more on family C. The ZX stage on top of level 3 (PSEL3) saves 3.49 % and 2.34 % (Table SB). PSEL4 saves 3.50 % against level 3 on family C and 0.73 % on B1 (Table P4).
- `[F]` The vbe_adder_3 fidelity gain is not significant at 0.05 after Holm correction over all three H2-2E circuits. grover_5 shows no gain at 4000 shots.
- `[F]` Family C is count-only apart from the H2-2E runs of vbe_adder_7 (Tables 3c and 3d). The PSEL output is proven on 18 of its 20 circuits. hrs_mult_5 is only spot-checked on 64 random basis inputs. The P0 pick of draper_adder_28 has no check. Family B1x has no check.
- `[F]` The 16.7 % family C saving rests on two multipliers with continuous rotation angles. Without continuous-angle circuits the saving is 7.47 %.
- `[F]` hwb8 carries 84.5 % of the B1 saving and has no sourced algorithm role.
- `[F]` The certificate covers 24 circuits with n at most 5. On the four B1 circuits it leaves most of the remaining T-count unaccounted for.
- `[F]` No user interview or survey supports the need. `[O]` The USD values of Section 1.5 rest on plan-average prices and not on a quoted marginal price.
- `[F]` The learned component of this submission is a cost model fitted on proxy fidelities (Appendix 4). This submission contains no learned rewriting.

## References

1. C.-F. Kam et al., An Exactness Barrier for ZX-Calculus Optimization of Synthesized Clifford+T Circuits, arXiv:2608.22801.
2. D. De Silva et al., Numerical Evaluation of ZX Calculus Optimization for Solovay Kitaev Quantum Circuit Synthesis, arXiv:2608.22810.
3. A. Kissinger and J. van de Wetering, Reducing the number of non-Clifford gates in quantum circuits, Phys. Rev. A 102, 022406 (2020), arXiv:1903.10477.
4. M. Amy, D. Maslov and M. Mosca, arXiv:1303.2042. M. Amy and M. Mosca, arXiv:1601.07363. Y. Nam et al., arXiv:1710.07345. L. Heyfron and E. Campbell, arXiv:1712.01557. AlphaTensor-Quantum, arXiv:2402.14396.
5. L. K. Grover, arXiv:quant-ph/9605043. A. Barenco et al., arXiv:quant-ph/9503016. D. Litinski, Quantum 3, 128 (2019), arXiv:1808.02892.
6. Quantinuum, Helios costing (HQC formula), https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html, and Singapore Grand Challenge code samples, https://github.com/Quantinuum/sg_grand_challenge.
7. Quantinuum, H2 emulators and noise model, https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/h2_emulators.html. Selene, https://github.com/quantinuum/selene.
8. pytket-quantinuum 0.59.3 and PyZX 0.10.7.
9. Quantinuum, pytket 2.18.5 documentation, `PassSelector` and `ZXGraphlikeOptimisation`, https://docs.quantinuum.com/tket/api-docs/passes.html.
10. Microsoft, Azure Quantum pricing, Quantinuum subscriptions, https://learn.microsoft.com/en-us/azure/quantum/pricing.
11. M. Reiher et al., arXiv:1605.03590. M. E. Beverland et al., arXiv:2211.07629. N. J. Ross and P. Selinger, arXiv:1403.2975.
12. S. Chakrabarti et al., A Threshold for Quantum Advantage in Derivative Pricing, arXiv:2012.03819.
13. D. Gosset, V. Kliuchnikov, M. Mosca and V. Russo, An algorithm for the T-count, Quantum Inf. Comput. 14 (2014), arXiv:1308.4134.
14. R. Duncan, A. Kissinger, S. Perdrix and J. van de Wetering, Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus, Quantum 4, 279 (2020), arXiv:1902.03178.
15. K. Staudacher, T. Guggemos, S. Grundner-Culemann and W. Gehrke, Reducing 2-QuBit Gate Count for ZX-Calculus based Quantum Circuit Optimization, EPTCS 394, 29 (2023), arXiv:2311.08881.
16. K. Chen et al., Quantum Circuit Optimization Based on Dynamic Grouping and ZX-Calculus for Reducing 2-Qubit Gate Count, arXiv:2507.14434.
17. M. Nägele and F. Marquardt, Optimizing ZX-diagrams with deep reinforcement learning, Mach. Learn.: Sci. Technol. 5, 035077 (2024), arXiv:2311.18588.
18. J. Riu, J. Nogué, G. Vilaplana, A. Garcia-Saez and M. P. Estarellas, Reinforcement Learning Based Quantum Circuit Optimization via ZX-Calculus, Quantum 9, 1758 (2025), arXiv:2312.11597.
19. Z. Li et al., Quarl: A Learning-Based Quantum Circuit Optimizer, Proc. ACM Program. Lang. 8, OOPSLA1 (2024), arXiv:2307.10120.
20. D. Kremer et al., Practical and efficient quantum circuit synthesis and transpiling with Reinforcement Learning, arXiv:2405.13196.
