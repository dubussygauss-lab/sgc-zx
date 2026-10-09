### 1.2 What the pipeline saves on H2 today

`[F]` Headline. PSEL saves HQC on two sets of circuits. On the 15 checked B1 circuits it saves 743.6 HQC or 4.79 % against P0. This saving comes from the ZX stage P2 and PSEL matches it within 0.4 HQC. On the 15 arithmetic and oracle circuits of family C with 20 to 56 qubits and no continuous rotation angles it saves 748.4 of 10,019.6 HQC or 7.47 % against P0. Over all 20 family C circuits it saves 4,104.4 HQC or 16.7 % (Table 1.1b). This secondary figure rests on two multipliers with continuous rotation angles. rgqft_mult_6 is proven equal to its input and hrs_mult_5 is only spot-checked. Per application it saves 12.9 % on the adders and 34.5 % on the multipliers. The 34.5 % comes from two multipliers with continuous rotation angles. These two circuits carry 3,356.0 HQC or 81.8 % of the family C saving. PSEL saves 0.1 % on the multi-controlled X oracles and 0 % on the QFT adders, where it keeps P0. On family C PSEL also avoids 1,057.2 HQC against always running P2, because P2 is dearer on all three QFT adders.

`[F]` Family C status. Family C is count-only apart from one H2-2E run of vbe_adder_7 (Section 3.7.2). A PyZX miter reduction proves the PSEL output of every one of the 15 circuits without continuous angles equal to its input as a full unitary up to global phase. It proves the PSEL output of 18 of the 20 circuits. These include 13 of the 14 P2 picks. The compiled angles of hrs_mult_5 lie off the dyadic grid. Its P2 output is therefore only spot-checked on 64 random basis inputs. The miter of the P0 pick of draper_adder_28 timed out after 300 s and that output has no check. Section 3.8 gives the method. The two multipliers and the three QFT adders carry rotation angles outside the pi/4 grid. After the ZX stage 600 such rotations remain in hrs_mult_5 and 507 in rgqft_mult_6. The T-count does not count them. PyZX rounds the P2 input of draper_adder_28 by at most 1.50e-06 rad per angle. PSEL keeps P0 on that circuit.

`[F]` Table 1.1b. Family C, HQC at 1000 shots of PSEL against P0 and P2 per application. Count-only. Checked counts the circuits whose P0 and P2 outputs both pass the 64-input basis check. Section 3.8 gives the proof verdict per circuit. Saved % is computed on the application sums. Source: `value/family_C_selector.md`, computed from `results/family_C_counts.csv`. Section 3.8 gives the per-circuit rows.

| Application | Circuits | Qubits | PSEL picks P2 | HQC P0 | HQC P2 | HQC PSEL | Saved vs P0 | Saved vs P0 % | Saved vs P2 | Checked |
|---|---|---|---|---|---|---|---|---|---|---|
| Adders | 9 | 20-56 | 9 | 5,777.0 | 5,031.4 | 5,031.4 | 745.6 | 12.9 | 0.0 | 7 |
| Multipliers | 2 | 21-24 | 2 | 9,737.0 | 6,381.0 | 6,381.0 | 3,356.0 | 34.5 | 0.0 | 2 |
| Multi-controlled X oracles (Grover) | 6 | 21-56 | 3 | 4,242.6 | 4,239.8 | 4,239.8 | 2.8 | 0.1 | 0.0 | 4 |
| QFT adders (Draper) | 3 | 20-56 | 0 | 4,778.4 | 5,835.6 | 4,778.4 | 0.0 | 0.0 | 1,057.2 | 1 |
| All family C | 20 | 20-56 | 14 | 24,535.0 | 21,487.8 | 20,430.6 | 4,104.4 | 16.7 | 1,057.2 | 14 |

`[F]` Worked use case. Two Grover search instances find one marked item among 2^5 and 2^6 entries on 7 and 9 qubits (Section 3.9). Both pass the exactness check under P0 and P2. PSEL picks P2 on both. It saves 39.8 HQC or 5.42 % on the 7-qubit instance and 80.8 HQC or 4.96 % on the 9-qubit instance. Within the 10,000 HQC budget and a limit of 10,000 shots per job PSEL affords 791 and 322 more shots. At the ideal success probability the expected hits rise from 13687.8 to 14478.2 and from 6132.0 to 6452.9. The T-count falls from 448 to 210 and from 1008 to 436. `[O]` This T-count drop comes from Toffolis that the Barenco construction repeats on the same qubits, whose T phases partly cancel under the ZX stage. It is not a general ZX gain.

`[F]` The organisers' sample code prices an H2 program as HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. N_1q counts PhasedX gates. N_2q counts ZZPhase and ZZMax gates. N_SPAM counts initialisations, measurements and resets. `estimate_cost` starts N_SPAM at the number of qubits and adds one per measurement and reset. A circuit with every qubit measured once has N_SPAM = 2n. Rz gates are free. The source is `estimate_cost` in `src/python/pytket_cost_estimation.py` of `Quantinuum/sg_grand_challenge`. `pipelines/compile.py:hqc` reproduces that function. `[O]` We take this as the H2 price. `[F]` The Helios costing page gives the same form with maxima over 10 shots in its equation (1). See Reference 6 and `docs/platform_notes.md` section 3.4.

