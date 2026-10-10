# Independent verification of fddb264 / ce4b43e (PSEL4 reframe)

Verifier: agent that did not produce the work. Date 2026-10-10. Time box 15 min. No tracked file edited.

## Verdict: PASS WITH ISSUES

Every requested number reproduces from the CSVs and payloads with my own code. No number is wrong. Issues are wording and consistency (one Medium, four Low).

## 1. Recomputation [F]

| Claim | Recomputed | Source | Result |
|---|---|---|---|
| Always L2 / L3 / PSEL4 HQC | 58,837.2 / 50,632.2 / 49,580.6 | value/psel4_ledger.csv (217 rows) | match |
| L3 saving, PSEL4 saving | 13.945 %, 15.733 % | same | match (13.9, 15.7) |
| L3 costlier than L2 | 45 circuits | same | match |
| PSEL4 = min(P0,P2,L3,P2L3) | 0 mismatches. PSEL4 > L2 on 0, > L3 on 0 | same | match |
| gf2_pow_4_mult L3 loss | (244.2-216.2)/216.2 = 12.951 % | same | match |
| Compile-time ratio, HQC/s | 3475.56/683.86 = 5.082. 8468.0/2791.7 = 3.033 (215 circuits, t_wall) | family_A_counts, family_{B1,C}_counts, strong_baselines, psel4_runs | match |
| cdkm_adder_10 pooled p | L3 992/1200 = 0.8267, P0 1043/1200 = 0.8692, z = -2.904 | 6 payloads in nexus_H2-2E_famC_multi, expected bitstrings rebuilt from rng seed 20261011 | match |
| modadd_2n_10 z | 0.8383 vs 0.8417, z = -0.223 | 6 payloads | match |
| H2-2E jobs and HQC | 34 payloads with counts, sum hqc_estimate 8983.44 | results/emulator/nexus_H2-2E*/ | match |
| L3 saving on 18 proven | 14798.0 -> 12825.4, 13.330 % | family_C_equivalence_L3.csv + strong_baselines.csv | match |
| PSEL4 saving on 17 proven | 11296.8 -> 10142.2, 10.221 % | psel4_ledger.csv, unproven set from value/psel4_proven.md | match |
| Spearman, family C | rho -0.6417, p 0.00992 (n = 15) | mechanism_zx_l3.csv IN rows + ledger | match |
| Non-Clifford after P2 / L3, B1 | 656 / 746 (14 circuits) | mechanism_zx_l3.csv | match |
| Blind P2 on A, 3 QFT adders, ZXG on B1 | 6.27 %, 22.12 %, 59.22 % | mechanism table, ledger, strong_baselines.csv | match |

Pre-registration: results/h22e_multi_prereg.md touched only by 3e587bf (02:20:17Z). First famC_multi job 02:30:34Z. The primary metric (per-circuit pooled p, z) is what the reports call primary. Secondary pooled-over-both z -2.19 is in h22e_multi.md and not promoted. [F]

Not recomputed (time): Holm p 0.052 (traced to report_v5.md only), classifier 0.433/0.500, Qiskit 25.24/25.16 % (traced to strong_baselines.md lines 56, 102), 445 rows (traced to official_baseline.md).

## 2. Findings

| # | Severity | File / location | Observation and evidence | Proposed fix |
|---|---|---|---|---|
| 1 | Medium | report/one_page_summary.md line 3 (bold subtitle), mirrored in one_page_summary.pdf | [F] "by construction it never costs more than level 2 or level 3 on any circuit". The guarantee only holds where both candidates pass the check (as the Approach paragraph, SUMMARY.md and report_short.md say). The subtitle drops the qualifier. | "...and by construction never costs more than level 2 or level 3 where both pass its check" or state the measured fact "costs more than level 2 on 0 of 217 circuits". |
| 2 | Low | one_page_summary.md "Approach" and "Limits"; report_short.md 1.1 Guarantee | [F] Approach says each candidate is checked on the all-zero input "from 9 to 20 qubits". In the headline ledger run no candidate of the two 20-qubit family C circuits was checked: draper_adder_10 and modadd_2n_10 have status ok-unchecked, check_kind none for P0, P2 (family_C_counts.csv), L3 and P2L3 (psel4_ledger.csv). Limits says only "the level 3 check stopped at 12 qubits". Miter proofs cover both circuits, so no unproven output results. | Limits: "In the ledger runs no candidate above 12 qubits was checked. Family C outputs rest on the PyZX miter proofs." |
| 3 | Low | one_page_summary.md result 3 vs report_short.md Finding 3, SUMMARY.md Finding 3 | [F] One-pager: "Three pre-registered H2-2E tests". Report and SUMMARY: "Two pre-registered H2-2E tests ... with three non-zero inputs each", then vbe_adder_7 separately. Both counts are defensible (vbe_adder_7 has its own prereg) but the documents disagree. | Use one wording in all files, e.g. "Three pre-registered H2-2E tests (two multi-input, one single-input)". |
| 4 | Low | report/presentation/presentation.tex line 296 (slide 13) | [F] "Runs 28 test files ... rc=0 for all 28". submission/build_logs/tests_summary.txt has 33 entries, 33 rc=0 (commit ce4b43e says 33/33). | Change 28 to 33. |
| 5 | Low | report_full.pdf page 1 | [F] "report version 5 (9 October 2026)" while SUMMARY.md says the package was built on 10 October and report_full now carries the PSEL4 framing of fddb264. | Update the date. |
| 6 | Low | one_page_summary.md result 3, slide 7, report_short Finding 3 | [O] Two-qubit depth 65 vs 122 is a post-hoc quantity (results/h22e_multi_depth.md), not in the prereg. It sits next to the pre-registered result without a label. | Add "(post hoc)" after the depth figures. |

## 3. Overclaim checks

- Emulator-only: stated in one-pager Limits, report_short Limitations, report_v5 Section 7 ("Nothing in this report has run on hardware"), slide 11. Finding 3 conclusions are scoped to "the H2-2E emulator". Slide 7 title is unqualified but its caption and assessment carry the scope. [F]
- Check scope sentence (full unitary up to 8, all-zero input 9 to 20, none above 20) matches pipelines/compile.py check(unitary_max_qubits=8) and pass_select.py CHECK_MAX_QUBITS = 20. See finding 2 for the ledger-run gap. [F]
- Unproven outputs disclosed: two L3 (hrs_mult_5, rgqft_mult_6) and three PSEL4 (draper_adder_28, hrs_mult_5, rgqft_mult_6) in all documents. [F]
- Limitations present in report_short.md line 26 and Section 7 (line 461), and report_v5.md Section 7 (line 1243) with the cost-is-not-fidelity and mechanism-coverage items. [F]
- Spearman -0.64 is over 15 of 20 family C circuits (the 5 lacking mechanism data are excluded). The "lacks 6 circuits" limitation covers this. [O] Stating n = 15 next to the rho would help.

## 4. Consistency and layout

- Title "PSEL4 compiles each H2 circuit four ways and keeps the cheapest" is identical in one_page_summary.pdf, presentation.pdf, report.pdf, report_full.pdf and SUMMARY.md. [F]
- Headline numbers (15.7, 13.9, 49,580.6, 58,837.2, -2.90, 0.8267, 8983.4, 5.08, 3.03) appear in every PDF (pdftotext). 50,632.2 and 13.33 are absent from SUMMARY.md only. [F]
- one_page_summary.pdf: 1 page. presentation.pdf: 13 slides rendered at 50 dpi, no clipped or overflowing text seen. [F]
