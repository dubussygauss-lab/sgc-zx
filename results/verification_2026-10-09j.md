# Verification 2026-10-09j: H2-2E family C run (vbe_adder_7), report integration, presentation, submission package

Verifier: independent agent that did not produce the work. Repository `/home/claude/sgc-zx`, HEAD `84ba731`, compared with `9193bc3`. Date 9 October 2026.

## Verdict

**PASS WITH ISSUES.** [F] Every number of the vbe_adder_7 run recomputes from the payloads and from an independent simulation. The H2-2E totals, the code.zip, the one-page summary and the test suite all check out. [F] One `[F]` sentence in the appendix limitations is now false ("No family C or use-case circuit ran on an emulator."). Two unqualified "Family C is count-only." sentences contradict the new Table 3c / E4 in the same documents.

## 1. Data recomputation (vbe_adder_7, H2-2E)

All numbers below were recomputed by the verifier's own code. The repo's simulator, `h22e_stats` and `evidence_index` were not used.

| Quantity | Claimed | Recomputed | Status |
|---|---|---|---|
| Counts sum, P0 / P2 | 1000 / 1000 | 1000 / 1000 (49 and 59 distinct 22-bit keys) | [F] OK |
| Ideal output of `bench/family_C/vbe_adder_7.qasm` on all-zero input | one basis state | qiskit 2.5.2 `Statevector`: only `0...0` nonzero, p = 1 - 1.7e-14 | [F] OK |
| F_H P0 / P2 | 0.886 / 0.897 | 886/1000 = 0.886, 897/1000 = 0.897 (single-outcome reference, so F_H = p_hat; bit order irrelevant) | [F] OK |
| Binomial sd P0 / P2 | 0.0101 / 0.0096 | 0.010050 / 0.009612 | [F] OK |
| dF, sd, z | +0.0110, 0.0139, 0.79 | +0.011000, 0.013907, 0.7910 (two-sided p 0.43) | [F] OK |
| Job IDs in `results/emulator_jobs.csv` | COMPLETED | both rows present, status COMPLETED, platform nexus:H2-2E, options `{"noisy_simulation": true}`, shots 1000. Payload `job.payload.status` COMPLETED, platform name H2-2E | [F] OK |
| HQC P0 | 370.4 | compiled `results/compiled/P0/vbe_adder_7.qasm`: 187 U1q, 142 RZZ, 16 rz, 22 measure. 5 + 1000(187 + 1420 + 5*44)/5000 = 370.4 | [F] OK |
| HQC P2 | 294.4 | compiled P2: 157 U1q, 107 RZZ, 15 rz, 22 measure. 5 + 1000(157 + 1070 + 220)/5000 = 294.4 | [F] OK |
| 35 fewer two-qubit gates | 35 | 142 - 107 = 35 | [F] OK |
| 76.0 HQC less | 76.0 | 370.4 - 294.4 = 76.0 | [F] OK |
| Two jobs | 664.8 | 664.8 | [F] OK |
| H2-2E grand total | 20 jobs, 6598.0, 3402.0 left | 20 payloads with counts = shots and no error, 20 distinct job IDs, 6598.0 HQC, 3402.0 left. All 20 job IDs are COMPLETED ledger rows. Ledger has 20 H2-2E rows, all COMPLETED | [F] OK |
| Tables E2/E3 inputs | 18 jobs, 5933.2 | dirs nexus_H2-2E (6 jobs, 1840.0) + _r2/_r3/_r4 (4 each, 1364.4 each) = 18 jobs, 5933.2. `git diff 9193bc3 84ba731` on those payload dirs, their CSVs, `h22e_stats.py` and `h22e_pooled.py` is empty | [F] OK |
| "ideal output probabilities differ ... by at most 1.02e-14" | 1.02e-14 | CSV `ideal_vs_ref_maxdiff` 5.33e-15 (P0), 1.02e-14 (P2), max = 1.02e-14. Own numpy simulation of the compiled hqslib1 circuits gives p(0...0) within 4.9e-15 (P0) and 2.7e-15 (P2) of 1, all other probabilities ~0 | [F] consistent. The exact value depends on the simulator |
| Ledger "11 of 55 rows" (EVIDENCE.md) | 11 of 55 | 55 rows, 11 not COMPLETED | [F] OK |
| Table C3 row vbe_adder_7 | P0 370.4, P2 294.4, PSEL P2, n_2q 142/107 | `results/family_C_counts.csv`: same values, so the P2 run is the PSEL output | [F] OK |

