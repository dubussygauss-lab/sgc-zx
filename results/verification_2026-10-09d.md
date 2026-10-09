# Verification of official baseline, family C and use case (2026-10-09d)

Independent verifier. Own code only (scratch scripts, not committed). No `value/` script was imported. `pipelines/compile.py` was imported once, only to reproduce the stored use-case P2 circuit for an exactness check (item 3.6). Tools: pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx, qiskit 2.5.2 (source reading only), own sparse and dense simulators. Each simulator was tested on negative controls. A wrong circuit gave |overlap| 0 and a single RZZ angle perturbed by 0.01 pi gave deviation 1.2e-4. Both were reported FAIL.

HQC convention used throughout: HQC = 5 + (N_1q + 10 N_2q + 5 N_SPAM) * 1000/5000 with N_SPAM = n_qubits + Measure + Reset. This is `estimate_cost` of the challenge repo (`src/python/pytket_cost_estimation.py`, `spam` starts at `circuit.n_qubits`). For a circuit with every qubit measured, N_SPAM = 2n.

## Summary

| # | claim | verdict |
|---|---|---|
| 1.1 | Own offline-backend compiles (13 circuits, A/B1/B1x/B2) equal stored P0 rows | PASS |
| 1.2 | P0off agrees with stored P0 on all 223 circuits (CSV level) | PASS |
| 1.3 | P2off agrees with stored P2 on 222 circuits, hwb8 P2off timeout | PASS |
| 2.1 | Family C HQC, pick, saving %, n_2q change, T saved per circuit (20) | PASS |
| 2.2 | Family C per-application aggregates (5 rows) | PASS |
| 2.3 | Family C extra shots at 10,000 HQC budget | FAIL (convention) |
| 2.4 | P0 recompile from bench/family_C (4 circuits) | PASS |
| 2.5 | manifest.csv citations (10 arXiv IDs) | PASS |
| 2.6 | Exactness of P0 and P2 for cdkm_adder_10, vbe_adder_7, mcx_clean_11 | PASS |
| 2.7 | Continuous-angle flags and T/Rz counts as written | PASS |
| 2.8 | Multiplier 34.5 % figure | PASS as arithmetic. It depends entirely on continuous-angle circuits (overclaim risk) |
| 3.1 | Grover success probabilities | PASS |
| 3.2 | T-counts written and after ZX | PASS |
| 3.3 | HQC, n_2q, PSEL pick | PASS (P2 1q count depends on the conversion route, see 3.5) |
| 3.4 | Shots in budget, expected hits, model ratio | PASS |
| 3.5 | Independent P2 route reproduces stored P2 | Not reproduced exactly (n_1q differs, stored values are the conservative ones) |
| 3.6 | Both compiled circuits exact | PASS |

FAIL list: 2.3 only.

## 1. Official baseline

1.1 `[F]` I compiled each circuit with `QuantinuumBackend(device_name="H2-1", api_handler=QuantinuumAPIOffline()).get_compiled_circuit(c, optimisation_level=2)` and recounted the result. I sampled 4 circuits from A, 3 from B1, 2 from B1x and 3 from B2 at random (seed 7), plus B1/hwb8.qasm. All 13 compiled circuits have n_2q (ZZPhase+ZZMax), PhasedX count and HQC equal to the P0 row of `results/family_*_counts.csv`.

