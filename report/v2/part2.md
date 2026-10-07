## 3. Results

### 3.1 Family A, Trotter spin chains

`[F]` Table A1. Mean ZZPhase count by n and pipeline, 36 circuits per n. "ZZ terms" is n_cx / 2 of the circuit as written, the number of two-body Pauli exponentials in the Trotter formula.

<!-- TABLE:A1_zz_by_n -->
| n | circuits | ZZ terms | P0ref | P0 | P0L1 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 36 | 12.4 | 24.9 | 12.4 | 24.9 | 25.9 | 12.9 | 26.1 | 31.4 |
| 6 | 36 | 21.0 | 42.0 | 21.0 | 42.0 | 62.0 | 22.7 | 58.9 | 71.0 |
| 8 | 36 | 29.6 | 59.1 | 29.6 | 59.1 | 107.6 | 32.2 | 108.2 | 119.9 |
| 10 | 36 | 38.1 | 76.2 | 38.1 | 76.2 | 173.7 | 41.7 | 157.2 | 189.8 |
| 12 | 36 | 46.7 | 93.3 | 46.7 | 93.3 | 246.1 | 50.7 | 233.4 | 262.6 |
<!-- /TABLE:A1_zz_by_n -->

`[F]` Table A2. Each pipeline against P0 on the same circuit, 180 circuits. Ratios are averaged over circuits.

<!-- TABLE:A2_vs_P0 -->
| pipeline | better than P0 | equal to P0 | worse than P0 | mean ZZ ratio | min ZZ ratio | max ZZ ratio | mean 2q-depth ratio | mean HQC ratio |
|---|---|---|---|---|---|---|---|---|
| P0ref | 0 | 0 | 180 | 2.00 | 2.00 | 2.00 | 2.00 | 1.63 |
| P0L1 | 0 | 0 | 180 | 2.00 | 2.00 | 2.00 | 2.00 | 1.63 |
| P1 | 0 | 0 | 180 | 4.43 | 1.28 | 10.32 | 10.92 | 3.03 |
| P2 | 0 | 120 | 60 | 1.04 | 1.00 | 1.19 | 1.25 | 1.03 |
| P3 | 0 | 0 | 180 | 3.79 | 1.31 | 7.91 | 10.29 | 2.76 |
| P4 | 0 | 0 | 180 | 4.90 | 1.44 | 10.36 | 11.88 | 3.33 |
<!-- /TABLE:A2_vs_P0 -->

`[F]` Table A3. P0 against the ZZ term count, by model and Trotter steps.

<!-- TABLE:A3_floor -->
| model | r | circuits | mean ZZ terms | mean n_2q P0 | circuits with n_2q = ZZ terms |
|---|---|---|---|---|---|
| ladder | 1 | 20 | 10.0 | 10.0 | 20 |
| ladder | 2 | 20 | 20.0 | 20.0 | 20 |
| ladder | 4 | 20 | 40.0 | 40.0 | 20 |
| tfim | 1 | 20 | 7.0 | 7.0 | 20 |
| tfim | 2 | 20 | 14.0 | 14.0 | 20 |
| tfim | 4 | 20 | 28.0 | 28.0 | 20 |
| xxz | 1 | 20 | 21.0 | 21.0 | 20 |
| xxz | 2 | 20 | 42.0 | 42.0 | 20 |
| xxz | 4 | 20 | 84.0 | 84.0 | 20 |
<!-- /TABLE:A3_floor -->

![Family A ZZPhase ratio](figures/fig_A_zz_ratio.png)

Figure 1. Family A. ZZPhase count of each pipeline divided by the P0 count on the same circuit, mean over the 36 circuits at each n with the min-max band shaded. The dashed line is P0 itself. Data: Table A2 and `results/family_A_counts.csv`.

`[F]` P0 compiles every one of the 180 circuits to exactly one ZZPhase per two-body term. No pipeline goes below that count on any circuit. P2 equals P0 on 120 circuits and is worse on 60, by at most a factor 1.19. P1, P3 and P4 are worse than P0 on all 180 circuits. The ratio to P0 runs from 1.28 to 10.32 for P1, from 1.31 to 7.91 for P3 and from 1.44 to 10.36 for P4. The mean ratio grows with n for each of the three, from 2.39 at n = 4 to 6.53 at n = 12 for P1, from 2.49 to 5.18 for P3 and from 2.92 to 6.92 for P4.

`[O]` One ZZPhase per two-body exponential is the natural count for this family and P0 reaches it. A rewrite that preserves the unitary has no room to remove entangling gates here. The ZX extraction pipelines add them because `extract_circuit` resynthesises the graph with CNOTs that no longer follow the Trotter term structure.

