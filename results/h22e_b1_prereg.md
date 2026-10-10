# Pre-registration: H2-2E run of vbe_adder_3 and hwb6 on non-zero inputs (P0 vs the PSEL4 pick)

Written and committed alone before any job of this run was submitted. The commit time of this file is the
pre-registration time. Nothing below is changed after the jobs run. The result is reported whatever it is.

## Circuits and pipelines

| Circuit | Qubits | Register layout | Inputs | Pipelines |
|---|---|---|---|---|
| `bench/family_B1/vbe_adder_3.qasm` | 10 | `q[0]` = cin, `q[1+3i]` = a_i, `q[2+3i]` = b_i (i = 0, 1, 2), `q[3]`, `q[6]` = carry ancillas, `q[9]` = cout | 4 | P0, L3 |
| `bench/family_B1/hwb6.qasm` | 7 | reversible function on `q[0..6]`, bit i of the input x on `q[i]` | 3 | P0, P2L3 |

- vbe_adder_3: pyzx benchmark circuit (3-bit VBE ripple-carry adder, {CX, H, T, Tdg}). The register layout was identified
  by simulating the circuit as written on all 64 inputs with a = 0..7 on `q[1], q[4], q[7]`, b = 0..7 on `q[2], q[5], q[8]`
  and all other qubits 0 (`bench/sv.py`): the output has a unchanged, b_i <- bit i of (a + b) mod 8, `q[9]` = carry
  floor((a + b) / 8), and `q[0]`, `q[3]`, `q[6]` back to 0 in every case. cin and the carry ancillas are kept 0.
- hwb6: pyzx benchmark circuit (hidden weighted bit function on 6 bits plus one ancilla, {CX, H, T, Tdg, X}). It is a
  permutation of the computational basis, so each basis input gives one basis output. The expected output is the
  statevector of the input-prepared circuit as written (`bench/sv.py`), required to be a single basis state.
- P0: pytket-quantinuum default compilation pass at optimisation level 2 (`pipelines/compile.py compile_pipeline("P0", ...)`).
- PSEL4 picks from `value/psel4_ledger.csv`: **L3** for vbe_adder_3 (`pick_PSEL4 = L3`, ledger HQC at 1000 shots P0 151.6,
  L3 100.0) and **P2L3** for hwb6 (`pick_PSEL4 = P2L3`, ledger HQC P0 243.0, P2L3 208.8), compiled with
  `pipelines/pass_select.py compile_candidate(<pick>, ...)`. The pick is fixed from the ledger (made on the circuit as
  written). It is not re-selected on the input-prepared circuits.
- Each pipeline compiles the input-prepared circuit (X gates included). Measure-all is appended with `compile.add_measure_all`,
  which carries the implicit qubit permutation of L3 / P2L3 in the measurement map (measure q[j] -> c[i]), and the result is
  written as hqslib1 QASM to `results/compiled/<pipeline>/<file>`. Outputs are read on the classical bits c[i], so the expected
  bitstring is the same for every pipeline.

## Inputs (drawn before this file was written)

```
rng = numpy.random.default_rng(20261012)
vbe  = rng.integers(1, 8, size=(4, 2))     # rows (a, b), first draw
hwb6 = rng.integers(1, 128, size=3)        # x, second draw from the same generator
```

Uniform on 1..7 for each of a and b (non-zero values of the 3-bit registers), uniform on 1..127 for x (non-zero 7-bit
inputs). Input preparation: X on the qubits holding the 1-bits of the input, placed after `qreg` in front of the circuit as
written. Stored as `bench/family_B1_multi/<circuit>_i<k>.qasm`, k in draw order (`submit/h22e_b1_run.py --prepare`).

## Expected outputs

Bitstring convention of `submit/common.py` (`counts_to_probs`): character i is classical bit c[i], which holds qubit q[i] after
measure-all.

| File | a | b | a + b | Sum register | Carry | Expected output (c[0] first) |
|---|---|---|---|---|---|---|
| `vbe_adder_3_i1.qasm` | 4 | 5 | 9 | 1 | 1 | `0010000101` |
| `vbe_adder_3_i2.qasm` | 6 | 3 | 9 | 1 | 1 | `0010100101` |
| `vbe_adder_3_i3.qasm` | 3 | 7 | 10 | 2 | 1 | `0100110001` |
| `vbe_adder_3_i4.qasm` | 7 | 5 | 12 | 4 | 1 | `0100100111` |

| File | x | Input bits (q[0] first) | Expected output (c[0] first) |
|---|---|---|---|
| `hwb6_i1.qasm` | 126 | `0111111` | `1001011` |
| `hwb6_i2.qasm` | 78 | `0111001` | `0111111` |
| `hwb6_i3.qasm` | 40 | `0001010` | `0100010` |

- vbe_adder_3 arithmetic: a unchanged, b <- (a + b) mod 8, cout = floor((a + b) / 8), cin and the carry ancillas 0
  (`submit/h22e_b1_run.py expected_bits`). Independent check: statevector simulation of each input-prepared file with
  `bench/sv.py` gives a single basis state with probability 1 equal to the string above (`--prepare`).
