# Summary for the judges

The main report is `report.pdf` and the technical appendix is `report_full.pdf`.

Team Learned ZX Rewriting. Report title: "A pass selector keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2". Quantinuum Singapore Grand Challenge, submission 1. `report.pdf` is built from `report/report_short.md`. `report_full.pdf` is the full report v5 built from `report/report_v5.md` without its changelog sections. This page was built on 9 October 2026 and is aligned with the main report `report.pdf` and with Section 1 of the technical appendix `report_full.pdf`.

`[F]` marks a statement copied from the report or from the `value/` outputs. `[O]` marks a judgement. The script `check_summary_numbers.py` finds every number of this page in `report/report_v5.md` or in `value/`.

## HQC saved on arithmetic and oracle circuits of 20 to 56 qubits

`[F]` On the 15 arithmetic and oracle circuits of 20 to 56 qubits without continuous rotation angles the pass selector PSEL saves 748.4 of 10,019.6 HQC or 7.47 % against P0 at 1000 shots. These are the 9 adders and the 6 multi-controlled X oracles of family C. Family C was built by qiskit from published constructions (appendix Section 3.8). PSEL saves 12.9 % on the adders and 0.1 % on the oracles. As a secondary figure PSEL saves 4,104.4 HQC or 16.7 % over all 20 circuits of family C. Two spot-checked multipliers with continuous rotation angles drive this figure. They save 34.5 % and carry 81.8 % of that saving. On the 3 QFT adders PSEL keeps P0 and saves 0 %. On the QFT adders P2 is dearer and PSEL avoids 1,057.2 HQC against always running P2.

`[F]` Family C is count-only. The compiled outputs of 14 circuits are spot-checked on 64 random basis inputs and agree with the input up to a global phase. This covers 64 of 2^n inputs and is not a proof of equivalence. The other 6 circuits are unchecked and carry 41.6 HQC of the saving. Four of them are P2 picks, namely modadd_2n_10, modadd_2n_20, mcx_dirty_28 and mcx_b95_54. The multipliers and the QFT adders carry rotation angles outside the pi/4 grid. Their T-counts leave out these rotations.

## Worked use case

`[F]` Two Grover search instances of 7 and 9 qubits pass the exactness check under P0 and P2 (appendix Section 3.9). PSEL picks P2 on both. It saves 39.8 HQC or 5.42 % and 80.8 HQC or 4.96 % at 1000 shots. Within the 10,000 HQC budget with at most 10,000 shots per job PSEL affords 791 and 322 more shots. At the ideal success probability the expected hits rise from 13687.8 to 14478.2 and from 6132.0 to 6452.9. The T-count falls from 448 to 210 and from 1008 to 436.

`[O]` This T-count drop comes from Toffolis that the Barenco construction repeats on the same qubits. It is not a general ZX gain.

## Value in USD and finance use