### 3.2 Family B1, Clifford+T benchmarks

`[F]` Table B1. ZZPhase count per circuit and pipeline. "T after ZX" is the T-count of the PyZX circuit after the ZX stage of P1 and P2, which agree on every circuit. For hwb8 it is the P4 value.

<!-- TABLE:B1_per_circuit -->
| circuit | n | T written | ZZ P0ref | ZZ P0 | ZZ P0L1 | ZZ P1 | ZZ P2 | ZZ P3 | ZZ P4 | P2 vs P0 % | T after ZX | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tof_3 | 5 | 21 | 18 | 15 | 18 | 22 | 14 | 25 | 25 | 6.7 | 15 |  |
| barenco_tof_3 | 5 | 28 | 24 | 20 | 24 | 23 | 19 | 27 | 27 | 5.0 | 16 |  |
| mod5_4 | 5 | 28 | 28 | 24 | 28 | 25 | 22 | 20 | 29 | 8.3 | 8 |  |
| qft_4 | 5 | 69 | 46 | 36 | 46 | 43 | 36 | 64 | 57 | 0.0 | 67 |  |
| tof_4 | 7 | 35 | 30 | 25 | 30 | 31 | 23 | 40 | 38 | 8.0 | 23 |  |
| barenco_tof_4 | 7 | 56 | 48 | 40 | 48 | 41 | 38 | 54 | 54 | 5.0 | 28 |  |
| hwb6 | 7 | 105 | 116 | 99 | 116 | 130 | 94 | 189 | 144 | 5.1 | 75 |  |
| mod_mult_55 | 9 | 49 | 48 | 41 | 48 | 71 | 39 | 85 | 90 | 4.9 | 35 |  |
| tof_5 | 9 | 49 | 42 | 35 | 42 | 48 | 32 | 56 | 66 | 8.6 | 31 |  |
| barenco_tof_5 | 9 | 84 | 72 | 60 | 72 | 70 | 57 | 90 | 87 | 5.0 | 40 |  |
| grover_5 | 9 | 336 | 288 | 240 | 288 | 256 | 218 | 322 | 278 | 9.2 | 166 |  |
| vbe_adder_3 | 10 | 70 | 66 | 56 | 66 | 55 | 41 | 61 | 67 | 26.8 | 24 |  |
| mod_red_21 | 11 | 119 | 105 | 88 | 105 | 107 | 83 | 140 | 132 | 5.7 | 73 |  |
| gf2_pow_4_mult | 12 | 112 | 99 | 83 | 99 | 260 | 83 | 277 | 290 | 0.0 | 68 |  |
| hwb8 | 12 | 5887 | 7118 | 5912 | 7118 | 8305 | 5587 | 11537 | 8461 | 5.5 | 3517 |  |
<!-- /TABLE:B1_per_circuit -->

![Family B1 ZZPhase count](figures/fig_B1_zz.png)

Figure 2. Family B1. ZZPhase count per circuit for P0ref, P0 and P2, log scale, circuits ordered by qubit number then T-count. hwb8 (5912 under P0) is omitted. Data: Table B1.

`[F]` On the 14 circuits where P2 completed, P2 is below P0 on 12, equal on 2 (qft_4 and gf2_pow_4_mult) and above on none. The mean reduction against P0 is 7.0 %. The largest is vbe_adder_3, 56 to 41 ZZPhase gates, 26.8 %. P1 is above P0 on 13 of the 14 circuits it completed and below on one (vbe_adder_3). P3 is above P0 on 14 of 15 and below on one (mod5_4). P4 is above P0 on 15 of 15.

`[F]` The hwb8 rerun with a 5400 s timeout (`results/family_B1_hwb8_long_counts.csv`, run log `results/family_B1_hwb8_long_run.log`) completed P1 in 886 s and P2 in 844 s of wall time. P1 gives 8305 ZZPhase gates against 5912 under P0 and P2 gives 5587, a reduction of 5.5 %. Both leave the T-count at 3517, the P4 value in Table B1. The two rows are not yet merged into `results/family_B1_counts.csv`, so Table B1 and the counts in the previous paragraph still carry the timeout. With the two rows merged, P2 is below P0 on 13 of 15 and P1 above P0 on 14 of 15.

`[F]` The T-counts after the ZX stage equal the PyZX benchmark values of Kissinger and van de Wetering for the circuits listed there `[O: to be checked against the paper's table before submission]`. The source is Kissinger and van de Wetering, "Reducing the number of non-Clifford gates in quantum circuits", Phys. Rev. A 102, 022406 (2020), arXiv:1903.10477. The paper is not in the repository. A fetched copy of arXiv:1903.10477v3 lists tof_3 15, mod5_4 8 and vbe_adder_3 24 in its PyZX column and has no grover_5 row, so the grover_5 value 166 is Unverifiable against that paper.

