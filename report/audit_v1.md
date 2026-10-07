# Audit of report/report_v1.md (first pass, read only)

Auditor: an agent that did not write the report. Date: 7 October 2026. Every number below was recomputed from `results/*.csv` or read from the named source file. `[F]` = verifiable from the repository, `[O]` = judgement. Severity: Critical (a claim a judge would find false), Major (a claim that cannot be traced or contradicts an artifact), Minor (clarity or prose rule).

## A. Logic breaks, unsupported claims, numbers without a source

### Major

A1. Section 1, paragraph 1, "HQC = 5 + C (N_1q + 10 N_2q + 5 N_M) / 5000", tagged `[F]`. `[F]` `docs/platform_notes.md` section 3.4 says the formula is quoted from the Helios costing page and that the H2 form is inferred ("Treat the H2 form as inferred until the H2-2SC syntax checker returns a cost", tagged `[O]` there). The report presents the H2 form as `[F]`. Fix: keep the formula, cite it as the Helios page with the H2 form stated as an inference, or run the H2-2SC syntax checker on one circuit and quote the returned cost. Marked `[NEEDS SOURCE]` in the text.

A2. Section 1, paragraph 6, "three circuit families and five compilation pipelines". `[F]` Section 2.2 lists seven pipelines (P0ref, P0, P0L1, P1, P2, P3, P4) and Tables A1, A2 and B1 report seven. Family B2 is run on five (`make_tables.py`, `PIPELINES_B2`). The count is wrong for families A and B1. Marked `[NEEDS SOURCE]`.

A3. Section 2.2, last paragraph, "`pyzx_angle_err` column, at most 2.2e-16 x pi on family A". `[F]` Recomputed: max of `pyzx_angle_err` over `results/family_A_counts.csv` is 1.48e-10 rad, which is 4.7e-11 x pi (`pipelines/compile.py:pyzx_angle_rounding` returns radians). 2.2e-16 is machine epsilon and appears nowhere in the CSV. Marked `[NEEDS SOURCE]`.

A4. Section 2.5, paragraph 3, `[PENDING: certificates]`, and Section 3.2 and 3.3 `[PENDING: certificates]`, and Section 5 scripts table "Certificates `[PENDING: certificates]`". `[F]` `results/certificates.csv` (24 rows: 20 family B2, 4 family B1 at n = 5) and `results/certificates.md` exist in the repository (commit 6cd21b6) and `claude/status-2026-10-07.md` item 4 reports them as done (floor <= T_zx on all 24 rows, B2 floor/T_zx 99.28 % or above per instance). The report says the certificates are not yet measured. The pending markers are stale against the artifacts. Not changed (a claim). The author should either inject a Table C from `results/certificates.csv` or state why the rows are withheld.

A5. Section 3.1, Table A4 and the paragraph after it, "It is being rerun with the published H2-2E parameters and will be replaced", and Section 6 "Table A4 is a local proxy with data-sheet parameters". `[F]` `results/family_A_proxy_h22e.csv` (540 rows, 108 circuits x 5 pipelines) and `results/family_B1_proxy_h22e.csv` exist, and `claude/status-2026-10-07.md` items 2 and 3 report the H2-2E-parameter rerun as done. `make_tables.py:family_a_proxy` still reads `family_A_proxy.csv` (data-sheet parameters, `noise/h2_params.py:H2_TYPICAL`, p1 = 3e-5, p2 = 1.5e-3). The table and the text are stale against the rerun. Not changed (numbers). Fix: point `family_a_proxy` at `family_A_proxy_h22e.csv` and rewrite the caption, or keep A4 and add the H2-2E rows.

A6. Section 3.1, paragraph after the figure, "P1, P3 and P4 are worse than P0 on all 180 circuits by factors between 1.19 and 10.36". `[F]` Table A2 in the same section gives min ZZ ratio 1.28 (P1), 1.31 (P3), 1.44 (P4) and max 10.36 (P4). Recomputed from `family_A_counts.csv`: 1.278 to 10.364. The value 1.19 is the max ratio of P2 and the min of the pre-regeneration xxz rows quoted in `claude/status-2026-10-07.md`. Marked `[NEEDS SOURCE]`.

A7. Section 3.2, "The T-counts after the ZX stage reproduce the published PyZX values." `[F]` No reference in the report gives these values. The four numbers (15, 8, 24, 166) are not in `papers/` or `docs/`. Marked `[NEEDS SOURCE]`. Fix: cite Kissinger and van de Wetering, "Reducing the number of non-Clifford gates in quantum circuits", Phys. Rev. A 102, 022406 (2020), after checking the table there.