| family | file | n_2q | PhasedX | HQC |
|---|---|---|---|---|
| A | tfim_n12_r4_disorder_s3 | 44 | 75 | 132.0 |
| A | ladder_n6_r1_disorder_s3 | 7 | 11 | 33.2 |
| A | tfim_n6_r2_disorder_s2 | 10 | 20 | 41.0 |
| A | xxz_n6_r4_disorder_s3 | 60 | 121 | 161.2 |
| B1 | barenco_tof_3 | 20 | 23 | 59.6 |
| B1 | barenco_tof_4 | 40 | 45 | 108.0 |
| B1 | mod_red_21 | 88 | 113 | 225.6 |
| B1 | hwb8 | 5912 | 7140 | 13281.0 |
| B1x | csla_mux_3 | 63 | 90 | 179.0 |
| B1x | gf2_pow_5_mult | 129 | 163 | 325.6 |
| B2 | haar_n3_eps1e-05_s4 | 19 | 37 | 56.4 |
| B2 | haar_n2_eps1e-03_s2 | 3 | 8 | 16.6 |
| B2 | haar_n3_eps1e-05_s2 | 19 | 37 | 56.4 |

1.2 `[F]` `results/official_baseline.csv` holds 223 P0off rows (A 180, B1 15, B1x 8, B2 20). The stored P0 rows number 223 with the same split. I joined the two tables myself. n_2q, n_1q and HQC show 0 mismatches and no stored row is missing.

1.3 `[F]` The table holds 222 P2off rows with counts. All 222 equal the stored P2 rows. B1/hwb8 P2off has no count (timeout), as the md states.

Note `[O]`: the task brief writes the formula with "5 N_M". The stored numbers use N_SPAM = 2n (preparation + measurement). This matches the challenge's `estimate_cost`. Any text in the report should state N_SPAM, not N_M = n. For example, ladder_n10 gives 55.6 with 2n and would give 45.6 with n.

## 2. Family C

2.1 `[F]` I recounted all 40 compiled files in `results/compiled/{P0,P2}/<file>`, parsed from hqslib1 QASM with maxwidth 128. Per circuit, the P0/P2 n_2q, PhasedX and HQC equal `results/family_C_counts.csv`. The PSEL pick, hqc_PSEL, saved_hqc, saved_pct, n2q_P0, n2q_PSEL, d_n2q, t_written and t_saved_PSEL equal `value/family_C_selector.csv` to 1e-6 in all 20 rows. t_zx_P2 was taken from the counts CSV. I recomputed the ZX-stage T-count myself for the use case only (3.2).

2.2 `[F]` The aggregates I recomputed match `value/family_C_selector_apps.csv` exactly. Grover oracle 4242.6/4239.8/4239.8, saved 2.8 (0.066 %). QFT adder 0 saving. Adder 5777.0 to 5031.4, saved 745.6 (12.906 %), d_n2q -351, T saved 1110. Multiplier 9737.0 to 6381.0, saved 3356.0 (34.466 %), d_n2q -1532, T saved 1408. All 24535.0 to 20430.6, saved 4104.4 (16.729 %), 14 P2 picks, d_n2q -1884, T saved 2548.

2.3 FAIL (convention) `[F]` `extra_shots` uses a single-job formula, floor(9995*5000/G). This gives one-job shot counts above 10,000. Examples are mcx_clean_11 at 56,854 shots and 16 of 20 circuits overall above 10,000. `value/finals_plan.py`, `value/value_by_application.py` and `value/usecase.py` all apply the H2 cap of 10,000 shots per job with a 5 HQC fee per job. Family C does not, so its shot numbers are inconsistent with the rest of the package. Recomputed with the cap (P0 shots, extra shots): modadd_2n_10 26056, 1180. cdkm_adder_10 27236, 3116. vbe_adder_7 27326, 7159. cdkm_adder_15 18276, 2126. vbe_adder_11 16972, 4528. modadd_2n_20 12531, 365. cdkm_adder_20 13748, 1602. vbe_adder_18 10202, 3178. cdkm_adder_27 10208, 1198. mcx_b95_20 14511, 9. mcx_dirty_28 17047, 59. The sum is 27,317 capped against 27,389 stored. Fix: compute `shots_P0`, `shots_PSEL` and `extra_shots` in `value/family_C_selector.py` with the same capped function as `value/usecase.py` (`shots_capped`) and say so in the md header. Hold-out `[O]`: the `extra_shots` total in the "all" and per-application rows adds shots of different circuits. The sum has no single physical meaning. Drop it or label it as a sum of per-circuit budgets.

