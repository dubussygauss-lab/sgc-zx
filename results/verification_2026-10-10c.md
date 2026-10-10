# Verification 2026-10-10c (commits a646fcc, b63d29f)

Independent verifier. No tracked file edited. Recomputation by own code from `value/psel4_ledger.csv`, `results/strong_baselines.csv`, `results/family_C_equivalence.csv` and `results/family_C_equivalence_psel4.csv` (not via `value/psel4_zx_only.py`).

**Verdict: PASS WITH ISSUES.** All headline numbers recompute. Titles and headline numbers agree across the five submission files. No weakness was removed. Two caveats are missing from the short-form documents (findings 1 and 2) and the Section 7 cross-reference in the summaries points to text that is not there (finding 3).

## (1) Recomputation

| Set | n | L2 | L3 | min(L2,L3) | PSEL4 | vs L2 % | vs L3 % | ZX-only % | ZX picks | stated | match |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C proven | 17 | 11296.8 | 10224.2 | 10168.2 | 10142.2 | 10.22 | 0.80 | 0.26 | 5 | 10.22 / 0.26 | [F] yes |
| C all | 20 | 24535.0 | 18853.2 | 18797.2 | 18193.2 | 25.85 | 3.50 | 3.21 | 7 | 25.85 / 3.21 | [F] yes |
| B1 | 15 | 15516.0 | 13965.8 | 13932.0 | 13863.4 | 10.65 | 0.73 | 0.49 | 5 | 10.65 / 0.49 | [F] yes |
| A | 180 | 16422.6 | 16231.2 | 15949.0 | 15949.0 | 2.88 | 1.74 | 0.00 | 0 | 2.88 / 0 | [F] yes |
| Grover | 2 | 2363.6 | 1582.0 | 1582.0 | 1575.0 | 33.36 | 0.44 | 0.44 | 2 | 33.36 / 0.44 | [F] yes |

- [F] hqc_PSEL4 equals the minimum of the four candidate columns on all 217 rows.
- [F] Unproven PSEL4 picks: draper_adder_28 (P2L3, timeout), hrs_mult_5 (P2, inconclusive), rgqft_mult_6 (L3, timeout). The 17 proven circuits span 20 to 56 qubits.
- [F] 87.6 %: hrs_mult_5 313.0 + draper_adder_28 265.0 of 660.0 HQC saved vs L3 = 87.58 %.
- [F] 59.22 %: ZXG 3558.6 vs L2 2235.0 on the 14 B1 circuits with ZXG status ok. ZXG on C +116.49 %, QK3 on B1(14) +25.24 %, QK3 on C +25.16 %, L3 vs L2 -13.71 % (B1 14) and -23.16 % (C), PSEL4 on B1(14) 18.29 / 5.31: all match slide 7.
- [F] 6.27 % (1030.4 / 16422.6, family A P2 vs P0) and 22.1 % (1057.2 HQC, draper_adder_10/16/28 P2 vs P0) match.
- [F] vbe_adder_7 PSEL4 pick is L3. z for 0.883 vs 0.901 at 1000 shots each = 1.297, stated 1.30.
- [F] Number provenance: every number of `report/one_page_summary.md` and `report/presentation/presentation.tex` (except the LaTeX options `169,11` and TikZ coordinate `2.35`) occurs in `report/report_v5.md`, `report/report_short.md`, `value/*.md` or `results/*.md`. `submission/check_summary_numbers.py` 174/174 found. `report/check_short_numbers.py` 537/537 found.

## (2)-(3) Overclaims and consistency

- [F] "Most of the saving comes from level 3" is stated in the one-pager (Split bullet), SUMMARY.md line 15, report_short.md Summary, report_v5.md Section 1, slide 1 and slide 5.
- [F] "By construction / design property, not a measured result" is stated in all five documents.
- [F] "3 picks unproven" is in the one-pager table, SUMMARY.md lines 13 and 25, report_short.md Summary, slides 5, 8 and 11.
- [F] "z = 1.30, not resolved" is in all five documents.
- [F] a646fcc changed no line of Section 7 in report_short.md (hunks at lines 1 to 48 only) or report_v5.md (hunks at lines 1 to 34 only). The removed Section 1 sentences on PSEL vs level 3 (9.92 %, 8.37 %, PSEL3 3.49 % / 2.34 %) survive in report_short.md Section 7 bullet 2 and report_v5.md Section 7 paragraph 1.
- [F] Title "PSEL4 compiles each H2 circuit four ways and keeps the cheapest" is identical in one_page_summary.pdf, presentation.pdf, report.pdf, report_full.pdf and SUMMARY.md line 5. Headline numbers 10.22, 25.85, 10.65, 2.88, 33.36, 0.26, 3.21, 0.49, 0.44, 59.22, 6.27, 22.1, 87.6, 1.30, 0.883, 0.901, 445, 217 occur in each of the four PDFs (pdftotext).
- [F] one_page_summary.pdf has 1 page. presentation.pdf has 13 pages. At 50 dpi no slide shows text running past a frame edge or overlapping another element.
- [F] submission/presentation.tex and .pdf are byte-identical to report/presentation/. submission/report.md equals report/report_short.md.

## Findings

Ordered by severity, then document order.

