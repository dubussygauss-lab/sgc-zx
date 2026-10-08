# Verification of H2-2E pooled results (2026-10-09a)

Independent verifier. Did not import `submit/h22e_pooled.py` or `submit/h22e_stats.py`. Ideal distributions from `submit/common.reference_probs("B1", file)` only. All other quantities recomputed from the raw `counts` of the 18 JSONs under `results/emulator/nexus_H2-2E*/`. Verification scripts were kept outside the repository (scratchpad); the code is summarised below so it can be rerun.

Overall verdict: numbers PASS. Wording: 2 FAIL (minor, omission), both outside Section 3.7.1.

## 1. Data integrity

| Check | Result | Verdict |
|---|---|---|
| `[F]` Number of H2-2E JSONs | 18 (6 in `nexus_H2-2E/`, 4 each in `_r2`, `_r3`, `_r4`) | PASS |
| `[F]` Counts sum per JSON | 1000 in all 18 | PASS |
| `[F]` Repeat job ids (`_r2`..`_r4`) | 12 ids, 12 distinct. All 18 ids distinct | PASS |
| `[F]` CSV status | each of the 18 `result_path` values has exactly one row in `results/emulator_jobs.csv`, its `job_id` equals the JSON `job_id`, status COMPLETED. JSON payload status COMPLETED, platform H2-2E, shots 1000, options `noisy_simulation: True` | PASS |
| `[F]` Stored per-run F_H | equals my recomputation from counts on all 18 files | PASS |
| `[F]` Total hqc_estimate, 18 JSONs | 5933.2 HQC = 59.332 % of 10,000 (report: 5933.2, 59.3 %) | PASS |
| `[F]` Six original jobs / twelve repeats | 1840.0 / 4093.2 HQC (report: same) | PASS |

## 2. Recomputed statistics vs Table E3 and pooled prose (Section 3.7.1)

Method. F_H = (sum_x sqrt(p_x q_x))^2. Pooled cell = summed counts of 4 runs (4000 shots). sd: binomial sqrt(F(1-F)/4000) on vbe_adder_3 (single ideal outcome, verified support size 1). grover_5 (ideal support 64 outcomes, uniform 1/64): sd over 4000 multinomial bootstrap resamples of pooled counts, my seed 12345 (not the report seed). Difference sd = sqrt(sd0^2 + sd2^2). Two-sided p = 1 - erf(|z|/sqrt 2). Holm over the two circuits. Predicted gain = F0_pooled (exp(1.1801e-3 dN_2q) - 1). Homogeneity: chi-square contingency over the 4 runs (vbe_adder_3: success/failure; grover_5: 64 support bins plus one other bin, empty columns dropped).

| Quantity | Recomputed | Report | Verdict |
|---|---|---|---|
| vbe_adder_3 P0 per-run F_H | 0.954, 0.947, 0.951, 0.956 (range 0.9470 to 0.9560) | 0.9470 to 0.9560 | PASS |
| vbe_adder_3 P2 per-run F_H | 0.959, 0.968, 0.964, 0.960 (range 0.9590 to 0.9680) | 0.9590 to 0.9680 | PASS |
| grover_5 P0 per-run F_H | 0.8652, 0.8482, 0.8617, 0.8626 | 0.8482 to 0.8652 | PASS |
| grover_5 P2 per-run F_H | 0.8728, 0.8710, 0.8560, 0.8400 | 0.8400 to 0.8728 | PASS |
| vbe_adder_3 pooled F_H, sd (P0) | 0.9520, 0.0034 | 0.9520, 0.0034 | PASS |
| vbe_adder_3 pooled F_H, sd (P2) | 0.96275, 0.0030 | 0.9628, 0.0030 | PASS |
| grover_5 pooled F_H, sd (P0) | 0.8704, 0.0054 | 0.8704, 0.0053 | PASS (bootstrap, 1.9 % apart) |
| grover_5 pooled F_H, sd (P2) | 0.8711, 0.0054 | 0.8711, 0.0053 | PASS (bootstrap) |
| vbe_adder_3 P2 - P0, sd, z | +0.01075, 0.004515, +2.381 | +0.0108, 0.0045, +2.38 | PASS |
| vbe_adder_3 two-sided p | 0.0173 | 0.017 | PASS |
| grover_5 P2 - P0, sd, z | +0.0007, 0.0076, +0.099 | +0.0007, 0.0075, +0.10 | PASS (bootstrap) |
| grover_5 two-sided p | 0.921 | 0.92 | PASS |
| Holm-adjusted p | vbe_adder_3 0.0346, grover_5 0.921 | 0.035, 0.92 | PASS |
| Predicted gain vbe_adder_3 (dN_2q = 15) | 0.01700 | 0.0170 | PASS |
| Predicted gain grover_5 (dN_2q = 22) | 0.02287 | 0.0229 | PASS |
| vbe_adder_3 measured - predicted, in sd of difference | -1.3845 | -1.38 | PASS |
| grover_5 measured - predicted, in sd of difference | -2.93 (bootstrap sd 0.0076) | -2.94 | PASS (bootstrap) |
| Homogeneity p vbe_adder_3 P0 / P2 | 0.800 / 0.702 (chi2 1.01, 1.42, dof 3) | 0.80 / 0.70 | PASS |
| Homogeneity p grover_5 P0 / P2 | 0.908 / 0.685 (chi2 166.5, 182.1, dof 192, min expected cell 7.75 and 9.0) | 0.91 / 0.68 | PASS |
| "No cell rejects homogeneity at 0.05" | all p >= 0.685 | same | PASS |
| "pooled F_H of grover_5 under P0 exceeds every single-run value" | 0.8704 > 0.8652 | same | PASS |
| Section 1.5: relative gain 1.13 %, predicted 1.79 % | 1.129 %, 1.786 % | 1.13 %, 1.79 % | PASS |

