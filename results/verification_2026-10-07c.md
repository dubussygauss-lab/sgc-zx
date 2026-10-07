# Verification of report/report_v2.md (7 October 2026, run c)

Independent recomputation from the raw files in `results/`, `papers/barrier/main.tex` and the test scripts. Changelog entries were not used as evidence. Environment: pytket 2.18.4, pyzx 0.10.7, numpy 2.5.3, pandas 2.3.3. Every verdict is `[F]` unless marked `[O]`.

Summary: 61 claims checked. 59 CONFIRMED, 1 MISMATCH (wording, Section 4.3 group denominator), 1 UNVERIFIABLE (Section 3.5 per-circuit P0ref counts, not recomputed). Four stale changelog lines contradict the merged data (item 8). One prose-rule offender (item 9).

## Item 1. Sections 1 and 2 prose

| Claim (section, quoted) | Recomputed | File | Verdict |
|---|---|---|---|
| 1: "mean 1.35e-3" for p_meas | (9e-4 + 1.8e-3)/2 = 1.35e-3 | prose inputs | CONFIRMED |
| 1, 2.2: "Seven compilation pipelines run on families A and B1 and five on family B2" | A: 7 pipelines (P0, P0L1, P0ref, P1, P2, P3, P4), 180 circuits, 1260 rows. B1: same 7, 15 circuits, 105 rows. B2: 5 (P0, P0ref, P1, P2, P3), 20 circuits, 100 rows | `family_A_counts.csv`, `family_B1_counts.csv`, `family_B2_counts.csv` | CONFIRMED |
| 2.2: "maximum over the 1260 family A rows is 1.48e-10 rad, which is 4.7e-11 x pi" | max `pyzx_angle_err` = 1.4812e-10, / pi = 4.715e-11 | `family_A_counts.csv` | CONFIRMED |
| 2.4: "All 1260 family A rows, all 100 family B2 rows and all 105 family B1 rows pass" | `check_ok` all True and `status` all `ok` in the three files (1260, 100, 105) | same | CONFIRMED |
| 2.4: hwb8 P1/P2 "check_dev at most 1.7e-13" | P1 1.525e-13, P2 1.619e-13, both `status ok` | `family_B1_counts.csv` | CONFIRMED |
| 2.4: B2 "largest deviation ... is 7.1e-6" | max `target_dev` = 7.102e-6 | `family_B2_counts.csv` | CONFIRMED |
| 2.5: "The 24 rows are in results/certificates.csv ... floor <= T_zx holds on all 24 rows, and P1 and P2 give the same T_zx on every row" | 24 rows; lde_floor <= t_zx_P1 and <= t_zx_P2 on 24/24; t_zx_P1 == t_zx_P2 on 24/24; `invariant_ok` all True | `certificates.csv` | CONFIRMED |
| 2.6: "468 noiseless runs and 68 depolarising runs" | 468 rows (A 432, B1 36); 68 rows (A 40, B1 28) | `selene_noiseless.csv`, `selene_depolarizing.csv` | CONFIRMED |
| 2.6: "144 family A circuits with n <= 10 and 12 family B1 circuits with n <= 10 under P0, P1 and P2" | A 144 circuits, B1 12, max n = 10 both, pipelines {P0, P1, P2}, shots 2000 | `selene_noiseless.csv` | CONFIRMED |
| 2.6: "No run was flagged ... and no shot landed outside the exact support" | sum(flag) = 0, sum(TVD > 4 TVD_scale) = 0, sum(shots_outside_support) = 0 | `selene_noiseless.csv` | CONFIRMED |
| 2.6: "32 of 34 runs agree" (gates_meas_init) | agree_2sd sum = 32 of 34; p_meas column = 1.35e-3, p_init = 4e-5 in that variant | `selene_depolarizing.csv` | CONFIRMED |
| 2.6: "540 rows, 108 circuits x 5 pipelines" and "35 rows, 7 circuits x 5 pipelines" | 540 rows / 108 files / 5 pipelines; 35 / 7 / 5 | `family_A_proxy_h22e.csv`, `family_B1_proxy_h22e.csv` | CONFIRMED |
| 2.6: "P1, P3 and P4 are above P0 ... on 14 of 15, 14 of 15 and 15 of 15 family B1 circuits" | 14, 14, 15 (see item 2) | `family_B1_counts.csv` | CONFIRMED |

