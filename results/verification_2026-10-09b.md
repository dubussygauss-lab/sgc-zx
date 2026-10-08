# Verification of the pass selector (2026-10-09b)

Independent verifier. Did not import `value/`. All numbers recomputed from `results/family_A_counts.csv`, `family_B1_counts.csv`, `family_B1x_counts.csv` and `family_B2_counts.csv` (P0 and P2 rows) with HQC = 5 + 1000 (N_1q + 10 N_2q + 5 N_M)/5000, N_1q = n_phasedx, N_M = 2 n_qubits. PSEL rule: min HQC (rounded to 1e-9), then lower n_2q, then P0. Scripts kept in the scratchpad, logic summarised below.

Overall verdict: numbers PASS (every checked figure). Code PASS. Wording: 5 FAIL (F1 to F5), none changes a number.

## 1. Numbers

`[F]` Recomputed HQC equals the stored `hqc` column on every P0 and P2 row of the four files (max abs diff 0.0). n_2q = n_zzphase + n_zzmax on every row. Circuits: A 180, B1 15, B1x 8, B2 20, total 223.

| Family | Picks P2 | HQC P0 | HQC P2 | HQC PSEL | Saved vs P0 | % | Saved vs P2 | Median % vs P0 | Report |
|---|---|---|---|---|---|---|---|---|---|
| A | 57 | 16,422.6 | 17,453.0 | 16,376.6 | 46.0 | 0.28 | 1,076.4 | 0.00 | PASS |
| B1 | 14 | 15,516.0 | 14,772.8 | 14,772.4 | 743.6 | 4.79 | 0.4 | 3.94 | PASS |
| B1x | 7 | 3,288.8 | 3,141.0 | 3,141.0 | 147.8 | 4.49 | 0.0 | 2.40 | PASS |
| B2 | 0 | 730.0 | 731.6 | 730.0 | 0.0 | 0.00 | 1.6 | 0.00 | PASS |

| Claim (location) | Recomputed | Verdict |
|---|---|---|
| PSEL keeps P0 on 123 of 180 A, P2 dearer on 108, tie on 15 (1.2 last para, 1.5, 6, SUMMARY) | 123, 108, 15 | PASS |
| PSEL never raises n_2q vs P0 on 223 (Section 1 bullet, 1.2, SUMMARY) | 0 of 223 raised | PASS |
| Lowers n_2q on 13 of 15 B1 and 5 of 8 B1x (1.2) | 13, 5 | PASS |
| P2 alone +6.27 % on A (bullet, 1.2, 1.5, SUMMARY) | +6.27 % | PASS |
| XXZ: P2 dearer on all 60, +12.33 %, PSEL keeps P0 on 60 (1.2, 6, SUMMARY) | 60, +12.33 %, 60 | PASS |
| TFIM: P2 picked 32, PSEL saves 0.62 %. Ladder: 25, 0.52 % (1.2) | 32, 0.62 %. 25, 0.52 % | PASS |
| P2 cheaper on 14 of 15 B1, qft_4 the exception at +0.4 HQC, only PSEL-P2 difference on B1 and B1x (1.2) | 14, qft_4 98.8 vs 98.4, only qft_4 | PASS |
| B2: P2 never cheaper (1.2) | 7 dearer, 13 ties, 0 cheaper | PASS |
| hwb8 share 84.5 %, 115.0 HQC without hwb8 (1.2, SUMMARY) | 84.53 %, 115.0 | PASS |
| vbe_adder_3 largest per-circuit % saving on B1 (1.2) | 21.50 %, next grover_5 6.61 % | PASS |
| Shots at 10,000 HQC, one fee: vbe_adder_3 68,178 vs 87,675, +19,497, 28.6 % (1.2) | 68,178, 87,675, 19,497, 28.60 % | PASS |
| mod5_4: +11,757 shots, 7.5 % (1.2) | 157,649 to 169,406, 11,757, 7.46 % | PASS |
| With 10,000-shot job limit: 67,974 vs 87,324, +19,350, 28.5 %. mod5_4 +11,584, 7.4 % (1.2) | same, 28.47 %, 7.40 % | PASS |
| Median extra-shot gain of P2 over 15 B1 circuits 4.3 % (1.2) | 4.32 % | PASS |
| P2 saves 7.9 % on factoring and 4.8 % on search (1.5, SUMMARY) | 7.87 % (4 circuits), 4.78 % (8 circuits) | PASS |
| n_2q-optimal choice agrees with PSEL on 223 (1.2) | 223 of 223 only if n_2q ties are broken by HQC, see F4 | PASS (number) |

## 2. Code

`[F]` `python3 pipelines/test_pass_select.py`: 3 of 3 passed, 6.0 s wall. `python3 -m pytest value/test_selector_ledger.py -q`: 4 passed (run only, not imported).

`[F]` CLI `python3 pipelines/pass_select.py` on circuits outside the test set, chosen pipeline against the CSV-derived choice:

| Circuit | CLI choice, HQC P0 / P2, n_2q P0 / P2 | CSV-derived | Verdict |
|---|---|---|---|
| family_B1/mod5_4 | P2, 68.4 / 64.0, 24 / 22 | P2 | PASS |
| family_A/tfim_n6_r2_disorder_s1 | P2, 40.8 / 40.4, 10 / 10 | P2 | PASS |
| family_B2/haar_n3_eps1e-03_s1 | P0, 56.4 / 56.6, 19 / 19 | P0 | PASS |
| family_A/ladder_n10_r1_disorder_s1 (HQC and n_2q tie) | P0, 55.6 / 55.6, 13 / 13 | P0 | PASS |

`[F]` The code matches the report description in 1.2 and 2.2: candidates P0 and P2, drop on error, non-native gate or failed `compile.check`, tie-break HQC then n_2q then P0, no check above 20 qubits with status `ok-unchecked`.

## 3. Scope of claims

`[F]` PSEL is described everywhere as a choice between P0 and P2 only (1.2, 2.2, SUMMARY). The HQC is defined as the organisers' formula in 1.2 with "`[O]` We take this as the H2 price". No sentence claims a fidelity gain for PSEL. The fidelity statements in 1.5 and SUMMARY concern P2 against P0 and match Section 3.7.1. The statement that PSEL differs from P2 only on qft_4 on B1 and B1x is present (1.2). Section 6 states that the family totals come from stored rows and not from a rerun.

## 4. FAIL list

F1. Section 1 bullet "H2 cost. PSEL never costs more HQC than P0", Section 1.2 "By construction PSEL never costs more HQC than P0 on any circuit", Section 1.5 "and never costs more HQC than P0".
Observation: `compile_select` drops P0 when P0 fails `compile.check` or raises. P2 is then returned at any HQC, or nothing is returned. The bound holds by construction only when P0 survives. On the stored rows every P0 row is `ok` or `ok-unchecked`.
Fix (1.2): "PSEL costs more HQC than P0 only if P0 is dropped by an error or by the exactness check. No P0 row of the four families was dropped." Fix (bullet and 1.5): "PSEL costs no more HQC than P0 on any of the 223 circuits."

F2. `submission/SUMMARY.md`, "HQC saved on H2", "At 1000 shots it costs 14,772.4 HQC".
Observation: SUMMARY never says that HQC is computed from the organisers' cost formula on compiled gate counts. A reader can take the figures for billed charges.
Fix: after the first sentence of that paragraph insert "HQC is computed with the organisers' formula `estimate_cost` from the gate counts of the compiled circuit (report Section 1.2)."

F3. Section 1.5, "It answers \"should I run ZX before pytket\" per circuit".
Observation: PSEL decides only between P0 and P2. The ZX pipelines P1, P3 and P4 are not candidates. The quoted question is broader than the tool.
Fix: "It decides per circuit whether to run PyZX teleport_reduce before pytket's Quantinuum pass."

F4. Section 1.2, "The choice that minimises n_2q agrees with the choice that minimises HQC on all 223 circuits".
Observation: n_2q of P0 and P2 tie on 120 family A circuits. All 57 family A circuits where PSEL picks P2 are n_2q ties. With n_2q ties going to P0 the two choices differ on 57 circuits. The 223 of 223 holds with the rule of `value/selector_ledger.md` (lower n_2q, then lower HQC, then P0).
Fix: "The choice that minimises n_2q, with an n_2q tie broken by HQC, agrees with the choice of PSEL on all 223 circuits (`value/selector_ledger.md`)."

F5. Section 5, "Seven verification reports by agents that did not produce the results are in `results/verification_2026-10-0*.md`".
Observation: `results/verification_2026-10-09a.md` is committed (a56a8af) and is not listed. With this file the count is nine.
Fix: change "Seven" to "Nine" and add two bullets: "`results/verification_2026-10-09a.md` checked the pooled H2-2E results of Section 3.7.1." and "`results/verification_2026-10-09b.md` checked the pass selector PSEL, Table 1.1a and the PSEL statements of Sections 1, 2.2, 5 and 6 and of `submission/SUMMARY.md`."

## 5. Style

`[F]` Checked lines 9 to 16, 20 to 56, 73 to 81, 126 to 136, 152, 164, 831 to 838, 857, 875 to 877 of `report/report_v5.md` and all of `submission/SUMMARY.md`. No semicolon, no em-dash or en-dash, no "rather than", no hedge adverb. Every paragraph and bullet starts with a tag except the byline of SUMMARY line 3, which follows the untagged byline of the report. Sentences with more than two commas are lists or thousands separators. Parentheses hold formulas, references or glosses. PASS.

`[O]` Section 6 "`[F]` PSEL catches it in HQC" borrows the verb of the preceding `[O]` sentence. The verifiable content is the next sentence. Optional: delete "PSEL catches it in HQC." and start with "PSEL keeps P0 on all 60 XXZ circuits".
