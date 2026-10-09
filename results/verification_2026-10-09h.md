# Verification 2026-10-09h: submission checklist package

Independent verifier. Repository `/home/claude/sgc-zx`, HEAD `54e85d5`. Package `submission/`. Checklist source: organisers' "SUBMISSION CHECKLIST" and "FAQS" (criteria.txt). No tracked file was edited. `[F]` = checked against files or recomputed, `[O]` = judgement.

## Verdict

**PASS WITH ISSUES.**

`[F]` Every number in `report/one_page_summary.md` was found in the sources and recomputed from the CSV/JSON inputs where inputs exist. All matched. The emulator job counts and the HQC sum match. Every job ID in `EVIDENCE.md` is in the ledger. `code.zip` holds no credentials. The two README commands that were run work from the unzipped tree. The three wording changes in `0e3d54f` match the data.

`[O]` No finding blocks submission. Two Medium items concern the code package: a README run command that the zip cannot run, and an evidence reference to logs that are not shipped. The other items are Low.

## Checklist table

| Checklist item | Status | File(s) | Note |
|---|---|---|---|
| Code package: working source code in the challenge workspace | Satisfied for the zip. Upload is Unverifiable | `submission/code.zip` (2423 files, `git archive` of `0e3d54f` minus `submission/`) | `[F]` The local repo has no git remote. Whether the code is in the Aqora workspace or a shared repo cannot be checked from here. |
| Code package: README with run instructions | Satisfied, weak | `submission/README.md` (= `README.md` in zip) | `[F]` Commands 2 and 5 work. Command 3, `bash submission/run_tests.sh`, fails in the zip tree (F1). Stale lines: F3, F6. |
| Code package: dependencies and configuration | Satisfied, weak | `submission/requirements.txt`, README "Configuration" | `[F]` All 19 pins match the installed versions. `mqt-qcec` is imported but not pinned (F4). |
| Execution evidence: job IDs, logs, outputs, plots | Satisfied | `submission/EVIDENCE.md`, `results/emulator/*/*/*.json`, `results/emulator_jobs.csv`, `report/notebook_executed.html` | `[F]` 18 H2-2E jobs (5933.2 HQC est.), 3 completed H2-Emulator jobs with 22 rows, 2 H2-2SC jobs. The cited logs are missing (F2). |
| Execution evidence: representative results | Satisfied | `report.pdf` Tables E2/E3, `results/emulator_nexus_H2-*.csv`, `EVIDENCE.md` F_H column | — |
| One-page summary in Word/PPT/PDF | Satisfied | `submission/one_page_summary.pdf` | `[F]` `pdfinfo` Pages: 1, A4. Rendered at 110 dpi. No text is clipped, all text is readable, and the page is about 70 % filled. The PDF numbers equal the md numbers (set difference empty). |
| Summary: problem statement and approach | Satisfied | `one_page_summary.pdf` "Problem statement", "Approach" | — |
| Summary: key results and relevance to quantum computing | Satisfied | "Key results", "Relevance to quantum computing" | Precision issues F5, F7, F8. |
| Summary: potential impact | Satisfied | "Potential impact" | USD figures tagged `[O]`. Recomputed below. |
| FAQ 13: Aqora workspace, GitHub repo or zip with source | Satisfied | `code.zip` | — |
| FAQ 13: source code repository | Unverifiable | — | `[F]` `git remote -v` is empty in `/home/claude/sgc-zx`. |
| FAQ 13: written report | Satisfied | `report.pdf` (from `report_short.md`), `report_full.pdf` | — |
| FAQ 13: evidence of hardware utilization | Not satisfiable in phase 1. Emulator evidence given | `EVIDENCE.md` | `[F]` No hardware run, stated in the summary and in EVIDENCE.md. `[O]` Hardware access opens to finalists on 21 Oct, so emulator use is the only possible evidence now. |
| Final verification: Publish, Submit to Track, confirmation | Pending / Unverifiable | — | These are portal actions outside the package. |

