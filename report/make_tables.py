"""Generate the tables and figures of report/report_v1.md from results/*.csv.

Every number in the report's tables comes from this script.  Nothing is typed
by hand.  Run from the repository root:

    python report/make_tables.py            # writes report/tables/*.md and
                                            # report/figures/*.png, then injects
                                            # the tables into report/report_v1.md
    python report/make_tables.py --no-inject

Injection: the report carries marker pairs

    <!-- TABLE:name -->
    ...
    <!-- /TABLE:name -->

and the block between a pair is replaced by report/tables/<name>.md.

Inputs (all under results/)
  family_A_counts.csv   180 Trotter circuits x 7 pipelines
  family_A_proxy_h22e.csv  local density-matrix noise proxy (H2-2E parameters), family A, n <= 8
  family_B1_counts.csv  15 Clifford+T benchmark circuits x 7 pipelines
  family_B2_counts.csv  20 QSD + gridsynth Haar circuits x 5 pipelines
  family_B1_proxy_h22e.csv  local density-matrix noise proxy (H2-2E parameters), family B1, n <= 7
  certificates.csv      exactness-barrier certificate, 20 family B2 + 4 family B1 circuits
  selene_noiseless.csv, selene_depolarizing.csv  Selene local-emulator runs
  cost_model_metrics.csv, cost_model_coefficients.csv, fig_cost_model.png
                        written by model/cost_model.py (tables M1, M2 and the
                        cost-model figure of Section 4)

The marker injection runs on report/report_v1.md, report/report_v2.md and
every report/v2/part*.md that exists.

Definitions used below
  n_2q           ZZPhase + ZZMax count of the compiled native circuit
  depth_2q       two-qubit depth of the compiled native circuit
  hqc            5 + C (N_1q + 10 N_2q + 5 N_M) / 5000 with C = 1000,
                 N_1q = PhasedX count, N_M = 2 n_qubits (initialisation plus
                 one terminal measurement per qubit), as computed by
                 pipelines/compile.py:hqc
  ratio to P0    n_2q[pipeline] / n_2q[P0] on the same circuit, then averaged
  reduction %    100 (1 - x[pipeline] / x[P0]) on the same circuit
  T after ZX     T-count of the pyzx circuit after the ZX stage, before any
                 pytket pass (column t_count_zx in B1, t_count_after_zx in B2)
  ZZ term count  n_cx / 2 of the Trotter circuit as written: one ZZ-type
                 Pauli exponential per cx pair
"""

import argparse
import glob
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
TABLES = os.path.join(ROOT, "report", "tables")
FIGURES = os.path.join(ROOT, "report", "figures")
REPORT = os.path.join(ROOT, "report", "report_v1.md")
REPORT_V2 = os.path.join(ROOT, "report", "report_v2.md")

PIPELINES_A = ["P0ref", "P0", "P0L1", "P1", "P2", "P3", "P4"]
PIPELINES_B2 = ["P0ref", "P0", "P1", "P2", "P3"]
LABEL = {
    "P0ref": "P0ref (rebase only)",
    "P0": "P0 (pytket L2)",
    "P0L1": "P0L1 (pytket L1)",
    "P1": "P1 (full_reduce)",
    "P2": "P2 (teleport_reduce)",
    "P3": "P3 (ZXGraphlike)",
    "P4": "P4 (full_reduce, no peephole)",
}
# Categorical palette, fixed slot order (dataviz reference palette, light).
COLOR = {
    "P0ref": "#2a78d6",
    "P0": "#eb6834",
    "P1": "#1baf7a",
    "P2": "#eda100",
    "P3": "#e87ba4",
    "P4": "#008300",
}


INT_COLUMNS = {"n", "r", "circuits", "circuits per pipeline", "T written",
               "better than P0", "equal to P0", "worse than P0",
               "circuits with n_2q = ZZ terms", "T after ZX",
               "ZZ P0ref", "ZZ P0", "ZZ P0L1", "ZZ P1", "ZZ P2", "ZZ P3", "ZZ P4",
               "support", "floor", "runs", "shots per run", "flagged (TVD > 4 TVD_scale)",
               "shots outside support", "abs z <= 2"}


