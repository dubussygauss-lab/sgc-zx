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
  family_B1x_counts.csv 8 Clifford+T benchmark circuits with 14 <= n <= 19 x
                        3 pipelines (P0ref, P0, P2), compiled with --no-check,
                        status ok-unchecked (table B1x of Section 3.2.1)
  family_B2_counts.csv  20 QSD + gridsynth Haar circuits x 5 pipelines
  family_B1_proxy_h22e.csv  local density-matrix noise proxy (H2-2E parameters), family B1, n <= 7
  certificates.csv      exactness-barrier certificate, 20 family B2 + 4 family B1 circuits
  selene_noiseless.csv, selene_depolarizing.csv  Selene local-emulator runs
  emulator_nexus_H2-Emulator.csv  Nexus H2-Emulator runs, 1000 shots, with the
                        counts in emulator/nexus_H2-Emulator/<pipeline>/<file>.json
                        (table E1 of Section 3.7)
  emulator_nexus_H2-2E.csv  Nexus H2-2E runs, 1000 shots, counts in
                        emulator/nexus_H2-2E/<pipeline>/<file>.json, statistics
                        from submit/h22e_stats.py (table E2 of Section 3.7.1)
  emulator/nexus_H2-2E_r*/  repeat H2-2E runs of vbe_adder_3 and grover_5, pooled
                        with the original run by submit/h22e_pooled.py (table E3
                        of Section 3.7.1, injected only where its marker exists)
  cost_model_metrics.csv, cost_model_coefficients.csv, fig_cost_model.png
                        written by model/cost_model.py (tables M1, M2 and the
                        cost-model figure of Section 4)

The marker injection runs on report/report_v1.md, report/report_v2.md,
report/report_v3.md, report/report_v4.md, report/report_v5.md and every report/v2/part*.md that exists.

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
REPORT_V3 = os.path.join(ROOT, "report", "report_v3.md")
REPORT_V4 = os.path.join(ROOT, "report", "report_v4.md")
REPORT_V5 = os.path.join(ROOT, "report", "report_v5.md")

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
               "shots outside support", "abs z <= 2",
               "depth_2q P0", "depth_2q P2", "n_2q"}


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


# ---------------------------------------------------------------- family B1x

def family_b1x():
    """Table B1x: the count-only family B1x (results/family_B1x_counts.csv),
    8 benchmark circuits with 14 <= n <= 19 under P0ref, P0 and P2, compiled
    with --no-check.  No unitary, statevector or distribution check exists for
    these rows (status ok-unchecked), only the gate-set check.  One row per
    circuit, ordered by n and then by T-count as written."""
    path = os.path.join(RESULTS, "family_B1x_counts.csv")
    if not os.path.exists(path):
        write("B1x_per_circuit", "[PENDING: B1x] results/family_B1x_counts.csv not found.\n")
        return None
    b = pd.read_csv(path)
    assert b.native.all(), "family B1x has non-native rows"
    assert (b.status == "ok-unchecked").all(), "family B1x status is not ok-unchecked on every row"
    piv = b.pivot_table(index="file", columns="pipeline", values="n_2q")
    dep = b.pivot_table(index="file", columns="pipeline", values="depth_2q")
    tz = b.pivot_table(index="file", columns="pipeline", values="t_count_zx")
    meta = b[b.pipeline == "P0ref"].set_index("file")[["n", "t_count_written"]]
    order = meta.sort_values(["n", "t_count_written"]).index
    rows = []
    for f in order:
        rows.append({
            "file": f.replace(".qasm", ""), "n": int(meta.loc[f, "n"]),
            "ZZ P0ref": int(piv.loc[f, "P0ref"]), "ZZ P0": int(piv.loc[f, "P0"]),
            "ZZ P2": int(piv.loc[f, "P2"]),
            "P2 vs P0 %": float(100 * (1 - piv.loc[f, "P2"] / piv.loc[f, "P0"])),
            "depth_2q P0": int(dep.loc[f, "P0"]), "depth_2q P2": int(dep.loc[f, "P2"]),
            "T written": int(meta.loc[f, "t_count_written"]),
            "T after ZX P2": int(tz.loc[f, "P2"]),
        })
    t = pd.DataFrame(rows)
    text = ("Count-only rows, status ok-unchecked on every row: no unitary, statevector or "
            "distribution check was run at this size, only the gate-set check. "
            "P2 vs P0 % = 100 (1 - ZZ P2 / ZZ P0).\n\n"
            + md_table(t, fmt={"T after ZX P2": "{:.0f}"}))
    write("B1x_per_circuit", text)
    red = 100 * (1 - piv["P2"] / piv["P0"])
    return {"t": t, "n_circuits": int(piv.shape[0]),
            "p2_better": int((piv["P2"] < piv["P0"]).sum()),
            "p2_equal": int((piv["P2"] == piv["P0"]).sum()),
            "p2_worse": int((piv["P2"] > piv["P0"]).sum()),
            "zz_P0": int(piv["P0"].sum()), "zz_P2": int(piv["P2"].sum()),
            "zz_P0ref": int(piv["P0ref"].sum()),
            "agg_red_pct": float(100 * (1 - piv["P2"].sum() / piv["P0"].sum())),
            "max_red": (red.idxmax().replace(".qasm", ""), float(red.max()))}


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


