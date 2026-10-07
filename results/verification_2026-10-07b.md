# Independent verification, 2026-10-07 (b)

Verifier: separate agent, files only (no agent reports read). Environment: pytket 2.18.4, pyzx 0.10.7, numpy, pandas. All derived numbers below were recomputed with code from the raw files named in each entry.

## Part 1. run_bench_B.py fix

`[F]` Cause of the crash in `results/family_B1_hwb8_long_run.log` (old): `--files hwb8` was matched exactly against manifest entries of the form `hwb8.qasm`, so the subset was empty, zero jobs ran, and `pd.DataFrame([])` had no `file` column for the merge at line 201. The log contained no job lines before the traceback, confirming zero jobs.

`[F]` Fix in `pipelines/run_bench_B.py` (only file modified besides this one): `--files` now accepts names with or without `.qasm` and warns on names absent from the manifest; an empty selection or an empty result set exits with a clear message instead of a KeyError; the `pipeline` Categorical is restricted to the pipelines actually run so a `--pipelines` subset cannot index a missing pivot column in the summary.

`[F]` Smoke run: `--manifest bench/family_B1/manifest.csv --files tof_3 --pipelines P2 --prefix smoke --workers 1` completed, status ok, n_2q = 14, t_count_zx = 15, summary written. `results/compiled/P2/tof_3.qasm` was byte-identical before and after (md5 b71315e31457e9e25f60894e895385aa). The smoke CSVs were removed.

`[F]` hwb8 rerun started at 21:37 with nohup: `--files hwb8 --pipelines P1,P2 --prefix family_B1_hwb8_long --timeout 5400 --workers 2`, log `results/family_B1_hwb8_long_run.log`, parent PID 404, two worker processes running. Not waited for; outcome not verified here.

## Part 2. Claims

### Claim 1. Family A generator and files

Files: `bench/family_A/*.qasm` (180 circuits plus `_meas` copies), `bench/family_A/manifest.csv`, `bench/family_A/xxz_n4_r1_uniform_s1.npy`, `bench/gen_trotter.py`, `bench/sv.py`.

- `[F]` All 60 xxz `.qasm` files begin, after the 3 header lines, with `x q[i];` for exactly the odd i < n, and contain no other `x` gate. Recomputed: 60/60. CONFIRMED.
- `[F]` None of the 120 tfim/ladder `.qasm` files (nor their `_meas` copies) contains an `x` gate. CONFIRMED.
- `[F]` manifest.csv (180 rows): initial_state = neel on every xxz row and zero on every tfim/ladder row, no other value. CONFIRMED.
- `[F]` `xxz_n4_r1_uniform_s1.qasm` body (53 lines) equals, line for line, a hand-written Trotter step in the documented order: Neel prep, bonds (0,1), (2,3), (1,2) (even bonds then odd), per bond XX, YY, ZZ with rz(0.2), rz(0.2), rz(0.1) for Jx = Jy = 1, Jz = 0.5, dt = 0.1, with the YY conjugation rx(pi/2)/rx(-pi/2). It also equals the output of `state_prep_gates + trotter_circuit(terms(...))` called directly. CONFIRMED.
- `[F]` `xxz_n4_r1_uniform_s1.npy`: support (p > 1e-12) = 6, states {0011, 0101, 0110, 1001, 1010, 1100}; p[5] = p(0101) = 0.886204 with q[0] as MSB (p(1010) = 0.001496, so the bit order is distinguishable). Independent recomputation with dense `scipy.linalg.expm` of the three bond terms applied to |0101> agrees to 7.8e-16. CONFIRMED.

### Claim 2. results/family_A_counts.csv

Files: `results/family_A_counts.csv`, `bench/family_A/manifest.csv`.

- `[F]` 1260 rows, status ok on 1260. CONFIRMED.
- `[F]` xxz mean n_2q by n = 4, 6, 8, 10, 12: P0 = 21, 35, 49, 63, 77; P2 = 22.3333, 40, 57, 73, 89. CONFIRMED.
- `[F]` P0 n_2q = n_cx/2 (manifest n_cx) on 180/180. CONFIRMED.
- `[F]` No pipeline has n_2q < P0 on any circuit (0 of 180 for each of P0ref, P0L1, P1, P2, P3, P4; min n_2q - P0 over circuits: P2 0, P0ref/P0L1/P1 3, P3/P4 5). CONFIRMED.

