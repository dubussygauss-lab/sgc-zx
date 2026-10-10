# Pre-registration: H2-2E run of vbe_adder_7 on one non-zero input

Written and committed before any job of this run was submitted. The commit time of this file is the
pre-registration time. Nothing below is changed after the jobs run.

## Circuit and input

- Circuit: `bench/family_C/vbe_adder_7.qasm` as written (22 qubits, qiskit `VBERippleCarryAdder(7, kind='full')`,
  transpiled at optimization_level 0 to {CX, H, T, Tdg}, one register `q[22]`, see `bench/build_family_C.py`).
- Register layout (qiskit register order of `VBERippleCarryAdder(7, kind='full')`, index 0 = least significant bit):
  `q[0]` = cin, `q[1..7]` = a (a_0 .. a_6), `q[8..14]` = b (b_0 .. b_6), `q[15]` = cout, `q[16..21]` = helper (6 ancillas).
  The adder maps b to (a + b) mod 2^7, writes the carry into cout, and leaves a, cin and the helpers unchanged.
- Draw: `rng = numpy.random.default_rng(20261010); a, b = rng.integers(1, 2**7, size=2)`, uniform on 1..127 (non-zero values of
  the 7-bit register). Result: **a = 28, b = 111**. cin = 0.
- Input preparation: X on the qubits holding the 1-bits of a and b, placed in front of the circuit as written:
  X on q[3], q[4], q[5] (a = 28 = 0b0011100) and on q[8], q[9], q[10], q[11], q[13], q[14] (b = 111 = 0b1101111).
  Stored as `bench/family_C_nz/vbe_adder_7_nz.qasm` (the bench file with these nine `x` lines after `qreg`).
- a + b = 139 = 0b10001011: sum register (b) = 139 mod 128 = 11, cout = 1.

## Expected output

Bitstring in the convention of `submit/common.py` (`counts_to_probs`): character i is classical bit c[i], which holds qubit q[i]
after measure-all.

**Expected output: `0001110011010001000000`**
(q[0] cin = 0 | q[1..7] a = 0011100 | q[8..14] sum = 1101000 | q[15] cout = 1 | q[16..21] helpers = 000000)

- Statevector simulation of `bench/family_C_nz/vbe_adder_7_nz.qasm` with `bench/sv.py` (numpy, 22 qubits): a single basis
  state with probability 1.0, index string `0001110011010001000000`.
- Arithmetic cross-check (a, unchanged; b <- (a + b) mod 128; cout = carry; cin and helpers 0) gives the same string.

## Pipelines (one job each)

- **P0**: pytket-quantinuum default compilation pass at optimisation level 2, `pipelines/compile.py compile_pipeline("P0", ...)`,
  as in `submit/common.py` and the earlier family C run (`results/emulator/nexus_H2-2E_famC/P0`).
- **L3**: official pass at optimisation level 3, `QuantinuumBackend("H2-1", QuantinuumAPIOffline()).get_compiled_circuit(circ,
  optimisation_level=3)`, `pipelines/pass_select.py compile_candidate("L3", ...)` (same as `pipelines/strong_baselines.py
  compile_variant("L3", ...)`). L3 is the PSEL4 pick for vbe_adder_7 (`value/psel4_ledger.csv`).
- Both compile the input-prepared circuit (X gates included). Measure-all is appended with `compile.add_measure_all`, written as
  hqslib1 QASM, as in `results/compiled/<pipeline>/`. Before submission each compiled circuit must be in the H2 native gate set and
  its ideal output (22-qubit statevector of the compiled measured QASM) must be the single expected bitstring.

## Execution

- Platform nexus:H2-2E through aqora, team org as in the earlier H2-2E runs, `noisy_simulation: true`, 1000 shots per job,
  exactly two jobs (one per pipeline). Run tag `famC_nz` (directory `results/emulator/nexus_H2-2E_famC_nz/`).
- Budget: HQC estimates of the two jobs must total under 700. No resubmission. A job that does not return within the runner's
  wait is fetched with `submit/fetch_job.py`, never resubmitted.

## Analysis (fixed in advance)

- Primary metric, per pipeline: success probability p = (count of `0001110011010001000000`) / N, N = 1000, binomial
  sd = sqrt(p (1 - p) / N). For this single-outcome ideal distribution the Hellinger fidelity to the ideal output equals p.
- Secondary: d = p(L3) - p(P0), sd = sqrt(sd_L3^2 + sd_P0^2), z = d / sd.
- Also reported: n_2q (ZZPhase + ZZMax) and HQC estimate of each compiled circuit, and the H2-2E grand total over all stored
  payloads with valid counts.
- Analysis script: `submit/h22e_famC_nz.py` (offline, from the stored payloads), output `results/h22e_famC_nz.md`.
