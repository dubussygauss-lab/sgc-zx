# Verification 2026-10-08a (independent, files only)

Verifier worked from the repository files only, no agent reports. Environment: pytket 2.18.4, pyzx 0.10.7. Every recomputed value below comes from code run on the named files on 8 October 2026. Commit at time of check: c30fb04.

## 1. B1x numbers in report_v3.md (Section 1, 2.1, 2.4, 3.2.1, 5, 6)

Inputs: `results/family_B1x_counts.csv` (24 rows), `bench/family_B1x/manifest.csv` (8 rows), `results/family_B1x_summary.csv`.

| Claim (report) | Recomputed | Files | Verdict |
|---|---|---|---|
| 8 circuits, 24 rows, pipelines P0ref, P0, P2 | 8 files, 24 rows, {P0, P0ref, P2} | counts.csv | CONFIRMED |
| all 24 rows `ok-unchecked`, `native`, `check_kind` none, check columns NaN | 24/24, 24/24, 24/24, check_dev NaN 24/24 | counts.csv | CONFIRMED |
| n from 14 to 19, largest ham15-med 1600 gates | min 14, max 19, max n_gates 1600 (ham15-med) | counts.csv, manifest.csv (n agree) | CONFIRMED |
| P2 below P0 on 5, equal on 3 (csla_mux_3, gf2_pow_5_mult, gf2_pow_6_mult), above on 0 | 5 / 3 / 0, equal set identical | counts.csv | CONFIRMED |
| aggregate ZZ P0ref 1603, P0 1329, P2 1256 | 1603, 1329, 1256 | counts.csv | CONFIRMED |
| P2 vs P0 5.5 % | 100(1 - 1256/1329) = 5.49 % | counts.csv | CONFIRMED |
| P0 vs P0ref 17.1 % | 100(1 - 1329/1603) = 17.09 % | counts.csv | CONFIRMED |
| mean per-circuit P2 reduction 4.1 % | 4.07 % | counts.csv | CONFIRMED |
| largest reduction ham15-med 427 to 379, 11.2 % | 427 to 379, 11.24 % | counts.csv | CONFIRMED |
| P0 below P0ref on 8 of 8 | 8 of 8 | counts.csv | CONFIRMED |
| depth_2q P2 below P0 on the 5 circuits with lower count, above on the 3 equal ones | below on 5, above on 3, and the two 5-sets coincide | counts.csv | CONFIRMED |
| P0ref ZZ equals CX as written on 6 of 8; rc_adder_6 93 vs 88, csla_mux_3 80 vs 76 | 6 of 8; rc_adder_6 (93, 88), csla_mux_3 (80, 76) | manifest.csv, counts.csv | CONFIRMED |
| `RemoveRedundancies` alone leaves 91 CX on rc_adder_6 and 72 on csla_mux_3 | 91 and 72 (pytket 2.18.4, rerun by verifier) | bench/family_B1x/*.qasm | CONFIRMED |
| T written 1652, T after ZX (P2) 854, `n_non_cliffordT_zx` 0 on every row | 1652 (manifest and counts agree), 854, 0 | manifest.csv, counts.csv | CONFIRMED |
| total `t_wall` 36.8 s | 36.8 s | counts.csv | CONFIRMED |
| summary CSV n_2q columns equal the counts pivot | equal for P0ref, P0, P2 on all 8 | summary.csv, counts.csv | CONFIRMED |
| Section 1: checked B1, 15 circuits, P2 below P0 on 13, equal on 2 | 15 circuits (105 rows), 13 / 2 / 0 | results/family_B1_counts.csv | CONFIRMED |

Table B1x_per_circuit (8 rows, 10 columns): every cell recomputed from counts.csv and manifest.csv (n, ZZ P0ref, ZZ P0, ZZ P2, P2 vs P0 % to one decimal, depth_2q P0, depth_2q P2, T written, T after ZX P2). All 80 cells match. Row order (n, then T written ascending) matches the caption. Verdict: CONFIRMED.

## 2. Recompilation of tof_10 and rc_adder_6 (verifier's own run)

`compile.compile_pipeline(p, circuit_from_qasm("bench/family_B1x/<f>.qasm"))`, then `compile.metrics`.

| circuit | pipeline | n_2q recomputed | n_2q CSV | depth_2q recomputed | depth_2q CSV | native | Verdict |
|---|---|---|---|---|---|---|---|
| tof_10 | P0ref | 102 | 102 | 86 | 86 | True | CONFIRMED |
| tof_10 | P0 | 85 | 85 | 77 | 77 | True | CONFIRMED |
| tof_10 | P2 | 77 | 77 | 68 | 68 | True | CONFIRMED |
| rc_adder_6 | P0ref | 88 | 88 | 54 | 54 | True | CONFIRMED |
| rc_adder_6 | P0 | 76 | 76 | 48 | 48 | True | CONFIRMED |
| rc_adder_6 | P2 | 73 | 73 | 43 | 43 | True | CONFIRMED |

Exactness check (this is the verifier's check, not a check reported in report_v3.md, whose B1x rows remain `ok-unchecked`): `compile.statevector` on |0...0>, 19 qubits for tof_10 (2^19 amplitudes, 12 s), 14 qubits for rc_adder_6.

| circuit | pair | fidelity |<psi_a|psi_b>|^2 | infidelity | Verdict |
|---|---|---|---|---|
| tof_10 | P0 vs P2 | 1.000000 | -4.0e-15 (rounding) | CONFIRMED exact on |0..0> |
| tof_10 | P0ref vs P2 | 1.000000 | 0.0 | CONFIRMED |
| tof_10 | written vs P2 | 1.000000 | 4.4e-16 | CONFIRMED |
| tof_10 | written vs P0 | 1.000000 | -5.3e-15 | CONFIRMED |
| rc_adder_6 | P0 vs P2 | 1.000000 | 2.2e-15 | CONFIRMED |
| rc_adder_6 | written vs P2 | 1.000000 | 1.8e-15 | CONFIRMED |

Scope of this check: statevector on the all-zero input only, not a unitary check. The other 6 B1x circuits were not checked here.

## 3. B1 and B1x never merged

`grep -n "23"` on report_v3.md: 9 hits, all in unrelated table cells or numbers (lines 117, 165, 168, 214, 337, 341, 376, 410, 422: cost table values, depth cells, "5.7e-11", "2.3 expected", "0.0023"). `grep -n "of 23"`: no hit. Lines 34, 225 and 655 state the two counts separately (15 circuits 13/2, 8 circuits 5/3). Verdict: CONFIRMED, no merged 23-circuit statement exists.

## 4. results/family_B2_compiled_check.csv

| Claim | Recomputed | Verdict |
|---|---|---|
| 100 rows | 100 | CONFIRMED |
| metrics_match 100/100 | 100/100 | CONFIRMED |
| reread_native 100/100 | 100/100 | CONFIRMED |
| dist_ok 99/100, single failure haar_n3_eps1e-05_s3 P0 | 99/100; failing row: haar_n3_eps1e-05_s3.qasm, P0, status FLAGGED, dist_maxdiff 2.230182e-08 | CONFIRMED |

dist_maxdiff recomputed by the verifier as max|`compile.probs_from_measured_qasm(results/compiled/<p>/<f>.qasm)` - `compile.probs(bench/family_B2/<f>.qasm)`|:

| file | pipeline | recomputed | CSV | Verdict |
|---|---|---|---|---|
| haar_n3_eps1e-05_s3 | P0 | 2.230e-08 | 2.230182e-08 | CONFIRMED (above 1e-8, fails) |
| haar_n3_eps1e-05_s3 | P2 | 7.977e-10 | 7.9772e-10 | CONFIRMED |
| haar_n2_eps1e-05_s1 | P0 | 1.613e-09 | 1.6134e-09 | CONFIRMED |
| haar_n2_eps1e-05_s1 | P0ref | 9.381e-14 | 9.3814e-14 | CONFIRMED |

## 5. report_v3.md vs report_v2.md

`git diff --no-index --stat`: 48 insertions, 7 deletions, one file. Word-level diff of the 7 modified lines:

1. header line: "v2 (7" -> "v3 (8" October 2026
2. scoring-map row (Technical performance): "A1 to B2," -> "A1 to B2 and the count-only table B1x,"
3. Section 1 opening `[O]` paragraph: "three circuit families" -> "three checked circuit families and one count-only family", pipeline sentence extended, B1 13/2 and B1x 5/3 sentences and the separation sentence added
4. Section 2.2 pipelines sentence: "and five ... on family B2." -> "five ... on family B2 and three (P0ref, P0, P2) on the count-only family B1x."
5. Section 2.4 checks paragraph: one sentence appended ("The 24 rows of family B1x were compiled with `--no-check` ...")
6. Section 5 Checks paragraph: `[F]` sentence on `--no-check` appended
7. Section 6 hwb8 paragraph: `[F]` sentence on B1x unchecked appended

Pure insertions: Section 2.1 B1x paragraph, Section 3.2.1 (heading, table block, three paragraphs), two Section 5 scripts-table rows, Changelog v2 to v3 (10 bullets). No other line differs. Verdict: CONFIRMED, changes are limited to the B1x additions, the header, the Section 1 / 2.2 / 2.4 / 5 / 6 sentences and the changelog. Note: the task statement lists "Section 5/6 sentences"; the Section 1, 2.2 and 2.4 sentence edits are also present and are all B1x-related, as the changelog bullets state.

## 6. md5 and re-injection

| item | value |
|---|---|
| md5 report_v3.md before `python report/make_tables.py --no-fig` | c2903e35a6672c5094d05e813e4cf859 |
| md5 report_v3.md after | c2903e35a6672c5094d05e813e4cf859 |
| md5 report_v2.md before / after | 7fa05ebc2da26bcd084c2f9310ca52d2 (both; matches the md5 quoted in the v3 changelog) |
| md5 report_v1.md before / after | 24af7e5bb629b3928f68a37beeaf1fb5 (both) |
| `--no-fig` flag | exists (`report/make_tables.py` line 675) |
| injection | `inject()` reports 12 table blocks injected into report_v3.md (11 into v2, 6 into v1); all three files byte-identical after re-injection |

Verdict: CONFIRMED. `git status` showed no change to any report or results file from the run (pre-existing uncommitted edits to `report/notebook_skeleton.py`, its marimo session file and the untracked `results/selene_depolarizing_full.csv` are unrelated and were not touched).

## Summary

All six items CONFIRMED. No MISMATCH, no UNVERIFIABLE. The one gap outside the report's own claims: B1x exactness is now checked by the verifier on the all-zero input for tof_10 (19 qubits) and rc_adder_6 only; the report's `ok-unchecked` status for all 24 rows remains correct as stated.
