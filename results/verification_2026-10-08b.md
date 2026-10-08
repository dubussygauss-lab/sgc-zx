# Verification of report v5, Section 1, Section 3.7.1, Section 6 hardware sentence, scoring map and Changelog v4 to v5

Verifier: independent agent, 8 October 2026. The report was not edited.

## Method

- `[F]` Every number was recomputed with fresh code from the raw CSVs, the compiled QASM in `results/compiled/` and the JSON payloads. `value/` and `submit/h22e_stats.py` were not imported.
- `[F]` HQC = 5 + 1000 (N_1q + 10 N_2q + 5 N_M) / 5000 with N_1q = PhasedX (`U1q` in the QASM) and N_2q = ZZPhase + ZZMax (`RZZ`). N_M = qubits + measures + resets, counted from each compiled QASM file. The QASM PhasedX and ZZ counts match the CSV columns on 105 of 105 B1 rows, 24 of 24 B1x rows and 1260 of 1260 family A rows. The recomputed HQC equals the CSV `hqc` column on every row (max difference 0.0).
- `[F]` Area assignment follows the summary table of `docs/applications.md` with the first listed row winning, so the three adders go to factoring and not to the chemistry row.
- `[F]` Ideal distributions for the H2-2E F_H come from a qiskit statevector of `bench/family_B1/<file>.qasm`. vbe_adder_3 and hwb6 have one ideal outcome. grover_5 has 64, and its counts keys are read in reversed bit order. Bootstrap sd uses `numpy.random.default_rng` with 4000 resamples. Twenty seeds were run to measure the Monte Carlo spread.
- `[F]` The slope a is the no-intercept least-squares fit of -ln F_H on n_2q over the 35 rows of `results/family_B1_proxy_h22e.csv`.
- `[F]` Scripts: scratchpad `verify.py`, `verify2.py`, `v3.py`, `v4.py` (not committed, outputs quoted below).
- `[F]` `python3 -m pytest -q value submit` gave 26 passed. `python3 report/make_tables.py --no-fig` ran and `git status --short` and `git diff --stat` were empty afterwards.

## Claim table