- tof_3: 21 to 15
- mod5_4: 28 to 8
- vbe_adder_3: 70 to 24
- grover_5: 336 to 166

`[O]` Teleport reduction keeps the circuit skeleton and only moves phases, so the pytket pass that follows sees a circuit of the same shape with fewer non-Clifford phases and can merge more. Full reduction with extraction replaces the skeleton, and the extracted CNOT structure costs more two-qubit gates on H2 than the original.

`[F]` The certified T-count floors for the four n = 5 circuits are in Table C1 of Section 3.4. The floor is at or below the T-count after the ZX stage on all four, and the ratio floor / T after ZX is 25.00 % for barenco_tof_3 and mod5_4, 26.67 % for tof_3 and 55.22 % for qft_4.

`[PENDING: emulator]` Emulated fidelity of P0 against P2 on H2-2E.

### 3.3 Family B2, synthesised Haar unitaries

`[F]` Table B2. Means over 5 circuits per row. "T red. %" is the T-count reduction by the ZX stage against the circuit as written. "max target dev." is the largest 1 - |tr(U_target^dagger U_compiled)| / 2^n in the row.

<!-- TABLE:B2_summary -->
| n | eps | circuits | mean T written | T after ZX P1 | T red. % P1 | T after ZX P2 | T red. % P2 | T after ZX P3 | T red. % P3 | ZZ P0 | ZZ P2 | HQC P0 | max target dev. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 1e-05 | 5 | 1048.4 | 1024.4 | 2.3 | 1024.4 | 2.3 | 1037.6 | 1.0 | 3 | 3 | 16.6 | 3.2e-10 |
| 2 | 0.001 | 5 | 638.4 | 624.4 | 2.2 | 624.4 | 2.2 | 628.4 | 1.6 | 3 | 3 | 16.6 | 1.9e-06 |
| 3 | 1e-05 | 5 | 4220.8 | 4167.2 | 1.3 | 4167.2 | 1.3 | 4189.6 | 0.7 | 19 | 19 | 56.4 | 9.4e-10 |
| 3 | 0.001 | 5 | 2571.6 | 2490.8 | 3.1 | 2490.8 | 3.1 | 2522.8 | 1.9 | 19 | 19 | 56.4 | 7.1e-06 |
<!-- /TABLE:B2_summary -->

![Family B2 T-count reduction](figures/fig_B2_t.png)

Figure 3. Family B2. Percentage of the written T-count removed by the ZX stage of P1, P2 and P3, mean over the 5 circuits in each (n, eps) group. P1 and P2 give the same T-count on every circuit. Data: Table B2.

`[F]` The mean raw T-counts match the barrier manuscript's Table E6 for the two rows it reports: n = 2 at eps = 1e-3 gives 638.4 here against 644 there, and n = 3 at eps = 1e-3 gives 2571.6 against 2570. The manuscript rows are means over 50 and 8 instances, this table over 5.

`[F]` The ZX stage removes between 1.3 % and 3.1 % of the T-count under P1 and P2, and between 0.7 % and 1.9 % under P3. The ZZPhase count after P0 is 3 at n = 2 and 19 at n = 3 for every circuit, and P2 leaves it unchanged.

`[O]` Synthesised circuits are the case where the fault-tolerant layer matters and the NISQ layer does not. The two-qubit count is fixed by the KAK or QSD skeleton. The whole cost is in the gridsynth words, which are near their floors by construction, and the certificate measures how near.

`[F]` The certified floor of every one of the 20 circuits is in Table C1 of Section 3.4. The floor divided by the T-count after the ZX stage averages 99.84, 99.79, 99.57 and 99.76 % over the four (n, eps) configurations in the row order of Table C1. The minimum over the 20 circuits is 99.28 %.

### 3.4 Certificates

`[F]` Table C1. The exactness-barrier certificate (`barrier/certificate.py`, Section 2.5) on the 20 family B2 circuits and the four family B1 circuits with n = 5, from `results/certificates.csv`. The 4^n x 4^n channel is small at these sizes. The floor is the least denominator exponent of the exact Pauli channel of the circuit as written. "T after ZX" is the T-count after PyZX teleport_reduce, which equals the full_reduce value on every row.

<!-- TABLE:C1_certificates -->
Per circuit. floor = lde of the exact Pauli channel (Corollary cert, Theorem C(c)), T after ZX = T-count after PyZX teleport_reduce (P2, equal to the full_reduce value on every row), achieved % = 100 (1 - T after ZX / T written).

