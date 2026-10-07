## 4. Learned cost model

`[F]` Version 1 of this section was a protocol with no trained model. Version 2 trains the model on the local proxy fidelities of Section 3 and reports its validation. Every number in Tables M1 and M2 is produced by `report/make_tables.py` from `results/cost_model_metrics.csv` and `results/cost_model_coefficients.csv`, which are written by `model/cost_model.py`.

`[F]` Data. The training set is the proxy output of `noise/run_proxy.py` with the published H2-2E emulator defaults p1 = 7.3e-5, p2 = 1.29e-3, readout flip rates 9e-4 and 1.8e-3 and p_init = 4e-5. Family A contributes 540 rows, the 108 Trotter circuits with n in {4, 6, 8} under the five pipelines P0ref, P0, P1, P2 and P3. Family B1 contributes 35 rows, the 7 benchmark circuits with n in {5, 7} under the same five pipelines. F_H is the Hellinger fidelity of the exact noisy output distribution against the ideal one, with no shot sampling. `[O]` These are proxy numbers from a density-matrix model that omits leakage, crosstalk and duration-based dephasing. The script reruns unchanged on emulator CSVs with the same columns, and every table of this section will be refit on emulator data `[PENDING: emulator]`.

### 4.1 Target and features

`[F]` The target is y = -ln F_H. For a product of independent small error channels F_H is close to exp(-sum_k p_k N_k), so y is linear in the gate counts to first order. The seven features are read from the compiled circuit: n_2q, the ZZPhase and ZZMax count, which carries the dominant fault probability p2. n_1q, the PhasedX count, which carries p1. Rz is virtual and noiseless and is not counted. n_qubits, the number of measured qubits, which carries one readout and one initialisation fault each. depth_2q, the two-qubit depth, which stands in for idle error since the proxy has no duration model. support_size, the number of bitstrings with ideal probability above 1e-12, and log2_support. The seventh feature is the interaction n_2q_offsupport = n_2q (1 - support_size / 2^n). `[O]` The interaction is justified by the metric. A Pauli fault after a gate moves a fraction of the output mass to other bitstrings. When the ideal distribution covers most of the 2^n strings the displaced mass lands on strings that already carry ideal weight and the Hellinger overlap barely changes. When the ideal output is one string every fault removes its mass from the support and the full per-gate error appears in y. The factor (1 - support_size / 2^n) is the fraction of the output space outside the support and is the first-order estimate of the lost mass. `[F]` The two families sit at opposite ends of this factor. The mean support fraction support_size / 2^n is 0.758 in family A and 280 of its 540 rows have full support. In family B1 the mean support fraction is 0.088 and the three values that occur are 0.0078, 0.031 and 0.5.

### 4.2 Models

`[F]` Four models are fitted to y on the same feature matrix. The physics baseline y = p2 n_2q + p1 n_1q + (p_meas_avg + p_init) n_qubits has no fitted parameter, with p_meas_avg + p_init = 1.39e-3 the mean of the two readout flip rates plus the initialisation fault. The OLS model is least squares on the seven features without intercept, since an empty circuit has y = 0 and the n_qubits column carries the SPAM floor. The ridge model scales each column to unit RMS on the training set and applies penalty lambda = 1 to the scaled coefficients, again without intercept. The gradient-boosted model is sklearn `GradientBoostingRegressor` with 300 trees of depth 3, learning rate 0.05, subsample 0.8 and `random_state=0`. `[O]` The three fitted models are ordered by capacity. OLS tests whether a linear correction of the physics baseline is enough. Ridge tests whether the OLS coefficients are stable under shrinkage. The boosted model is the learned component and tests whether a nonlinear fit buys anything beyond the linear one.

### 4.3 Validation splits

`[F]` Three kinds of split are reported. Leave-one-family-out trains on A and tests on B1 and the reverse. Leave-one-model-out trains on two of the three Trotter models of A and tests on the third. Five-fold cross-validation on the pooled 575 rows is run twice. In the plain split cv5 the rows are shuffled into folds with seed 0. In the grouped split cv5g the folds are drawn over circuit classes, where a class is the file name with the disorder-seed suffix removed, so that all pipelines and all seeds of a class are in the same fold.

