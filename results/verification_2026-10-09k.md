# Verification 2026-10-09k: commit 07e7449 (stronger baselines, confirmatory H2-2E test, Gosset attribution, one-pager and slides)

Verifier: independent agent that did not produce the work. Scope: `git diff db9ea16 07e7449` and the package rebuilt in 36daf11. No tracked file was edited. Scratch scripts were kept outside the repository.

## Verdict

PASS WITH ISSUES. [O]

Every number checked in Table SB, the confirmatory test, the one-pager and the figure recomputes exactly or within bootstrap noise. [F] The citations to arXiv:1308.4134 are accurate. [F] The issues are framing problems. The pitch headline still leads with a per-circuit saving against level 2 on a circuit where level 3 alone beats PSEL by 43 %. The documents also disagree on whether the post-hoc repeats-only test or the pooled three-circuit test is the headline emulator result. [O]

## a. Strong baselines (Table SB and surrounding sentences)

- [F] I recomputed every total from `results/strong_baselines.csv` (210 rows, one row per circuit and variant, 2 timeouts) plus the stored P0/P2/PSEL columns of `value/selector_ledger_circuits.csv` and `value/family_C_selector.csv`, using my own code. All of these match: L2, L3, ZXG, QK3, PSEL, P2 and QK3L1 totals, saved % vs L2 and vs L3, BEST (1894.8 and 18797.2), PSEL vs BEST (-11.89 %, -8.69 %), PSEL3 totals and savings (3.49 %, 2.34 %), L3 vs L2 (13.71 %, 23.16 %), unique-lowest win counts (B1: L3 11, PSEL 3; C: L3 9, PSEL 6), tied counts (C: L2 5, PSEL 11) and the 15-circuit B1 figures (PSEL 4.79 % vs L2, -5.78 % vs L3).
- [F] L2 equals the stored P0 on all 35 circuits (max abs difference 0). Stored PSEL equals min(P0, P2) on all 35.
- [F] All 88 B1 rows with status ok have check_ok = True (42 unitary, 46 statevector). All outputs are native.
- [F] Spot check with the official pass `QuantinuumBackend("H2-1", api_handler=QuantinuumAPIOffline()).get_compiled_circuit(c, optimisation_level=k)` and my own HQC = 5 + (N_1q + 10 N_2q + 5 * 2n) / 5:

| circuit | L2 (mine) | L2 (CSV) | L3 (mine) | L3 (CSV) |
|---|---|---|---|---|
| tof_3 (B1) | 48.8 | 48.8 | 46.4 | 46.4 |
| mod5_4 (B1) | 68.4 | 68.4 | 41.0 | 41.0 |
| vbe_adder_7 (C) | 370.4 | 370.4 | 232.2 | 232.2 |

## b. Confirmatory H2-2E test

- [F] I simulated the ideal outputs myself with a Qiskit Statevector of the source QASM. vbe_adder_3 has one outcome, 0000000000. grover_5 is uniform over 64 states (1/64 each). The payload bit strings match the ideal support only under reversed Qiskit order, so the payloads use the big-endian convention.
- [F] Summed r2 to r4 counts, 3000 shots per cell: vbe_adder_3 F_H 0.951333 (P0) and 0.964000 (P2). grover_5 F_H 0.866337 (P0) and 0.866730 (P2). The per-run F_H stored in each payload also matches my recomputation.
- [F] vbe_adder_3: dF 0.012667, binomial sd 0.005196, z 2.4377, two-sided p 0.014782, one-sided p 0.007391. These are identical to `results/h22e_confirmatory.csv`.
- [F] grover_5 with my own 4000-sample multinomial bootstrap (seed 20261008, one generator per cell): sd 0.00628 for both pipelines (reported 0.00624 and 0.00625), sd of dF 0.00888 (reported 0.00883), z 0.044 (reported 0.0445), p 0.965 (reported 0.9645). The differences are within bootstrap noise.
- [F] Holm over the two circuits gives 0.0296 for vbe_adder_3 and 0.965 for grover_5. This matches the reported 0.030 and 0.96.
- [F] Timing: commit eb0465f is dated 2026-10-08 21:19:51 +0200, which is 19:19:51 UTC. The text of that commit contains "predicted gains of 0.0170, 0.0055 and 0.0228". The first repeat job in `results/emulator_jobs.csv` is at 2026-10-08T21:13:30Z and the last is at 21:19:24.9Z. All 12 repeats fall after the commit. [O] Git commit dates are set by the author's clock and are not externally anchored. A judge may note this.
- [F] h22e_pooled.py and Table E3 entered in 11f86d7 (2026-10-08 23:55 +0200). The md and reports disclose that the choice to report r2 to r4 alone came after that.

