# Verification of the finals plan and the notebook execution (9 October 2026, c)

Verifier: an agent that did not produce the work. Scope: `report/report_v5.md` Section 6 (lines 879 to 901), the notebook sentences of Section 7 (line 915) and `README.md` (line 75), `report/notebook_skeleton.py`, `report/notebook_executed.html`, cross-references after the renumbering. Nothing was edited except this file.

Method `[F]`. All numbers were recomputed by an independent script (scratchpad `verify.py`, not committed) that does not import `value/finals_plan.py`, `submit/h22e_pooled.py` or `submit/common.py`. It parses the compiled QASM in `results/compiled/{P0,P2}/`, simulates the ideal distribution with its own numpy statevector (U1q, rz, RZZ), sums the four runs per cell from `results/emulator/nexus_H2-2E*/`, and computes F_H = (sum sqrt(p q))^2. The count keys are read with c[0] as the leftmost bit. The reverse order gives F_H near 0.04 on grover_5, so the order is unambiguous.

## Verdict

`[F]` FAIL on 7 items, all minor or moderate. Every Section 6 number except one (the 0.80-power shot count) and every HQC value reproduce. No finals budget is invented. The H2-2SC job and the notebook guard check out.

## Recomputed numbers

| Quantity | Report | Recomputed | Result |
|---|---|---|---|
| vbe_adder_3 pooled F_H P0 / P2 (4 runs, 4000 shots) | 0.9520 / 0.9628 | 3808/4000 = 0.9520 / 3851/4000 = 0.96275 | PASS |
| vbe_adder_3 per-run ranges | 0.9470 to 0.9560 / 0.9590 to 0.9680 | same | PASS |
| vbe_adder_3 difference, binomial sd, z | +0.0108, 0.0045, +2.38 | +0.01075, 0.004515, +2.381 | PASS |
| Shots for 2 sd at the measured gain | 2823, rounded to 2900 | 2823.007 | PASS |
| sd and expected z at 2900 | 0.0053, 2.03 | 0.00530, 2.027 | PASS |
| One-sided power at 2900 (z_crit 1.645) | 0.65 | 0.649 | PASS |
| Smallest confirming difference at 2900 | 0.0087 | 0.00872 | PASS |
| Shots for power 0.80 | 4363 | 4363.35, so 4364 (power at 4363 is 0.79997) | FAIL (F2) |
| grover_5 pooled F_H P0 / P2 | 0.8704 / 0.8711 | 0.8704 / 0.8711 | PASS |
| grover_5 per-run ranges | 0.8482 to 0.8652 / 0.8400 to 0.8728 | same | PASS |
| grover_5 prediction F_H(P0)(exp(22a) - 1), a = 1.1801e-3 | 0.0229 | 0.02289 | PASS |
| grover_5 shortfall | 0.0229 - 0.0007 = 0.0221 | 0.02289 - 0.00075 = 0.02214 | value PASS, displayed arithmetic FAIL (F1) |
| grover_5 bootstrap sd of difference | 0.0075 | 0.00751 to 0.00756 (own streams, B = 4000, two seeds) | PASS |
| Shortfall in sd | 2.94 | 2.93 to 2.95 | PASS |
| Shots for 2 sd at the shortfall | 1854, rounded to 1900 | 1835 to 1865 by bootstrap stream | PASS (within bootstrap Monte Carlo error, rounding to 1900 unaffected) |
| sd and power at 1900 | 0.0109, 0.65 | 0.01088 to 0.01094, 0.648 to 0.652 | PASS |
| HQC vbe_adder_3 P0 at 2900 (N_1q 73, N_2q 56, N_M 10 + 10) | 430.1 | 430.14 | PASS |
| HQC vbe_adder_3 P2 at 2900 (60, 41, 20) | 335.6 | 335.60 | PASS |
| HQC grover_5 P0 at 1900 (313, 240, 9 + 9) | 1070.1 | 1070.14 | PASS |
| HQC grover_5 P2 at 1900 (346, 218, 18) | 999.1 | 999.08 | PASS |
| Primary / secondary / total | 765.7 / 2069.2 / 2835.0 | 765.74 / 2069.22 / 2834.96 | PASS |
| Per-shot HQC (limit 50) and shots per job (limit 10,000) | within limits | max 0.561 HQC per shot, max 2900 shots | PASS |
| H2-2E stored HQC estimates, 18 JSON payloads | 5933.2, remainder 4066.8 | 5933.2, 4066.8 | PASS |
| 1000-shot HQC from QASM vs Table E2 | 151.6, 119.0, 243.0, 232.6, 565.6, 528.2 | identical | PASS |
| ZZ removed by P2 | 15 (vbe), 22 (grover) | 56 - 41, 240 - 218 | PASS |
| PSEL choice on vbe_adder_3 | P2 | `value/selector_ledger_circuits.csv` row 13: P2 | PASS |

