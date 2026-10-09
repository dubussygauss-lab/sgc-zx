# Verification of PSEL4 (package commit d2bb2a0), 9 October 2026

Independent verifier. No tracked file edited. Scratch work outside the repository.

## Verdict: PASS WITH ISSUES

All numbers reproduce, the official-pass recompilations match, the 17 of 20 proof count is correct and code.zip is correct. The issues are in the wording: most of the family C saving that the headline quotes comes from outputs with no exactness evidence, and the "pass their checks" qualifier does not apply to family C.

## 1. Numbers (Table P4, PSEL4 sentences)

- [F] I rebuilt the candidates independently from `value/selector_ledger_circuits.csv` (A, B1), `value/family_C_selector.csv` (C), `value/usecase.csv`, `results/strong_baselines.csv` (B1, C L3/P2L3) and `value/psel4_runs.csv` (A, usecase L3/P2L3), and applied my own min with the tie order P0, L3, P2, P2L3. The HQC and pick match `value/psel4_ledger.csv` on all 217 circuits (0 mismatches).
- [F] Every Table P4 cell reproduces exactly: A 16422.6 / 16231.2 / 15949.0, 2.88 / 1.74, picks 35/145/0/0. B1 15516.0 / 13965.8 / 13863.4, 10.65 / 0.73, 0/10/2/3. B1 without hwb8 2235.0 / 1928.6 / 1826.2, 18.29 / 5.31. C 24535.0 / 18853.2 / 18193.2, 25.85 / 3.50, 5/8/4/3. C without continuous angles (15 files from `bench/family_C/manifest.csv`) 10019.6 / 8922.4 / 8865.0, 11.52 / 0.64, 3/7/3/2. Usecase 2363.6 / 1582.0 / 1575.0, 33.36 / 0.44, 0/0/0/2. PSEL columns, medians and maxima also match.
- [F] 217 circuits (A 180, B1 15, C 20, usecase 2) have both L2 and L3 passed. Violations of PSEL4 <= min(L2, L3): 0. Strictly below on 14.
- [F] The stored P0 equals the L2 row of `strong_baselines.csv` on all 35 B1 and C circuits.
- [F] "Most of its saving against level 2 comes from level 3 itself": on family C, L3 alone accounts for 5681.8 of the 6341.8 HQC saved against L2 (89.6 %).

## 2. Recompilation with the official pass

`QuantinuumBackend("H2-1", api_handler=QuantinuumAPIOffline()).get_compiled_circuit(..., optimisation_level=3)`, P2L3 with `compile.zx_teleport_reduce` first. I computed the HQC myself as 5 + 1000 (N_PhasedX + 10 N_ZZ + 5 * 2n) / 5000. Output gate sets are {PhasedX, Rz, ZZPhase}.

| circuit | variant | n | N_1q | N_2q | HQC (mine) | HQC (ledger) |
|---|---|---|---|---|---|---|
| A xxz_n6_r2_uniform_s1 | L3 | 6 | 63 | 34 | 97.6 | 97.6 |
| A xxz_n6_r2_uniform_s1 | P2L3 | 6 | 62 | 34 | 97.4 | 97.4 |
| B1 gf2_pow_4_mult | L3 | 12 | 86 | 99 | 244.2 | 244.2 |
| B1 gf2_pow_4_mult | P2L3 | 12 | 119 | 99 | 250.8 | 250.8 |
| C modadd_2n_10 | L3 | 20 | 202 | 147 | 379.4 | 379.4 |
| C modadd_2n_10 | P2L3 | 20 | 194 | 142 | 367.8 | 367.8 |

## 3. Proof claim (17 of 20)

- [F] The 11 L3/P2L3 picks in `results/family_C_equivalence_psel4.csv` give 9 proven and 2 timed out (rgqft_mult_6 L3, draper_adder_28 P2L3). The 9 P0/P2 picks in `results/family_C_equivalence.csv` give 8 proven and hrs_mult_5 (P2) inconclusive. 9 + 8 = 17. Correct.
- [F] I reran the miter on my own fresh compilations, not the stored QASM, by calling `equiv_psel4_C.miter_check` with `compiled_path` redirected to scratch. modadd_2n_10 P2L3 was proven in 3.1 s and cdkm_adder_10 L3 was proven in 2.1 s, both with snap 0 on grid 2^-4.

## 4. Text and rendering

- [F] `submission/one_page_summary.pdf` is 1 page and matches the commit. Slides 1 and 12 of `submission/presentation.pdf` (identical to `report/presentation/presentation.pdf`) render with no overflow.
- [F] `submission/report.md` and `report_full.md` carry the new Table P4 text.

## 5. Package