def selene_depol_full():
    """Table S2: full depolarising Selene run (results/selene_depolarizing_full.csv),
    gates_meas_init, 156 circuits x P0/P1/P2, per family and n."""
    path = os.path.join(RESULTS, "selene_depolarizing_full.csv")
    if not os.path.exists(path):
        write("S2_selene_depol", "[PENDING: selene] results/selene_depolarizing_full.csv not found.\n")
        return None
    d = pd.read_csv(path)
    w = d.pivot_table(index=["family", "n", "file"], columns="pipeline",
                      values="F_H_selene_depol").reset_index()
    rows = []
    for (fam, n), g in w.groupby(["family", "n"]):
        rows.append({"family": fam, "n": int(n), "circuits": int(len(g)),
                     "mean F_H P0": float(g.P0.mean()), "mean F_H P1": float(g.P1.mean()),
                     "mean F_H P2": float(g.P2.mean()),
                     "P0 > P1": int((g.P0 > g.P1).sum()), "P2 > P1": int((g.P2 > g.P1).sum())})
    rows.append({"family": "all", "n": "", "circuits": int(len(w)),
                 "mean F_H P0": float(w.P0.mean()), "mean F_H P1": float(w.P1.mean()),
                 "mean F_H P2": float(w.P2.mean()),
                 "P0 > P1": int((w.P0 > w.P1).sum()), "P2 > P1": int((w.P2 > w.P1).sum())})
    t = pd.DataFrame(rows)
    text = ("Depolarising runs on the full set (DepolarizingErrorModel, p_1q = 7.3e-5, "
            "p_2q = 1.29e-3, p_meas = 1.35e-3, p_init = 4e-5, 2000 shots). F_H is the Hellinger "
            "fidelity of the Selene samples to the ideal distribution. P0 > P1 and P2 > P1 count "
            "circuits with a strictly higher F_H.\n\n"
            + md_table(t, "{:.4f}", fmt={"P0 > P1": "{:d}", "P2 > P1": "{:d}"}))
    write("S2_selene_depol", text)
    both = int(((w.P0 > w.P1) & (w.P2 > w.P1)).sum())
    return {"t": t, "runs": int(len(d)), "circuits": int(len(w)), "both": both,
            "mean_p2_minus_p0": float((w.P2 - w.P0).mean())}


# ------------------------------------------------------------ H2-Emulator

EMU_BOOT = 4000      # bootstrap resamples per row
EMU_SEED = 20261008  # bootstrap seed


def _emu_reference(family: str, file: str) -> np.ndarray:
    """Ideal distribution used for F_H, as in submit/common.py:reference_probs:
    family A from the bench .npy, B1 from the P0ref compilation."""
    if family == "A":
        return np.load(os.path.join(ROOT, "bench", "family_A", file[:-5] + ".npy"))
    import sys
    sys.path.insert(0, os.path.join(ROOT, "pipelines"))
    from compile import probs_from_measured_qasm
    with open(os.path.join(RESULTS, "compiled", "P0ref", file)) as f:
        return probs_from_measured_qasm(f.read())


def _emu_counts(pipeline: str, file: str, n: int):
    import json
    path = os.path.join(RESULTS, "emulator", "nexus_H2-Emulator", pipeline, file[:-5] + ".json")
    with open(path) as f:
        d = json.load(f)
    c = np.zeros(2 ** n)
    for key, v in d["counts"].items():
        c[int(key.replace(" ", ""), 2)] += v
    return c, d["family"]