## Item 2. Section 3.2, family B1 counts after the hwb8 merge

| Claim | Recomputed | Verdict |
|---|---|---|
| "P2 is below P0 on 13, equal on 2 (qft_4 and gf2_pow_4_mult) and above on none" | below 13, equal 2 (gf2_pow_4_mult, qft_4), above 0 | CONFIRMED |
| "The mean reduction against P0 is 6.9 %" | mean over 15 circuits of 100 (1 - P2/P0) = 6.909 % (the ratio-of-means form would give 5.73 %, so the per-circuit mean is the convention used) | CONFIRMED |
| "vbe_adder_3, 56 to 41 ZZPhase gates, 26.8 %" | 56 -> 41, 26.786 % | CONFIRMED |
| "P1 is above P0 on 14 of 15 and below on one (vbe_adder_3)" | above 14, below 1 (vbe_adder_3), equal 0 | CONFIRMED |
| "P3 is above P0 on 14 of 15 and below on one (mod5_4)" | above 14, below 1 (mod5_4) | CONFIRMED |
| "P4 is above P0 on 15 of 15" | above 15 | CONFIRMED |
| hwb8 "P1 gives 8305 ... P2 gives 5587, a reduction of 5.5 %" | 8305, 5587, 100 (1 - 5587/5912) = 5.497 % | CONFIRMED |
| hwb8 P1/P2 rows "status ok", "check_dev at most 1.7e-13", "T-count at 3517" | status ok, ok; check_dev 1.525e-13, 1.619e-13; t_count_zx 3517, 3517 (P4 also 3517) | CONFIRMED |
| hwb8 "completed P1 in 886 s and P2 in 844 s" (3.2), "885.6 s" and "843.8 s" (5) | t_wall 885.606, 843.800; log "total wall 886s" | CONFIRMED |
| "T after ZX ... P1 and P2, which agree on every circuit" | t_count_zx P1 == P2 on 15/15 | CONFIRMED |
| Table B1 cells: tof_3 P1 22; hwb6 P3 189; grover_5 P4 278; mod_mult_55 P1 71; vbe_adder_3 P2 41; gf2_pow_4_mult P4 290; plus T after ZX hwb6 75, grover_5 166 and "P2 vs P0 %" grover_5 9.2 (22/240), mod_red_21 5.7 (5/88) | all equal to `family_B1_counts.csv` | CONFIRMED |

## Item 3. Section 3.4, certificates

