# Family C: full equivalence check by ZX miter

Written by `python3 pipelines/equiv_family_C.py --summary` from `results/family_C_equivalence.csv`, `value/family_C_selector.csv` (column `pick`) and `bench/family_C/manifest.csv` (column `continuous_angles`). Script: `pipelines/equiv_family_C.py` (method in its docstring). Tests: `pipelines/test_equiv_family_C.py` (one positive and one broken case).

## Method

- [F] Each compiled output (`results/compiled/{P0,P2}/<file>`) is compared with the input `bench/family_C/<file>`, and P2 with P0, as full 2^n x 2^n unitaries up to global phase. Measurements are stripped and pytket's implicit qubit permutation is read from the measurement map. No ancilla is fixed to |0>, so a proof here is stronger than equality on clean-ancilla inputs.
- [F] PyZX 0.10.7: miter `G_A ; adjoint(G_B)`, `full_reduce`, then the test of `Circuit.verify_equality` (2n boundary vertices only, simple edges, input i wired to output i). Angles are snapped to the dyadic grid 2^-G with G = (input's largest dyadic exponent) + 4. The input angles lie on that grid exactly. The largest snap on the compiled side is 5.27e-12 half-turns over all 54 proven PyZX rows (float noise). A positive result proves equivalence of the snapped circuits. A negative result is inconclusive.
- [F] MQT QCEC 3.10.2 was run as a second method on cdkm_adder_10 and draper_adder_10 only (see table). Its ZX checker returned `probably_not_equivalent` on 5 of 6 pairs that PyZX proves. This is QCEC's "could not reduce" outcome and not a counterexample. The alternating DD checker is a floating-point check with tolerance.

## Results (PyZX miter)

- [F] P0 vs input: 18 of 20 proven.
- [F] P2 vs input: 18 of 20 proven.
- [F] P2 vs P0: 18 of 20 proven.
- [F] hrs_mult_5 (P0, P2): inconclusive, not run by PyZX. FullPeepholeOptimise's KAK resynthesis leaves angles off any dyadic grid, and PyZX needs exact phases. The 64-input basis check (pass) remains the only check for this circuit.
- [F] draper_adder_28 (P0, P2): timeout (300 s) in `full_reduce`. P2 vs P0 not run. The 64-input basis check does not cover it either (branching ancilla). It is unchecked.

## PSEL picks

- [F] PSEL output proven equal to its input: 18 of 20 circuits.
- [F] P2 picks proven: 13 of 14. Not proven: hrs_mult_5.
- [F] P0 picks proven: 5 of 6. Not proven: draper_adder_28.
- [F] Circuits without continuous angles: PSEL output proven for 15 of 15.

## Verdict table

| circuit | n | PSEL pick | P0 vs input | P2 vs input | P2 vs P0 | QCEC (second method) |
|---|---|---|---|---|---|---|
| draper_adder_10 | 20 | P0 | proven | proven | proven | P0/qcec_zx: inconclusive; P2/qcec_zx: inconclusive; P2vsP0/qcec_zx: inconclusive; P0/qcec_alt: proven; P2/qcec_alt: proven; P2vsP0/qcec_alt: timeout |
| modadd_2n_10 | 20 | P2 | proven | proven | proven | not run |
| hrs_mult_5 | 21 | P2 | inconclusive | inconclusive | inconclusive | not run |
| mcx_clean_11 | 21 | P0 | proven | proven | proven | not run |
| cdkm_adder_10 | 22 | P2 | proven | proven | proven | P0/qcec_zx: inconclusive; P2/qcec_zx: proven; P2vsP0/qcec_zx: inconclusive; P0/qcec_alt: proven; P2/qcec_alt: proven; P2vsP0/qcec_alt: proven |
| mcx_b95_20 | 22 | P2 | proven | proven | proven | not run |
| vbe_adder_7 | 22 | P2 | proven | proven | proven | not run |
| rgqft_mult_6 | 24 | P2 | proven | proven | proven | not run |
| cdkm_adder_15 | 32 | P2 | proven | proven | proven | not run |
| draper_adder_16 | 32 | P0 | proven | proven | proven | not run |
| vbe_adder_11 | 34 | P2 | proven | proven | proven | not run |
| mcx_clean_20 | 39 | P0 | proven | proven | proven | not run |
| modadd_2n_20 | 40 | P2 | proven | proven | proven | not run |
| cdkm_adder_20 | 42 | P2 | proven | proven | proven | not run |
| mcx_clean_28 | 55 | P0 | proven | proven | proven | not run |
| mcx_dirty_28 | 55 | P2 | proven | proven | proven | not run |
| vbe_adder_18 | 55 | P2 | proven | proven | proven | not run |
| cdkm_adder_27 | 56 | P2 | proven | proven | proven | not run |
| draper_adder_28 | 56 | P0 | timeout | timeout | not run | not run |
| mcx_b95_54 | 56 | P2 | proven | proven | proven | not run |

## Open items

- [O] draper_adder_28 needs a timeout above 300 s or a different method.
- [O] hrs_mult_5 needs a checker that accepts non-dyadic angles.
- [O] QCEC on the remaining 18 circuits was not run. It is kept for cross-checking only and does not change any PyZX verdict.