## Findings

Ordered by severity, then by file.

**F1. Medium. `README.md` line 10.** `[F]` The "Running the solution" block lists `bash submission/run_tests.sh`. `code.zip` excludes `submission/` (`build.sh` line 86, `':(exclude)submission'`). Run from the unzipped tree it gives `bash: submission/run_tests.sh: No such file or directory`. `run_tests.sh` ships only as a loose file in the submission folder. Proposed fix: either drop the exclusion for `run_tests.sh`, or say in the README that the script sits next to `code.zip`, or list the pytest/script commands directly.

**F2. Medium. `results/EVIDENCE.md` (= `submission/EVIDENCE.md`) line 94.** `[F]` It reads "Logs: `results/emu_*.log`, `results/fetch_*.log`." Those files exist only in the local working tree. They are ignored by `.gitignore` line 4 (`*.log`), so they are in neither `code.zip` nor `submission/`. Only `results/proxy_h22e_fits.log` is tracked. A judge who follows this reference finds nothing. `[O]` The project rule that nothing lives only in a container is also not met for these logs. Proposed fix: un-ignore and commit the emulator and fetch logs, or remove the line from `submit/evidence_index.py`.

**F3. Low. `README.md` line 37.** `[F]` The layout row for `report/notebook_skeleton.py` says "gated submission to `nexus:H2-2E` through `aqora.QPU`". The notebook (`PLATFORM = "nexus:H2-2SC"`, `require_free_checker`) and README lines 15, 87 and 124 say it submits only to platforms ending in `SC`. Proposed fix: "gated submission to the free `nexus:H2-2SC` syntax checker".

**F4. Low. `requirements.txt`.** `[F]` `pipelines/equiv_family_C.py` line 309 imports `mqt.qcec`. Its default `--methods` (line 489) is `pyzx,qcec_zx,qcec_alt`. `mqt-qcec` 3.10.2 is installed here but is not pinned in `requirements.txt`, so the default run of the family C equivalence script fails in an environment built from the file. Proposed fix: add `mqt-qcec==3.10.2` to the optional block.

**F5. Low. Rounding of the worst-instance bound in the favourable direction.** `[F]` The minimum floor / T_after_ZX is 2478/2496 = 0.992788 (haar_n3_eps1e-03_s5). The worst-instance gain bound is therefore 0.721 %.
- `report/one_page_summary.md` line 19 says "at most ... 0.7 % on the worst instance".
- `report_short.md` line 99 and `report_v5.md` lines 124 and 176 (`sec1_v5.md` lines 107 and 159) say "at most 0.7 %". The 99.28 % added in `0e3d54f` reads "at least 99.28 %".

An upper bound rounded down (0.721 to 0.7) and a lower bound rounded up (99.2788 to 99.28) both read as slightly stronger than the data. `report_short.md` line 248 already uses 0.72 %. The pooled values are safe: 0.2889 % ≤ 0.3 % and 99.711 % ≥ 99.7 %. Proposed fix: "0.72 %" and "99.27 %" (or "99.28 % rounded").

**F6. Low. `README.md` lines 96, 107, 124, 128.** `[F]` Line 96 says "Six run as scripts" and line 107 says "Five run under pytest". `submission/build_logs/tests_summary.txt` runs 21 test files. The missing ones include `test_pass_select`, `test_evidence_index`, `test_equiv_family_C`, `test_official_baseline` and `test_finals_plan`. Line 124 says `TEAM_ORG` is read "in the second cell", but it is set in the third `@app.cell` (line 130 of the notebook). Line 124 omits the second way to open the gate, `SGC_NOTEBOOK_SUBMIT_SC=1`. Line 128 gives an unpinned `pip install` that differs from `requirements.txt`. Proposed fix: point the Tests and Environment sections to `run_tests.sh` and `requirements.txt`.

