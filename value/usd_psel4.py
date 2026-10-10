"""USD value of the PSEL4 HQC saving at the Azure Quantum H2 plan-average prices.

Prices (report/report_short.md Section 1.5, Reference 10)
  Standard Plan  USD 125,000 per month for 10,000 HQC
  Premium Plan   USD 175,000 per month for 17,000 HQC
  Plan average = monthly price / HQC. These are averages, not marginal prices.

Input  value/psel4_ledger.csv (one row per circuit, HQC at 1000 shots, columns hqc_P0 = level 2,
       hqc_L3 = level 3, hqc_PSEL4, family).

Computes per family and in total
  saved_vs_L2   sum(hqc_P0 - hqc_PSEL4)
  saved_vs_L3   sum(hqc_L3 - hqc_PSEL4)
  L3_loss       sum of positive (hqc_L3 - hqc_P0): HQC always-level-3 loses against level 2
  USD value of each at the two plan averages.
Monthly workload assumption: a team spends the Standard Plan's 10,000 HQC per month on a workload
with the ledger's mix; HQC freed = 10,000 x (1 - sum PSEL4 / sum P0).

Run from the repository root:  python3 value/usd_psel4.py   (writes value/usd_psel4.md)
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "value" / "psel4_ledger.csv"
OUT_MD = ROOT / "value" / "usd_psel4.md"
PLANS = {"Standard": (125000.0, 10000.0), "Premium": (175000.0, 17000.0)}
MONTHLY_HQC = 10000.0


def price(plan: str) -> float:
    usd, hqc = PLANS[plan]
    return usd / hqc


def compute() -> dict:
    L = pd.read_csv(LEDGER)
    L["s_L2"] = L.hqc_P0 - L.hqc_PSEL4
    L["s_L3"] = L.hqc_L3 - L.hqc_PSEL4
    L["l3_minus_l2"] = L.hqc_L3 - L.hqc_P0
    L["l3_loss"] = L.l3_minus_l2.clip(lower=0)
    rows = []
    groups = [(f, L[L.family == f]) for f in sorted(L.family.unique())] + [("total", L)]
    for f, g in groups:
        rows.append(dict(family=f, n=len(g), hqc_L2=g.hqc_P0.sum(), hqc_L3=g.hqc_L3.sum(),
                         hqc_PSEL4=g.hqc_PSEL4.sum(), saved_vs_L2=g.s_L2.sum(), saved_vs_L3=g.s_L3.sum(),
                         l3_loss=g.l3_loss.sum(), n_l3_loses=int((g.l3_minus_l2 > 1e-9).sum())))
    T = pd.DataFrame(rows)
    T["saved_vs_L2_pct"] = 100 * T.saved_vs_L2 / T.hqc_L2
    T["saved_vs_L3_pct"] = 100 * T.saved_vs_L3 / T.hqc_L3
    p_std, p_prem = price("Standard"), price("Premium")
    for col in ("saved_vs_L2", "saved_vs_L3", "l3_loss"):
        T[col + "_usd_premium"] = T[col] * p_prem
        T[col + "_usd_standard"] = T[col] * p_std
    tot = T.set_index("family").loc["total"]
    ratio = tot.hqc_PSEL4 / tot.hqc_L2
    freed = MONTHLY_HQC * (1 - ratio)
    monthly = dict(ratio=ratio, freed_hqc=freed, freed_usd_standard=freed * p_std,
                   freed_usd_premium=freed * p_prem)
    minL = float(np.minimum(L.hqc_P0, L.hqc_L3).sum())
    return dict(L=L, T=T, p_std=p_std, p_prem=p_prem, monthly=monthly, minL=minL)


def _usd(x: float) -> str:
    return "{:,.0f}".format(x)


def render_md(r: dict) -> str:
    T, m = r["T"], r["monthly"]
    out = ["# USD value of the PSEL4 HQC saving", "",
           "`[F]` Prices from report/report_short.md Section 1.5 (Reference 10): Standard Plan USD 125,000 per month "
           "for 10,000 HQC and Premium Plan USD 175,000 per month for 17,000 HQC. Plan averages: USD %.4f per HQC "
           "(Standard) and USD %.4f per HQC (Premium)." % (r["p_std"], r["p_prem"]),
           "",
           "`[F]` HQC from `value/psel4_ledger.csv` (%d circuits, 1000 shots of each circuit once, formula estimate). "
           "Script: `value/usd_psel4.py`. Each USD range runs from the Premium to the Standard plan average." % len(r["L"]),
           "",
           "| Family | Circuits | HQC L2 | HQC L3 | HQC PSEL4 | Saved vs L2 (HQC) | % | USD | Saved vs L3 (HQC) | % | USD |",
           "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|"]
    for t in T.itertuples():
        out.append("| %s | %d | %.1f | %.1f | %.1f | %.1f | %.2f | %s to %s | %.1f | %.2f | %s to %s |" % (
            t.family, t.n, t.hqc_L2, t.hqc_L3, t.hqc_PSEL4, t.saved_vs_L2, t.saved_vs_L2_pct,
            _usd(t.saved_vs_L2_usd_premium), _usd(t.saved_vs_L2_usd_standard), t.saved_vs_L3, t.saved_vs_L3_pct,
            _usd(t.saved_vs_L3_usd_premium), _usd(t.saved_vs_L3_usd_standard)))
    out += ["", "## Always level 3 against level 2", "",
            "| Family | Circuits where L3 costs more | HQC lost | USD |", "|---|---:|---:|---|"]
    for t in T.itertuples():
        out.append("| %s | %d | %.1f | %s to %s |" % (t.family, t.n_l3_loses, t.l3_loss,
                                                      _usd(t.l3_loss_usd_premium), _usd(t.l3_loss_usd_standard)))
    tot = T.set_index("family").loc["total"]
    out += ["", "## Headline", "",
            "- `[F]` PSEL4 saves %.1f HQC (%.2f %%) against always level 2 on the ledger, worth USD %s to %s at the plan averages."
            % (tot.saved_vs_L2, tot.saved_vs_L2_pct, _usd(tot.saved_vs_L2_usd_premium), _usd(tot.saved_vs_L2_usd_standard)),
            "- `[F]` PSEL4 saves %.1f HQC (%.2f %%) against always level 3, worth USD %s to %s."
            % (tot.saved_vs_L3, tot.saved_vs_L3_pct, _usd(tot.saved_vs_L3_usd_premium), _usd(tot.saved_vs_L3_usd_standard)),
            "- `[F]` Always level 3 costs more than level 2 on %d circuits and loses %.1f HQC there, worth USD %s to %s."
            % (tot.n_l3_loses, tot.l3_loss, _usd(tot.l3_loss_usd_premium), _usd(tot.l3_loss_usd_standard)),
            "- `[F]` Split of the saving against always level 2: always level 3 gives %.2f points and per-circuit "
            "selection plus ZX give the remaining %.2f points (%.2f %% in total)."
            % (100 * (1 - tot.hqc_L3 / tot.hqc_L2), tot.saved_vs_L2_pct - 100 * (1 - tot.hqc_L3 / tot.hqc_L2), tot.saved_vs_L2_pct),
            "- `[F]` Against the per-circuit cheaper of level 2 and level 3 (%.1f HQC) PSEL4 saves %.1f HQC, %.2f %% of that "
            "total and %.2f %% of the always-level-2 total." % (r["minL"], r["minL"] - tot.hqc_PSEL4,
            100 * (1 - tot.hqc_PSEL4 / r["minL"]), 100 * (r["minL"] - tot.hqc_PSEL4) / tot.hqc_L2),
            "- `[O]` Workload assumption: a team spends the Standard Plan's 10,000 HQC per month on circuits with the "
            "ledger's mix. `[F]` Under that assumption PSEL4 / L2 = %.4f, and PSEL4 frees 10,000 x (1 - %.4f) = %.1f HQC "
            "per month, worth USD %s at the Standard average (USD %s at the Premium average)."
            % (m["ratio"], m["ratio"], m["freed_hqc"], _usd(m["freed_usd_standard"]), _usd(m["freed_usd_premium"])),
            "- `[O]` Plan averages are not marginal prices. The figures ignore bundled eHQCs and Azure infrastructure "
            "costs. The total depends on the ledger's family mix. Family C gives %.1f of the %.1f HQC saved against level 2."
            % (T.set_index("family").loc["C", "saved_vs_L2"], tot.saved_vs_L2)]
    return "\n".join(out) + "\n"


def main():
    r = compute()
    OUT_MD.write_text(render_md(r))
    print(render_md(r))


if __name__ == "__main__":
    main()
