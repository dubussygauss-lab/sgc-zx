"""Value by application area: regroup the value ledger by the algorithm each circuit serves.

No new experiments and no new data.  Every number in value/value_by_application.md and
value/value_by_application.csv is computed here from
  value/value_ledger.csv            (HQC and magic-state ledger, P2 vs P0, 1000 shots),
  docs/applications.md              (summary table: application area -> circuits),
  results/emulator_nexus_H2-2E.csv  and results/emulator/nexus_H2-2E/<P>/<stem>.json
                                    (H2-2E fidelities and HQC estimates, reported as context).

Assignment rule.  The summary table of docs/applications.md lists some circuits in two
areas (the three adders appear under integer factoring and under arithmetic for chemistry).
Each circuit is assigned to exactly one primary area: the first row of the summary table,
in table order, that lists it.  Secondary memberships are kept in the column
`secondary_areas` and do not enter any sum.

Families.  B1 (checked) and B1x (count-only, unchecked) are never merged.  Every row of
the output carries its family.  Family A (control) and family B2 are reported in their own
blocks.

Run: python3 value/value_by_application.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "value"
LEDGER = OUT / "value_ledger.csv"
APPS = ROOT / "docs/applications.md"
H22E_CSV = ROOT / "results/emulator_nexus_H2-2E.csv"
H22E_DIR = ROOT / "results/emulator/nexus_H2-2E"
FAMILIES = ("B1", "B1x")
SELECTED = ("vbe_adder_3.qasm", "mod5_4.qasm", "grover_5.qasm")


# ---------------------------------------------------------------- application table
def _token_to_regex(tok):
    """Map a circuit name of the summary table to a regex on ledger file names."""
    tok = tok.strip().strip("`")
    tok = tok.replace("gf2^", "gf2_pow_")          # gf2^4_mult -> gf2_pow_4_mult
    if tok.endswith("_n"):                          # tof_n, barenco_tof_n
        return re.compile(r"^%s_\d+\.qasm$" % re.escape(tok[:-2]))
    return re.compile(r"^%s\.qasm$" % re.escape(tok))


def read_summary_table(path=APPS):
    """Return [(area, [regex, ...], citation_cell)] in table order."""
    lines = path.read_text().splitlines()
    start = lines.index("## Summary")
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.startswith("|") or line.startswith("|---") or "Application area" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        area, circuits, citation = cells[0], cells[1], cells[2]
        # "grover_5, mod5_4, tof_n and barenco_tof_n as oracle and diffusion parts"
        circuits = circuits.split(" as ")[0]
        toks = [t for part in circuits.split(",") for t in part.split(" and ")]
        rows.append((area, [_token_to_regex(t) for t in toks if t.strip()], citation))
    if not rows:
        raise RuntimeError("summary table not found in %s" % path)
    return rows


def placement_status(area, file, citation):
    """[F] or [O] placement status, copied from the citation cell of the summary table."""
    if "[O]` for the circuit placement" in citation:
        return "[O]"
    if "[O]` for the tof_n placement" in citation and re.match(r"^(barenco_)?tof_\d+", file):
        return "[O]"
    return "[F]"


def assign_areas(files, table):
    """Return DataFrame file -> primary_area, placement, secondary_areas."""
    out = []
    for f in files:
        hits = [(a, cit) for a, regs, cit in table if any(r.match(f) for r in regs)]
        if not hits:
            raise RuntimeError("circuit %s is in no application area" % f)
        primary, cit = hits[0]
        out.append(dict(file=f, area=primary, placement=placement_status(primary, f, cit),
                        secondary_areas="; ".join(a for a, _ in hits[1:])))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- aggregation
def area_rows(led, amap, table):
    nisq = led[(led.layer == "NISQ") & (led.row_kind == "circuit")]
    ft = led[(led.layer == "FT") & (led.row_kind == "circuit")]
    rows = []
    order = [a for a, _, _ in table]
    for fam in FAMILIES:
        n = nisq[nisq.family == fam].merge(amap, on="file")
        t = ft[ft.family == fam].merge(amap, on="file")
        for area in order:
            ns, ts = n[n.area == area], t[t.area == area]
            if ns.empty and ts.empty:
                continue
            assert set(ns.file) == set(ts.file), (fam, area)
            p0, p2 = ns.hqc_P0.sum(), ns.hqc_P2.sum()
            tw, tz = ts.T_written.sum(), ts.T_zx_P2.sum()
            rows.append(dict(
                family=fam, area=area, n_circuits=len(ns),
                circuits=", ".join(sorted(f.replace(".qasm", "") for f in ns.file)),
                placement=",".join(sorted(set(ns.placement))),
                hqc_P0=p0, hqc_P2=p2, hqc_saved=ns.hqc_saved.sum(),
                hqc_saved_pct=100 * (p0 - p2) / p0,
                hqc_saved_pct_median=float(np.median(ns.hqc_saved_pct)),
                hqc_share_of_family_saved=np.nan,
                T_written=tw, T_after_zx=tz, magic_saved=ts.magic_saved.sum(),
                magic_saved_pct=100 * (tw - tz) / tw,
            ))
        # family total row, recomputed from circuit rows and checked against ledger TOTAL
        fam_rows = [r for r in rows if r["family"] == fam]
        saved_tot = sum(r["hqc_saved"] for r in fam_rows)
        for r in fam_rows:
            r["hqc_share_of_family_saved"] = 100 * r["hqc_saved"] / saved_tot
        led_tot_n = led[(led.layer == "NISQ") & (led.family == fam) & (led.row_kind == "total")].iloc[0]
        led_tot_t = led[(led.layer == "FT") & (led.family == fam) & (led.row_kind == "total")].iloc[0]
        tot = dict(
            family=fam, area="ALL (family total)", n_circuits=sum(r["n_circuits"] for r in fam_rows),
            circuits="", placement="",
            hqc_P0=sum(r["hqc_P0"] for r in fam_rows), hqc_P2=sum(r["hqc_P2"] for r in fam_rows),
            hqc_saved=saved_tot, hqc_saved_pct=np.nan,
            hqc_saved_pct_median=float(np.median(n.hqc_saved_pct)),
            hqc_share_of_family_saved=100.0,
            T_written=sum(r["T_written"] for r in fam_rows), T_after_zx=sum(r["T_after_zx"] for r in fam_rows),
            magic_saved=sum(r["magic_saved"] for r in fam_rows), magic_saved_pct=np.nan)
        tot["hqc_saved_pct"] = 100 * tot["hqc_saved"] / tot["hqc_P0"]
        tot["magic_saved_pct"] = 100 * tot["magic_saved"] / tot["T_written"]
        assert np.isclose(tot["hqc_P0"], led_tot_n.hqc_P0) and np.isclose(tot["hqc_P2"], led_tot_n.hqc_P2)
        assert np.isclose(tot["T_written"], led_tot_t.T_written) and np.isclose(tot["T_after_zx"], led_tot_t.T_zx_P2)
        rows.append(tot)
    return pd.DataFrame(rows)


def selected_rows(led):
    nisq = led[(led.layer == "NISQ") & (led.row_kind == "circuit") & led.file.isin(SELECTED)]
    ft = led[(led.layer == "FT") & (led.row_kind == "circuit") & led.file.isin(SELECTED)]
    nisq = nisq.drop(columns=["T_written", "T_zx_P2", "magic_saved"])
    m = nisq.merge(ft[["file", "family", "T_written", "T_zx_P2", "magic_saved"]], on=["file", "family"])
    m = m.assign(extra_shots_pct=100 * m.extra_shots_at_budget / m.shots_at_budget_P0)
    return m[["file", "family", "hqc_P0", "hqc_P2", "hqc_saved", "hqc_saved_pct", "shots_at_budget_P0",
              "shots_at_budget_P2", "extra_shots_at_budget", "extra_shots_pct", "T_written", "T_zx_P2",
              "magic_saved"]].set_index("file").loc[list(SELECTED)].reset_index()


def family_a(led):
    a = led[(led.layer == "NISQ") & (led.family == "A") & (led.row_kind == "circuit")].copy()
    a["model"] = a.file.str.split("_").str[0]
    g = a.groupby("model").agg(n_circuits=("file", "size"), hqc_P0=("hqc_P0", "sum"),
                               hqc_P2=("hqc_P2", "sum"), hqc_saved=("hqc_saved", "sum"),
                               hqc_saved_pct_median=("hqc_saved_pct", "median"),
                               n_P2_dearer=("hqc_saved", lambda s: int((s < -1e-9).sum())),
                               n_P2_cheaper=("hqc_saved", lambda s: int((s > 1e-9).sum()))).reset_index()
    tot = dict(model="ALL", n_circuits=len(a), hqc_P0=a.hqc_P0.sum(), hqc_P2=a.hqc_P2.sum(),
               hqc_saved=a.hqc_saved.sum(), hqc_saved_pct_median=a.hqc_saved_pct.median(),
               n_P2_dearer=int((a.hqc_saved < -1e-9).sum()), n_P2_cheaper=int((a.hqc_saved > 1e-9).sum()))
    g = pd.concat([g, pd.DataFrame([tot])], ignore_index=True)
    g["hqc_increase_P2_vs_P0_pct"] = 100 * (g.hqc_P2 - g.hqc_P0) / g.hqc_P0
    return g


def family_b2(led):
    b = led[(led.layer == "FT") & (led.family == "B2") & (led.row_kind == "circuit")]
    tw, tz, fl = b.T_written.sum(), b.T_zx_P2.sum(), b.cert_floor.sum()
    frac = fl / tz
    return dict(n_circuits=len(b), T_written=tw, T_after_zx=tz, magic_saved=tw - tz,
                magic_saved_pct=100 * (tw - tz) / tw, cert_floor=fl, above_floor=tz - fl,
                certified_fraction_pooled=frac,
                max_further_gain_pct_pooled=100 * (1 - frac),
                certified_fraction_min=b.cert_incompressible_frac_of_remaining.min(),
                max_further_gain_pct_worst_instance=100 * (1 - b.cert_incompressible_frac_of_remaining.min()))


def b1_certified(led):
    b = led[(led.layer == "FT") & (led.family == "B1") & (led.row_kind == "circuit") & led.cert_floor.notna()]
    return dict(n_circuits=len(b), circuits=", ".join(b.file.str.replace(".qasm", "")),
                T_after_zx=b.T_zx_P2.sum(), cert_floor=b.cert_floor.sum(),
                certified_fraction_pooled=b.cert_floor.sum() / b.T_zx_P2.sum())


def h22e(led):
    e = pd.read_csv(H22E_CSV)
    rows, tot = [], 0.0
    for _, r in e.iterrows():
        d = json.loads((H22E_DIR / r.pipeline / r.file.replace(".qasm", ".json")).read_text())
        assert np.isclose(d["F_H"], r.F_H)
        lrow = led[(led.layer == "NISQ") & (led.family == "B1") & (led.file == r.file)].iloc[0]
        assert np.isclose(d["hqc_estimate"], lrow["hqc_" + r.pipeline]), (r.file, r.pipeline)
        tot += d["hqc_estimate"]
        rows.append(dict(file=r.file, pipeline=r.pipeline, n_2q=r.n_2q, F_H=r.F_H, hqc=d["hqc_estimate"]))
    return pd.DataFrame(rows), tot


# ---------------------------------------------------------------- output
def fmt(x, nd=1):
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        return f"{x:,.{nd}f}"
    if isinstance(x, (int, np.integer)):
        return f"{x:,d}"
    return str(x)


def md_table(df, cols, nd=None):
    nd = nd or {}
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(fmt(r[c], nd.get(c, 1)) for c in cols) + " |")
    return "\n".join(out)


def main():
    led = pd.read_csv(LEDGER)
    table = read_summary_table()
    files = sorted(led[(led.layer == "NISQ") & led.family.isin(FAMILIES) & (led.row_kind == "circuit")].file)
    amap = assign_areas(files, table)
    areas = area_rows(led, amap, table)
    sel = selected_rows(led)
    fa = family_a(led)
    b2 = family_b2(led)
    b1c = b1_certified(led)
    h2, h2_tot = h22e(led)

    # CSV: area rows (both families, unmerged) plus control and B2 blocks, one schema
    csv = areas.assign(block="area")
    extra = [dict(block="family_A_control", family="A", area="Trotter control (" + r.model + ")",
                  n_circuits=r.n_circuits, hqc_P0=r.hqc_P0, hqc_P2=r.hqc_P2, hqc_saved=r.hqc_saved,
                  hqc_saved_pct=-r.hqc_increase_P2_vs_P0_pct, hqc_saved_pct_median=r.hqc_saved_pct_median)
             for r in fa.itertuples()]
    extra.append(dict(block="family_B2_certified", family="B2", area="Synthesised Haar unitaries",
                      n_circuits=b2["n_circuits"], T_written=b2["T_written"], T_after_zx=b2["T_after_zx"],
                      magic_saved=b2["magic_saved"], magic_saved_pct=b2["magic_saved_pct"],
                      cert_floor=b2["cert_floor"], certified_fraction=b2["certified_fraction_pooled"]))
    extra.append(dict(block="family_B1_certified", family="B1", area="B1 circuits with a certificate",
                      n_circuits=b1c["n_circuits"], circuits=b1c["circuits"], T_after_zx=b1c["T_after_zx"],
                      cert_floor=b1c["cert_floor"], certified_fraction=b1c["certified_fraction_pooled"]))
    csv = pd.concat([csv, pd.DataFrame(extra)], ignore_index=True)
    csv.to_csv(OUT / "value_by_application.csv", index=False)

    cols = ["area", "n_circuits", "hqc_P0", "hqc_P2", "hqc_saved", "hqc_saved_pct", "hqc_saved_pct_median",
            "hqc_share_of_family_saved", "T_written", "T_after_zx", "magic_saved", "magic_saved_pct"]
    nd = {"n_circuits": 0, "T_written": 0, "T_after_zx": 0, "magic_saved": 0}
    for c in ("T_written", "T_after_zx", "magic_saved"):
        areas[c] = areas[c].astype(int)
    L = ["# Value by application area",
         "",
         "Generated by `value/value_by_application.py` from `value/value_ledger.csv`, the summary table of "
         "`docs/applications.md` and the H2-2E emulator files. No number is typed by hand. No new experiments.",
         "",
         "`[F]` Assignment rule: each circuit goes to the first row of the summary table of "
         "`docs/applications.md`, in table order, that lists it. vbe_adder_3, rc_adder_6 and csla_mux_3 are "
         "listed under integer factoring and under arithmetic for chemistry and simulation oracles. They are "
         "assigned to integer factoring, and the chemistry row therefore has no primary circuit. "
         "The per-circuit assignment is the last table of this file.",
         "",
         "`[F]` HQC at 1000 shots, P2 (ZX teleport_reduce + pytket L2) against P0 (pytket L2). "
         "hqc_saved_pct = 100 (sum P0 - sum P2) / sum P0. hqc_saved_pct_median is the median of the per-circuit "
         "percentages. hqc_share_of_family_saved is the share of the family's total HQC saved. "
         "magic_saved = T written - T after the ZX stage of P2, one magic state per T gate.",
         ""]
    for fam, label in (("B1", "Family B1 (checked)"), ("B1x", "Family B1x (count-only, unchecked, never merged with B1)")):
        L += ["## " + label, "", md_table(areas[areas.family == fam], cols, nd), ""]
    L += ["`[F]` Placement status of the primary area per row (from `docs/applications.md`): "
          + "; ".join(f"{r.family} {r.area}: {r.placement}" for r in areas[areas.area != "ALL (family total)"].itertuples()),
          ""]
    sel_cols = ["file", "family", "hqc_P0", "hqc_P2", "hqc_saved", "hqc_saved_pct", "shots_at_budget_P0",
                "shots_at_budget_P2", "extra_shots_at_budget", "extra_shots_pct", "T_written", "T_zx_P2", "magic_saved"]
    sel_nd = {c: 0 for c in ("shots_at_budget_P0", "shots_at_budget_P2", "extra_shots_at_budget",
                             "T_written", "T_zx_P2", "magic_saved")}
    L += ["## Selected circuits, shots at a fixed 10,000 HQC budget", "",
          md_table(sel, sel_cols, sel_nd), "",
          "`[F]` extra_shots_pct = 100 extra_shots_at_budget / shots_at_budget_P0.", ""]
    fa_cols = ["model", "n_circuits", "hqc_P0", "hqc_P2", "hqc_saved", "hqc_increase_P2_vs_P0_pct",
               "hqc_saved_pct_median", "n_P2_dearer", "n_P2_cheaper"]
    L += ["## Family A control (Trotter circuits)", "",
          md_table(fa, fa_cols, {"n_circuits": 0, "n_P2_dearer": 0, "n_P2_cheaper": 0}), "",
          "`[F]` hqc_increase_P2_vs_P0_pct = 100 (sum P2 - sum P0) / sum P0. A positive value means P2 costs more.", ""]
    L += ["## Family B2 (synthesised Haar unitaries) and certified B1 circuits", "",
          "| quantity | value |", "|---|---|",
          f"| B2 circuits | {b2['n_circuits']} |",
          f"| B2 T written | {fmt(int(b2['T_written']), 0)} |",
          f"| B2 T after ZX | {fmt(int(b2['T_after_zx']), 0)} |",
          f"| B2 magic states saved | {fmt(int(b2['magic_saved']), 0)} |",
          f"| B2 magic states saved, percent of written | {b2['magic_saved_pct']:.1f} |",
          f"| B2 certified floor (sum) | {fmt(int(b2['cert_floor']), 0)} |",
          f"| B2 T above the floor after ZX | {fmt(int(b2['above_floor']), 0)} |",
          f"| B2 certified-incompressible fraction, pooled | {b2['certified_fraction_pooled']:.3f} |",
          f"| B2 maximum further gain of any exact rewrite, pooled, percent of T after ZX | {b2['max_further_gain_pct_pooled']:.1f} |",
          f"| B2 certified-incompressible fraction, worst instance | {b2['certified_fraction_min']:.3f} |",
          f"| B2 maximum further gain, worst instance, percent | {b2['max_further_gain_pct_worst_instance']:.1f} |",
          f"| B1 certified circuits | {b1c['n_circuits']} ({b1c['circuits']}) |",
          f"| B1 certified circuits, T after ZX (sum) | {int(b1c['T_after_zx'])} |",
          f"| B1 certified circuits, floor (sum) | {int(b1c['cert_floor'])} |",
          f"| B1 certified circuits, certified fraction, pooled | {b1c['certified_fraction_pooled']:.3f} |",
          ""]
    L += ["## H2-2E emulator runs (context, 1000 shots)", "",
          md_table(h2, ["file", "pipeline", "n_2q", "F_H", "hqc"], {"n_2q": 0, "F_H": 3}), "",
          f"`[F]` Total HQC estimate of the {len(h2)} jobs: {h2_tot:,.1f}. Each job's `hqc_estimate` equals the "
          "ledger value for its circuit and pipeline (asserted by the script).", ""]
    L += ["## Per-circuit assignment", "",
          md_table(amap, ["file", "area", "placement", "secondary_areas"]), ""]
    (OUT / "value_by_application.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
