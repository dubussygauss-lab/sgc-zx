Nexus H2-Emulator, noisy_simulation = True, 1000 shots per row. F_H is the Hellinger fidelity of the returned counts to the ideal distribution. sd F_H emulator is the sd of F_H over 4000 multinomial bootstrap resamples of the counts (seed 20261008). F_H proxy is the exact density-matrix proxy value of Section 3.5 and is empty where the proxy has no row. F_H Selene depol is the 2000-shot Selene DepolarizingErrorModel value of Section 3.6.

| file | n | pipeline | n_2q | F_H emulator | sd F_H emulator | F_H proxy | F_H Selene depol |
|---|---|---|---|---|---|---|---|
| tof_3 | 5 | P0 | 15 | 0.9860 | 0.0037 | 0.9791 | 0.9785 |
| tof_3 | 5 | P2 | 14 | 0.9810 | 0.0044 | 0.9800 | 0.9810 |
| barenco_tof_3 | 5 | P0 | 20 | 0.9770 | 0.0048 | 0.9739 | 0.9740 |
| barenco_tof_3 | 5 | P1 | 23 | 0.9760 | 0.0049 | 0.9692 | 0.9700 |
| barenco_tof_3 | 5 | P2 | 19 | 0.9660 | 0.0057 | 0.9747 | 0.9655 |
| barenco_tof_4 | 7 | P0 | 40 | 0.9500 | 0.0068 | 0.9513 | 0.9470 |
| barenco_tof_4 | 7 | P1 | 41 | 0.9420 | 0.0073 | 0.9451 | 0.9490 |
| barenco_tof_4 | 7 | P2 | 38 | 0.9660 | 0.0057 | 0.9528 | 0.9450 |
| barenco_tof_5 | 9 | P0 | 60 | 0.9280 | 0.0080 |  | 0.9305 |
| barenco_tof_5 | 9 | P1 | 70 | 0.9160 | 0.0088 |  | 0.9120 |
| barenco_tof_5 | 9 | P2 | 57 | 0.9130 | 0.0088 |  | 0.9255 |
| grover_5 | 9 | P0 | 240 | 0.7898 | 0.0131 |  | 0.8245 |
| ladder_n4_r1_uniform_s1 | 4 | P0 | 4 | 0.9993 | 0.0009 | 0.9992 | 0.9984 |
| ladder_n4_r1_uniform_s1 | 4 | P1 | 11 | 0.9927 | 0.0027 | 0.9954 | 0.9948 |
| ladder_n4_r1_uniform_s1 | 4 | P2 | 4 | 0.9981 | 0.0014 | 0.9992 | 0.9978 |
| ladder_n4_r2_uniform_s1 | 4 | P0 | 8 | 0.9993 | 0.0017 | 0.9995 | 0.9975 |
| ladder_n4_r2_uniform_s1 | 4 | P1 | 25 | 0.9901 | 0.0033 | 0.9933 | 0.9899 |
| ladder_n4_r2_uniform_s1 | 4 | P2 | 8 | 0.9947 | 0.0018 | 0.9995 | 0.9970 |
| ladder_n4_r4_uniform_s1 | 4 | P0 | 16 | 0.9957 | 0.0026 | 0.9998 | 0.9987 |
| ladder_n4_r4_uniform_s1 | 4 | P1 | 42 | 0.9912 | 0.0032 | 0.9970 | 0.9950 |
| ladder_n4_r4_uniform_s1 | 4 | P2 | 16 | 0.9924 | 0.0029 | 0.9998 | 0.9975 |
| ladder_n6_r1_uniform_s1 | 6 | P0 | 7 | 0.9963 | 0.0018 | 0.9986 | 0.9962 |
