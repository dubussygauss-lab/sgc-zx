# PSEL keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2

**PSEL is a drop-in pytket pass selector. It never costs more HQC than pytket's default pass when that pass passes its checks. It saves up to 50.4 % HQC against that pass on arithmetic circuits.**

Team Learned ZX Rewriting: C.-F. Kam, A. Mahasinghe, D. De Silva, N. Karunarathne, F. Cadet, M. Bessafi, K. De Silva. Quantinuum Singapore Grand Challenge, submission 1. Main report `report.pdf`, technical appendix `report_full.pdf` (cited as "App."), source `code.zip` with `README.md`, emulator evidence `EVIDENCE.md`.

## Problem statement

A run on Quantinuum H2 is billed in HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000 (App. 1.2). ZX rewriting placed before pytket's Quantinuum pass can lower this cost or raise it. Always run, it costs 6.27 % more HQC than pytket alone on 180 Trotter circuits and 22.1 % more on 3 QFT adders. A team with a fixed HQC budget cannot tell in advance which circuits gain. [O]

## Approach

PSEL (`pipelines/pass_select.py`) compiles each circuit twice. P0 is pytket-quantinuum's default pass at optimisation level 2. P2 is PyZX teleport_reduce followed by P0. PSEL drops a candidate that fails its exactness check and keeps the one with the lower HQC. Our P0 and P2 give the same counts as the official pytket-quantinuum pass on all 445 compiled rows of families A, B1, B1x and B2 (App. 2.2). A PyZX miter proves the PSEL output equal to its input on 18 of the 20 family C circuits (App. 3.8). PSEL is pytket's `PassSelector` pattern with HQC as the metric. The contribution is the measured cost ledger and the guard. [O]

## Key results

<img src="figures/fig_hqc_saved.png" alt="HQC saved by PSEL against P0 per family C circuit" width="68%">

<small>Figure 1. Family C per circuit. A zero bar means PSEL keeps P0. Data `value/family_C_selector.csv`, script `value/fig_hqc_saved.py`.</small>

- **Arithmetic.** On the 20 circuits of family C (20 to 56 qubits) PSEL saves 4104.4 HQC or 16.7 %. rgqft_mult_6 saves 50.4 % and vbe_adder_18 saves 23.6 %. The 15 circuits without continuous angles save 748.4 of 10,019.6 HQC or 7.47 %, and the 9 adders save 12.9 %. Two multipliers with continuous angles carry 81.8 % of the total.
- **Guard.** Against always running P2, PSEL avoids 1,076.4 HQC on the 180 Trotter circuits and 1,057.2 HQC on the 3 QFT adders.
- **Benchmarks.** On 15 Clifford+T circuits of family B1 PSEL saves 743.6 HQC or 4.79 %. hwb8 alone gives 84.5 % of that saving.
- **Use case.** On Grover search with 7 and 9 qubits PSEL saves 5.42 % and 4.96 % of the HQC. That buys 791 and 322 more shots within a 10,000 HQC budget.
- **Magic states.** The ZX stage removes 40.6 % of the written T-count on B1. On 20 synthesised Haar circuits of 2 and 3 qubits the channel bound of Gosset et al. (2014), evaluated exactly by the team, caps any further exact T saving at 0.3 % pooled.
- **Stronger baselines.** pytket's default is optimisation level 2. Against level 3 PSEL costs 8.37 % more on family C. Running teleport_reduce before level 3 and keeping the cheaper result still saves 2.34 % (App. 3.8.1).
- **Emulator.** 20 H2-2E jobs (6598.0 HQC by the cost formula) and 3 H2-Emulator jobs ran, with job IDs in `EVIDENCE.md`. vbe_adder_7 ran under P0 and P2 with Hellinger fidelity 0.886 and 0.897.

**Limits.** No user interview. Family C is count-only apart from one emulator run. No hardware run. On the emulator P2 beats P0 on vbe_adder_3 in the repeats run after the circuit was chosen (Holm p = 0.030 over two circuits), not in the pooled test over three (0.052). Inputs are all-zero.

## Relevance to quantum computing

The cited literature places adders in the modular arithmetic of Shor factoring (App. 1.4) and arithmetic in derivative pricing (App. 1.5, Chakrabarti et al., arXiv:2012.03819). On a surface code each T gate consumes one magic state (Litinski, arXiv:1808.02892). PSEL lowers the cost of these subroutines on H2 today. [O]

## Potential impact

At the Azure Quantum plan averages of USD 12.50 and 10.29 per HQC (App. 1.5) the 748.4 HQC saved on family C is worth about USD 7,700 to 9,400 at 1000 shots per circuit. The 1,076.4 HQC avoided on the Trotter circuits is worth about USD 11,100 to 13,500. [O] PSEL costs one extra compilation. Learned ZX rewriting is the finals goal. A model will predict which ZX rewrites lower HQC, and the P0 and P2 rows of the PSEL ledger are its training data. [O] The finals plan runs 4364 shots per pipeline on vbe_adder_3 at 1147.3 HQC, with power 0.80 if the emulator gain holds on hardware (App. 6). [O]

<small>Untagged statements are facts checkable in the repository. [O] marks a judgement.</small>