**F7. Low. `one_page_summary.md` line 19, "certified-incompressible fraction is 0.997 pooled".** `[F]` 0.997 is floor / T_after_ZX = 41,414 / 41,534 = 0.99711. This matches the definition in `value/value_ledger.md` line 46 ("of the remaining T-count"). The column `certified_incompressible_fraction` in `results/certificates.csv` has the same name but is floor / T_written, and its pooled value is 0.977. The summary also omits that the 20 Haar circuits have n = 2 and 3. Proposed fix: "certified-incompressible fraction of the T-count left after ZX is 0.997 pooled (n = 2, 3)".

**F8. Low. `one_page_summary.md` line 11, "proves the PSEL output equal to its input on 18".** `[F]` For three of the 18 (draper_adder_10, draper_adder_16, rgqft_mult_6), PyZX proves equality of the angle-snapped compiled circuit. The largest snap is 5.27e-12 half-turns (`results/family_C_equivalence.md`, Method). For the 15 circuits without continuous angles the snap is 0, so "all 15 ... proven" (line 15) is exact. Proposed fix: add "(3 of them after snapping angles by at most 5.3e-12 half-turns, App. 3.8)" or leave it to App. 3.8.

**F9. Low. `one_page_summary.md` line 24, "The circuits PSEL saves most on are arithmetic and oracle subroutines".** `[F]` On B1, hwb8 carries 84.5 % of the PSEL saving. `report_short.md` line 57 states that hwb8 "serves no sourced quantum algorithm". The sentence holds for family C, where the multipliers and adders lead, but not for B1. Proposed fix: "On family C the circuits PSEL saves most on ...".

**F10. Low. `one_page_summary.md` lines 20 and 30.** `[F]` "18 H2-2E jobs (5933.2 HQC)" is the sum of formula estimates stored in the payloads, not a billed figure. EVIDENCE.md and report_v5 line 154 say "HQC estimates". The finals line "4364 shots per pipeline ... for power 0.80" is computed at the measured H2-2E gain of +0.0108. The summary leaves that assumption out (`value/finals_plan.md` lines 12–18 state it). Proposed fix: "(5933.2 HQC estimated)" and "for power 0.80 at the emulator-measured gain".

**F11. Low. `submission/REPRODUCE.md` line 3.** `[F]` It says "`code.zip` is `git archive` of commit `0e3d54f…`". The archive is that commit minus `submission/` (40 files). `MANIFEST.txt` line 1 states the exclusion and REPRODUCE.md does not. Proposed fix: append "(submission/ excluded)".

**F12. Low, tag. `one_page_summary.md` line 20.** `[F]` The sentence "The fidelity gain is not established at 0.05 after correction" is tagged `[O]`. Given the Holm-adjusted p of 0.0518 it is checkable, so `[F]` would fit. The same tagging is used in report_short.md line 233. `[O]` This is optional.

### Checked and correct (no finding)

- `[F]` Family C, recomputed from `value/family_C_selector.csv` and `bench/family_C/manifest.csv`:
  - The 15 circuits without continuous angles are 9 adders and 6 MCX. P0 total 10,019.6, saved 748.4 HQC, 7.469 %. Adders 12.906 %.
  - All 20: saved 4104.4 HQC, 16.729 %. The two multipliers' share is 81.77 %.
  - PSEL pick proven: 18/20. Without continuous angles: 15/15. The unproven ones are hrs_mult_5 (inconclusive) and draper_adder_28 (timeout), both with continuous angles.
