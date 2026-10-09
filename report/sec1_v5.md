## 1. Problem and value

`[F]` The HQC, shot and T-count numbers below come from the script outputs `value/selector_ledger.md`, `value/value_ledger.md` and `value/value_by_application.md`. The noise parameters come from `docs/platform_notes.md` section 3.3. Manuscript statements are cited by their labels in arXiv:2608.22801. P0 is pytket's Quantinuum pass at level 2. P2 runs PyZX teleport_reduce before that pass. The pass selector PSEL compiles each circuit with P0 and with P2 and keeps the result with the lower HQC. HQC figures are for 1000 shots.

- `[F]` Tool. The delivered tool is the pass selector PSEL in `pipelines/pass_select.py`. It compiles each circuit with P0 and with P2 and keeps the compiled circuit with the lower HQC.
- `[F]` H2 cost. PSEL cannot cost more HQC than P0 on a circuit where P0 passes the exactness check, because P0 is always one of its two candidates. This holds by construction and is not a measured result. On the 15 checked B1 circuits the saving of 743.6 HQC or 4.79 % against P0 comes from the ZX stage P2. P2 alone saves 743.2 HQC there and PSEL matches it within 0.4 HQC. PSEL's own contribution is on family A. There P2 alone would cost 1,030.4 HQC or 6.27 % more than P0. PSEL picks P2 on 57 of the 180 circuits and saves 46.0 HQC or 0.28 % against P0. It thus avoids 1,076.4 HQC against always running P2 and keeps the B1 gain. It never raises n_2q against P0 on any of the 223 circuits of the four families.
- `[O]` User. A team that runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget and will later price them on a fault-tolerant Helios.
- `[O]` Decision. Should this circuit go through ZX rewriting before pytket's Quantinuum pass? `[F]` PSEL takes this decision per circuit from the HQC of both compilations.
- `[F]` Fault-tolerant cost. Against the written input circuits ZX removes 2,862 of 7,048 T gates on B1. Each T gate is one magic state, so the saving against the written circuits is 40.6 %. Our T-count after ZX equals the best ancilla-free value in the six papers of Section 3.4 on 14 of 22 comparable B1 and B1x circuits and is above it on the other 8 (Table C2). On the four B1 circuits with a certificate the certified fraction of the remaining T-count is 0.443. The fraction 0.997 holds for the 20 synthesised B2 Haar circuits at n = 2 and 3 and not for the B1 circuits.
- `[F]` Algorithms. Every circuit except hwb6, hwb8 and the two ham15 circuits is an adder, multiplier, Fourier transform, oracle, search instance or multi-controlled Toffoli. The adders, multipliers and the Fourier transform come from factoring and discrete-log circuits. grover_5 and mod5_4 come from search (Section 1.4). `[O]` The Toffoli circuits are placed in search as oracle and diffusion parts.

### 1.1 The user and the decision

`[O]` The user pays each H2 run in HQC from a fixed budget. On a fault-tolerant machine the same subroutines are priced in T gates. `[F]` The track budget is 10,000 HQC per team on H2-1E and H2-2E according to the Aqora forum topic "Emulator Cost" by Irfan Khan of Quantinuum (Section 3.7). No copy is in the repository.

`[F]` The decision is made per circuit between P0 alone and the ZX stage followed by P0. PSEL takes it from the HQC of both compilations. `[O]` The ledger explains the decision in HQC and in magic states and shows where the answer is no.

`[F]` No user interview or survey is part of this submission. `[O]` The need rests on the H2 cost formula and on the algorithm literature of Section 1.4. None of the six papers of Section 3.4 compares ZX rewriting against pytket's Quantinuum pass on the native H2 gate set.

### 1.2 What the pipeline saves on H2 today

`[F]` The organisers' sample code prices an H2 program as HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_M) / 5000. N_1q counts PhasedX gates. N_2q counts ZZPhase and ZZMax gates. N_M counts initialisations, measurements and resets. Rz gates are free. The source is `estimate_cost` in `src/python/pytket_cost_estimation.py` of `Quantinuum/sg_grand_challenge`. `pipelines/compile.py:hqc` reproduces that function. `[O]` We take this as the H2 price. `[F]` The Helios costing page gives the same form with maxima over 10 shots in its equation (1). See Reference 6 and `docs/platform_notes.md` section 3.4.

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

`[F]` PSEL keeps P0 on 123 of the 180 family A circuits. P2 is dearer on 108 of them and ties P0 in HQC on 15. Run on every family A circuit P2 would cost 17,453.0 HQC against 16,422.6 for P0. That is 1,030.4 HQC or 6.27 % more. PSEL costs 16,376.6 HQC on family A. It saves 46.0 HQC against P0 and 1,076.4 HQC against always running P2. On family A this avoided loss is what PSEL adds over P2. On the 60 XXZ circuits P2 is dearer on every circuit and would raise the total by 12.33 %. PSEL keeps P0 on all 60 of them. On the 60 TFIM circuits PSEL picks P2 on 32 and saves 0.62 % against P0. On the 60 ladder circuits it picks P2 on 25 and saves 0.52 %. `[O]` A user with a Trotter circuit runs PSEL and does not need to decide in advance whether the ZX stage pays.

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

