# Verification of Table C2 and the overclaim fixes (8 October 2026, c)

Independent verifier. Scope: `git diff HEAD~4` for `report/report_v5.md`, `README.md`, `value/`, `results/literature_tcounts.csv`, `report/build_literature_tcounts.py`, `report/make_tables.py:literature_c2()`. The report was not edited.

Sources fetched on 8 October 2026 from arxiv.org/pdf and converted with `pdftotext -layout`: 1303.2042v2, 1601.07363v2, 1710.07345v2, 1712.01557v3, 1903.10477v3, 2402.14396v2. Table columns in the conversions were read row by row. No conversion damage was found in the rows used, except that superscripts are flattened (`GF(24 )` for GF(2^4)), which does not affect the counts.

## Summary table

| # | Check | Result | Recomputed / evidence |
|---|---|---|---|
| 1 | Published T-counts in `results/literature_tcounts.csv` against the fetched papers | PASS | All 219 rows compared: AMM2014 Table 1 (17), AM2016 Table II (69), Nam2018 Table 4 (24), TODD2018 Tables I and II (45), KvdW2020 Table 1 (42), AQ2024 Table 2 (22). No value differs. |
| 2 | Certified circuits barenco_tof_3, mod5_4, qft_4, tof_3 | PASS | mod5_4: AMM 16, AM2016 16/16/16, Nam L 16, TODD 16, TODD-part 18, PyZX 8, PyZX+TODD 7, AQ 7. barenco_tof_3: 16 (T-par, RM, Nam L/H, PyZX, PyZX+TODD), TODD 14, TODD-part 22, AQ 13. tof_3: 15 (all T-par family, PyZX, TODD-part), TODD 13 (Table I label "NC Toff4", n = 5), AQ 13. qft_4: AM2016 67/67/67, TODD 55, TODD-part 67, AQ 53. |
| 3 | GF(2^4), GF(2^5), GF(2^6) multipliers | PASS | AMM 68/111/150. AM2016 RMrec 68/101/144. Nam L 68/115/150. TODD 54/87/126. TODD-part 56/90/132. PyZX 68/115/150. PyZX+TODD 52/86/122. AQ 39/59/77. |
| 4 | same_circuit and ancilla_free flags | PASS | grover_5 same_circuit = no is right (AM2016 original 140, TODD and AQ input 52, ours 336). csla_mux_3 TODD rows same_circuit = no is right (TODD lists n = 16). TODD Table I ancilla_free = no is right (nh column > 0). AQ ancilla_free = yes exactly where the AQ "Compiled" qubit count equals "Original" (Mod 54 5/5, GF(2^m) 12/12, 15/15, 18/18), "unknown" where AQ marks the circuit split (Grover5, Hamming15 med). KvdW2020 states it targets ancilla-free optimisation (lines 123-124 of the conversion). |
| 5 | Table C2 cells, recomputed from the CSV with own code | PASS | 23 rows, 0 cell differences in best ancilla-free, sources, best with ancillas, floor and both differences. |
| 6 | C2 totals and Section 3.4 numbers | PASS | T after ZX 16+8+67+15 = 106. Best ancilla-free 16+7+67+15 = 105. Floor 4+2+37+4 = 47. 106-105 = 1. 105-47 = 58. 106-47 = 59. Best with ancillas 13+16+53+13 = 95. Comparable circuits 22, matches 14, others 8 (4 PyZX+TODD: mod5_4, mod_mult_55, hwb8, csla_mux_3. 3 AQ: GF multipliers. 1 T-par: hwb6). |
| 7 | Last sentence of the Section 3.4 `[O]` paragraph | FAIL | See F1. |
| 8 | Eligibility rule stated in the Section 3.4 intro | FAIL | See F2. |
| 9 | Scope of "published" claims in Section 3.4 | FAIL | See F3. |
| 10 | Tagging of the Section 3.4 `[O]` paragraph | FAIL | See F4. |
| 11 | hwb6 sentence | FAIL | See F5. |
| 12 | Section 1 bullet "Fault-tolerant cost": 0.443 beside the B1 saving, 0.997 for B2 only | PASS | B1 certified: floor 47 / T after ZX 106 = 0.4434. B2: 41,414 / 41,534 = 0.99711. B2 removed 862 of 42,396 = 2.03 %. Remaining removable 0.289 %, worst instance 1 - 0.99279 = 0.72 %. |
| 13 | Section 1.5 certificate scope | PASS | `results/certificates.csv` has 24 rows, max n = 5, B1 rows barenco_tof_3, mod5_4, qft_4, tof_3. "certified magic-state counts per subroutine" is gone. |
| 14 | Median extra-shot gain 4.3 % (Section 1.2) | PASS | From `value/value_ledger.csv`, NISQ layer, 15 B1 circuits: median of 100 extra_shots_at_budget / shots_at_budget_P0 = 4.320. Independent recomputation of shots as floor(9995 / ((HQC - 5) / 1000)) gives the same median. vbe_adder_3 is the maximum (28.6 %). One circuit is negative (-0.43 %). |
| 15 | Other Section 1.2 HQC figures | PASS | P0 15,516.0, P2 14,772.8, saved 743.2 = 4.79 %, per-circuit median 3.94 %. |
| 16 | Header and Section 6 do not imply certified counts per subroutine | PASS with open item | Section 6 states the 24-circuit scope and the loose B1 floors. The title "A certified resource ledger" is unchanged and the changelog leaves it to Kam. |
| 17 | No `[PENDING` or `[TBD` outside changelogs | PASS | Remaining hits are changelog lines 861, 871, 885, 926, 928, 939, 950 only. |
| 18 | Section 7 invents no roles | PASS with open item | Members listed without roles. First authorship of arXiv:2608.22801 confirmed on arxiv.org/abs (first `citation_author` is "Kam, Chon-Fai"). Aqora owner tagged `[O]`. The sentence "Roles of the other members to be confirmed by Kam before submission" is an open item without a bracket marker. |
| 19 | Section 1 identical to `report/sec1_v5.md` | PASS | Identical apart from one trailing blank line. |
| 20 | README against the repo | FAIL | See F6. Files named in the README exist (`barrier/run_certificates.py`, `submit/fetch_job.py`, `value/value_ledger.py`). H2-Emulator CSV has 22 rows and 3 job ids. The 1840 HQC total was not rechecked (the `hqc_or_seconds` column of `results/emulator_jobs.csv` holds durations for the H2-2E rows). Unverifiable here. |
| 21 | Style on added lines | FAIL (minor) | No semicolons, no em-dashes, no hedge adverbs, no "rather than" in the added report lines. Comma counts above two occur only in lists. One untagged line, see F7. |
| 22 | Tests | PASS | `python3 -m pytest -q value submit report/test_c2_literature.py`: 28 passed in 9.9 s. `report/test_c2_literature.py` runs its asserts at import, so pytest exercises it without collecting a test function. |
| 23 | `python3 report/make_tables.py --no-fig` leaves the tree clean | PASS | Exit 0. `git status --short` and `git diff --stat` empty. |