## 2. Findings

Ordered by severity, then document order.

### F1. Major. False `[F]` sentence in appendix limitations
- File: `report/report_v5.md` line 1081, copied to `submission/report_full.md` line 1081 and the rebuilt `submission/report_full.pdf`.
- Evidence: [F] The paragraph opens "Family C is count-only apart from one H2-2E run of vbe_adder_7 (Section 3.7.2)." and ends with "No family C or use-case circuit ran on an emulator." The last sentence was not updated and is contradicted by Section 3.7.2 / Table E4.
- Proposed fix: replace it with "No use-case circuit ran on an emulator. vbe_adder_7 is the only family C circuit that did (Section 3.7.2)." Then rebuild the submission.

### F2. Minor. Unqualified "Family C is count-only." in the main-report limitations
- File: `report/report_short.md` line 327 (identical in `submission/report.md` and `report.pdf`), Section 7 Limitations.
- Evidence: [F] The text reads "`[F]` Family C is count-only. The PSEL output is proven on 18 of its 20 circuits." The same document now reports the H2-2E run in the Summary ("count-only apart from one H2-2E run of vbe_adder_7"), at Table 1 (line 31) and in Table 3c.
- Proposed fix: "Family C is count-only apart from one H2-2E run of vbe_adder_7 (Table 3c)."

### F3. Minor. Unqualified "Family C is count-only." in SUMMARY.md
- File: `submission/SUMMARY.md` line 13.
- Evidence: [F] "`[F]` Family C is count-only. The PSEL output of every one of the 15 circuits ..." Line 69 of the same file now reports the vbe_adder_7 run.
- Proposed fix: as in F2.

### F4. Minor. Appendix limitations list the emulator runs without Section 3.7.2
- File: `report/report_v5.md` line 1073 (also `submission/report_full.md`).
- Evidence: [F] "The 22 H2-Emulator rows of Section 3.7 and the 18 H2-2E jobs of Section 3.7.1 are emulator runs." and "The emulator jobs of Sections 3.7 and 3.7.1 were submitted by `submit/syntax_check.py` and `submit/run_emulator.py`." The two Section 3.7.2 jobs are omitted. [F] The famC log shows that the P0 result was fetched later with `submit/fetch_job.py`. [O] The sentences are not false, but the list is incomplete.
- Proposed fix: "... and the 20 H2-2E jobs of Sections 3.7.1 and 3.7.2 are emulator runs." and "The emulator jobs of Sections 3.7 to 3.7.2 were submitted by ...".

### F5. Info. Section 1.5 emulator paragraph still gives only the 18-job total
- File: `report/report_v5.md` line 154.
- Evidence: [F] "The 18 H2-2E jobs carry HQC estimates that sum to 5933.2 HQC." This is true for Tables E2/E3. The section does not mention the 20-job total or the vbe_adder_7 run, although the family C sentences at lines 24, 43 and 148 now refer to it.
- Proposed fix (optional): add one sentence: "Two more H2-2E jobs ran vbe_adder_7 of family C (Section 3.7.2). All 20 jobs total 6598.0 HQC."

### F6. Info. "exercises every gate" wording
- File: `report/report_v5.md` Section 3.7.2, last `[O]` paragraph.
- Evidence: [F] "The all-zero input exercises every gate of the circuit but tests the adder on one input only." [O] Every gate is executed and subject to noise. On the all-zero input the Toffoli-type blocks act on zero controls, however, so "exercises" can be read as functional coverage. The second clause limits the claim.
- Proposed fix (optional): "executes every gate of the circuit".

### F7. Info. Hand annotations inside a run log; payload field asymmetry
- File: `results/emu_h22e_famC.log` lines 9 and 17. P2 payload `results/emulator/nexus_H2-2E_famC/P2/vbe_adder_7.json`.
- Evidence: [F] The bracketed lines "[runner stopped at 2026-10-09T17:08:10Z ...]" and "[fetch_job.py for P0 ...]" are interleaved with program output. [F] The P0 payload has `fetched_by_id: true` and the P2 payload lacks the key. `t_wait` is 3.1 s (P0) and 1021.4 s (P2). [O] The annotations are consistent with the ledger timestamps and do not change any result.
- Proposed fix (optional): add one line at the top of the log saying that bracketed lines are manual annotations.