| family | file | n | T written | floor | T after ZX | floor / T after ZX % | achieved % |
|---|---|---|---|---|---|---|---|
| B2 | haar_n2_eps1e-03_s1 | 2 | 662 | 651 | 652 | 99.85 | 1.51 |
| B2 | haar_n2_eps1e-03_s2 | 2 | 628 | 611 | 612 | 99.84 | 2.55 |
| B2 | haar_n2_eps1e-03_s3 | 2 | 638 | 630 | 630 | 100.00 | 1.25 |
| B2 | haar_n2_eps1e-03_s4 | 2 | 622 | 613 | 614 | 99.84 | 1.29 |
| B2 | haar_n2_eps1e-03_s5 | 2 | 642 | 612 | 614 | 99.67 | 4.36 |
| B2 | haar_n2_eps1e-05_s1 | 2 | 1046 | 1021 | 1022 | 99.90 | 2.29 |
| B2 | haar_n2_eps1e-05_s2 | 2 | 1046 | 1025 | 1026 | 99.90 | 1.91 |
| B2 | haar_n2_eps1e-05_s3 | 2 | 1038 | 1002 | 1004 | 99.80 | 3.28 |
| B2 | haar_n2_eps1e-05_s4 | 2 | 1052 | 1030 | 1036 | 99.42 | 1.52 |
| B2 | haar_n2_eps1e-05_s5 | 2 | 1060 | 1033 | 1034 | 99.90 | 2.45 |
| B2 | haar_n3_eps1e-03_s1 | 3 | 2566 | 2483 | 2496 | 99.48 | 2.73 |
| B2 | haar_n3_eps1e-03_s2 | 3 | 2544 | 2442 | 2452 | 99.59 | 3.62 |
| B2 | haar_n3_eps1e-03_s3 | 3 | 2570 | 2486 | 2490 | 99.84 | 3.11 |
| B2 | haar_n3_eps1e-03_s4 | 3 | 2588 | 2511 | 2520 | 99.64 | 2.63 |
| B2 | haar_n3_eps1e-03_s5 | 3 | 2590 | 2478 | 2496 | 99.28 | 3.63 |
| B2 | haar_n3_eps1e-05_s1 | 3 | 4208 | 4132 | 4144 | 99.71 | 1.52 |
| B2 | haar_n3_eps1e-05_s2 | 3 | 4218 | 4158 | 4162 | 99.90 | 1.33 |
| B2 | haar_n3_eps1e-05_s3 | 3 | 4224 | 4179 | 4188 | 99.79 | 0.85 |
| B2 | haar_n3_eps1e-05_s4 | 3 | 4248 | 4184 | 4192 | 99.81 | 1.32 |
| B2 | haar_n3_eps1e-05_s5 | 3 | 4206 | 4133 | 4150 | 99.59 | 1.33 |
| B1 | barenco_tof_3 | 5 | 28 | 4 | 16 | 25.00 | 42.86 |
| B1 | mod5_4 | 5 | 28 | 2 | 8 | 25.00 | 71.43 |
| B1 | qft_4 | 5 | 69 | 37 | 67 | 55.22 | 2.90 |
| B1 | tof_3 | 5 | 21 | 4 | 15 | 26.67 | 28.57 |

Family B2 by configuration, 5 circuits each.

| n | eps | circuits | mean T written | mean floor / T after ZX % | min floor / T after ZX % | mean achieved % | mean collapse rate % |
|---|---|---|---|---|---|---|---|
| 2 | 1e-03 | 5 | 638.4 | 99.84 | 99.67 | 2.19 | 1.25 |
| 2 | 1e-05 | 5 | 1048.4 | 99.79 | 99.42 | 2.29 | 1.34 |
| 3 | 1e-03 | 5 | 2571.6 | 99.57 | 99.28 | 3.14 | 1.86 |
| 3 | 1e-05 | 5 | 4220.8 | 99.76 | 99.59 | 1.27 | 0.80 |
<!-- /TABLE:C1_certificates -->

`[F]` The invariant floor <= T after ZX holds on 24 of 24 rows, for the full_reduce and the teleport_reduce T-counts alike, and the two T-counts are equal on 24 of 24 rows. The certificate ran in at most 0.4 s per circuit at n = 2, at most 36.4 s at n = 3 and at most 38.5 s on the n = 5 family B1 circuits (`wall_s` in the CSV).