- hwb6: the string is the single basis state of the `bench/sv.py` simulation of the input-prepared file (probability 1).
- Before submission each compiled circuit must be in the H2 native gate set, carry one Measure per qubit, and its ideal output
  (statevector of the compiled measured QASM, read on c[i]) must be the single expected bitstring. Checked for all 14
  programs (`--check`), sha256 of each file recorded in `results/compiled/h22e_b1_checked.json`.

## Compiled programs and budget (computed before submission)

| File | Pipeline | n_2q | n_1q | HQC (400 shots) |
|---|---|---|---|---|
| `vbe_adder_3_i1.qasm` | P0 | 56 | 76 | 63.88 |
| `vbe_adder_3_i1.qasm` | L3 | 33 | 46 | 43.08 |
| `vbe_adder_3_i2.qasm` | P0 | 56 | 77 | 63.96 |
| `vbe_adder_3_i2.qasm` | L3 | 33 | 47 | 43.16 |
| `vbe_adder_3_i3.qasm` | P0 | 56 | 78 | 64.04 |
| `vbe_adder_3_i3.qasm` | L3 | 33 | 47 | 43.16 |
| `vbe_adder_3_i4.qasm` | P0 | 56 | 78 | 64.04 |
| `vbe_adder_3_i4.qasm` | L3 | 33 | 46 | 43.08 |
| `hwb6_i1.qasm` | P0 | 99 | 133 | 100.44 |
| `hwb6_i1.qasm` | P2L3 | 83 | 116 | 86.28 |
| `hwb6_i2.qasm` | P0 | 99 | 131 | 100.28 |
| `hwb6_i2.qasm` | P2L3 | 83 | 116 | 86.28 |
| `hwb6_i3.qasm` | P0 | 99 | 131 | 100.28 |
| `hwb6_i3.qasm` | P2L3 | 83 | 117 | 86.36 |

Total 988.32 HQC over 14 programs. Remaining H2-2E quota by the same formula before this run: 10000 - 8983.44 = 1016.56
(sum of `hqc_estimate` over the 34 stored H2-2E payloads with valid counts).

## Execution

- Platform nexus:H2-2E only, through aqora, team org as in the earlier H2-2E runs, `noisy_simulation: true`, 400 shots per
  (circuit, input, pipeline). One job per program, 14 jobs. Run tag `famB1_multi`
  (directory `results/emulator/nexus_H2-2E_famB1_multi/`, CSV `results/emulator_nexus_H2-2E_famB1_multi.csv`), ledger
  family B1.
- Submission order: input by input with both arms of one input adjacent, vbe_adder_3 i1 P0, i1 L3, hwb6 i1 P0, i1 P2L3,
  vbe_adder_3 i2 P0, i2 L3, hwb6 i2 ..., vbe_adder_3 i3 ..., hwb6 i3 ..., vbe_adder_3 i4 P0, i4 L3 last.
- Budget: HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000 per program, C = 400, N_SPAM = qubits + measurements, computed from
  each compiled circuit before submission. The 14 programs must total at most 990 HQC, or nothing is submitted.
- No resubmission. Every job is recorded in `results/emulator_jobs.csv`. A job that has not returned is fetched by id with
  `submit/fetch_job.py`, never resubmitted. A job that fails is reported as failed and its program is left out of the analysis.

## Analysis (fixed in advance)

For each program, success k = count of the expected bitstring, N = 400, p = k / N. For a single-outcome ideal distribution the
Hellinger fidelity to the ideal output equals p.

- **Primary test, one per circuit**: success probability pooled over the inputs of the circuit (S = 1600 shots per arm for
  vbe_adder_3, S = 1200 for hwb6), p_pick = K_pick / S and p_P0 = K_P0 / S, d = p_pick - p_P0, pooled two-proportion
  statistic z = d / sqrt(pp (1 - pp) (2 / S)) with pp = (K_pick + K_P0) / (2 S), two-sided p = 2 (1 - Phi(|z|)), alpha = 0.05,
  Holm step-down over the two circuits (smaller p compared with 0.025, the other with 0.05). Reported for vbe_adder_3
  (L3 minus P0) and hwb6 (P2L3 minus P0). No other test is primary. A non-rejection is reported as such, not as evidence of
  equality.
- Secondary: HQC per correct output, R = (H_pick / K_pick) / (H_P0 / K_P0) with H = sum of the HQC estimates of the arm, and
  its 95 % interval by the delta method on log R with var(log p) = (1 - p) / (S p) per arm, H held fixed (the method of
  `value/hqc_per_correct.py`). Per-input p with binomial sd sqrt(p (1 - p) / 400) for each pipeline, the per-input d with
  Wald sd and z, and the pooled difference over both circuits (PSEL4 pick minus P0, 2800 shots per arm, Wald sd).
- Also reported: n_2q and HQC estimate of each compiled circuit, the HQC of each job and of the run, and the H2-2E grand total
  over all stored payloads with valid counts.
- Analysis script: `submit/h22e_b1.py` (offline, from the stored payloads), output `results/h22e_b1.md`. The two pairs are
  appended as rows 7 and 8 of `value/hqc_per_correct.py`, whose headline counts run over all pairs and, separately, over the
  pairs whose alternative is the PSEL4 pick.