### Claim 3. Proxy CSVs and fits

Files: `results/family_A_proxy_h22e.csv`, `results/family_B1_proxy_h22e.csv`.

- `[F]` Family A: 540 rows, pipelines P0ref/P0/P1/P2/P3, n in {4, 6, 8}, 36 circuits per (n, pipeline). Mean F_H at n = 8: P0ref 0.97037, P0 0.98259, P1 0.95036, P2 0.98074, P3 0.95135. CONFIRMED.
- `[F]` P0 > P0ref on 108/108. CONFIRMED.
- `[F]` P2 > P0 on 43/108 (P2 < P0 on 65, ties 0). CONFIRMED.
- `[F]` Fit -ln F_H = a n_2q on all 540 rows, OLS **without intercept**: a = 5.1393e-4 +/- 1.28e-5 (standard error from residual variance with n - 1 degrees of freedom), residual sd 1.82e-2, R^2 = 0.6121 when computed as 1 - SS_res/SS_tot about the mean (the uncentred R^2 is 0.7497). This reproduces the claim. With intercept: a = 5.24e-4 +/- 1.8e-5, b = -9.1e-4 +/- 1.1e-3, which does not. CONFIRMED (no-intercept OLS, centred R^2).
- `[F]` Family B1: 35 rows, 7 circuits x 5 pipelines. No-intercept OLS: a = 1.1801e-3 +/- 2.33e-5, centred R^2 = 0.9675 (uncentred 0.9869). With intercept a = 1.150e-3 +/- 3.6e-5. CONFIRMED (no-intercept OLS, centred R^2).
- `[F]` B1 P2 > P0 on 7/7. CONFIRMED.
- `[O]` Reporting a centred R^2 for a no-intercept fit is a convention choice; it should be stated wherever the 0.968 is quoted.

### Claim 4. Proxy rerun

Files: `noise/run_proxy.py` (`one_run` with noise = h22e, which builds `NoiseModel` from `h2_params.H2_2E_EMULATOR`: p1 7.3e-5, p2 1.29e-3, p_meas_0 9e-4, p_meas_1 1.8e-3, p_init 4e-5, p_idle 0), `noise/dm_sim.py`, `results/compiled/<pipeline>/<file>`, references `bench/family_A/*.npy` (A) or noise-free P0ref (B1).

| circuit | pipeline | F_H rerun | F_H CSV | diff |
|---|---|---|---|---|
| xxz_n8_r2_uniform_s1 | P2 | 0.951992032 | 0.951992032 | 1.1e-16 |
| ladder_n6_r1_disorder_s2 | P0 | 0.998570602 | 0.998570602 | 0 |
| tfim_n8_r4_disorder_s3 | P1 | 0.950066844 | 0.950066844 | 0 |
| hwb6 (B1) | P2 | 0.896167643 | 0.896167643 | 0 |

`[F]` TVD and n_2q also agree (TVD diff <= 1.4e-16). Four circuits checked, all within 1e-6. CONFIRMED.

### Claim 5. results/certificates.csv

Files: `results/certificates.csv`, `barrier/certificate.py`, `bench/family_B2/*.qasm`, `bench/family_B1/tof_3.qasm`, `results/family_B2_counts.csv`.

- `[F]` 24 rows; lde_floor <= t_zx_P1 and <= t_zx_P2 on 24/24 (t_zx_P1 = t_zx_P2 on every row). CONFIRMED.
- `[F]` B2 mean of 100 x lde_floor / t_zx_P2 per (n, eps), 5 circuits each: (2, 1e-3) 99.839, (2, 1e-5) 99.786, (3, 1e-3) 99.566, (3, 1e-5) 99.760. Claimed 99.84, 99.79, 99.57, 99.76. CONFIRMED (rounding). The CSV column `floor_over_t_zx_P2` equals the recomputed ratio on all rows.
- `[F]` Minimum over the 20 B2 instances: 99.279 % (haar_n3_eps1e-03_s5, 2478/2496). Claimed 99.28. CONFIRMED.
- `[F]` Direct recomputation with `certificate_from_qasm(path, compute_unitary=False)`:
  - `haar_n2_eps1e-05_s4.qasm`: t_count 1052, floor 1030, collapse_count 11, max_removable_fraction 0.0209125. CSV: 1052, 1030, 11, 0.0209125. CONFIRMED.
  - `tof_3.qasm`: t_count 21, floor 4, collapse_count 13, max_removable_fraction 0.809524. CSV: 21, 4, 13, 0.809524. CONFIRMED.