`[F]` On family B2 the configuration means of the floor divided by the T-count after the ZX stage are 99.84, 99.79, 99.57 and 99.76 % in the row order of Table C1. The minimum over the 20 circuits is 99.28 % (haar_n3_eps1e-03_s5, floor 2478 against 2496 after ZX) and the maximum is 100.00 % (haar_n2_eps1e-03_s3). The barrier manuscript calls this quantity lde / T_tel (caption of Table tab:e6, `papers/barrier/main.tex` line 3066). Its Table tab:e6 (lines 3076 and 3079) reports 99.79 +/- 0.30 with minimum 98.6 at (2, 1e-3) over 50 instances and 99.55 +/- 0.20 with minimum 99.3 at (3, 1e-3) over 8 instances. Line 3108 states that the quantity averages 99.4 to 99.9 % and never falls below 96.9 % on any instance. All four configuration means here lie inside 99.4 to 99.9 % and every instance is above 96.9 %. The (n, eps) = (2, 1e-5) and (3, 1e-5) configurations have no counterpart in that table. The manuscript's line 3118 gives the collapse rate as 1.0 to 2.3 %. The collapse rate here is 1.25, 1.34, 1.86 and 0.80 % in the same row order. The last configuration sits below that range.

`[O]` The number a user reads from Table C1 is the gap between the two percentages. On family B2 the ZX stage removes 1.3 to 3.1 % of the written T-count. The certificate shows that at most 0.16 to 0.43 % of the remaining count is removable by any semantics-exact rewrite on the configuration means and at most 0.72 % on any single instance. The gridsynth words are within a fraction of a percent of their floor and no further optimiser effort on them is worth paying for.

`[F]` On the four family B1 circuits the floor is loose. For mod5_4 the floor is 2 while the ZX stage leaves 8 T gates, so the floor is 25.00 % of the achieved count, and the denominator exponent collapses at 19 of the 28 T gates in the certificate's step record (`collapse_count` in the CSV). The ratios on barenco_tof_3 and tof_3 are 25.00 % and 26.67 % and on qft_4 it is 55.22 %.

`[O]` The B1 floors are loose because these circuits are hand-written Toffoli networks, not synthesised ring elements. The theorem bounds the T-count of every exact rewrite from below by the denominator exponent of the channel, and on a gridsynth word the exponent grows by one at all but 0.5 to 2.5 % of the T gates (the per-instance `collapse_rate` in the CSV), so the bound is tight there. In a Toffoli network most T gates cancel in the channel and the exponent stays small, so the bound stays well below what any known rewrite reaches. The gap between 2 and 8 on mod5_4 is either headroom for a better rewrite or slack in the bound, and the certificate does not say which. The manuscript's percentages are stated for synthesised circuits only and the B1 rows are not covered by them.

### 3.5 Noise proxy with H2-2E parameters

`[F]` Table A4. Local density-matrix proxy on family A at n <= 8 with 36 circuits per (n, pipeline) cell and 540 rows in `results/family_A_proxy_h22e.csv`. The simulator is `noise/dm_sim.py` with the published H2-2E emulator parameters from `noise/h2_params.py` (p1 = 7.3e-5, p2 = 1.29e-3, readout flips 9e-4 and 1.8e-3, p_init = 4e-5). The ideal distribution is the family reference `bench/family_A/<stem>.npy`.

<!-- TABLE:A4_proxy -->
Provisional local proxy. Density-matrix simulation with the published H2-2E emulator parameters (p1 = 7.3e-5, p2 = 1.29e-3, readout 9e-4 and 1.8e-3, p_init = 4e-5) and no leakage, crosstalk or dephasing, to be replaced by emulator runs. Mean Hellinger fidelity F_H of the noisy output distribution against the ideal one.

| n | circuits per pipeline | F_H P0ref | F_H P0 | F_H P1 | F_H P2 | F_H P3 |
|---|---|---|---|---|---|---|
| 4 | 36 | 0.9867 | 0.9922 | 0.9893 | 0.9919 | 0.9893 |
| 6 | 36 | 0.9785 | 0.9874 | 0.9735 | 0.9862 | 0.9743 |
| 8 | 36 | 0.9704 | 0.9826 | 0.9504 | 0.9807 | 0.9514 |

| pipeline | mean F_H | mean TVD | mean n_2q | mean n_1q |
|---|---|---|---|---|
| P0ref | 0.9785 | 0.0352 | 42.0 | 57.7 |
| P0 | 0.9874 | 0.0210 | 21.0 | 40.1 |
| P1 | 0.9710 | 0.0494 | 65.1 | 62.8 |
| P2 | 0.9863 | 0.0221 | 22.6 | 42.0 |
| P3 | 0.9717 | 0.0482 | 64.4 | 72.9 |
<!-- /TABLE:A4_proxy -->

