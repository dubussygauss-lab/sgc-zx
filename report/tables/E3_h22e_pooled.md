`[F]` Nexus H2-2E, noisy_simulation = True, 1000 shots per run, one job per run. runs counts the original run of Table E2 and the completed repeats. pooled F_H is the Hellinger fidelity of the summed counts to the ideal distribution. sd is binomial on vbe_adder_3 and the sd over 4000 multinomial bootstrap resamples of the pooled counts on grover_5 (seed 20261008). The per-run F_H range is the smallest and largest F_H of single runs.

| file | pipeline | runs | shots | n_2q | pooled F_H | sd | per-run F_H range |
|---|---|---|---|---|---|---|---|
| vbe_adder_3 | P0 | 4 | 4000 | 56 | 0.9520 | 0.0034 | 0.9470 to 0.9560 |
| vbe_adder_3 | P2 | 4 | 4000 | 41 | 0.9628 | 0.0030 | 0.9590 to 0.9680 |
| grover_5 | P0 | 4 | 4000 | 240 | 0.8704 | 0.0053 | 0.8482 to 0.8652 |
| grover_5 | P2 | 4 | 4000 | 218 | 0.8711 | 0.0053 | 0.8400 to 0.8728 |

`[F]` vbe_adder_3 F_H(P2) - F_H(P0) +0.0108, sd 0.0045, z +2.38, p 0.017, predicted 0.0170, measured - predicted -1.38 sd. grover_5 F_H(P2) - F_H(P0) +0.0007, sd 0.0075, z +0.10, p 0.92, predicted 0.0229, measured - predicted -2.94 sd. Homogeneity p: vbe_adder_3 P0 0.80, vbe_adder_3 P2 0.70, grover_5 P0 0.91, grover_5 P2 0.68. H2-2E HQC estimate of the 18 completed jobs 5933.2, 59.3 % of 10000.
