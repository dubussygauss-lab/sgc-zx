# Exactness-barrier certificates

Floor = lde of the exact Pauli channel (Corollary cert, Theorem C(c) of papers/barrier/main.tex), computed by barrier/certificate.py from the QASM as written. T_zx = T-count after the ZX stage of P1 (PyZX full_reduce) and P2 (PyZX teleport_reduce), from results/family_B2_counts.csv (t_count_after_zx) and results/family_B1_counts.csv (t_count_zx). incomp. = floor / T_written; removable = 1 - floor / T_written; achieved = 1 - T_zx / T_written; floor/T_zx is the quantity the manuscript's Table tab:e6 calls incomp. Invariant: floor <= T_zx.

| family | file | n | gates | T_written | floor | incomp. % | removable % | collapses | T_zx P1 | T_zx P2 | achieved % P1 | achieved % P2 | floor/T_zx % P2 | floor<=T_zx | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 | haar_n2_eps1e-03_s1.qasm | 2 | 1735 | 662 | 651 | 98.34 | 1.66 | 6 | 652 | 652 | 1.51 | 1.51 | 99.85 | True | 0.3 |
| B2 | haar_n2_eps1e-03_s2.qasm | 2 | 1690 | 628 | 611 | 97.29 | 2.71 | 9 | 612 | 612 | 2.55 | 2.55 | 99.84 | True | 0.2 |
| B2 | haar_n2_eps1e-03_s3.qasm | 2 | 1673 | 638 | 630 | 98.75 | 1.25 | 4 | 630 | 630 | 1.25 | 1.25 | 100.00 | True | 0.2 |
| B2 | haar_n2_eps1e-03_s4.qasm | 2 | 1659 | 622 | 613 | 98.55 | 1.45 | 5 | 614 | 614 | 1.29 | 1.29 | 99.84 | True | 0.2 |
| B2 | haar_n2_eps1e-03_s5.qasm | 2 | 1686 | 642 | 612 | 95.33 | 4.67 | 16 | 614 | 614 | 4.36 | 4.36 | 99.67 | True | 0.2 |
| B2 | haar_n2_eps1e-05_s1.qasm | 2 | 2713 | 1046 | 1021 | 97.61 | 2.39 | 14 | 1022 | 1022 | 2.29 | 2.29 | 99.90 | True | 0.4 |
| B2 | haar_n2_eps1e-05_s2.qasm | 2 | 2740 | 1046 | 1025 | 97.99 | 2.01 | 11 | 1026 | 1026 | 1.91 | 1.91 | 99.90 | True | 0.3 |
| B2 | haar_n2_eps1e-05_s3.qasm | 2 | 2712 | 1038 | 1002 | 96.53 | 3.47 | 19 | 1004 | 1004 | 3.28 | 3.28 | 99.80 | True | 0.3 |
| B2 | haar_n2_eps1e-05_s4.qasm | 2 | 2759 | 1052 | 1030 | 97.91 | 2.09 | 11 | 1036 | 1036 | 1.52 | 1.52 | 99.42 | True | 0.4 |
| B2 | haar_n2_eps1e-05_s5.qasm | 2 | 2777 | 1060 | 1033 | 97.45 | 2.55 | 15 | 1034 | 1034 | 2.45 | 2.45 | 99.90 | True | 0.4 |
| B2 | haar_n3_eps1e-03_s1.qasm | 3 | 6813 | 2566 | 2483 | 96.77 | 3.23 | 44 | 2496 | 2496 | 2.73 | 2.73 | 99.48 | True | 18.2 |
| B2 | haar_n3_eps1e-03_s2.qasm | 3 | 6760 | 2544 | 2442 | 95.99 | 4.01 | 52 | 2452 | 2452 | 3.62 | 3.62 | 99.59 | True | 17.6 |
| B2 | haar_n3_eps1e-03_s3.qasm | 3 | 6855 | 2570 | 2486 | 96.73 | 3.27 | 44 | 2490 | 2490 | 3.11 | 3.11 | 99.84 | True | 13.2 |
| B2 | haar_n3_eps1e-03_s4.qasm | 3 | 6864 | 2588 | 2511 | 97.02 | 2.98 | 41 | 2520 | 2520 | 2.63 | 2.63 | 99.64 | True | 13.1 |
| B2 | haar_n3_eps1e-03_s5.qasm | 3 | 6873 | 2590 | 2478 | 95.68 | 4.32 | 58 | 2496 | 2496 | 3.63 | 3.63 | 99.28 | True | 12.7 |
| B2 | haar_n3_eps1e-05_s1.qasm | 3 | 10968 | 4208 | 4132 | 98.19 | 1.81 | 42 | 4144 | 4144 | 1.52 | 1.52 | 99.71 | True | 32.8 |
| B2 | haar_n3_eps1e-05_s2.qasm | 3 | 10940 | 4218 | 4158 | 98.58 | 1.42 | 31 | 4162 | 4162 | 1.33 | 1.33 | 99.90 | True | 36.4 |
| B2 | haar_n3_eps1e-05_s3.qasm | 3 | 10971 | 4224 | 4179 | 98.93 | 1.07 | 23 | 4188 | 4188 | 0.85 | 0.85 | 99.79 | True | 28.8 |
| B2 | haar_n3_eps1e-05_s4.qasm | 3 | 11007 | 4248 | 4184 | 98.49 | 1.51 | 34 | 4192 | 4192 | 1.32 | 1.32 | 99.81 | True | 26.9 |
| B2 | haar_n3_eps1e-05_s5.qasm | 3 | 10916 | 4206 | 4133 | 98.26 | 1.74 | 39 | 4150 | 4150 | 1.33 | 1.33 | 99.59 | True | 28.8 |
| B1 | barenco_tof_3.qasm | 5 | 76 | 28 | 4 | 14.29 | 85.71 | 18 | 16 | 16 | 42.86 | 42.86 | 25.00 | True | 15.2 |
| B1 | mod5_4.qasm | 5 | 79 | 28 | 2 | 7.14 | 92.86 | 19 | 8 | 8 | 71.43 | 71.43 | 25.00 | True | 15.6 |
| B1 | qft_4.qasm | 5 | 187 | 69 | 37 | 53.62 | 46.38 | 26 | 67 | 67 | 2.90 | 2.90 | 55.22 | True | 38.5 |
| B1 | tof_3.qasm | 5 | 57 | 21 | 4 | 19.05 | 80.95 | 13 | 15 | 15 | 28.57 | 28.57 | 26.67 | True | 10.1 |