`[F]` The 40.6 % saving on B1 in Table 1.2 is measured against the written input circuits and not against published optimisers. Our T-count after ZX equals the best ancilla-free value in the six papers of Section 3.4 on 14 of 22 comparable B1 and B1x circuits and is above it on the other 8 (Table C2).

`[F]` The exactness-barrier manuscript gives a per-instance floor (Kam et al., arXiv:2608.22801). The least denominator exponent of the exact Pauli channel of a Clifford+T circuit over Z[sqrt 2] is a lower bound on the T-count of every semantics-exact rewrite. The statements are Theorem B, Corollary cert and Theorem C of arXiv:2608.22801.

`[F]` On the 20 synthesised Haar circuits of family B2 the ZX stage removes 862 of 42,396 T gates or 2.0 %. The certified floor is 41,414 against 41,534 T gates after ZX. The certified-incompressible fraction is 0.997. Further exact T optimisation of these instances can gain at most 0.3 % of the remaining T-count. On the worst single instance the bound is 0.7 %.

`[F]` On the four certified B1 circuits the floor is 47 against 106 T gates after ZX. The fraction is 0.443. `[O]` The certificate does not say whether this gap is headroom for a better rewrite or slack in the bound (Section 3.4).

`[F]` Converting magic states into Helios time or cost needs factory and logical-cycle figures that Quantinuum has not published in any source we found. No conversion is made. As context only, Dasu et al. report a logical magic state on H1-1 with infidelity 7(+3/-1) x 10^-5 (arXiv:2506.14688).

### 1.4 Where these circuits sit in real algorithms

`[F]` Table 1.3. All B1 and B1x circuit names appear in Table II of Amy and Mosca (arXiv:1601.07363). Their Grover_5 is a different circuit (Section 3.4). Each circuit is counted in the first area of the summary table of `docs/applications.md` that lists it.

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

`[F]` The delivered tool is PSEL in `pipelines/pass_select.py`. It decides per circuit whether to run PyZX teleport_reduce before pytket's Quantinuum pass. It cannot cost more HQC than P0 where P0 passes the exactness check, because P0 is always one of its candidates. This holds by construction. On the 15 checked B1 circuits the saving of 4.79 % against P0 comes from the ZX stage P2. PSEL picks P2 on 14 of them and matches the P2 total within 0.4 HQC. P2 saves 7.9 % on the checked factoring circuits and 4.8 % on the checked search circuits. PSEL's own contribution is on family A. There P2 alone would cost 1,030.4 HQC or 6.27 % more than P0. PSEL keeps P0 on 123 of the 180 circuits and saves 46.0 HQC or 0.28 % against P0. It thus avoids 1,076.4 HQC against always running P2 and keeps the B1 gain. `[O]` A user does not need to decide in advance whether the ZX stage pays. `[F]` The ledger gives magic-state counts for every B1, B1x and B2 circuit. The certificate covers only the 24 circuits of `results/certificates.csv`, all with n at most 5. Four of them are B1 subroutines with a pooled certified fraction of 0.443. The other 20 are the synthesised B2 Haar circuits at n = 2 and 3 with a pooled fraction of 0.997.

`[F]` The winner of the finals receives credits on the on-premise Helios machine in Singapore according to the organisers' timeline email of 25 Aug 2026. No copy is in the repository. `[O]` Quantinuum's Helios roadmap targets fault tolerance. The T-count column prices a later fault-tolerant layer. `[F]` The Helios HQC formula charges no Rz gate (`docs/platform_notes.md` section 3.4). The T-count therefore does not change the cost of the finals credits.

`[F]` Model prediction. A proxy fit of 1.18e-3 per ZZ gate predicts a relative fidelity gain of 1.79 % for P2 on vbe_adder_3 and a median relative gain of 0.24 % over B1. `[O]` These are model predictions and not measurements.

`[F]` The 18 H2-2E jobs carry HQC estimates that sum to 5933.2 HQC. Six ran vbe_adder_3, hwb6 and grover_5 under P0 and P2 at 1000 shots. Twelve repeated vbe_adder_3 and grover_5 three more times. At 1000 shots the emulator does not resolve P2 against P0 on any of the three circuits. At 4000 shots per pipeline the pooled F_H of vbe_adder_3 is 0.9520 under P0 and 0.9628 under P2. The difference of +0.0108 has z = +2.38 and a two-sided p of 0.017. The repeat circuits were chosen after Table E2. The Holm-adjusted p is 0.035 over the two repeated circuits and 0.052 over all three H2-2E circuits. This measured relative gain of 1.13 % lies below the predicted 1.79 % by 1.38 sd of the difference. On grover_5 the pooled difference is +0.0007 with z = +0.10 and is not resolved at 4000 shots per pipeline. It lies 2.94 sd of the difference below the predicted gain of 0.0229 (Section 3.7.1). `[O]` The vbe_adder_3 gain is significant before correction and after correction over the two repeated circuits. It is not significant at 0.05 after correction over all three H2-2E circuits.

`[F]` The ledger states value in HQC, shots and magic states and makes no claim in currency. `[O]` The team name Learned ZX Rewriting names the research programme. `[F]` The learned component of this submission is the cost model of Section 4, which predicts fidelity from compile-time features. This submission contains no learned rewriting.
