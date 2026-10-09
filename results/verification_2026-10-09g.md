# Verification 2026-10-09g: family C equivalence proofs and judge-round-6 wording

Verifier: independent agent, did not see how the work was produced. Scope: `git log -6` (c7b35fc..60d1f1a), `git diff HEAD~5 -- report/ submission/SUMMARY.md results/family_C_equivalence.* pipelines/equiv_family_C.py`. Nothing was edited except this file. No platform jobs.

## Verdict

| # | Check | Result |
|---|---|---|
| 1a | Independent PyZX miter re-proof | PASS |
| 1b | Negative controls | PASS |
| 1c | Counts 18/20, 13/14, 15/15, gaps | PASS |
| 2a | vbe_adder_3 fidelity wording | PASS |
| 2b | PSEL condition sentence | PASS |
| 2c | pytket 2.18.4 vs 2.18.5 | PASS |
| 2d | Platform tools sentence | PASS |
| 3 | No stale "spot-checked/unchecked" text, no proof claim for the two gaps | FAIL (F1) |
| 4 | Style | PASS |
| 5 | report.pdf pages and tables | PASS |

## FAIL list

**F1. draper_adder_16 is still called unchecked, but it is proven.**
- [F] `results/family_C_equivalence.csv` has `proven` for draper_adder_16 under P0, P2 and P2vsP0 (PyZX, grid 2^-20, max snap 5.27e-12 half-turns). Table C3 and Table 2b show `proven` for it.
- [F] Stale text, 6 places:
  - `report/report_short.md` line 97 (and `submission/report.md` line 97): "On draper_adder_16 it costs 1,385.0 HQC against 906.8 or 52.7 % more. This circuit is unchecked."
  - `submission/SUMMARY.md` line 35: "... 906.8 for P0 or 52.7 % more. This circuit is unchecked."
  - `report/sec1_v5.md` line 153, `report/report_v5.md` line 170 and `submission/report_full.md` line 170: "This circuit is count-only and unchecked."
- Fix: in all six, replace the last sentence with "A PyZX miter proves its P0 and P2 outputs equal to its input (Appendix Section 3.8)." In sec1_v5 and report_v5 use "(Section 3.8)" and keep "count-only" if wanted: "This circuit is count-only. A PyZX miter proves its P0 and P2 outputs equal to its input (Section 3.8)." Then rebuild the submission package. `report.pdf` must stay at 8 pages or fewer.

## 1. Equivalence claims

### 1a. Independent re-proof
- [F] Own script (scratchpad, not committed). The input QASM is parsed by `pyzx.Circuit.from_qasm` directly. pytket is not used. The compiled hqslib1 QASM is parsed by my own regex: `U1q(a,b)` -> ZPhase(-b) XPhase(a) ZPhase(b) in circuit order, `RZZ(a)` -> CNOT ZPhase(a) CNOT, `rz(a)` -> ZPhase(a). Angles are exact `Fraction` of the decimal text. No snapping. The output permutation is read from `measure q[j] -> c[i]` and realised as CNOT swap triples appended to the compiled circuit. The test is pyzx 0.10.7 `Circuit.verify_equality` called as is (pytket 2.18.4 and pyzx 0.10.7 installed).
- [F] Results (all max angle denominator 4, all identity permutations):

| circuit | n | comparison | verdict | seconds |
|---|---|---|---|---|
| cdkm_adder_10 | 22 | P0, P2, P2vsP0 | proven, proven, proven | 1.1, 1.3, 1.4 |
| modadd_2n_10 | 20 | P0, P2, P2vsP0 | proven, proven, proven | 1.9, 1.7, 2.7 |
| mcx_dirty_28 | 55 | P2, P2vsP0 | proven, proven | 6.6, 6.7 |
| vbe_adder_18 | 55 | P2 | proven | 5.3 |
| mcx_b95_54 | 56 | P2 | proven | 230.6 |

- [F] All agree with the CSV verdicts.
- [F] No proven family C output has a non-identity output permutation. Only draper_adder_28 (20 moved wires under P0 and P2) has one, and it timed out. The permutation handling is therefore not exercised by any proven row.
- [F] The input angles are written exactly (`rz(pi/2)`, `rz(pi/4)`) in draper_adder_10 and rgqft_mult_6. This supports "the input angles lie on that grid exactly".

### 1b. Negative controls
- [F] cdkm_adder_10 P2 with the first `RZZ(0.5*pi) q[1],q[0]` deleted: not proven.
- [F] vbe_adder_18 P2 with the first `RZZ(0.25*pi) q[19],q[38]` deleted: not proven.

