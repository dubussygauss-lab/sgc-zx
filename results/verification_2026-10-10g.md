# Verification 2026-10-10g

Independent verifier, no prior sight of the work. Scope: commits dac11f2, a3b1059, b25efb3, bcc5924, 6c7bc22, d8348cb, 43409f1 (since feff66a). No tracked file edited. Scratch scripts outside the repository.

## Verdict: PASS WITH ISSUES (no Major or Critical finding)

## 1. Basis-input check

- [F] `pipelines/pass_select.basis_check_many` (lines 243-279): one phase phi = arg(sum_x o_x) common to all inputs; check_dev = max_x 1 - Re(e^{-i phi} o_x)^2. Reference and candidate both carry their own global phase (`circ.phase`) and implicit qubit permutation (`_Compiled.order`, line 222-226). The comparison is correct.
- [F] `basis_inputs` (line 115-125): all-zero plus 63 distinct nonzero inputs, seed 20261010, as documented.
- [F] Rerun with an independent simulator (pytket `get_statevector` with X preparation for 9 and 10 qubits, own numpy tensordot simulator for 12 qubits) on barenco_tof_5 (9), vbe_adder_3 (10), tfim_n12_r2_disorder_s1 (12), all four candidates: repo and independent check_dev agree, all below 1e-14, on the seed inputs and on 16 other random inputs.
- [F] Wrong candidates: L3 plus Rz(0.5) on the last qubit (diagonal error, invisible on all-zero) gives check_dev 0.56 / 0.59 / 0.61, fail. L3 plus an extra CX gives 1.0, fail. L3 of barenco_tof_5 already carries an implicit permutation and passes. An equivalent copy with an extra implicit permutation passes (2.4e-15). A single SWAP turned implicit fails (1.0).
- [F] Recount from `value/psel4_basis_check.csv`: picks 83/83, required 187/187, others 142/142, 3 not checked (hwb8 P0, P2, P2L3), all non-required. Matches the md. The 20-qubit circuits were not rerun (500 to 670 s each).

## 2. Conservative variant

- [F] Own code from `value/psel4_ledger.csv` and the three `results/family_C_equivalence*.csv` (pyzx proven only): totals 58837.2 / 50632.2 / 49580.6 / 51628.8, conservative 12.25 % vs L2, -1.97 % vs L3; verified counts P0 215, P2 215, L3 215, P2L3 198; costlier than L2 0; costlier than L3 2 (hrs_mult_5 P0, rgqft_mult_6 P2); changed picks draper_adder_28 (+265.0), hrs_mult_5 (+1117.0), rgqft_mult_6 (+666.2); flagged hrs_mult_5 only. All match. Status mapping applied as stated.

## 3. Derived numbers

- [F] 13.9453 and 1.7873 points (15.7326 total), 50260.2 HQC, 679.6 HQC, 1.352 %, 1.155 %, 0.8427, 1573.26 HQC, USD 19,665.7 and 16,195.3, 2085.12/2523.12 = 0.8264, (8556/9400)/(8554/9400) = 1.0002, R = 0.8262. All match. 45 circuits and 372.0 HQC lost by always L3, gf2_pow_4_mult 12.95 %, family C 3.21 % also match. PSEL4 > L2 and PSEL4 > L3 on 0 of 217.

## Findings (severity, then document order)

1. Minor. `report/one_page_summary.md` line 27, `report/report_short.md` line 175, slide 8. Evidence: `results/family_C_equivalence_qcec.md` target table, hrs_mult_5 qcec_alt row: "killed", no QCEC verdict. Text says the alternating checker returned "no_information" for the three outputs. Fix: "no_information on rgqft_mult_6 and draper_adder_28, killed after 630 s on hrs_mult_5".
2. Minor. Title of `report/one_page_summary.md` line 1, `submission/SUMMARY.md` line 11 and `report/report_short.md` line 16 ("It is never costlier than the default compile", tagged [F]). Evidence: compile_select drops a candidate that fails the check, so the guarantee holds by construction only when P0 passes. The one-pager subtitle and slide 3 ("where both pass the check") qualify it. The [F] sentences do not. Fix: "It was never costlier than the default compile on the 217 benchmark circuits, and by construction is not whenever the default output passes the check."
3. Minor [O]. `value/psel4_conservative.md` status mapping. Evidence: A/B1 P0/P2 rows at 9 to 12 qubits are counted verified on a single all-zero statevector check (160 rows, `check_kind` statevector in `results/family_A_counts.csv`, `family_B1_counts.csv`), while C `stored:pass` (64 basis inputs, stronger) is counted not verified. No pick changes. Fix: one sentence stating the asymmetry, or cite the new basis check for those rows.
4. Info. 13.95 + 1.79 = 15.74 against 15.73 (rounding of unrounded parts). No fix needed, optionally note rounding.

## 4-6. Other checks

- [F] No text calls the conservative variant proof-only. Both reports say it is not (report_short line 177, psel4_conservative.md).
- [F] The per-answer finding says three of six pairs compare P2 (one-pager line 31, report_short limitations, slide 9). Matches `value/hqc_per_correct.csv`.
- [F] Limitations present in report.pdf (Section 7) and report_full.pdf (Section 7), including exactness coverage, hwb8 not basis-checked, per-answer P2 pairs, no hardware.
- [F] one_page_summary.pdf 1 page. presentation.pdf 11 slides, rendered at 50 dpi, no clipping seen. Headline numbers (15.73, 13.95, 1.79, 679.6, 1.35, 1,573.3, 19,666, 12.25, 0.8262, 187/187) appear in all four PDFs and SUMMARY.md with no conflicting value found. 142/142 is absent from the slides (text says "and 142" split across lines, present).
- [O] Traceability checked for the numbers above, 3.21 % and 5.08x. Other numbers in the PDFs were not traced in the time limit and are Unverifiable by this run.