- `[F]` Family A from `results/family_A_counts.csv`: P2 is +1030.4 HQC (6.274 %). PSEL avoids 1076.4 against P2 and saves 46.0 against P0.
- `[F]` QFT adders: P2 − P0 = 1057.2 HQC (22.125 %).
- `[F]` B1 from `results/family_B1_counts.csv`: saved 743.6 HQC (4.792 %), median 3.937 %, hwb8 share 84.53 %. T-count 7048 to 4186 (40.607 %). The largest n is 12.
- `[F]` Grover use case (`value/usecase.csv`): 5.42 % and 4.96 %, +791 and +322 shots, on 7 and 9 qubits.
- `[F]` B2 certificate: pooled 0.99711. Minimum 0.992788.
- `[F]` 445 official-baseline rows = 180·2 + 15 + 14 + 8·2 + 20·2. All are identical in `results/official_baseline.md`, and hwb8/P2off timed out.
- `[F]` USD figures:
  - 748.4 × 10.294 = 7,704 and 748.4 × 12.50 = 9,355, so "7,700 to 9,400".
  - 1076.4 gives 11,081 and 13,455, so "11,100 to 13,500".
  - 125,000/10,000 = 12.50 and 175,000/17,000 = 10.294.
- `[F]` Finals plan, from `value/finals_plan.compute()`: shots_80 raw 4363.35, ceiling 4364. HQC 644.76 + 502.50 = 1147.26.
- `[F]` Pooled vbe_adder_3, recomputed directly from the eight JSON payloads:
  - P0 3808/4000 = 0.9520 and P2 3851/4000 = 0.96275, so dF = +0.01075 and sd = 0.004515.
  - z = 2.381 and two-sided p = 0.01728.
  - Holm over two circuits (with grover_5 p at z 0.10): 0.0346. Over three (adding hwb6 p = 0.225): 0.0518.
- `[F]` "Nothing has run on hardware": every payload platform is `nexus:H2-2E`, `nexus:H2-Emulator` or `nexus:H2-2SC`.
- `[F]` The pytket 2.18.4 `ZXGraphlikeOptimisation.__doc__` contains "may increase the cost of the circuit".
- `[F]` arXiv IDs looked up through the arXiv API:
  - 2608.22801 is "An Exactness Barrier for ZX-Calculus Optimization of Synthesized Clifford+T Circuits" (Kam et al.).
  - 2012.03819 is Chakrabarti et al., derivative pricing.
  - 1808.02892 is Litinski, "A Game of Surface Codes".
- `[F]` App. anchors: 1.2 has the HQC formula (report_v5 line 57), 2.2 has the 445 rows (line 210), 3.8 has the family C proofs, 6 has the finals plan.

### Task 3: EVIDENCE.md recomputation

- `[F]` There are 52 JSON payloads under `results/emulator/*/*/`.
- `[F]` H2-2E: 18 payloads, all with counts summing to shots (1000). 18 distinct job IDs. HQC estimate sum 5933.2.
- `[F]` H2-Emulator: 32 payloads. 22 have counts summing to shots, spread over 3 job IDs (`…9nXyFL_A` 10 rows, `…oHj_0khA` 10 rows, `…cR7Af3ZA` 2 rows), with HQC est. 2127.6. The other 10 payloads share the failed job `…RRv_BIzw` and have no counts. `results/emulator_nexus_H2-Emulator.csv` has 22 data rows.
- `[F]` All 24 real job IDs in EVIDENCE.md are in `results/emulator_jobs.csv`. The regex also matched one truncated status string, `AFByb3ZpZGVySm9iAaE`, which is not an ID. The ledger has 53 rows: 42 COMPLETED, 10 FAILED, 1 SUBMIT_ERROR. All 42 completed result paths exist, and each payload job_id equals its ledger job_id.
- `[F]` Running `python3 submit/evidence_index.py` in the unzipped copy regenerates a byte-identical `results/EVIDENCE.md`, which also equals `submission/EVIDENCE.md`.

### Task 4/5: code.zip