A8. Section 6, paragraph 1, "P1, P3 and P4 are above P0 on every family A circuit and on 13 or 14 of the 15 family B1 circuits". `[F]` Recomputed from `family_B1_counts.csv`: P1 above P0 on 13 of the 14 circuits it completed (hwb8 timed out), P3 on 14 of 15, P4 on 15 of 15. "13 or 14 of the 15" is wrong for P1 (denominator 14) and for P4 (15 of 15). Marked `[NEEDS SOURCE]`.

A9. Scoring map, "Remaining criteria, 20 %, Not published by the organisers at the time of writing". `[F]` `claude/grand-challenge-plan.md` section 1 says the remaining 20 % and the rubric wording are in `sgc_scoring_brief.pdf`, which the team has but is not in the connected folder, and that the rubric is readable by GraphQL with the Aqora token. The criterion exists and has not been read, which is not the same as not published. Marked `[NEEDS SOURCE]`.

A10. References 1 and 2, arXiv:2608.22801 and arXiv:2608.22810. `[F]` Neither number appears in `papers/barrier/main.tex`, `papers/skzx/DeSilva-SK-ZX-QIP.tex`, `README.md` or `docs/`. Unverifiable from the repository. Not changed.

### Minor

A11. Preamble, "Every number in a table is produced by `report/make_tables.py`". `[F]` The pipeline table (2.2), the environment table and the scripts table (Section 5) and the team table (Section 7) are typed by hand. Only the six marked blocks in Section 3 are injected. Fixed in place to "Every number in a results table of Section 3".

A12. Section 1, paragraph 5, tagged `[F]`: "The team's manuscript on the exactness barrier (Kam, arXiv:2608.22801) gives that floor per instance." The theorem content is traceable to `papers/barrier/main.tex` (thm:B line 1813, cor:cert line 2568, thm:C line 2662). The arXiv number is Unverifiable (A10).

A13. Section 1 uses C for the shot count and Section 2.5 uses C for the circuit and C^ for its channel. Symbol clash. Not changed (notation from the manuscript). Fix: write the shot count as C_shots or the circuit as W.

A14. Section 2.3, paragraph 2, tagged `[F]`: "Emulated fidelity will be the Hellinger fidelity ..." is a plan, not a verifiable fact, and `[PENDING: emulator]` follows it. Tag not changed (tags are out of scope). Suggest `[O]` or no tag.

A15. Section 2.5, paragraph 3, tagged `[O]`: "The certificate is applied to family B1 at n = 5 and to family B2, where the 4^n x 4^n channel is small." This is a description of what was computed, so `[F]` fits once the certificate rows are in the report. Tag not changed.

A16. Section 4, Models (a), "p_meas" is not defined in the report. Platform notes section 3.3 gives p_meas = (9e-4, 1.8e-3) for H2-2E. Fix: define it at first use.

A17. Section 5, Tests list: the paragraph "The compile tests check every pipeline ..." was glued to the last bullet. Fixed in place (blank line).

A18. Section 7, every role is `[TBD]`. A judge reads this table. Not changed.

A19. Section 2.1, family B1, "its T-count is the literature value, for example tof_3 = 21 and mod5_4 = 28" has no citation. The manifest supports the counts, not the word "literature". Minor, left as is (A7 covers the citation).

## B. Prose-rule violations (quoted phrase, section, rule)

B1. Section 1, paragraph 4, "The second cost layer is not visible on H2 at all." Emphatic tail. Fixed: "The second cost layer is invisible on H2."

B2. Section 1, paragraph 4, "The ledger needs both columns." Short sentence used as a beat. Fixed: merged into the preceding sentence.

B3. Section 2.2, pipeline table, P0 row, "This is the baseline." Beat with a placeholder subject. Fixed: "P0 is the baseline."

B4. Section 2.4, paragraph 1, "Every compiled circuit is checked against ... : the unitary deviation ... for n <= 8 and the statevector infidelity on |0...0> beyond, with tolerance 1e-8, plus the maximum difference ..." One sentence carrying three checks and a colon. Fixed: split into three sentences.

B5. Section 2.5, paragraph 4, "One point needs stating." Beat. Fixed: merged with the sentence before.

B6. Section 2.5, paragraph 4, "the "reduction fires exactly once" half of that lemma was found to fail on the word T T". Passive with no agent. Fixed: "the implementation found that the ... half of that lemma fails on the word T T".

B7. Section 3.1, after the figure, "The factor grows with n." Short sentence used as a beat. Fixed: merged into the preceding sentence.

B8. Section 3.1, after Table A4, "It is being rerun ..." Pronoun opener. Fixed: "The proxy is being rerun ...". Content stale, see A5.

B9. Section 3.3, paragraph 3, "the certificate quantifies "near"". Scare quotes carrying the point. Fixed: "and the certificate measures how near."

B10. Section 4, paragraph 1, "This section is a protocol." Placeholder subject. Fixed: "Section 4 is a protocol."

