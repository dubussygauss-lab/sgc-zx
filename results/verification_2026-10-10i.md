# Verification 2026-10-10i (independent, commits 88bd01b..b8c007f)

Verdict: PASS WITH ISSUES

## Checks
- [F] Figure, recomputed from value/psel4_ledger.csv: 217 rows (A 180, B1 15, C 20, usecase 2); L3/L2 > 1 on 45, max 1.12951 (gf2_pow_4_mult); PSEL4/L2 > 1 on 0, max 1.0000; PSEL4 > L3 on 0. Titles, y label "HQC relative to level 2", x label "HQC of level 2 per circuit (1000 shots, log scale)", annotation "worst 1.13x" match. PNG in report/ and submission/ identical.
- [F] Lead numbers recomputed: L2 58,837.2, L3 50,632.2, PSEL4 49,580.6, min(L2,L3) 50,260.2. L3 saves 13.945 %; PSEL4 15.733 %; HQC lost on the 45 = 372.0; worst 12.951 %; PSEL4 below L3 2.077 % / 1,051.6; below per-circuit min 1.352 % / 679.6; 10,000 x 0.15733 = 1,573.3. All match.
- [F] one_page_summary.pdf 1 page; presentation.pdf 11 pages, all pages rendered, none clipped (slide 4 figure and table fit). Lead numbers identical in one-pager, slides, report.md, report_full.md, SUMMARY.md, README.md. Both report PDFs contain Figure PC.
- [F] One-pager still has: 2 significant accuracy losses, "not significantly better on 1", conservative variant (Correctness item 4, as before, not in Limits), unproven outputs and 48 jobs / 9971.8 HQC in Limits.

## Findings
1. Medium. report/one_page_summary.md line 33 (Correctness). Removed: QCEC ZX checker returned "probably_not_equivalent", alternating checker "no_information"/killed on hrs_mult_5. Now only "returned no counterexample", which reads stronger. Fix: restore "inconclusive (ZX checker: probably_not_equivalent)".
2. Low. one_page_summary.md line 29. "so neither HQC nor gate counts order fidelity" lost "on the emulator"; rests on one circuit. Fix: restore "on the emulator".
3. Low. one_page_summary.md line 29. Explicit "No pick was significantly more accurate" removed (still implied). Fix: optional restore.
4. Low. one_page_summary.md line 3. Bold lead of [F] facts is tagged only [O]. Fix: tag facts [F], workload/USD [O].
5. Low. Working tree: report/figures/fig_policy.pdf modified after commit (same size, regenerated). Fix: commit or git checkout.