### 1. Moderate: one-pager and slide 8 drop the 12-qubit limit of the level 3 check
- File: `report/one_page_summary.md` line 27 ("Outputs are checked exactly up to 20 qubits.") and `report/presentation/presentation.tex` lines 188 to 191 (frame title "Outputs are checked exactly up to 20 qubits", bullet "PSEL4 checks every candidate up to 20 qubits.").
- Evidence: [F] report_short.md Summary, SUMMARY.md line 19 and report_v5.md Section 1 all add "In the PSEL4 ledger runs the check of the level 3 candidates stopped at 12 qubits." [F] report_v5.md Section 3.8.1 says "In these ledger runs exactness is checked up to 12 qubits." [O] Without that sentence, a reader of the one-pager or the deck takes the 20-qubit check to cover the L3 and P2L3 picks that produce most of the saving.
- Proposed fix: add the same sentence to the one-pager Correctness bullet and to slide 8. Alternatively, change the slide 8 bullet to "The selector checks up to 20 qubits. In the ledger runs the level 3 candidates were checked up to 12 qubits."

### 2. Moderate: the one-pager's "ZX part of the saving" column uses a different base from the column beside it
- File: `report/one_page_summary.md` lines 17 to 25.
- Evidence: [F] The column "HQC saved vs level 2" is relative to L2. "ZX part of the saving" is relative to min(L2, L3). On the level-2 base the additive split is 9.99 + 0.23 (C proven), 23.39 + 2.46 (C all), 10.21 + 0.44 (B1), 2.88 + 0 (A) and 33.07 + 0.30 (Grover). [O] Next to the vs-L2 column, a reader takes "part of the saving" as an additive share and overstates the ZX share. On C all the overstatement is 3.21 against 2.46. Slide 5 avoids this because it labels the column "ZX-only" and defines it.
- Proposed fix: rename the column "ZX saving over the cheaper level" (or "ZX-only, vs min(L2, L3)"). Alternatively, report the level-2-base split.

### 3. Minor: "Limitations (Section 7)" cites PSEL4 limits that Section 7 does not contain
- File: `report/report_short.md` line 28 (Summary) against lines 394 to 404. `submission/SUMMARY.md` line 25 ("Limitations (appendix Section 7)") against `report/report_v5.md` lines 1158 to 1184.
- Evidence: [F] Neither Section 7 states that three PSEL4 family C picks are unproven, the 87.6 % concentration, that the ZX-only gain is small, or that the vbe_adder_7 difference is unresolved. Section 7 discusses PSEL ("proven on 18 of its 20 circuits"). [F] These limits do appear elsewhere: report_short.md Summary and Section 3.2 line 268, report_v5.md Section 1 line 26 and Section 3.8.1 line 870, slide 11. Nothing was removed from the submission.
- Proposed fix: add one Section 7 bullet in each report. Suggested wording: "PSEL4 output is proven on 17 of 20 family C circuits. hrs_mult_5 and draper_adder_28 give 87.6 % of the saving against level 3. The ZX-only saving is 0.26 % on the 17 proven circuits. The vbe_adder_7 difference of L3 over P0 has z = 1.30 and is not resolved."

### 4. Minor: the one-pager Limits paragraph names two unproven picks without the third
- File: `report/one_page_summary.md` line 42 ("Two unproven picks, hrs_mult_5 and draper_adder_28, give 87.6 %").
- Evidence: [F] There are three unproven picks, and rgqft_mult_6 (L3) contributes 0 against L3. The table at line 20 says "3 picks unproven". [O] The wording can be read as "two unproven picks in total".
- Proposed fix: "Three picks are unproven. Two of them, hrs_mult_5 and draper_adder_28, give 87.6 % ..." (as in SUMMARY.md line 25).

### 5. Minor: two B1 PSEL4 figures in the deck
- File: `report/presentation/presentation.tex` line 171 (B1 with 14 circuits, hwb8 excluded: 18.29 / 5.31) against slide 5 (B1 with 15 circuits: 10.65 / 0.73).
- Evidence: [F] Both recompute and both are labelled. [O] A judge comparing slides 5 and 7 sees two B1 savings vs L2.
- Proposed fix: add "(10.65 % on all 15 with hwb8, slide 5)" to the slide 7 caption.

### 6. Minor: the one-pager's Qiskit sentence has no set qualifier
- File: `report/one_page_summary.md` line 26 ("Qiskit level 3 rebased to H2 costs more than level 2.").
- Evidence: [F] This holds on B1 (+25.24 % on 14 circuits, +29.11 % on 15) and on family C (+25.16 %) only. Qiskit level 3 was not measured on families A or the use case in `results/strong_baselines.csv`.
- Proposed fix: append "on B1 and family C".

### 7. Minor: stale build date and empty PDF metadata
- File: `submission/SUMMARY.md` line 5 ("This page was built on 9 October 2026").
- Evidence: [F] The page was rewritten in a646fcc, dated 2026-10-10 03:57 +0200. [F] All four submission PDFs have an empty Title field (pdfinfo).
- Proposed fix: update the date to 10 October 2026. Optionally, set the PDF Title metadata in build.sh.

### 8. Minor (judgement): the one-pager figure shows the earlier product
- File: `report/one_page_summary.md` lines 30 to 32.
- Evidence: [F] Figure 1 is the two-candidate PSEL against level 2. The caption says so. [O] It is the only figure on a page that leads with PSEL4, and its bars (up to 50 %) do not match the PSEL4 table.
- Proposed fix: keep it as is, or replace it with a per-circuit PSEL4 vs L2 / vs min(L2, L3) bar chart if one exists in `value/`. Do not create a new one without approval.
