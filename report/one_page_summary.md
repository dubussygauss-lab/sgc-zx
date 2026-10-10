# PSEL4 is a drop-in auto level for Quantinuum H2 that was never costlier than the default compile on 217 benchmark circuits

**PSEL4, a cost-aware auto level that compiles each circuit four ways and keeps the cheapest checked result, needs 15.7 % less HQC than pytket-quantinuum's default level 2 on our 217-circuit benchmark and costs more on none. A team that spends the Standard Plan's 10,000 HQC a month on this mix frees 1,573.3 HQC, worth USD 19,666 a month (workload assumption). [O]**

<style>table{border-collapse:collapse;margin:0.3em 0;font-size:9.8pt}th,td{border-bottom:1px solid #bbb;padding:1px 8px;text-align:left}th:nth-child(n+2),td:nth-child(n+2){text-align:right}</style>

## Problem statement

A job on Quantinuum H2 is billed in HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. pytket-quantinuum compiles at optimisation level 2 by default. Level 3 and ZX rewriting can each lower the HQC of a circuit or raise it. A cost-bound user needs the cheapest correct compile of each circuit without trying every option by hand. [O]

## Approach

PSEL4 compiles each circuit four ways: level 2, level 3 and PyZX teleport_reduce before each. Each candidate is checked against its input as a full unitary up to 8 qubits and on 64 random computational basis inputs (including all-zero) from 9 to 20 qubits. Above 20 qubits family C relies on PyZX miter proofs (result 2). PSEL4 drops a candidate that fails and keeps the lowest HQC. It is pytket's `PassSelector` pattern with HQC as the metric.

## Key results

**1. Cost: level 3 adoption made safe.** Total HQC at 1000 shots per circuit.

| Policy, 217 circuits | Total HQC | Saved vs level 2 | Circuits costlier than level 2 | Largest per-circuit loss |
|---|---|---|---|---|
| Always level 2 (default) | 58,837.2 | 0 | 0 | none |
| Always level 3 | 50,632.2 | 13.95 % | 45 | 12.95 % (gf2_pow_4_mult) |
| PSEL4 | 49,580.6 | 15.73 % | 0 | none |

Always level 3 gives 13.95 points of the saving and per-circuit selection plus ZX give 1.79 points. Against the per-circuit cheaper of level 2 and level 3, PSEL4 saves 679.6 HQC (1.35 %). Always level 3 loses 372.0 HQC on its 45 costlier circuits. PSEL4 loses on none.

**2. Correctness.** All 83 PSEL4 picks with 9 to 20 qubits pass the 64-basis-input check, as do 187 of 187 required candidates and 142 of 142 others. Negative controls fail as they should. A PyZX miter proves the PSEL4 output equal to its input on 17 of 20 family C circuits. MQT QCEC 3.10.2 proved none of the other three. Its ZX checker ("probably_not_equivalent") and alternating checker ("no_information", or killed on hrs_mult_5) were inconclusive and returned no counterexample on any pair. The ZX checker gives the same verdict on cdkm_adder_10, whose output PyZX proved. A conservative variant keeps the cheapest verified candidate, else the default level 2 output flagged "default, unverified" (only hrs_mult_5). It saves 12.25 % against level 2 and is costlier than level 2 on 0 circuits. It is costlier than level 3 on 2 circuits whose level 3 output is itself unverified.

**3. H2-2E emulator.** The HQC saving carried over to cost per correct answer in 6 of 6 pairs because accuracy did not fall on average (pooled HQC ratio 0.8264 divided by accuracy ratio 1.0002 gives R = 0.8262). The one significant accuracy loss is cdkm_adder_10 under level 3 (0.8267 against 0.8692, z = -2.90). Three of six pairs compare P2, the earlier selector's pick.

**4. Mechanism.** Level 3 wins mainly through two-qubit resynthesis by GreedyPauliSimp, and two-qubit gates dominate HQC. ZX phase teleportation removes non-Clifford rotations that level 3 keeps and saves a further 3.21 % over the cheaper level on family C.

## Relevance to quantum computing

Adders sit in the modular arithmetic of Shor factoring and in arithmetic for derivative pricing (Chakrabarti et al., arXiv:2012.03819). PSEL4 lowers the cost of these subroutines on H2 today with no change to the user's code. [O]

## Potential impact

A team that spends 10,000 HQC a month on this mix saves USD 19,666 a month at the Standard Plan average. The full ledger saving of 9,256.6 HQC is worth USD 95,289 to 115,707 at the Azure plan averages. [O] Drop-in use: `python3 pipelines/pass_select.py --psel4 <circuit.qasm>`, at 5.08 times the compile time of level 2. Finals goal: a fidelity-aware learned selector that keeps the per-answer saving and protects accuracy where users need it, as on cdkm_adder_10. [O]

**Limits.** No user interview. Emulator only (34 H2-2E jobs, 8983.4 HQC). HQC is the formula estimate. Three PSEL4 and two level 3 family C outputs are unproven. On draper_adder_28 the PSEL4 pick starts from angles PyZX rounded by up to 1.50e-06 rad. The ledger run checked level 3 only up to 12 qubits. The mechanism analysis lacks 6 circuits.

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Report `report.pdf`, appendix `report_full.pdf`, code `code.zip`, evidence `EVIDENCE.md`.

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
