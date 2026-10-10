# Verification 2026-10-10a: PSEL4-first framing (commit 05b6b74, package 39dbdfb)

Independent verifier, no prior exposure to the work. Scope: `git diff 3890b2a 05b6b74 -- report` and `git diff 3890b2a 39dbdfb -- submission/SUMMARY.md` (SUMMARY.md changed in the package commit 39dbdfb, not in 05b6b74), plus `pdftotext -layout` of `submission/one_page_summary.pdf`, `report.pdf`, `report_full.pdf`, `presentation.pdf`. No tracked file was edited.

## Verdict: PASS WITH ISSUES

No number is wrong. One new contradiction (Medium) and five Low wording issues.

## 1. Numbers (recomputed with own pandas code from `value/psel4_ledger.csv`)

| claim | recomputed | source agreement |
|---|---|---|
| PSEL4 vs L3, family C (20) 3.50 % | L3 18853.2, PSEL4 18193.2, 3.50 % | psel4_ledger.md |
| PSEL4 vs L2, family C 25.85 % | L2 24535.0, 25.85 % | psel4_ledger.md |
| L3 vs L2, family C 23.16 % | 23.16 % | strong_baselines.md l.100 |
| proven 17: vs L3 0.80 %, vs L2 10.22 % | L2 11296.8, L3 10224.2, PSEL4 10142.2; 0.80 %, 10.22 % | psel4_proven.md |
| 87.6 % of 660.0 HQC from unproven picks | 660.0 saved, 578.0 unproven, 87.6 % | psel4_proven.md |
| B1 0.73 % / 10.65 % (15), A 1.74 % / 2.88 % (180), usecase 0.44 % / 33.36 % | identical | psel4_ledger.md |
| PSEL vs L3 on C +8.37 % | 8.37 % | strong_baselines.md l.104 |
| 217 circuits, 0 violations of PSEL4 <= min(L2, L3) | 217, 0 | psel4_ledger.md |
| 22.1 % more for P2 on 3 QFT adders | P0 4778.4, P2 5835.6, 22.12 % | family_C_selector.csv |
| 6.27 % on family A | 6.27 % | selector_ledger.md l.13 |
| 9.92 % (14 B1), 3.49 %, 2.34 % | as stated | strong_baselines.md l.58, 71, 115 |
| Holm 0.035 (2 circuits), 0.052 (3 circuits), repeats-only 0.030; z +2.38, p 0.017, dF +0.0108 | as stated | h22e_confirmatory.md l.38, 48-49; report_v5.md l.158, 364, 735 |
| Tie order P0, L3, P2, P2L3 | `TIE_ORDER` in pipelines/pass_select.py l.48 | matches |

`report/check_short_numbers.py`: 522 of 522 numbers found. `submission/check_summary_numbers.py`: 158 of 158 found.

## 2. Titles across deliverables

All five documents carry "PSEL4 keeps ZX rewriting only where it beats pytket level 3 on Quantinuum H2" (SUMMARY.md, report.pdf, report_full.pdf, presentation.pdf, one_page_summary.pdf). The headline 0.80 % on 17 proven circuits appears in all five. 17 is attributed to PSEL4 and 18 to PSEL everywhere checked.

## 3. Findings (severity, then document order)

### M1. Section 1.5 still names PSEL as the delivered tool
- File: report/report_v5.md l.152 (and report_full.pdf Section 1.5). Unchanged by the commit.
- Evidence: l.24 (changed) "The delivered tool is the pass selector PSEL4 in `pipelines/pass_select.py --psel4`". l.152 "The delivered tool is PSEL in `pipelines/pass_select.py`."
- Fix: change l.152 to "The delivered tool is PSEL4 (`pipelines/pass_select.py --psel4`). Its two-candidate form PSEL ..." and keep the PSEL guarantee as a second statement.

### L1. Table P4 paragraph states the guarantee as a measured count without "by construction"
- File: report/report_short.md l.276, report/report_v5.md l.852 (line touched by the commit).
- Evidence: "It costs no more than the cheaper of level 2 and level 3 on all 217 circuits where both compiled within the time limit." Correct (217, 0 violations), but reads as a measurement next to text that says the guarantee "is not a measured result".
- Fix: "By construction it costs no more than the cheaper of level 2 and level 3. The ledger assertion confirms this on all 217 circuits where both compiled within the time limit."

### L2. "Design property" in place of "holds by construction"
- File: report/report_v5.md l.5, submission/SUMMARY.md l.11 (and report_full.pdf p.1).
- Evidence: "This guarantee is a design property. It is not a measured result." Same meaning, different wording from l.25-26 and report_short l.16, l.25.
- Fix: "This holds by construction and is not a measured result."

### L3. "87.6 % ... comes from 3 picks whose output is not proven" overstates the number of contributing picks
- File: report/report_short.md l.16, report/report_v5.md l.5 and l.25, submission/SUMMARY.md l.13, one_page_summary.pdf.
- Evidence: rgqft_mult_6 picks L3 and saves 0.0 HQC against L3. The 578.0 HQC come from hrs_mult_5 (4487.4 - 4174.4 = 313.0) and draper_adder_28 (2601.2 - 2336.2 = 265.0).
- Fix: "87.6 % of that saving comes from two unproven picks, hrs_mult_5 and draper_adder_28."

### L4. 20-qubit check limit is presented as the operative limit for the reported PSEL4 figures
- File: report/report_short.md l.25 ("The exactness check runs up to 20 qubits only. Above that size the output rests on separate PyZX miter proofs."), report/report_v5.md l.25 ("PSEL4 runs no exactness check above 20 qubits").
- Evidence: the PSEL4 ledger runs used `CHECK_MAX_QUBITS = 12` (value/psel4_ledger.py l.43). All 20 family C L3 and P2L3 rows are ok-unchecked, including the two 20-qubit circuits draper_adder_10 and modadd_2n_10 (modadd_2n_10 picks P2L3). Table P4 paragraph states this correctly. Not a contradiction, but "above that size" implies 20-qubit outputs were checked.
- Fix: add "In the reported ledger runs the check stopped at 12 qubits, so all 20 family C PSEL4 outputs rest on the miter proofs."

### L5. PSEL guarantee loses its condition in the short report
- File: report/report_short.md l.25.
- Evidence: "In the same way PSEL costs no more HQC than P0." The previous text and report_v5 l.26 carry "whenever P0 passes PSEL's checks".
- Fix: "In the same way PSEL costs no more HQC than P0 whenever P0 passes its checks."

### Info
- one_page_summary.pdf: "keeps the one with the lower HQC" for four candidates. Proposed: "lowest".
- report_v5.md l.25 vs l.27: PSEL4 on B1 is over 15 circuits (0.73 %), PSEL vs L3 on B1 over 14 (9.92 %). Both labelled correctly. No change needed.
- SUMMARY.md says "built on 9 October 2026"; package commit 39dbdfb is dated 2026-10-10 02:14 +0200. Proposed: update the date.