`[F]` P0 and P2 have the highest fidelity in every one of the nine (model, n) cells of family A and P0 is above P0ref on 108 of 108 circuits. P0 and P2 differ by at most 0.0056 in any cell (xxz at n = 8), and per circuit P2 is above P0 on 43 and below on 65. P1 and P3 are below P0 and below P2 in every cell. The position of P0ref depends on the model. On ladder and tfim P0ref is above P1 and P3 in all six cells and on 36 of 36 circuits each. On xxz P0ref is below P1 in all three cells and below P3 at n = 4 and n = 6, because on xxz the extraction pipelines leave a ZZPhase count close to the P0ref count (30.3 against 42.0 at n = 4 under P1) while on ladder and tfim they leave 1.4 to 3.2 times the P0ref count. Over the 36 circuits at each n the ordering is P0 ~ P2 > P0ref > P1 ~ P3 at n = 6 and n = 8, and at n = 4 P1 and P3 (both 0.9893) sit above P0ref (0.9867).

`[F]` Table A5. The same proxy on the seven family B1 circuits with n <= 7, 35 rows in `results/family_B1_proxy_h22e.csv`. The ideal distribution is the noise-free output of the P0ref circuit. "support" is the number of outcomes with probability above 1e-12.

<!-- TABLE:A5_proxy_b1 -->
| circuit | n | support | F_H P0ref | F_H P0 | F_H P1 | F_H P2 | F_H P3 | ZZ P0 | ZZ P2 |
|---|---|---|---|---|---|---|---|---|---|
| barenco_tof_3 | 5 | 1 | 0.9696 | 0.9739 | 0.9692 | 0.9747 | 0.9644 | 20 | 19 |
| mod5_4 | 5 | 1 | 0.9647 | 0.9689 | 0.9661 | 0.9710 | 0.9705 | 24 | 22 |
| qft_4 | 5 | 16 | 0.9641 | 0.9704 | 0.9623 | 0.9706 | 0.9527 | 36 | 36 |
| tof_3 | 5 | 1 | 0.9759 | 0.9791 | 0.9691 | 0.9800 | 0.9655 | 15 | 14 |
| barenco_tof_4 | 7 | 1 | 0.9430 | 0.9513 | 0.9451 | 0.9528 | 0.9316 | 40 | 38 |
| hwb6 | 7 | 1 | 0.8751 | 0.8915 | 0.8521 | 0.8962 | 0.7977 | 99 | 94 |
| tof_4 | 7 | 1 | 0.9614 | 0.9667 | 0.9567 | 0.9684 | 0.9464 | 25 | 23 |
<!-- /TABLE:A5_proxy_b1 -->

`[F]` On family B1 P2 is above P0 on 7 of 7 circuits and P0 is above P0ref on 7 of 7. P1 is below P0 on 7 of 7 and P3 on 6 of 7. The exception is mod5_4, where P3 has the fewest ZZPhase gates of any pipeline (20 against 24 under P0). The largest fidelity gain of P2 over P0 is hwb6, 0.8915 to 0.8962 with 99 to 94 ZZPhase gates.

`[F]` A fit of -ln F_H = a n_2q with no intercept gives a = 1.18e-3 +/- 2.3e-5 on the 35 family B1 rows, with centred R^2 0.968, against the two-qubit error rate p2 = 1.29e-3 of the noise model. On the 540 family A rows the same fit gives a = 5.14e-4 +/- 1.3e-5 with centred R^2 0.612. Per model the slope is 2.28e-4 on ladder, 2.26e-4 on tfim and 7.58e-4 on xxz. The standard errors are from the residual variance and the R^2 is centred, 1 - SS_res / SS_tot about the mean of -ln F_H (`results/proxy_h22e_fits.log`, Section 4).

`[F]` The family B1 circuits have a single-outcome ideal distribution on 6 of 7 circuits (support 16 on qft_4), the xxz circuits have mean support 29.8 and the ladder and tfim circuits have mean support 107.8 out of 2^n. Adding a support term to the family A fit, -ln F_H = a n_2q + b n_1q + u support, gives u = -7.9e-5 per outcome and raises the centred R^2 from 0.714 to 0.784.

`[O]` The slope follows the support of the ideal distribution. A depolarising error after a two-qubit gate moves probability off the ideal outcomes, and the Hellinger fidelity pays for it in full when the ideal distribution is a single outcome and only in part when the ideal distribution already covers most strings. The B1 slope close to p2 is the first case and the ladder and tfim slopes near 0.18 p2 are the second. A cost model that predicts F_H from gate counts therefore needs the support as a feature, which is the reason it enters Section 4.

`[O]` The proxy contains no leakage, crosstalk, idle dephasing or the RZZ angle scaling of the published H2-2E model, so it ranks pipelines by their ZZPhase count under the H2-2E gate rates and does not predict the emulator's absolute fidelity. The emulator runs of Section 3.7 replace it.

### 3.6 Selene runs