## Other checks

- `[F]` PASS. No finals HQC budget is stated. Section 6 says none is published and conditions the fallback on "the finals budget" without a number. `docs/platform_notes.md` section 3.4 quotes the 10,000 shots per job and 50 HQC per shot limits. Reference 6 is the Helios costing page and is tagged as an inference.
- `[F]` PASS. Dates (shortlist 20 October, Grand Finale with hardware access 21 October, Submission 2 14 November, finals 19 November, email of 25 August 2026) match `claude/grand-challenge-plan.md` section 1.
- `[F]` PASS. Both decision rules are stated before any hardware data, and no hardware data exist in the repository. The primary outcomes (z >= 1.645, z <= -1.645, otherwise) are exhaustive and disjoint. The secondary outcomes are exhaustive with precedence to refutation. Joint refutation and gain z >= 1.645 would need a prediction of 3.29 sd (0.036 at 1900 shots), above the largest possible prediction 0.0263.
- `[F]` PASS. Cross-references after the renumbering. Scoring map row Problem and Value "Section 1, Section 7" now points to Limitations, which it named as Section 6 before the commit 754595d. Row Technical names "Section 6 for the H2 hardware plan". Section 5 script table row "Finals hardware plan, Section 6", the verification list "(now Section 7)" and "(then numbered 6)", and Section 7 "Section 6 gives the plan" all resolve. Headings are 6 Plan, 7 Limitations, 8 Team and roles. No other "Section 6/7/8" reference in lines 1 to 942 points to a wrong section. Changelog lines before 9 October keep the numbering of their time.
- `[F]` PASS. Section 5 says nine verification reports. Nine files `results/verification_2026-10-0*.md` existed before this one. This file makes ten (see N5).
- `[F]` PASS. `python3 -m pytest value/test_finals_plan.py -q` gives 5 passed in 6.9 s.
- `[F]` PASS. Job `AFByb3ZpZGVySm9iAaEdzTywfrOWhGbnlXxd-w` is row 54 of `results/emulator_jobs.csv`: platform `nexus:H2-2SC`, file tof_3.qasm, pipeline `select:P2`, 1000 shots, status COMPLETED, cost column `{"duration": null}`. The raw payload `results/emulator/nexus_H2-2SC/notebook_select/tof_3.json` reports platform H2-2SC, status COMPLETED, 1000 all-zero shots and no key containing cost, hqc or credit. "No cost field" holds.
- `[F]` PASS. It is the only H2-2SC row with a `select:` pipeline, so "executed once" holds.
- `[F]` PASS. `report/notebook_executed.html` contains the submission cell output with the job id, reported platform H2-2SC, team `learned_zx_rewriting` and status COMPLETED.
- `[F]` PASS. `python3 -m pytest report/test_notebook_submit.py -q` gives 20 passed in 0.65 s. `require_free_checker` raises AssertionError explicitly (not by a bare assert, so it survives `python -O`) for any non-string or any name not ending in "SC". `submit_free_check` calls it before any import or client, and the submission cell calls it before the gate.
- `[F]` PASS. Style of the new text (Section 6 lines 881 to 901, Section 7 line 915, README line 75). No semicolon, em-dash, en-dash, "rather than" or hedge adverb. No sentence has more than two commas. Every paragraph opens with a tag.

## FAIL list with exact fixes

F1 `[F]` Section 6, line 895, "0.0229 - 0.0007 = 0.0221". The rounded operands give 0.0222. The value 0.0221 is right only before rounding (0.02289 - 0.00075 = 0.02214). Fix: replace with "The measured H2-2E shortfall is 0.02289 - 0.00075 = 0.02214 with sd 0.0075 at 4000 shots per pipeline."