### 1c. Counts recomputed with code
- [F] Inputs: `results/family_C_equivalence.csv`, `value/family_C_selector.csv` (column `pick`) and `bench/family_C/manifest.csv` (column `continuous_angles`).
- [F] The CSV has 59 PyZX rows: 54 proven, 3 inconclusive and 2 timeout. There are no duplicate (file, comparison) rows.
- [F] P0 vs input proven 18 of 20, P2 vs input 18 of 20, P2 vs P0 18 of 20 (19 rows, because draper_adder_28 P2vsP0 was not run).
- [F] PSEL output proven 18 of 20. P2 picks 13 of 14, gap hrs_mult_5. P0 picks 5 of 6, gap draper_adder_28. Circuits without continuous angles 15 of 15.
- [F] The gaps are exactly hrs_mult_5 and draper_adder_28.
- [F] Largest snap over the proven rows is 5.27e-12 half-turns, from draper_adder_16. For the 15 circuits without continuous angles it is 0.
- [O] The SUMMARY and report_short Section 2.4 put "largest snap of 5.27e-12" right after the 15-circuit sentence. The figure is correct over all proven rows. Optional fix: add "over all proven rows" after it.

## 2. Judge-round-6 wording

- [F] 2a. `report_short.md` line 16 gives the numbers +0.0108, z = +2.38, p = 0.017 and the Holm values 0.035 and 0.052 under `[F]`. It then gives "`[O]` The vbe_adder_3 gain is not established at 0.05 after correction over all three circuits." Line 233 uses the same split. Recomputed: p = 2(1 - Phi(2.38)) = 0.0173, Holm x2 = 0.0346, Holm x3 = 0.0519. Line 318 (Limitations) states "not significant at 0.05 after Holm correction" under `[F]`. [O] This is acceptable as a fact because 0.052 > 0.05.
- [F] 2b. "costs no more HQC than P0 whenever P0 passes PSEL's checks" followed by "PSEL runs no exactness check above 20 qubits" is present in report_short lines 16 and 25, SUMMARY lines 35 and 45, sec1_v5 lines 6 and 131, and sec12_selector_v5. No "cannot cost more" wording remains in these files.
- [F] 2c. The contrast "pytket 2.18.5 documentation, same docstring in the installed 2.18.4" appears once in each of report_short/report.md (line 97), report_full.md (line 169) and SUMMARY.md (line 35). Other mentions are the environment pin and the reference entry. In the installed pytket 2.18.4, `ZXGraphlikeOptimisation.__doc__` contains "may increase the cost of the circuit" and `PassSelector`'s docstring contains "the best circuit as selected by a given metric".
- [F] 2d. report_short line 153 (Section 3) was recounted:
  - `results/emulator_jobs.csv`: H2-Emulator has 3 distinct completed job ids with 22 completed rows (10 further rows FAILED). H2-2E has 18 completed jobs. H2-2SC has 2 completed jobs and 1 SUBMIT_ERROR.
  - The job ids of the 18 rows in `results/emulator_nexus_H2-2E*.csv` match the completed H2-2E job ids in `emulator_jobs.csv`.
  - HQC = 5 + (n_1q + 10 n_2q + 5 (n_qubits + n_measure)) shots/5000 with n_measure = n_qubits (`compile.hqc`). Recomputed over these 18 rows it sums to 5933.2.
  - Selene CSVs: noiseless 468, depolarizing 68 and depolarizing_full 468 rows.
  - All match.

## 3. Remaining text on family C checks
- [F] "spot-checked" now appears only for hrs_mult_5. Stale "14 of them are spot-checked" and "Four of the unchecked circuits are P2 picks" are gone from report_short, sec1_v5, sec12_selector_v5, report_v5 and SUMMARY.
- [F] No text claims a proof for hrs_mult_5 (inconclusive, off-grid) or for draper_adder_28 (timeout).
- [F] The basis-check column "unchecked" in Tables C3 and 2b is defined in the caption as the 64-input basis check and sits next to the proof column. This is consistent.
- [F] Exception: F1.

## 4. Style (added lines of `git diff HEAD~5`, 180 lines)
- [F] Prose has no semicolons, no em-dashes, no "rather than" and no hedge adverbs (usually, generally, typically, likely, roughly, approximately and similar).
- [F] No prose sentence has more than 2 commas outside lists and references.
- [F] Every added prose paragraph and bullet in the report and SUMMARY carries `[F]` or `[O]`.
- [F] The one semicolon is in the code span `G_A ; adjoint(G_B)` in `results/family_C_equivalence.md` line 7. [O] It is notation, not prose. No fix needed.
- [F] Untagged line: "Written by `python3 pipelines/equiv_family_C.py --summary` ..." in `results/family_C_equivalence.md`. [O] It is a provenance line in a results file. Optional: prefix `[F]`.

## 5. submission/report.pdf
- [F] `pdfinfo`: 8 pages, A4.
- [F] `check_pdf_tables.py submission/report.md <pdftotext -layout> --set short`: all tables report "ok".
- [F] My own row check found 101 table rows. Every row's first and last cell appear in the PDF text. The `barrier/` row matched after removing the backticks.
- [F] Largest text xMax in `pdftotext -bbox` is 554.4 pt on a 595 pt page. No text runs past the page edge.
- [F] Table 2b shows `timeout` for draper_adder_28 and `inconclusive` for hrs_mult_5.
