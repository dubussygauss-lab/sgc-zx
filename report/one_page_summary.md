# PSEL4 compiles each H2 circuit four ways and keeps the cheapest

**PSEL4 is a drop-in replacement for pytket's default compile on Quantinuum H2 that by construction never costs more HQC than pytket level 2 or level 3 and saves 10.22 % HQC against the default level 2 on 17 arithmetic and oracle circuits with proven outputs.**

<style>table{border-collapse:collapse;margin:0.3em 0;font-size:9.8pt}th,td{border-bottom:1px solid #bbb;padding:1px 8px;text-align:left}th:nth-child(n+2),td:nth-child(n+2){text-align:right}</style>

## Problem statement

A job on Quantinuum H2 is billed in HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000 (App. 1.2). Arithmetic and oracle subroutines run on H2 from a fixed HQC budget. pytket's default is optimisation level 2. Level 3 and ZX rewriting can each lower the HQC of a circuit or raise it. The user needs the cheapest correct compile of each circuit without running every option by hand. [O]

## Approach

PSEL4 compiles each circuit four ways. These are level 2, level 3 and PyZX teleport_reduce before each. It drops a candidate that fails its checks and keeps the lowest HQC. Level 2 and level 3 are always candidates. The guarantee therefore holds on every circuit where both levels pass the checks. It is a design property and the ledger confirms it on 217 circuits. PSEL4 is pytket's `PassSelector` pattern with HQC as the metric.

## Key results

| Circuit set | HQC saved vs level 2 | ZX-only, vs cheaper of L2 and L3 |
|---|---|---|
| Family C, 17 arithmetic and oracle circuits with proven output (20 to 56 qubits) | 10.22 % | 0.26 % |
| Family C, all 20 circuits (3 picks unproven) | 25.85 % | 3.21 % |
| B1, 15 Clifford+T benchmarks | 10.65 % | 0.49 % |
| A, 180 Trotter circuits | 2.88 % | 0 |
| Grover use case | 33.36 % | 0.44 % |

- **Split.** Most of the saving comes from choosing level 3 where it is cheaper. The ZX part is the saving on top of the cheaper of the two levels per circuit.
- **Guard.** Running ZX blindly before level 2 costs 6.27 % more HQC on 180 Trotter circuits and 22.1 % more on 3 QFT adders. pytket's ZXGraphlikeOptimisation before level 2 costs 59.22 % more on 14 B1 circuits. Qiskit level 3 rebased to H2 costs more than level 2. PSEL4 never pays these losses.
- **Correctness.** Outputs up to 8 qubits are checked as full unitaries. From 9 to 20 qubits the check compares the output state on the all-zero input only. A PyZX miter proves 17 of the 20 family C outputs equal to their input. Our level 2 compiles, with and without ZX, give the same counts as the official pytket-quantinuum pass on 445 rows.
- **Emulator.** 22 H2-2E jobs ran, with job IDs in `EVIDENCE.md`. On a non-zero input fixed in advance the 22-qubit adder vbe_adder_7 returns the correct sum 139 in 0.883 of shots under level 2 and 0.901 under level 3, the PSEL4 pick (z = 1.30, not resolved).

<img src="figures/fig_hqc_saved.png" alt="HQC saved by the earlier two-candidate selector against level 2 per family C circuit" width="56%">

<small>Figure 1. Earlier two-candidate selector (level 2 or ZX then level 2) against level 2, per family C circuit. A zero bar means it keeps level 2. Data `value/family_C_selector.csv`, script `value/fig_hqc_saved.py`.</small>

## Relevance to quantum computing

Adders sit in the modular arithmetic of Shor factoring (App. 1.4) and arithmetic in derivative pricing (App. 1.5, Chakrabarti et al., arXiv:2012.03819). PSEL4 lowers the cost of these subroutines on H2 today with no change to the user's code. [O]

## Potential impact

A user on the default level 2 gains the full saving at the price of three extra compilations. A user already on level 3 gains a small exact ZX saving and a guard against ZX losses. [O] Learned ZX rewriting is the finals roadmap and the ledger rows are its training data. [O] A first classifier on input-circuit features does not beat constant choices on held-out families (App.). The finals model therefore needs structural features. [O]

**Limits.** No user interview. The ZX-only gain is small. Two unproven picks, hrs_mult_5 and draper_adder_28, give 87.6 % of the family C saving against level 3. The P2 over P0 fidelity gain on vbe_adder_3 has pooled Holm p = 0.052 and earlier emulator inputs were all-zero. HQC is the formula estimate. No hardware run.

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Report `report.pdf`, appendix `report_full.pdf` (App.), code `code.zip`, evidence `EVIDENCE.md`.

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