| # | Location | Claim | Recomputed | Verdict |
|---|---|---|---|---|
| 1 | 1, bullet "H2 cost" | B1 P2 14,772.8 vs P0 15,516.0, saved 743.2 = 4.8 %, median 3.9 % | 14,772.8 / 15,516.0 / 743.2 / 4.79 % / 3.94 % | PASS |
| 2 | 1, bullet "Fault-tolerant cost" | 2,862 of 7,048 T removed, 40.6 %. B2 certified fraction 0.997 | 2,862 / 7,048 / 40.61 %. 41,414 / 41,534 = 0.9971 | PASS |
| 3 | 1, bullet "Algorithms" | every circuit except hwb6, hwb8, ham15 x2 "is an adder, multiplier, oracle or Toffoli gate" | qft_4 is a Fourier transform and grover_5 a full search instance (Table 1.3 of the report says so). tof_n/barenco_tof_n placement is `[O]` in `docs/applications.md` | FAIL (F1) |
| 4 | 1, para 1 | "Every number below comes from ... value_ledger.md and value_by_application.md" | 7.3e-5, 9e-4, 1.8e-3 and 4e-5 occur in neither file. They come from `docs/platform_notes.md` 3.3. Line numbers 1813/2568/2662 come from the manuscript | FAIL (F2) |
| 5 | 1.1 | budget 10,000 HQC per team on H2-1E and H2-2E | same as Section 3.7. The forum topic is not stored in the repo. Only a code comment in `submit/h22e_stats.py:51` records it | PASS for consistency. Source Unverifiable from repo |
| 6 | 1.2 para 1 | HQC formula, N_1q = PhasedX, N_2q = ZZPhase + ZZMax, N_M = init + meas + reset, Rz free, from `estimate_cost` | GitHub `estimate_cost` fetched: spam = n_qubits + Measure + Reset, n1q = PhasedX, n2q = ZZMax + ZZPhase, 5 + gating_cost x shots/5000. `pipelines/compile.py:hqc` matches | PASS (see F8 on the tag) |
| 7 | 1.2 para 2 | p2 1.29e-3, p1 7.3e-5, readout 9e-4 / 1.8e-3, p_init 4e-5 | match `docs/platform_notes.md` 3.3 table | PASS |
| 8 | Table 1.1, all 10 rows | HQC P0, P2, saved, saved %, median % per area and family | every cell reproduced exactly (e.g. factoring B1 592.2 / 545.6 / 46.6 / 7.87 / 4.19, B1x all 3,288.8 / 3,141.0 / 147.8 / 4.49 / 2.40) | PASS |
| 9 | 1.2 para after Table 1.1 | P2 cheaper on 14 of 15 B1. hwb8 84.6 % of saving. 114.6 without hwb8 | 14 cheaper, 1 dearer (qft_4 98.4 to 98.8). 84.58 %. 114.6 | PASS (metric is HQC. Sections 3.2 and 6 give 13 of 15 with 2 ties on ZZPhase. Not a contradiction, see N1) |
| 10 | 1.2 shots para | vbe_adder_3 68,178 vs 87,675, +19,497, 28.6 %. mod5_4 +11,757, 7.5 % | 68,178.7 / 87,675.4 / 19,497 / 28.60 %. mod5_4 157,649 / 169,406 / 11,757 / 7.46 % | PASS as arithmetic under one job (see F7) |
| 11 | 1.2 family A para | P2 17,453.0 vs P0 16,422.6, +1,030.4, 6.3 %. dearer 108, cheaper 57. XXZ dearer on 60 of 60, +12.3 % | 17,453.0 / 16,422.6 / 1,030.4 / 6.27 %. 108 / 57 (15 equal). XXZ 9,353.8 vs 8,327.4, 60 of 60, 12.33 % | PASS |
| 12 | 1.3 para 1 | Litinski, Quantum 3, 128 (2019), arXiv:1808.02892 | title "A Game of Surface Codes", D. Litinski, DOI 10.22331/q-2019-03-05-128. The one-magic-state-per-T statement is not in the abstract. It is the paper's construction of pi/8 rotations | PASS |
| 13 | Table 1.2, all 10 rows | T written, T after ZX, saved, saved % | every cell reproduced exactly (e.g. Grover B1 637 / 327 / 310 / 48.67, B1x reversible 735 / 309 / 426 / 57.96) | PASS |
| 14 | 1.3 para 3 | Theorem B line 1813, Corollary cert line 2568, Theorem C line 2662 | `\begin{theorem}[Exactness Barrier]\label{thm:B}` at 1813, `\begin{corollary}\label{cor:cert}` at 2568 (tmin(V) >= lde(V hat)), `\begin{theorem}\label{thm:C}` at 2662 | PASS |
| 15 | 1.3 para 3 | arXiv:2608.22801 by Kam | fetched: same title. Authors Kam, Mahasinghe, K. De Silva, Cadet, Wang. Submitted 24 Aug 2026 | PASS |
| 16 | 1.3 B2 para | 862 of 42,396, 2.0 %. Floor 41,414 vs 41,534. 0.997. At most 0.3 %. Worst 0.7 % | 862 / 42,396 / 2.03 %. 41,414 / 41,534 / 0.9971. 0.289 %. Worst 0.721 % (haar_n3_eps1e-03_s5) | PASS |
| 17 | 1.3 B1 para | floor 47 vs 106, 0.443 | 4+2+37+4 = 47. 16+8+67+15 = 106. 0.4434 | PASS |
| 18 | 1.3 last para | Dasu et al., H1-1, 7(+3/-1) x 10^-5, arXiv:2506.14688 | fetched: S. Dasu first author, H1-1, 7(+3/-1) x 10^-5 | PASS |
| 19 | 1.4 Table 1.3 | areas, circuits and citations per row | match the summary table and circuit-group sections of `docs/applications.md`. Status column matches its `[F]`/`[O]` tags | PASS |
| 20 | 1.4 | arXiv:1601.07363 Amy and Mosca | fetched: "T-count optimization and Reed-Muller codes", Amy and Mosca | PASS |
| 21 | 1.4 | arXiv:0710.1093 | fetched: Cheung, Maslov, Mathew, Pradhan. Abstract covers binary-field multiplication and ECDLP over GF(2^m) | PASS |
| 22 | 1.4 | arXiv:1703.10535 | fetched: Figgatt et al. Abstract names Toffoli-4 with Toffoli-3 for Grover | PASS |
| 23 | 1.4 | arXiv:1202.6614 | fetched: Markov and Saeedi. Abstract: "arise as components of modular exponentiation in Shor's ..." | PASS |
| 24 | 1.4 | arXiv:quant-ph/9503016 | fetched: Barenco et al., "Elementary gates for quantum computation" | PASS |
| 25 | 1.4 Unverifiable para | mod_red_21 and 0710.1093 items | same wording as `docs/applications.md` | PASS |
| 26 | 1.5 para 1 | factoring 7.9 %, search 4.8 % | 7.87 %, 4.78 % | PASS on numbers. FAIL on tag (F5) |
| 27 | 1.5 para 2 | prize in Helios credits (email 25 Aug 2026) | email not in the repository | Unverifiable |
| 28 | 1.5 para 3 | slope 1.18e-3. Predicted gain 1.79 % on vbe_adder_3. Median 0.24 % over B1 | a = 1.1801e-3. exp(15a) - 1 = 1.786 %. Median over 15 B1 circuits of exp(a dN_2q) - 1 = 0.236 % | PASS on numbers. FAIL on tag (F5). 1.79 % is relative, 3.7.1 gives the absolute 0.0170 (N2) |
| 29 | 1.5 para 4 | six H2-2E jobs "cost 1,840 HQC" | sum of `hqc_estimate` = 1,840.0. Section 3.7.1 says the charged amount is not recorded | FAIL (F3) |
| 30 | 1.5 para 4 | F_H 0.954 / 0.959, not resolved on any of three, "(Section 3.7)" | 0.9540 / 0.9590. abs(z) at most 1.21 | PASS on numbers. Cross-reference should be 3.7.1 (F4) |
| 31 | 3.7.1 runs | six jobs, ids, completed 8 Oct, ledger rows | ids in CSV, JSON and `emulator_jobs.csv` rows 36 to 41 match the listed order. All COMPLETED, 1000 shots, `noisy_simulation` true | PASS |
| 32 | 3.7.1 cost | 1840.0 HQC, 18.4 %. Cost fields hold only duration | 1840.0. 18.40 %. `cost_fields` = {duration} in all six JSON | PASS |
| 33 | Table E2 | HQC estimate per row | formula from CSV counts gives 151.6, 119.0, 243.0, 232.6, 565.6, 528.2 = stored values | PASS |
| 34 | Table E2 | F_H per row | 0.9540, 0.9590, 0.9240, 0.9090, 0.8652, 0.8728 from counts. Equal to CSV and JSON | PASS |
| 35 | Table E2 | sd F_H | binomial 0.0066, 0.0063, 0.0084, 0.0091. grover_5 bootstrap 0.0112 / 0.0108 with my stream. 20-seed range 0.0111 to 0.0116 (P0) and 0.0108 to 0.0113 (P2) contains 0.0114 / 0.0112 | PASS |
| 36 | Table E2 | proxy (hwb6 only) and Selene columns | 0.8915, 0.8962. Selene 0.9410, 0.9350, 0.8845, 0.8805, 0.8245, 0.8315 | PASS |
| 37 | 3.7.1 paired differences | +0.0050 / 0.0091 / +0.55. -0.0150 / 0.0124 / -1.21. +0.0076 / 0.0160 / +0.48 | +0.0050 / 0.0091 / +0.55. -0.0150 / 0.0124 / -1.21. +0.0076 / 0.0156 / +0.49 (bootstrap stream) | PASS |
| 38 | 3.7.1 predicted gain | a = 1.1801e-3 over 35 rows, log line 77. dN 15, 5, 22. Ratios 1.0179, 1.0059, 1.0263. Gains 0.0170, 0.0055, 0.0228. 1.87, 0.44, 1.42 sd. Below by 1.32, 1.66, 0.95 sd | a = 1.1801e-3, line 77 is "a n_2q only a = 1.1801e-03". All values reproduced. grover_5 gives 1.46 / 0.97 with my bootstrap sd, inside the Monte Carlo spread | PASS |
| 39 | 3.7.1 shots for 2 sd | 1147, 20462, 1974 | 1147, 20462. grover_5 1878 with my sd, 1972 with the table sds. The 20-seed range is 1,888 to 1,992 | PASS (grover_5 value depends on the bootstrap stream, N3) |
| 40 | 3.7.1 proxy | hwb6 3.88 sd (P0), 1.41 sd (P2). Proxy P2 gain +0.0047 | 3.88, 1.41, +0.0047 | PASS |
| 41 | 3.7.1 Selene | excess 0.0130 to 0.0413, z 1.60 to 3.85, five of six > 2 sd | excess 0.0130 to 0.0413. z 1.60, 3.13, 3.85, 2.56, 2.96, 3.12. Five of six > 2 | PASS |
| 42 | 3.7.1 H2-Emulator | grover_5 P0 0.7898 on H2-Emulator, H2-2E 4.29 sd higher | F_H 0.7898. With the sds printed in Table E1 (0.0131) and Table E2 (0.0114) z = 4.34. 4.29 needs an H2-Emulator sd of 0.0134, which `h22e_stats.py` draws from a second bootstrap stream | FAIL (F6) |
| 43 | 3.7.1 `[O]` closing para | counts 1147 / 1974 / 20462. Above proxy and Selene on every row where either exists | reproduced | PASS on numbers. FAIL on tag (F5) |
| 44 | 6, hardware sentence | "six H2-2E rows ... are emulator runs. The 468 noiseless and 68 depolarising Selene runs ..." | the 22 H2-Emulator rows of Table E1 are not mentioned. The 468 full depolarising Selene runs (`results/selene_depolarizing_full.csv`, 468 rows, Section 2.6 and Table S2) are omitted | FAIL (F9) |
| 45 | Scoring map | four criteria and weights | `docs/rubric.md`: Problem & Value 0.3, Technical Performance & Hardware Use 0.3, Scientific Merit 0.2, Engineering & Reproducibility 0.2 | PASS |
| 46 | Scoring map, Engineering row | tests under bench/, noise/, barrier/, pipelines/, selene/, model/, submit/ | `value/test_value_ledger.py` and `value/test_value_by_application.py` exist and are the tests behind Section 1. They are not listed | FAIL (F10) |
| 47 | Changelog v4 to v5, bullet 1 | tagged `[O]` | Section 1 equals `report/sec1_v5.md` (diff: one trailing blank line). The H2-2SC paragraph is in 3.7 and the pipeline-scope paragraph in 2.2. The bullet is factual | FAIL on tag (F11) |
| 48 | Changelog bullets 2 to 6 | REPORT_V5 injector, `emulator_h22e()`, scratch copy removed, test file, markers removed, 3.88 sd | `REPORT_V5` at `make_tables.py:74` and injected. `emulator_h22e()` at line 822 calls `h22e_stats.compute`. `results/h22e_stats.py` absent. `submit/test_h22e_stats.py` has tests for rows, F_H, sd rule, HQC total and slope. No `[PENDING: H2-2E]` left. 3.88 reproduced | PASS |
| 49 | Changelog | no entry for the new `value/` scripts and tests | `value/value_ledger.py`, `value/value_by_application.py` and two tests are new in v5 (Section 1 cites their outputs) and absent from the changelog | FAIL (F10) |
| 50 | Style, scoped text | no semicolons, no em-dashes, no hedge adverbs, no "rather than" | none found | PASS |
| 51 | Style, scoped text | at most two commas per sentence outside lists | lines 26, 65, 894 and 896 exceed two only through lists or the citation parenthesis | PASS |
| 52 | Style, scoped text | every paragraph and bullet starts with a tag | the three job-id bullets (lines 549 to 551) and the generated E2 caption (line 558) carry no tag | FAIL (F12) |
| 53 | Consistency with 3.2 | "14 of 15" (Section 1, HQC) and "13 of 15, two ties" (3.2 and 6, ZZPhase) | both correct for their metric | PASS (N1) |
| 54 | Consistency with 3.3 and 3.4 | B2 2.0 % aggregate vs 1.3 to 3.1 % per configuration. 0.3 % vs 0.16 to 0.43 %. Worst 0.7 % vs 99.28 % minimum | consistent | PASS |
| 55 | Tests and tables | pytest value and submit. make_tables `--no-fig` then git diff | 26 passed. Diff empty | PASS |