### F8. Info. Test wall time
- File: `README.md` line 10 ("about 4 min").
- Evidence: [F] A fresh unzip of code.zip in this container gave a wall-time sum of 351 s over the 22 files (gen_trotter 126 s, usecase 52 s, certificate 49 s, famC_h22e 34 s). [O] This depends on the environment and is not an error.

## 3. Report text checks (item 2)

[F] Every new or changed sentence in `git diff 9193bc3 84ba731 -- report README.md submission/SUMMARY.md` about the run was checked against Section 1 of this file. The checked text covers report_v5 Section 3.7.2, Table E4, the Section 6 quota sentence (4066.8 before the run, 3402.0 after), report_short Table 3c and the paragraph after it, the H2-2E bullet (18 jobs 5933.2 = 59.3 %, 20 jobs 6598.0), one_page_summary (20 jobs, 6598.0, F_H 0.886 and 0.897, z = 0.79), the SUMMARY.md emulator paragraph, the README status line and the test counts (22 files, 7 scripts + 15 pytest). All numbers match. "count-only apart from one H2-2E run" is accurate: the run is the only family C execution in the ledger. [F] 59.3 % = 100 x 5933.2/10000 rounded. No overclaim was found in the new text beyond F6. The remaining issues are stale sentences outside the diff (F1 to F5).

## 4. Presentation (item 3)

- [F] `report/presentation/presentation.pdf` has 12 pages and is byte-identical to `submission/presentation.pdf`. The .tex files are identical too.
- [F] Every page was rendered at 50 dpi and inspected. No clipped or overflowing text, table or diagram is visible on any page. The low resolution limits the check to visible overflow.
- [F] `python3 report/check_short_numbers.py <pdftotext of deck>` from the repo root: "156 distinct numbers ..., 156 found in sources, 0 missing".
- [F] Own spot-check of 12 numbers against `results/family_C_counts.csv`, `results/family_A_counts.csv`, `requirements.txt` and arithmetic. All match:
  1. Slide 2: P2 costs 6.27 % more on 180 Trotter circuits (P0 16422.6, P2 17453.0, +1030.4).
  2. Slide 2: 22.1 % more on the 3 QFT adders (4778.4 to 5835.6, +22.12 %).
  3. Slide 2: draper_adder_16 costs 1,385.0 against 906.8.
  4. Slide 3: P2 raises the 60 XXZ circuits by 12.33 % (12.326 %).
  5. Slide 5: adders 5777.0 to 5031.4, saved 745.6, 12.9 %.
  6. Slide 5: multipliers 9737.0 to 6381.0, saved 3356.0, 34.5 %.
  7. Slide 5: all 20 circuits 24535.0 to 20430.6, saved 4104.4, 16.7 %.
  8. Slide 6: PSEL picks P2 on 57 of 180 and saves 46.0.
  9. Slide 10: 748.4 x 10.29 = 7,701 and x 12.50 = 9,355.
  10. Slide 10: 1,076.4 x 10.29 = 11,076 and x 12.50 = 13,455.
  11. Slide 11: 644.8 + 502.5 = 1147.3.
  12. Slide 12: `requirements.txt` pins 20 packages.

  Slide 9 vbe_adder_7 rows (142/107, 0.886/0.897, 0.0101/0.0096, +0.0110, z 0.79, 20 jobs 6598.0) match Section 1.
- [F] The slide claims were compared with the reports. "This submission contains no learned rewriting" (slide 11) is in report_short line 332. "Family C is count-only apart from one H2-2E run" matches report_v5. No new claim was found.
- [F] Slide 12 says "Runs 22 test files, seven as scripts and fifteen under pytest. All 22 return rc=0 from a fresh unzip of code.zip." The verifier unzipped `submission/code.zip` into an empty directory and ran `TEST_LOG_DIR=$PWD/tlogs bash run_tests.sh`. Result: 22 rows, 22 with rc=0, `done` written. famC_h22e: 6 passed. h22e_pooled: 10 passed. evidence_index: 3 passed. Confirmed.