2.4 `[F]` I recompiled P0 myself from `bench/family_C` with the offline backend. vbe_adder_7 gives 142/187/370.4, cdkm_adder_10 141/203/371.6, rgqft_mult_6 1994/2023/4445.6 and mcx_clean_11 59/79/180.8 (n_2q/PhasedX/HQC). All equal the stored P0 rows.

2.5 `[F]` I fetched the arXiv abstract pages for all 10 IDs in `bench/family_C/manifest.csv` and `value/usecase.md`. Titles and authors match the citations: quant-ph/0008033 Draper. 1706.07884 Gidney, "Factoring with n+2 clean qubits and n-1 dirty qubits". 1805.12445 Haener, Roetteler, Svore. 1508.03273 Maslov. quant-ph/0410184 Cuccaro, Draper, Kutin, Moulton. quant-ph/9503016 Barenco et al. 1501.06911 Iten, Colbeck, Kukuljan, Home, Christandl. quant-ph/9511018 Vedral, Barenco, Ekert. 1411.5949 Ruiz-Perez, Garcia-Escartin. quant-ph/9605043 Grover. The attribution of `ModularAdderGate(n).definition` (= `adder_modular_v17`) to 1706.07884 matches the docstring of Qiskit 2.5.2 `vrg_modular_adder.py`.

2.6 `[F]` I wrote my own sparse simulator using pytket `Op.get_unitary` per gate. The output wire map was read from the `measure q[j] -> c[i]` lines. For 16 basis inputs (all-zero plus 15 random) I compared input and compiled outputs and required one common global phase across all inputs. Max deviation: mcx_clean_11 P0 3.1e-15 and P2 2.4e-15. vbe_adder_7 P0 7.0e-15 and P2 3.2e-15. cdkm_adder_10 P0 8.0e-15 and P2 5.3e-15. min |overlap| = 1.0 in all cases. PASS. `[O]` This checks 16 of 2^21 or 2^22 columns. It is not a proof of equivalence, and the md states the same for its own 64-input check.

2.7 `[F]` I recounted T/Tdg plus Rz at odd multiples of pi/4 as T, and other non-Clifford Rz separately, in the input QASM. The counts equal the manifest `t_count_as_written` and `n_rz_non_cliffordT_as_written` for all 20 files. Five circuits contain continuous angles and carry continuous_angles=True: draper_adder_10/16/28, hrs_mult_5 (1050 non-Clifford+T Rz) and rgqft_mult_6 (1842).

2.8 `[F]` Both multipliers contain continuous angles. The 34.5 % multiplier saving, and 3356.0 of the 4104.4 total HQC saved (81.8 %), come from these two circuits only. The 15 circuits without continuous angles save 748.4 of 10019.6 HQC = 7.47 %. The five continuous-angle circuits save 3356.0 of 14515.4 = 23.12 %, all of it from the two multipliers (the three Draper adders pick P0). The arithmetic is correct.

Further `[F]` facts for headline use:
- 4 of the 14 P2 picks are not covered by any check ("unchecked-branching"): modadd_2n_10, modadd_2n_20, mcx_dirty_28, mcx_b95_54. Together they save 41.6 HQC.
- "T saved" for hrs_mult_5 (1163) and rgqft_mult_6 (245) counts T only. These circuits keep 600 and 507 non-Clifford+T rotations after the ZX stage (`n_non_cliffordT_zx`). They are not Clifford+T circuits, so T-count is not their non-Clifford cost.

## 3. Use case (Grover)