def md_table(df: pd.DataFrame, floatfmt="{:.1f}", fmt: dict = None) -> str:
    """Markdown table.  Columns named in INT_COLUMNS print as integers,
    `fmt` maps a column name to its own format string."""
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, (float, np.floating, int, np.integer)) and not isinstance(v, bool):
                if isinstance(v, (float, np.floating)) and np.isnan(v):
                    cells.append("")
                elif c in INT_COLUMNS:
                    cells.append(str(int(v)))
                else:
                    cells.append(fmt.get(c, floatfmt).format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def write(name: str, text: str):
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name + ".md"), "w") as f:
        f.write(text)


# ------------------------------------------------------------------ family A

def family_a(fig=True):
    a = pd.read_csv(os.path.join(RESULTS, "family_A_counts.csv"))
    assert (a.status == "ok").all() and a.check_ok.all(), "family A has failed rows"
    n_circ = a.file.nunique()
    piv = a.pivot_table(index="file", columns="pipeline", values="n_2q")
    meta = a[a.pipeline == "P0"].set_index("file")[["model", "n", "r", "disorder", "n_cx"]]

    # Table A1: mean ZZPhase count by n and pipeline (36 circuits per n)
    rows = []
    for n, grp in meta.groupby("n"):
        files = grp.index
        row = {"n": int(n), "circuits": len(files), "ZZ terms": float(grp.n_cx.mean() / 2)}
        for p in PIPELINES_A:
            row[p] = float(piv.loc[files, p].mean())
        rows.append(row)
    t_a1 = pd.DataFrame(rows)
    write("A1_zz_by_n", md_table(t_a1))

    # Table A2: every pipeline against P0 on the same circuit
    rows = []
    for p in PIPELINES_A:
        if p == "P0":
            continue
        r = piv[p] / piv["P0"]
        d = a.pivot_table(index="file", columns="pipeline", values="depth_2q")
        h = a.pivot_table(index="file", columns="pipeline", values="hqc")
        rows.append({
            "pipeline": p,
            "better than P0": int((piv[p] < piv["P0"]).sum()),
            "equal to P0": int((piv[p] == piv["P0"]).sum()),
            "worse than P0": int((piv[p] > piv["P0"]).sum()),
            "mean ZZ ratio": float(r.mean()),
            "min ZZ ratio": float(r.min()),
            "max ZZ ratio": float(r.max()),
            "mean 2q-depth ratio": float((d[p] / d["P0"]).mean()),
            "mean HQC ratio": float((h[p] / h["P0"]).mean()),
        })
    t_a2 = pd.DataFrame(rows)
    write("A2_vs_P0", md_table(t_a2, "{:.2f}"))

    # Table A3: P0 against the ZZ term count, by model and r
    p0 = a[a.pipeline == "P0"].copy()
    p0["zz_terms"] = p0.n_cx / 2
    rows = []
    for (m, r), grp in p0.groupby(["model", "r"]):
        rows.append({
            "model": m, "r": int(r), "circuits": len(grp),
            "mean ZZ terms": float(grp.zz_terms.mean()),
            "mean n_2q P0": float(grp.n_2q.mean()),
            "circuits with n_2q = ZZ terms": int((grp.n_2q == grp.zz_terms).sum()),
        })
    t_a3 = pd.DataFrame(rows)
    write("A3_floor", md_table(t_a3))
    at_floor = int((p0.n_2q == p0.zz_terms).sum())
    below = int((piv.min(axis=1) < (meta.n_cx / 2).reindex(piv.index)).sum())

    if fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(FIGURES, exist_ok=True)
        fig_, ax = plt.subplots(figsize=(6.4, 3.8))
        ns = sorted(meta.n.unique())
        for p in ["P0ref", "P1", "P2", "P3", "P4"]:
            ratio = (piv[p] / piv["P0"])
            means = [ratio[meta.n == n].mean() for n in ns]
            lo = [ratio[meta.n == n].min() for n in ns]
            hi = [ratio[meta.n == n].max() for n in ns]
            ax.plot(ns, means, color=COLOR[p], lw=2, marker="o", ms=5, label=LABEL[p])
            ax.fill_between(ns, lo, hi, color=COLOR[p], alpha=0.12, lw=0)
        ax.axhline(1.0, color="#888888", lw=1, ls="--", label=LABEL["P0"] + ", ratio 1")
        ax.set_xlabel("qubits n")
        ax.set_ylabel("ZZPhase count / ZZPhase count of P0")
        ax.set_title("Family A ZZPhase count relative to P0, mean with min-max band",
                     fontsize=10)
        ax.set_xticks(ns)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", lw=0.8)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        fig_.tight_layout()
        fig_.savefig(os.path.join(FIGURES, "fig_A_zz_ratio.png"), dpi=160)
        plt.close(fig_)

    return {"n_circuits": n_circ, "t_a1": t_a1, "t_a2": t_a2, "t_a3": t_a3,
            "p0_at_floor": at_floor, "any_below_floor": below,
            "p2_ties": int((piv["P2"] == piv["P0"]).sum()),
            "p2_worse": int((piv["P2"] > piv["P0"]).sum())}


