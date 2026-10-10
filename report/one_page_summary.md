# PSEL4 is a drop-in auto level for Quantinuum H2 that was never costlier than the default compile on 217 benchmark circuits

**PSEL4, a cost-aware auto level that compiles each circuit four ways and keeps the cheapest checked result, needs 15.7 % less HQC than pytket-quantinuum's default level 2 on our 217-circuit benchmark and costs more on none. A team that spends the Standard Plan's 10,000 HQC a month on this mix frees 1,573.3 HQC, worth USD 19,666 a month (workload assumption). [O]**

<style>table{border-collapse:collapse;margin:0.3em 0;font-size:9.8pt}th,td{border-bottom:1px solid #bbb;padding:1px 8px;text-align:left}th:nth-child(n+2),td:nth-child(n+2){text-align:right}</style>

## Problem statement

A job on Quantinuum H2 is billed in HQC = 5 + N_shots (N_1q + 10 N_2q + 5 N_SPAM) / 5000. pytket-quantinuum compiles at optimisation level 2 by default. Level 3 and ZX rewriting can each lower the HQC of a circuit or raise it. A cost-bound user needs the cheapest correct compile of each circuit without trying every option by hand. [O]

## Approach

PSEL4 compiles each circuit four ways: level 2, level 3 and PyZX teleport_reduce before each. Each candidate is checked against its input as a full unitary up to 8 qubits and on 64 random computational basis inputs (including all-zero) from 9 to 20 qubits. Above 20 qubits family C relies on PyZX miter proofs (result 4). PSEL4 drops a candidate that fails and keeps the lowest HQC. It is pytket's `PassSelector` pattern with HQC as the metric.

## Key results

**1. Cost: level 3 adoption made safe.** Total HQC at 1000 shots per circuit.

| Policy, 217 circuits | Total HQC | Saved vs level 2 | Circuits costlier than level 2 | Largest per-circuit loss |
|---|---|---|---|---|
| Always level 2 (default) | 58,837.2 | 0 | 0 | none |
| Always level 3 | 50,632.2 | 13.95 % | 45 | 12.95 % (gf2_pow_4_mult) |
| PSEL4 | 49,580.6 | 15.73 % | 0 | none |

Always level 3 gives 13.95 points of the saving and per-circuit selection plus ZX give 1.79 points. Against the per-circuit cheaper of level 2 and level 3, PSEL4 saves 679.6 HQC (1.35 %). Always level 3 loses 372.0 HQC on its 45 costlier circuits. PSEL4 loses on none.

**2. Fidelity on the H2-2E emulator. The HQC-cheapest compile is not the most accurate.** Five pre-registered comparisons of the PSEL4 pick against level 2 on non-zero inputs (3 to 4 inputs each, 400 shots per program). The pick was significantly less accurate on 2 (cdkm_adder_10, level 3, 0.8267 against 0.8692, z = -2.90, and hwb6, ZX then level 3, 0.8883 against 0.9200, z = -2.64, Holm p = 0.0168), not different on 2 (modadd_2n_10 z = -0.22, vbe_adder_3 z = +0.51) and not significantly better on 1 (vbe_adder_7 z = +1.30). No pick was significantly more accurate. On cdkm_adder_10 the less accurate pick has fewer two-qubit gates (118 against 141) and lower two-qubit depth (65 against 122, post hoc), so neither HQC nor gate counts order fidelity on the emulator. The HQC saving still exceeds the accuracy loss: HQC per correct answer is lower for the pick in 5 of 5 pairs (8 of 8 including three earlier pairs of the two-candidate selector), pooled 18.1 % lower (R = 0.8192, bootstrap 95 % interval 0.8132 to 0.8254, HQC ratio 0.8170 over accuracy ratio 0.9973). PSEL4 serves cost-bound users. Accuracy-bound users need a fidelity-aware choice, which is the finals deliverable: a learned selector trained on this ledger and these emulator labels. [O]

**3. Mechanism.** HQC charges no Rz gate and bills every PhasedX at the same rate whatever its angle, so the T-count reduction ZX is best at has no HQC value on H2, and ZX can pay only through two-qubit gates, which level 3 already resynthesises by GreedyPauliSimp. ZX phase teleportation still removes non-Clifford rotations that level 3 keeps (656 against 746 on 14 B1 circuits). On top of the cheaper pytket level the ZX candidates add 0.26 % on the 17 proven family C circuits, 3.21 % on all 20, 0.49 % on B1 and nothing on family A. The gain falls with T-density (family C Spearman rho -0.64).

**4. Correctness.** All 83 PSEL4 picks with 9 to 20 qubits pass the 64-basis-input check, as do 187 of 187 required candidates and 142 of 142 others. Negative controls fail as they should. A PyZX miter proves the PSEL4 output equal to its input on 17 of 20 family C circuits. MQT QCEC 3.10.2 proved none of the other three. Its ZX checker ("probably_not_equivalent") and alternating checker ("no_information", or killed on hrs_mult_5) were inconclusive and returned no counterexample on any pair. A conservative variant keeps the cheapest verified candidate, else the default level 2 output flagged "default, unverified" (only hrs_mult_5). It saves 12.25 % against level 2 and is costlier than level 2 on 0 circuits.

## Relevance to quantum computing

Adders sit in the modular arithmetic of Shor factoring and in arithmetic for derivative pricing (Chakrabarti et al., arXiv:2012.03819). PSEL4 lowers the cost of these subroutines on H2 today with no change to the user's code. [O]

## Potential impact

A team that spends 10,000 HQC a month on this mix saves USD 19,666 a month at the Standard Plan average. The full ledger saving of 9,256.6 HQC is worth USD 95,289 to 115,707 at the Azure plan averages. [O] Drop-in use: `python3 pipelines/pass_select.py --psel4 <circuit.qasm>`, at 5.08 times the compile time of level 2. Finals goal: a fidelity-aware learned selector. Submission 1 provides the ledger (217 circuits by 4 candidates, checked) and the emulator labels (5 pre-registered PSEL4-pick pairs, 48 jobs). A first classifier on input-circuit features does not beat a constant choice (0.433 against 0.500), so the model needs compiled-candidate structural features and emulator labels. [O]

**Limits.** The PSEL4 pick was significantly less accurate on 2 of 5 pre-registered pairs. Per-answer intervals pool inputs and ignore between-run variation. 3 of 8 per-answer pairs use P2, the earlier selector's pick. No user interview. Emulator only (48 H2-2E jobs, 9971.8 HQC). HQC is the formula estimate. Three PSEL4 and two level 3 family C outputs are unproven. On draper_adder_28 the PSEL4 pick starts from angles PyZX rounded by up to 1.50e-06 rad. The ledger run checked level 3 only up to 12 qubits. The mechanism analysis lacks 6 circuits.

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Report `report.pdf`, appendix `report_full.pdf`, code `code.zip`, evidence `EVIDENCE.md`.

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
