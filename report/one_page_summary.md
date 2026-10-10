# PSEL4 compiles each H2 circuit four ways and keeps the cheapest

**PSEL4 needs 15.7 % less HQC than pytket-quantinuum's default level 2 over 217 circuits, and on the H2-2E emulator the cheaper compile (the PSEL4 pick in 3 of 6 pairs) needs 17.4 % fewer HQC per correct answer, fewer in 6 of 6 comparisons.**

<style>table{border-collapse:collapse;margin:0.3em 0;font-size:9.8pt}th,td{border-bottom:1px solid #bbb;padding:1px 8px;text-align:left}th:nth-child(n+2),td:nth-child(n+2){text-align:right}</style>

## Problem statement

A job on Quantinuum H2 is billed in HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. pytket-quantinuum compiles at optimisation level 2 by default. Level 3 and ZX rewriting can each lower the HQC of a circuit or raise it. A cost-bound user needs the cheapest correct compile of each circuit without trying every option by hand. [O]

## Approach

PSEL4 compiles each circuit four ways: level 2, level 3 and PyZX teleport_reduce before each. Each candidate is checked against its input as a full unitary up to 8 qubits and as the output state on the all-zero input from 9 to 20 qubits. Above that the selector runs no check, and family C relies on miter proofs (result 4). PSEL4 drops a candidate that fails and keeps the lowest HQC. It is pytket's `PassSelector` pattern with HQC as the metric.

## Key results

**1. Cost: level 3's savings without its regressions.** Total HQC at 1000 shots per circuit.

| Policy, 217 circuits | Total HQC | Saved vs level 2 | Circuits costlier than level 2 | Largest per-circuit loss |
|---|---|---|---|---|
| Always level 2 (default) | 58,837.2 | 0 | 0 | none |
| Always level 3 | 50,632.2 | 13.9 % | 45 | 12.95 % (gf2_pow_4_mult) |
| PSEL4 | 49,580.6 | 15.7 % | 0 | none |

Switching to level 3 alone loses 372.0 HQC on 45 circuits. PSEL4 keeps every level 3 saving, avoids all 45 regressions and adds ZX where it pays, 2.08 % below always level 3. It saves 25.8 % on family C (20 arithmetic and oracle circuits of 20 to 56 qubits), 10.7 % on B1 (15 Clifford+T benchmarks), 2.9 % on A (180 Trotter circuits) and 33.4 % on the Grover use case. Blind ZX before level 2 costs 6.27 % more on the Trotter circuits.

**2. Cheaper per correct answer.** On the H2-2E emulator the lower-HQC compile of each pair delivered each correct answer for fewer HQC than level 2 in 6 of 6 comparisons, each with the 95 % upper bound of the cost ratio R below 1. Pooled over the 6 pairs it needs 17.4 % fewer HQC per correct answer (bootstrap 95 % interval 16.7 to 18.1 %). On cdkm_adder_10 the level 3 pick returns the correct sum less often (0.8267 against 0.8692, z = -2.90) yet costs 8.0 % fewer HQC per correct sum (R = 0.9203, 95 % interval 0.8896 to 0.9521). The three newest pairs use the PSEL4 pick. The three earlier pairs (vbe_adder_3, hwb6, vbe_adder_7 on the all-zero input) use P2 from the earlier two-candidate selector.

**3. Mechanism.** Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp, and two-qubit gates dominate HQC. ZX phase teleportation removes non-Clifford rotations that level 3 keeps (656 against 746 on 14 B1 circuits). Its gain on top of the cheaper level is 3.21 % on all 20 family C circuits and falls as T-density rises (Spearman rho -0.64, p 0.010).

**4. Correctness.** A PyZX miter proves the output equal to its input on 18 of 20 family C circuits for level 3 and 17 of 20 for PSEL4. Our level 2 compiles give the same counts as the official pytket-quantinuum pass on 445 rows.

## Relevance to quantum computing

Adders sit in the modular arithmetic of Shor factoring and in arithmetic for derivative pricing (Chakrabarti et al., arXiv:2012.03819). PSEL4 lowers the cost of these subroutines on H2 today with no change to the user's code. [O]

## Potential impact

The ledger saving of 9,256.6 HQC is worth USD 95,289 to 115,707 at the Azure plan averages (USD 10.29 to 12.50 per HQC). A team that spends the Standard Plan's 10,000 HQC a month on this mix frees 1,573.3 HQC a month, worth USD 19,666 (workload assumption). [O] PSEL4 is a drop-in: `python3 pipelines/pass_select.py --psel4 <circuit.qasm>`, at 5.08 times the compile time of level 2. Finals goal: a learned, fidelity-aware selector that keeps the per-answer saving and protects accuracy where users need it, as on cdkm_adder_10. [O]

**Limits.** No user interview. Emulator only (34 H2-2E jobs, 8983.4 HQC), HQC is the formula estimate. Two level 3 and three PSEL4 family C outputs are unproven. On draper_adder_28 the PSEL4 pick starts from angles PyZX rounded by up to 1.50e-06 rad. The ledger run checked level 3 only up to 12 qubits. The mechanism analysis lacks 6 circuits.

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Report `report.pdf`, appendix `report_full.pdf`, code `code.zip`, evidence `EVIDENCE.md`.

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