# ------------------------------------------------------------ family A proxy

def family_a_proxy():
    path = os.path.join(RESULTS, "family_A_proxy_h22e.csv")
    if not os.path.exists(path):
        write("A4_proxy", "[PENDING: proxy rerun] results/family_A_proxy_h22e.csv not found.\n")
        return None
    pr = pd.read_csv(path)
    pipes = [p for p in ["P0ref", "P0", "P1", "P2", "P3"] if p in set(pr.pipeline)]
    rows = []
    for n, grp in pr.groupby("n"):
        row = {"n": int(n), "circuits per pipeline": int(grp.groupby("pipeline").size().max())}
        for p in pipes:
            g = grp[grp.pipeline == p]
            row[f"F_H {p}"] = float(g.F_H.mean())
        rows.append(row)
    t = pd.DataFrame(rows)
    rows2 = []
    for p in pipes:
        g = pr[pr.pipeline == p]
        rows2.append({"pipeline": p, "mean F_H": float(g.F_H.mean()),
                      "mean TVD": float(g.TVD.mean()),
                      "mean n_2q": round(float(g.n_2q.mean()), 1),
                      "mean n_1q": round(float(g.n_1q.mean()), 1)})
    t2 = pd.DataFrame(rows2)
    text = ("Provisional local proxy. Density-matrix simulation with the published "
            "H2-2E emulator parameters (p1 = 7.3e-5, p2 = 1.29e-3, readout 9e-4 and 1.8e-3, "
            "p_init = 4e-5) and no leakage, crosstalk or dephasing, to be replaced by emulator runs. "
            "Mean Hellinger fidelity F_H of the noisy output distribution against "
            "the ideal one.\n\n"
            + md_table(t, "{:.4f}") + "\n"
            + md_table(t2, "{:.4f}", fmt={"mean n_2q": "{:.1f}", "mean n_1q": "{:.1f}"}))
    write("A4_proxy", text)
    return {"t": t, "t2": t2}


# ----------------------------------------------------------------- family B1