## Findings

F1. Section 3.4, last sentence of the `[O]` paragraph after Table C2: "Published optimisation from 2013 to 2024 has moved the four certified circuits toward the floor by one gate in total."
Observation: false as written. The six papers move the four circuits from 146 written T gates to 105, and from the 2013 to 2016 T-par values (16 + 16 + 67 + 15 = 114, AMM2014 Table 1 and AM2016 Table II) to 105, a move of 9 gates. One gate is the move beyond our own P2 output, which is itself PyZX (2019).
Fix: "Beyond our ZX output, the six papers lower the four certified circuits by one gate in total."

F2. Section 3.4, intro `[F]` paragraph: "A published value enters the ancilla-free column only if the paper's circuit has our qubit count and our written T-count."
Observation: the CSV cannot meet this rule for two sources. All 22 AQ2024 rows have an empty `paper_t_original` because AQ Table 2 lists no original T-count. All 24 Nam2018 rows have an empty `paper_n` because Nam Table 4 lists no qubit count. AQ2024 supplies the best ancilla-free value on mod5_4 and on the three GF multipliers.
Fix: add "AQ2024 lists no original T-count and takes its circuits from Amy's benchmark set (arXiv:2402.14396, "We take the circuits from Amy [36]", text before Table 2). Nam2018 lists no qubit count. For these two sources the match rests on the circuit name."

