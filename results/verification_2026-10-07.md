# Independent verification of claude/status-2026-10-06.md claims (7 Oct 2026, 21:00 CEST)

Verifier: an agent that did not see how the results were produced. Only files under /home/claude/sgc-zx were read; no agent reports. Environment: pytket 2.18.4, pyzx 0.10.7, qiskit 2.5.2. Nothing in the project was modified except this file. All numbers below are recomputed from the raw files named; [F] = verifiable by recomputation, [O] = judgement.

Scope note on family A [F]: another agent is regenerating the `xxz` subset. At verification time `results/family_A_counts.csv` (mtime 2026-10-06 22:28) and `bench/family_A/xxz_*` (mtime 2026-10-06 21:30) were unchanged, so the CSV still carries the old xxz rows. Each family A number is reported twice: on the full CSV (the figures the status doc quotes) and on the 120 non-xxz circuits (840 rows). The non-xxz numbers are the ones that survive the regeneration.

## Claim 1. Family A means, ties, deviations, status

Source files: results/family_A_counts.csv, results/family_A_summary.csv.

| Claim | Recomputed (full CSV, 36 circuits at n = 12) | Recomputed (non-xxz, 24 circuits at n = 12) | Verdict |
|---|---|---|---|
| mean ZZPhase at n = 12, P0 = 46.7 | 46.667 | 31.500 | CONFIRMED (full CSV) |
| P0ref = 93.3 | 93.333 | 63.000 | CONFIRMED |
| P1 = 248.4 | 248.444 | 244.833 | CONFIRMED |
| P2 = 50.7 | 50.667 | 31.500 | CONFIRMED |
| P3 = 227.8 | 227.778 | 187.000 | CONFIRMED |
| P2 never beats P0 on n_2q, ties 120/180 | P2 < P0: 0, ties 120, P2 > P0: 60 of 180 | P2 < P0: 0, ties 116, P2 > P0: 4 of 120 | CONFIRMED |
| max deviation 5.7e-11 for P1/P2/P4 | max dist_maxdiff 5.688e-11 (tfim_n6_r4_disorder_s2, P1); max qasm_dist_maxdiff 5.688e-11 | same rows (non-xxz) | CONFIRMED |
| ~1e-14 for P0/P0L1/P3/P0ref | max over these pipelines: check_dev 3.04e-14, dist_maxdiff 3.46e-14, qasm_dist_maxdiff 4.04e-14 | 7.3e-15 / 2.4e-14 / 1.6e-14 | CONFIRMED |
| all 1260 rows status ok | 1260 rows, 1260 `ok`, check_ok True on all | 840 rows, all ok | CONFIRMED |

[F] n_zzphase equals n_2q on every row (n_zzmax = 0 everywhere), so the "ZZPhase count" and "n_2q" claims are the same numbers.
[F] Summary vs counts: 630 groups, identical n_circuits, n_ok, n_2q, depth_2q; hqc, n_phasedx, t_total agree to 1e-13; red_vs_P0ref_pct and red_vs_P0_pct agree to 1e-13. Summary column `max_check_dev` is the max of `check_dev` (unitary/statevector check, <= 3.0e-14), not of `dist_maxdiff`; the 5.7e-11 figure is visible only in the counts CSV.
[O] After the xxz regeneration the n = 12 means and the tie count in the status doc will change; the non-xxz column above is the stable part.

## Claim 2. Compiled family A circuits: recount and HQC

Source files: results/family_A_counts.csv, results/compiled/<pipeline>/<file>.qasm (pytket `circuit_from_qasm`, hqslib1 header). Sample: 10 random non-xxz (file, pipeline) pairs, seed 20261007.

