# Family C: full equivalence check by ZX miter

Script: `pipelines/equiv_family_C.py` (method in its docstring). Tests: `pipelines/test_equiv_family_C.py` (one positive, one broken case, both pass). Raw rows: `results/family_C_equivalence.csv`.

## Method

- [F] Each compiled output (`results/compiled/{P0,P2}/<file>`) is compared with the input `bench/family_C/<file>`, and P2 with P0, as full 2^n x 2^n unitaries up to global phase. Measurements are stripped and pytket's implicit qubit permutation is read from the measurement map. No ancilla is fixed to |0>, so a proof here is stronger than equality on clean-ancilla inputs.
- [F] PyZX 0.10.7: miter `G_A ; adjoint(G_B)`, `full_reduce`, then the test of `Circuit.verify_equality` (2n boundary vertices only, simple edges, input i wired to output i). Angles are snapped to the dyadic grid 2^-G with G = (input's largest dyadic exponent) + 4. The input angles lie on that grid exactly. The largest snap on the compiled side is at most 5.3e-12 half-turns over all proven rows (float noise), recorded per row. A positive result proves equivalence of the snapped circuits. A negative result is inconclusive.
- [F] MQT QCEC 3.10.2 installed. ZX checker and alternating DD checker were run only on cdkm_adder_10 and draper_adder_10 before the 45-minute budget ran out (see table). QCEC's ZX checker returned `probably_not_equivalent` on 5 of 6 pairs that PyZX proves, which is QCEC's "could not reduce" outcome, not a counterexample. The alternating DD checker is a floating-point check with tolerance.

## Results (PyZX miter)

- [F] P0 vs input: 17 of 20 proven.
- [F] P2 vs input: 17 of 20 proven.
- [F] P2 vs P0: 17 of 20 proven.
- [F] hrs_mult_5 (P0, P2): inconclusive, not run by PyZX. FullPeepholeOptimise's KAK resynthesis leaves angles off any dyadic grid (e.g. 1/3 half-turn), and PyZX needs exact phases. The 64-input basis check (pass) remains the only check for this circuit.
- [F] draper_adder_28 (P0, P2): timeout (300 s) in `full_reduce`. P2 vs P0 not run (time budget). The "equal up to rounding" path (input angles rounded to denominator 2^20 as pyzx parses them) was therefore never reached. Its status is unchanged from before: unchecked.
- [F] mcx_b95_54: not run (time budget).

## The four previously unchecked P2 picks

- [F] modadd_2n_10: P2 vs input proven; P0 vs input proven; P2 vs P0 proven.
- [F] modadd_2n_20: P2 vs input proven; P0 vs input proven; P2 vs P0 proven.
- [F] mcx_dirty_28: P2 vs input proven; P0 vs input proven; P2 vs P0 proven.
- [F] mcx_b95_54: P2 vs input not run (time budget); P0 vs input not run (time budget); P2 vs P0 not run (time budget).

## Verdict table

| circuit | n | P0 vs input | P2 vs input | P2 vs P0 | QCEC (second method) |
|---|---|---|---|---|---|
| draper_adder_10 | 20 | proven | proven | proven | P0/qcec_zx: inconclusive; P2/qcec_zx: inconclusive; P2vsP0/qcec_zx: inconclusive; P0/qcec_alt: proven; P2/qcec_alt: proven; P2vsP0/qcec_alt: timeout |
| modadd_2n_10 | 20 | proven | proven | proven | not run |
| hrs_mult_5 | 21 | inconclusive | inconclusive | inconclusive | not run |
| mcx_clean_11 | 21 | proven | proven | proven | not run |
| cdkm_adder_10 | 22 | proven | proven | proven | P0/qcec_zx: inconclusive; P2/qcec_zx: proven; P2vsP0/qcec_zx: inconclusive; P0/qcec_alt: proven; P2/qcec_alt: proven; P2vsP0/qcec_alt: proven |
| mcx_b95_20 | 22 | proven | proven | proven | not run |
| vbe_adder_7 | 22 | proven | proven | proven | not run |
| rgqft_mult_6 | 24 | proven | proven | proven | not run |
| cdkm_adder_15 | 32 | proven | proven | proven | not run |
| draper_adder_16 | 32 | proven | proven | proven | not run |
| vbe_adder_11 | 34 | proven | proven | proven | not run |
| mcx_clean_20 | 39 | proven | proven | proven | not run |
| modadd_2n_20 | 40 | proven | proven | proven | not run |
| cdkm_adder_20 | 42 | proven | proven | proven | not run |
| mcx_clean_28 | 55 | proven | proven | proven | not run |
| mcx_dirty_28 | 55 | proven | proven | proven | not run |
| vbe_adder_18 | 55 | proven | proven | proven | not run |
| cdkm_adder_27 | 56 | proven | proven | proven | not run |
| draper_adder_28 | 56 | timeout | timeout | not run (time budget) | not run |
| mcx_b95_54 | 56 | not run (time budget) | not run (time budget) | not run (time budget) | not run |

## Open items

- [O] mcx_b95_54 (all three comparisons) and draper_adder_28 P2 vs P0 need one more run: `python3 pipelines/equiv_family_C.py --files mcx_b95_54,draper_adder_28 --methods pyzx` (rows already present are skipped). draper_adder_28 needs a timeout above 300 s or a different method.
- [O] QCEC on the remaining 18 circuits was not run. Kept as a second method only for cross-checking. It does not change any PyZX verdict.
