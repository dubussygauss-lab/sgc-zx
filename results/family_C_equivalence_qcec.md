# Family C: MQT QCEC check of the unproven PSEL4 outputs and of L3

Written by `python3 pipelines/equiv_qcec_C.py --summary` from `results/family_C_equivalence_qcec.csv`, with PSEL4 picks and PyZX verdicts taken from `equiv_psel4_C.summary_facts()` (`results/family_C_equivalence_psel4.csv` and `results/family_C_equivalence.csv`). Method and configuration in the docstring of `pipelines/equiv_qcec_C.py`.

## Method

- [F] Tool: mqt.qcec 3.10.2, `qcec.verify` on qelib1 QASM written by `equiv_family_C.qelib_qasm` (float angles as stored, no snapping, output permutation from the measurement map realised by swaps). No qubit is declared ancilla or garbage. A positive verdict is equality of the full 2^n x 2^n unitaries up to global phase.
- [F] Two configurations per pair, each alone: `run_zx_checker=True` and `run_alternating_checker=True`, with `parallel=False`, `nthreads=1`, `timeout=600` for the three targets. QCEC defaults kept: `numerical_tolerance` 2.27e-13, `trace_threshold` 1e-8, `check_approximate_equivalence=False`.
- [F] Only the QCEC verdicts `equivalent` and `equivalent_up_to_global_phase` count as proven. The alternating checker is a floating-point decision-diagram computation, so its positive verdict holds within the tolerances above. This matters for hrs_mult_5, whose compiled angles lie off the dyadic grid.

## PSEL4 outputs

- [F] Proven earlier by the PyZX miter: 17 of 20.
- [F] Of the three unproven targets, QCEC proved 0: none.
- [F] PSEL4 output proven equal to its input (PyZX or QCEC): 17 of 20.
- [F] Still not proven: hrs_mult_5, rgqft_mult_6, draper_adder_28.

### Target checks

| circuit | n | candidate | method | config | QCEC verdict | verdict | time (s) | notes |
|---|---|---|---|---|---|---|---|---|
| rgqft_mult_6 | 24 | L3 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 602.16 | qcec check time 600.2 s (no_information: timeout or checker gave up) |
| hrs_mult_5 | 21 | P2 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 |  | killed | 630.15 | process killed after 630 s |
| hrs_mult_5 | 21 | P2 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 6.18 | qcec check time 3.9 s |
| rgqft_mult_6 | 24 | L3 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 4.99 | qcec check time 3.6 s |
| draper_adder_28 | 56 | P2L3 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 2.63 | qcec check time 1.2 s |
| draper_adder_28 | 56 | P2L3 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=600, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 609.43 | qcec check time 607.9 s (no_information: timeout or checker gave up) |

## L3 outputs (all family C circuits)

- [F] Circuits with an L3 QCEC row: 7 of 20.
- [F] L3 proven by QCEC: 0. QCEC `not_equivalent`: 0.
- [F] L3 sweep timeout: 60 s per checker. The L3 output of rgqft_mult_6 is in the target table (600 s). The other circuits without an L3 row were not reached in the time budget and no L3 output was recompiled.
- [F] QCEC returned no counterexample (`not_equivalent`) on any pair. `probably_not_equivalent` from the ZX checker and `no_information` from the alternating checker are inconclusive.

| circuit | n | method | config | QCEC verdict | verdict | time (s) | notes |
|---|---|---|---|---|---|---|---|
| cdkm_adder_10 | 22 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 61.47 | qcec check time 61.3 s (no_information: timeout or checker gave up) |
| cdkm_adder_10 | 22 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.23 | qcec check time 0.1 s |
| vbe_adder_7 | 22 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 84.36 | qcec check time 84.2 s (no_information: timeout or checker gave up) |
| vbe_adder_7 | 22 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.25 | qcec check time 0.0 s |
| cdkm_adder_15 | 32 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 66.78 | qcec check time 66.5 s (no_information: timeout or checker gave up) |
| cdkm_adder_15 | 32 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.37 | qcec check time 0.1 s |
| vbe_adder_11 | 34 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 |  | killed | 90.12 | process killed after 90 s |
| vbe_adder_11 | 34 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.32 | qcec check time 0.1 s |
| cdkm_adder_20 | 42 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 |  | killed | 90.11 | process killed after 90 s |
| cdkm_adder_20 | 42 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.56 | qcec check time 0.2 s |
| vbe_adder_18 | 55 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 |  | killed | 90.14 | process killed after 90 s |
| vbe_adder_18 | 55 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 0.68 | qcec check time 0.1 s |
| cdkm_adder_27 | 56 | qcec_alt | run_alternating_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | no_information | not proven | 69.46 | qcec check time 68.7 s (no_information: timeout or checker gave up) |
| cdkm_adder_27 | 56 | qcec_zx | run_zx_checker=True, other checkers False, parallel=False, nthreads=1, timeout=60, numerical_tolerance=default 2.27e-13, trace_threshold=default 1e-8 | probably_not_equivalent | not proven | 1.21 | qcec check time 0.5 s |