| Claim | Recomputed from `certificates.csv` | Verdict |
|---|---|---|
| "configuration means ... are 99.84, 99.79, 99.57 and 99.76 %" (3.3 and 3.4) | mean floor_over_t_zx_P2 by (n, eps): (2, 1e-3) 99.839, (2, 1e-5) 99.786, (3, 1e-3) 99.566, (3, 1e-5) 99.760 | CONFIRMED |
| "minimum over the 20 circuits is 99.28 % (haar_n3_eps1e-03_s5, floor 2478 against 2496)" and "maximum is 100.00 % (haar_n2_eps1e-03_s3)" | min 99.279 on haar_n3_eps1e-03_s5 (2478/2496); max 100.0 on haar_n2_eps1e-03_s3 (630/630) | CONFIRMED |
| "floor <= T after ZX holds on 24 of 24 rows ... equal on 24 of 24 rows" | 24/24 and 24/24 | CONFIRMED |
| B1 ratios "25.00 % for barenco_tof_3 and mod5_4, 26.67 % for tof_3 and 55.22 % for qft_4" | 4/16 = 25.00, 2/8 = 25.00, 4/15 = 26.67, 37/67 = 55.22 | CONFIRMED |
| "mod5_4 the floor is 2 while the ZX stage leaves 8 ... collapses at 19 of the 28 T gates" | lde_floor 2, t_zx_P2 8, collapse_count 19, t_written 28 | CONFIRMED |
| "at most 0.4 s per circuit at n = 2, at most 36.4 s at n = 3 and at most 38.5 s on the n = 5" | max wall_s 0.4, 36.4, 38.5 | CONFIRMED |
| "collapse rate here is 1.25, 1.34, 1.86 and 0.80 %" and "0.5 to 2.5 %" per instance (3.4 [O] paragraph) | means 1.252, 1.336, 1.859, 0.801 %; per-instance range 0.54 to 2.49 % | CONFIRMED |
| "at most 0.16 to 0.43 % ... and at most 0.72 % on any single instance" | 100 (1 - means) = 0.16, 0.21, 0.43, 0.24; 100 (1 - min) = 0.72 | CONFIRMED |
| Table C1 configuration block (mean T written 638.4 / 1048.4 / 2571.6 / 4220.8, mean achieved 2.19 / 2.29 / 3.14 / 1.27) | identical | CONFIRMED |
| Table C1 per-circuit block, all 24 rows of floor / T after ZX % and achieved % | identical after rounding to 2 dp | CONFIRMED |
| `main.tex` line 1813 Theorem B, 2568 Corollary cert, 2662 Theorem C | `\begin{theorem}[Exactness Barrier]\label{thm:B}`, `\begin{corollary}\label{cor:cert}`, `\begin{theorem}\label{thm:C}` | CONFIRMED |
| line 3066 caption "lde / T_tel"; lines 3076 and 3079 "99.79 +/- 0.30 [98.6] over 50" and "99.55 +/- 0.20 [99.3] over 8"; line 3108 "99.4 to 99.9 %, never below 96.9 %"; line 3118 "1.0 to 2.3 %" | 3066 is inside the caption of `\label{tab:e6}` (line 3068) and reads `\mathrm{lde}/T_{\mathrm{tel}}`; 3076: `2 & 10^{-3} & 50 & 644 & ... & 99.79\pm0.30 [98.6]`; 3079: `3 & 10^{-3} & 8 & 2570 & ... & 99.55\pm0.20 [99.3]`; 3108-3109: "averages 99.4--99.9% and never falls below 96.9%"; 3118: "it measures 1.0--2.3%" (collapse rate, line 3116) | CONFIRMED |

## Item 4. Section 3.5, noise proxy

Regression convention that reproduces the quoted numbers: no-intercept least squares a = sum(x y) / sum(x^2) with x = n_2q and y = -ln F_H; SE(a) = sqrt(SS_res / (N - 1) / sum(x^2)); R^2 centred, 1 - SS_res / sum((y - mean y)^2). With N - 2 degrees of freedom the B1 SE is 2.36e-5, which rounds to 2.4e-5, so N - 1 is the convention that reproduces "2.3e-5".

