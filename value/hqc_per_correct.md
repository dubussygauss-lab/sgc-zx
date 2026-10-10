# HQC per correct output on the H2-2E emulator

`[F]` Source: every H2-2E payload under `results/emulator/nexus_H2-2E*/` (34 payloads, 26 used). Script: `value/hqc_per_correct.py`. HQC is the formula estimate `hqc_estimate` stored with each job, not a billed amount. All runs are on the H2-2E emulator, not hardware.

`[F]` Success probability p = count of the ideal bitstring / shots. The ideal bitstring comes from the repository code (`common.reference_probs`, `h22e_famC_nz.expected_bits`, `h22e_multi_run.expected_bits`). On every used payload p equals the stored F_H (max |p - F_H| = 9.0e-15).

`[F]` Pooled per circuit and pipeline over repeats or inputs. Cost per correct output C = sum HQC / sum correct. R = C_alt / C_P0. The interval is the delta method on log R. The bootstrap column is a parametric bootstrap (10,000 resamples, seed 20261010). z is the pooled two-proportion statistic of p_alt - p_P0.

| Circuit | Runs | Alt | Shots per arm | p_P0 | p_alt | z | HQC per 1000 correct, P0 | HQC per 1000 correct, alt | R | 95 % interval (delta) | 95 % interval (bootstrap) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| vbe_adder_3 | H2-2E+H2-2E_r2+H2-2E_r3+H2-2E_r4 | P2 | 4000 | 0.9520 | 0.9627 | +2.38 | 159.2 | 123.6 | 0.7762 | [0.7690, 0.7834] | [0.7689, 0.7835] |
| hwb6 | H2-2E | P2 | 1000 | 0.9240 | 0.9090 | -1.21 | 263.0 | 255.9 | 0.9730 | [0.9476, 0.9991] | [0.9488, 0.9992] |
| vbe_adder_7 | H2-2E_famC | P2 | 1000 | 0.8860 | 0.8970 | +0.79 | 418.1 | 328.2 | 0.7851 | [0.7614, 0.8095] | [0.7612, 0.8093] |
| vbe_adder_7_nz | H2-2E_famC_nz | L3 | 1000 | 0.8830 | 0.9010 | +1.30 | 421.5 | 257.7 | 0.6114 | [0.5930, 0.6303] | [0.5930, 0.6302] |
| cdkm_adder_10 | H2-2E_famC_multi | L3 | 1200 | 0.8692 | 0.8267 | -2.90 | 437.5 | 402.6 | 0.9203 | [0.8896, 0.9521] | [0.8892, 0.9522] |
| modadd_2n_10 | H2-2E_famC_multi | P2L3 | 1200 | 0.8417 | 0.8383 | -0.22 | 470.1 | 447.8 | 0.9526 | [0.9199, 0.9864] | [0.9199, 0.9857] |

## Headline

- `[F]` The alternative costs fewer HQC per correct output than P0 (R < 1) in 6 of 6 pairs.
- `[F]` The upper 95 % bound of R is below 1 in 6 of 6 pairs by the delta method and in 6 of 6 by the bootstrap.
- `[F]` cdkm_adder_10 (L3, three inputs pooled): R = 0.9203, delta interval [0.8896, 0.9521].
- `[F]` In percent: cdkm_adder_10 needs 8.0 % fewer HQC per correct output than P0 (95 % interval 4.8 to 11.0 %).
- `[F]` Pooled over the 6 pairs: R = (2085.12 / 8556) / (2523.12 / 8554) = 0.8262, bootstrap interval [0.8189, 0.8335].
- `[F]` In percent: pooled over the 6 pairs the alternative needs 17.4 % fewer HQC per correct output (bootstrap 95 % interval 16.7 to 18.1 %).
- `[F]` grover_5 is excluded. Its ideal distribution (`common.reference_probs`) has 64 outcomes with largest probability 0.015625, so it has no unique marked item. Its HQC ratio alt / P0 over 4 runs is 0.9339.
- `[O]` Pooling the three inputs of cdkm_adder_10 and modadd_2n_10 treats them as one binomial. The intervals ignore variation between inputs and between emulator runs.
