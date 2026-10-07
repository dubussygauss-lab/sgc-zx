### 4.7 Refit on Selene depolarising data

[F] The cost model of Sections 4.1 to 4.3 was refitted without code changes on the Selene depolarising runs of Section 3.6. [F] The Selene layer has 432 family A rows with n = 4, 6, 8 and 10 and 36 B1 rows from 12 circuits. [F] The proxy fit used 540 A rows with n up to 8 and 35 B1 rows from 7 circuits. [F] The target is the depolarised sampled F_H divided by the noiseless sampled F_H at the same seed. [F] On the 345 rows with a proxy value this ratio differs from the exact proxy F_H by 0.0022 in mean absolute value, and the raw sampled F_H differs by 0.0058. [O] The ratio is the closest available match to the exact fidelity that the proxy fit used.

[F] Under circuit-grouped cross-validation the refit matches the proxy fit, with pooled R^2 = 0.935 for OLS and 0.974 for GBR. [F] Training on A and testing on B1 gives R^2 = 0.859 for ridge and 0.848 for GBR. [F] The unfitted physics baseline drops on B1 from R^2 = 0.785 on the proxy to 0.216 on Selene. [F] Training on B1 and testing on A still fails, with R^2 = 0.327 for GBR and negative R^2 for all other models. [F] The largest OLS terms on A remain n_qubits, log2_support and n_2q_offsupport with t = 14.7, -14.9 and 15.9. [O] The Selene layer confirms the two proxy conclusions. Transfer runs from A to B1 only, and within a family the fitted models interpolate.

| model | split | R^2 proxy | R^2 Selene | MAE(F_H) proxy | MAE(F_H) Selene |
|---|---|---|---|---|---|
| physics | A to B1 | 0.785 | 0.216 | 0.0151 | 0.0201 |
| ols | A to B1 | 0.560 | 0.356 | 0.0252 | 0.0333 |
| ridge | A to B1 | 0.840 | 0.859 | 0.0150 | 0.0154 |
| gbr | A to B1 | 0.805 | 0.848 | 0.0083 | 0.0140 |
| physics | B1 to A | -3.513 | -3.760 | 0.0430 | 0.0464 |
| ols | B1 to A | -261.894 | -313.944 | 0.1971 | 0.6838 |
| ridge | B1 to A | -0.605 | -98.831 | 0.0259 | 0.2673 |
| gbr | B1 to A | 0.326 | 0.327 | 0.0184 | 0.0234 |
| physics | cv5g pooled | -2.739 | -2.773 | 0.0413 | 0.0444 |
| ols | cv5g pooled | 0.938 | 0.935 | 0.0051 | 0.0065 |
| ridge | cv5g pooled | 0.938 | 0.936 | 0.0052 | 0.0065 |
| gbr | cv5g pooled | 0.971 | 0.974 | 0.0017 | 0.0035 |

[F] Test rows: A to B1 35 proxy and 36 Selene, B1 to A 540 and 432, cv5g pooled 575 and 468. Source: `results/cost_model_selene.md`.