def emulator_h2e():
    """Table E1: Nexus H2-Emulator runs (results/emulator_nexus_H2-Emulator.csv,
    counts in results/emulator/nexus_H2-Emulator/), with the bootstrap sd of F_H
    per row and the proxy and Selene depolarising F_H of the same (file, pipeline)."""
    path = os.path.join(RESULTS, "emulator_nexus_H2-Emulator.csv")
    if not os.path.exists(path):
        write("E1_h2emulator", "[PENDING: emulator] results/emulator_nexus_H2-Emulator.csv not found.\n")
        return None
    e = pd.read_csv(path)
    rng = np.random.default_rng(EMU_SEED)
    sd, sd_delta, f_check, fams = [], [], [], []
    for r in e.itertuples():
        c, fam = _emu_counts(r.pipeline, r.file, int(r.n_qubits))
        fams.append(fam)
        q = _emu_reference(fam, r.file)
        N = int(c.sum())
        assert N == int(r.shots)
        phat = c / N
        f = float(np.sum(np.sqrt(phat * q)) ** 2)
        f_check.append(abs(f - r.F_H))
        boot = rng.multinomial(N, phat, size=EMU_BOOT) / N
        fb = np.sum(np.sqrt(boot * q[None, :]), axis=1) ** 2
        sd.append(float(fb.std(ddof=1)))
        b = np.sqrt(f)
        qs = float(q[phat > 0].sum())
        sd_delta.append(float(b * np.sqrt(max(qs - b * b, 0.0) / N)))
    e = e.assign(sd_boot=sd, sd_delta=sd_delta, family=fams)
    assert max(f_check) < 1e-9, "F_H recomputed from counts differs from the CSV"
    proxy = pd.concat([pd.read_csv(os.path.join(RESULTS, f"family_{fam}_proxy_h22e.csv"))
                       for fam in ["A", "B1"]])[["file", "pipeline", "F_H"]]
    proxy = proxy.rename(columns={"F_H": "F_H_proxy"})
    sel = pd.read_csv(os.path.join(RESULTS, "selene_depolarizing_full.csv"))[
        ["file", "pipeline", "F_H_selene_depol", "shots"]].rename(columns={"shots": "shots_selene"})
    m = e.merge(proxy, on=["file", "pipeline"], how="left").merge(sel, on=["file", "pipeline"], how="left")
    t = pd.DataFrame({"file": m.file.str.replace(".qasm", "", regex=False), "n": m.n.astype(int),
                      "pipeline": m.pipeline, "n_2q": m.n_2q.astype(int),
                      "F_H emulator": m.F_H, "sd F_H emulator": m.sd_boot,
                      "F_H proxy": m.F_H_proxy, "F_H Selene depol": m.F_H_selene_depol})
    # Comparisons.  Proxy: exact, so the sd of the difference is the emulator sd.
    # Selene: sampled at shots_selene, its sd taken as sd_boot * sqrt(1000 / shots_selene).
    mp = m[m.F_H_proxy.notna()]
    dp = mp.F_H - mp.F_H_proxy
    ms = m[m.F_H_selene_depol.notna()]
    ss = np.sqrt(ms.sd_boot ** 2 * (1 + ms.shots / ms.shots_selene))
    ds = ms.F_H - ms.F_H_selene_depol
    # P2 against P0 on the same circuit.
    w = m.pivot_table(index="file", columns="pipeline", values=["F_H", "sd_boot", "n_2q"])
    pairs = []
    for f in w.index:
        if not (np.isfinite(w.loc[f, ("F_H", "P0")]) and np.isfinite(w.loc[f, ("F_H", "P2")])):
            continue
        pairs.append({"file": f, "dzz": int(w.loc[f, ("n_2q", "P0")] - w.loc[f, ("n_2q", "P2")]),
                      "dF": float(w.loc[f, ("F_H", "P2")] - w.loc[f, ("F_H", "P0")]),
                      "sd_diff": float(np.hypot(w.loc[f, ("sd_boot", "P0")], w.loc[f, ("sd_boot", "P2")]))})
    pairs = pd.DataFrame(pairs)
    # Expected F_H gain per removed ZZ gate: no-intercept slope of -ln F_H on n_2q,
    # family B1 proxy (as in family_b1_proxy).
    pb = pd.read_csv(os.path.join(RESULTS, "family_B1_proxy_h22e.csv"))
    y, x = -np.log(pb.F_H.values), pb.n_2q.values.astype(float)
    slope = float(x @ y / (x @ x))
    if len(pairs):
        f0 = np.array([float(w.loc[f, ("F_H", "P0")]) for f in pairs.file])
        pairs["dF_expected"] = f0 * (np.exp(slope * pairs.dzz) - 1)
        pairs["z_observed"] = pairs.dF / pairs.sd_diff
        pairs["expected_over_sd"] = pairs.dF_expected / pairs.sd_diff
    b1 = m[(m.support_size == 1)]
    # Shots per pipeline for a one-gate F_H difference to equal two sd of the
    # P2 - P0 difference on a support-1 circuit at the mean B1 F_H of the table.
    fb = float(b1.F_H.mean())
    d1 = fb * (np.exp(slope) - 1)
    shots_1gate_2sd = float(2 * fb * (1 - fb) * (2 / d1) ** 2)
    off_p = mp[(dp.abs() > 2 * mp.sd_boot)]
    off_s = ms[(ds.abs() > 2 * ss)]
    text = ("Nexus H2-Emulator, noisy_simulation = True, 1000 shots per row. F_H is the Hellinger "
            "fidelity of the returned counts to the ideal distribution. sd F_H emulator is the sd of "
            f"F_H over {EMU_BOOT} multinomial bootstrap resamples of the counts (seed {EMU_SEED}). "
            "F_H proxy is the exact density-matrix proxy value of Section 3.5 and is empty where the "
            "proxy has no row. F_H Selene depol is the 2000-shot Selene DepolarizingErrorModel value "
            "of Section 3.6.\n\n"
            + md_table(t, "{:.4f}"))
    write("E1_h2emulator", text)
    return {"t": t, "rows": int(len(m)), "sd_min": float(m.sd_boot.min()), "sd_max": float(m.sd_boot.max()),
            "sd_b1_min": float(b1.sd_boot.min()), "sd_b1_max": float(b1.sd_boot.max()),
            "sd_b1_mean": float(b1.sd_boot.mean()),
            "sd_A_min": float(m[m.family == "A"].sd_boot.min()),
            "sd_A_max": float(m[m.family == "A"].sd_boot.max()),
            "max_rel_delta_vs_boot": float((np.abs(m.sd_delta - m.sd_boot) / m.sd_boot).max()),
            "n_proxy": int(len(mp)), "mean_d_proxy": float(dp.mean()),
            "within2_proxy": int((dp.abs() <= 2 * mp.sd_boot).sum()),
            "n_selene": int(len(ms)), "mean_d_selene": float(ds.mean()),
            "within2_selene": int((ds.abs() <= 2 * ss).sum()),
            "pairs": pairs, "slope_b1": slope, "fb_mean": fb, "dF_1gate": float(d1),
            "shots_1gate_2sd": shots_1gate_2sd,
            "off_proxy": list(zip(off_p.file, off_p.pipeline)),
            "off_selene": list(zip(off_s.file, off_s.pipeline)),
            "mean_abs_d_proxy": float(dp.abs().mean()), "mean_abs_d_selene": float(ds.abs().mean()),
            "mean_d_proxy_A": float(dp[mp.family == "A"].mean()),
            "mean_d_proxy_B1": float(dp[mp.family == "B1"].mean())}


