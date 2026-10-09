# Family C: equivalence of the PSEL4 picks

Written by `python3 pipelines/equiv_psel4_C.py --summary` from `results/family_C_equivalence_psel4.csv` (L3 / P2L3 picks, this run), `results/family_C_equivalence.csv` (P0 / P2 picks, PyZX rows), `value/family_C_selector.csv` and `results/strong_baselines.csv`. Method in the docstring of `pipelines/equiv_psel4_C.py`. Test: `pipelines/test_equiv_psel4_C.py`.

## Selector

- [F] PSEL4 keeps the lowest HQC of P0, P2, L3, P2L3 per circuit. Ties go to the lower n_2q, then to the order P0, L3, P2, P2L3.
- [F] Picks: L3 8, P0 5, P2 4, P2L3 3 (of 20).

## Method

- [F] L3 and P2L3 picks were recompiled with `strong_baselines.compile_variant` (QuantinuumBackend("H2-1", QuantinuumAPIOffline()), optimisation_level=3). The recomputed HQC equals the `results/strong_baselines.csv` value for every recompiled circuit: True. Outputs are stored as `results/compiled/{L3,P2L3}/<file>`.
- [F] Check: the PyZX miter of `pipelines/equiv_family_C.py` (dyadic snap to 2^-(G_in+4), off-grid tolerance 1e-6 half-turns, `full_reduce`, identity-wire test), full 2^n x 2^n unitary up to global phase, 300 s per circuit, 2 workers. Off-grid circuits get the 64-random-basis-input check of `run_family_C.basis_check` as a spot check, which is not a proof.
- [F] P0 and P2 picks are taken from the existing PyZX rows of `results/family_C_equivalence.csv`; nothing was rerun for them.

## Result

- [F] PSEL4 output proven equal to its input: 17 of 20 circuits.
- [F] L3 / P2L3 picks proven in this run: 9 of 11.
- [F] Proven only up to angle rounding: 0.
- [F] Not proven: hrs_mult_5 (P2, inconclusive, spot check pass (run_family_C)); rgqft_mult_6 (L3, timeout); draper_adder_28 (P2L3, timeout).

## Per circuit

| circuit | n | PSEL4 pick | HQC | method / source | verdict | max snap (half-turns) | time (s) | spot check | notes |
|---|---|---|---|---|---|---|---|---|---|
| draper_adder_10 | 20 | P0 | 370.4 | pyzx miter, family_C_equivalence.csv | proven | 4.35e-14 | 3.2 |  | grid 2^-14; max snap 4.35e-14 half-turns |
| modadd_2n_10 | 20 | P2L3 | 367.8 | pyzx miter, this run | proven | 0 | 3.48 |  |  |
| hrs_mult_5 | 21 | P2 | 4174.4 | pyzx miter, family_C_equivalence.csv | inconclusive |  | 2.53 | pass (run_family_C) | off-grid angles: max distance to 2^-7 grid 0.00391 half-turns (KAK resynthesis); PyZX needs exact phases, not run |
| mcx_clean_11 | 21 | P0 | 180.8 | pyzx miter, family_C_equivalence.csv | proven | 0 | 0.74 |  | grid 2^-4; max snap 0 half-turns |
| cdkm_adder_10 | 22 | L3 | 325.4 | pyzx miter, this run | proven | 0 | 2.15 |  |  |
| mcx_b95_20 | 22 | P2 | 693.0 | pyzx miter, family_C_equivalence.csv | proven | 0 | 22.1 |  | grid 2^-4; max snap 0 half-turns |
| vbe_adder_7 | 22 | L3 | 232.2 | pyzx miter, this run | proven | 0 | 1.44 |  |  |
| rgqft_mult_6 | 24 | L3 | 1540.4 | pyzx miter, this run | timeout |  | 300 |  | killed after 300 s |
| cdkm_adder_15 | 32 | L3 | 484.0 | pyzx miter, this run | proven | 0 | 9.7 |  |  |
| draper_adder_16 | 32 | P0 | 906.8 | pyzx miter, family_C_equivalence.csv | proven | 5.27e-12 | 27.6 |  | grid 2^-20; max snap 5.27e-12 half-turns |
| vbe_adder_11 | 34 | L3 | 367.4 | pyzx miter, this run | proven | 0 | 7.83 |  |  |
| mcx_clean_20 | 39 | P0 | 339.2 | pyzx miter, family_C_equivalence.csv | proven | 0 | 2.15 |  | grid 2^-4; max snap 0 half-turns |
| modadd_2n_20 | 40 | P2L3 | 771.8 | pyzx miter, this run | proven | 0 | 25.4 |  |  |
| cdkm_adder_20 | 42 | L3 | 632.2 | pyzx miter, this run | proven | 0 | 13 |  |  |
| mcx_clean_28 | 55 | P0 | 480.0 | pyzx miter, family_C_equivalence.csv | proven | 0 | 3.76 |  | grid 2^-4; max snap 0 half-turns |
| mcx_dirty_28 | 55 | P2 | 589.0 | pyzx miter, family_C_equivalence.csv | proven | 0 | 6.63 |  | grid 2^-4; max snap 0 half-turns |
| vbe_adder_18 | 55 | L3 | 604.0 | pyzx miter, this run | proven | 0 | 15.2 |  |  |
| cdkm_adder_27 | 56 | L3 | 840.4 | pyzx miter, this run | proven | 0 | 22.4 |  |  |
| draper_adder_28 | 56 | P2L3 | 2336.2 | pyzx miter, this run | timeout |  | 300 |  | killed after 300 s |
| mcx_b95_54 | 56 | P2 | 1957.8 | pyzx miter, family_C_equivalence.csv | proven | 0 | 204 |  | grid 2^-4; max snap 0 half-turns |