| Claim | Recomputed | Verdict |
|---|---|---|
| "a = 1.18e-3 +/- 2.3e-5 on the 35 family B1 rows, with centred R^2 0.968" | a = 1.1801e-3, SE 2.33e-5, R^2 0.9675 | CONFIRMED |
| "On the 540 family A rows ... a = 5.14e-4 +/- 1.3e-5 with centred R^2 0.612" | a = 5.139e-4, SE 1.28e-5, R^2 0.6121 | CONFIRMED |
| "Per model the slope is 2.28e-4 on ladder, 2.26e-4 on tfim and 7.58e-4 on xxz" | 2.283e-4, 2.257e-4, 7.579e-4 | CONFIRMED |
| "u = -7.9e-5 per outcome and raises the centred R^2 from 0.714 to 0.784" | fit n_2q + n_1q: R^2 0.7137; + support: u = -7.92e-5, R^2 0.7843 | CONFIRMED |
| "P0 is above P0ref on 108 of 108 circuits" | 108/108 | CONFIRMED |
| "P2 is above P0 on 43 and below on 65" | 43 above, 65 below, 0 equal | CONFIRMED |
| "P0 and P2 have the highest fidelity in every one of the nine (model, n) cells", "differ by at most 0.0056 in any cell (xxz at n = 8)" | min(P0, P2) >= max(P0ref, P1, P3) in 9/9 cells; max |P0 - P2| = 0.00556 at (xxz, 8) | CONFIRMED |
| "On xxz P0ref is below P1 in all three cells and below P3 at n = 4 and n = 6", "(30.3 against 42.0 at n = 4 under P1)" | xxz cells P0ref < P1 at n = 4, 6, 8; P0ref < P3 at n = 4, 6 and P0ref > P3 at n = 8; mean n_2q xxz n = 4: P1 30.33, P0ref 42.0 | CONFIRMED |
| "at n = 4 P1 and P3 (both 0.9893) sit above P0ref (0.9867)" | by-n means P1 0.9893, P3 0.9893, P0ref 0.9867 | CONFIRMED |
| "On ladder and tfim P0ref is above P1 and P3 ... on 36 of 36 circuits each" | per-circuit count not recomputed within the time budget (cells confirmed) | UNVERIFIABLE (not recomputed) |
| "P2 is above P0 on 7 of 7 ... P0 is above P0ref on 7 of 7. P1 is below P0 on 7 of 7 and P3 on 6 of 7. The exception is mod5_4" | 7, 7, 7, 6; exception mod5_4 (P3 0.9705 > P0 0.9689) | CONFIRMED |
| "hwb6, 0.8915 to 0.8962 with 99 to 94" | F_H P0 0.89151, P2 0.89617; n_2q 99, 94 | CONFIRMED |
| "single-outcome ideal distribution on 6 of 7 circuits (support 16 on qft_4), the xxz circuits have mean support 29.8 and the ladder and tfim circuits have mean support 107.8" | B1 supports {1,1,16,1,1,1,1}; xxz mean 29.83; ladder 107.78, tfim 107.78 | CONFIRMED |
| Table A4 pipeline block (F_H, TVD, n_2q, n_1q for P0ref, P0, P1, P2, P3) and by-n block | identical at 4 dp | CONFIRMED |
| Table A5 cells: barenco_tof_3 P0ref 0.9696; hwb6 P2 0.8962; qft_4 P3 0.9527; tof_4 P1 0.9567; mod5_4 ZZ P2 22; (plus support and ZZ P0 columns) | identical to `family_B1_proxy_h22e.csv` | CONFIRMED |

## Item 5. Section 3.6, Selene

| Claim | Recomputed | Verdict |
|---|---|---|
| Table S1 noiseless: A 144 circuits, 432 runs, max TVD 0.117, max ratio 1.111, 0 flagged, 0 outside; B1 12, 36, 0.080, 1.121, 0, 0 | A: 432 runs, max TVD 0.11678, max TVD_over_scale 1.1107, flag 0, outside 0; B1: 36, 0.0800, 1.1210, 0, 0 | CONFIRMED |
| "largest TVD ... 0.117 and the largest ratio ... 1.121" over 468 | 0.1168 and 1.1210 | CONFIRMED |
| "support is smaller than 2^n on 276 runs" | 276 | CONFIRMED |
| "agrees with the family reference to 5.7e-11" | max exact_vs_ref_maxdiff = 5.69e-11 | CONFIRMED |
| "median 0.93 and maximum 2.26" of TVD / expected | 0.928, 2.256 | CONFIRMED |
| "234 runs with support between 2 and 64 gives p < 0.01 on 4 runs and p < 0.05 on 13, against 2.3 and 11.7 expected" | 234 rows with 2 <= support <= 64, all with chi2_p_pooled; 4 below 0.01, 13 below 0.05; 2.34 and 11.70 | CONFIRMED |
| "4 runs were resampled ... none of the deviations persists" | `selene_recheck.txt` lists 4 runs, 8 reruns, all pooled p >= 0.033 | CONFIRMED |
| Table S1 depolarising rows (runs 20/20/14/14, agree 20/17/12/10, mean z -0.13/0.83/-0.50/1.24, sd z 0.82/1.17/1.18/1.11, max abs z 1.73/3.52/2.81/2.43, mean diffs) | all reproduced; sd z reproduces only with population sd (ddof = 0: 0.820, 1.165, 1.177, 1.112; sample sd would be 0.84, 1.20, 1.22, 1.15). Convention not stated in the caption | CONFIRMED (convention ddof = 0 unstated) |
| "32 of 34 runs, with mean z = -0.29, standard deviation of z 1.00 and largest abs z 2.81" | 32/34, mean -0.285, sd ddof0 0.999 (ddof1 1.014), max 2.809 | CONFIRMED |
| "gates_only ... 27 of 34 runs with mean z = +1.00" | 27/34, mean 0.999 | CONFIRMED |
| "-0.0056 in gates_meas_init ... falls to -0.0016" | -0.0056, -0.0016 | CONFIRMED |
| "17 circuits under P0 and P2, in two variants of 34 runs" | A 10 + B1 7 circuits, pipelines {P0, P2}, 34 per variant | CONFIRMED |
| 3.6 last paragraph: "465 s for the 468 noiseless runs ... 68 s for the 68", "median is 1.4 s and the maximum 10.3 s (P1 on xxz_n10_r4_disorder_s1)" | `selene_run.log`: 465.4 s, 68.0 s, total 533.5 s; t_total median 1.43 s, max 10.31 s on xxz_n10_r4_disorder_s1 P1 | CONFIRMED |

