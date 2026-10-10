# Verification 2026-10-10f: HQC per correct output, USD value, framing 3 package

Verifier: independent agent, no prior exposure to the work. Repository HEAD ba635bb. No tracked file edited.
Own scripts (scratch, not committed): a statevector simulator written from scratch (h, x, t, tdg, s, sdg, z, cx, ccx) and a recomputation from the raw payloads that does not import the repository code.

## Verdict: PASS WITH ISSUES (two minor framing issues, no numeric error)

## (1) HQC per correct output

- [F] 34 payloads under `results/emulator/nexus_H2-2E*/`, 26 used. Counts sum to shots in every payload. On every used payload K/shots equals the stored F_H to 1e-9.
- [F] Correct bitstrings came from the own simulator on the bench QASM files. Each source circuit (vbe_adder_3, hwb6, vbe_adder_7, vbe_adder_7_nz, cdkm_adder_10_i1..i3, modadd_2n_10_i1..i3) gives a single basis state with probability 1 (1e-14). The bitstrings match the ones the script uses. The observed mode equals that bitstring in all 26 used payloads.
- [F] Arithmetic decode. cdkm_adder_10_i1: a = 692, b = 435 (seed 20261011 redrawn), 692 + 435 = 1127 = 1024 + 103. The simulated output carries a = 692, sum bits = 103, cout = 1. vbe_adder_7_nz: simulated output equals `0001110011010001000000` (A = 28, B = 111).
- [F] Recomputed table (p_P0, p_alt, HQC per 1000 correct, R, delta interval) matches `value/hqc_per_correct.md` to every printed digit for all 6 pairs.
- [F] Pooled R = (2085.12/8556)/(2523.12/8554) = 0.82621, i.e. 17.38 % → 17.4 %.
- [F] cdkm_adder_10: R = 0.9203, delta interval [0.8896, 0.9521], saving 8.0 % (4.8 to 11.0 %).
- [F] Delta upper bound < 1 in 6 of 6 (largest: hwb6 0.9991).
- [F] grover_5: own simulation gives a uniform distribution over 64 outcomes (qubits 0 to 5 uniform, 6 to 8 zero), p_max = 0.015625. No single correct output exists, so the exclusion is justified. The bootstrap interval was not re-run (Unverifiable here, delta interval agrees).

## (2) USD value

- [F] Recomputed from `value/psel4_ledger.csv` (217 rows) with the csv module: 9256.6 HQC, 15.73 %, USD 95,289 to 115,707. 1051.6 HQC, 2.08 %, USD 10,825 to 13,145. 45 circuits, 372.0 HQC, USD 3,829 to 4,650. PSEL4/L2 = 0.8427, 1573.3 HQC per month, USD 19,666 (Standard) and USD 16,195 (Premium). All match.
- [F] Prices match report/report_short.md line 111.
- [F] One-pager "8983.4 HQC" over 34 jobs: recomputed 8983.44. "12.95 % (gf2_pow_4_mult)" recomputed 12.951 %.

## (3) Overclaims

- [F] "Three of six pairs compare P2, not the PSEL4 pick" is stated in report_short.md line 267 and Section 7 line 443, report_v5.md lines 852 and 1315, SUMMARY.md line 15, README.md line 6, slide 5 caption and the one-pager body. Emulator-only and the HQC formula estimate are stated in each. USD figures are labelled plan averages, and the monthly figure is labelled a workload assumption.
- [F] The cdkm accuracy drop (0.8267 against 0.8692, z = -2.90) is visible in the one-pager, slides 5, 9 and 10, SUMMARY.md, report and appendix.
- [F] Section 7 of report_short.md and report_v5.md: no bullet removed against 1b54085. One bullet was renamed ("Cost is not fidelity" became "Selection on cost" or "Accuracy of the cheaper pick") with its content kept, and one bullet was added.
- [F] No headline says PSEL4 itself was compared in all six pairs.

## (4) Package

- [F] one_page_summary.pdf has 1 page. presentation.pdf has 11 pages, all viewed, with no clipping. The headline numbers (17.4 %, 0.8262, 6 of 6, 0.9203, 8.0 %, 15.7 %, 95,289 to 115,707, 9,256.6, 1,573.3, 19,666, 372.0) agree across the one-pager, slides, report.pdf, report_full.pdf and SUMMARY.md. No conflicting value was found. submission/report.md is byte-identical to report/report_short.md.

## Findings

1. Minor. `report/one_page_summary.md` line 3 (also `submission/one_page_summary.pdf` headline) and `report/presentation/presentation.tex` line 60 (title slide).
   - [O] Problem: "PSEL4 needs 15.7 % less HQC ... and on the H2-2E emulator the cheaper compile needs 17.4 % fewer HQC per correct answer" places the 17.4 % next to PSEL4. A judge who reads only the headline can attribute it to PSEL4. In three of the six pairs the compile is P2, and the body text is the only place that says so.
   - Proposed fix: write "the lower-HQC compile (the PSEL4 pick in 3 of the 6 pairs)" in the headline and on the title slide.
2. Minor. Slide 9 (Limitations), `presentation.tex`.
   - [F] Problem: the slide does not state the P2 caveat or the one-binomial pooling caveat. Both appear only in the slide 5 caption.
   - Proposed fix: add one bullet to slide 9.

Not checked (outside scope or time): slide 2 and slide 7 to 8 figures (5.08, 3.03, 6.27 %, 3.21 %, 656/746, proofs). The parametric bootstrap intervals (16.7 to 18.1 %) were not re-run.
