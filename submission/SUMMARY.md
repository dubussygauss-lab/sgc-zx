# Summary for the judges

The main report is `report.pdf` and the technical appendix is `report_full.pdf`.

Team Learned ZX Rewriting. Report title: "PSEL4 compiles each H2 circuit four ways and keeps the cheapest". Quantinuum Singapore Grand Challenge, submission 1. `report.pdf` is built from `report/report_short.md`. `report_full.pdf` is the full report v5 built from `report/report_v5.md` without its changelog sections. This page was built on 10 October 2026 and is aligned with the main report `report.pdf` and with Section 1 of the technical appendix `report_full.pdf`.

`[F]` marks a statement copied from the report or from the `value/` outputs. `[O]` marks a judgement. The script `check_summary_numbers.py` finds every number of this page in `report/report_v5.md` or in `value/`.

## Product and four findings

`[F]` Problem, measured. pytket-quantinuum's level 3 saves 13.9 % HQC over the default level 2 on our 217 circuits but costs more than level 2 on 45 of them. Those 45 lose 372.0 HQC in total and the worst loses 12.95 % on gf2_pow_4_mult (`value/policy_compare.md`, `value/usd_psel4.md`). `[O]` A user cannot tell in advance which circuits regress.

`[F]` Solution. PSEL4 removes that risk. It compiles each circuit four ways (level 2, level 3 and PyZX teleport_reduce before each), checks each result and keeps the cheapest. On the 217 circuits it is costlier than level 2 on none. It needs 15.7 % less HQC than always level 2, 2.08 % (1,051.6 HQC) less than always level 3 and 1.35 % (679.6 HQC) less than the per-circuit cheaper of level 2 and level 3. It is a drop-in for pytket-quantinuum's default compile on Quantinuum H2 and by construction never costs more than level 2 or level 3 where both pass its checks. Figure PC of the main report shows the two per-circuit ratios (`value/fig_policy.py`). `[O]` For a team that spends the Standard Plan's 10,000 HQC a month on this mix it frees 1,573.3 HQC a month, worth USD 19,666 (workload assumption).