## Item 6. Section 4, cost model

| Claim | Recomputed from `cost_model_metrics.csv`, `cost_model_coefficients.csv` | Verdict |
|---|---|---|
| Table M1 lofo A -> B1: physics 0.785 / 0.0151, ols 0.560 / 0.0252, ridge 0.840 / 0.0150, gbr 0.805 / 0.0083, n 35 | 0.7850 / 0.01508, 0.5596 / 0.02521, 0.8402 / 0.01504, 0.8046 / 0.00834, 35 | CONFIRMED |
| Table M1 lofo B1 -> A: -3.513 / 0.0430, -261.894 / 0.1971, -0.605 / 0.0259, 0.326 / 0.0184, n 540 | -3.5131 / 0.04297, -261.8935 / 0.19712, -0.6046 / 0.02590, 0.3256 / 0.01839, 540 | CONFIRMED |
| Table M2 cells: n_2q OLS A 3.73e-04 (11.8); n_2q_offsupport OLS A+B1 6.19e-04 (30.3); n_qubits ridge A+B1 3.49e-03; n_2q_offsupport GBR 1.47e-03 (7.0e-04) | 3.730e-4 (11.76); 6.194e-4 (30.34); 3.485e-3; 1.466e-3 (6.99e-4) | CONFIRMED |
| 4.5: "R^2 0.805 and MAE(F_H) 0.0083 ... 0.785 and MAE(F_H) 0.0151 ... 0.326" | as above | CONFIRMED |
| 4.5: "lowers the B1 error ... by 0.0067 in MAE(F_H), a factor 1.81" | 0.015077 - 0.008338 = 0.00674; ratio 1.808 | CONFIRMED |
| 4.5: "1.47e-3 ... 5.95e-5, a factor 24.6 lower"; "2.89e-4 + 6.19e-4 = 9.08e-4" | 24.63; 9.08e-4 | CONFIRMED |
| 4.5: "60.7 against 37.3 for ladder and 31.0 for tfim, and 4 of the 180 xxz rows exceed" | 60.7, 37.3, 31.0; 4 rows | CONFIRMED |
| 4.1: "mean support fraction ... 0.758 in family A and 280 of its 540 rows have full support ... 0.088 ... 0.0078, 0.031 and 0.5" | 0.7579, 280, 0.0882, {0.0078, 0.03125, 0.5} | CONFIRMED |
| 4.3: "27 of the 54 classes of A have three disorder seeds. Within one class and one pipeline the three seeds have identical n_2q, identical depth_2q and identical support_size in 265 of the 270 class-pipeline groups, and their F_H values lie within 0.0056" | 54 classes, 27 with three seeds. Only 135 class-pipeline groups have three seeds; identical in 130 of those 135. The figure 265 of 270 is obtained only by counting the 135 single-seed groups as trivially identical. Max F_H spread 0.00553 | MISMATCH (denominator: 130 of 135 three-seed groups, not 265 of 270; the sentence attributes three seeds to all 270) |

