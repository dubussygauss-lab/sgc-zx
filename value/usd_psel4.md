# USD value of the PSEL4 HQC saving

`[F]` Prices from report/report_short.md Section 1.5 (Reference 10): Standard Plan USD 125,000 per month for 10,000 HQC and Premium Plan USD 175,000 per month for 17,000 HQC. Plan averages: USD 12.5000 per HQC (Standard) and USD 10.2941 per HQC (Premium).

`[F]` HQC from `value/psel4_ledger.csv` (217 circuits, 1000 shots of each circuit once, formula estimate). Script: `value/usd_psel4.py`. Each USD range runs from the Premium to the Standard plan average.

| Family | Circuits | HQC L2 | HQC L3 | HQC PSEL4 | Saved vs L2 (HQC) | % | USD | Saved vs L3 (HQC) | % | USD |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| A | 180 | 16422.6 | 16231.2 | 15949.0 | 473.6 | 2.88 | 4,875 to 5,920 | 282.2 | 1.74 | 2,905 to 3,528 |
| B1 | 15 | 15516.0 | 13965.8 | 13863.4 | 1652.6 | 10.65 | 17,012 to 20,657 | 102.4 | 0.73 | 1,054 to 1,280 |
| C | 20 | 24535.0 | 18853.2 | 18193.2 | 6341.8 | 25.85 | 65,283 to 79,273 | 660.0 | 3.50 | 6,794 to 8,250 |
| usecase | 2 | 2363.6 | 1582.0 | 1575.0 | 788.6 | 33.36 | 8,118 to 9,858 | 7.0 | 0.44 | 72 to 88 |
| total | 217 | 58837.2 | 50632.2 | 49580.6 | 9256.6 | 15.73 | 95,289 to 115,707 | 1051.6 | 2.08 | 10,825 to 13,145 |

## Always level 3 against level 2

| Family | Circuits where L3 costs more | HQC lost | USD |
|---|---:|---:|---|
| A | 35 | 282.2 | 2,905 to 3,528 |
| B1 | 2 | 33.8 | 348 to 423 |
| C | 8 | 56.0 | 576 to 700 |
| usecase | 0 | 0.0 | 0 to 0 |
| total | 45 | 372.0 | 3,829 to 4,650 |

## Headline

- `[F]` PSEL4 saves 9256.6 HQC (15.73 %) against always level 2 on the ledger, worth USD 95,289 to 115,707 at the plan averages.
- `[F]` PSEL4 saves 1051.6 HQC (2.08 %) against always level 3, worth USD 10,825 to 13,145.
- `[F]` Always level 3 costs more than level 2 on 45 circuits and loses 372.0 HQC there, worth USD 3,829 to 4,650.
- `[O]` Workload assumption: a team spends the Standard Plan's 10,000 HQC per month on circuits with the ledger's mix. `[F]` Under that assumption PSEL4 / L2 = 0.8427, and PSEL4 frees 10,000 x (1 - 0.8427) = 1573.3 HQC per month, worth USD 19,666 at the Standard average (USD 16,195 at the Premium average).
- `[O]` Plan averages are not marginal prices. The figures ignore bundled eHQCs and Azure infrastructure costs. The total depends on the ledger's family mix. Family C gives 6341.8 of the 9256.6 HQC saved against level 2.
