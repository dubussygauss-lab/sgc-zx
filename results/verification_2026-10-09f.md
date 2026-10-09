# Verification of value additions, 9 October 2026 (f)

Verifier: independent agent, no access to how the work was produced. Scope: `git diff HEAD~3 -- report/ submission/SUMMARY.md` at df8f20f, i.e. `report/report_short.md` Sections 1.5, 2.1 and Limitations, `report/report_v5.md` Sections 1.5, 1.6, 2.2, 6 and References 11 to 16, and `submission/SUMMARY.md`. Recomputation scripts were run from a scratch directory against the repository files. Nothing in the repository was edited except this file.

## Summary

| Check | Result |
|---|---|
| 1. Azure prices, allotments, page date, USD per HQC, USD estimates, [O] tags | PASS |
| 2. Quoted sentences (Reiher, Beverland, Ross and Selinger, Chakrabarti, pytket docs) | PASS with two minor wording FAILs (F1, F2) |
| 3. HQC numbers from CSVs | PASS |
| 4. Finals plan power 0.80 numbers | PASS |
| 5. No overclaim (PSEL as PassSelector pattern, finance claim) | PASS (see F2 for one scope wording) |
| 6. Style rules on added lines | PASS |
| 7. `submission/report.pdf` at most 8 pages, no clipped tables | PASS |

## FAIL list

- F1 `[F]` Ross and Selinger qualifier dropped. `report/report_short.md` Section 1.5 and `submission/SUMMARY.md` "Where not to spend fault-tolerant compiler effort" write "approximate a z-rotation with T-count 3 log2(1/eps) plus lower-order terms". The source (arXiv:1403.2975, abstract) says "In the typical case, this yields circuit approximations of T-count 3 log2(1/ε) + O(log(log(1/ε)))", and the result holds under a number-theoretic hypothesis. `report/report_v5.md` Section 1.6 keeps "in the typical case". Fix: append "in the typical case" after "lower-order terms" in both places.
- F2 `[F]` Finance sentence broader than its source. All three files write "Derivative pricing by amplitude estimation needs quantum arithmetic for path loading and payoff". Appendix C of arXiv:2012.03819 says "Quantum arithmetic is required for path loading using the Riemann summation method (Section 4.1) and the re-parameterization method (Section 4.2), as well as the payoff calculation described in Section 5." This covers the two loading methods of that paper and not every loading scheme. Fix: "In the derivative-pricing methods of Chakrabarti et al. both path-loading schemes and the payoff calculation need quantum arithmetic (Appendix C)." or equivalent wording that names the paper's methods as the scope.

## 1. Azure Quantum pricing

- `[F]` Fetched https://learn.microsoft.com/en-us/azure/quantum/pricing on 9 October 2026. Quantinuum, tab Subscriptions: "Standard Plan: USD125,000/Month + Azure infrastructure costs", "10k HQCs for use on Quantinuum System Model H2", "100k eHQCs". "Premium Plan: USD175,000/Month + Azure infrastructure costs", "17k HQCs", "170k eHQCs". Footer "Last updated on 2025-12-23". All quoted figures match. PASS.
- `[F]` The page also offers Quantinuum Pay as You Go without listed rates. Its metadata carries `updated_at 2026-04-23`, which differs from the displayed date. The report quotes the displayed date, which is correct.
- `[F]` Recomputed: 125,000 / 10,000 = 12.50 USD per HQC. 175,000 / 17,000 = 10.2941 USD per HQC. Family C 748.4 HQC gives 9,355.0 and 7,704.1 USD. Family A 1,076.4 HQC gives 13,455.0 and 11,080.6 USD. Rounded figures 7,700 to 9,400 and 11,100 to 13,500 and the unrounded 7,704, 9,355, 11,081, 13,455 match. PASS.
- `[F]` The USD estimates carry `[O]` in all three files. Stated assumptions: plan average not marginal price, 1000 shots per circuit once, eHQCs valued at zero, infrastructure costs excluded. `report_v5.md` also states full use of the monthly allotment. `[O]` The short report and SUMMARY omit the full-allotment assumption. This is acceptable because "plan average" implies it. Not a FAIL.

## 2. Quotations

