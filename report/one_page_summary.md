# PSEL4 compiles each H2 circuit four ways and keeps the cheapest

**Over 217 circuits PSEL4 needs 15.7 % less HQC on Quantinuum H2 than pytket-quantinuum's default level 2, and by construction it never costs more than level 2 or level 3 on any circuit.**

<style>table{border-collapse:collapse;margin:0.3em 0;font-size:9.8pt}th,td{border-bottom:1px solid #bbb;padding:1px 8px;text-align:left}th:nth-child(n+2),td:nth-child(n+2){text-align:right}</style>

## Problem statement

A job on Quantinuum H2 is billed in HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. pytket-quantinuum compiles at optimisation level 2 by default. Level 3 and ZX rewriting can each lower the HQC of a circuit or raise it. A cost-bound user needs the cheapest correct compile of each circuit without trying every option by hand. [O]

## Approach

PSEL4 compiles each circuit four ways. The candidates are level 2, level 3 and PyZX teleport_reduce before each. Each candidate is checked against its input as a full unitary up to 8 qubits and as the output state on the all-zero input from 9 to 20 qubits. Above 20 qubits the selector runs no check. PSEL4 drops a candidate that fails and keeps the lowest HQC. Level 2 and level 3 are always candidates, so PSEL4 never costs more than either where both pass. It is pytket's `PassSelector` pattern with HQC as the metric.

## Key results

**1. Cost.** Total HQC at 1000 shots per circuit for three compile policies.

| Policy, 217 circuits | Total HQC | Saved vs level 2 | Circuits costlier than level 2 | Largest per-circuit loss |
|---|---|---|---|---|
| Always level 2 (default) | 58,837.2 | 0 | 0 | none |
| Always level 3 | 50,632.2 | 13.9 % | 45 | 12.95 % (gf2_pow_4_mult) |
| PSEL4 | 49,580.6 | 15.7 % | 0 | none |

PSEL4 saves 25.8 % on family C (20 arithmetic and oracle circuits of 20 to 56 qubits), 10.7 % on B1 (15 Clifford+T benchmarks), 2.9 % on A (180 Trotter circuits) and 33.4 % on the Grover use case. Blind ZX before level 2 costs 6.27 % more HQC on the 180 Trotter circuits and 22.1 % more on 3 QFT adders. ZXGraphlikeOptimisation before level 2 costs 59.22 % more on 14 B1 circuits.

**2. Mechanism.** Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp, and two-qubit gates dominate HQC. ZX phase teleportation still removes non-Clifford rotations that level 3 keeps (656 against 746 on 14 B1 circuits), but its gain on top of the cheaper level is 0.26 % on the 17 proven family C circuits, 3.21 % on all 20, 0.49 % on B1 and 0 on Trotter circuits, and it falls as T-density rises (family C Spearman rho -0.64, p 0.010). The hypothesis that ZX rewriting lowers the H2 cost partly holds. [O]

**3. Cost is not fidelity.** Three pre-registered H2-2E tests compare the PSEL4 pick with level 2 on non-zero inputs. On cdkm_adder_10 the pick (level 3) has 118 two-qubit gates against 141 and two-qubit depth 65 against 122. It returns the correct sum less often, 0.8267 against 0.8692 over 3 inputs and 1200 shots per arm (z = -2.90). On modadd_2n_10 there is no resolved difference (z = -0.22). On vbe_adder_7 level 3 is ahead, 0.901 against 0.883 (z = 1.30, not resolved). On the H2-2E emulator the cheapest compile is not always the most accurate. [O]

**4. Correctness.** A PyZX miter proves the level 3 output equal to its input on 18 of 20 family C circuits, where level 3 saves 13.33 % against level 2. It proves the PSEL4 output on 17 of 20. Our level 2 compiles, with and without ZX, give the same counts as the official pytket-quantinuum pass on 445 rows.

## Relevance to quantum computing

Adders sit in the modular arithmetic of Shor factoring and in arithmetic for derivative pricing (Chakrabarti et al., arXiv:2012.03819). PSEL4 lowers the cost of these subroutines on H2 today with no change to the user's code. [O]

## Potential impact

For a cost-bound H2 user PSEL4 is a drop-in that cuts HQC by 15.7 % on this benchmark at 5.08 times the total compile time of level 2, or 3.03 HQC saved per extra second. [O] For accuracy-bound work result 3 says to check fidelity first. [O] This motivates the finals goal, a learned and fidelity-aware selector. [O] A first classifier on input-circuit features does not beat constant choices on held-out families (App.). The finals model therefore needs structural features and emulator labels. [O]

**Limits.** No user interview. The ZX-only gain is small. Two family C level 3 outputs and three PSEL4 outputs are unproven. In the ledger runs the level 3 check stopped at 12 qubits. HQC is the formula estimate. Emulator only, no hardware run (34 H2-2E jobs, 8983.4 HQC). Earlier vbe_adder_3 tests used all-zero inputs (pooled Holm p = 0.052 over three circuits). The T-count floor is the Gosset et al. bound on 24 circuits of at most 5 qubits. The mechanism analysis lacks 6 circuits.

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Report `report.pdf`, appendix `report_full.pdf` (App.), code `code.zip`, evidence `EVIDENCE.md`.

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