| file | pipeline | n_2q CSV / mine | PhasedX CSV / mine | hqc CSV / mine | gate set |
|---|---|---|---|---|---|
| ladder_n8_r4_disorder_s2 | P0ref | 80 / 80 | 102 / 102 | 201.4 / 201.4 | Measure, PhasedX, Rz, ZZPhase |
| tfim_n12_r4_uniform_s1 | P0ref | 88 / 88 | 135 / 135 | 232.0 / 232.0 | same |
| ladder_n12_r1_uniform_s1 | P4 | 120 / 120 | 68 / 68 | 282.6 / 282.6 | same |
| ladder_n4_r4_uniform_s1 | P0L1 | 32 / 32 | 39 / 39 | 84.8 / 84.8 | same |
| ladder_n10_r2_disorder_s3 | P2 | 28 / 28 | 49 / 49 | 90.8 / 90.8 | same |
| tfim_n8_r2_disorder_s2 | P0 | 14 / 14 | 27 / 27 | 54.4 / 54.4 | same |
| tfim_n8_r2_uniform_s1 | P0 | 14 / 14 | 27 / 27 | 54.4 / 54.4 | same |
| tfim_n10_r2_disorder_s3 | P4 | 152 / 152 | 80 / 80 | 345.0 / 345.0 | same |
| tfim_n12_r4_disorder_s3 | P4 | 452 / 452 | 220 / 220 | 977.0 / 977.0 | same |
| tfim_n6_r4_disorder_s3 | P1 | 105 / 105 | 87 / 87 | 244.4 / 244.4 | same |

Verdict: CONFIRMED on 10/10 (n_2q, n_zzphase, n_zzmax = 0, n_phasedx, n_rz, n_qubits, hqc = 5 + (n_PhasedX + 10 n_2q + 5 (n_qubits + n_measure))/5, gate set within {Rz, PhasedX, ZZPhase, ZZMax, Measure}; n_measure = n_qubits in all 10).
[F] Side observation: the CSV column `n_total` excludes the Measure gates (my total gate count minus n_measure equals n_total on all 10). Not a claim, noted for anyone reading `n_total`.

## Claim 3. Family A correctness of P2 (unitary equivalence)

Source files: bench/family_A/<file>.qasm, results/compiled/P2/<file>.qasm. Sample: 5 random non-xxz circuits with n <= 8, seed 7. Measures stripped; the measure map `measure q[j] -> c[i]` was read and applied (it was the identity permutation in all 5).

| file | n | permutation | 1 - abs(tr(U^dag V))/2^n | phase-aligned operator norm of U - V |
|---|---|---|---|---|
| tfim_n4_r2_disorder_s2 | 4 | identity | -2.2e-16 | 5.0e-11 |
| ladder_n6_r2_uniform_s1 | 6 | identity | -6.7e-16 | 9.3e-11 |
| tfim_n6_r1_disorder_s3 | 6 | identity | 0.0 | 3.5e-11 |
| ladder_n4_r2_disorder_s3 | 4 | identity | 0.0 | 7.7e-11 |
| ladder_n4_r4_disorder_s2 | 4 | identity | -8.9e-16 | 8.5e-11 |