def emulator_h22e(e1=None):
    """Table E2: Nexus H2-2E runs (results/emulator_nexus_H2-2E.csv, counts in
    results/emulator/nexus_H2-2E/).  The statistics come from
    submit/h22e_stats.py:compute, which recomputes F_H from the counts."""
    if not os.path.exists(os.path.join(RESULTS, "emulator_nexus_H2-2E.csv")):
        write("E2_h22e", "[PENDING: H2-2E] results/emulator_nexus_H2-2E.csv not found.\n")
        return None
    import sys
    sys.path.insert(0, os.path.join(ROOT, "submit"))
    import h22e_stats
    r = h22e_stats.compute()
    m = r["rows"]
    assert r["max_abs_dF_csv"] < 1e-9, "F_H recomputed from counts differs from the CSV"
    assert r["max_abs_dF_json"] < 1e-9, "F_H recomputed from counts differs from the JSON payload"
    if e1 is not None:
        # The H2-Emulator sd in the cross-emulator z is the sd printed in Table E1.
        t1 = e1["t"]
        for x in r["cross"].itertuples():
            sd1 = t1[(t1.file == x.file[:-5]) & (t1.pipeline == x.pipeline)]["sd F_H emulator"].iloc[0]
            assert abs(sd1 - x.sd_h2emulator) < 1e-12, (x.file, x.pipeline, sd1, x.sd_h2emulator)
    t = pd.DataFrame({"file": m.file.str.replace(".qasm", "", regex=False), "n": m.n.astype(int),
                      "pipeline": m.pipeline, "n_2q": m.n_2q.astype(int),
                      "HQC estimate": m.hqc, "F_H": m.F_H, "sd F_H": m.sd,
                      "F_H proxy": m.F_H_proxy, "F_H Selene depol": m.F_H_selene})
    text = ("`[F]` Nexus H2-2E, noisy_simulation = True, 1000 shots per row, one job per row. F_H is the "
            "Hellinger fidelity of the returned counts to the ideal distribution. sd F_H is the binomial "
            "value sqrt(F_H (1 - F_H) / 1000) on vbe_adder_3 and hwb6, whose ideal output is a single "
            f"bit string. On grover_5 it is the sd over {h22e_stats.BOOT} multinomial bootstrap resamples "
            f"of the counts (seed {h22e_stats.SEED}). HQC estimate is the formula value stored with each "
            "job. F_H proxy is the exact density-matrix proxy value of Section 3.5 and is empty where the "
            "proxy has no row (n > 7). F_H Selene depol is the 2000-shot Selene DepolarizingErrorModel "
            "value of Section 3.6.\n\n"
            + md_table(t, "{:.4f}", fmt={"HQC estimate": "{:.1f}"}))
    write("E2_h22e", text)
    return r



