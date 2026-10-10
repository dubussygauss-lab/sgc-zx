# Verification 2026-10-10b: H2-2E non-zero-input run of vbe_adder_7 (P0 vs L3)

Independent verifier. Commits checked: f8367fe, da6a6cb, e47b71b, d5ec540 (and 60d2fa7, which carries the
`submission/` copies). No tracked file was edited. Recomputation used my own numpy 22-qubit statevector code
(not `bench/sv.py`, not `submit/h22e_famC_nz.py`).

**Verdict: PASS WITH ISSUES** (all numbers reproduce; two Minor stale sentences, two Info notes).

## 1. Pre-registration

- [F] `results/h22e_nonzero_prereg.md` was added in f8367fe, 2026-10-10 00:35:27 UTC, and never changed afterwards (`git log` on the file shows only f8367fe).
- [F] The ledger rows in `results/emulator_jobs.csv` are written at status SUBMITTING before `QPU.run` (`submit/h22e_famC_nz_run.py` `submit_only`): P0 00:38:19.37Z, L3 00:38:43.13Z. The run log `results/emu_h22e_famC_nz.log` gives submission at 00:38:43.04Z and 00:38:45.44Z, and the payload `createdAt` is 00:38:43.05Z and 00:38:45.45Z. All are after the pre-registration commit (gap 2 min 52 s to the first ledger row).
- [F] `numpy.random.default_rng(20261010).integers(1, 2**7, size=2)` returns [28, 111] (numpy, this container).
- [F] The X positions match the layout: a = 28 sets a_2, a_3, a_4 -> q[3], q[4], q[5]. b = 111 sets b_0..b_3, b_5, b_6 -> q[8..11], q[13], q[14]. `bench/family_C_nz/vbe_adder_7_nz.qasm` equals `bench/family_C/vbe_adder_7.qasm` plus exactly these nine `x` lines (diff, apart from a trailing newline).
- [F] The metric (count of `0001110011010001000000` / 1000, binomial sd, d, z) and the expected bitstring are fixed in the pre-registration.

## 2. Recomputation from payloads

- [F] Own simulation of `bench/family_C_nz/vbe_adder_7_nz.qasm`: a single basis state, probability 1 - 1e-14, string `0001110011010001000000` with character i = q[i]. This is the counts convention of `submit/common.py` `counts_to_probs` (character i = c[i]).
- [F] Decoding: q[1..7] read LSB-first gives a = 28 (unchanged). q[8..14] gives 11 = 139 mod 128. q[15] cout = 1 = floor(139/128). cin and helpers 0.
- [F] Counts sum to 1000 in both payloads. All keys have 22 bits. The expected string is the modal outcome in both.
- [F] P0: 883/1000 = 0.883, sd 0.0102. L3: 901/1000 = 0.901, sd 0.0094. Payload `F_H` agrees (0.883, 0.901).
- [F] d = +0.0180, sd 0.0139, z = 1.297 (rounds to 1.30).
- [F] HQC from the compiled QASM: P0 has 196 U1q, 19 rz, 142 RZZ, 22 measure. L3 has 126 U1q, 19 rz, 79 RZZ, 22 measure. With rz free and spam = 22 qubits + 22 measures: P0 5 + (196 + 1420 + 220)/5 = 372.2, L3 5 + (126 + 790 + 220)/5 = 232.2. Sum 604.4 (pre-registered limit 700).
- [F] Both job IDs are COMPLETED on nexus:H2-2E with `{"noisy_simulation": true}` in `results/emulator_jobs.csv` (rows 57, 58) and in the payload (`platform.name` H2-2E, `status` COMPLETED).
- [F] All H2-2E ledger rows: 22, all COMPLETED. Stored H2-2E payloads with valid counts: 22, 22 distinct job IDs, `hqc_estimate` sum 7202.4, 10,000 - 7202.4 = 2797.6.

## 3. Compiled circuits