B11. Section 4, "What the model is for. Predicting which pipeline to run before spending HQCs, and giving the rewriting search a cost signal once learned rewriting is attempted." Sentence fragment. Fixed: "Use. The model predicts which pipeline to run before HQCs are spent, and later gives the rewriting search a cost signal once learned rewriting is attempted."

B12. Section 6, paragraph 2, "This is the right control, because ..." Placeholder subject. Fixed: "The Trotter family is the right control, because ...".

B13. Section 6, paragraph 6, "It is reported for the other five pipelines only." Pronoun opener. Fixed: "hwb8 is reported ...".

B14. Section 6, paragraph 7, "Five circuits per row in Table B2 against 50 and 8 in the manuscript." Fragment. Fixed: "Table B2 has five circuits per row against 50 and 8 in the manuscript."

Mechanical hits checked and kept: "therefore" (Section 1 paragraph 3, Section 2.1) is a logical connective and not on the author's list. "exactly one ZZPhase" (3.1) and "preserves its unitary exactly" (2.5) carry mathematical content. "only" in "scores only ZZPhase count", "only moves phases", "P0 and P2 only" is restrictive, not emphatic. "does not" in "does not depend", "does not extract" is plain negation. Set lists with more than two commas ({4, 6, 8, 10, 12}, the gate set, the pipeline stages) are allowed by the rule. "Three models: ..." (2.1) introduces a plain list. Parentheses in the text are term glosses and cross-references. No semicolons, em-dashes, hedge adverbs, "rather than" or praise words were found.

## C. Scoring axes

Problem and value (30 %). Section 1 carries the problem (one number to minimise on H2, the invisible T layer, the floor) and Section 6 the limits. Artifact a judge would open: `docs/platform_notes.md` sections 3.3 and 3.4 for the HQC formula and the noise parameters, and `papers/barrier/main.tex` for the floor theorem. The "value for Quantinuum users now" claim has no artifact beyond the tables in Section 3.

Technical performance and hardware use (30 %). Section 3 carries the count tables and Section 5 the reproduction path. Artifacts: `results/family_A_counts.csv`, `results/family_B1_counts.csv`, `results/family_B2_counts.csv`, `results/compiled/<pipeline>/*.qasm`, `report/make_tables.py`. Hardware use has no artifact: no emulator or hardware job has run, Table A4 is a local proxy, and `report/notebook_skeleton.py` has no emulator cell with output. This axis is half empty at the time of the draft.

Scientific merit (20 %). Section 2.5 carries the certificate and Section 3.3 the rigidity result. Artifacts: `barrier/certificate.py`, `barrier/test_certificate.py` (24, 1536, 18384 reproduced, `[F]` lines 214, 275, 320), `barrier/NOTES.md` section 8 (the Lemma mqval(b) discrepancy), `results/certificates.csv` and `results/certificates.md`. The report does not yet show the certificate rows (A4), so a judge reading the report alone sees the method without its output.

Remaining criteria (20 %). No section is assigned. The criterion text is in `sgc_scoring_brief.pdf`, which is not in the repository (A9). No artifact. Sections 4 and 7 are named as candidates, and both are empty of results (Section 4 is a protocol, Section 7 is all `[TBD]`).

## D. Figures (read as images before and after the change)

fig_A_zz_ratio.png. Before: legend used bare codes P0ref, P1 to P4 with no expansion, the reference P0 was not named in the legend, the dashed line at ratio 1 was unlabelled, the title used the "Family A: clause" colon form, and the end-of-line annotations duplicated the legend. The y range 1 to 10.4 spans one decade, so the linear axis stays. After: legend spells out each pipeline once, the dashed line is labelled as P0 (pytket L2), the annotations are removed, the title is one sentence. Caption added under the figure in the report.

fig_B1_zz.png. Before: y axis linear from 0 to 300, so the n = 5 circuits (14 to 28 ZZPhase gates) are unreadable next to grover_5 (288). The title used the colon form. Colours match the other figures through `COLOR`. After: log y axis with ticks at 10, 20, 50, 100, 200, 300, title in one sentence. Caption added.

fig_B2_t.png. Before: labels, legend and units were sufficient. The title used the colon form, and the x tick labels wrote "eps" for the synthesis precision. After: title in one sentence, x labels "n = 2, eps = 1e-5" kept with spaces. Caption added.

## E. Changes made in the second pass

Text fixes B1 to B14 and A11, A17 as listed. `[NEEDS SOURCE]` markers inserted at A1, A2, A3, A6, A7, A8, A9. No number, table block, tag or claim was altered. Figure code changed in `report/make_tables.py` as in section D, `python report/make_tables.py` re-run, tables re-injected byte-identical to the previous ones.