F2 `[F]` Section 6, line 889, "A power of 0.80 would need 4363 shots per pipeline." The exact requirement is 4363.35 shots. At 4363 the power is 0.79997. Fix: "4364". The same value appears in `value/finals_plan.md` ("Power 0.80 would need 4363"), so `value/finals_plan.py` should take the ceiling.

F3 `[O]` Section 6, lines 891 and 897. The decision rules do not define how z and sd are computed from the hardware counts. Section 6 line 885 defines only the planning sd scaled from the emulator. A rule stated before data needs its statistic fixed. Fix, append to line 891: "The z is the hardware difference F_H(P2) - F_H(P0) divided by its binomial sd, the square root of F_0 (1 - F_0) / N + F_2 (1 - F_2) / N at N shots per pipeline." Append to line 897: "The sd is that of the hardware difference from 4000 multinomial bootstrap resamples of the counts of each pipeline with seed 20261008. The sampling error of the prediction is neglected." `[F]` Neglecting it changes the sd by a factor of about (1 + 0.0263) on the P0 term, about 1.3 % on the total.

F4 `[O]` Tag blurring in Section 6. Plan choices sit inside `[F]` paragraphs and facts inside `[O]` paragraphs. Fixes:
- line 889: insert `` `[O]` `` before "The plan rounds this up to 2900." and `` `[F]` `` before "At 2900 shots".
- line 895: insert `` `[O]` `` before "The plan rounds this up to 1900." and `` `[F]` `` before "There the sd".
- line 899: open the paragraph with `` `[O]` The plan has four jobs, one per circuit and pipeline. `` then `` `[F]` `` before "vbe_adder_3 costs".
- line 887: insert `` `[F]` `` before "PSEL picks P2" and `` `[O]` `` before "The alternative hypothesis".
- line 893: insert `` `[F]` `` before "On H2-2E the measured gain" and `` `[O]` `` before "The secondary test does not enter".

F5 `[F]` Section 6, line 881, "Hardware access opens only at the Grand Finale on 21 October 2026." The team plan records "Grand Finale (hardware access) 21 October" and does not say "opens" or "only". Fix: "The team plan records hardware access at the Grand Finale on 21 October 2026."

F6 `[F]` `report/notebook_skeleton.py`, cell "What this notebook shows and what is open", "the emulator tables E1 and E2 and this notebook". The scoring map now names tables E2 and E3 and Section 6. Fix: "the Selene tables S1 and S2, the emulator tables E1 to E3, the H2 hardware plan of Section 6 and this notebook". Then re-export `report/notebook_executed.html` without re-running the submission cell, or leave the export and state that it predates the text change.

F7 `[F]` Dates of the notebook execution. The ledger timestamp is 2026-10-08T23:15:24Z, which is 9 October 01:15 CEST. Section 7 says "on 9 October 2026" and README line 75 sits under the header "Status on 8 October 2026:". Fix: Section 7 "on 9 October 2026 (CEST, ledger time 2026-10-08T23:15Z)". README header "Status on 9 October 2026:".

## Notes, no fix required

- N1 `[O]` The primary rule calls z <= -1.645 a refutation. That branch is a one-sided test in the opposite direction at 0.05. The rule is then a two-sided test at 0.10 overall. "Shows that P2 lowers F_H" is more precise than "refutes".
- N2 `[O]` Both tests are designed at power 0.65. vbe_adder_3 was taken forward as the only resolved circuit of three, so the measured gain 0.0108 may be biased upward and the true power lower. `[F]` Power 0.80 at the measured gain costs 1147.3 HQC at 4364 shots (644.8 + 502.5), against 765.7 at 2900.
- N3 `[F]` `submission/report.md` predates Section 6. Its scoring map has no Section 6 entry and its line 889 lacks "Section 6 gives the plan". The package needs a rebuild before upload.
- N4 `[F]` The grover_5 shot count 1854 depends on the bootstrap stream. Two independent streams gave 1835 to 1865. The rounding to 1900 and the power 0.65 hold for any sd between 0.00745 and 0.00760.
- N5 `[F]` After this file is committed Section 5 should say ten verification reports and list `results/verification_2026-10-09c.md`.
