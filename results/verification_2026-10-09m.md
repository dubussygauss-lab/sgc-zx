# Verification 2026-10-09m (commits bcee97a content, 92d3690 package)

Independent verifier, 12-minute budget. No tracked file edited.

## Verdict: PASS WITH ISSUES

No number checked is wrong. Three Medium issues concern framing a judge would notice: the random-gate comparator, the one-pager guarantee omitting the 20-qubit check limit, and the L3-first one-pager against an L2-first report.

## What was checked

- [F] `python3 value/zx_classifier.py` rerun (exit 0). `git status` clean afterwards, so `value/zx_classifier.md/.csv` reproduce byte for byte.
- [F] Report numbers match the regenerated table: LOFO logreg bal. acc 0.433, gbt 0.398, regret 2139.6, gated 46.6, skipped 123. GCV logreg 0.749 / 3345.8 / 2244.8 / 109, gbt 0.686 / 1237.8 / 139.0 / 137. Random-gate 2591.7. Family A 37.0 vs 27.6 with 108 skips. Recomputed 46.6 / 57693.6 = 0.0808 % (reported 0.081 %).
- [F] "Within each family [GCV gbt] regret is never below the better constant choice": A 58.4 > 46.0, B1 1.4 > 0.4, B1x 120.8 > 0, B2/C/U equal. Holds. "No model beats the better constant on any held-out family" (LOFO): holds for logreg, gbt and gbt_reg.
- [F] Family label is not in `FEATURES` (`value/zx_classifier.py` line 47). GroupKFold is over `group`, and line 197 asserts train/test group disjointness for GCV. 38 groups. Cross-family groups (vbe_adder B1/C, grover B1/U, tof, barenco_tof, gf2 mult B1/B1x) are single groups, so they never straddle a GCV fold.
- [F] One-pager figures recomputed from `value/psel4_ledger.md` and `value/psel4_proven.md`: 0.80 % (82/10224.2 = 0.802), 3.50 % (660/18853.2), 87.6 % (578/660), 23.16 % (5681.8/24535), B1 0.73 % (102.4/13965.8), use case 0.44 % (7/1582), family A 1.74 % (282.2/16231.2), 6.27 % (1030.4/16422.6). All match.
- [F] `submission/one_page_summary.pdf` has 1 page (pdfinfo).
- [F] Holm values consistent across one-pager, slides, report_short 233-236, report_v5 732/743/749, SUMMARY 87 and `results/h22e_confirmatory.md`: pooled 0.035 (two circuits), 0.052 (three), repeats-only 0.030 (two).
- [F] 17 vs 18 proofs: 18 is the two-candidate PSEL pick (`results/family_C_equivalence.csv`), 17 the PSEL4 output (`value/psel4_proven.md`, QCEC added none). Every occurrence found names the selector. Slide line 287 states both.
- [F] References checked on arXiv abstract pages: 2311.18588 (Nägele, Marquardt, DOI 10.1088/2632-2153/ad76f7 = MLST), 2312.11597 (Riu, Nogué, Vilaplana, Garcia-Saez, Estarellas, DOI Quantum 2025-05-28-1758), 2307.10120 (Li, Peng, Mei, Lin, Wu, Padon, Jia), 2507.14434 (Chen, Liu, Xu, Li, Li, He, two-qubit count). Titles, authors and ids match. In-text numbering matches each document's list (report_short 3, 4, 14-20; report_v5 16-26).

## Findings (severity, then document order)

1. Medium. `report/report_short.md` 4.4, `report/report_v5.md` 3.8.2 line 867, `report/snippets/classifier_snippet.md` line 15. "against an expected 2591.7 HQC for a random gate that skips as many".
   - Evidence [F]: `random_gate()` (zx_classifier.py ~line 295) spreads the 123 skips uniformly over all 245 circuits, so it charges skips to family C (regret_always_P0 4104.4). The logreg skips fall in A (108), B1 (5) and B2 (10). A random gate with the same per-family skip counts has expected regret A 27.6 + B1 (5/15 × 743.6 = 247.9) + B2 0 = 275.5 HQC, against the model's 46.6 (A 37.0 + B1 9.6). The model still wins the stratified comparison, but by 228.9 HQC, all from B1, and it loses on A (37.0 vs 27.6). The pooled gap of 2545.1 HQC overstates this by about 11 times.
   - [O] A judge will read 2591.7 as the model's skill. Most of that gap is family allocation (the same effect the text itself names for GCV).
   - Proposed fix: replace the pooled comparator with the family-stratified one (275.5 HQC) or state both, and say the gain over it comes from 5 B1 circuits.