- `[F]` certificates.csv t_zx_P2 equals `t_count_after_zx` of the P2 row in `results/family_B2_counts.csv` on all 20 B2 rows; for tof_3 it equals the P2 t_count_zx (15) from the smoke run. CONFIRMED.

### Claim 6. report/report_v1.md tables and B1 statement

Files: `report/report_v1.md`, `results/family_A_counts.csv`, `results/family_B1_counts.csv`, `results/family_B2_counts.csv`.

Spot-checked cells (recomputed value, report value):

| table | cell | recomputed | report |
|---|---|---|---|
| A1 | n = 8, P1 | 107.6 | 107.6 |
| A1 | n = 12, P4 | 262.6 | 262.6 |
| A1 | n = 10, P2 | 41.7 | 41.7 |
| A1 | n = 6, ZZ terms | 21.0 | 21.0 |
| B1 | hwb6, ZZ P3 | 189 | 189 |
| B1 | vbe_adder_3, ZZ P2 / P2 vs P0 % | 41 / 26.8 | 41 / 26.8 |
| B1 | grover_5, ZZ P1 / T after ZX | 256 / 166 | 256 / 166 |
| B1 | hwb8, ZZ P0 / ZZ P4 / T after ZX (P4) | 5912 / 8461 / 3517 | 5912 / 8461 / 3517 |
| B2 | (3, 1e-3) mean T written / T after ZX P2 / T red. % P3 | 2571.6 / 2490.8 / 1.9 | 2571.6 / 2490.8 / 1.9 |
| B2 | (2, 1e-5) T after ZX P3 / HQC P0 / max target dev. | 1037.6 / 16.6 / 3.2e-10 | 1037.6 / 16.6 / 3.2e-10 |

`[F]` All 10 spot-checked cells match. CONFIRMED.

`[F]` B1 statement (section 3.2, "On the 14 circuits where P2 completed..."): from `results/family_B1_counts.csv`, P2 completed on 14 of 15 (hwb8 timeout); P2 < P0 on 12, = P0 on 2 (qft_4, gf2_pow_4_mult), > P0 on 0; mean reduction 7.01 %; vbe_adder_3 56 to 41 = 26.8 %; P1 > P0 on 13 of 14 completed, < P0 on vbe_adder_3 only; P3 > P0 on 14 of 15, < P0 on mod5_4 only. Every number in the sentence is reproduced. CONFIRMED.

`[F]` Section 2.4 "103 of 105 rows pass ... two are the hwb8 timeouts under P1 and P2": CSV has 103 ok, 2 timeout (hwb8 P1, P2). CONFIRMED.

`[O]` Not among the claims, but noted for the report owner: Table A4 and its caption still carry the data-sheet "typical" proxy from `results/family_A_proxy.csv` (its n = 8 means 0.9567/0.9757/0.9238/0.9728/0.9185 match that file), not the H2-2E values in `results/family_A_proxy_h22e.csv` that claim 3 refers to. The caption says this is pending replacement. Section 5 says the hwb8 rerun used 900 s; the run started today uses 5400 s.

## Summary

| claim | verdict |
|---|---|
| 1 Family A files, manifest, ideal distribution | CONFIRMED |
| 2 family_A_counts.csv | CONFIRMED |
| 3 proxy CSVs, fits (no-intercept OLS, centred R^2), win counts | CONFIRMED |
| 4 proxy rerun, 4 circuits | CONFIRMED |
| 5 certificates.csv, direct recomputation | CONFIRMED |
| 6 report tables (10 cells) and B1 "12 of 14" statement | CONFIRMED |

No MISMATCH and no UNVERIFIABLE entries. The hwb8 rerun result is not covered (still running at the time of writing).