def emulator_h22e_pooled():
    """Table E3: pooled H2-2E runs of vbe_adder_3 and grover_5 (original run of Table E2
    plus the repeats in results/emulator/nexus_H2-2E_r*/).  The statistics come from
    submit/h22e_pooled.py:compute.  The table goes only into a report that carries the
    TABLE:E3_h22e_pooled marker pair (inject() replaces existing pairs only)."""
    if not glob.glob(os.path.join(RESULTS, "emulator", "nexus_H2-2E_r*")):
        return None
    import sys
    sys.path.insert(0, os.path.join(ROOT, "submit"))
    import h22e_pooled
    r = h22e_pooled.compute()
    c = r["cells"]
    t = pd.DataFrame({"file": c.file.str.replace(".qasm", "", regex=False), "pipeline": c.pipeline,
                      "runs": c.runs.astype(int), "shots": c.shots.astype(int), "n_2q": c.n_2q.astype(int),
                      "pooled F_H": c.F_H, "sd": c.sd,
                      "per-run F_H range": [f"{a:.4f} to {b:.4f}" for a, b in zip(c.F_min, c.F_max)]})
    status = ("" if r["final"] else
              f"[PENDING: H2-2E repeats] not all cells hold {h22e_pooled.EXPECTED_RUNS} runs. ")
    text = (f"`[F]` {status}Nexus H2-2E, noisy_simulation = True, 1000 shots per run, one job per run. "
            "runs counts the original run of Table E2 and the completed repeats. pooled F_H is the Hellinger "
            "fidelity of the summed counts to the ideal distribution. sd is binomial on vbe_adder_3 and the sd "
            f"over {h22e_pooled.BOOT} multinomial bootstrap resamples of the pooled counts on grover_5 "
            f"(seed {h22e_pooled.SEED}). The per-run F_H range is the smallest and largest F_H of single runs.\n\n"
            + md_table(t, "{:.4f}", fmt={"shots": "{:.0f}"}))
    lines = []
    for x in r["pairs"].itertuples():
        lines.append(f"{x.file[:-5]} F_H(P2) - F_H(P0) {x.dF:+.4f}, sd {x.sd:.4f}, z {x.z:+.2f}, p {x.p:.2g}, "
                     f"predicted {x.dF_pred:.4f}, measured - predicted {x.z_vs_pred:+.2f} sd")
    hom = ", ".join(f"{a.file[:-5]} {a.pipeline} {a.p_hom:.2f}" for a in c.itertuples())
    text += (f"\n`[F]` " + ". ".join(lines) + f". Homogeneity p: {hom}. H2-2E HQC estimate of the "
             f"{r['jobs_completed']} completed jobs {r['hqc_completed']:.1f}, {r['hqc_pct']:.1f} % of "
             f"{h22e_pooled.QUOTA_HQC:.0f}.\n")
    write("E3_h22e_pooled", text)
    return r


def literature_c2():
    """Table C2: best published T-count beside our T after ZX and the certified floor.
    Reads results/literature_tcounts.csv (one row per circuit and published column) and
    results/certificates.csv.  A published number counts toward 'best ancilla-free' only
    when ancilla_free == yes, same_circuit == yes and reported_error == no."""
    path = os.path.join(RESULTS, "literature_tcounts.csv")
    if not os.path.exists(path):
        return None
    lit = pd.read_csv(path)
    cert = pd.read_csv(os.path.join(RESULTS, "certificates.csv"))
    cert = cert[cert.family == "B1"].assign(circuit=lambda d: d.file.str.replace(".qasm", "", regex=False))
    floor = dict(zip(cert.circuit, cert.lde_floor))
    tzx_cert = dict(zip(cert.circuit, cert.t_zx_P2))
    ok = lit[(lit.ancilla_free == "yes") & (lit.same_circuit == "yes") & (lit.reported_error == "no")]
    anc = lit[(lit.ancilla_free == "no") & (lit.same_circuit == "yes")]
    order = lit.drop_duplicates("circuit")[["circuit", "family", "n", "t_written", "t_zx_P2"]]
    order = order.sort_values(["family", "n", "circuit"]).reset_index(drop=True)
    rows = []
    for r in order.itertuples():
        g = ok[ok.circuit == r.circuit]
        best = int(g.published_t.min()) if len(g) else np.nan
        src = ", ".join(sorted(set(g[g.published_t == best].source_key))) if len(g) else ""
        ga = anc[anc.circuit == r.circuit]
        besta = int(ga.published_t.min()) if len(ga) else np.nan
        srca = ", ".join(sorted(set(ga[ga.published_t == besta].source_key))) if len(ga) else ""
        fl = floor.get(r.circuit, np.nan)
        if r.circuit in tzx_cert:
            assert tzx_cert[r.circuit] == r.t_zx_P2, (r.circuit, tzx_cert[r.circuit], r.t_zx_P2)
        rows.append({"family": r.family, "circuit": r.circuit, "n": int(r.n), "T written": int(r.t_written),
                     "T after ZX": int(r.t_zx_P2), "best ancilla-free": best, "source": src,
                     "best with ancillas": besta, "source (ancillas)": srca, "floor": fl,
                     "T after ZX - best": r.t_zx_P2 - best if not np.isnan(best) else np.nan,
                     "best - floor": best - fl if not (np.isnan(best) or np.isnan(fl)) else np.nan})
    t = pd.DataFrame(rows)
    c = t[t.floor.notna()]
    tot = {"T after ZX": int(c["T after ZX"].sum()), "best": int(c["best ancilla-free"].sum()),
           "floor": int(c.floor.sum())}
    tot["headroom"] = tot["T after ZX"] - tot["best"]
    tot["open"] = tot["best"] - tot["floor"]
    tot["gap"] = tot["T after ZX"] - tot["floor"]
    assert tot["headroom"] + tot["open"] == tot["gap"]
    t_anc_cert = int(c["best with ancillas"].sum())
    fmt_int = lambda v: "" if (isinstance(v, float) and np.isnan(v)) else str(int(v))
    show = t.copy()
    for col in ["best ancilla-free", "best with ancillas", "floor", "T after ZX - best", "best - floor"]:
        show[col] = show[col].map(fmt_int)
    text = ("`[F]` Per circuit of families B1 and B1x. T after ZX is the P2 T-count. best ancilla-free is the "
            "smallest T-count reported in the six papers on the same n qubits, taken over the columns of "
            "`results/literature_tcounts.csv` with ancilla_free = yes, same_circuit = yes and reported_error = no. "
            "best with ancillas is the smallest published T-count of a method that adds Hadamard ancillas. "
            "These methods are TODD and AlphaTensor-Quantum when its compiled qubit count exceeds n. The floor is the certified "
            "lde floor of Table C1 and exists for the four n = 5 circuits only. T after ZX - best is the part of the "
            "ZX output that a published ancilla-free method is known to remove. best - floor is the part that "
            "neither a published method nor the certificate has closed. Source keys: AMM2014 arXiv:1303.2042 "
            "Table 1, AM2016 arXiv:1601.07363 Table II, Nam2018 arXiv:1710.07345 Table 4, TODD2018 and TODDpart2018 "
            "arXiv:1712.01557 Tables I and II, KvdW2020 arXiv:1903.10477 Table 1, AQ2024 arXiv:2402.14396 Table 2. "
            "grover_5 has no same-circuit published value.\n\n"
            + md_table(show, "{:.0f}")
            + f"\n`[F]` On the {len(c)} circuits with a floor: T after ZX {tot['T after ZX']}, best ancilla-free "
              f"{tot['best']}, floor {tot['floor']}. T after ZX - best = {tot['headroom']}, best - floor = "
              f"{tot['open']}, sum {tot['gap']}. Best with ancillas on the same circuits: {t_anc_cert}.\n")
    write("C2_literature", text)
    return {"t": t, "tot": tot, "anc_cert": t_anc_cert}