2. Medium. `report/one_page_summary.md` line 13 and slide 3 ("Answer", "Guarantee"). "It drops a candidate that fails its exactness check" with no statement that `pipelines/pass_select.py` runs no check above 20 qubits (`CHECK_MAX_QUBITS = 20`, line 49).
   - Evidence [F]: family C is 20 to 56 qubits, so on most of family C no candidate is checked online. `report_short.md` 1.1 states this limit. The one-pager and slides do not.
   - Proposed fix: add "No exactness check runs above 20 qubits" after the sentence on line 13 and in the slide 3 Answer bullet.
3. Medium. Framing mismatch between `report/one_page_summary.md` (title and headline: PSEL4 against level 3, 0.80 %) and `report/report_short.md` / `report_v5.md` (title "A pass selector keeps ZX rewriting only where it lowers the cost...", Summary headline PSEL 7.47 % against P0 = level 2, then "Against level 3 PSEL costs 8.37 % more").
   - Evidence [F]: lines 1-3 of the one-pager vs lines 1 and 16 of report_short. The user statement also differs ("arithmetic and oracle subroutines" vs "Clifford+T subroutines ... fault-tolerant machine", report_short 1.1).
   - [O] A judge opening report.pdf after the one-pager sees a different baseline and title. Proposed fix: either lead the report Summary with the PSEL4 vs L3 result, or have the one-pager say the report's headline is against L2.
4. Low. `report/one_page_summary.md` line 25 and `submission/SUMMARY.md` line 79. "skips 123 of 245 ZX compilations" sits next to "PSEL keeps P0 on 123 of 180 family A circuits" (SUMMARY 47, report_v5 100). Same number, different quantity. Proposed fix: none required, or write "123 of 245 second compilations" consistently as in report_short.
5. Low. `report/one_page_summary.md` line 25 "Learned gate" listed under Key results. [O] The gate loses to a stratified random gate on family A and does not beat constants. The bullet's second sentence discloses this. Acceptable. Optional: move to Limits or to Potential impact.
6. Low. `value/zx_classifier.md` line 19. States only B1x's LOFO split is not construction-disjoint. [F] C (vbe_adder shared with B1) and U (grover shared with B1) are also not construction-disjoint under LOFO. Proposed fix: name C and U too.
7. Low. `report/presentation/presentation.tex` slide 2, "On draper\_adder\_16 it costs 1,385.0 HQC against 906.8." The preceding bullet is about level 3, so "it" reads as level 3. [F] The figures are P2 vs P0 (report_v5 813). Proposed fix: "On draper\_adder\_16 P2 costs 1,385.0 HQC against 906.8 for level 2."
8. Low. Slide 3 "Why per circuit" uses P2, P0 and PSEL before slide 4 defines them. Proposed fix: "ZX before level 2 raises ... the two-candidate selector keeps level 2 on all 60."
9. Low. Related-work characterisations not confirmable from abstracts. [F] Abstract of 2311.18588 does not state the reward (node count). Abstract of 2312.11597 names two-qubit count only for the extended experiments, not "total". Abstract of 2307.10120 names neither Nam/IBM gate sets nor the 35.8 % / 33.9 % figures (report_v5 515). Status: Unverifiable within this check, not wrong. Proposed fix: give a section or table anchor for each in the reference notes (report_v5 1203-1205 already partly do).
10. Low. `report/report_short.md` 4.3 last sentences: "against the official pytket-quantinuum pass at optimisation levels 2 and 3". [F] Slide 4 says "Family C was not compiled with the official pass". The headline family C ledger is therefore against the team's P0/L3 reimplementation, checked equal to the official pass on A, B1, B1x, B2 only. Proposed fix: add "checked equal to the official pass on families A, B1, B1x and B2".

## Not checked

QCEC paragraph numbers beyond the summary counts (17 of 20, 0 proved by QCEC), slides after 3, report_full.pdf rendering, Quarl body figures.