## FAIL list with exact fixes

F1. Section 1 bullet "Algorithms" (line 26). Quoted: "is an adder, multiplier, oracle or Toffoli gate from factoring, discrete-log or search algorithms". qft_4 is a Fourier transform and grover_5 a full search instance. The Toffoli placement in search is `[O]` in `docs/applications.md`. Fix: "`[F]` Every circuit except hwb6, hwb8 and the two ham15 circuits is an adder, multiplier, Fourier transform, oracle, search instance or multi-controlled Toffoli. `[F]` The adders, multipliers and the Fourier transform come from factoring and discrete-log circuits, and grover_5 and mod5_4 from search (Section 1.4). `[O]` The Toffoli circuits are placed in search as oracle and diffusion parts."

F2. Section 1 paragraph 1 (line 20). Quoted: "Every number below comes from the script outputs". The noise parameters of 1.2 and the manuscript line numbers are not in those files. Fix: "`[F]` The HQC, shot and T-count numbers below come from the script outputs `value/value_ledger.md` and `value/value_by_application.md`. The noise parameters come from `docs/platform_notes.md` section 3.3."

F3. Section 1.5 paragraph 4 (line 114). Quoted: "cost 1,840 HQC". Section 3.7.1 states that the charged amount is not recorded. Fix: "`[F]` The six H2-2E jobs of vbe_adder_3, hwb6 and grover_5 under P0 and P2 carry HQC estimates that sum to 1,840 HQC."

