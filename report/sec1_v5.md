## 1. Problem and value

`[F]` The HQC, shot and T-count numbers below come from the script outputs `value/value_ledger.md` and `value/value_by_application.md`. The noise parameters come from `docs/platform_notes.md` section 3.3. Manuscript statements are cited by their labels in arXiv:2608.22801. P0 is pytket's Quantinuum pass at level 2. P2 runs PyZX teleport_reduce before that pass. HQC figures are for 1000 shots.

- `[O]` User. A team that runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget and will later price them on a fault-tolerant Helios.
- `[O]` Decision. Should this circuit go through ZX rewriting before pytket's Quantinuum pass?
- `[F]` H2 cost. On the 15 checked B1 circuits P2 costs 14,772.8 HQC against 15,516.0 for P0. The saving is 743.2 HQC or 4.8 %. The median per-circuit saving is 3.9 %.
- `[F]` Fault-tolerant cost. ZX removes 2,862 of 7,048 T gates on B1. Each T gate is one magic state, so the saving is 40.6 %. On the four B1 circuits with a certificate the certified fraction of the remaining T-count is 0.443. The fraction 0.997 holds for the 20 synthesised B2 Haar circuits at n = 2 and 3 and not for the B1 circuits.
- `[F]` Algorithms. Every circuit except hwb6, hwb8 and the two ham15 circuits is an adder, multiplier, Fourier transform, oracle, search instance or multi-controlled Toffoli. The adders, multipliers and the Fourier transform come from factoring and discrete-log circuits. grover_5 and mod5_4 come from search (Section 1.4). `[O]` The Toffoli circuits are placed in search as oracle and diffusion parts.

### 1.1 The user and the decision

`[O]` The user pays each H2 run in HQC from a fixed budget. On a fault-tolerant machine the same subroutines are priced in T gates. `[F]` The track budget is 10,000 HQC per team on H2-1E and H2-2E according to the Aqora forum topic "Emulator Cost" by Irfan Khan of Quantinuum (Section 3.7). No copy is in the repository.

`[O]` The decision is made per circuit: run P0 alone or insert the ZX stage first. The ledger answers it in HQC and in magic states. It also says when the answer is no.

`[F]` No user interview or survey is part of this submission. `[O]` The need rests on the H2 cost formula and on the algorithm literature of Section 1.4. None of the six papers of Section 3.4 compares ZX rewriting against pytket's Quantinuum pass on the native H2 gate set.

### 1.2 What the pipeline saves on H2 today

`[F]` The organisers' sample code prices an H2 program as HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_M) / 5000. N_1q counts PhasedX gates. N_2q counts ZZPhase and ZZMax gates. N_M counts initialisations, measurements and resets. Rz gates are free. The source is `estimate_cost` in `src/python/pytket_cost_estimation.py` of `Quantinuum/sg_grand_challenge`. `pipelines/compile.py:hqc` reproduces that function. `[O]` We take this as the H2 price. `[F]` The Helios costing page gives the same form with maxima over 10 shots in its equation (1). See Reference 6 and `docs/platform_notes.md` section 3.4.

`[F]` p2 = 1.29e-3 is the largest gate fault rate of the H2-2E emulator. The H2-2E emulator parameters are p2 = 1.29e-3 and p1 = 7.3e-5 per gate, readout flips 9e-4 and 1.8e-3 for states 0 and 1 and p_init = 4e-5 (`docs/platform_notes.md` section 3.3).

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

`[F]` Saved HQC buys shots. The following figures assume one job that pays the 5 HQC job fee once. At the 10,000 HQC team budget P0 affords 68,178 shots of vbe_adder_3 and P2 affords 87,675. That is 19,497 extra shots or 28.6 % more. vbe_adder_3 has the largest per-circuit percentage saving of the 15 B1 circuits. The median extra-shot gain over the 15 circuits is 4.3 % (`value/value_by_application.md`). On the Grover oracle mod5_4 the gain is 11,757 shots or 7.5 %.

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

`[O]` For an H2 user the ledger is a reproducible answer to "should I run ZX before pytket" in HQC per area. `[F]` P2 saves 7.9 % on the checked factoring circuits and 4.8 % on the checked search circuits. `[O]` On Trotter circuits the answer is no. `[F]` The ledger gives magic-state counts for every B1, B1x and B2 circuit. The certificate covers only the 24 circuits of `results/certificates.csv`, all with n at most 5. Four of them are B1 subroutines with a pooled certified fraction of 0.443. The other 20 are the synthesised B2 Haar circuits at n = 2 and 3 with a pooled fraction of 0.997.

`[F]` The winner of the finals receives credits on the on-premise Helios machine in Singapore according to the organisers' timeline email of 25 Aug 2026. No copy is in the repository. `[O]` Quantinuum's Helios roadmap targets fault tolerance. The T-count column prices a later fault-tolerant layer. `[F]` The Helios HQC formula charges no Rz gate (`docs/platform_notes.md` section 3.4). The T-count therefore does not change the cost of the finals credits.

`[F]` Model prediction. A proxy fit of 1.18e-3 per ZZ gate predicts a relative fidelity gain of 1.79 % for P2 on vbe_adder_3 and a median relative gain of 0.24 % over B1. `[O]` These are model predictions and not measurements.

`[F]` The six H2-2E jobs of vbe_adder_3, hwb6 and grover_5 under P0 and P2 carry HQC estimates that sum to 1,840 HQC. At 1000 shots the emulator does not resolve P2 against P0 on any of the three. On vbe_adder_3 the measured F_H was 0.954 under P0 and 0.959 under P2 (Section 3.7.1).

`[F]` The ledger states value in HQC, shots and magic states and makes no claim in currency. `[O]` The team name Learned ZX Rewriting names the research programme. `[F]` The learned component of this submission is the cost model of Section 4, which predicts fidelity from compile-time features. This submission contains no learned rewriting.
