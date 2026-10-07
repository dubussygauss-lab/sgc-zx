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
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
TABLES = os.path.join(ROOT, "report", "tables")
FIGURES = os.path.join(ROOT, "report", "figures")
REPORT = os.path.join(ROOT, "report", "report_v1.md")

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
               "ZZ P0ref", "ZZ P0", "ZZ P0L1", "ZZ P1", "ZZ P2", "ZZ P3", "ZZ P4"}


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
            "p_init = 4e-5; no leakage, crosstalk or dephasing), to be replaced by emulator runs. "
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
    print("family A: circuits", fa["n_circuits"], "| P0 at ZZ term count:",
          fa["p0_at_floor"], "| circuits with any pipeline below it:", fa["any_below_floor"],
          "| P2 ties P0:", fa["p2_ties"], "worse:", fa["p2_worse"])
    print("family B1:", {k: v for k, v in fb1.items() if k != "t_b1"})
    print("family B2: mean T reduction by pipeline (%):",
          {p: round(float(v.mean()), 2) for p, v in fb2["red"].items()},
          "| max target deviation:", float(fb2["max_target_dev"].max()))
    for name in ["A1_zz_by_n", "A2_vs_P0", "A3_floor", "A4_proxy", "B1_per_circuit", "B2_summary"]:
        print(f"\n### {name}\n" + open(os.path.join(TABLES, name + ".md")).read())
    if not args.no_inject and os.path.exists(REPORT):
        k = inject(REPORT)
        print(f"injected {k} table blocks into {REPORT}")


if __name__ == "__main__":
    main()