F4. Same paragraph. Quoted: "(Section 3.7)". Fix: "(Section 3.7.1)".

F5. Tags on sourced facts in `[O]` paragraphs. (a) Line 108. "P2 saves 7.9 % on the checked factoring circuits and 4.8 % on the checked search circuits" sits in an `[O]` paragraph. Fix: open that sentence with `[F]`. (b) Line 112. The fit value, 1.79 % and 0.24 % are computed values. Fix: "`[F]` Model prediction. A proxy fit of 1.18e-3 per ZZ gate predicts a relative fidelity gain of 1.79 % for P2 on vbe_adder_3 and a median relative gain of 0.24 % over B1. `[O]` These are model predictions and not measurements." (c) Line 582. The sentences "They agree with the proxy within sampling error on hwb6 under P2 and not under P0", "The emulator F_H lies above the proxy and above Selene on every row where either exists" and "At the predicted gains a 2-sd resolution needs 1147 ..." are facts. Fix: move them into an `[F]` paragraph before the `[O]` paragraph. Keep "One reading is ..." under `[O]`.

F6. Section 3.7.1 "Comparison with the H2-Emulator" (line 580). Quoted: "4.29 sd higher". Tables E1 and E2 print sd 0.0131 and 0.0114, which give 0.0754 / hypot(0.0131, 0.0114) = 4.34. 4.29 uses an sd of 0.0134 from a separate bootstrap stream in `submit/h22e_stats.py`. Fix: "is 4.34 sd higher, with the sd of Table E1 and Table E2 combined". Alternatively make `h22e_stats.py` reuse the Table E1 sd.