`[F]` p2 = 1.29e-3 is the largest gate fault rate of the H2-2E emulator. The H2-2E emulator parameters are p2 = 1.29e-3 and p1 = 7.3e-5 per gate, readout flips 9e-4 and 1.8e-3 for states 0 and 1 and p_init = 4e-5 (`docs/platform_notes.md` section 3.3).

`[F]` The tool we deliver is the pass selector PSEL in `pipelines/pass_select.py`. It compiles each circuit with P0 and with P2 and keeps the compiled circuit with the lower HQC. An HQC tie goes to the lower n_2q and a further tie goes to P0. A candidate that fails the exactness check of `pipelines/compile.py:check` is dropped. Section 2.2 defines PSEL next to the other pipelines.

`[F]` Table 1.1a. HQC at 1000 shots of PSEL against P0 and P2, per family. B1x is count-only and is never merged with B1. Saved % is computed on the family sums. The median is over per-circuit percentages against P0. Source: `value/selector_ledger.md`, computed from the P0 and P2 rows of `value/value_ledger.csv` and `results/family_B2_counts.csv`.

| Family | Circuits | PSEL picks P2 | HQC P0 | HQC P2 | HQC PSEL | Saved vs P0 | Saved vs P0 % | Saved vs P2 | Median per-circuit % vs P0 |
|---|---|---|---|---|---|---|---|---|---|
| A, Trotter | 180 | 57 | 16,422.6 | 17,453.0 | 16,376.6 | 46.0 | 0.28 | 1,076.4 | 0.00 |
| B1, checked | 15 | 14 | 15,516.0 | 14,772.8 | 14,772.4 | 743.6 | 4.79 | 0.4 | 3.94 |
| B1x, count-only | 8 | 7 | 3,288.8 | 3,141.0 | 3,141.0 | 147.8 | 4.49 | 0.0 | 2.40 |
| B2, Haar | 20 | 0 | 730.0 | 731.6 | 730.0 | 0.0 | 0.00 | 1.6 | 0.00 |

`[F]` PSEL costs more HQC than P0 only if P0 is dropped by an error or by the exactness check. No P0 row of the four families was dropped. The four families hold 223 circuits. PSEL saves 743.6 HQC or 4.79 % on B1. It saves 147.8 HQC or 4.49 % on B1x. On B1 and B1x these savings come from the ZX stage P2. P2 alone saves 743.2 HQC on B1 and 147.8 HQC on B1x. On family A it saves 46.0 HQC or 0.28 %. On B2 it saves nothing because P2 is never cheaper than P0 there.

`[F]` PSEL never raises the ZZ gate count against P0 on any of the 223 circuits. It lowers n_2q on 13 of the 15 B1 circuits and on 5 of the 8 B1x circuits. The choice that minimises n_2q, with an n_2q tie broken by HQC, agrees with the choice of PSEL on all 223 circuits (`value/selector_ledger.md`).

`[F]` Table 1.1. HQC at 1000 shots of P2 against P0 by application area. B1 is checked. B1x is count-only and is never merged with B1. Saved % is computed on the area sums. Source: `value/value_by_application.md`.

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

`[F]` P2 is cheaper than P0 in HQC on 14 of the 15 B1 circuits. The exception is qft_4 in the integer factoring row. There P2 costs 0.4 HQC more and PSEL keeps P0. This is the only HQC difference between PSEL and P2 on B1 and B1x.

`[F]` hwb8 alone accounts for 84.5 % of the PSEL saving on B1 but serves no sourced quantum algorithm. Without hwb8 the PSEL saving on B1 is 115.0 HQC. `[O]` The median of 3.94 % is the better guide for a single circuit.

`[F]` Saved HQC buys shots. The following figures assume one job that pays the 5 HQC job fee once. PSEL picks P2 for vbe_adder_3. At the 10,000 HQC team budget P0 affords 68,178 shots of vbe_adder_3 and PSEL affords 87,675. That is 19,497 extra shots or 28.6 % more. vbe_adder_3 has the largest per-circuit percentage saving of the 15 B1 circuits. The median extra-shot gain of P2 over the 15 circuits is 4.3 % (`value/value_by_application.md`). On the Grover oracle mod5_4 PSEL also picks P2 and the gain is 11,757 shots or 7.5 %.

`[F]` The H2 hardware guide limits a job to 10,000 shots (`docs/platform_notes.md` section 3.4). With that limit and one fee per job P0 affords 67,974 shots of vbe_adder_3 and PSEL affords 87,324. That is 19,350 extra shots or 28.5 % more. On mod5_4 the gain is 11,584 shots or 7.4 % (`value/value_by_application.md`). Whether the per-job limit applies on H2-2E is Unverifiable from the repository.

`[F]` PSEL keeps P0 on 123 of the 180 family A circuits. P2 is dearer on 108 of them and ties P0 in HQC on 15. Run on every family A circuit P2 would cost 17,453.0 HQC against 16,422.6 for P0. That is 1,030.4 HQC or 6.27 % more. PSEL costs 16,376.6 HQC on family A. It saves 46.0 HQC against P0 and 1,076.4 HQC against always running P2. On family A this avoided loss is what PSEL adds over P2. On the 60 XXZ circuits P2 is dearer on every circuit and would raise the total by 12.33 %. PSEL keeps P0 on all 60 of them. On the 60 TFIM circuits PSEL picks P2 on 32 and saves 0.62 % against P0. On the 60 ladder circuits it picks P2 on 25 and saves 0.52 %. `[O]` A user with a Trotter circuit runs PSEL and does not need to decide in advance whether the ZX stage lowers the HQC.