## Item 7. Section 5, tests and versions

| Claim | Result | Verdict |
|---|---|---|
| `pipelines/test_compile.py` "6 of 6 passed", "2 s" | 6 `ok` lines, "all tests passed", 1.8 s wall | CONFIRMED |
| `model/test_cost_model.py` "7 of 7 passed", "under 1 s" | 7 `ok` lines, 0.4 s | CONFIRMED |
| Versions: pytket 2.18.4, pyzx 0.10.7, selene-sim 0.3.4, guppylang 1.1.2 | `pip show`: 2.18.4, 0.10.7, 0.3.4, 1.1.2 (also pytket-quantinuum 0.59.3, numpy 2.5.3, pandas 2.3.3, scikit-learn 1.9.1, hugr 0.18.8, Python 3.13.16 match) | CONFIRMED |

## Item 8. Internal consistency

Occurrences in the report body (lines 1 to 556): line 100 "14 of 15, 14 of 15 and 15 of 15"; line 183 "13" / "6.9 %" / "14 of 15" twice / "15 of 15"; line 506 "status = timeout", "103 of 105 rows ok", "--timeout 5400"; line 508 "13 of 14" and "12 of 14" (quoted history of the earlier verification, correctly attributed to the pre-merge status document); line 512 "14 of 15, P3 on 14 of 15 and P4 on 15 of 15"; line 526 "5.50 %", "13 of 15 ... with two ties". All consistent with the merged `family_B1_counts.csv`. "7.0 %" and "12 of 1" do not occur in the body.

Changelog lines inconsistent with the merged data if read as current state (they are superseded by the "Integration" entry at line 612 but are not marked as superseded):
- line 573: "the recomputed 13 of 14, 14 of 15 and 15 of 15 counts" (P1 is 14 of 15 after the merge).
- line 584: "with the note that it is not merged into `results/family_B1_counts.csv`" (it is merged).
- line 602: "not merged into the main CSV" (it is merged).
- line 604: "P1 13 of 14" (14 of 15 after the merge).
- line 609: "Open: the hwb8 rows need merging" (closed at line 612, but the "Open" label remains).

Cross-references: every "Section x.y" in the body (1, 2.2, 2.3, 2.5, 2.6, 3, 3.4, 3.7, 4, 5, 6, 7) resolves to a heading. "Section 3.3" occurs only in the changelog (line 613) as a quoted old string. Every "Table X" (A1, A2, A3, A4, A5, B1, B2, C1, S1, M1, M2) has a `<!-- TABLE:... -->` marker and a caption; "Table E6" and "Table tab:e6" refer to the manuscript. Figures 1 to 4 exist. Section 3.7 is a `[PENDING: emulator]` placeholder and is referenced at lines 325 and 357 as the replacement for the proxy, which is consistent with its content.

## Item 9. Prose rules (body, lines 1 to 556)

Counts: semicolons 0; em-dashes 0; en-dashes 0; "rather than" 0; "usually" 0; "in general" 0; "typically" 0; "often" 0.

Sentences with more than two commas, after removing set lists, formulas, tuples, citations, code paths and bracketed parameter lists:
- line 181, Figure 2 caption: "ZZPhase count per circuit for P0ref, P0 and P2, log scale, circuits ordered by qubit number then T-count." Three commas, a list followed by two appended fragments. Offender.
- Borderline (a list carrying two commas plus one clause comma): line 284 "and no leakage, crosstalk or dephasing, to be replaced by emulator runs"; line 325 "no leakage, crosstalk, idle dephasing or the RZZ angle scaling ..., so it ranks"; line 524 "25.0 % (barenco_tof_3), 25.0 % (mod5_4), 55.2 % (qft_4) and 26.7 % (tof_3) of the post-ZX T-count, so there the certificate". `[O]` These pass if the list exemption is applied to the list part.

No other offender found.