`[F]` The grouped split exists because the seeds of one circuit class are near-duplicate rows. 27 of the 54 classes of A have three disorder seeds. Within one class and one pipeline the three seeds have identical n_2q, identical depth_2q and identical support_size in 265 of the 270 class-pipeline groups, and their F_H values lie within 0.0056 of each other. A random fold therefore places a near-copy of almost every test row in the training set and its score measures interpolation between pipelines and seeds of a circuit already seen. `[F]` The effect is visible in Table M1. The boosted model scores R^2 0.990 on cv5 and 0.971 on cv5g on the pooled rows, and 0.923 against 0.830 on the B1 rows. `[O]` The grouped split is the one that answers the question a user asks, which is the fidelity of a circuit the model has not seen, and it is the split used for the calibration figure and the permutation importance.

### 4.4 Results

`[F]` Table M1. R^2 of y and mean absolute error of F_H on the test set of each split, one cell per model. R^2 is taken about the mean of the test y and is negative for a model worse than that mean. n is the number of test rows.

<!-- TABLE:M1_cost_metrics -->
| split | train | test | n | physics | ols | ridge | gbr |
|---|---|---|---|---|---|---|---|
| lofo | A | B1 | 35 | 0.785 / 0.0151 | 0.560 / 0.0252 | 0.840 / 0.0150 | 0.805 / 0.0083 |
| lofo | B1 | A | 540 | -3.513 / 0.0430 | -261.894 / 0.1971 | -0.605 / 0.0259 | 0.326 / 0.0184 |
| lomo | A minus ladder | A ladder | 180 | -34.797 / 0.0489 | 0.399 / 0.0058 | 0.410 / 0.0060 | 0.751 / 0.0030 |
| lomo | A minus tfim | A tfim | 180 | -33.455 / 0.0424 | 0.637 / 0.0044 | 0.522 / 0.0047 | 0.843 / 0.0023 |
| lomo | A minus xxz | A xxz | 180 | -2.061 / 0.0376 | -1.272 / 0.0350 | 0.541 / 0.0159 | -1.035 / 0.0353 |
| cv5 | A+B1 (4/5) | A+B1 (1/5) | 575 | -2.739 / 0.0413 | 0.944 / 0.0050 | 0.944 / 0.0050 | 0.990 / 0.0009 |
| cv5g | A+B1 (4/5) | A+B1 (1/5) | 575 | -2.739 / 0.0413 | 0.938 / 0.0051 | 0.938 / 0.0052 | 0.971 / 0.0017 |
| cv5g | A+B1 (4/5) | A rows of fold | 540 | -3.513 / 0.0430 | 0.937 / 0.0049 | 0.935 / 0.0050 | 0.990 / 0.0014 |
| cv5g | A+B1 (4/5) | B1 rows of fold | 35 | 0.785 / 0.0151 | 0.918 / 0.0090 | 0.926 / 0.0079 | 0.830 / 0.0074 |
<!-- /TABLE:M1_cost_metrics -->

`[F]` Table M2. Coefficients of y per unit of each feature. The physics column is fixed by the emulator parameters. The OLS columns give the coefficient and its t statistic for the three training sets. The ridge column is the shrunk coefficient on the pooled set. The last column is the permutation importance of the boosted model, the mean increase of out-of-fold mean squared error of y when that feature is shuffled in the test fold of cv5g, with the standard deviation over 5 folds times 10 shuffles. `[O]` The OLS standard errors assume independent homoscedastic residuals. The five pipeline rows of one circuit are not independent, so the t statistics are optimistic and only their ranking is used below.

