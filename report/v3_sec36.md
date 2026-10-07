### 3.6 Selene runs

`[F]` Tables S1 and S2. Runs of the compiled circuits on Quantinuum's local emulator Selene (`selene-sim` 0.3.4, route in Section 2.6), from `results/selene_noiseless.csv` (468 rows), `results/selene_depolarizing.csv` (68 rows) and `results/selene_depolarizing_full.csv` (468 rows). The noiseless runs cover the 144 family A circuits with n <= 10 and the 12 family B1 circuits with n <= 10 under P0, P1 and P2 at 2000 shots. The full depolarising run covers the same 156 circuits under P0, P1 and P2 at 2000 shots with `DepolarizingErrorModel` at the H2-2E rates p_1q = 7.3e-5, p_2q = 1.29e-3, p_meas = 1.35e-3 and p_init = 4e-5.

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

<!-- TABLE:S2_selene_depol -->
Depolarising runs on the full set (DepolarizingErrorModel, p_1q = 7.3e-5, p_2q = 1.29e-3, p_meas = 1.35e-3, p_init = 4e-5, 2000 shots). F_H is the Hellinger fidelity of the Selene samples to the ideal distribution. P0 > P1 and P2 > P1 count circuits with a strictly higher F_H.

| family | n | circuits | mean F_H P0 | mean F_H P1 | mean F_H P2 | P0 > P1 | P2 > P1 |
|---|---|---|---|---|---|---|---|
| A | 4 | 36 | 0.9914 | 0.9880 | 0.9902 | 33 | 29 |
| A | 6 | 36 | 0.9832 | 0.9706 | 0.9820 | 35 | 32 |
| A | 8 | 36 | 0.9705 | 0.9410 | 0.9691 | 36 | 34 |
| A | 10 | 36 | 0.9517 | 0.8918 | 0.9501 | 36 | 36 |
| B1 | 5 | 4 | 0.9722 | 0.9638 | 0.9739 | 4 | 3 |
| B1 | 7 | 3 | 0.9328 | 0.9210 | 0.9308 | 2 | 2 |
| B1 | 9 | 4 | 0.9121 | 0.8816 | 0.9109 | 4 | 4 |
| B1 | 10 | 1 | 0.9410 | 0.9260 | 0.9350 | 1 | 1 |
| all |  | 156 | 0.9716 | 0.9459 | 0.9702 | 151 | 141 |
<!-- /TABLE:S2_selene_depol -->

`[F]` Table S2. The full depolarising run has 468 runs on 156 circuits. The mean F_H over the 156 circuits is 0.9716 for P0, 0.9459 for P1 and 0.9702 for P2. P0 is strictly above P1 on 151 circuits and P2 is strictly above P1 on 141. Both P0 and P2 are strictly above P1 on 140 of the 156 circuits. The 16 exceptions are 14 family A circuits with n <= 8 and the B1 circuits barenco_tof_3 and barenco_tof_4.

`[F]` The mean of F_H(P2) minus F_H(P0) over the 156 circuits is -0.0013 and P2 is strictly above P0 on 67 circuits. The single-run sampling sd of F_H at 2000 shots has mean 0.0028 over the 345 runs with a proxy row. The mean difference is therefore 0.47 single-run sampling sd. The standard error of the mean difference over the 156 circuits is 0.0004.

`[O]` A single circuit's ordering of P2 against P0 is not resolved at 2000 shots. The ensemble mean favours P0 by 0.0013 in F_H, which is small next to the P1 deficit of 0.0256 against P0.

`[F]` 345 of the 468 runs have a density-matrix proxy row. The 123 runs without one are the family A circuits with n = 10 and the family B1 circuits with n = 9 and n = 10. On the 345 runs |z| <= 2 holds for 335, which is 97.1 %. The mean z is -0.001 and the population sd of z is 0.957 with largest |z| 2.82. Independent draws from the proxy's sampling distribution give mean 0, sd 1 and 95.4 % within two sd. The mean of F_H under Selene minus the exact proxy F_H is -0.0051 and falls to +0.0002 against the proxy's F_H evaluated on 2000-shot samples.

`[F]` An earlier 68-run comparison on 17 circuits under P0 and P2 agreed within two sd on 32 of 34 runs in `gates_meas_init` and on 27 of 34 runs in `gates_only`, which leaves readout and initialisation noiseless.

`[F]` Selene's `DepolarizingErrorModel` was probed at p = 0.3 with 20000 shots per probe (`selene/calibrate_error_model.py`, `results/selene_calibration.txt`). Rz gates receive no noise. A single-qubit gate flips with probability 0.2051 +/- 0.0029 against 2p / 3 = 0.200 for a uniformly random non-identity Pauli. A ZZPhase leaves the 00 state with probability 0.2442 +/- 0.0030 against 12p / 15 = 0.240. Readout flips symmetrically at 0.306 and 0.304 and initialisation flips at 0.298. The conventions match `noise/dm_sim.py`, except that the proxy's readout flip is asymmetric and Selene's is one rate.

`[O]` Selene's `DepolarizingErrorModel` and the proxy share one gate-level convention, so their agreement checks the proxy's implementation and its handling of the measure map. The agreement does not test fidelity to H2-2E. Neither model contains the emission and leakage branch, the crosstalk or the duration-based dephasing of the published H2-2E model. The Selene runs are the first use of Quantinuum tooling in this submission and the emulator runs of Section 3.7 are the second.

`[F]` Wall time on the 2-core container was 465 s for the 468 noiseless runs and 68 s for the 68-run comparison, both with two processes. The per-run wall times of the 468 full depolarising runs sum to 1437 s. Every TVD and F_H value of the noiseless runs and the 68-run comparison was bit-identical between two complete runs of the driver. `results/selene.md` records one execution of the full depolarising run.