# ------------------------------------------------- family C and the use case

def family_c():
    """Table C3: family C, 20 application-scale circuits of 20 to 56 qubits, count-only.
    Reads value/family_C_selector.csv and value/family_C_selector_apps.csv (written by
    value/family_C_selector.py from results/family_C_counts.csv) and
    bench/family_C/manifest.csv.  The PSEL HQC of every circuit is recomputed here from
    the P0 and P2 rows of results/family_C_counts.csv.  Injected only where the
    TABLE:C3_familyC marker pair exists (report v5)."""
    p_sel = os.path.join(ROOT, "value", "family_C_selector.csv")
    p_app = os.path.join(ROOT, "value", "family_C_selector_apps.csv")
    if not (os.path.exists(p_sel) and os.path.exists(p_app)):
        return None
    r = pd.read_csv(p_sel)
    a = pd.read_csv(p_app)
    man = pd.read_csv(os.path.join(ROOT, "bench", "family_C", "manifest.csv"))
    cnt = pd.read_csv(os.path.join(RESULTS, "family_C_counts.csv"))
    # recompute PSEL from the raw counts: lower HQC, tie to lower n_2q, then P0
    for x in r.itertuples():
        p0 = cnt[(cnt.file == x.file) & (cnt.pipeline == "P0")].iloc[0]
        p2 = cnt[(cnt.file == x.file) & (cnt.pipeline == "P2")].iloc[0]
        pick = "P2" if (p2.hqc, p2.n_2q) < (p0.hqc, p0.n_2q) else "P0"
        assert pick == x.pick, (x.file, pick, x.pick)
        assert abs(min(p0.hqc, p2.hqc) - x.hqc_PSEL) < 1e-9, x.file
    assert abs(a[a.application == "all"].saved_hqc.iloc[0] - r.saved_hqc.sum()) < 1e-6
    cont = dict(zip(man.file, man.continuous_angles))
    checked = (r.check_P0 == "pass") & (r.check_P2 == "pass")
    apps = pd.DataFrame({"application": a.application, "circuits": a.n_circuits.astype(int),
                         "qubits": a.qubits, "PSEL picks P2": a.p2_picks.astype(int),
                         "HQC P0": a.hqc_P0, "HQC P2": a.hqc_P2, "HQC PSEL": a.hqc_PSEL,
                         "saved vs P0": a.saved_hqc, "saved %": a.saved_pct,
                         "saved vs P2": a.hqc_P2 - a.hqc_PSEL,
                         "n_2q P0": a.n2q_P0.astype(int), "n_2q PSEL": a.n2q_PSEL.astype(int),
                         "T written": a.t_written.astype(int), "T saved": a.t_saved_PSEL.astype(int),
                         "checked": a.n_checked_both.astype(int)})
    per = pd.DataFrame({"file": r.file.str.replace(".qasm", "", regex=False), "n": r.n_qubits.astype(int),
                        "application": r.application, "pick": r.pick,
                        "HQC P0": r.hqc_P0, "HQC P2": r.hqc_P2, "HQC PSEL": r.hqc_PSEL,
                        "saved %": r.saved_pct, "n_2q P0": r.n2q_P0.astype(int),
                        "n_2q PSEL": r.n2q_PSEL.astype(int), "T written": r.t_written.astype(int),
                        "T after ZX P2": r.t_zx_P2.astype(int),
                        "continuous angles": ["yes" if cont[f] else "no" for f in r.file],
                        "check": ["pass" if c else "unchecked" for c in checked]})
    fmt = {c: "{:,.1f}" for c in ["HQC P0", "HQC P2", "HQC PSEL", "saved vs P0", "saved vs P2"]}
    fmt.update({"saved %": "{:.1f}", "n_2q P0": "{:d}", "n_2q PSEL": "{:d}", "T saved": "{:d}",
                "PSEL picks P2": "{:d}", "checked": "{:d}", "T after ZX P2": "{:d}"})
    for c in ["n_2q P0", "n_2q PSEL", "T written", "T saved", "PSEL picks P2", "checked", "T after ZX P2",
              "circuits", "n"]:
        for t in (apps, per):
            if c in t:
                t[c] = t[c].astype(int).astype(str)
    sv = a[a.application == "all"].iloc[0]
    n_unc = int((~checked).sum())
    text = ("`[F]` Family C, count-only. HQC at 1000 shots with every qubit measured (`compile.hqc`). PSEL keeps the "
            "lower HQC of P0 and P2, an HQC tie goes to the lower n_2q and a further tie to P0. saved % is "
            "computed on the sums against P0. T saved is the T-count removed by the ZX stage on the circuits "
            "where PSEL picks P2. checked counts circuits whose P0 and P2 outputs both agree with the input on "
            "64 random basis inputs up to a global phase (`pipelines/run_family_C.py --check`). unchecked means "
            "the sparse simulation exceeded 2^20 amplitudes. A pass covers 64 of 2^n inputs and is not a proof "
            "of equivalence. continuous angles marks inputs with rotations outside the pi/4 grid "
            "(`bench/family_C/manifest.csv`). Source: `value/family_C_selector.csv`.\n\n"
            + md_table(apps, "{:.1f}", fmt=fmt)
            + "\n" + md_table(per, "{:.1f}", fmt=fmt)
            + f"\n`[F]` {len(r)} circuits, {int(checked.sum())} checked and {n_unc} unchecked. PSEL saves "
              f"{sv.saved_hqc:,.1f} HQC or {sv.saved_pct:.1f} % against P0 and {sv.hqc_P2 - sv.hqc_PSEL:,.1f} HQC "
              f"against P2. Saving on the checked circuits {r[checked].saved_hqc.sum():,.1f} HQC, on the unchecked "
              f"circuits {r[~checked].saved_hqc.sum():,.1f} HQC.\n")
    disc = r[[not cont[f] for f in r.file]]
    ca = r[[bool(cont[f]) for f in r.file]]
    text += (f"\n`[F]` On the {len(disc)} circuits without continuous angles PSEL saves "
             f"{disc.saved_hqc.sum():,.1f} of {disc.hqc_P0.sum():,.1f} HQC "
             f"({100 * disc.saved_hqc.sum() / disc.hqc_P0.sum():.2f} %). The {len(ca)} continuous-angle circuits "
             f"save {ca.saved_hqc.sum():,.1f} of {ca.hqc_P0.sum():,.1f} HQC, all of it from the two multipliers.\n")
    write("C3_familyC", text)
    return {"r": r, "a": a, "checked": int(checked.sum()), "unchecked": n_unc}


