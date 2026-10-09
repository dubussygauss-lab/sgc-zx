# H2-2E confirmatory test on the repeats r2, r3, r4

Source: `submit/h22e_confirmatory.py` (writes `results/h22e_confirmatory.csv`). Test: `submit/test_h22e_confirmatory.py`. Payloads: `results/emulator/nexus_H2-2E_r2/`, `_r3/`, `_r4/`.

## Design

- `[F]` The original run r1 (Table E2) covered vbe_adder_3, hwb6 and grover_5 at 1000 shots per pipeline. vbe_adder_3 and grover_5 were chosen for repetition after r1 was seen. The pooled test of Table E3 (`submit/h22e_pooled.py`) includes r1.
- `[F]` The 12 repeat jobs r2, r3, r4 were submitted between 2026-10-08T21:13:30Z and 2026-10-08T21:19:25Z (`results/emulator_jobs.csv`). That is after the choice of circuits. A test on r2 to r4 alone uses no data that informed the choice.
- `[F]` The predicted gains of Section 3.7.1 ("predicted gains of 0.0170, 0.0055 and 0.0228") entered the repository in commit `eb0465f` at 2026-10-08 21:19:51 +0200 (19:19:51 UTC). That is before the first repeat was submitted. The slope model predicts P2 above P0 on both repeated circuits because P2 has fewer ZZ gates.
- `[F]` The decision to report r2 to r4 alone as the confirmatory test was taken after the pooled Table E3 result and the r2 to r4 data were known, following a judge recomputation.
- `[F]` F_H and sd follow `submit/h22e_pooled.py`. F_H is the Hellinger fidelity of the summed r2 to r4 counts to the P0ref ideal distribution. sd is binomial sqrt(F (1 - F) / N) on vbe_adder_3 (single-outcome ideal) and the sd over 4000 multinomial bootstrap resamples of the summed counts on grover_5 (seed 20261008, fresh generator per cell). dF = F_H(P2) - F_H(P0), sd of dF = hypot of the two sds, z = dF / sd. Two-sided p = erfc(|z| / sqrt 2) is primary. One-sided p for P2 > P0 = 0.5 erfc(z / sqrt 2) is secondary. Holm adjustment is over the two confirmatory circuits.

## Input and ideal output

| file | qubits | input | resets in QASM | ideal support (basis states with p > 1e-12) | ideal output |
|---|---|---|---|---|---|
| vbe_adder_3 | 10 | all-zero | 0 | 1 | 0000000000 |
| grover_5 | 9 | all-zero | 0 | 64 of 512 | uniform, each 0.015625 = 1/64 |
| hwb6 (r1 only, not repeated) | 7 | all-zero | 0 | 1 | 0000000 |

- `[F]` No source (`bench/family_B1/`) or compiled (`results/compiled/P0ref`, `P0`, `P2`) QASM of these circuits contains a reset. OpenQASM 2 starts every qubit in |0>, so the input is the all-zero basis state. The `x q[5]` at the start of the grover_5 source belongs to the circuit.
- `[F]` On the all-zero input the ideal output of vbe_adder_3 and hwb6 equals the all-zero input string. Their F_H is the probability of returning to the all-zero string.
- `[O]` grover_5 shows no amplitude amplification on this input. Its ideal output is flat over 64 states.

## Per cell (r2 + r3 + r4 summed)

| file | pipeline | runs | shots | n_2q | F_H | sd | sd method |
|---|---|---|---|---|---|---|---|
| vbe_adder_3 | P0 | r2, r3, r4 | 3000 | 56 | 0.9513 | 0.0039 | binomial |
| vbe_adder_3 | P2 | r2, r3, r4 | 3000 | 41 | 0.9640 | 0.0034 | binomial |
| grover_5 | P0 | r2, r3, r4 | 3000 | 240 | 0.8663 | 0.0062 | bootstrap |
| grover_5 | P2 | r2, r3, r4 | 3000 | 218 | 0.8667 | 0.0062 | bootstrap |

## Differences P2 - P0

| file | dN_2q | dF | sd | z | p two-sided | Holm p (2 circuits) | p one-sided (P2 > P0) | Holm one-sided | dF predicted | (dF - pred) / sd |
|---|---|---|---|---|---|---|---|---|---|---|
| vbe_adder_3 | 15 | +0.0127 | 0.0052 | +2.44 | 0.015 | 0.030 | 0.0074 | 0.015 | 0.0170 | -0.83 |
| grover_5 | 22 | +0.0004 | 0.0088 | +0.04 | 0.96 | 0.96 | 0.48 | 0.48 | 0.0228 | -2.54 |

- `[F]` Unrounded: vbe_adder_3 dF 0.012667, sd 0.005196, z 2.4377, p 0.014782, Holm 0.029565, one-sided 0.0073910. grover_5 dF 0.000393, sd 0.008826, z 0.0445, p 0.9645, one-sided 0.4822.
- `[F]` Predicted gain uses the r2 to r4 F_H(P0) and a = 1.1801e-3 per ZZ gate, as in Table E3. It differs from the Table E3 prediction (0.0229 on grover_5) because F_H(P0) differs.

## Comparison with the pooled r1 to r4 test (Table E3)

| file | test | shots per pipeline | dF | sd | z | p two-sided | Holm p (2 circuits) |
|---|---|---|---|---|---|---|---|
| vbe_adder_3 | pooled r1 to r4 | 4000 | +0.0108 | 0.0045 | +2.38 | 0.017 | 0.035 |
| vbe_adder_3 | confirmatory r2 to r4 | 3000 | +0.0127 | 0.0052 | +2.44 | 0.015 | 0.030 |
| grover_5 | pooled r1 to r4 | 4000 | +0.0007 | 0.0075 | +0.10 | 0.92 | 0.92 |
| grover_5 | confirmatory r2 to r4 | 3000 | +0.0004 | 0.0088 | +0.04 | 0.96 | 0.96 |

- `[F]` Pooled rows are copied from report/report_v5.md Table E3 and the paragraph after it. `submit/test_h22e_confirmatory.py` recomputes them from `submit/h22e_pooled.py`.
- `[O]` Dropping r1 does not change the conclusion on either circuit. On vbe_adder_3 the confirmatory two-sided p is below 0.05 before and after Holm adjustment over the two repeated circuits. On grover_5 no difference is resolved and the measured difference lies more than 2 sd below the slope prediction.
- `[O]` The confirmatory family is the two repeated circuits. hwb6 has no data outside r1 and does not enter it.
