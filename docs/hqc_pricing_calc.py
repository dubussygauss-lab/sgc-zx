"""Money value of HQC savings already in the repo.

Prices: Azure Quantum pricing page, Quantinuum section, fetched 2026-10-09
(https://learn.microsoft.com/en-us/azure/quantum/pricing, "Last updated on
2025-12-23"). Standard Plan USD 125,000/month with 10k HQCs on System Model H2,
Premium Plan USD 175,000/month with 17k HQCs. The implied price per HQC is the
plan price divided by the HQCs included. It is an average for that plan, not a
marginal price. It assigns zero value to the bundled eHQCs and leaves out
Azure infrastructure costs.

Savings are read from value/selector_ledger.md, value/family_C_selector.md and
value/usecase.md. Run from the repo root: python docs/hqc_pricing_calc.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PLANS = {
    "Azure Standard (USD 125,000 / 10,000 HQC)": (125_000, 10_000),
    "Azure Premium (USD 175,000 / 17,000 HQC)": (175_000, 17_000),
}


def num(s):
    return float(s.replace(",", ""))


def table_row(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return [c.strip() for c in line.strip().strip("|").split("|")]
    raise KeyError(prefix)


def read_savings():
    sel = (ROOT / "value/selector_ledger.md").read_text()
    fc = (ROOT / "value/family_C_selector.md").read_text()
    uc = (ROOT / "value/usecase.md").read_text()
    out = {}
    hdr = table_row(sel, "| family | group | circuits | picks_P2")
    a = dict(zip(hdr, table_row(sel, "| A | all |")))
    b1 = dict(zip(hdr, table_row(sel, "| B1 | all |")))
    out["B1 PSEL vs P0, 15 circuits"] = num(b1["saved_vs_P0"])
    out["Family A PSEL vs always-P2 (avoided loss), 180 circuits"] = num(a["saved_vs_P2"])
    hdr = table_row(fc, "| application | n_circuits")
    c = dict(zip(hdr, table_row(fc, "| all | 20 |")))
    out["Family C PSEL vs P0, 20 circuits"] = num(c["saved_hqc"])
    m = re.search(r"Circuits without continuous angles:.*?Saved ([\d.,]+) HQC or ([\d.]+) %", fc)
    out["Family C subset without continuous angles (7.47 %), 15 circuits"] = num(m.group(1))
    hdr = table_row(uc, "| file | qubits | k |")
    for f in ("grover_d5.qasm", "grover_d6.qasm"):
        r = dict(zip(hdr, table_row(uc, f"| {f} |")))
        out[f"Grover use case {f}, PSEL vs P0"] = num(r["saving"])
    return out


def main():
    price = {k: p / h for k, (p, h) in PLANS.items()}
    print("Implied average price per HQC (USD):")
    for k, v in price.items():
        print(f"  {k}: {v:.4f}")
    sav = read_savings()
    print("\nSaving per 1000 shots per circuit set (HQC) and money value (USD):")
    for k, h in sav.items():
        vals = "  ".join(f"{v * h:,.0f}" for v in price.values())
        print(f"  {k}: {h:,.1f} HQC -> USD {vals}  (Standard, Premium)")
    print("\nShare of one month's plan HQCs:")
    for k, h in sav.items():
        print(f"  {k}: " + "  ".join(f"{100 * h / q:.2f} %" for _, q in PLANS.values()))


if __name__ == "__main__":
    main()