`[F]` Azure Quantum lists the Quantinuum H2 Standard Plan at USD 125,000 per month with 10,000 HQC and the Premium Plan at USD 175,000 per month with 17,000 HQC (https://learn.microsoft.com/en-us/azure/quantum/pricing). The page was last updated on 2025-12-23. The implied plan-average price is USD 12.50 per HQC on Standard and USD 10.29 on Premium (appendix Section 1.5).

`[O]` At these averages the family C saving of 748.4 HQC on the 15 circuits without continuous angles is worth about USD 7,700 to 9,400. The family A avoided loss of 1,076.4 HQC is worth about USD 11,100 to 13,500. Both figures count 1000 shots of each circuit once. They use the plan average and not a marginal price. They ignore the bundled eHQCs and the Azure infrastructure costs.

`[F]` In the derivative-pricing methods of Chakrabarti et al. both path-loading schemes and the payoff calculation need quantum arithmetic (Chakrabarti et al., arXiv:2012.03819, Appendix C). The same paper writes that "the T-count dominates the computational requirements". PSEL saves 12.9 % HQC on the 9 adders and 7.47 % on the 15 family C circuits without continuous angles. `[O]` These adders are the kind of arithmetic such circuits call. A claim that arithmetic dominates the cost of derivative pricing is Unverifiable.

## User and decision

`[O]` The user runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget. The same team will later price these subroutines in T gates on a fault-tolerant Helios. The decision is made per circuit. Should the circuit go through PyZX teleport_reduce (pipeline P2) before pytket's Quantinuum pass at level 2 (pipeline P0)? `[F]` The delivered tool is the pass selector PSEL in `pipelines/pass_select.py`. It decides per circuit whether to run PyZX teleport_reduce before pytket's Quantinuum pass. It compiles each circuit with P0 and with P2 and keeps the compiled circuit with the lower HQC. `[O]` The ledger explains the choice in HQC and in magic states.

## Do-no-harm guard for pytket users

`[O]` A pytket user can add a ZX stage in front of the Quantinuum pass without knowing whether it pays. `[F]` pytket ships one such pass, `pytket.passes.ZXGraphlikeOptimisation`. Its documentation warns that it "may increase the cost of the circuit". pytket also documents `PassSelector`, which returns "the best circuit as selected by a given metric" (pytket 2.18.5 API documentation, https://docs.quantinuum.com/tket/api-docs/passes.html). We measured the PyZX stage of P2 and not that pass. Added blindly, the P2 stage costs 1,030.4 HQC or 6.27 % more than P0 on the 180 Trotter circuits of family A. It costs 1,057.2 HQC or 22.1 % more on the 3 QFT adders of family C. On draper_adder_16 it costs 1,385.0 HQC against 906.8 for P0 or 52.7 % more. This circuit is unchecked. PSEL removes this risk by construction and still keeps the 4.79 % saving on B1 and the 7.47 % saving on the 15 family C circuits without continuous angles. `[O]` PSEL is the PassSelector pattern applied to P0 and P2 with HQC as the metric. The contribution is the measured ledger and the guard result and not a new selection mechanism. PSEL lets a pytket user try ZX rewriting on every circuit for the price of a second compilation.

## Where not to spend fault-tolerant compiler effort

`[O]` A team that plans fault-tolerant chemistry or phase-estimation workloads needs to know where exact T optimisation still pays. `[F]` Reiher et al. write of the rotations in their FeMoco simulation that "These rotations dominate the cost of the quantum simulation" (arXiv:1605.03590). Beverland et al. call non-Clifford rotations "among the most resource intensive operations" (arXiv:2211.07629). Ross and Selinger approximate a z-rotation with T-count 3 log2(1/eps) plus lower-order terms in the typical case (arXiv:1403.2975). On the 20 B2 circuits with gridsynth-synthesised rotations the ZX stage removes 862 of 42,396 T gates or 2.0 %. The certified floor is 41,414 of the 41,534 T gates left after ZX. Every exact rewrite therefore keeps at least 99.7 % of the remaining T-count. Further exact T optimisation can gain at most 0.3 % of the pooled count and 0.7 % on the worst instance. The certificate covers 24 circuits, all with n at most 5. `[O]` The certificate tells such a team per instance that exact rewriting of synthesised rotations is not where its compiler effort pays.

## HQC saved on the B1 benchmarks and Trotter circuits

`[F]` Our reproduced P0 matches the official pytket-quantinuum 0.59.3 pass on every compiled row. The official P0 and P2 equal our P0 and P2 in n_2q, n_1q, two-qubit depth and HQC on all 445 compiled rows of families A, B1, B1x and B2 (appendix Section 2.2). hwb8 under the official P2 timed out. Family C was not compiled with the official pass.

`[F]` PSEL cannot cost more HQC than P0 on a circuit where P0 passes the exactness check. This holds by construction because P0 is always one of its two candidates. It is not a measured result. PSEL picks P2 on 14 of the 15 checked B1 circuits. HQC is computed with the organisers' formula `estimate_cost` from the gate counts of the compiled circuit (appendix Section 1.2). At 1000 shots it costs 14,772.4 HQC against 15,516.0 for P0 on the 15 checked B1 circuits. The saving is 743.6 HQC or 4.79 %. It comes from the ZX stage P2. P2 alone costs 14,772.8 HQC there and PSEL matches it within 0.4 HQC. The median per-circuit saving is 3.94 %. On the 180 Trotter circuits of family A PSEL picks P2 on 57 and saves 46.0 HQC or 0.28 %. It never raises the ZZ gate count against P0 on any of the 223 circuits.

`[F]` P2 is cheaper than P0 on 14 of the 15 B1 circuits. hwb8 alone accounts for 84.5 % of the PSEL saving on B1 and serves no sourced quantum algorithm. Without hwb8 the PSEL saving on B1 is 115.0 HQC. On family A P2 alone would cost 1,030.4 HQC or 6.27 % more than P0. PSEL keeps P0 on 123 of these 180 circuits and on all 60 XXZ circuits. PSEL's own contribution is to avoid this P2 loss while it keeps the B1 gain. On family A it saves 1,076.4 HQC against always running P2.

`[O]` The median of 3.94 % is the better guide for a single circuit. A user with a Trotter circuit runs PSEL and does not need to decide in advance whether the ZX stage pays.

## Magic states saved

`[F]` On a surface-code machine each T gate consumes one magic state (Litinski, arXiv:1808.02892). Against the written input circuits the ZX stage removes 2,862 of 7,048 T gates on B1. That is 40.6 % of the written T-count. On the 8 count-only B1x circuits it removes 798 of 1,652 or 48.3 %. On the 20 synthesised B2 Haar circuits it removes 862 of 42,396 or 2.0 %. Our T-count after ZX equals the best ancilla-free value in the six papers of appendix Section 3.4 on 14 of 22 comparable B1 and B1x circuits and is above it on the other 8 (appendix Table C2).

## Certified fraction

`[F]` The exactness-barrier certificate (Kam et al., arXiv:2608.22801) gives a per-instance floor on the T-count of every semantics-exact rewrite. It covers 24 circuits, all with n at most 5. On the 20 B2 circuits at n = 2 and 3 the floor is 41,414 against 41,534 T gates after ZX. The certified-incompressible fraction is 0.997. On the four B1 circuits at n = 5 the floor is 47 against 106 and the fraction is 0.443. The fraction 0.997 does not hold for B1.

`[O]` The certificate does not say whether the B1 gap is headroom for a better rewrite or slack in the bound.

## Application map

`[F]` All B1 and B1x circuits appear in Table II of Amy and Mosca (arXiv:1601.07363). Appendix Table 1.3 places vbe_adder_3, mod_mult_55, mod_red_21 and qft_4 under integer factoring. gf2_pow_4_mult goes under elliptic-curve discrete log over GF(2^m). grover_5 and mod5_4 go under Grover search. hwb6, hwb8 and the two ham15 circuits have no sourced algorithm role. P2 saves 7.9 % HQC on the checked factoring circuits and 4.8 % on the checked search circuits.

`[O]` The tof and barenco_tof circuits are placed in search as oracle and diffusion parts.

## Emulator runs

`[F]` Three H2-Emulator jobs with 22 circuit rows and six H2-2E jobs ran on 8 October 2026 at 1000 shots. Twelve repeat H2-2E jobs ran vbe_adder_3 and grover_5 three more times. The 18 H2-2E jobs carry HQC estimates that sum to 5933.2 HQC. On H2-2E at 1000 shots the difference F_H(P2) minus F_H(P0) is +0.0050 on vbe_adder_3 (z = +0.55), -0.0150 on hwb6 (z = -1.21) and +0.0076 on grover_5 (z = +0.48). On the H2-Emulator the four Toffoli comparisons all lie within two sd of zero. Neither tier resolves P2 against P0 at 1000 shots. At the predicted gain a 2-sd resolution needs 1147 shots per pipeline on vbe_adder_3, 1974 on grover_5 and 20462 on hwb6. At 4000 shots per pipeline the pooled H2-2E difference is +0.0108 on vbe_adder_3 with z = +2.38 and a two-sided p of 0.017. The repeat circuits were chosen after Table E2. The Holm-adjusted p is 0.035 over the two repeated circuits and 0.052 over all three H2-2E circuits. On grover_5 it is +0.0007 with z = +0.10 and is not resolved. It lies 2.94 sd below the predicted gain of 0.0229. Nothing in the report has run on hardware.

`[O]` The emulator runs confirm execution and HQC accounting on the Quantinuum platform. vbe_adder_3 is the one circuit on which the emulator measures a fidelity gain of P2 over P0. The gain is significant before correction and after correction over the two repeated circuits. It is not significant at 0.05 after correction over all three H2-2E circuits. Elsewhere the P2 against P0 comparison rests on the ZZPhase counts and the Selene ensemble means.

## Table C2 finding

`[F]` Appendix Table C2 sets our T-count after ZX beside the smallest T-count reported in six papers and beside the certified floor. Our ZX stage matches the best published ancilla-free count on 14 of the 22 comparable circuits. On the four certified circuits the ZX stage leaves 106 T gates and the floor is 47. The best published ancilla-free counts on them sum to 105. Published optimisers therefore close 1 of the 59 gates between our count and the floor. That gate is on mod5_4. The other 58 gates are closed by neither side.

`[O]` The certificate cannot tell whether the 58 open gates are headroom or slack in the bound.

## Files in this package

| File | Content |
|---|---|
| `report.pdf`, `report.md` | Main report, built from `report/report_short.md` |
| `report_full.pdf`, `report_full.md` | Technical appendix, report v5 without its changelog sections |
| `figures/` | Images of both reports |
| `code.zip` | `git archive` of the commit named in `MANIFEST.txt` |
| `REPRODUCE.md` | Environment, commands, tests and seeds |
| `SUMMARY.md`, `check_summary_numbers.py` | This page and the script that checks its numbers |
| `MANIFEST.txt` | Size and sha256 of every file |
| `build.sh`, `run_tests.sh`, `strip_changelog.py`, `check_pdf_tables.py`, `report.css` | Scripts that rebuild and check this package |
| `build_logs/` | Build log and test logs |