`[O]` A naive homogeneity test that compares per-run F_H with the pooled F_H is biased on grover_5, because single-run F_H of a spread distribution sits below the pooled value. The report uses the contingency test, which is the correct choice.

## 3. Single-run numbers quoted in Section 3.7.1 (Table E2 prose) and SUMMARY

| Quantity | Recomputed | Report | Verdict |
|---|---|---|---|
| Diff / sd / z: vbe_adder_3, hwb6, grover_5 | +0.0050/0.0091/+0.55, -0.0150/0.0124/-1.21, +0.0076/0.0160/+0.48 | same | PASS |
| Predicted ratio | 1.0179, 1.0059, 1.0263 | same | PASS |
| Predicted gain | 0.0170, 0.0055, 0.0228 | same | PASS |
| Predicted gain in sd | 1.87, 0.44, 1.42 | same | PASS |
| (predicted - measured) in sd | 1.32, 1.66, 0.95 | same | PASS |
| Shots for 2-sd resolution | 1147 (1146.5), 20460, 1974 (1973.8) | 1147, 20462, 1974 | PASS. `[O]` hwb6 differs by 2 shots, consistent with the refit slope at full precision in place of 1.1801e-3 |

## 4. Wording and claim strength

Criterion: "resolved" only where |z| >= 2 and Holm p < 0.05. grover_5 must be stated as not resolved.

| Location | Finding | Verdict |
|---|---|---|
| Section 3.7.1, `[O]` paragraph after Table E3 ("On vbe_adder_3 the pooled data resolve ...") | vbe_adder_3 resolved with z = +2.38, Holm 0.035. grover_5 "not resolved". Slope miss on grover_5 stated | PASS |
| Section 3.7.1, `[F]` summary paragraph ("At 4000 shots per pipeline the pooled runs resolve ...") | resolved claim carries z and Holm p. "They do not resolve grover_5" | PASS |
| Section 3.7.1, closing `[O]` ("vbe_adder_3 is the one circuit ...") | consistent | PASS |
| Section 6, emulator paragraph ("vbe_adder_3 at 4000 shots per pipeline is the only emulator comparison that resolves ...") | z given, "No other emulator comparison of P2 against P0 is resolved" covers grover_5. Holm p not quoted | PASS. Optional: add "and a Holm-adjusted p of 0.035" after "z = +2.38" |
| Section 1.5 ("On grover_5 the pooled difference is +0.0007 with z = +0.10 (Section 3.7.1).") | grover_5 not stated as not resolved. The vbe_adder_3 slope comparison is given but the grover_5 slope miss (2.94 sd below prediction) is omitted, so the section reports only the favourable comparison | FAIL (W1) |
| `submission/SUMMARY.md`, "Emulator runs" `[F]` ("On grover_5 it is +0.0007 with z = +0.10.") | same omission: grover_5 not stated as not resolved, slope miss absent | FAIL (W2) |

## 5. FAIL list and exact fixes

W1. `report/report_v5.md` Section 1.5, last sentence of the H2-2E paragraph.
Replace
"On grover_5 the pooled difference is +0.0007 with z = +0.10 (Section 3.7.1)."
with
"On grover_5 the pooled difference is +0.0007 with z = +0.10 and is not resolved at 4000 shots per pipeline. It lies 2.94 sd of the difference below the predicted gain of 0.0229 (Section 3.7.1)."

W2. `submission/SUMMARY.md`, section "Emulator runs", `[F]` paragraph.
Replace
"On grover_5 it is +0.0007 with z = +0.10."
with
"On grover_5 it is +0.0007 with z = +0.10 and is not resolved. It lies 2.94 sd below the predicted gain of 0.0229."
Then rerun `check_summary_numbers.py` (0.0229 and 2.94 both occur in `report/report_v5.md`) and rebuild the package.

No numerical FAIL.
