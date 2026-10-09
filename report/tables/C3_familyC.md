`[F]` Family C, count-only. HQC at 1000 shots with every qubit measured (`compile.hqc`). PSEL keeps the lower HQC of P0 and P2, an HQC tie goes to the lower n_2q and a further tie to P0. saved % is computed on the sums against P0. T saved is the T-count removed by the ZX stage on the circuits where PSEL picks P2. checked counts circuits whose P0 and P2 outputs both agree with the input on 64 random basis inputs up to a global phase (`pipelines/run_family_C.py --check`). unchecked means the sparse simulation exceeded 2^20 amplitudes. A pass covers 64 of 2^n inputs and is not a proof of equivalence. continuous angles marks inputs with rotations outside the pi/4 grid (`bench/family_C/manifest.csv`). Source: `value/family_C_selector.csv`.

| application | circuits | qubits | PSEL picks P2 | HQC P0 | HQC P2 | HQC PSEL | saved vs P0 | saved % | saved vs P2 | n_2q P0 | n_2q PSEL | T written | T saved | checked |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Grover oracle (MCX) | 6 | 21-56 | 3 | 4,242.6 | 4,239.8 | 4,239.8 | 2.8 | 0.1 | 0.0 | 1677 | 1676 | 1827 | 30 | 4 |
| QFT adder | 3 | 20-56 | 0 | 4,778.4 | 5,835.6 | 4,778.4 | 0.0 | 0.0 | 1,057.2 | 2004 | 2004 | 459 | 0 | 1 |
| adder | 9 | 20-56 | 9 | 5,777.0 | 5,031.4 | 5,031.4 | 745.6 | 12.9 | 0.0 | 2222 | 1871 | 2198 | 1110 | 7 |
| multiplier | 2 | 21-24 | 2 | 9,737.0 | 6,381.0 | 6,381.0 | 3,356.0 | 34.5 | 0.0 | 4329 | 2797 | 3353 | 1408 | 2 |
| all | 20 | 20-56 | 14 | 24,535.0 | 21,487.8 | 20,430.6 | 4,104.4 | 16.7 | 1,057.2 | 10232 | 8348 | 7837 | 2548 | 14 |

| file | n | application | pick | HQC P0 | HQC P2 | HQC PSEL | saved % | n_2q P0 | n_2q PSEL | T written | T after ZX P2 | continuous angles | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mcx_clean_11 | 21 | Grover oracle (MCX) | P0 | 180.8 | 180.8 | 180.8 | 0.0 | 59 | 59 | 79 | 79 | no | pass |
| mcx_b95_20 | 22 | Grover oracle (MCX) | P2 | 693.4 | 693.0 | 693.0 | 0.1 | 292 | 292 | 308 | 296 | no | pass |
| mcx_clean_20 | 39 | Grover oracle (MCX) | P0 | 339.2 | 339.2 | 339.2 | 0.0 | 113 | 113 | 151 | 151 | no | pass |
| mcx_clean_28 | 55 | Grover oracle (MCX) | P0 | 480.0 | 480.0 | 480.0 | 0.0 | 161 | 161 | 215 | 215 | no | pass |
| mcx_dirty_28 | 55 | Grover oracle (MCX) | P2 | 591.0 | 589.0 | 589.0 | 0.3 | 216 | 215 | 222 | 216 | no | unchecked |
| mcx_b95_54 | 56 | Grover oracle (MCX) | P2 | 1,958.2 | 1,957.8 | 1,957.8 | 0.0 | 836 | 836 | 852 | 840 | no | unchecked |
| draper_adder_10 | 20 | QFT adder | P0 | 370.4 | 550.8 | 370.4 | 0.0 | 145 | 145 | 81 | 31 | yes | pass |
| draper_adder_16 | 32 | QFT adder | P0 | 906.8 | 1,385.0 | 906.8 | 0.0 | 376 | 376 | 135 | 49 | yes | unchecked |
| draper_adder_28 | 56 | QFT adder | P0 | 3,501.2 | 3,899.8 | 3,501.2 | 0.0 | 1483 | 1483 | 243 | 85 | yes | unchecked |
| modadd_2n_10 | 20 | adder | P2 | 388.2 | 371.6 | 371.6 | 4.3 | 147 | 142 | 72 | 72 | no | unchecked |
| cdkm_adder_10 | 22 | adder | P2 | 371.6 | 333.8 | 333.8 | 10.2 | 141 | 121 | 140 | 80 | no | pass |
| vbe_adder_7 | 22 | adder | P2 | 370.4 | 294.4 | 294.4 | 20.5 | 142 | 107 | 182 | 56 | no | pass |
| cdkm_adder_15 | 32 | adder | P2 | 551.6 | 494.4 | 494.4 | 10.4 | 211 | 181 | 210 | 120 | no | pass |
| vbe_adder_11 | 34 | adder | P2 | 593.6 | 469.4 | 469.4 | 20.9 | 230 | 173 | 294 | 88 | no | pass |
| modadd_2n_20 | 40 | adder | P2 | 802.2 | 779.6 | 779.6 | 2.8 | 307 | 302 | 152 | 152 | no | unchecked |
| cdkm_adder_20 | 42 | adder | P2 | 731.6 | 655.8 | 655.8 | 10.4 | 281 | 241 | 280 | 160 | no | pass |
| vbe_adder_18 | 55 | adder | P2 | 984.2 | 751.6 | 751.6 | 23.6 | 384 | 279 | 490 | 144 | no | pass |
| cdkm_adder_27 | 56 | adder | P2 | 983.6 | 880.8 | 880.8 | 10.5 | 379 | 325 | 378 | 216 | no | pass |
| hrs_mult_5 | 21 | multiplier | P2 | 5,291.4 | 4,174.4 | 4,174.4 | 21.1 | 2335 | 1807 | 3035 | 1872 | yes | pass |
| rgqft_mult_6 | 24 | multiplier | P2 | 4,445.6 | 2,206.6 | 2,206.6 | 50.4 | 1994 | 990 | 318 | 73 | yes | pass |

`[F]` 20 circuits, 14 checked and 6 unchecked. PSEL saves 4,104.4 HQC or 16.7 % against P0 and 1,057.2 HQC against P2. Saving on the checked circuits 4,062.8 HQC, on the unchecked circuits 41.6 HQC.