`[F]` Table S1. Runs of the compiled circuits on Quantinuum's local emulator Selene (`selene-sim` 0.3.4, route in Section 2.6), from `results/selene_noiseless.csv` (468 rows) and `results/selene_depolarizing.csv` (68 rows). The noiseless runs cover the 144 family A circuits with n <= 10 and the 12 family B1 circuits with n <= 10 under P0, P1 and P2 at 2000 shots. The depolarising runs cover 10 family A and 7 family B1 circuits under P0 and P2 in two variants.

<!-- TABLE:S1_selene -->
Noiseless runs (IdealErrorModel, Quest backend). TVD is against the exact output distribution of the compiled QASM, TVD_scale = sqrt(support / (2 pi shots)).

| family | circuits | pipelines | runs | shots per run | max TVD | max TVD / TVD_scale | flagged (TVD > 4 TVD_scale) | shots outside support |
|---|---|---|---|---|---|---|---|---|
| A | 144 | P0, P1, P2 | 432 | 2000 | 0.117 | 1.111 | 0 | 0 |
| B1 | 12 | P0, P1, P2 | 36 | 2000 | 0.080 | 1.121 | 0 | 0 |

Depolarising runs (DepolarizingErrorModel, p_1q = 7.3e-5, p_2q = 1.29e-3) against the density-matrix proxy, pipelines P0 and P2. z = (F_H Selene - mean F_H of 400 2000-shot samples of the proxy distribution) / their sd. gates_meas_init adds p_meas = 1.35e-3 and p_init = 4e-5, gates_only sets both to 0.

| family | variant | runs | abs z <= 2 | mean z | sd z | max abs z | mean F_H Selene - proxy exact | mean F_H Selene - proxy sampled |
|---|---|---|---|---|---|---|---|---|
| A | gates_meas_init | 20 | 20 | -0.13 | 0.82 | 1.73 | -0.0075 | -0.0007 |
| A | gates_only | 20 | 17 | 0.83 | 1.17 | 3.52 | -0.0035 | 0.0033 |
| B1 | gates_meas_init | 14 | 12 | -0.50 | 1.18 | 2.81 | -0.0029 | -0.0027 |
| B1 | gates_only | 14 | 10 | 1.24 | 1.11 | 2.43 | 0.0045 | 0.0046 |
<!-- /TABLE:S1_selene -->

`[F]` In the 468 noiseless runs the largest TVD between the sampled and the exact distribution is 0.117 and the largest ratio of TVD to its sampling scale sqrt(support / (2 pi N_shots)) is 1.121, so no run reaches the flag threshold of 4. No shot landed outside the exact support in any of the 468 runs. The support is smaller than 2^n on 276 runs, so a shot could have landed outside it there. The exact distribution of each compiled QASM file agrees with the family reference to 5.7e-11. The TVD divided by its asymptotic expectation for the actual distribution has median 0.93 and maximum 2.26 over the 468 runs. A pooled chi-square test against the exact multinomial on the 234 runs with support between 2 and 64 gives p < 0.01 on 4 runs and p < 0.05 on 13, against 2.3 and 11.7 expected under the null. The 4 runs were resampled with fresh seeds at 20000 shots (`results/selene_recheck.txt`) and none of the deviations persists.

`[O]` A wrong measure map or a wrong gate in the compiled QASM would put shots on zero-probability strings or push the TVD above its sampling scale. Neither happened on any of the 156 circuits under any of the three pipelines, so the compiled files run on Quantinuum's own toolchain and reproduce the distributions the local checks computed.

`[F]` In the depolarising runs the like-for-like variant `gates_meas_init` agrees with the density-matrix proxy within two sampling standard deviations on 32 of 34 runs, with mean z = -0.29, standard deviation of z 1.00 and largest |z| 2.81. The variant `gates_only` leaves readout and initialisation noiseless and agrees on 27 of 34 runs with mean z = +1.00. The mean of F_H under Selene minus the exact proxy F_H is -0.0056 in `gates_meas_init`, and that difference falls to -0.0016 once the proxy's F_H is also evaluated on 2000-shot samples, because a finite sample biases F_H downward.

`[F]` Selene's `DepolarizingErrorModel` was probed at p = 0.3 with 20000 shots per probe (`selene/calibrate_error_model.py`, `results/selene_calibration.txt`). Rz gates receive no noise. A single-qubit gate flips with probability 0.2051 +/- 0.0029 against 2p / 3 = 0.200 for a uniformly random non-identity Pauli. A ZZPhase leaves the 00 state with probability 0.2442 +/- 0.0030 against 12p / 15 = 0.240. Readout flips symmetrically at 0.306 and 0.304 and initialisation flips at 0.298. The conventions match `noise/dm_sim.py`, except that the proxy's readout flip is asymmetric and Selene's is one rate.

