# HQC price sources and money value of savings

All pages below were fetched on 2026-10-09. Numbers derived from them are computed in `docs/hqc_pricing_calc.py`.

## 1. Sources with a price

### 1.1 Azure Quantum pricing, Quantinuum section (primary source)

- `[F]` URL: https://learn.microsoft.com/en-us/azure/quantum/pricing (section "Quantinuum", tab "Subscriptions").
- `[F]` Page dates: footer "Last updated on 2025-12-23", metadata `ms.date` 2025-09-17, metadata `updated_at` 2026-04-23T15:34:00Z.
- `[F]` Exact quote: "Subscriptions are monthly subscription plans available through queued access."
- `[F]` Exact quote: "**Standard Plan**: USD125,000/Month + Azure infrastructure costs" with "10k HQCs for use on Quantinuum System Model H2" and "100k eHQCs for use on the Quantinuum System Model H2 emulators".
- `[F]` Exact quote: "**Premium Plan**: USD175,000/Month + Azure infrastructure costs" with "17k HQCs for use on Quantinuum System Model H2" and "170k eHQCs for use on the Quantinuum System Model H2 emulators".
- `[F]` Currency USD. Plans are monthly subscriptions for System Model H2. H1 is not listed.
- `[F]` The page also names a "Pay as You Go" offering. Its tab has no price text in the fetched page.
- `[F]` The page says provider prices may change and should be checked in the Azure Quantum workspace.
- `[F]` The fetched text cells for the plans ran together ("H2100k"). The split into HQC and eHQC above follows the HTML table rows. A second source (1.2) gives the same split.

Implied price per HQC (computed in `docs/hqc_pricing_calc.py`):

| plan | USD per month | HQC included | implied USD per HQC |
|---|---|---|---|
| Standard | 125,000 | 10,000 | 12.5000 |
| Premium | 175,000 | 17,000 | 10.2941 |

- `[O]` These are implied averages for each plan, not marginal prices. They assume the full monthly HQC allotment is used, give the bundled eHQCs zero value, and leave out Azure infrastructure costs. A plan used below its allotment has a higher cost per HQC actually spent.

### 1.2 Secondary sources quoting the same plans

- `[F]` Quantum Benchmark Zoo, https://www.quantumbenchmarkzoo.org/content/business-info/hardware-access (no page date). Lists for the Quantinuum H1 and H2 models on Azure "125 000 $USD / month", "contains 10 000 HQC", "Contains 100 000 eHQC" (Standard) and "175 000 $USD / month", "contains 17 000 HQC", "Contains 170 000 eHQC" (Premium). H2 pay-as-you-go and Helios are listed as "Custom". It cites the Azure page in 1.1.
- `[F]` Quantum Observer, "(Quantum) Business Advantage", https://quantumobserver.substack.com/p/cost-of-gates-sold, dated 2021-09-20. Exact quote: "you can pay either $125,000 per month for 10,000 Honeywell Quantum Credits (HQC), or $175,000 per month for 17,000 HQC". It cites the Azure Honeywell provider page of that time. The same plan prices were therefore in place in 2021 under the Honeywell name.
- `[O]` These are not independent price measurements. They show only that the Azure figures have been stable and public since 2021.

## 2. Sources checked without a price

- `[F]` Azure Quantum provider page, https://learn.microsoft.com/en-us/azure/quantum/provider-quantinuum, "Last updated on 2026-05-15". Gives the HQC formula and targets H2-1 and H2-2. No money figure. Says emulator use "is offered free-of-charge with a hardware subscription".
- `[F]` Quantinuum Nexus user terms, https://nexus.quantinuum.com/auth/terms_and_conditions/quantum_system, "Qstc V6.0 June 2026". Says HQCs "are neither units of time nor money" and refers to "agreed fees" without amounts.
- `[F]` Quantinuum documentation, Helios job costing, https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html (copyright 2025, no version). Formula only, no price.
- `[F]` AWS Braket pricing, https://aws.amazon.com/braket/pricing/ (`og:updated_time` 2026-09-25). Quantinuum is not listed.
- `[F]` No academic paper or press item with a per-HQC or per-circuit price other than the 2021 article in 1.2 was found in the searches run.
- `[F]` Unverifiable: Azure pay-as-you-go price for Quantinuum H2, direct Quantinuum subscription prices, Helios prices. None is published on the pages above.