def family_b1(fig=True):
    b = pd.read_csv(os.path.join(RESULTS, "family_B1_counts.csv"))
    piv = b.pivot_table(index="file", columns="pipeline", values="n_2q")
    tz = b.pivot_table(index="file", columns="pipeline", values="t_count_zx")
    st = b.pivot_table(index="file", columns="pipeline", values="status", aggfunc="first")
    meta = b[b.pipeline == "P0ref"].set_index("file")[["n", "t_count_written"]]
    order = meta.sort_values(["n", "t_count_written"]).index
    rows = []
    for f in order:
        row = {"circuit": f.replace(".qasm", ""), "n": int(meta.loc[f, "n"]),
               "T written": int(meta.loc[f, "t_count_written"])}
        for p in PIPELINES_A:
            v = piv.loc[f, p]
            row[f"ZZ {p}"] = "" if np.isnan(v) else int(v)
        v = piv.loc[f, "P2"]
        row["P2 vs P0 %"] = np.nan if np.isnan(v) else float(100 * (1 - v / piv.loc[f, "P0"]))
        tv = tz.loc[f, "P1"] if not np.isnan(tz.loc[f, "P1"]) else tz.loc[f, "P4"]
        row["T after ZX"] = "" if np.isnan(tv) else int(tv)
        bad = [p for p in PIPELINES_A if st.loc[f, p] != "ok"]
        row["note"] = "" if not bad else "timeout: " + ", ".join(bad)
        rows.append(row)
    t_b1 = pd.DataFrame(rows)
    write("B1_per_circuit", md_table(t_b1))

    done = piv.dropna(subset=["P2"])
    stats = {
        "n_circuits": int(piv.shape[0]),
        "p2_done": int(done.shape[0]),
        "p2_better": int((done["P2"] < done["P0"]).sum()),
        "p2_equal": int((done["P2"] == done["P0"]).sum()),
        "p2_worse": int((done["P2"] > done["P0"]).sum()),
        "p1_worse": int((piv["P1"] > piv["P0"]).sum()),
        "p1_done": int(piv["P1"].notna().sum()),
        "p3_worse": int((piv["P3"] > piv["P0"]).sum()),
        "p3_done": int(piv["P3"].notna().sum()),
        "p2_mean_red_pct": float((100 * (1 - done["P2"] / done["P0"])).mean()),
        "t_zx_agree": bool(((tz["P1"] == tz["P2"]) | tz["P1"].isna() | tz["P2"].isna()).all()),
    }
    if fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(FIGURES, exist_ok=True)
        sub = t_b1[t_b1.circuit != "hwb8"]
        x = np.arange(len(sub))
        w = 0.26
        fig_, ax = plt.subplots(figsize=(8.5, 3.8))
        for i, p in enumerate(["P0ref", "P0", "P2"]):
            vals = [int(v) for v in sub[f"ZZ {p}"]]
            ax.bar(x + (i - 1) * w, vals, width=w - 0.03, color=COLOR[p], label=LABEL[p])
        ax.set_xticks(x)
        ax.set_xticklabels(sub.circuit, rotation=40, ha="right", fontsize=8)
        ax.set_yscale("log")
        ax.set_yticks([10, 20, 50, 100, 200, 300])
        ax.set_yticklabels(["10", "20", "50", "100", "200", "300"])
        ax.set_ylabel("ZZPhase count (log scale)")
        ax.set_title("Family B1 ZZPhase count per circuit, hwb8 omitted", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", lw=0.8)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=8)
        fig_.tight_layout()
        fig_.savefig(os.path.join(FIGURES, "fig_B1_zz.png"), dpi=160)
        plt.close(fig_)
    return {"t_b1": t_b1, **stats}


# ----------------------------------------------------------------- family B2

def family_b2(fig=True):
    c = pd.read_csv(os.path.join(RESULTS, "family_B2_counts.csv"))
    assert (c.status == "ok").all()
    rows = []
    for (n, eps), grp in c.groupby(["n", "eps"]):
        p0 = grp[grp.pipeline == "P0"]
        row = {"n": int(n), "eps": f"{eps:g}", "circuits": int(p0.shape[0]),
               "mean T written": float(p0.t_count_written.mean())}
        for p in ["P1", "P2", "P3"]:
            g = grp[grp.pipeline == p]
            row[f"T after ZX {p}"] = float(g.t_count_after_zx.mean())
            row[f"T red. % {p}"] = float((100 * (1 - g.t_count_after_zx / g.t_count_written)).mean())
        row["ZZ P0"] = float(p0.n_2q.mean())
        row["ZZ P2"] = float(grp[grp.pipeline == "P2"].n_2q.mean())
        row["HQC P0"] = float(p0.hqc.mean())
        row["max target dev."] = float(grp.target_dev.max())
        rows.append(row)
    t_b2 = pd.DataFrame(rows)
    write("B2_summary", md_table(t_b2, "{:.1f}", fmt={"max target dev.": "{:.1e}"}))
    dev = c.groupby(["n", "eps"]).target_dev.max()
    red = {}
    for p in ["P1", "P2", "P3"]:
        g = c[c.pipeline == p]
        red[p] = (100 * (1 - g.t_count_after_zx / g.t_count_written))
    if fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(FIGURES, exist_ok=True)
        fig_, ax = plt.subplots(figsize=(6.4, 3.6))
        groups = list(c.groupby(["n", "eps"]).groups.keys())
        x = np.arange(len(groups))
        w = 0.26
        for i, p in enumerate(["P1", "P2", "P3"]):
            vals = []
            for (n, eps) in groups:
                g = c[(c.n == n) & (c.eps == eps) & (c.pipeline == p)]
                vals.append((100 * (1 - g.t_count_after_zx / g.t_count_written)).mean())
            ax.bar(x + (i - 1) * w, vals, width=w - 0.03, color=COLOR[p], label=LABEL[p])
        ax.set_xticks(x)
        ax.set_xticklabels([f"n = {n}, eps = {eps:g}" for n, eps in groups], fontsize=8)
        ax.set_ylabel("T-count removed by the ZX stage (%)")
        ax.set_title("Family B2 mean T-count reduction by the ZX stage, 5 circuits per group",
                     fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", lw=0.8)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=8)
        fig_.tight_layout()
        fig_.savefig(os.path.join(FIGURES, "fig_B2_t.png"), dpi=160)
        plt.close(fig_)
    return {"t_b2": t_b2, "max_target_dev": dev, "red": red,
            "red_min": min(float(v.mean()) for v in red.values()),
            "red_max": max(float(v.mean()) for v in red.values())}


# -------------------------------------------------------------- cost model

COST_MODELS = ["physics", "ols", "ridge", "gbr"]
COST_FEATURES = ["n_2q", "n_1q", "n_qubits", "depth_2q", "support_size",
                 "log2_support", "n_2q_offsupport"]


def cost_model_metrics():
    """Table M1: one row per validation split, one cell 'R^2(y) / MAE(F_H)'
    per model, from results/cost_model_metrics.csv (written by
    model/cost_model.py).  y = -ln F_H."""
    path = os.path.join(RESULTS, "cost_model_metrics.csv")
    if not os.path.exists(path):
        write("M1_cost_metrics", "[PENDING: cost model] results/cost_model_metrics.csv not found.\n")
        return None
    m = pd.read_csv(path)
    rows_wanted = [
        ("lofo", "A", "B1"),
        ("lofo", "B1", "A"),
        ("lomo", "A minus ladder", "A ladder"),
        ("lomo", "A minus tfim", "A tfim"),
        ("lomo", "A minus xxz", "A xxz"),
        ("cv5", "A+B1 (4/5)", "A+B1 (1/5)"),
        ("cv5g", "A+B1 (4/5)", "A+B1 (1/5)"),
        ("cv5g", "A+B1 (4/5)", "A rows of fold"),
        ("cv5g", "A+B1 (4/5)", "B1 rows of fold"),
    ]
    models = [x for x in COST_MODELS if x in set(m.model)]
    rows = []
    for split, train, test in rows_wanted:
        sel = m[(m.split == split) & (m.train == train) & (m.test == test)]
        if sel.empty:
            continue
        row = {"split": split, "train": train, "test": test,
               "n": int(sel.n_test.iloc[0])}
        for mod in models:
            r = sel[sel.model == mod]
            row[mod] = "" if r.empty else "%.3f / %.4f" % (r.r2_y.iloc[0], r.mae_F.iloc[0])
        rows.append(row)
    t = pd.DataFrame(rows)
    write("M1_cost_metrics", md_table(t))
    return {"t": t, "m": m}


def cost_model_coefficients():
    """Table M2: one row per feature.  Physics baseline coefficient, OLS
    coefficient with t statistic for the three training sets, ridge
    coefficient on A+B1, GBR permutation importance (mean and sd over the
    circuit-grouped folds), from results/cost_model_coefficients.csv.
    Also copies results/fig_cost_model.png into report/figures/."""
    path = os.path.join(RESULTS, "cost_model_coefficients.csv")
    if not os.path.exists(path):
        write("M2_cost_coefficients", "[PENDING: cost model] results/cost_model_coefficients.csv not found.\n")
        return None
    c = pd.read_csv(path)

    def cell(model, train, feature, kind, with_t=False, with_sd=False):
        r = c[(c.model == model) & (c.train == train) & (c.feature == feature) & (c.kind == kind)]
        if r.empty:
            return ""
        v = float(r.value.iloc[0])
        if with_t and not np.isnan(r.t.iloc[0]):
            return "%.2e (%.1f)" % (v, float(r.t.iloc[0]))
        if with_sd and not np.isnan(r.se.iloc[0]):
            return "%.2e (%.1e)" % (v, float(r.se.iloc[0]))
        return "%.2e" % v

    rows = []
    for f in COST_FEATURES:
        rows.append({
            "feature": f,
            "physics": cell("physics", "none", f, "coefficient"),
            "OLS A (t)": cell("ols", "A", f, "coefficient", with_t=True),
            "OLS B1 (t)": cell("ols", "B1", f, "coefficient", with_t=True),
            "OLS A+B1 (t)": cell("ols", "A+B1", f, "coefficient", with_t=True),
            "ridge A+B1": cell("ridge", "A+B1", f, "coefficient"),
            "GBR importance (sd)": cell("gbr", "A+B1 (cv5g out-of-fold)", f,
                                        "permutation_importance", with_sd=True),
        })
    t = pd.DataFrame(rows)
    write("M2_cost_coefficients", md_table(t))
    src = os.path.join(RESULTS, "fig_cost_model.png")
    if os.path.exists(src):
        import shutil
        os.makedirs(FIGURES, exist_ok=True)
        shutil.copyfile(src, os.path.join(FIGURES, "fig_cost_model.png"))
    resid = {tr: float(c[(c.model == "ols") & (c.train == tr) & (c.feature == "resid_sd")].value.iloc[0])
             for tr in ["A", "B1", "A+B1"]}
    return {"t": t, "c": c, "resid_sd": resid}


# ----------------------------------------------------------- family B1 proxy

def family_b1_proxy():
    """Table A5: the H2-2E-parameter density-matrix proxy on family B1, one
    row per circuit (results/family_B1_proxy_h22e.csv)."""
    path = os.path.join(RESULTS, "family_B1_proxy_h22e.csv")
    if not os.path.exists(path):
        write("A5_proxy_b1", "[PENDING: proxy rerun] results/family_B1_proxy_h22e.csv not found.\n")
        return None
    pb = pd.read_csv(path)
    pipes = [p for p in ["P0ref", "P0", "P1", "P2", "P3"] if p in set(pb.pipeline)]
    fh = pb.pivot_table(index="file", columns="pipeline", values="F_H")
    nq = pb.pivot_table(index="file", columns="pipeline", values="n_2q")
    meta = pb[pb.pipeline == "P0"].set_index("file")[["n", "support_size"]]
    order = meta.sort_values(["n"]).index
    rows = []
    for f in order:
        row = {"circuit": f.replace(".qasm", ""), "n": int(meta.loc[f, "n"]),
               "support": int(meta.loc[f, "support_size"])}
        for p in pipes:
            row[f"F_H {p}"] = float(fh.loc[f, p])
        row["ZZ P0"] = int(nq.loc[f, "P0"])
        row["ZZ P2"] = int(nq.loc[f, "P2"])
        rows.append(row)
    t = pd.DataFrame(rows)
    write("A5_proxy_b1", md_table(t, "{:.4f}"))
    y = -np.log(pb.F_H.values)
    x = pb.n_2q.values.astype(float)
    a = float(x @ y / (x @ x))
    res = y - a * x
    se = float(np.sqrt((res @ res) / (len(x) - 1) / (x @ x)))
    r2 = float(1 - (res @ res) / ((y - y.mean()) @ (y - y.mean())))
    return {"t": t, "slope": a, "slope_se": se, "r2_centred": r2,
            "p2_above_p0": int((fh["P2"] > fh["P0"]).sum()), "n_circuits": int(fh.shape[0])}


# -------------------------------------------------------------- certificates

def certificates():
    """Table C1: the exactness-barrier certificate per circuit
    (results/certificates.csv) and the family B2 means per (n, eps)."""
    path = os.path.join(RESULTS, "certificates.csv")
    if not os.path.exists(path):
        write("C1_certificates", "[PENDING: certificates] results/certificates.csv not found.\n")
        return None
    c = pd.read_csv(path)
    assert (c.status == "ok").all()
    c = c.copy()
    c["ratio"] = 100 * c.lde_floor / c.t_zx_P2
    c["achieved"] = 100 * (1 - c.t_zx_P2 / c.t_written)
    c["eps"] = c.file.str.extract(r"eps(1e-\d+)")[0]
    rows = []
    for _, r in c.iterrows():
        rows.append({"family": r.family, "file": r.file.replace(".qasm", ""), "n": int(r.n),
                     "T written": int(r.t_written), "floor": int(r.lde_floor),
                     "T after ZX": int(r.t_zx_P2), "floor / T after ZX %": float(r.ratio),
                     "achieved %": float(r.achieved)})
    t = pd.DataFrame(rows)
    b2 = c[c.family == "B2"]
    rows2 = []
    for (n, eps), g in b2.groupby(["n", "eps"]):
        rows2.append({"n": int(n), "eps": eps, "circuits": int(len(g)),
                      "mean T written": float(g.t_written.mean()),
                      "mean floor / T after ZX %": float(g.ratio.mean()),
                      "min floor / T after ZX %": float(g.ratio.min()),
                      "mean achieved %": float(g.achieved.mean()),
                      "mean collapse rate %": float(100 * g.collapse_rate.mean())})
    t2 = pd.DataFrame(rows2)
    text = ("Per circuit. floor = lde of the exact Pauli channel (Corollary cert, Theorem C(c)), "
            "T after ZX = T-count after PyZX teleport_reduce (P2, equal to the full_reduce value "
            "on every row), achieved % = 100 (1 - T after ZX / T written).\n\n"
            + md_table(t, "{:.2f}")
            + "\nFamily B2 by configuration, 5 circuits each.\n\n"
            + md_table(t2, "{:.2f}", fmt={"mean T written": "{:.1f}"}))
    write("C1_certificates", text)
    return {"t": t, "t2": t2, "n_rows": int(len(c)),
            "invariant_ok": int(((c.lde_floor <= c.t_zx_P1) & (c.lde_floor <= c.t_zx_P2)).sum()),
            "b2_min_ratio": float(b2.ratio.min()),
            "b2_config_ratio": {k: round(v, 2) for k, v in zip(
                [f"n={r.n} eps={r.eps}" for r in t2.itertuples()], t2["mean floor / T after ZX %"])}}


# -------------------------------------------------------------------- selene

def selene():
    """Table S1: Selene local-emulator runs (results/selene_noiseless.csv,
    results/selene_depolarizing.csv), summarised per family."""
    p_noise = os.path.join(RESULTS, "selene_noiseless.csv")
    p_depol = os.path.join(RESULTS, "selene_depolarizing.csv")
    if not (os.path.exists(p_noise) and os.path.exists(p_depol)):
        write("S1_selene", "[PENDING: selene] results/selene_*.csv not found.\n")
        return None
    s = pd.read_csv(p_noise)
    d = pd.read_csv(p_depol)
    rows = []
    for fam, g in s.groupby("family"):
        rows.append({"family": fam, "circuits": int(g.file.nunique()),
                     "pipelines": ", ".join(sorted(g.pipeline.unique())),
                     "runs": int(len(g)), "shots per run": int(g.shots.iloc[0]),
                     "max TVD": float(g.TVD.max()),
                     "max TVD / TVD_scale": float(g.TVD_over_scale.max()),
                     "flagged (TVD > 4 TVD_scale)": int(g.flag.sum()),
                     "shots outside support": int(g.shots_outside_support.sum())})
    t = pd.DataFrame(rows)
    rows2 = []
    for (fam, var), g in d.groupby(["family", "variant"]):
        rows2.append({"family": fam, "variant": var, "runs": int(len(g)),
                      "abs z <= 2": int(g.agree_2sd.sum()),
                      "mean z": float(g.z.mean()),
                      "sd z": float(g.z.std(ddof=0)),
                      "max abs z": float(g.z.abs().max()),
                      "mean F_H Selene - proxy exact": float((g.F_H_selene_depol - g.F_H_proxy_exact).mean()),
                      "mean F_H Selene - proxy sampled": float((g.F_H_selene_depol - g.F_H_proxy_sampled_mean).mean())})
    t2 = pd.DataFrame(rows2)
    text = ("Noiseless runs (IdealErrorModel, Quest backend). TVD is against the exact output "
            "distribution of the compiled QASM, TVD_scale = sqrt(support / (2 pi shots)).\n\n"
            + md_table(t, "{:.3f}")
            + "\nDepolarising runs (DepolarizingErrorModel, p_1q = 7.3e-5, p_2q = 1.29e-3) against "
            "the density-matrix proxy, pipelines P0 and P2. z = (F_H Selene - mean F_H of 400 "
            "2000-shot samples of the proxy distribution) / their sd. gates_meas_init adds "
            "p_meas = 1.35e-3 and p_init = 4e-5, gates_only sets both to 0.\n\n"
            + md_table(t2, "{:.2f}", fmt={"mean F_H Selene - proxy exact": "{:.4f}",
                                          "mean F_H Selene - proxy sampled": "{:.4f}"}))
    write("S1_selene", text)
    return {"t": t, "t2": t2, "runs": int(len(s)), "flagged": int(s.flag.sum()),
            "outside": int(s.shots_outside_support.sum()),
            "max_over_scale": float(s.TVD_over_scale.max()),
            "depol_runs": int(len(d))}


# --------------------------------------------------------------- injection

def inject(report_path: str):
    with open(report_path) as f:
        text = f.read()
    pattern = re.compile(r"<!-- TABLE:([A-Za-z0-9_]+) -->\n.*?<!-- /TABLE:\1 -->", re.S)

    def repl(m):
        name = m.group(1)
        path = os.path.join(TABLES, name + ".md")
        body = open(path).read() if os.path.exists(path) else f"[PENDING: table {name}]\n"
        return f"<!-- TABLE:{name} -->\n{body}<!-- /TABLE:{name} -->"

    new, k = pattern.subn(repl, text)
    with open(report_path, "w") as f:
        f.write(new)
    return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-inject", action="store_true")
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    fa = family_a(fig=not args.no_fig)
    fp = family_a_proxy()
    fb1 = family_b1(fig=not args.no_fig)
    fb2 = family_b2(fig=not args.no_fig)
    fm1 = cost_model_metrics()
    fm2 = cost_model_coefficients()
    fpb = family_b1_proxy()
    fc = certificates()
    fs = selene()
    print("family A: circuits", fa["n_circuits"], "| P0 at ZZ term count:",
          fa["p0_at_floor"], "| circuits with any pipeline below it:", fa["any_below_floor"],
          "| P2 ties P0:", fa["p2_ties"], "worse:", fa["p2_worse"])
    print("family B1:", {k: v for k, v in fb1.items() if k != "t_b1"})
    print("family B2: mean T reduction by pipeline (%):",
          {p: round(float(v.mean()), 2) for p, v in fb2["red"].items()},
          "| max target deviation:", float(fb2["max_target_dev"].max()))
    if fm2 is not None:
        print("cost model: OLS residual sd of y by training set:", fm2["resid_sd"])
    if fpb is not None:
        print("family B1 proxy: slope a = %.4e +/- %.2e, centred R^2 %.4f, P2 above P0 on %d of %d"
              % (fpb["slope"], fpb["slope_se"], fpb["r2_centred"], fpb["p2_above_p0"], fpb["n_circuits"]))
    if fc is not None:
        print("certificates: rows", fc["n_rows"], "| floor <= T_zx on", fc["invariant_ok"],
              "| B2 min floor/T_zx %", round(fc["b2_min_ratio"], 2), "| B2 config means", fc["b2_config_ratio"])
    if fs is not None:
        print("selene: noiseless runs", fs["runs"], "| flagged", fs["flagged"], "| shots outside support",
              fs["outside"], "| max TVD/scale", round(fs["max_over_scale"], 3), "| depolarising runs", fs["depol_runs"])
    for name in ["A1_zz_by_n", "A2_vs_P0", "A3_floor", "A4_proxy", "B1_per_circuit", "B2_summary",
                 "M1_cost_metrics", "M2_cost_coefficients", "A5_proxy_b1", "C1_certificates", "S1_selene"]:
        if os.path.exists(os.path.join(TABLES, name + ".md")):
            print(f"\n### {name}\n" + open(os.path.join(TABLES, name + ".md")).read())
    if not args.no_inject:
        for path in ([REPORT, REPORT_V2]
                     + sorted(glob.glob(os.path.join(ROOT, "report", "v2", "part*.md")))):
            if os.path.exists(path):
                k = inject(path)
                print(f"injected {k} table blocks into {path}")


if __name__ == "__main__":
    main()