`[O]` The positive mean z of `gates_only` is expected for a model that omits two error sources the proxy keeps. The agreement of `gates_meas_init` confirms the proxy's implementation and its handling of the measure map. The agreement says nothing about the proxy's fidelity to H2-2E, because neither model contains the emission and leakage branch, the crosstalk or the duration-based dephasing of the published H2-2E model. The Selene runs are the first use of Quantinuum tooling in this submission and the emulator runs of Section 3.7 are the second.

`[F]` Wall time on the 2-core container was 465 s for the 468 noiseless runs with two processes and 68 s for the 68 depolarising runs. The per-run median is 1.4 s and the maximum 10.3 s (P1 on xxz_n10_r4_disorder_s1). Every TVD and F_H value was bit-identical between two complete runs of the driver.

### 3.7 Emulator runs

`[PENDING: emulator]` Once the team's Aqora credentials are in hand the runs will be the H2-2SC syntax check of every compiled circuit for its official HQC, the Nexus-tier H2-Emulator on families A (n <= 8) and B1 under P0, P1 and P2 with and without noise, and an H2-2E subset of P0 against P2 on family B1 within the credit budget.

<!-- CHANGELOG part2 -->

Changelog, part 2 (Section 3), 7 October 2026.

- A4: the two `[PENDING: certificates]` markers of 3.2 and 3.3 replaced by the certificate results, and a new 3.4 written with Table C1 (`<!-- TABLE:C1_certificates -->`, generated by `certificates()` in `report/make_tables.py` from `results/certificates.csv`). B2 configuration means 99.84, 99.79, 99.57, 99.76 %, minimum 99.28 %, floor <= T_zx on 24 of 24, mod5_4 floor 2 against T_zx 8 with 19 collapses, all recomputed. Manuscript comparison anchored at `papers/barrier/main.tex` lines 3066, 3076, 3079, 3108, 3118.
- A5: the provisional proxy paragraph of 3.1 removed. New 3.5 holds Table A4 (block moved from 3.1, content unchanged, already generated from `family_A_proxy_h22e.csv`), the new Table A5 (`<!-- TABLE:A5_proxy_b1 -->`, `family_b1_proxy()` from `results/family_B1_proxy_h22e.csv`), the B1 slope 1.18e-3 +/- 2.3e-5 (centred R^2 0.968) against p2 = 1.29e-3, the family A slope 5.14e-4 +/- 1.3e-5, the per-model slopes and the support term. The ordering P0 ~ P2 > P0ref > P1 ~ P3 requested for every cell does not hold in the data: P0ref is below P1 in the three xxz cells and below P3 in two of them, and at n = 4 over all models P1 = P3 = 0.9893 is above P0ref = 0.9867. The text states what the CSV gives.
- A6: "factors between 1.19 and 10.36" replaced by the per-pipeline ranges 1.28 to 10.32 (P1), 1.31 to 7.91 (P3), 1.44 to 10.36 (P4), and the mean ratio by n added.
- A7: citation added as instructed with the `[O: to be checked against the paper's table before submission]` marker. A web fetch of arXiv:1903.10477v3 on 7 October gave tof_3 15, mod5_4 8, vbe-adder_3 24 in the PyZX column and no grover_5 row. The arXiv title is "Reducing T-count with the ZX-calculus" and the DOI on the abstract page is 10.1103/PhysRevA.102.022406.
- A8: "P1 is above P0 on 13 of 14 completed, P3 on 14 of 15, P4 on 15 of 15" recomputed and stated in 3.2. The hwb8 long run (`results/family_B1_hwb8_long_counts.csv`, P1 8305, P2 5587, both ok) is reported in a separate paragraph with the note that it is not merged into `results/family_B1_counts.csv`.
- New 3.6 with Table S1 (`<!-- TABLE:S1_selene -->`, `selene()` from `results/selene_noiseless.csv` and `results/selene_depolarizing.csv`). New 3.7 placeholder.
- `report/make_tables.py`: three functions added (`family_b1_proxy`, `certificates`, `selene`), called from `main()`, with a console summary line each. INT_COLUMNS extended. `python report/make_tables.py --no-fig` run: 11 tables written, `report/report_v1.md` byte-identical before and after injection (checked with `cmp`).
- Recomputation commands run from the repository root: `python report/recompute_part2_check.py` (family A ratios and counts, proxy means per cell and per circuit, no-intercept fits and the support fit, B1 counts and T-counts, hwb8 long rows, certificate ratios and minima, Selene noiseless and depolarising summaries) and `python report/make_tables.py --no-fig`. The script prints every number quoted in this section and is kept in the repository.
