# QCEC snippet (family C, PSEL4)

Source of every number: `results/family_C_equivalence_qcec.md`.

- [F] MQT QCEC 3.10.2 was run on the three PSEL4 outputs that the PyZX miter did not prove (hrs_mult_5, rgqft_mult_6, draper_adder_28), with the ZX checker and the alternating decision-diagram checker run separately, each with a 600 s timeout.
- [F] QCEC proved none of the three. The ZX checker returned `probably_not_equivalent` on all three, and the alternating checker returned `no_information` or was killed at its time limit. No pair returned `not_equivalent`.
- [F] The PSEL4 output is proven equal to its input on 17 of 20 family C circuits. hrs_mult_5, rgqft_mult_6 and draper_adder_28 remain unproven.
- [F] A QCEC check of the L3 outputs on 7 further circuits with a 60 s timeout proved none of them. All 7 are L3 PSEL4 picks proven by the PyZX miter in `results/family_C_equivalence_psel4.md`.
- [O] QCEC adds no proof on family C beyond the PyZX miter. The three open circuits need a different method or a longer time budget.