`[F]` Product. The candidates are level 2 (pytket's default, P0), level 3 (L3) and PyZX teleport_reduce before each (P2, P2L3). Usage is one command, `python3 pipelines/pass_select.py --psel4 <circuit.qasm>`. Level 2 and level 3 are always candidates. PSEL4 therefore never costs more HQC than level 2 or level 3 on a circuit where both pass its checks. This guarantee is a design property. It is not a measured result. Each candidate is checked against its input as a full unitary up to 8 qubits and on 64 random computational basis inputs from 9 to 20 qubits. The all-zero input is one of the 64. Above 20 qubits family C relies on PyZX miter proofs.

`[F]` Finding 1, level 3 adoption made safe. Over 217 circuits PSEL4 needs 49,580.6 HQC against 58,837.2 for always level 2 and 50,632.2 for always level 3 (appendix Section 3.8.4, `value/policy_compare.md`). Always level 3 gives 13.95 points of the 15.7 % saving. Per-circuit selection plus ZX give the other 1.79 points (`value/usd_psel4.md`). PSEL4 costs more than level 2 or level 3 on none. `[F]` It takes 5.08 times the compile wall time of level 2.

`[F]` Finding 2, the HQC-cheapest compile is not the most accurate. Five pre-registered H2-2E comparisons of the PSEL4 pick against level 2 on non-zero inputs were run with one to four inputs each and 400 shots per program (1000 on the single-input vbe_adder_7). The pick was significantly less accurate on 2. On cdkm_adder_10 the level 3 pick returns the correct sum in 0.8267 of shots against 0.8692 under level 2, z = -2.90. On hwb6 the pick ZX then level 3 returns the correct output in 0.8883 against 0.9200, z = -2.64 and Holm p = 0.0168. The pick was not significantly different on 2 (modadd_2n_10 z = -0.22, vbe_adder_3 z = +0.51) and not significantly better on 1 (vbe_adder_7 z = +1.30). No pick was significantly more accurate. On cdkm_adder_10 the less accurate pick has fewer two-qubit gates (118 against 141) and lower two-qubit depth (65 against 122, post hoc). `[O]` Neither HQC nor gate counts order fidelity on the emulator. `[F]` The HQC saving still exceeds the accuracy loss. HQC per correct answer is lower for the pick in 5 of 5 pairs and in 8 of 8 including three earlier pairs of the two-candidate selector. Pooled over the 8 pairs it is 18.1 % lower (R = 0.8192, bootstrap 95 % interval 0.8132 to 0.8254), decomposed as HQC ratio 0.8170 over accuracy ratio 0.9973 (`value/hqc_per_correct.md`). `[O]` So PSEL4 serves cost-bound users. Accuracy-bound users need a fidelity-aware choice, which is the finals deliverable.

`[F]` Finding 3, mechanism. HQC charges no Rz gate and bills every PhasedX at the same rate whatever its angle, so the T-count reduction that ZX is best at has no HQC value on H2, and ZX can pay mainly through two-qubit gates, which level 3 already resynthesises. Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp (appendix Section 3.8.5, `value/mechanism_zx_l3.md`). ZX phase teleportation still removes non-Clifford gates that level 3 keeps. On 14 B1 circuits 656 remain after P2 against 746 after level 3. The ZX-only gain on top of the cheaper pytket level is 0.26 % on the 17 proven family C circuits, 3.21 % on all 20, 0.49 % on B1 and nothing on the Trotter circuits (`value/psel4_zx_only.md`). It falls as T-density rises (family C Spearman rho -0.64).

`[F]` Finding 4, correctness. All 83 PSEL4 picks with 9 to 20 qubits pass the 64-basis-input check. So do 187 of 187 required candidates and 142 of 142 others. Negative controls fail as they should (`value/psel4_basis_check.md`). A PyZX miter proves the PSEL4 output equal to its input on 17 of the 20 family C circuits of 20 to 56 qubits. MQT QCEC proved none of the other three. Its verdicts there were inconclusive and it returned no counterexample on any pair. Its alternating run on hrs_mult_5 was killed after 630 s. A conservative variant keeps the cheapest verified candidate. Where none is verified it keeps the level 2 output flagged "default, unverified", which happens only on hrs_mult_5. It saves 12.25 % against level 2. It is costlier than level 2 on 0 circuits and costlier than level 3 on 2 circuits whose level 3 output is itself unverified (`value/psel4_conservative.md`).

`[F]` Guard. Run on every circuit before level 2, the ZX stage costs 6.27 % more HQC on the 180 Trotter circuits. pytket's own ZXGraphlikeOptimisation followed by level 2 costs 59.22 % more than level 2 on 14 B1 circuits. PSEL4 pays none of these losses on the 217 circuits of its ledger.

`[O]` Finals. The finals goal is a fidelity-aware learned selector that keeps the per-answer saving and protects accuracy where users need it. `[F]` Submission 1 provides its training data, the ledger of 217 circuits times 4 checked candidates and the emulator labels of the 5 pre-registered PSEL4-pick pairs from 48 H2-2E jobs. A first classifier on input-circuit features does not beat a constant choice on held-out families, with balanced accuracy 0.433 against 0.500 (appendix Section 3.8.2). `[O]` The finals model needs structural features of the compiled candidates and the emulator labels.

`[F]` Limitations (appendix Section 7). The PSEL4 pick was significantly less accurate on 2 of 5 pre-registered pairs. No user interview supports the need. The ZX-only gain is small. Two family C level 3 outputs and three PSEL4 outputs have no proof. One of the three is the P2L3 pick of draper_adder_28, whose input PyZX rounded by at most 1.50e-06 rad per angle. No exactness check runs above 20 qubits apart from the miter proofs. The hwb8 P0 and P2 candidates were not basis-checked within the time budget. HQC is the formula estimate. All platform runs are emulator runs and nothing has run on H2 hardware. The earlier vbe_adder_3 tests ran on all-zero inputs and have a pooled Holm-adjusted p of 0.052 over three circuits. The per-answer intervals pool inputs and ignore between-run variation. 3 of 8 per-answer pairs use P2, the earlier selector's pick. The T-count floor is the known bound of Gosset et al. evaluated on 24 circuits of at most 5 qubits. The mechanism analysis lacks 6 circuits for lack of CPU budget. `[O]` PSEL4 is the PassSelector pattern of pytket. `[F]` The earlier two-candidate selector PSEL keeps the lower HQC of P0 and P2. Below it appears only for the earlier H2-2E pairs.

## HQC saved on arithmetic and oracle circuits of 20 to 56 qubits

`[F]` On the 15 arithmetic and oracle circuits of 20 to 56 qubits without continuous rotation angles PSEL4 saves 11.52 % against level 2 at 1000 shots (appendix Table P4). These are the 9 adders and the 6 multi-controlled X oracles of family C. Family C was built by qiskit from published constructions (appendix Section 3.8). Over all 20 circuits of family C PSEL4 saves 25.85 % against level 2 and 3.50 % against level 3. PSEL4 picks level 3 on 7 of the 9 adders and P2L3 on the other 2. On the QFT adders draper_adder_10 and draper_adder_16 it keeps P0. On the QFT adders P2 is dearer than P0 and PSEL4 never pays that loss.

`[F]` Family C is count-only apart from the H2-2E runs of vbe_adder_7, cdkm_adder_10 and modadd_2n_10. The PSEL4 output of every one of the 15 circuits without continuous angles is proven equal to its input as a full unitary up to global phase by a PyZX miter reduction. The miter joins the compiled circuit to the adjoint of the input and must reduce under `full_reduce` to plain wires as in PyZX's `verify_equality` test. No ancilla is assumed to start in |0>. Compiled angles are snapped to a dyadic grid with a largest snap of 5.27e-12 half-turns. Over all 20 circuits the PSEL4 output is proven on 17 (`results/family_C_equivalence_psel4.md`). The compiled angles of the P2 pick of hrs_mult_5 lie off the dyadic grid. It is only spot-checked on 64 random basis inputs. The miter of the L3 pick of rgqft_mult_6 timed out after 300 s. On draper_adder_28 PSEL4 picks P2L3 at 2336.2 HQC. PyZX rounded its input by at most 1.50e-06 rad per angle, so the PSEL4 output equals the input only up to that rounding. Its miter timed out after 300 s and the output is unproven. The multipliers and the QFT adders carry rotation angles outside the pi/4 grid. Their T-counts leave out these rotations.

## Worked use case

`[F]` Two Grover search instances of 7 and 9 qubits pass the exactness check under P0 and P2 (appendix Section 3.9). PSEL4 picks P2L3 on both, at 533.4 and 1041.6 HQC against 734.2 and 1629.4 under P0 and 533.6 and 1048.4 under level 3 (`value/psel4_ledger.md`). Over the two instances PSEL4 saves 33.36 % against level 2. The T-count after the ZX stage falls from 448 to 210 and from 1008 to 436. Shot counts within the 10,000 HQC budget are in appendix Table U1.

`[O]` This T-count drop comes from Toffolis that the Barenco construction repeats on the same qubits. It is not a general ZX gain.

## Value in USD and finance use

`[F]` Azure Quantum lists the Quantinuum H2 Standard Plan at USD 125,000 per month with 10,000 HQC and the Premium Plan at USD 175,000 per month with 17,000 HQC (https://learn.microsoft.com/en-us/azure/quantum/pricing). The page was last updated on 2025-12-23. The implied plan-average price is USD 12.50 per HQC on Standard and USD 10.29 on Premium (appendix Section 1.5).

`[F]` At these averages the PSEL4 saving of 9,256.6 HQC against always level 2 on the 217 ledger circuits is worth USD 95,289 to 115,707 (`value/usd_psel4.md`). Its saving of 1,051.6 HQC against always level 3 is worth USD 10,825 to 13,145. The 372.0 HQC that always level 3 loses on its 45 costlier circuits are worth USD 3,829 to 4,650. Family C gives 6,341.8 of the 9,256.6 HQC saved against level 2.

`[O]` Workload assumption. A team spends the Standard Plan's 10,000 HQC a month on circuits with the ledger's mix. `[F]` Under that assumption PSEL4 frees 1573.3 HQC a month. That is worth USD 19,666 at the Standard average and USD 16,195 at the Premium average. `[O]` All USD figures count 1000 shots of each circuit once. They use the plan average and not a marginal price. They ignore the bundled eHQCs and the Azure infrastructure costs.

`[F]` In the derivative-pricing methods of Chakrabarti et al. both path-loading schemes and the payoff calculation need quantum arithmetic (Chakrabarti et al., arXiv:2012.03819, Appendix C). The same paper writes that "the T-count dominates the computational requirements". PSEL4 saves 11.52 % HQC against level 2 on the 15 family C circuits without continuous angles, which are the 9 adders and the 6 oracles. `[O]` These adders are the kind of arithmetic such circuits call. A claim that arithmetic dominates the cost of derivative pricing is Unverifiable.

## User and decision

`[O]` The user runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget. The same team will later price these subroutines in T gates on a fault-tolerant Helios. The decision is made per circuit. Should the circuit go through PyZX teleport_reduce before pytket's Quantinuum pass, and at level 2 or level 3? `[F]` The delivered tool is PSEL4 (`python3 pipelines/pass_select.py --psel4 <circuit.qasm>`). It compiles each circuit with P0, L3, P2 and P2L3 and keeps the compiled circuit with the lowest HQC. `[O]` The ledger explains the choice in HQC and in magic states.

## Do-no-harm guard for pytket users

`[O]` A pytket user can add a ZX stage in front of the Quantinuum pass without knowing whether it pays. `[F]` pytket 2.18.4 ships one such pass, `pytket.passes.ZXGraphlikeOptimisation`. Its documentation warns that it "may increase the cost of the circuit". pytket also documents `PassSelector`. It returns "the best circuit as selected by a given metric" (pytket 2.18.5 documentation, same docstring in the installed 2.18.4, https://docs.quantinuum.com/tket/api-docs/passes.html). We measured the PyZX stage of P2 and not that pass. Added blindly, the P2 stage costs 1,030.4 HQC or 6.27 % more than P0 on the 180 Trotter circuits of family A. It costs 1,057.2 HQC or 22.1 % more on the 3 QFT adders of family C. On draper_adder_16 it costs 1,385.0 HQC against 906.8 for P0 or 52.7 % more. A PyZX miter proves its P0 and P2 outputs equal to its input (Appendix Section 3.8). PSEL4 costs no more HQC than level 2 or level 3 where its checks pass. It saves 10.65 % against level 2 on B1 and 11.52 % on the 15 family C circuits without continuous angles (appendix Table P4). `[O]` PSEL4 is the PassSelector pattern applied to P0, L3, P2 and P2L3 with HQC as the metric. The contribution is the measured ledger and the guard result and not a new selection mechanism. PSEL4 lets a pytket user try ZX rewriting and level 3 on every circuit for the price of three extra compilations.

## Where not to spend fault-tolerant compiler effort

`[O]` A team that plans fault-tolerant chemistry or phase-estimation workloads needs to know where exact T optimisation still pays. `[F]` Reiher et al. write of the rotations in their FeMoco simulation that "These rotations dominate the cost of the quantum simulation" (arXiv:1605.03590). Beverland et al. call non-Clifford rotations "among the most resource intensive operations" (arXiv:2211.07629). Ross and Selinger approximate a z-rotation with T-count 3 log2(1/eps) plus lower-order terms in the typical case (arXiv:1403.2975). On the 20 B2 circuits with gridsynth-synthesised rotations the ZX stage removes 862 of 42,396 T gates or 2.0 %. The certified floor is 41,414 of the 41,534 T gates left after ZX. Every exact rewrite therefore keeps at least 99.7 % of the pooled remaining T-count and on the worst single circuit, haar_n3_eps1e-03_s5, at least 2478 of its 2496 T gates. Further exact T optimisation can gain at most 0.3 % of the pooled count and 0.72 % on the worst instance. The certificate covers 24 circuits, all with n at most 5. `[O]` The certificate tells such a team per instance that exact rewriting of synthesised rotations is not where its compiler effort pays.

## HQC saved on the B1 benchmarks and Trotter circuits

`[F]` Our reproduced P0 matches the official pytket-quantinuum 0.59.3 pass on every compiled row. The official P0 and P2 equal our P0 and P2 in n_2q, n_1q, two-qubit depth and HQC on all 445 compiled rows of families A, B1, B1x and B2 (appendix Section 2.2). hwb8 under the official P2 timed out. Family C was not compiled with the official pass.

`[F]` HQC is computed with the organisers' formula `estimate_cost` from the gate counts of the compiled circuit (appendix Section 1.2). At 1000 shots PSEL4 costs 13,863.4 HQC against 15,516.0 for level 2 on the 15 checked B1 circuits. That is a saving of 10.65 %. Against level 3 it saves 0.73 %. hwb8 serves no sourced quantum algorithm. Without it PSEL4 saves 18.29 % against level 2 on the other 14 B1 circuits (appendix Table P4).

`[F]` On the 180 Trotter circuits of family A PSEL4 saves 2.88 % against level 2 and 1.74 % against level 3. It picks no ZX candidate there. It keeps P0 on 35 circuits and picks L3 on 145. P2 alone would cost 1,030.4 HQC or 6.27 % more than P0 on these circuits. `[O]` A user with a Trotter circuit runs PSEL4 and does not need to decide in advance whether the ZX stage lowers the HQC.

## Magic states saved

`[F]` On a surface-code machine each T gate consumes one magic state (Litinski, arXiv:1808.02892). Against the written input circuits the ZX stage removes 2,862 of 7,048 T gates on B1. That is 40.6 % of the written T-count. On the 8 count-only B1x circuits it removes 798 of 1,652 or 48.3 %. On the 20 synthesised B2 Haar circuits it removes 862 of 42,396 or 2.0 %. Our T-count after ZX equals the best ancilla-free value in the six papers of appendix Section 3.4 on 14 of 22 comparable B1 and B1x circuits and is above it on the other 8 (appendix Table C2).

## Certified fraction

`[F]` The per-instance floor on the T-count of every semantics-exact rewrite is the channel bound of Gosset, Kliuchnikov, Mosca and Russo (arXiv:1308.4134), restated in the exactness-barrier manuscript (Kam et al., arXiv:2608.22801). The team evaluates it exactly. The bound itself is not new. It covers 24 circuits, all with n at most 5. On the 20 B2 circuits at n = 2 and 3 the floor is 41,414 against 41,534 T gates after ZX. The certified-incompressible fraction is 0.997. On the four B1 circuits at n = 5 the floor is 47 against 106 and the fraction is 0.443. The fraction 0.997 does not hold for B1.

`[O]` The certificate does not say whether the B1 gap is headroom for a better rewrite or slack in the bound.

## Application map

`[F]` All B1 and B1x circuits appear in Table II of Amy and Mosca (arXiv:1601.07363). Appendix Table 1.3 places vbe_adder_3, mod_mult_55, mod_red_21 and qft_4 under integer factoring. gf2_pow_4_mult goes under elliptic-curve discrete log over GF(2^m). grover_5 and mod5_4 go under Grover search. hwb6, hwb8 and the two ham15 circuits have no sourced algorithm role. P2 saves 7.9 % HQC on the checked factoring circuits and 4.8 % on the checked search circuits.

`[O]` The tof and barenco_tof circuits are placed in search as oracle and diffusion parts.

## Emulator runs

`[F]` Three H2-Emulator jobs with 22 circuit rows and six H2-2E jobs ran on 8 October 2026 at 1000 shots. Twelve repeat H2-2E jobs ran vbe_adder_3 and grover_5 three more times. The 18 H2-2E jobs carry HQC estimates that sum to 5933.2 HQC. On H2-2E at 1000 shots the difference F_H(P2) minus F_H(P0) is +0.0050 on vbe_adder_3 (z = +0.55), -0.0150 on hwb6 (z = -1.21) and +0.0076 on grover_5 (z = +0.48). On the H2-Emulator the four Toffoli comparisons all lie within two sd of zero. Neither tier resolves P2 against P0 at 1000 shots. At the predicted gain a 2-sd resolution needs 1147 shots per pipeline on vbe_adder_3, 1974 on grover_5 and 20462 on hwb6. At 4000 shots per pipeline the pooled H2-2E difference is +0.0108 on vbe_adder_3 with z = +2.38 and a two-sided p of 0.017. The repeat circuits were chosen after Table E2. The Holm-adjusted p is 0.035 over the two repeated circuits and 0.052 over all three H2-2E circuits. On grover_5 it is +0.0007 with z = +0.10 and is not resolved. It lies 2.94 sd below the predicted gain of 0.0229. Two more H2-2E jobs ran the 22-qubit family C adder vbe_adder_7 under P0 and P2 at 1000 shots. F_H is 0.886 under P0 and 0.897 under P2 with z = 0.79, not resolved. On the non-zero input a = 28, b = 111, fixed and committed before submission, it returns the correct sum in 0.883 of shots under P0 and 0.901 under L3, the PSEL4 pick (z = 1.30). Twelve more H2-2E jobs ran cdkm_adder_10 and modadd_2n_10 on three pre-registered non-zero inputs each. On cdkm_adder_10 the PSEL4 pick L3 succeeds less often than P0 with z = -2.90. On modadd_2n_10 the pick P2L3 shows z = -0.22. Fourteen more H2-2E jobs ran vbe_adder_3 on four pre-registered non-zero inputs and hwb6 on three at 400 shots per job. On vbe_adder_3 the pick L3 gives z = +0.51 (Holm p 0.6089). On hwb6 the pick P2L3 succeeds less often than P0 with z = -2.64 (Holm p 0.0168). HQC per correct output is lower for the pick in all 8 pairs, pooled R = 0.8192 (`value/hqc_per_correct.md`). All 48 H2-2E jobs total 9971.8 HQC, which leaves 28.2 of the quota. Every job ID is in `EVIDENCE.md`. Nothing in the report has run on hardware.

`[O]` The emulator runs confirm execution and HQC accounting on the Quantinuum platform. The vbe_adder_3 difference is significant before correction and after correction over the two repeated circuits. The gain is not established at 0.05 after correction over all three H2-2E circuits. Elsewhere the P2 against P0 comparison rests on the ZZPhase counts and the Selene ensemble means.

## Stronger baselines

`[F]` pytket-quantinuum's default compilation is optimisation level 2, our P0. Running teleport_reduce before level 3 and keeping the cheaper result saves 3.49 % and 2.34 % against level 3 (appendix Section 3.8.1). The level-3-aware selector PSEL4 keeps the lowest HQC of P0, P2, L3 and P2L3. It costs no more than either level on all 217 circuits where both passed. It saves 3.50 % against level 3 and 25.85 % against level 2 on family C. A PyZX miter proves its output on 17 of these 20 circuits. On those 17 it saves 0.80 % against level 3 and 10.22 % against level 2 (appendix Table P4).

## Related work

`[O]` Learned ZX rewriters (Nägele and Marquardt, Riu et al.) and Quarl minimise node or gate counts. None of them prices its output with the H2 HQC formula. This submission adds no new rewriter. It adds a measured HQC ledger on H2 against the official pytket-quantinuum pass with equivalence proofs (appendix Section 3.4.1).

## Confirmatory emulator test

`[F]` On the repeats r2 to r4 alone, run after the two circuits were chosen, vbe_adder_3 gives a difference of +0.0127 with z = +2.44 and a Holm-adjusted p of 0.030 over the two repeated circuits. The choice to report the repeats alone was made after the pooled result was known. Every circuit ran on the all-zero input.

## Table C2 finding

`[F]` Appendix Table C2 sets our T-count after ZX beside the smallest T-count reported in six papers and beside the certified floor. Our ZX stage matches the best published ancilla-free count on 14 of the 22 comparable circuits. On the four certified circuits the ZX stage leaves 106 T gates and the floor is 47. The best published ancilla-free counts on them sum to 105. Published optimisers therefore close 1 of the 59 gates between our count and the floor. That gate is on mod5_4. The other 58 gates are closed by neither side.

`[O]` The certificate cannot tell whether the 58 open gates are headroom or slack in the bound.

## Files in this package

| File | Content |
|---|---|
| `presentation.pdf`, `presentation.tex` | Slide deck of 12 slides and its LaTeX source |
| `one_page_summary.pdf` | One-page summary required by the submission checklist, built from `report/one_page_summary.md` |
| `report.pdf`, `report.md` | Main report, built from `report/report_short.md` |
| `report_full.pdf`, `report_full.md` | Technical appendix, report v5 without its changelog sections |
| `figures/` | Images of both reports |
| `code.zip` | `git archive` of the commit named in `MANIFEST.txt` |
| `README.md`, `requirements.txt` | Instructions for running the solution and pinned dependencies (copies of the repository files) |
| `EVIDENCE.md` | Execution evidence: every emulator job ID with shots, HQC estimate and result file |
| `REPRODUCE.md` | Environment, commands, 39 tests and seeds |
| `SUMMARY.md`, `check_summary_numbers.py` | This page and the script that checks its numbers |
| `MANIFEST.txt` | Size and sha256 of every file |
| `build.sh`, `strip_changelog.py`, `check_pdf_tables.py`, `report.css` | Scripts that rebuild and check this package |
| `build_logs/` | Build log and test logs |