F7. Section 1.2 shots paragraph (line 59). The numbers assume one job that pays the 5 HQC fee once. `docs/platform_notes.md` 3.4 quotes a hardware limit of 10,000 shots per job. Under that limit the numbers are 67,974 vs 87,324 (+19,350, 28.5 %) on vbe_adder_3 and 156,466 vs 168,050 (+11,584, 7.4 %) on mod5_4. Whether the per-job limit applies on H2-2E is Unverifiable from the repo. Fix: add "with the 5 HQC job fee counted once" after "At the 10,000 HQC team budget", or replace the numbers by the 10,000-shot-per-job values above.

F8. Section 1.2 paragraph 1 (line 38), tag. The sentence "The price of an H2 program is HQC = ..." is tagged `[F]`. `docs/platform_notes.md` 3.4 and Reference 6 mark the H2 form as `[O]` inferred from the Helios page. The organisers' `estimate_cost` (fetched) supports the formula as the challenge's estimator. It does not establish the H2 charge. Fix: "`[F]` The organisers' sample code prices an H2 program as HQC = ... `[O]` We take this as the H2 price. The Helios costing page gives the same form (Reference 6)."

F9. Section 6 (line 770). Quoted: "The six H2-2E rows of Section 3.7.1 are emulator runs. The 468 noiseless and 68 depolarising Selene runs". Fix: "`[F]` Nothing in this report has run on hardware. The 22 H2-Emulator rows of Section 3.7 and the six H2-2E rows of Section 3.7.1 are emulator runs. The 468 noiseless, the 68 depolarising and the 468 full depolarising Selene runs are local, use the Quest statevector backend, and do not contain the H2-2E noise model."