## 3. HQC formula on the sources against ours

- `[F]` Ours (`pipelines/compile.py`, `hqc`): HQC = 5 + C (N_1q + 10 N_2q + 5 N_spam)/5000 with N_1q = PhasedX count, N_2q = ZZMax + ZZPhase count, N_spam = n_qubits + Measure + Reset. Rz is free.
- `[F]` Azure pricing and provider pages: "HQC = 5 + C(N_{1q} + 10 N_{2q} + 5 N_m)/5000". N_m is "the number of state preparation and measurement (SPAM) operations in a circuit including initial implicit state preparation and any intermediate and final measurements and state resets". N_1q is "the number of single-qubit operations".
- `[F]` Coefficients and structure match ours. Our N_spam counts initial preparation (n_qubits), measurements and resets, as the Azure N_m does.
- `[F]` Nexus terms V6.0 give the same coefficients but define N_m as "the number of measurements, including intermediate and final", without preparation. The terms call the formula "representative of the actual formula".
- `[F]` The Quantinuum Helios costing page excludes Rz from N_1q ("`Rz` operations are excluded"), as we do. The Azure text says only "single-qubit operations" and does not say whether Rz counts.
- `[O]` The formula match is close enough for the conversion below. The two definitional differences (preparation in N_m, Rz in N_1q) are known and stated.

## 4. Money value of savings already in the repo

Savings are read by `docs/hqc_pricing_calc.py` from `value/selector_ledger.md`, `value/family_C_selector.md` and `value/usecase.md`. All are HQC at 1000 shots per circuit, summed over the circuits named.

| saving | source | HQC | USD at Standard (12.50) | USD at Premium (10.29) | share of Standard month | share of Premium month |
|---|---|---|---|---|---|---|
| B1 PSEL vs P0, 15 circuits | selector_ledger.md, B1 all, saved_vs_P0 | 743.6 | 9,295 | 7,655 | 7.44 % | 4.37 % |
| Family A PSEL vs always-P2 (avoided loss), 180 circuits | selector_ledger.md, A all, saved_vs_P2 | 1,076.4 | 13,455 | 11,081 | 10.76 % | 6.33 % |
| Family C PSEL vs P0, 20 circuits | family_C_selector.md, row "all" | 4,104.4 | 51,305 | 42,251 | 41.04 % | 24.14 % |
| Family C subset without continuous angles (7.47 %), 15 circuits | family_C_selector.md, text below table | 748.4 | 9,355 | 7,704 | 7.48 % | 4.40 % |
| Grover use case grover_d5.qasm | usecase.md | 39.8 | 497 | 410 | 0.40 % | 0.23 % |
| Grover use case grover_d6.qasm | usecase.md | 80.8 | 1,010 | 832 | 0.81 % | 0.48 % |

- `[F]` The HQC column and both shares are from the repo files and the plan sizes. The shares are 100 x HQC saved / HQC in one month of the plan.
- `[O]` Every USD figure is an estimate. It assumes the saved HQCs are worth the implied plan average (USD 12.50 or 10.29 per HQC), that the subscriber uses the whole monthly allotment and would buy more HQCs at that rate, and that Azure infrastructure costs and eHQCs are ignored. It is not a quoted marginal price.
- `[O]` The figures are per 1000 shots of each circuit set once. A user who runs a set repeatedly multiplies the saving by the number of runs.
- `[O]` The Family C total is dominated by two circuits with continuous angles (hrs_mult_5.qasm and rgqft_mult_6.qasm, 3,356.0 HQC per family_C_selector.md). The 748.4 HQC subset is the more conservative figure to quote.
- `[O]` The Family A row is an avoided loss against always running P2, not a saving against the P0 baseline.