## c. arXiv:1308.4134 (fetched v1 PDF and read the text)

- [F] Section 2.3 "Channel representation, and modding out global phases" defines U^_rs = Tr(P_r U P_s U^dagger) / 2^n. Correct.
- [F] Definition 1 (Section 4) defines the smallest denominator exponent sde. For a matrix, sde is the maximum over its entries. Correct.
- [F] Theorem 1 (Section 4) states T(U) = sde(U^) for single-qubit U. Correct.
- [F] Proposition 1 (Section 3) gives U = e^{i phi} prod_{i=T(U)}^{1} R(P_i) C_0 with exactly T(U) factors. The paper states no numbered n-qubit lower bound. Correct as stated in the reports.
- [F] Section 6 (Conclusions): "the sde of the channel representation of the Toffoli gate is 2 but its T-count is 7". Correct. T-count 7 is proven in Section 5.3.
- [F] The reference "Quantum Inf. Comput. 14 (2014)" is correct.

## d and e. Findings

Ordered by severity, then by document order.

### 1. Major: slide 1 headline claims up to 50.4 % saving with no baseline named

- File: `report/presentation/presentation.tex` line 48.
- Evidence: the slide reads "It saves up to 50.4\,\% HQC on arithmetic circuits." It names no baseline. [F] The 50.4 % is rgqft_mult_6 against L2. On that circuit L3 alone gives 1540.4 HQC and PSEL gives 2206.6, so PSEL costs 43.25 % more than L3 (recomputed). Teleport_reduce before L3 (P2L3, 1604.8) does not help there either. [O] A judge who reads the Table SB slide will treat this headline as an overclaim.
- Proposed fix: name the baseline and add the level-3 result to the headline. Example: "It saves up to 50.4 % HQC against pytket's default level 2. Against level 3 a ZX stage still saves 2.34 % on family C." Alternatively, lead with PSEL3.

### 2. Major: the one-pager headline and its two examples are all beaten by level 3

- File: `report/one_page_summary.md` lines 3 and 21. The same text appears in `submission/one_page_summary.pdf`.
- Evidence: line 3 says "saves up to 50.4 % HQC against that pass on arithmetic circuits" and is correctly qualified to the default pass. Line 21 cites rgqft_mult_6 (50.4 %) and vbe_adder_18 (23.6 %). [F] Against L3, PSEL costs 43.25 % more on rgqft_mult_6 and 24.44 % more on vbe_adder_18. On vbe_adder_7, the circuit run on the emulator, it costs 26.79 % more. The stronger-baselines bullet (line 26) gives only the family C total (-8.37 %). It omits B1 (-9.92 %) and does not say that L3 is the lowest compiler on 11 of 14 B1 circuits and 9 of 20 family C circuits. [O] The page is literally true but leads with circuits where pytket level 3 alone does better than PSEL.
- Proposed fix: in the headline or the first bullet, add one sentence saying that pytket level 3 alone costs less than PSEL in total on both families (-9.92 % and -8.37 %) and that ZX before level 3 still saves 3.49 % and 2.34 %. Alternatively, drop the per-circuit maxima from the headline.

### 3. Moderate: documents disagree on which emulator test is primary

- Files and lines: `report/report_v5.md` line 732 vs lines 154, 738 and 1105. `report/report_short.md` line 16 (Summary) and line 342 (Limitations) vs line 236. `report/presentation/presentation.tex` line 223 (slide 9 title).
- Evidence: report_v5 line 732 says "[O] The two-sided confirmatory test is the primary test of a P2 gain on H2-2E. It resolves the vbe_adder_3 gain". Section 1.3 (line 154), the closing [O] of 3.7.1 (line 738) and Section 7 (line 1105) still conclude only from the pooled test ("not significant at 0.05 after correction over all three") and do not mention the confirmatory result. report_short's Summary and Limitations do the same, while its Section 3.2 (line 236) reports the confirmatory test. Slide 9's title says "H2-2E resolves a gain on vbe\_adder\_3 in the repeats". [F] The analysis that drops r1 was chosen after the pooled result and the r2 to r4 data were known, so it is not a pre-specified confirmatory test. Only the circuit choice preceded the data.
- Proposed fix: choose one framing everywhere. The defensible framing is that the pooled test over three circuits is the reported result (Holm 0.052). The repeats-only analysis is a post-hoc sensitivity check that agrees in sign and size (Holm 0.030 over two). Drop "primary" from line 732. Retitle slide 9, for example "vbe_adder_3 gains in every analysis, but misses 0.05 over three circuits". Add one sentence on the sensitivity check to the report_short Summary and to both Limitations sections.

