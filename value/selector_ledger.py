"""Selector ledger: HQC of the pass selector PSEL against P0 and P2.

No new experiments.  Every number in value/selector_ledger.csv and
value/selector_ledger.md is computed here from CSVs already in the repository.

Selector rule (approved by Kam, implemented in pipelines/select.py):
  for each circuit compile P0 (pytket L2) and P2 (ZX teleport_reduce + L2),
  keep the one with the lower HQC; on an HQC tie keep the one with the lower
  n_2q; on a further tie keep P0.

ZZ-optimal choice (for comparison only): keep the one with the lower n_2q;
  on a tie keep the lower HQC; on a further tie keep P0.

Inputs
  value/value_ledger.csv, layer NISQ, row_kind circuit: families A, B1, B1x
    (hqc_P0, hqc_P2 at 1000 shots, n2q_P0, n2q_P2).
  results/family_B2_counts.csv, pipelines P0 and P2 (hqc at 1000 shots, n_2q).
  Family A model is taken from results/family_A_counts.csv (column model).

Families are reported separately and never merged.  B1x is count-only and unchecked.

Run: python3 value/selector_ledger.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "value"
SHOTS = 1000          # hqc columns are at this shot count
DEC = 6               # HQC values are compared after rounding to this many decimals


def select(hqc0, hqc2, n0, n2):
    """Return 'P0' or 'P2' by the selector rule."""
    h0, h2 = round(hqc0, DEC), round(hqc2, DEC)
    if h2 < h0:
        return "P2"
    if h2 > h0:
        return "P0"
    return "P2" if n2 < n0 else "P0"


def select_zz(hqc0, hqc2, n0, n2):
    """Return 'P0' or 'P2' by the ZZ-optimal rule."""
    if n2 < n0:
        return "P2"
    if n2 > n0:
        return "P0"
    return "P2" if round(hqc2, DEC) < round(hqc0, DEC) else "P0"


def load():
    led = pd.read_csv(OUT / "value_ledger.csv")
    led = led[(led.layer == "NISQ") & (led.row_kind == "circuit")]
    rows = led[["file", "family", "hqc_P0", "hqc_P2", "n2q_P0", "n2q_P2"]].copy()

    a_model = (pd.read_csv(ROOT / "results/family_A_counts.csv")
               .drop_duplicates("file").set_index("file")["model"])
    rows["model"] = np.where(rows.family == "A", rows.file.map(a_model), "")
    assert rows[rows.family == "A"].model.notna().all()

    b2 = pd.read_csv(ROOT / "results/family_B2_counts.csv")
    b2 = b2[b2.pipeline.isin(["P0", "P2"])]
    assert set(b2.status) == {"ok"} and b2.check_ok.all()
    p = b2.pivot(index="file", columns="pipeline", values=["hqc", "n_2q"])
    b2r = pd.DataFrame({
        "file": p.index, "family": "B2",
        "hqc_P0": p[("hqc", "P0")].values, "hqc_P2": p[("hqc", "P2")].values,
        "n2q_P0": p[("n_2q", "P0")].values, "n2q_P2": p[("n_2q", "P2")].values,
        "model": ""})
    rows = pd.concat([rows, b2r], ignore_index=True)
    for c in ("n2q_P0", "n2q_P2"):
        rows[c] = rows[c].astype(int)
    return rows


def per_circuit(rows):
    r = rows.copy()
    r["choice"] = [select(*t) for t in zip(r.hqc_P0, r.hqc_P2, r.n2q_P0, r.n2q_P2)]
    r["choice_zz"] = [select_zz(*t) for t in zip(r.hqc_P0, r.hqc_P2, r.n2q_P0, r.n2q_P2)]
    r["hqc_SEL"] = np.where(r.choice == "P2", r.hqc_P2, r.hqc_P0)
    r["n2q_SEL"] = np.where(r.choice == "P2", r.n2q_P2, r.n2q_P0)
    r["saved_vs_P0"] = r.hqc_P0 - r.hqc_SEL
    r["saved_vs_P0_pct"] = 100 * r.saved_vs_P0 / r.hqc_P0
    r["saved_vs_P2"] = r.hqc_P2 - r.hqc_SEL
    r["saved_vs_P2_pct"] = 100 * r.saved_vs_P2 / r.hqc_P2
    r["dn2q_SEL_vs_P0"] = r.n2q_SEL - r.n2q_P0
    return r


def summarise(r, label, group):
    hp0, hp2, hs = r.hqc_P0.sum(), r.hqc_P2.sum(), r.hqc_SEL.sum()
    return dict(
        family=label, group=group, circuits=len(r),
        picks_P2=int((r.choice == "P2").sum()), picks_P0=int((r.choice == "P0").sum()),
        hqc_P0=hp0, hqc_P2=hp2, hqc_SEL=hs,
        saved_vs_P0=hp0 - hs, saved_vs_P0_pct=100 * (hp0 - hs) / hp0,
        saved_vs_P2=hp2 - hs, saved_vs_P2_pct=100 * (hp2 - hs) / hp2,
        p2_extra_vs_P0_pct=100 * (hp2 - hp0) / hp0,
        median_saved_vs_P0_pct=r.saved_vs_P0_pct.median(),
        n2q_P0=int(r.n2q_P0.sum()), n2q_SEL=int(r.n2q_SEL.sum()),
        sel_raises_n2q=int((r.dn2q_SEL_vs_P0 > 0).sum()),
        sel_lowers_n2q=int((r.dn2q_SEL_vs_P0 < 0).sum()),
        p2_raises_n2q=int((r.n2q_P2 > r.n2q_P0).sum()),
        p2_lowers_n2q=int((r.n2q_P2 < r.n2q_P0).sum()),
        p2_cheaper=int((r.hqc_P2.round(DEC) < r.hqc_P0.round(DEC)).sum()),
        p2_dearer=int((r.hqc_P2.round(DEC) > r.hqc_P0.round(DEC)).sum()),
        hqc_ties=int((r.hqc_P0.round(DEC) == r.hqc_P2.round(DEC)).sum()),
        zz_vs_hqc_choice_differ=int((r.choice != r.choice_zz).sum()),
    )


BUDGET = 10_000


def shots_affordable(hqc1000, budget):
    k = round((hqc1000 - 5) * 5000 / SHOTS, 6)
    return int(np.floor((budget - 5) * 5000 / k))


FAMILY_ORDER = ["A", "B1", "B1x", "B2"]
FAMILY_NOTE = {"A": "A", "B1": "B1", "B1x": "B1x (unchecked)", "B2": "B2"}


def build():
    r = per_circuit(load())
    out = []
    for fam in FAMILY_ORDER:
        rf = r[r.family == fam]
        out.append(summarise(rf, fam, "all"))
        if fam == "A":
            for m in ("tfim", "ladder", "xxz"):
                out.append(summarise(rf[rf.model == m], fam, m))
    return r, pd.DataFrame(out)


def fmt(x, nd=1):
    if isinstance(x, (int, np.integer)):
        return f"{x:,}"
    return f"{x:,.{nd}f}"


def md_table(df, cols, nd):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(
            fmt(row[c], nd.get(c, 1)) if not isinstance(row[c], str) else row[c]
            for c in cols) + " |")
    return "\n".join(lines)


def write(r, s):
    r.to_csv(OUT / "selector_ledger_circuits.csv", index=False)
    s.to_csv(OUT / "selector_ledger.csv", index=False)
    s_disp = s.copy()
    s_disp["family"] = s_disp.family.map(FAMILY_NOTE)
    md = ["# Selector ledger", "",
          "Generated by `value/selector_ledger.py`. No number is typed by hand. No new experiments.", "",
          "`[F]` Selector PSEL: for each circuit keep P0 (pytket L2) or P2 (ZX teleport_reduce + L2), "
          "whichever has the lower HQC. An HQC tie goes to the lower n_2q and a further tie to P0. "
          "HQC is at 1000 shots. Families are never merged. B1x is count-only and unchecked.", "",
          "`[F]` Inputs: `value/value_ledger.csv` (layer NISQ, families A, B1, B1x) and "
          "`results/family_B2_counts.csv` (pipelines P0 and P2). Per-circuit rows are in "
          "`value/selector_ledger_circuits.csv`.", "",
          "## HQC at 1000 shots", "",
          md_table(s_disp, ["family", "group", "circuits", "picks_P2", "hqc_P0", "hqc_P2", "hqc_SEL",
                            "saved_vs_P0", "saved_vs_P0_pct", "saved_vs_P2", "saved_vs_P2_pct",
                            "median_saved_vs_P0_pct", "p2_extra_vs_P0_pct"],
                   dict(saved_vs_P0_pct=2, saved_vs_P2_pct=2, median_saved_vs_P0_pct=2,
                        p2_extra_vs_P0_pct=2)), "",
          "`[F]` saved_vs_X = HQC_X - HQC_SEL summed over the group. saved_vs_X_pct = 100 saved_vs_X / "
          "HQC_X. median_saved_vs_P0_pct is the median of the per-circuit percentages. "
          "p2_extra_vs_P0_pct = 100 (HQC_P2 - HQC_P0) / HQC_P0, the cost of always running P2.", "",
          "## Two-qubit gates and choice", "",
          md_table(s_disp, ["family", "group", "circuits", "p2_cheaper", "p2_dearer", "hqc_ties",
                            "p2_raises_n2q", "p2_lowers_n2q", "n2q_P0", "n2q_SEL",
                            "sel_raises_n2q", "sel_lowers_n2q", "zz_vs_hqc_choice_differ"], {}), "",
          "`[F]` p2_cheaper, p2_dearer and hqc_ties compare HQC of P2 with P0 per circuit. "
          "p2_raises_n2q and p2_lowers_n2q compare n_2q of P2 with P0. "
          "sel_raises_n2q counts circuits where the selected circuit has more ZZ gates than P0. "
          "zz_vs_hqc_choice_differ counts circuits where the ZZ-optimal choice (lower n_2q, then lower "
          "HQC, then P0) differs from the HQC-optimal choice of PSEL.", ""]
    raised = r[r.dn2q_SEL_vs_P0 > 0]
    if len(raised):
        md += ["## Circuits where PSEL raises n_2q against P0", "",
               md_table(raised, ["file", "family", "hqc_P0", "hqc_P2", "n2q_P0", "n2q_P2"],
                        dict(hqc_P0=1, hqc_P2=1)), ""]
    differ = r[r.choice != r.choice_zz]
    if len(differ):
        md += ["## Circuits where the ZZ-optimal and HQC-optimal choices differ", "",
               md_table(differ, ["file", "family", "hqc_P0", "hqc_P2", "n2q_P0", "n2q_P2",
                                 "choice", "choice_zz"], dict(hqc_P0=1, hqc_P2=1)), ""]
    b1 = r[r.family == "B1"]
    hw = b1[b1.file == "hwb8.qasm"].iloc[0]
    md += ["## B1 notes", "",
           f"`[F]` hwb8 share of the B1 selector saving: "
           f"{fmt(100 * hw.saved_vs_P0 / b1.saved_vs_P0.sum(), 1)}%. "
           f"B1 selector saving without hwb8: {fmt(b1.saved_vs_P0.sum() - hw.saved_vs_P0, 1)} HQC. "
           f"B1 P2 saving without hwb8: "
           f"{fmt((b1.hqc_P0 - b1.hqc_P2).sum() - (hw.hqc_P0 - hw.hqc_P2), 1)} HQC.", ""]
    md += ["## Shots at a 10,000 HQC budget, one job fee", "",
           "| file | choice | shots_P0 | shots_SEL | extra_shots | extra_pct |", "|---|---|---|---|---|---|"]
    for f in ("vbe_adder_3.qasm", "mod5_4.qasm"):
        x = b1[b1.file == f].iloc[0]
        s0 = shots_affordable(x.hqc_P0, BUDGET)
        ss = shots_affordable(x.hqc_SEL, BUDGET)
        md.append(f"| {f} | {x.choice} | {s0:,} | {ss:,} | {ss - s0:,} | {fmt(100 * (ss - s0) / s0, 1)} |")
    md += ["", "`[F]` shots = floor((10,000 - 5) 5000 / k) with k = (HQC at 1000 shots - 5) 5000 / 1000.", ""]
    (OUT / "selector_ledger.md").write_text("\n".join(md))


if __name__ == "__main__":
    r, s = build()
    write(r, s)
    pd.set_option("display.width", 250)
    print(s.to_string())