def usecase_table():
    """Table U1: the two Grover use-case instances of value/usecase.py, read from
    value/usecase.csv.  Injected only where the TABLE:U1_usecase marker pair exists."""
    path = os.path.join(ROOT, "value", "usecase.csv")
    if not os.path.exists(path):
        return None
    u = pd.read_csv(path)
    assert (u.hqc_PSEL == u[["hqc_P0", "hqc_P2"]].min(axis=1)).all()
    t = pd.DataFrame({"file": u.file.str.replace(".qasm", "", regex=False),
                      "qubits": u.n_qubits.astype(int).astype(str), "k": u.iterations.astype(int).astype(str),
                      "P_succ ideal": u.p_success_ideal_sv, "check": u.check_kind,
                      "T written": u.t_count_written.astype(int).astype(str),
                      "T after ZX": u.t_count_after_zx_P2.astype(int).astype(str),
                      "n_2q P0": u.n2q_P0.astype(int).astype(str), "n_2q PSEL": u.n2q_PSEL.astype(int).astype(str),
                      "pick": u.chosen, "HQC P0": u.hqc_P0, "HQC PSEL": u.hqc_PSEL,
                      "saved %": u.hqc_saving_pct,
                      "shots P0": u.shots_capped_P0.astype(int).astype(str),
                      "shots PSEL": u.shots_capped_PSEL.astype(int).astype(str),
                      "hits P0": u.hits_ideal_P0, "hits PSEL": u.hits_ideal_PSEL})
    text = ("`[F]` Grover use case. k is the number of Grover iterations. P_succ ideal is the noise-free success "
            "probability from the statevector. check is the exactness check of `pipelines/compile.py:check` "
            "on P0 and P2. HQC at 1000 shots with every qubit measured. Shots are those affordable within "
            "10,000 HQC with at most 10,000 shots per job and 5 HQC per job. Hits are the expected marked-item "
            "hits within that budget at the ideal success probability. Source: `value/usecase.csv`.\n\n"
            + md_table(t, "{:.1f}", fmt={"P_succ ideal": "{:.6f}", "saved %": "{:.2f}"}))
    write("U1_usecase", text)
    return u


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
    fb1x = family_b1x()
    fb2 = family_b2(fig=not args.no_fig)
    fm1 = cost_model_metrics()
    fm2 = cost_model_coefficients()
    fpb = family_b1_proxy()
    fc = certificates()
    fs = selene()
    fsd = selene_depol_full()
    fe = emulator_h2e()
    fe2 = emulator_h22e(fe)
    fe3 = emulator_h22e_pooled()
    fl2 = literature_c2()
    fc3 = family_c()
    fu1 = usecase_table()
    print("family A: circuits", fa["n_circuits"], "| P0 at ZZ term count:",
          fa["p0_at_floor"], "| circuits with any pipeline below it:", fa["any_below_floor"],
          "| P2 ties P0:", fa["p2_ties"], "worse:", fa["p2_worse"])
    print("family B1:", {k: v for k, v in fb1.items() if k != "t_b1"})
    if fb1x is not None:
        print("family B1x (count-only, ok-unchecked):", {k: v for k, v in fb1x.items() if k != "t"})
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
    if fsd is not None:
        print("selene depol full: runs", fsd["runs"], "| circuits", fsd["circuits"], "| P0>P1 and P2>P1",
              fsd["both"], "| mean P2-P0 %.5f" % fsd["mean_p2_minus_p0"])
    if fe is not None:
        print("H2-Emulator:", {k: v for k, v in fe.items() if k not in ("t", "pairs")})
        print(fe["pairs"].to_string(index=False))
    if fe2 is not None:
        print("H2-2E: HQC estimate total %.1f (%.2f %% of quota), slope a %.4e"
              % (fe2["hqc_total"], 100 * fe2["quota_frac"], fe2["slope"]))
        print(fe2["pairs"].to_string(index=False))
        for x in fe2["cross"].itertuples():
            print("H2-2E vs H2-Emulator, %s %s: sd %.4f (E1) and %.4f (E2), z %.2f"
                  % (x.file, x.pipeline, x.sd_h2emulator, x.sd_h22e, x.z))
    if fe3 is not None:
        print("H2-2E pooled: runs per cell %s, final %s" % (list(fe3["cells"].runs), fe3["final"]))
    if fl2 is not None:
        print("C2 literature: totals on certified circuits", fl2["tot"], "| best with ancillas", fl2["anc_cert"])
    if fc3 is not None:
        print("family C (count-only): checked", fc3["checked"], "| unchecked", fc3["unchecked"])
    if fu1 is not None:
        print("use case: PSEL picks", list(fu1.chosen))
    for name in ["A1_zz_by_n", "A2_vs_P0", "A3_floor", "A4_proxy", "B1_per_circuit", "B1x_per_circuit", "B2_summary",
                 "M1_cost_metrics", "M2_cost_coefficients", "A5_proxy_b1", "C1_certificates", "S1_selene", "S2_selene_depol",
                 "E1_h2emulator", "E2_h22e", "E3_h22e_pooled", "C2_literature", "C3_familyC", "U1_usecase"]:
        if os.path.exists(os.path.join(TABLES, name + ".md")):
            print(f"\n### {name}\n" + open(os.path.join(TABLES, name + ".md")).read())
    if not args.no_inject:
        for path in ([REPORT, REPORT_V2, REPORT_V3, REPORT_V4, REPORT_V5]
                     + sorted(glob.glob(os.path.join(ROOT, "report", "v2", "part*.md")))):
            if os.path.exists(path):
                k = inject(path)
                print(f"injected {k} table blocks into {path}")


if __name__ == "__main__":
    main()
