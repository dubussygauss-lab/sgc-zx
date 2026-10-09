# One-page summary: a pass selector keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Main report `report.pdf`, technical appendix `report_full.pdf` (cited as "App."), source `code.zip` with `README.md`, emulator evidence `EVIDENCE.md`. `[F]` marks a checkable statement, `[O]` a judgement.

## Problem statement

`[F]` A run on Quantinuum H2 is billed in HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000 (App. 1.2). ZX rewriting (PyZX teleport_reduce) placed before pytket's Quantinuum pass can lower this cost or raise it. Always run, it costs 6.27 % more HQC than pytket alone on 180 Trotter circuits and 22.1 % more on 3 QFT adders. pytket's own ZX pass `ZXGraphlikeOptimisation` is documented as one that "may increase the cost of the circuit". `[O]` A team with a fixed HQC budget cannot tell in advance, circuit by circuit, whether ZX rewriting pays.

## Approach

`[F]` The pass selector PSEL (`pipelines/pass_select.py`) compiles each circuit twice: with P0, pytket-quantinuum's default pass at optimisation level 2, and with P2, PyZX teleport_reduce followed by P0. It drops a candidate that fails its exactness check and keeps the one with the lower HQC. Our P0 and P2 give the same counts as the official pytket-quantinuum pass on all 445 compiled rows of families A, B1, B1x and B2 (App. 2.2). `[O]` PSEL is pytket's `PassSelector` pattern with HQC as the metric; the contribution is the measured cost ledger and the guard result, not a new selection mechanism. `[F]` On the 20 circuits of family C (20 to 56 qubits) a PyZX miter reduction proves the PSEL output equal to its input on 18, three of them after snapping angles by at most 5.27e-12 half-turns (App. 3.8). The team's exactness-barrier certificate (arXiv:2608.22801) gives a per-instance floor on the T-count of any exact rewrite.

## Key results

- `[F]` 15 arithmetic and oracle circuits of 20 to 56 qubits without continuous rotation angles (9 adders, 6 multi-controlled X oracles): PSEL saves 748.4 of 10,019.6 HQC or 7.47 % against P0, and 12.9 % on the adders. The PSEL output of all 15 is proven equal to its input as a full unitary up to global phase. Family C is count-only. Over all 20 circuits of family C PSEL saves 4104.4 HQC or 16.7 %; two multipliers with continuous angles carry 81.8 % of that saving.
- `[F]` Guard: against always running P2, PSEL avoids 1,076.4 HQC on the 180 Trotter circuits and 1,057.2 HQC on the 3 QFT adders. PSEL costs no more HQC than P0 whenever P0 passes its checks, by construction.
- `[F]` Clifford+T benchmarks B1 (15 circuits, n <= 12): 743.6 HQC or 4.79 % saved, median per circuit 3.94 %; hwb8 alone gives 84.5 % of that saving.
- `[F]` Worked use case, Grover search on 7 and 9 qubits: PSEL saves 5.42 % and 4.96 % of the HQC and affords 791 and 322 more shots within a 10,000 HQC budget.
- `[F]` Magic states: the ZX stage removes 40.6 % of the written T-count on B1. On 20 synthesised Haar circuits of 2 and 3 qubits the certified floor is 0.997 of the T-count left after ZX, pooled: further exact T optimisation can gain at most 0.3 % pooled and 0.72 % on the worst instance.
- `[F]` Emulator execution: 18 H2-2E jobs (5933.2 HQC by the cost formula) and 3 H2-Emulator jobs, job IDs in `EVIDENCE.md`. At 4000 shots per pipeline the Hellinger fidelity of P2 minus P0 on vbe_adder_3 is +0.0108 (z = +2.38, p = 0.017; Holm-adjusted 0.052 over three circuits); grover_5 shows no gain. The fidelity gain is therefore not established at 0.05 after correction. Nothing has run on hardware.

## Relevance to quantum computing

`[F]` On family C PSEL saves most on arithmetic subroutines, which the cited literature places, with the oracles, in integer factoring, elliptic-curve discrete log, Grover search and derivative pricing (App. 1.3, 1.4; Chakrabarti et al., arXiv:2012.03819). On a surface-code machine each T gate consumes one magic state (Litinski, arXiv:1808.02892). `[O]` PSEL lowers the cost of these subroutines on H2 today. The certificate tells a fault-tolerant compiler team per instance that exact rewriting of synthesised rotations is not where its effort pays.

## Potential impact

`[O]` At the Azure Quantum plan averages of USD 12.50 and 10.29 per HQC (App. 1.5) the 748.4 HQC saved on family C is worth about USD 7,700 to 9,400, and the 1,076.4 HQC avoided on the Trotter circuits about USD 11,100 to 13,500, each circuit counted once at 1000 shots. PSEL drops into a pytket workflow for the price of a second compilation. `[F]` Limits: no user interview or survey is part of this submission; family C is count-only; no hardware run. `[O]` Finals plan: 4364 shots per pipeline on vbe_adder_3 at 1147.3 HQC, power 0.80 if the emulator gain holds on hardware (App. 6).