- `[F]` Reiher et al., arXiv:1605.03590, Section on Trotter decomposition: "using a sequence of elementary gates and single-qubit rotations [11]. These rotations dominate the cost of the quantum simulation." Context is the FeMoco simulation scheme of the paper. PASS.
- `[F]` Beverland et al., arXiv:2211.07629: "Non-Clifford rotations Rz(θ) are frequently used in quantum algorithms, but are among the most resource intensive operations when we consider implementation costs." PASS.
- `[F]` Ross and Selinger, arXiv:1403.2975: T-count 3 log2(1/ε) + O(log(log(1/ε))) "in the typical case". PASS in `report_v5.md`. See F1 for the short report and SUMMARY.
- `[F]` Chakrabarti et al., arXiv:2012.03819. Appendix C, "Fixed-point Quantum Arithmetic Resources": quoted in F2. Section 1: "in the fault tolerant setting where the number of T-gates, called the T-count dominates the computational requirements." The quoted phrase "the T-count dominates the computational requirements" is a verbatim substring with unchanged meaning. Reference 14 of `report_v5.md` correctly names Section 1 and Appendix C. PASS apart from F2.
- `[F]` pytket API docs (page shows 2.18.5), `PassSelector`: "The result of the compilation is the best circuit as selected by a given metric." `ZXGraphlikeOptimisation`: "As a resynthesis pass, this will ignore almost all optimisations achieved beforehand and may increase the cost of the circuit." The installed pytket 2.18.4 carries the same two docstrings and exports both names. PASS.
- `[F]` `grep PassSelector pipelines/pass_select.py` returns nothing, so "does not call it" holds. PASS.
- `[O]` Note only. The short report and SUMMARY say "pytket 2.18.4 ships" and cite the 2.18.5 docs. Both versions carry the same docstring, so the claim holds. Optional fix: add "(same docstring in the installed 2.18.4)".

## 3. HQC numbers recomputed from raw CSVs

PSEL recomputed per circuit as lower HQC, tie to lower n_2q, then P0.

| Number | Source | Recomputed | Result |
|---|---|---|---|
| 748.4 HQC, 7.47 % | `results/family_C_counts.csv`, 15 circuits with `n_rz_non_cliffordT_as_written` = 0 | 10,019.6 - 9,271.2 = 748.4, 7.469 % | PASS |
| 12.9 % | same, 9 circuits with application "adder" | 12.906 % | PASS |
| 1,076.4 HQC | `results/family_A_counts.csv`, 180 circuits, P2 minus PSEL | 17,453.0 - 16,376.6 = 1,076.4 | PASS |
| 6.27 %, 1,030.4 HQC | family A, (P2 - P0) / P0 | 1,030.4, 6.274 % | PASS |
| 22.1 %, 1,057.2 HQC | family C, 3 QFT adders | 1,057.2, 22.125 % | PASS |
| 52.7 % | draper_adder_16, 1,385.0 vs 906.8 | 52.735 %, status ok-unchecked | PASS |
| 4.79 % | `results/family_B1_counts.csv`, 15 circuits | 4.792 % | PASS |
| 2.0 %, 862 of 42,396 | `results/family_B2_counts.csv`, P2 rows | 862, 2.033 % | PASS |
| 99.7 %, 0.3 %, 0.7 % | `results/certificates.csv`, 20 B2 rows | 41,414 / 41,534 = 99.711 %, 0.289 %, worst 0.721 % | PASS |
| 0.443 on B1 | `results/certificates.csv`, 4 B1 rows | 0.4434 | PASS |

## 4. Finals plan, power 0.80

- `[F]` Pooled vbe_adder_3 counts from the four H2-2E JSON runs: P0 3808/4000 = 0.95200, P2 3851/4000 = 0.96275, difference 0.01075, sd 0.0045155.
- `[F]` n = 4000 ((1.6449 + 0.8416) sd / diff)^2 = 4363.35, ceiling 4364. PASS.
- `[F]` From `results/compiled/{P0,P2}/{vbe_adder_3,grover_5}.qasm`, counting U1q as N_1q (Rz excluded per the Helios costing page) and RZZ as N_2q, N_SPAM = 2n: vbe_adder_3 P0 73, 56, n 10, P2 60, 41. grover_5 P0 313, 240, n 9, P2 346, 218.
- `[F]` HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000: 644.8 (P0) and 502.5 (P2) at 4364 shots, sum 1147.3. grover_5 at 1900 shots 1070.1 and 999.1. Total 3216.5. PASS.

## 5. Overclaim

- `[F]` All three files present PSEL as the PassSelector pattern and state that it is not a new selection mechanism. PASS.
- `[F]` All three files mark the claim that arithmetic dominates derivative-pricing cost as Unverifiable and do not assert it. PASS.

## 6. Style on added lines

- `[F]` No semicolons, no em-dashes, no "rather than", no hedge adverbs from the list (usually, in general, generally, typically, often, mostly, largely, roughly, perhaps, likely, arguably) in the added lines of the three files.
- `[F]` No sentence outside the reference list has more than two commas after removing thousands separators, code spans and URLs. The reference entries 9, 10, 15 and 16 have three to five commas and follow citation format. PASS.
- `[F]` Every added prose line carries `[F]` or `[O]`. PASS.

## 7. PDF

- `[F]` `pdfinfo submission/report.pdf`: 8 pages, A4, created 9 October 2026 04:06 CEST, in commit df8f20f together with the current `report/report_short.md`.
- `[F]` `pdftotext` contains the new text (12.50, 10.29, 7,700, 11,100, the Reiher, Beverland, Chakrabarti and pytket quotes, 4364, 3216.5).
- `[F]` All 101 table rows of `report/report_short.md` were checked cell by cell against the `pdftotext` output. 0 cells missing. `pdftotext -bbox` shows maximum x of 554.4 pt on a 595 pt page and no word within 20 pt of the right edge or 10 pt of the bottom. PASS.