- [F] Own simulation of `results/compiled/P0/vbe_adder_7_nz.qasm` (U1q, rz, RZZ in hqslib1 semantics; mid-circuit measures deferred, no gate acts on a qubit after its measure): single outcome, c-string `0001110011010001000000`, probability 1.0.
- [F] `results/compiled/L3/vbe_adder_7_nz.qasm` measures with a permutation (q[9]<->c[17], q[10]<->c[18], q[11]<->c[19], q[12]<->c[20], q[13]<->c[21]). After applying the measure map its single outcome is `0001110011010001000000`, probability 1.0. The qubit-order string alone (`0001110010000001010100`) differs, so any check that ignores the measure map would fail on L3.
- [F] `value/psel4_ledger.csv`: vbe_adder_7 `pick_PSEL4` = L3 (hqc_L3 = hqc_P2L3 = hqc_PSEL4 = 232.2). `status_L3` there is `ok-unchecked`, which concerns the all-zero bench circuit, not this run.

## 4. Findings

### F1. Minor. Stale "one H2-2E run" in the short report
- File: `report/report_short.md` line 31 (copied to `submission/report.md` line 31).
- Evidence: "Family C is count-only above 20 qubits, apart from one H2-2E run of vbe_adder_7 (Table 3c)". Table 3d now exists and every other edited location says "the H2-2E runs of vbe_adder_7 (Tables 3c and 3d)".
- Proposed fix: "apart from the H2-2E runs of vbe_adder_7 (Tables 3c and 3d)", then rebuild `submission/report.md` and `report.pdf`.

### F2. Minor. "now total 20 jobs" in Section 3.7.2 reads as current
- File: `report/report_v5.md` line 767 (copied to `submission/report_full.md` line 767).
- Evidence: "All H2-2E jobs with valid counts now total 20 jobs and 6598.0 HQC, which leaves 3402.0". Section 3.7.3 (line ~782) then gives 22 jobs and 2797.6. Two "now" totals in adjacent sections disagree.
- Proposed fix: "After this run the H2-2E jobs with valid counts totalled 20 jobs and 6598.0 HQC (22 and 7202.4 after Section 3.7.3)."

### F3. Info. HQC convention
- [F] The HQC estimate counts PhasedX (U1q) only and treats Rz as free (`pipelines/compile.py` `hqc`, citing the challenge `estimate_cost`). Counting rz as 1q gates would give 376.0 and 236.0. The convention is the one used for all earlier rows.
- [F] Nexus returned only `duration` (566, 393). The billed HQC is Unverifiable from the payloads.
- Proposed fix: none required.

### F4. Info. Compiled files committed after submission
- [F] `results/compiled/{P0,L3}/vbe_adder_7_nz.qasm` first appear in da6a6cb (00:52:45 UTC), after the jobs were submitted. The payloads hold no circuit or hash, so identity with the submitted circuits is Unverifiable. Their HQC (372.2, 232.2) matches the `hqc_estimate` stored in the payloads and the pre-submission check line in the run log.
- Proposed fix: for later runs store a SHA-256 of the submitted QASM in the payload or ledger.

### Checked and not an issue
- [F] Remaining "all-zero" statements (`report_v5.md` 685, 758, 769; `report_short.md` 238; `presentation.tex` 246; `EVIDENCE.md` 96) refer to the earlier runs and are correctly scoped. The one-page summary now says "all-zero except one vbe_adder_7 run".
- [F] Job totals 22 / 7202.4 appear consistently in `README.md` 87, `report_short.md` 208, `report_v5.md` (3.7.3, Section 6 quota 2797.6), `one_page_summary.md` 25, `presentation.tex` 247, `submission/SUMMARY.md` 75. No remaining "20 H2-2E jobs" or "6598.0" claim as a current total except F2.
- [F] `submission/SUMMARY.md` was changed in 60d2fa7, not d5ec540.
- [O] The new text claims no resolved difference (z = 1.30 "not resolved"), which matches the data. No overclaim found.