- `[F]` The zip comment is `0e3d54fa48bfba1f4be1c7d83f83e991403fe8e4`. `diff -r` against `git archive 0e3d54f` shows one difference, `Only in arch: submission`. All other files are identical in content.
- `[F]` HEAD `54e85d5` changes only files under `submission/` relative to `0e3d54f`.
- `[F]` Credentials:
  - No `credentials.json`, `*.token`, `.env`, `*.pem` or `*.key` file.
  - `grep` for `refresh_token|access_token` finds only schema descriptions in `docs/platform_notes.md` lines 75–84.
  - No JWT-shaped strings and no `ghp_`/`sk-`/`AKIA` strings.
- `[F]` `pip list` versions equal all 19 pins in `requirements.txt` (Python 3.13.16).
- `[F]` From the unzipped tree:
  - `python3 pipelines/pass_select.py bench/family_B1/vbe_adder_3.qasm` prints P2, 119.0 HQC (P0 151.6, n2q 56 to 41) in 3 s.
  - `python3 -m pytest submit/test_evidence_index.py -q` gives 3 passed.
  - `report/test_notebook_submit.py` gives 20 passed.
  - `pipelines/test_pass_select.py` passes all.
  - `bash submission/run_tests.sh` fails (F1).

### Task 6: wording changes in 0e3d54f

- `[F]` hwb6, from `submit/h22e_stats.compute()` and the payloads: F_H 0.9240 (P0) and 0.9090 (P2), dF = −0.0150, sd 0.012367, z = −1.2129. HQC est. 243.0 (P0) and 232.6 (P2), so P2 is cheaper. The text is correct.
- `[F]` "at least 99.28 % on every single circuit": the minimum is 0.992788 (haar_n3_eps1e-03_s5, 2478/2496). The value is correct to two decimals but rounded up in an "at least" claim (F5).
- `[F]` "six papers of Appendix Section 3.4": `results/literature_tcounts.csv` has six distinct arXiv IDs (1303.2042, 1601.07363, 1710.07345, 1712.01557, 1903.10477, 2402.14396). Correct.
- `[F]` The change from "the ZX stage pays" to "lowers the HQC" is consistent with PSEL's HQC criterion.

## Commands run

```
git log --oneline; git status --short; git remote -v
pdfinfo submission/one_page_summary.pdf; pdftoppm -r 110 -png ...; pdftotext -layout ...; pdffonts ...
python3 (csv) recomputation of family C, A, B1, B2-certificate, QFT-adder numbers from results/*.csv, value/*.csv, bench/family_C/manifest.csv
grep -F of each summary number in report/report_v5.md, report/report_short.md, value/*.md, results/*.md
python3 report/check_short_numbers.py report/one_page_summary.md   # 66/66 found
python3 submission/check_summary_numbers.py                         # 137/137 found
python3 -c "import finals_plan; finals_plan.compute()"               # shots_80 4364, HQC 1147.26
python3 -c "import h22e_stats; h22e_stats.compute()"                # hwb6 z -1.2129
python3 (json) pooled vbe_adder_3 F_H, z, Holm from results/emulator/nexus_H2-2E*/
python3 (json, csv) payload/ledger cross-check for EVIDENCE.md
curl export.arxiv.org/api/query?id_list=2608.22801,2012.03819,1808.02892
unzip code.zip -> scratchpad/vh/unz; unzip -z; git archive 0e3d54f | tar -x; diff -r -q
find/grep for credential files and token strings in the unzipped tree
python3 -c importlib.metadata versions vs requirements.txt; pip list
(in unzipped tree) python3 pipelines/pass_select.py bench/family_B1/vbe_adder_3.qasm
(in unzipped tree) python3 -m pytest submit/test_evidence_index.py -q
(in unzipped tree) python3 -m pytest report/test_notebook_submit.py -q; python3 pipelines/test_pass_select.py
(in unzipped tree) bash submission/run_tests.sh                    # fails: file not in zip
(in unzipped tree) python3 submit/evidence_index.py; diff with submission/EVIDENCE.md
git show 0e3d54f --word-diff -- report/
python3 -c "from pytket.passes import ZXGraphlikeOptimisation; print(ZXGraphlikeOptimisation.__doc__)"
```