Verdict: CONFIRMED. [F] The trace quantity is second order in the angle error, so it sits at rounding level; the first-order operator-norm distance (~1e-10, from pyzx's angle rounding) is consistent with the CSV's dist_maxdiff of 1e-11 for these rows.

## Claim 4. Family B1

Source files: results/family_B1_counts.csv (105 rows: 15 files x 7 pipelines, 103 ok, hwb8 P1/P2 `timeout` at 900 s), bench/family_B1/manifest.csv, bench/family_B1/*.qasm.

Per-circuit n_2q (status ok rows):

| file | P0ref | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| vbe_adder_3 | 66 | 56 | 55 | 41 | 61 |
| grover_5 | 288 | 240 | 256 | 218 | 322 |
| hwb6 | 116 | 99 | 130 | 94 | 189 |
| tof_3 | 18 | 15 | 22 | 14 | 25 |
| mod5_4 | 28 | 24 | 25 | 22 | 20 |
| gf2_pow_4_mult | 99 | 83 | 260 | 83 | 277 |
| qft_4 | 46 | 36 | 43 | 36 | 64 |
| (others) | barenco_tof_3 24/20/23/19/27; barenco_tof_4 48/40/41/38/54; barenco_tof_5 72/60/70/57/90; mod_mult_55 48/41/71/39/85; mod_red_21 105/88/107/83/140; tof_4 30/25/31/23/40; tof_5 42/35/48/32/56; hwb8 7118/5912/timeout/timeout/11537 | | | | |

| Claim | Recomputed | Verdict |
|---|---|---|
| vbe_adder_3 P0 56 -> P2 41 (26.8 %) | 56 -> 41, 26.79 % | CONFIRMED |
| grover_5 240 -> 218 | 240 -> 218 | CONFIRMED |
| hwb6 99 -> 94 | 99 -> 94 | CONFIRMED |
| P2 fewer ZZ than P0 on 13 of 14 completed circuits | P2 < P0 on **12** of 14; ties on gf2_pow_4_mult (83 = 83) and qft_4 (36 = 36); P2 > P0 on 0 | MISMATCH (12/14, not 13/14; difference 1) |
| P1 worse than P0 on 13/14 | 13 of 14 (exception vbe_adder_3, 55 < 56) | CONFIRMED |
| P3 worse than P0 on 14/15 | 14 of 15 (exception mod5_4, 20 < 24) | CONFIRMED |
| T-count after ZX: tof_3 21 -> 15 | t_count_as_written 21, t_count_zx 15 (P1, P2, P4 agree) | CONFIRMED |
| mod5_4 28 -> 8 | 28 -> 8 | CONFIRMED |
| vbe_adder_3 70 -> 24 | 70 -> 24 | CONFIRMED |
| grover_5 336 -> 166 | 336 -> 166 | CONFIRMED |

T-count as written, counted directly in the QASM (`t` + `tdg` lines, no `ccx` left in the files):

| file | t | tdg | total | manifest t_count_as_written | literature (my recollection, [O]) |
|---|---|---|---|---|---|
| tof_3 | 12 | 9 | 21 | 21 | 21 |
| mod5_4 | 16 | 12 | 28 | 28 | 28 |
| vbe_adder_3 | 40 | 30 | 70 | 70 | 70 |
| grover_5 | 192 | 144 | 336 | 336 | 336 |

Verdict for the T-counts: CONFIRMED against the files and the manifest. [O] The literature values (21, 28, 70, 336 before; 15, 8, 24, 166 after full_reduce) agree with what I recall from the pyzx benchmark table (Kissinger and van de Wetering, "Reducing the number of non-Clifford gates in quantum circuits"); I did not fetch the paper, so the literature comparison is from memory.

[F] Side observation: results/family_B1_hwb8_long_run.log (mtime 2026-10-07 20:55) ends in a crash, `pipelines/run_bench_B.py` line 201, `meta.merge(counts, on="file", how="right")`, `KeyError: 'file'`. The 3600 s hwb8 rerun announced in the status doc has not produced rows; hwb8 P1/P2 are still `timeout` in the counts CSV (mtime 2026-10-06 23:11).

## Claim 5. Family B2

Source files: bench/family_B2/manifest.csv (20 rows), results/family_B2_counts.csv (100 rows, 5 pipelines, all ok), bench/family_B2/*.qasm and *_target.npy.

| Claim | Recomputed | Verdict |
|---|---|---|
| mean T-count written, n = 2, eps 1e-3 = 638.4 | 638.4 (5 instances; manifest t_count and counts t_count_written identical) | CONFIRMED |
| n = 3, eps 1e-3 = 2571.6 | 2571.6 | CONFIRMED |
| ZX reduction 1.3 to 3.1 % | Means of (t_written - t_after_zx)/t_written per (n, eps) group for P1 and P2 (pyzx full_reduce): 2.29, 2.19, 1.27, 3.14 %, i.e. range 1.27 to 3.14 %. Per-circuit range for P1/P2: 0.85 to 4.36 %. P3 (tket ZXGraphlike) group means: 0.74 to 1.90 %. | CONFIRMED as group means for P1/P2; the sentence does not say it is a mean over groups, and the per-circuit range is 0.85 to 4.36 % |
| all blocks Matsumoto-Amano, below bound | manifest: all_blocks_matsumoto_amano True on 20/20, below_bound True on 20/20, bound == n_rz_synthesised * eps on 20/20 | CONFIRMED (from manifest flags; MA property not independently re-derived) |

Operator-norm distance, QASM unitary vs stored target, global phase aligned by the phase of tr(T^dag U):

| file | n_gates (file / manifest) | my distance (qiskit little-endian) | manifest operator_norm_error | bound n_rz * eps |
|---|---|---|---|---|
| haar_n2_eps1e-03_s3 | 1673 / 1673 | 1.839370e-03 | 1.839370e-03 | 0.02 |
| haar_n3_eps1e-05_s2 | 10940 / 10940 | 6.907696e-05 | 6.907696e-05 | 0.0008 |

Verdict: CONFIRMED (agree to all printed digits; both below the bound). [F] The *_target.npy files are in Qiskit little-endian qubit order: pytket's `get_unitary` (ILO-BE) gives distance 1.9 without bit reversal and the same 1.84e-3 / 6.91e-5 after bit reversal. Any consumer using pytket on these targets must reverse the bit order.

## Claim 6. Single-qubit SK word compiles to 2 native gates

Reproduced: qiskit `SolovayKitaev(recursion_degree=3, basic_approximations=generate_basic_approximations(["s","sdg","t","tdg","z","h"], depth=10))` on rx(2.3) gives an 834-gate word (h 388, t 193, tdg 192, s 31, sdg 30), SK error 3.64e-3 in operator norm. pytket `AutoRebase({Rz, PhasedX, ZZPhase, ZZMax, Measure, Reset})` + `SquashRzPhasedX` + `RemoveRedundancies` gives exactly 2 gates: `PhasedX(0.73224, 0.00304914) q[0]; Rz(3.99447) q[0];`, unitary equal to the SK word (3.64e-3 from rx(2.3), unchanged). With qiskit's default basic approximations the word has 791 gates and also compiles to 2 gates.

Verdict: CONFIRMED (2 gates). [F] The status doc's "1064-gate" word length is not reproduced (834 or 791 here); the length depends on the basic-approximation depth, which the status doc does not state. UNVERIFIABLE for the 1064 figure.

## Claim 7. Barrier counterexample T T

Source file: barrier/certificate.py (`channel_accumulate`, `pair_constant`, `bloch`, `certificate`). Word convention per the module docstring: list order = matrix product order; for T T the order is immaterial.

Module output:
- lde(T-hat) = 1, lde(S-hat) = 0, lde(channel of T T) = 0. CONFIRMED.
- Step records from `channel_accumulate([("t",(0,)),("t",(0,))], n=1)`: step 0 `lde_before 0, criterion_fired False, lde_after 1, collapsed False`; step 1 `lde_before 1, criterion_fired True, lde_after 0, collapsed True`. The pair-constancy criterion fires at the second step. CONFIRMED.
- `certificate(...)`: t_count 2, floor 0, collapse_sizes [2], criterion_violations [], refinement_violations 1, lde_bloch 0, linkage_t_min 0, sound True. So the "criterion <=> collapse" half holds and the "lde = m" refinement fails (drop of 2, not 1), consistent with the status doc's statement that only the refinement is false.
- barrier/test_certificate.py run directly: 69/69 checks passed in 43.8 s.

Hand check [F]: the Bloch matrix of T is the rotation by pi/4 about z,
T-hat = [[1/sqrt2, -1/sqrt2, 0], [1/sqrt2, 1/sqrt2, 0], [0, 0, 1]] = (P + Q sqrt2)/sqrt2^1 with
P = [[1, -1, 0], [1, 1, 0], [0, 0, 0]], Q = [[0, 0, 0], [0, 0, 0], [0, 0, 1]] (the entry 1 = sqrt2/sqrt2 sits in Q). The module returns exactly these P, Q, e = 1.
P mod 2 = [[1, 1, 0], [1, 1, 0], [0, 0, 0]]: in every row the X and Y entries are equal (1, 1), (1, 1), (0, 0), so P is pair-constant on {X, Y}. P is not 0 mod 2, so lde(T-hat) = 1.
Product: (P + Q sqrt2)^2 = P^2 + 2 Q^2 + sqrt2 (PQ + QP) with P^2 = [[0, -2, 0], [2, 0, 0], [0, 0, 0]], 2 Q^2 = diag(0, 0, 2), PQ + QP = 0. So T-hat T-hat = [[0, -2, 0], [2, 0, 0], [0, 0, 2]]/sqrt2^2; the numerator is 0 mod 2 twice over, reducing to [[0, -1, 0], [1, 0, 0], [0, 0, 1]]/sqrt2^0 = S-hat, lde 0. The criterion fires (P pair-constant) and lde drops from 1 to 0, so "lde(V R_S) = m" (which would give 1) is false; "lde <= m" holds.

Verdict: CONFIRMED.

## Summary

- CONFIRMED: claims 1, 2, 3, 5 (numbers), 6 (2 gates), 7.
- MISMATCH: claim 4, "P2 fewer ZZ than P0 on 13 of 14 completed circuits". Recomputed 12 of 14 (two ties). All other B1 numbers confirmed.
- UNVERIFIABLE: the "1064-gate" SK word length (claim 6, status doc); the literature T-count values are checked against memory only.
- Caveats: family A figures in the status doc include the xxz rows that are being replaced; the hwb8 long rerun has crashed (KeyError 'file'); B2 targets are little-endian.