F3. Section 3.4, "the smallest published T-count of each B1 and B1x circuit", "no published ancilla-free method goes below our count", "Published optimisers therefore close 1 of the 59 gates".
Observation: the values come from six papers, not from an exhaustive survey of the literature. The wording reads as exhaustive.
Fix: replace "published" with "reported in the six papers" in these three places and in the C2 caption ("the smallest T-count in the six papers on the same n qubits").

F4. Section 3.4, `[O]` paragraph after Table C2.
Observation: sentences 1 to 4 ("matches ... on 14 of the 22", "four of the other eight ... TODD applied after PyZX", "three Galois-field multipliers ... AlphaTensor-Quantum", the hwb6 sentence) and sentence 6 are checkable facts inside an `[O]` paragraph. Only "The certificate cannot tell whether the 58 open gates are headroom or slack in the bound" is a judgement.
Fix: tag sentences 1 to 4 and the corrected F1 sentence `[F]` and keep `[O]` on the certificate sentence.

F5. Section 3.4, "The hwb6 value of 71 comes from a single T-par entry that conflicts with the same paper's text and with the 75 listed for T-par in arXiv:1903.10477."
Observation: the conflict is real (AM2016 says majority decoding gives "equal or lesser T-count than that reported by T-par", but its HWB6 row reads T-par 71, majority 75). "Single" is not accurate. arXiv:1712.01557 Table I also lists HWB6 with input 71 and method T-par.
Fix: "The hwb6 value of 71 is the T-par entry of arXiv:1601.07363 Table II, repeated as the input of arXiv:1712.01557 Table I. It conflicts with the text of arXiv:1601.07363 and with the 75 listed for T-par in arXiv:1903.10477."

F6. `README.md` ("Tests. Five run as scripts" and "Five run under pytest") and the Section 5 test table of the report.
Observation: commit eb18fea added `report/test_c2_literature.py` (a script-style test, docstring "Run: python3 report/test_c2_literature.py"), `report/build_literature_tcounts.py` and `results/literature_tcounts.csv`. None of the three appears in `README.md` or in Section 5 of the report.
Fix: README gains a line under "Reproducing every table" for `python report/build_literature_tcounts.py` (writes `results/literature_tcounts.csv`), and the script list becomes six with `python report/test_c2_literature.py`. Section 5 test table gains the same row with its run result.

F7. Table C2 block, summary line "On the 4 circuits with a floor: T after ZX 106, best ancilla-free 105, floor 47. ..."
Observation: the line carries no tag. It is written by `literature_c2()` in `report/make_tables.py`.
Fix: prefix the generated line with `` `[F]` `` in `make_tables.py` and regenerate.

## Observations without a FAIL

O1. `[O]` The "best with ancillas" total of 95 adds the TODD value 16 on mod5_4, which is above the ancilla-free 7 on the same circuit. The column is correct by its definition but the sum is not a best-case total. Consider dropping the sum or stating the per-circuit minimum over both columns (13 + 7 + 53 + 13 = 86).

O2. `[O]` The title "A certified resource ledger" still reads as if the whole ledger were certified. The certificate covers 24 circuits. The changelog leaves the wording to Kam.

O3. `[F]` The Section 7 sentence on the other members' roles is an open pre-submission item.
