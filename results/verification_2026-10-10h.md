# Verification 2026-10-10h (independent, HEAD 9825014)

Verdict: **PASS WITH ISSUES** (one factual error in two judge-facing files, no number wrong).

## Recomputed [F]

- famB1_multi payloads (own code, 14 files, 400 shots each, nexus:H2-2E, noisy_simulation): per-arm counts of the expected bitstring identical to `results/h22e_b1.md` Jobs table (381/379, 375/382, 386/384, 383/386; 367/349, 372/362, 365/355). Pooled z: vbe_adder_3 +0.5116 (p 0.6089), hwb6 -2.6351 (p 0.008412). Holm: hwb6 0.01682, vbe_adder_3 0.6089. R: 0.6713 [0.6613, 0.6815], 0.8909 [0.8679, 0.9144]. Pooled both circuits z -1.71. Run HQC 988.32.
- Expected bitstrings: own statevector simulator of the source files and of all 14 compiled hqslib1 files (measure map applied) gives probability 1.0 on exactly the pre-registered strings; vbe_adder_3 decodes a unchanged, b = a+b mod 8, cout = carry, ancillas 0 for (4,5), (6,3), (3,7), (7,5); hwb6 input X prefix matches bits of 126, 78, 40; RNG seed 20261012 reproduces the draws. sha256 of the 14 compiled files match `h22e_b1_checked.json`.
- Pre-registration: `dc56b94` author = committer 2026-10-10T11:42:24Z, only commit touching `h22e_b1_prereg.md`; first famB1_multi job 11:43:01Z (37 s later). The other two prereg commits also precede their first jobs.
- 8-pair pooled from CSV, rows cross-checked against all 48 payloads: R = (2516.52/11153)/(3080.04/11183) = 0.8192, 18.1 %, HQC ratio 0.8170, accuracy ratio 0.9973; own bootstrap [0.8131, 0.8255]. R < 1 and upper bound < 1 in 8/8 and 5/5. 48 payloads, 9971.76 HQC.
- Consistency: every headline number (z values, 0.0168, 18.1 %, 0.8192, 0.8170, 0.9973, 5 of 5, 8 of 8, 48, 9971.8) present and equal across the four PDFs, SUMMARY.md and README.md. One-pager 1 page; 11 slides, none clipped.

## Findings

1. **Medium, factual.** `report/one_page_summary.md` line 27 "(3 to 4 inputs each, 400 shots per program)" and `report/presentation/presentation.tex` line 164 "3 to 4 each at 400 shots per program": vbe_adder_7 is 1 input at 1000 shots (CSV row 4; report_short line 22 says so). Fix: "one to four inputs each, 400 shots per program, 1000 on the single-input vbe_adder_7".
2. **Low, wording.** "not different on 2" (all six files) contradicts the pre-registration's "a non-rejection is reported as such, not as evidence of equality". Fix: "not significantly different on 2".
3. **Low, tagging.** `report/report_short.md` line 24 (and one-pager line 29) tag "ZX can pay only through two-qubit gates" as [F]; HQC also charges PhasedX (N_1q, weight 1), as line 163 states. Fix: "pays mainly through" or [O].
4. **Low, presentation.** One-pager line 27 lists "Holm p = 0.0168" inside the parenthesis covering both cdkm_adder_10 and hwb6; only hwb6 had a pre-registered Holm step (Table F5 caption is explicit). Fix: attach it to hwb6 only.

Not issues: "none significantly better" is correct (vbe_adder_7 p = 0.195); limitations in all files state "less accurate on 2 of 5"; mechanism sentence matches the HQC definition; no softening of the accuracy loss found; no untraceable number found.