<!-- TABLE:M2_cost_coefficients -->
| feature | physics | OLS A (t) | OLS B1 (t) | OLS A+B1 (t) | ridge A+B1 | GBR importance (sd) |
|---|---|---|---|---|---|---|
| n_2q | 1.29e-03 | 3.73e-04 (11.8) | -4.77e-05 (-0.2) | 2.89e-04 (8.2) | 2.56e-04 | 5.95e-05 (1.2e-05) |
| n_1q | 7.30e-05 | 7.38e-06 (0.4) | 8.08e-05 (0.9) | 4.65e-05 (2.2) | 5.86e-05 | 2.91e-05 (4.0e-05) |
| n_qubits | 1.39e-03 | 8.69e-03 (17.0) | -5.57e-05 (-0.1) | 3.81e-03 (15.0) | 3.49e-03 | 2.89e-06 (1.6e-06) |
| depth_2q |  | -1.90e-04 (-6.2) | 1.68e-04 (1.0) | -1.40e-04 (-4.2) | -1.10e-04 | 4.13e-05 (2.2e-05) |
| support_size |  | 2.85e-06 (0.6) | 4.57e-03 (1.4) | -5.03e-06 (-0.9) | -4.99e-06 | 2.70e-06 (2.3e-06) |
| log2_support |  | -9.12e-03 (-16.2) | -1.71e-02 (-1.4) | -3.91e-03 (-13.6) | -3.57e-03 | 1.91e-06 (2.1e-06) |
| n_2q_offsupport |  | 4.97e-04 (24.7) | 9.81e-04 (4.1) | 6.19e-04 (30.3) | 6.27e-04 | 1.47e-03 (7.0e-04) |
<!-- /TABLE:M2_cost_coefficients -->

![Cost model calibration and coefficients](figures/fig_cost_model.png)

Figure 4. Learned cost model on the proxy data. Left, predicted F_H = exp(-y_hat) against actual F_H. Filled points are the out-of-fold cv5g predictions of the OLS model for family A in blue and family B1 in orange. Hollow squares are the B1 predictions of the OLS model trained on A only and hollow triangles those of the boosted model trained on A only. The dotted line is the identity. Right, the OLS coefficients on the pooled set multiplied by the standard deviation of each feature with 1 SE bars on the lower axis, and the permutation importance of the boosted model as diamonds on the upper axis. Data: Tables M1 and M2, `results/fig_cost_model.png`.

`[F]` In the left panel the hollow squares for the B1 circuits with actual F_H between 0.94 and 0.98 lie below the identity line, so the A-trained OLS model under-predicts their fidelity. The hollow triangles of the A-trained boosted model lie closer to the line on the same circuits. The filled B1 points of the grouped cross-validation lie on or near the line over the full range from 0.80 to 0.98.

### 4.5 What the data support

`[F]` Across families the transfer is one-directional. Trained on A, the boosted model predicts B1 with R^2 0.805 and MAE(F_H) 0.0083. The unfitted physics baseline gives R^2 0.785 and MAE(F_H) 0.0151 on the same 35 rows. Ridge reaches R^2 0.840 with MAE(F_H) 0.0150 and OLS reaches 0.560 with 0.0252. Fitting on A lowers the B1 error of the best model by 0.0067 in MAE(F_H), a factor 1.81 below the baseline. Trained on B1, no model predicts A. The best R^2 in that direction is 0.326 for the boosted model and the other three are negative. `[O]` Seven circuits under five pipelines are 35 rows spanning three support fractions and cannot pin down seven coefficients, which the OLS B1 column of Table M2 shows directly. The only coefficient with |t| above 2 on B1 is n_2q_offsupport at 4.1. `[O]` The one direction that works rests on 7 test circuits and does not establish generalisation.

`[F]` Within family A the models interpolate across circuit classes. On the grouped split the A rows score R^2 0.937 for OLS and 0.990 for the boosted model. Holding out a whole Trotter model is harder. The boosted model reaches R^2 0.751 on ladder and 0.843 on tfim and fails on xxz at -1.035, where ridge is the only model above zero at 0.541. `[F]` The xxz circuits have the largest mean n_2q of the three models, 60.7 against 37.3 for ladder and 31.0 for tfim, and 4 of the 180 xxz rows exceed the largest n_2q of the other two. `[O]` The cause of the failure on xxz is not identified.

`[F]` The physics baseline fails on A in every split. Its R^2 on the 540 A rows is -3.513 with MAE(F_H) 0.0430, against 0.785 and 0.0151 on B1. `[O]` The baseline charges the full p2 per two-qubit gate. On A, where 280 of 540 rows have full support, a fault displaces mass onto strings that already carry ideal weight and the Hellinger fidelity loses far less than p2 per gate. On B1, where the support is a few strings, nearly every fault leaves the support and the baseline is close to right.