- [F] `submission/REPRODUCE.md` names 21883ebc9cc1 as the commit for code.zip. Unzipping `submission/code.zip` and diffing it against `git archive 21883eb` minus `submission/` gives 0 differences in 2480 files. From 21883eb to d2bb2a0 only `submission/` files change.
- [F] `run_tests.sh` lists 26 unique test files and every one exists. The last `build_logs/tests_summary.txt` shows rc=0 for all 26, including psel4 and equiv_psel4_C.

## Findings

### F1. Major. The family C savings that the headline quotes rest mostly on outputs with no exactness evidence

- Location: `report/one_page_summary.md:3` (pitch), `:26` ("saves 3.50 % against level 3 there, with 17 of 20 outputs proven"); `report/presentation/presentation.tex:48` (slide 1), `:288`; `report/report_short.md:276`, `report/report_v5.md:837` (Section 3.8.1); `report/report_v5.md:24`, `report/sec1_v5.md:7`, `submission/SUMMARY.md:75`.
- Evidence [F]:
  - Against L3, PSEL4 saves 660.0 HQC on family C. Of that, 578.0 (87.6 %) comes from the two unproven picks hrs_mult_5 (313.0) and draper_adder_28 (265.0).
  - Against L2, PSEL4 saves 6341.8 HQC. Of that, 5187.2 (81.8 %) comes from the three unproven picks: rgqft_mult_6 2905.2, hrs_mult_5 1117.0 and draper_adder_28 1165.0.
  - rgqft_mult_6 (L3) and draper_adder_28 (P2L3) have no evidence at all. They are `ok-unchecked` in `strong_baselines.csv`, the miter timed out and there is no spot check.
  - On the 17 proven circuits, PSEL4 saves 0.80 % against L3 and 10.22 % against L2.
- [O] The one-pager places "3.50 %" next to "17 of 20 outputs proven", which reads as if the 3.50 % were proven. Table P4 lists the three unproven circuits but does not say they carry the saving.
- Proposed fix: add one sentence wherever 3.50 % or 25.85 % appears for family C. For example: "On the 17 circuits with a proven output PSEL4 saves 0.80 % against level 3 and 10.22 % against level 2." Alternatively, add a "C, proven outputs" row to Table P4.

### F2. Medium. "When both pass their checks" does not apply to family C, and slide 1 drops the qualifier

- Location: `report/one_page_summary.md:3`; `report/presentation/presentation.tex:48` ("never costs more than pytket level 2 or level 3", with no qualifier); `report/report_short.md:276` and `report_v5.md:837, 1109` ("on all 217 circuits where both passed").
- Evidence [F]:
  - All 20 family C L3 and P2L3 rows have status `ok-unchecked`. The ledger counts `ok-unchecked` as passed (`value/psel4_ledger.py:50`, `OK = {"ok", "ok-unchecked", "stored"}`). For family C, "both passed" therefore means that compilation finished, not that a check ran.
  - The inequality PSEL4 <= min(L2, L3) holds by construction whenever L2 and L3 are not dropped. When L3 times out or fails, it is not guaranteed. Slide 1 states it unconditionally.
- Proposed fix: write "when both compile within the time limit and pass the exactness check where one is run (up to 12 qubits for level 3)". Restore the qualifier on slide 1.

### F3. Minor. The one-pager puts the [O] tag on the wrong sentence

- Location: `report/one_page_summary.md:26`.
- Evidence [F]:
  - "[O] Running teleport_reduce before level 3 and keeping the cheaper result still saves 2.34 % (App. 3.8.1)" is a checkable number.
  - The sentence before it, "Most of its saving against level 2 comes from level 3 itself.", is untagged. It is true (89.6 %, Section 1 above).
- Proposed fix: remove the [O] from the 2.34 % sentence. Optionally quantify the level-3 share as "89.6 % of the saving against level 2".

### F4. Minor. "The ZX stage supplies the part against level 3" is too general

- Location: `report/report_short.md:276`, `report/report_v5.md:837` (final [O] sentence).
- Evidence [F]:
  - On family A, all 282.2 HQC saved against L3 come from P0 picks (L2 cheaper than L3) and none from ZX.
  - On family C, 30.6 of 660.0 come from P0 picks.
  - The paragraph already says this for family A, so the closing sentence contradicts it.
- Proposed fix: "On B1, C and the Grover instances the ZX candidates supply most of the saving against level 3."

### F5. Minor. Slide 12 and the one-pager mention only the PSEL proof count

- Location: `report/presentation/presentation.tex` slide 12, Limitations ("Its PSEL output is proven on 18 of 20 circuits"); one-pager Approach paragraph.
- Evidence [F]: slide 1 now headlines PSEL4 numbers, but slide 12 gives only the PSEL proof count (18 of 20). The PSEL4 count is 17 of 20 and appears only in the one-pager bullet and the reports.
- Proposed fix: add "PSEL4 output proven on 17 of 20" to slide 12.