3.1 `[F]` I ran a dense statevector of `bench/usecase/grover_d5.qasm` (7 qubits) and `grover_d6.qasm` (9 qubits) from |0>. Data-register success probability is 0.9991823155433 for d5 and 0.9965856807868 for d6. The closed form sin^2((2k+1) theta) with theta = asin(2^(-d/2)) gives the same values. Ancilla leakage is 0 to machine precision. k = floor(pi/4 sqrt(2^d)) = 4 and 6. The most likely data string, written q[0] first, is 10110 for d5 and 101101 for d6. These equal marked = 22 and 45 with q[0] as the most significant bit, which is the convention stated in `value/usecase.py`.

3.2 `[F]` T written is 448 and 1008 (64 and 144 Toffolis times 7). I ran pyzx myself: teleport_reduce, Circuit.from_graph, then basic_optimization. This gives T = 210 for d5 and 436 for d6, equal to the stored values. The Toffoli counts match Barenco Lemma 7.2 with m = d-1: 4(m-2) Toffolis per C^m X, two per iteration.

3.3 `[F]` My offline-backend P0 gives 320 / 376 PhasedX / 734.2 HQC for d5 and 720 / 832 / 1629.4 for d6. Both equal the stored values. The stored P2 values are n_2q 296 / 672 with HQC 694.4 / 1548.6. Compiling through `pipelines/compile.py` (P2) reproduces them exactly: n_1q 417 and 908. The PSEL pick is P2 in both. The saving is 39.8 HQC (5.42 %) and 80.8 HQC (4.96 %).

3.4 `[F]` Shots, recomputed with the 10,000-shot cap and 5 HQC per job: d5 P0 13,699 against PSEL 14,490 (+791, 5.77 %). d6 6,153 against 6,475 (+322, 5.23 %). Single-job values are 13,706 / 14,498 and 6,153 / 6,475. Ideal hits are 13,687.80 / 14,478.15 and 6,131.99 / 6,452.89. The model ratio exp(1.1801e-3 dN_2q) is 1.02873 for dN_2q = 24 and 1.05828 for 48. All match `value/usecase.csv`.

3.5 `[F]` I also built an independent P2 route: pyzx QASM parser, teleport_reduce, from_graph, basic_optimization, pyzx `to_qasm`, pytket parse, then the official L2 pass. It gives the same n_2q (296, 672) but fewer PhasedX (408 against 417, and 898 against 908). The HQC is 692.6 and 1546.6, lower by 1.8 and 2.0 than the stored values. `[O]` The P2 1q count depends on the circuit conversion route. The stored figures are the conservative ones and do not need a fix. A sentence that the P2 HQC is reproducible only with `pipelines/compile.py` conversions would be accurate.

3.6 `[F]` I checked exactness with dense unitaries over all 128 and 512 basis columns. The implicit qubit permutation was applied and one common global phase was required. Results: d5 P0 5.96e-14 and my P2 2.48e-13. d6 P0 1.11e-13 and my P2 9.31e-13. The stored-route P2 circuits from `pipelines/compile.py` give d5 4.84e-13 and d6 1.00e-12. This is a full-unitary check, not sampling. All circuits are exact.

## Overclaim risks for the report headline

- `[O]` The family C "16.7 % HQC saved" is 82 % driven by two multiplier circuits with continuous-angle rotations. A headline should give 7.5 % on the 15 discrete Clifford+T circuits (12.9 % on adders) alongside, or instead of, the 16.7 % and 34.5 % figures.
- `[O]` "T saved 2548" should not head the report for family C. 1408 of it comes from the two multipliers, which are not Clifford+T circuits, and T-count does not affect HQC on H2. HQC counts only PhasedX, ZZ and SPAM.
- `[O]` The family C exactness evidence is sampled (64 basis inputs) and absent for 4 of 14 P2 picks. Say "spot-checked on 64 basis inputs", not "verified exact".
- `[O]` Grover hit counts are ideal and the fidelity ratio comes from a model fitted on B1 proxies. Both are labelled in the md. A headline must not present them as hardware outcomes.
- `[O]` The official-baseline agreement shows that the reproduced P0 equals the official default pass at level 2 on these 223 inputs. It does not show this at level 3 or on circuits with classical control.