### 4. Moderate: the one-pager's Limits line omits that the repeats-only test was chosen post hoc

- File: `report/one_page_summary.md` line 29.
- Evidence: the line reads "P2 beats P0 on vbe_adder_3 in the repeats run after the circuit was chosen (Holm p = 0.030 over two circuits), not in the pooled test over three (0.052)". The post-hoc choice of analysis is disclosed in slide 9, SUMMARY.md line 79 and report_short line 236, but not here.
- Proposed fix: append "The repeats-only analysis was chosen after the pooled result was known."

### 5. Moderate: report_v5 never mentions the level-3 caveat outside Section 3.8.1

- File: `report/report_v5.md`, the Section 1 summary bullets (lines 20 to 30) and Section 7 Limitations (line 1093 onward).
- Evidence: report_short has it in its Summary (line 16) and Limitations (line 341), and SUMMARY.md has it at line 75. [F] `grep "level 3"` in report_v5 matches only lines 812 to 823. The technical appendix therefore states its savings without the caveat everywhere except 3.8.1.
- Proposed fix: add the report_short line-341 sentence to report_v5 Section 7 and one sentence to the Section 1 H2-cost bullet.

### 6. Minor: a stale statement in report_v5 Section 7

- File: `report/report_v5.md` line 1105.
- Evidence: "vbe_adder_3 at 4000 shots per pipeline is the only emulator comparison of P2 against P0 with z above 2." The r2 to r4 comparison (z = +2.44) is now also reported. It uses a subset of the same data.
- Proposed fix: add "and its repeats-only subset (z = +2.44)".

### 7. Minor: a property attributed to Gosset et al. Proposition 1 that the proposition does not state

- File: `report/report_v5.md` line 240. The same idea appears in `report/report_short.md` line 149.
- Evidence: "That proposition writes the unitary as a Clifford times one factor R(P) per T gate, and each factor raises the exponent by at most one." [F] Proposition 1 gives the factorisation only. The "at most one" step is not stated there for n qubits. It is a short derivation from the entries of the channel of R(P), which lie in {0, ±1, ±1/sqrt 2}. The overall attribution is correct.
- Proposed fix: "...one factor R(P) per T gate. The channel of each factor has sde at most 1, so the exponent grows by at most one per factor."

### 8. Minor: figure label "0.0" and an overlapping reference line

- File: `report/figures/fig_hqc_saved.png`, produced by `value/fig_hqc_saved.py`.
- Evidence: [F] the values match `value/family_C_selector.csv` to one decimal on all 20 bars, and the 7.47 % pooled line recomputes. mcx_b95_54 is labelled "0.0" (the saving is 0.02 %, PSEL picks P2). The caption says "A zero bar means PSEL keeps P0", which a reader can misread for that bar. The dashed 7.47 % line also runs through the "0, PSEL keeps P0" labels of the MCX group. This is cosmetic.
- Proposed fix: print two decimals for values below 0.1 (for example "0.02"), and stop the dashed line above the MCX zero-labels or give the labels a white background that covers the line.

## d. Other checks that passed

- [F] `submission/one_page_summary.pdf` is 1 page. It embeds the figure (1520 x 920 JPEG, 305 ppi), and the rendered page shows the figure legibly.
- [F] One-pager numbers recomputed from the CSVs and payloads: 4104.4 HQC and 16.7 %, rgqft_mult_6 50.36 %, vbe_adder_18 23.63 %, multiplier share 81.77 %, QFT adders P2 +22.12 %, 1057.2 HQC avoided on the QFT adders, 20 H2-2E payloads summing to 6598.0 HQC, and vbe_adder_7 F_H 0.886 (P0) and 0.897 (P2).
- [F] Slide 12's "24 test files, seven as scripts and seventeen under pytest" matches `run_tests.sh` (24 run lines, 7 without pytest). Slide 5b embeds the figure as a vector PDF, and its text is extractable from `submission/presentation.pdf`.
- [F] Slide 10's limitation and report_short Summary and Limitations state the level-3 numbers correctly.
- [F] No remaining novelty claim for the floor was found. report_v5 lines 122, 238, 240, 464, 466 and 1109, report_short lines 149, 269 and 299, SUMMARY.md line 57, one-pager line 25 and slide 8 all attribute the bound to Gosset et al. and state that it is not new.
- [F] Working tree clean after verification, apart from this file.