## 5. Package (item 4)

- [F] `submission/one_page_summary.pdf`: `pdfinfo` gives Pages: 1. Its text contains the new 20-job, 6598.0 and vbe_adder_7 sentences.
- [F] `submission/REPRODUCE.md` line 3 names `a142c853f52f7b93760a23c11de2ae5678a58cd8`, which is the full hash of `a142c85`.
- [F] `git archive a142c85`, extracted with `submission/` removed, compared by `diff -r` with a fresh unzip of `submission/code.zip`: identical (2497 files). `git diff a142c85 84ba731` outside `submission/` is empty.
- [F] No credential files in code.zip: no `*.env`, `*credential*`, `*token*`, `*.pem`, `*secret*`, `id_rsa*` or `.netrc` files. A grep for `ghp_`, `github_pat_`, `sk-...`, `AKIA...`, JWT-shaped strings and private-key headers finds nothing. `refresh_token` and `access_token` appear only as schema field names in `docs/platform_notes.md` line 75 and in the earlier verification report quoting that.

## 6. test_h22e_pooled.py change (item 5)

[F] In 005a7d7, `test_hqc_sum` now skips payload directories whose name does not match `nexus_H2-2E(_r\d+)?`. Before the change the glob `nexus_H2-2E*` matched exactly `nexus_H2-2E`, `_r2`, `_r3` and `_r4`, which are the directories that `h22e_pooled.compute` reads (`nexus_H2-2E` plus `glob nexus_H2-2E_r*`, `submit/h22e_pooled.py` line 96). The filter therefore restores the pre-change set and keeps the same three assertions (completed HQC, submitted HQC, percentage). Without it the new famC directory would have entered only the test's sum. [F] `re` and `Path` are imported. [F] The 18-job / 5933.2 subset and the 20-job / 6598.0 total are pinned separately in `submit/test_evidence_index.py`. [O] The test is not weakened. A future directory such as `nexus_H2-2E_rX` would be read by `h22e_pooled` but skipped by the test, so the test would fail. That makes it stricter, not weaker.

## 7. Commands run

```
git log --oneline -8; git diff --stat 9193bc3 84ba731
git show 005a7d7 -- submit/common.py submit/test_h22e_pooled.py submit/run_emulator.py
git diff 9193bc3 84ba731 -- report README.md submission/SUMMARY.md results/EVIDENCE.md
git diff --stat 9193bc3 84ba731 -- results/emulator/nexus_H2-2E{,_r2,_r3,_r4} results/emulator_nexus_H2-2E{,_r2,_r3,_r4}.csv submit/h22e_stats.py submit/h22e_pooled.py   # empty
python3 v1.py   # qiskit Statevector of bench/family_C/vbe_adder_7.qasm on |0..0>, F_H, binomial sd, dF, z from payload counts
python3 v2.py   # own numpy simulator of results/compiled/{P0,P2}/vbe_adder_7.qasm (U1q, rz, RZZ)
grep/awk gate counts of results/compiled/{P0,P2}/vbe_adder_7.qasm; HQC = 5 + 1000(N1q + 10 N2q + 5*44)/5000
python3 (pandas) over results/emulator/nexus_H2-2E*/*/*.json and results/emulator_jobs.csv   # 20 jobs 6598.0, 18 jobs 5933.2
python3 (pandas) over results/family_C_counts.csv, results/family_A_counts.csv   # slide spot checks
pdfinfo report/presentation/presentation.pdf; cmp with submission/presentation.pdf
pdftoppm -r 50 -png report/presentation/presentation.pdf; pdftotext -layout ... pres.txt
python3 report/check_short_numbers.py pres.txt   # 156/156 found
pdfinfo submission/one_page_summary.pdf   # 1 page
git archive a142c85 | tar -x; rm -r submission; unzip code.zip; diff -r   # identical
find/grep credential patterns in unzipped code.zip
unzip code.zip -d <empty dir>; TEST_LOG_DIR=$PWD/tlogs bash run_tests.sh   # 22/22 rc=0
```

Scratch scripts and outputs are in the verifier's scratchpad, not in the repository.