Invariant floor <= T_zx: 24 rows checked, 0 violations.

## B2 per configuration (mean over instances, min in brackets)

| n | eps | N | mean T_written | mean incomp. % (floor/T_written) | mean floor/T_zx % (P2) | mean achieved % (P2) | mean collapse rate % |
|---|---|---|---|---|---|---|---|
| 2 | 1e-03 | 5 | 638 | 97.65 [95.33] | 99.84 [99.67] | 2.19 | 1.25 |
| 2 | 1e-05 | 5 | 1048 | 97.50 [96.53] | 99.79 [99.42] | 2.29 | 1.34 |
| 3 | 1e-03 | 5 | 2572 | 96.44 [95.68] | 99.57 [99.28] | 3.14 | 1.86 |
| 3 | 1e-05 | 5 | 4221 | 98.49 [98.19] | 99.76 [99.59] | 1.27 | 0.80 |

Population standard deviations (P2): floor/T_zx 99.84±0.10, 99.79±0.19, 99.57±0.19, 99.76±0.10; achieved reduction 2.19±1.18, 2.29±0.59, 3.14±0.42, 1.27±0.22 (same row order). P1 and P2 give the same T_zx on every row.

## Comparison with papers/barrier/main.tex

Table tab:e6 (lines 3075-3079, columns n, eps, N, T_raw, reduction %, incomp. % [min]):
`2 & $10^{-3}$ & 50 & 644  & $2.6\pm1.4$ & $99.79\pm0.30$ [98.6]` and
`3 & $10^{-3}$ & 8  & 2570 & $2.1\pm0.7$ & $99.55\pm0.20$ [99.3]`; incomp. is defined in the caption (line 3066) as `$\mathrm{lde}/T_{\mathrm{tel}}$`, the floor over the post-teleport_reduce count, i.e. floor/T_zx (P2) here, not floor/T_written. Line 3108: `$\mathrm{lde}/T_{\mathrm{tel}}$ averages $99.4$--$99.9\%$ and never falls below $96.9\%$ on any single instance`. Line 3118: collapse rate `$1.0$--$2.3\%$`.

Our instances at eps = 1e-3 (N = 5 each): n = 2 gives 99.84 [99.67] against 99.79 [98.6]; n = 3 gives 99.57 [99.28] against 99.55 [99.3]. All four configuration means (99.57 to 99.84) lie inside the manuscript's 99.4 to 99.9 range and every instance is above 96.9. The eps = 1e-5 configurations have no counterpart in the table. The n = 3, eps = 1e-3 mean reduction 3.14 is above the table's 2.1±0.7. Collapse rates 0.80 to 1.86 overlap the 1.0 to 2.3 range except n = 3, eps = 1e-5 (0.80), an accuracy not in the table. The B1 circuits are not synthesized gridsynth circuits and are not covered by the manuscript's numbers.
