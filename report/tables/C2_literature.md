`[F]` Per circuit of families B1 and B1x. T after ZX is the P2 T-count. best ancilla-free is the smallest T-count reported in the six papers on the same n qubits, taken over the columns of `results/literature_tcounts.csv` with ancilla_free = yes, same_circuit = yes and reported_error = no. best with ancillas is the smallest published T-count of a method that adds Hadamard ancillas. These methods are TODD and AlphaTensor-Quantum when its compiled qubit count exceeds n. The floor is the certified lde floor of Table C1 and exists for the four n = 5 circuits only. T after ZX - best is the part of the ZX output that a published ancilla-free method is known to remove. best - floor is the part that neither a published method nor the certificate has closed. Source keys: AMM2014 arXiv:1303.2042 Table 1, AM2016 arXiv:1601.07363 Table II, Nam2018 arXiv:1710.07345 Table 4, TODD2018 and TODDpart2018 arXiv:1712.01557 Tables I and II, KvdW2020 arXiv:1903.10477 Table 1, AQ2024 arXiv:2402.14396 Table 2. grover_5 has no same-circuit published value.

| family | circuit | n | T written | T after ZX | best ancilla-free | source | best with ancillas | source (ancillas) | floor | T after ZX - best | best - floor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | barenco_tof_3 | 5 | 28 | 16 | 16 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 13 | AQ2024 | 4 | 0 | 12 |
| B1 | mod5_4 | 5 | 28 | 8 | 7 | AQ2024, KvdW2020_PyZXTODD | 16 | TODD2018 | 2 | 1 | 5 |
| B1 | qft_4 | 5 | 69 | 67 | 67 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, TODDpart2018 | 53 | AQ2024 | 37 | 0 | 30 |
| B1 | tof_3 | 5 | 21 | 15 | 15 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_L, TODDpart2018 | 13 | AQ2024, TODD2018 | 4 | 0 | 11 |
| B1 | barenco_tof_4 | 7 | 56 | 28 | 28 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 23 | AQ2024 |  | 0 |  |
| B1 | hwb6 | 7 | 105 | 75 | 71 | AM2016_Tpar | 51 | AQ2024, TODD2018 |  | 4 |  |
| B1 | tof_4 | 7 | 35 | 23 | 23 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_L, TODDpart2018 | 19 | AQ2024, TODD2018 |  | 0 |  |
| B1 | barenco_tof_5 | 9 | 84 | 40 | 40 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 33 | AQ2024 |  | 0 |  |
| B1 | grover_5 | 9 | 336 | 166 |  |  |  |  |  |  |  |
| B1 | mod_mult_55 | 9 | 49 | 35 | 20 | KvdW2020_PyZXTODD | 17 | AQ2024, TODD2018 |  | 15 |  |
| B1 | tof_5 | 9 | 49 | 31 | 31 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_L, TODDpart2018 | 25 | AQ2024, TODD2018 |  | 0 |  |
| B1 | vbe_adder_3 | 10 | 70 | 24 | 24 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_L | 19 | AQ2024 |  | 0 |  |
| B1 | mod_red_21 | 11 | 119 | 73 | 73 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 51 | AQ2024 |  | 0 |  |
| B1 | gf2_pow_4_mult | 12 | 112 | 68 | 39 | AQ2024 | 54 | TODD2018 |  | 29 |  |
| B1 | hwb8 | 12 | 5887 | 3517 | 3501 | KvdW2020_PyZXTODD |  |  |  | 16 |  |
| B1x | rc_adder_6 | 14 | 77 | 47 | 47 | AM2016_RMmaj, AM2016_RMrec, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 37 | AQ2024, TODD2018 |  | 0 |  |
| B1x | csla_mux_3 | 15 | 70 | 62 | 45 | KvdW2020_PyZXTODD | 39 | AQ2024 |  | 17 |  |
| B1x | gf2_pow_5_mult | 15 | 175 | 115 | 59 | AQ2024 | 87 | TODD2018 |  | 56 |  |
| B1x | ham15-low | 17 | 161 | 97 | 97 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD | 73 | AQ2024 |  | 0 |  |
| B1x | ham15-med | 17 | 574 | 212 | 212 | KvdW2020_PyZX, KvdW2020_PyZXTODD | 162 | TODD2018 |  | 0 |  |
| B1x | gf2_pow_6_mult | 18 | 252 | 150 | 77 | AQ2024 | 126 | TODD2018 |  | 73 |  |
| B1x | barenco_tof_10 | 19 | 224 | 100 | 100 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_H, Nam2018_L | 83 | AQ2024 |  | 0 |  |
| B1x | tof_10 | 19 | 119 | 71 | 71 | AM2016_RMmaj, AM2016_RMrec, AM2016_Tpar, AMM2014_Tpar, KvdW2020_PyZX, KvdW2020_PyZXTODD, Nam2018_L, TODDpart2018 | 55 | AQ2024, TODD2018 |  | 0 |  |

`[F]` On the 4 circuits with a floor: T after ZX 106, best ancilla-free 105, floor 47. T after ZX - best = 1, best - floor = 58, sum 59. Best with ancillas on the same circuits: 95.