F10. Scoring map, Engineering & Reproducibility row (line 16), and Changelog v4 to v5. `value/` (two scripts and two pytest files, 9 tests passing) is absent from both. Fix: add `value/` to the list of test directories in the scoring map. Add a changelog bullet: "[F] `value/value_ledger.py` and `value/value_by_application.py` added with `value/test_value_ledger.py` and `value/test_value_by_application.py`. Their outputs feed Section 1." Section 5 (outside this scope) should gain the same rows.

F11. Changelog v4 to v5, bullet 1 (line 894). It is tagged `[O]` but describes a verifiable edit. Fix: change `[O]` to `[F]`.

F12. Section 3.7.1 lines 549 to 551 (job-id bullets) and line 558 (generated E2 caption) carry no tag. Fix: prefix each job-id bullet with `[F]`. In the `emulator_h22e()` caption string of `report/make_tables.py`, prefix `[F]` and rerun the injector.

## Notes (not failures)

- N1. `[O]` Line 57 says "cheaper" without the metric. It is HQC (qft_4 is dearer by 0.4 HQC through PhasedX gates while its ZZ count ties). Writing "cheaper in HQC" would prevent a reader from setting it against the 13 of 15 ZZPhase count of Sections 3.2 and 6.
- N2. `[O]` The 1.79 % of Section 1.5 is a relative gain and the 0.0170 of Section 3.7.1 is absolute. Both are correct. The fix in F5(b) adds the word "relative".
- N3. `[F]` The grover_5 sd, z, gain/sd and shots-for-2-sd in Table E2 and 3.7.1 depend on the bootstrap stream. Across 20 seeds the shots-for-2-sd value ranges from 1,888 to 1,992.
- N4. `[F]` Reference 1 still carries "[O: the arXiv number is not in the repository, audit item A10]". arXiv:2608.22801 now resolves to the manuscript title with Kam as first author. The marker can be dropped (outside scope).
- N5. `[F]` The 10,000 HQC quota (forum topic) and the Helios-credit prize (organisers' email) are not stored in the repository and are Unverifiable from it.
