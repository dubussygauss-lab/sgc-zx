# Pre-registration: H2-2E run of cdkm_adder_10 and modadd_2n_10 on three non-zero inputs each

Written and committed alone before any job of this run was submitted. The commit time of this file is the
pre-registration time. Nothing below is changed after the jobs run.

## Circuits and pipelines

| Circuit | Qubits | Register layout (index 0 = least significant bit) | Pipelines |
|---|---|---|---|
| `bench/family_C/cdkm_adder_10.qasm` | 22 | `q[0]` = cin, `q[1..10]` = a, `q[11..20]` = b, `q[21]` = cout | P0, L3 |
| `bench/family_C/modadd_2n_10.qasm` | 20 | `q[0..9]` = a, `q[10..19]` = b | P0, P2L3 |

- cdkm_adder_10: qiskit `CDKMRippleCarryAdder(10, kind='full')` (registers cin, a, b, cout), transpiled at optimization_level 0
  to {CX, H, T, Tdg} on one register `q[22]` (`bench/build_family_C.py`). Maps b to (a + b) mod 2^10, writes the carry into cout,
  leaves a and cin unchanged.
- modadd_2n_10: qiskit `ModularAdderGate(10).definition` (registers a, b), same build. Maps b to (a + b) mod 2^10, leaves a
  unchanged. It has no ancilla and no carry. Every pair of 10-bit values is a valid input, so the only constraint is the register
  width.
- P0: pytket-quantinuum default compilation pass at optimisation level 2 (`pipelines/compile.py compile_pipeline("P0", ...)`).
- PSEL4 picks from `value/psel4_ledger.csv`: **L3** for cdkm_adder_10 (`pick_PSEL4 = L3`) and **P2L3** for modadd_2n_10
  (`pick_PSEL4 = P2L3`), compiled with `pipelines/pass_select.py compile_candidate(<pick>, ...)`. The pick is fixed from the
  ledger (made on the circuit as written). It is not re-selected on the input-prepared circuits.
- Each pipeline compiles the input-prepared circuit (X gates included). Measure-all is appended with `compile.add_measure_all`,
  which carries the implicit qubit permutation of L3 / P2L3 in the measurement map (measure q[j] -> c[i]), and the result is
  written as hqslib1 QASM to `results/compiled/<pipeline>/<file>`. Outputs are read on the classical bits c[i], so the expected
  bitstring is the same for every pipeline.

## Inputs (drawn before this file was written)

```
rng = numpy.random.default_rng(20261011)
cdkm   = rng.integers(1, 2**10, size=(3, 2))   # rows (a, b), first draw
modadd = rng.integers(1, 2**10, size=(3, 2))   # rows (a, b), second draw from the same generator
```

Uniform on 1..1023 for each of a and b (non-zero values of the 10-bit registers). cin = 0 for cdkm_adder_10, as in the earlier
non-zero-input run. Input preparation: X on the qubits holding the 1-bits of a and b, placed after `qreg` in front of the circuit
as written. Stored as `bench/family_C_multi/<circuit>_i<k>.qasm`, k = 1, 2, 3 in draw order.

## Expected outputs

Bitstring convention of `submit/common.py` (`counts_to_probs`): character i is classical bit c[i], which holds qubit q[i] after
measure-all.

| File | a | b | a + b | Sum register | Carry | Expected output (c[0] first) |
|---|---|---|---|---|---|---|
| `cdkm_adder_10_i1.qasm` | 692 | 435 | 1127 | 103 | 1 | `0001011010111100110001` |
| `cdkm_adder_10_i2.qasm` | 502 | 24 | 526 | 526 | 0 | `0011011111001110000010` |
| `cdkm_adder_10_i3.qasm` | 710 | 328 | 1038 | 14 | 1 | `0011000110101110000001` |
| `modadd_2n_10_i1.qasm` | 396 | 743 | 1139 | 115 | - | `00110001101100111000` |
| `modadd_2n_10_i2.qasm` | 460 | 452 | 912 | 912 | - | `00110011100000100111` |
| `modadd_2n_10_i3.qasm` | 335 | 130 | 465 | 465 | - | `11110010101000101110` |

- Arithmetic: a unchanged, b <- (a + b) mod 1024, cout = floor((a + b) / 1024) for cdkm, cin = 0
  (`submit/h22e_multi_run.py expected_bits`).
- Independent check: statevector simulation of each input-prepared file with `bench/sv.py` (numpy) gives a single basis state
  with probability 1 equal to the string above (`submit/h22e_multi_run.py --prepare`).
- Before submission each compiled circuit must be in the H2 native gate set, carry one Measure per qubit, and its ideal output
  (statevector of the compiled measured QASM, read on c[i]) must be the single expected bitstring.

## Execution

- Platform nexus:H2-2E only, through aqora, team org as in the earlier H2-2E runs, `noisy_simulation: true`, 400 shots per
  (circuit, input, pipeline). One job per program, 12 jobs. Run tag `famC_multi`
  (directory `results/emulator/nexus_H2-2E_famC_multi/`, CSV `results/emulator_nexus_H2-2E_famC_multi.csv`).
- Budget: HQC = 5 + C (N_1q + 10 N_2q + 5 N_SPAM) / 5000 per program, C = 400, N_SPAM = qubits + measurements, computed from
  each compiled circuit before submission. The 12 programs must total under 1900 HQC, or nothing is submitted.
- No resubmission. Every job is recorded in `results/emulator_jobs.csv`. A job that has not returned is fetched by id with
  `submit/fetch_job.py`, never resubmitted. A job that fails is reported as failed and its program is left out of the analysis.

## Analysis (fixed in advance)

For each program, success k = count of the expected bitstring, N = 400, p = k / N. For a single-outcome ideal distribution the
Hellinger fidelity to the ideal output equals p.

- **Primary metric, one per circuit**: success probability pooled over the 3 inputs, p_pick = sum k / 1200 and p_P0 = sum k / 1200,
  difference d = p_pick - p_P0, binomial sd = sqrt(p_pick (1 - p_pick) / 1200 + p_P0 (1 - p_P0) / 1200), z = d / sd.
  Reported for cdkm_adder_10 (L3 minus P0) and modadd_2n_10 (P2L3 minus P0). No other test is primary.
- Secondary: per-input p with binomial sd sqrt(p (1 - p) / 400) for each pipeline, and the per-input d, sd, z; the pooled
  difference over both circuits (PSEL4 pick minus P0, 2400 shots per arm, same formula).
- Also reported: n_2q (ZZPhase + ZZMax) and HQC estimate of each compiled circuit, the HQC of each job and of the run, and the
  H2-2E grand total over all stored payloads with valid counts.
- Analysis script: `submit/h22e_multi.py` (offline, from the stored payloads), output `results/h22e_multi.md`.