`[F]` The dominant term in every fitted model is n_2q_offsupport. On the pooled set its OLS t statistic is 30.3, the largest in Table M2, and the next are n_qubits at 15.0 and log2_support at -13.6. Its permutation importance for the boosted model is 1.47e-3, and the second largest is n_2q at 5.95e-5, a factor 24.6 lower. In the right panel of Figure 4 its bar is the longest and its diamond is the only one away from zero. `[F]` The pooled OLS coefficients give a per-gate cost of n_2q that moves from 2.89e-4 at full support to 2.89e-4 + 6.19e-4 = 9.08e-4 at a one-string output, against the emulator value p2 = 1.29e-3.

`[O]` Verdict. What the data support across families is the physics baseline plus a support correction, not a learned model. The one quantity that transfers is the per-two-qubit-gate cost scaled by the fraction of the output space outside the ideal support. `[F]` The boosted model trained on A cuts the B1 error of the baseline by a factor 1.8 and OLS on the same features does worse than the baseline. `[O]` On these 35 rows the gain comes from the nonlinear fit and not from the feature set alone. `[F]` The gain does not survive the reverse direction. The grouped cross-validation ranks ridge above the boosted model on the B1 rows at 0.926 against 0.830 and the leave-one-model-out split on xxz ranks ridge first as well. The form these data support is y = a n_2q (1 - support_size / 2^n) + b n_2q + SPAM with two fitted parameters. The refit on emulator data will score that form beside the boosted model on held-out circuits, and the boosted model stays in the submission as the learned component only if it wins there.

### 4.6 Status and use

`[F]` All numbers in this section come from the local proxy with the published H2-2E parameters. The proxy has no shot noise, no leakage, no crosstalk and no duration-based dephasing. The emulator F_H will be measured at 1000 shots. `[O]` Shot noise adds a floor to y that none of the seven features carries, so the refit on emulator data will need either an intercept or a shot-count term, and the coefficients of Table M2 will change.

`[O]` The model has two uses in this submission. Before HQCs are spent it ranks the five pipelines of a circuit by predicted F_H from their compiled counts, so that only the pipeline the model prefers is run. The rank correlation between predicted and measured F_H across the pipelines of a circuit is the metric that matters for that use and will be reported once emulator rows exist `[PENDING: emulator]`. After the run it predicts the fidelity of any further circuit from its compiled counts and support size, which is what a user who has not yet run the circuit can supply. The support size is computed from the ideal distribution and is available for every circuit in this benchmark because the ideal outputs are stored, and it is not available for a circuit too large to simulate. A cost signal for a rewriting search is future work and is not claimed here.

<!-- CHANGELOG part3 -->

- 2026-10-07. Section 4 rewritten from the v1 protocol to a trained-and-validated section on the proxy data. Added `cost_model_metrics()` and `cost_model_coefficients()` to `report/make_tables.py`, writing `report/tables/M1_cost_metrics.md` and `report/tables/M2_cost_coefficients.md` from the two CSVs and copying `results/fig_cost_model.png` to `report/figures/`. Marker injection now also runs on `report/v2/part*.md`. Existing tables unchanged, checked by checksum.
- Numbers recomputed from `results/cost_model_metrics.csv`, `results/cost_model_coefficients.csv` and the two proxy CSVs, not copied from `results/cost_model.md`.
- Discrepancy flagged: the docstring of `model/cost_model.py` says the seeds of one class have "identical gate counts and F_H within 3e-3". Recomputed on `results/family_A_proxy_h22e.csv`: n_2q and depth_2q are identical in all 270 class-pipeline groups, n_1q differs in 70 of them, support_size differs in 5, and the maximum F_H spread within a group is 0.0056. The text above uses the recomputed values.
- Unresolved: the v1 protocol named a rank-correlation metric across pipelines of a circuit as the figure of merit for pipeline choice. `model/cost_model.py` does not compute it. Left as `[PENDING: emulator]` in 4.6.
- Unresolved: the v1 protocol named a size-extrapolation split (train n <= 6, test n = 8). Not run. The leave-one-model-out split on xxz is the only extrapolation reported.
