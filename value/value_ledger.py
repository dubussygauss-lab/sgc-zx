"""Value ledger: translate existing compile results into HQC and magic-state terms.

No new experiments.  Every number in value/value_ledger.csv and value/value_ledger.md
is computed here from CSVs already in results/ and bench/.

Inputs
  results/family_B1_counts.csv, results/family_B1x_counts.csv (count-only, unchecked),
  results/family_A_counts.csv, results/family_B2_counts.csv, results/certificates.csv,
  bench/family_B1/manifest.csv, bench/family_B1x/manifest.csv,
  results/proxy_h22e_fits.log (B1 slope a), noise/h2_params.py (H2-2E p2).

HQC (pipelines/compile.py hqc(), Quantinuum sg_grand_challenge estimate_cost):
  HQC = 5 + C (N_1q + 10 N_2q + 5 N_spam) / 5000,
  N_1q = PhasedX, N_2q = ZZPhase + ZZMax, N_spam = n_qubits + Measure + Reset.
The counts CSVs store hqc at SHOTS = 1000.  The per-shot weight
k = N_1q + 10 N_2q + 5 N_spam is recovered as k = (hqc - 5) * 5000 / 1000.

Run: python3 value/value_ledger.py
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "value"
sys.path.insert(0, str(ROOT))

SHOTS_CSV = 1000          # SHOTS in pipelines/compile.py; hqc column is at this shot count
SHOTS = 1000              # shot count for the ledger
BUDGET = 10_000           # HQC budget for the shots-affordable column
FIT_LOG = ROOT / "results/proxy_h22e_fits.log"
# largest n_2q among the 35 B1 rows the slope a was fitted on
FIT_N2Q_MAX = int(pd.read_csv(ROOT / "results/family_B1_proxy_h22e.csv").n_2q.max())


# ---------------------------------------------------------------- inputs
def read_fit_slope():
    """Return (a, line_number, line_text) for the B1 fit '-ln F_H = a n_2q only'."""
    lines = FIT_LOG.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Family B1"))
    for i in range(start, len(lines)):
        if "a n_2q only" in lines[i]:
            m = re.search(r"a = ([0-9.eE+-]+)", lines[i])
            return float(m.group(1)), i + 1, lines[i].strip()
        if i > start and lines[i].startswith(("Family", "A + B1")) and i != start:
            break
    raise RuntimeError("B1 'a n_2q only' fit line not found in %s" % FIT_LOG)


def read_p2():
    from noise.h2_params import H2_2E_EMULATOR
    return H2_2E_EMULATOR["p2"]


def per_shot_weight(hqc):
    return (hqc - 5) * 5000 / SHOTS_CSV


def hqc_at(k, shots):
    return 5 + shots * k / 5000


def shots_affordable(k, budget):
    return np.floor((budget - 5) * 5000 / k).astype(int)


# ---------------------------------------------------------------- NISQ layer
def nisq_layer(family, path, a, p2, manifest=None, check_status=None):
    d = pd.read_csv(ROOT / path)
    if check_status is not None:
        assert set(d.status) == {check_status}, (path, set(d.status))
    p0 = d[d.pipeline == "P0"].set_index("file")
    p2r = d[d.pipeline == "P2"].set_index("file")
    files = list(p0.index)
    assert set(files) == set(p2r.index), path
    if manifest is not None:
        m = pd.read_csv(ROOT / manifest)
        assert set(m.file) == set(files), (manifest, set(m.file) ^ set(files))
    r = pd.DataFrame(index=files)
    r.index.name = "file"
    r["n_qubits"] = p0.n_qubits.astype(int)
    r["n2q_P0"] = p0.n_2q.astype(int)
    r["n2q_P2"] = p2r.loc[files, "n_2q"].astype(int)
    r["n1q_P0"] = p0.n_phasedx.astype(int)
    r["n1q_P2"] = p2r.loc[files, "n_phasedx"].astype(int)
    k0 = per_shot_weight(p0.hqc)
    k2 = per_shot_weight(p2r.loc[files, "hqc"])
    # consistency of the stored hqc with the stored counts (spam = 2 n_qubits: all qubits measured)
    k0_counts = r.n1q_P0 + 10 * r.n2q_P0 + 5 * 2 * r.n_qubits
    k2_counts = r.n1q_P2 + 10 * r.n2q_P2 + 5 * 2 * r.n_qubits
    assert np.allclose(k0, k0_counts) and np.allclose(k2, k2_counts), path
    r["hqc_P0"] = hqc_at(k0, SHOTS)
    r["hqc_P2"] = hqc_at(k2, SHOTS)
    r["hqc_saved"] = r.hqc_P0 - r.hqc_P2
    r["hqc_saved_pct"] = 100 * r.hqc_saved / r.hqc_P0
    r["shots_at_budget_P0"] = shots_affordable(k0.values, BUDGET)
    r["shots_at_budget_P2"] = shots_affordable(k2.values, BUDGET)
    r["extra_shots_at_budget"] = r.shots_at_budget_P2 - r.shots_at_budget_P0
    r["dN2q"] = r.n2q_P0 - r.n2q_P2
    r["F_ratio_fit_a"] = np.exp(a * r.dN2q)
    r["F_gain_pct_fit_a"] = 100 * (r.F_ratio_fit_a - 1)
    r["F_P0_model_fit_a"] = np.exp(-a * r.n2q_P0)
    r["fit_extrapolated"] = r.n2q_P0 > FIT_N2Q_MAX
    r["F_ratio_p2"] = np.exp(p2 * r.dN2q)
    r["F_gain_pct_p2"] = 100 * (r.F_ratio_p2 - 1)
    r.insert(0, "family", family)
    r.insert(0, "layer", "NISQ")
    return r.reset_index()


# ---------------------------------------------------------------- FT layer
def ft_layer(family, path, tcol_zx, certs, manifest=None, check_status=None):
    d = pd.read_csv(ROOT / path)
    if check_status is not None:
        assert set(d.status) == {check_status}, (path, set(d.status))
    p2r = d[d.pipeline == "P2"].set_index("file")
    if manifest is not None:
        m = pd.read_csv(ROOT / manifest).set_index("file")
        assert set(m.index) == set(p2r.index)
        assert (m.loc[p2r.index, "t_count_as_written"].values
                == p2r.t_count_written.astype(int).values).all(), "manifest T-count mismatch"
    r = pd.DataFrame(index=p2r.index)
    r.index.name = "file"
    r["T_written"] = p2r.t_count_written.astype(int)
    r["T_zx_P2"] = p2r[tcol_zx].astype(int)
    if "n_non_cliffordT_zx" in p2r:
        r["non_cliffordT_phases_zx"] = p2r.n_non_cliffordT_zx.astype(int)
    r["T_saved"] = r.T_written - r.T_zx_P2
    r["T_saved_pct"] = 100 * r.T_saved / r.T_written
    # one |T> magic state per T gate (Litinski, Quantum 3, 128 (2019))
    r["magic_written"] = r.T_written
    r["magic_zx_P2"] = r.T_zx_P2
    r["magic_saved"] = r.T_saved
    c = certs[certs.family == family].set_index("file")
    r["cert_floor"] = np.nan
    r["cert_gap"] = np.nan
    r["cert_incompressible_frac_of_remaining"] = np.nan
    if len(c):
        assert c.sound.all() and (c.criterion_violations == 0).all() and c.invariant_ok.all()
        assert (c.t_written == r.loc[c.index, "T_written"]).all(), "cert t_written mismatch"
        assert (c.t_zx_P2 == r.loc[c.index, "T_zx_P2"]).all(), "cert t_zx_P2 mismatch"
        r.loc[c.index, "cert_floor"] = c.lde_floor
        r.loc[c.index, "cert_gap"] = r.loc[c.index, "T_zx_P2"] - c.lde_floor
        r.loc[c.index, "cert_incompressible_frac_of_remaining"] = (
            c.lde_floor / r.loc[c.index, "T_zx_P2"])
    r.insert(0, "family", family)
    r.insert(0, "layer", "FT")
    return r.reset_index()


def total_row(df, sum_cols):
    t = {c: df[c].sum() for c in sum_cols}
    t.update(layer=df.layer.iloc[0], family=df.family.iloc[0], file="TOTAL")
    return t


def fmt(x, nd=1):
    if isinstance(x, (int, np.integer)):
        return f"{x:,}"
    if pd.isna(x):
        return ""
    return f"{x:,.{nd}f}"


def md_table(df, cols, nd):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    body = ""
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, str):
                cells.append(v)
            elif isinstance(v, (bool, np.bool_)):
                cells.append("yes" if v else "no")
            elif isinstance(v, (float, np.floating)) and not pd.isna(v) and float(v).is_integer() \
                    and nd.get(c, 1) == 0:
                cells.append(f"{int(v):,}")
            else:
                cells.append(fmt(v, nd.get(c, 1)))
        body += "| " + " | ".join(cells) + " |\n"
    return head + body


def main():
    a, a_line, a_text = read_fit_slope()
    p2 = read_p2()
    certs = pd.read_csv(ROOT / "results/certificates.csv")

    nisq = {
        "B1": nisq_layer("B1", "results/family_B1_counts.csv", a, p2,
                         "bench/family_B1/manifest.csv", "ok"),
        "B1x": nisq_layer("B1x", "results/family_B1x_counts.csv", a, p2,
                          "bench/family_B1x/manifest.csv", "ok-unchecked"),
        "A": nisq_layer("A", "results/family_A_counts.csv", a, p2, None, "ok"),
    }
    ft = {
        "B1": ft_layer("B1", "results/family_B1_counts.csv", "t_count_zx", certs,
                       "bench/family_B1/manifest.csv", "ok"),
        "B1x": ft_layer("B1x", "results/family_B1x_counts.csv", "t_count_zx", certs,
                        "bench/family_B1x/manifest.csv", "ok-unchecked"),
        "B2": ft_layer("B2", "results/family_B2_counts.csv", "t_count_after_zx", certs,
                       None, "ok"),
    }

    nisq_sum = ["n2q_P0", "n2q_P2", "n1q_P0", "n1q_P2", "hqc_P0", "hqc_P2", "hqc_saved", "dN2q"]
    ft_sum = ["T_written", "T_zx_P2", "T_saved", "magic_written", "magic_zx_P2", "magic_saved"]
    rows = []
    totals = {}
    for fam, df in nisq.items():
        t = total_row(df, nisq_sum)
        t["hqc_saved_pct"] = 100 * t["hqc_saved"] / t["hqc_P0"]
        totals[("NISQ", fam)] = t
        rows += [df, pd.DataFrame([t])]
    for fam, df in ft.items():
        t = total_row(df, ft_sum)
        t["T_saved_pct"] = 100 * t["T_saved"] / t["T_written"]
        cert = df.dropna(subset=["cert_floor"])
        if len(cert):
            t["cert_floor"] = cert.cert_floor.sum()
            t["cert_gap"] = cert.cert_gap.sum()
            t["cert_incompressible_frac_of_remaining"] = cert.cert_floor.sum() / cert.T_zx_P2.sum()
        totals[("FT", fam)] = t
        rows += [df, pd.DataFrame([t])]
    ledger = pd.concat(rows, ignore_index=True)
    ledger.insert(3, "row_kind", np.where(ledger.file == "TOTAL", "total", "circuit"))
    ledger.to_csv(OUT / "value_ledger.csv", index=False)

    # ------------------------------------------------------------ headlines
    b1 = nisq["B1"]
    i_max = b1.hqc_saved.idxmax()
    i_maxpct = b1.hqc_saved_pct.idxmax()
    b1_wo = b1[b1.file != "hwb8.qasm"]
    b2c = ft["B2"].dropna(subset=["cert_floor"])
    H = {
        "B1 total HQC saved at 1000 shots (P2 vs P0)": totals[("NISQ", "B1")]["hqc_saved"],
        "B1 total HQC P0": totals[("NISQ", "B1")]["hqc_P0"],
        "B1 total HQC P2": totals[("NISQ", "B1")]["hqc_P2"],
        "B1 total HQC saved, percent of P0 total": totals[("NISQ", "B1")]["hqc_saved_pct"],
        "B1 total HQC saved excluding hwb8": b1_wo.hqc_saved.sum(),
        "B1 median per-circuit HQC saved percent": b1.hqc_saved_pct.median(),
        "B1 circuits with HQC saved > 0 / total": f"{(b1.hqc_saved > 0).sum()} / {len(b1)}",
        "B1 largest single HQC saving": f"{b1.hqc_saved[i_max]:.1f} HQC ({b1.file[i_max]}, "
                                        f"{b1.hqc_saved_pct[i_max]:.1f}%)",
        "B1 largest single HQC saving in percent": f"{b1.hqc_saved_pct[i_maxpct]:.1f}% "
                                                   f"({b1.file[i_maxpct]})",
        "B1x total HQC saved at 1000 shots (unchecked)": totals[("NISQ", "B1x")]["hqc_saved"],
        "B1x median per-circuit HQC saved percent (unchecked)": nisq["B1x"].hqc_saved_pct.median(),
        "A (control) total HQC saved at 1000 shots": totals[("NISQ", "A")]["hqc_saved"],
        "A (control) median per-circuit HQC saved percent": nisq["A"].hqc_saved_pct.median(),
        "A (control) circuits with HQC saved > 0 / < 0 / = 0":
            f"{(nisq['A'].hqc_saved > 0).sum()} / {(nisq['A'].hqc_saved < 0).sum()} / "
            f"{(nisq['A'].hqc_saved == 0).sum()}",
        "B1 median per-circuit model fidelity gain percent, fit a [O]": b1.F_gain_pct_fit_a.median(),
        "B1 circuits outside the fit range (n_2q P0 > fit max)":
            ", ".join(b1.file[b1.fit_extrapolated]),
        "B1 T / magic states saved": totals[("FT", "B1")]["T_saved"],
        "B1 T saved percent of written": totals[("FT", "B1")]["T_saved_pct"],
        "B1x T / magic states saved (unchecked)": totals[("FT", "B1x")]["T_saved"],
        "B1x T saved percent of written (unchecked)": totals[("FT", "B1x")]["T_saved_pct"],
        "B2 T / magic states saved": totals[("FT", "B2")]["T_saved"],
        "B2 T saved percent of written": totals[("FT", "B2")]["T_saved_pct"],
        "B2 certified-incompressible fraction of remaining T (pooled)":
            totals[("FT", "B2")]["cert_incompressible_frac_of_remaining"],
        "B2 certified-incompressible fraction, per-circuit median":
            b2c.cert_incompressible_frac_of_remaining.median(),
        "B2 certified-incompressible fraction, per-circuit min":
            b2c.cert_incompressible_frac_of_remaining.min(),
        "B2 T gates above certified floor after ZX (pooled)": totals[("FT", "B2")]["cert_gap"],
        "B1 (4 certified circuits) certified-incompressible fraction (pooled)":
            totals[("FT", "B1")]["cert_incompressible_frac_of_remaining"],
    }
    pd.Series(H, name="value").to_csv(OUT / "value_headlines.csv", header=True)

    # ------------------------------------------------------------ markdown
    def hv(k, nd=1):
        v = H[k]
        return v if isinstance(v, str) else fmt(v, nd)

    nisq_cols = ["file", "n_qubits", "n2q_P0", "n2q_P2", "hqc_P0", "hqc_P2", "hqc_saved",
                 "hqc_saved_pct", "shots_at_budget_P0", "shots_at_budget_P2",
                 "extra_shots_at_budget", "dN2q", "F_P0_model_fit_a", "F_gain_pct_fit_a", "F_gain_pct_p2",
                 "fit_extrapolated"]
    nd_n = dict(n_qubits=0, n2q_P0=0, n2q_P2=0, dN2q=0, shots_at_budget_P0=0,
                shots_at_budget_P2=0, extra_shots_at_budget=0, hqc_P0=1, hqc_P2=1,
                hqc_saved=1, hqc_saved_pct=1, F_P0_model_fit_a=4, F_gain_pct_fit_a=2, F_gain_pct_p2=2)
    ft_cols = ["file", "T_written", "T_zx_P2", "T_saved", "T_saved_pct", "magic_zx_P2",
               "cert_floor", "cert_gap", "cert_incompressible_frac_of_remaining"]
    nd_f = dict(T_written=0, T_zx_P2=0, T_saved=0, T_saved_pct=1, magic_zx_P2=0,
                cert_floor=0, cert_gap=0, cert_incompressible_frac_of_remaining=3)

    def with_total(df, key):
        t = pd.DataFrame([totals[key]])
        return pd.concat([df, t], ignore_index=True)

    A = nisq["A"]
    A_by_model = A.assign(model=A.file.str.split("_").str[0]).groupby("model").agg(
        circuits=("file", "size"), hqc_P0=("hqc_P0", "sum"), hqc_P2=("hqc_P2", "sum"),
        hqc_saved=("hqc_saved", "sum"), median_pct=("hqc_saved_pct", "median")).reset_index()

    md = []
    md.append("# Value ledger: HQC and magic-state accounting\n")
    md.append("Generated by `value/value_ledger.py` from existing CSVs. No number in this file "
              "is typed by hand. No new experiments.\n")
    md.append("## Headline numbers\n")
    md.append("| quantity | value |\n|---|---|")
    for k in H:
        nd = 3 if "fraction" in k else (2 if "fidelity" in k else 1)
        md.append(f"| {k} | {hv(k, nd)} |")
    md.append("")
    md.append("## Sources and definitions\n")
    md.append(f"- `[F]` HQC = 5 + C (N_1q + 10 N_2q + 5 N_spam)/5000 (`pipelines/compile.py` "
              f"`hqc()`), N_1q = PhasedX, N_2q = ZZPhase + ZZMax, N_spam = n_qubits + Measure + "
              f"Reset. Here every qubit is measured once, so N_spam = 2 n_qubits (checked against "
              f"the stored `hqc` column for every row). C = {SHOTS} shots.")
    md.append(f"- `[F]` Shots affordable at a fixed budget of {BUDGET:,} HQC: "
              f"floor((B - 5) 5000 / (N_1q + 10 N_2q + 5 N_spam)).")
    md.append(f"- `[F]` Fit slope a = {a:.4e} per two-qubit gate, read from "
              f"`results/proxy_h22e_fits.log` line {a_line}, Family B1 section: `{a_text}`.")
    md.append(f"- `[F]` p2 = {p2:.3g}, H2-2E emulator default two-qubit fault probability, "
              f"`noise/h2_params.py` `H2_2E_EMULATOR['p2']`.")
    md.append("- `[O]` Fidelity columns are model predictions, not measurements: "
              "F_P2/F_P0 = exp(a dN_2q) with dN_2q = N_2q(P0) - N_2q(P2), and the same with p2 "
              "in place of a. The slope a comes from a local density-matrix proxy fit of "
              "-ln F_H on 35 B1 rows. It assumes all fidelity loss scales with the two-qubit "
              "count and ignores the single-qubit and depth differences between P0 and P2. "
              f"The fit rows span n_2q <= {FIT_N2Q_MAX} (`results/family_B1_proxy_h22e.csv`). "
              "Rows with `fit_extrapolated = True` lie outside that range and their fidelity "
              "numbers are extrapolations. F_P0_model_fit_a = exp(-a N_2q(P0)) is shown so the "
              "reader sees when the absolute fidelity is already negligible.")
    md.append("- `[F]` One |T> magic state is consumed per T gate: Litinski, \"A Game of Surface "
              "Codes: Large-Scale Quantum Computing with Lattice Surgery\", Quantum 3, 128 (2019), "
              "doi:10.22331/q-2019-03-05-128, arXiv:1808.02892. Section 2 of the arXiv version: "
              "\"Clifford+T circuits are a sequence of pi/8 rotations, each requiring the "
              "consumption of a magic state\". Magic-state counts below are therefore equal to "
              "T-counts.")
    md.append("- `[F]` T_zx_P2 is the PyZX T-count after the ZX stage of P2 (`t_count_zx` in the "
              "B1/B1x CSVs, `t_count_after_zx` in B2). `n_non_cliffordT_zx` is 0 on every B1 and "
              "B1x P2 row, so no non-Clifford+T phase is left uncounted.")
    md.append("- `[F]` Certified floor = `lde_floor` in `results/certificates.csv` (all rows "
              "`sound = True`, 0 criterion violations). Incompressible fraction of the remaining "
              "T-count = floor / T_zx_P2. The script asserts that `t_written` and `t_zx_P2` in "
              "the certificate file equal the counts CSVs.")
    md.append("- `[F]` B1x rows have `status = ok-unchecked`: counts only, no equivalence check. "
              "B1 and B1x are reported separately and never merged.")
    md.append("- `[O]` Conversion of magic-state counts to wall-clock time, qubit overhead or "
              "cost on Helios or H2 needs device-specific factory and logical-cycle figures. No "
              "Quantinuum source found in this pass states such a conversion, so none is made.")
    md.append("- `[F]` Context only, not used in any number above: Dasu et al. (Quantinuum), "
              "\"Breaking even with magic: demonstration of a high-fidelity logical non-Clifford "
              "gate\", arXiv:2506.14688 (https://arxiv.org/abs/2506.14688), report on H1-1 a "
              "logical magic state with experimental infidelity 7(+3/-1) x 10^-5 and a logical "
              "CH gate with infidelity <= 2.3(9) x 10^-4. The abstract gives no per-magic-state "
              "time or HQC cost.")
    md.append("")
    md.append(f"## NISQ layer, family B1 (P2 vs P0, {SHOTS} shots, budget {BUDGET:,} HQC)\n")
    md.append(md_table(with_total(nisq["B1"], ("NISQ", "B1")), nisq_cols, nd_n))
    md.append("`[F]` hwb8 accounts for "
              f"{fmt(100 * b1.hqc_saved[b1.file == 'hwb8.qasm'].iloc[0] / b1.hqc_saved.sum(), 1)}% "
              "of the B1 total HQC saved.\n")
    md.append(f"## NISQ layer, family B1x (count-only, unchecked)\n")
    md.append(md_table(with_total(nisq["B1x"], ("NISQ", "B1x")), nisq_cols, nd_n))
    md.append("## NISQ layer, family A (control), totals by model\n")
    md.append(md_table(A_by_model, ["model", "circuits", "hqc_P0", "hqc_P2", "hqc_saved",
                                    "median_pct"],
                       dict(circuits=0, hqc_P0=1, hqc_P2=1, hqc_saved=1, median_pct=1)))
    md.append(f"`[F]` Family A over all {len(A)} circuits: total HQC P0 "
              f"{fmt(totals[('NISQ', 'A')]['hqc_P0'])}, P2 {fmt(totals[('NISQ', 'A')]['hqc_P2'])}, "
              f"saved {fmt(totals[('NISQ', 'A')]['hqc_saved'])}. Per-circuit rows are in "
              f"`value/value_ledger.csv`.\n")
    md.append("## Fault-tolerant layer, family B1\n")
    md.append(md_table(with_total(ft["B1"], ("FT", "B1")), ft_cols, nd_f))
    md.append("## Fault-tolerant layer, family B1x (count-only, unchecked)\n")
    md.append(md_table(with_total(ft["B1x"], ("FT", "B1x")), ft_cols, nd_f))
    md.append("## Fault-tolerant layer, family B2\n")
    md.append(md_table(with_total(ft["B2"], ("FT", "B2")), ft_cols, nd_f))
    md.append("TOTAL rows: cert columns sum over certified circuits only, and the fraction is "
              "pooled (sum of floors / sum of T_zx_P2 over certified circuits).\n")
    (OUT / "value_ledger.md").write_text("\n".join(md))
    print("\n".join(f"{k}: {hv(k, 3)}" for k in H))


if __name__ == "__main__":
    main()
