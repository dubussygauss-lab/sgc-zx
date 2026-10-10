# Family C: equivalence of the pytket-quantinuum level 3 output (L3)

Written by `python3 pipelines/equiv_L3_C.py --summary` from `results/family_C_equivalence_L3.csv` and `results/strong_baselines.csv`. Method in the docstring of `pipelines/equiv_L3_C.py`. Test: `pipelines/test_equiv_L3_C.py`.

## Method

- [F] Every family C circuit was recompiled with `strong_baselines.compile_variant("L3")` (QuantinuumBackend("H2-1", QuantinuumAPIOffline()).get_compiled_circuit(c, optimisation_level=3)). Recomputed HQC equals the L3 value of `results/strong_baselines.csv` for every circuit: True. Outputs are stored as `results/compiled/L3/<file>` (column `stored`).
- [F] Check: the PyZX miter of `pipelines/equiv_family_C.py` via `equiv_psel4_C.miter_check` (measurement map applied as output permutation, dyadic snap to 2^-(G_in+4), off-grid tolerance 1e-6 half-turns, `full_reduce`, identity-wire test). It proves equality of the full 2^n x 2^n unitary up to global phase with no ancilla fixed. 900 s per circuit, 2 workers.
- [F] Timeouts are wall-clock on a 2-core machine shared with other jobs (load average about 5 to 6 during the run).
- [F] Circuits with off-grid angles are not provable with this PyZX method. They get the 64-random-basis-input check of `run_family_C.basis_check` (tolerance 1e-8), which is a spot check and not a proof.

## Result

- [F] L3 outputs proven equal to their input: 18 of 20.
- [F] Proven only up to angle rounding: 0.
- [F] Not proven: hrs_mult_5 (timeout); rgqft_mult_6 (timeout).
- [F] Over the 18 proven circuits: total HQC L2 14798.0, L3 12825.4, saving of L3 against L2 13.33 %.
- [F] Over all 20 circuits: total HQC L2 24535.0, L3 18853.2, saving of L3 against L2 23.16 %.
- [F] HQC values are those of `results/strong_baselines.csv` (variants L2, L3). Saving = (L2 - L3) / L2.

## Per circuit

| circuit | n | HQC L2 | HQC L3 | verdict | method | max snap (half-turns) | grid | time (s) | spot check (dev) | stored file | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| draper_adder_10 | 20 | 370.4 | 390.6 | proven | pyzx-miter | 0 | 2^-14 | 6.38 |  | new |  |
| modadd_2n_10 | 20 | 388.2 | 379.4 | proven | pyzx-miter | 0 | 2^-4 | 2.59 |  | new |  |
| hrs_mult_5 | 21 | 5291.4 | 4487.4 | timeout | pyzx-miter |  |  | 900 |  | new | killed after 900 s |
| mcx_clean_11 | 21 | 180.8 | 182.8 | proven | pyzx-miter | 0 | 2^-4 | 0.91 |  | new |  |
| cdkm_adder_10 | 22 | 371.6 | 325.4 | proven | pyzx-miter | 0 | 2^-4 | 2.27 |  | kept (matches) |  |
| mcx_b95_20 | 22 | 693.4 | 702.0 | proven | pyzx-miter | 0 | 2^-4 | 29.1 |  | new |  |
| vbe_adder_7 | 22 | 370.4 | 232.2 | proven | pyzx-miter | 0 | 2^-4 | 1.33 |  | kept (matches) |  |
| rgqft_mult_6 | 24 | 4445.6 | 1540.4 | timeout | pyzx-miter |  |  | 900 |  | kept (matches) | killed after 900 s |
| cdkm_adder_15 | 32 | 551.6 | 484.0 | proven | pyzx-miter | 0 | 2^-4 | 13.7 |  | kept (matches) |  |
| draper_adder_16 | 32 | 906.8 | 911.2 | proven | pyzx-miter | 1.73e-18 | 2^-20 | 87.9 |  | new |  |
| vbe_adder_11 | 34 | 593.6 | 367.4 | proven | pyzx-miter | 0 | 2^-4 | 7 |  | kept (matches) |  |
| mcx_clean_20 | 39 | 339.2 | 341.2 | proven | pyzx-miter | 0 | 2^-4 | 5.6 |  | new |  |
| modadd_2n_20 | 40 | 802.2 | 783.4 | proven | pyzx-miter | 0 | 2^-4 | 27.5 |  | new |  |
| cdkm_adder_20 | 42 | 731.6 | 632.2 | proven | pyzx-miter | 0 | 2^-4 | 13.3 |  | kept (matches) |  |
| mcx_clean_28 | 55 | 480.0 | 482.0 | proven | pyzx-miter | 0 | 2^-4 | 11.7 |  | new |  |
| mcx_dirty_28 | 55 | 591.0 | 599.2 | proven | pyzx-miter | 0 | 2^-4 | 22 |  | new |  |
| vbe_adder_18 | 55 | 984.2 | 604.0 | proven | pyzx-miter | 0 | 2^-4 | 15.7 |  | kept (matches) |  |
| cdkm_adder_27 | 56 | 983.6 | 840.4 | proven | pyzx-miter | 0 | 2^-4 | 23 |  | kept (matches) |  |
| draper_adder_28 | 56 | 3501.2 | 2601.2 | proven | pyzx-miter | 1.73e-18 | 2^-32 | 522 |  | new |  |
| mcx_b95_54 | 56 | 1958.2 | 1966.8 | proven | pyzx-miter | 0 | 2^-4 | 312 |  | new |  |
