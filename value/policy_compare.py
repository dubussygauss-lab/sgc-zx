"""Policy comparison for a user deciding whether to leave pytket level 2.

Policies (per circuit, then summed):
  always L2    hqc_P0 of value/psel4_ledger.csv (P0 = pytket optimisation level 2)
  always L3    hqc_L3
  always P2L3  hqc_P2L3; the one P2L3 timeout (B1 hwb8.qasm, 180 s) falls back
               to the L2 result, as a user running P2L3 with that timeout would
  PSEL4        hqc_PSEL4 (lowest of P0, P2, L3, P2L3)

Compile-time sources (one row per circuit and pipeline):
  A        P0, P2     results/family_A_counts.csv      t_total, t_wall
           L3, P2L3   value/psel4_runs.csv              t_wall (t_compile_check
                                                        includes the check, no
                                                        compile-only column)
  B1, C    L2, L3,    results/strong_baselines.csv      t_total, t_wall
           P2L3       (variant L2 is P0, HQC identical)
           P2         results/family_{B1,C}_counts.csv  t_total, t_wall
  usecase  L3, P2L3   value/psel4_runs.csv              t_wall
           P0, P2     no timing column (value/usecase.csv) -> Unverifiable
t_wall = wall time of one (circuit, pipeline) job including the equivalence
check where one ran. t_total = compile only (preprocessing + pytket passes).
PSEL4 time = P0 + P2 + L3 + P2L3 (candidates run one after another).

Run: python3 value/policy_compare.py  -> value/policy_compare.md
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "value/psel4_ledger.csv"
OUT_MD = ROOT / "value/policy_compare.md"
FAMS = ["A", "B1", "C", "usecase"]
EPS = 1e-9


# ------------------------------------------------------------------ HQC

def load_ledger():
    L = pd.read_csv(LEDGER)
    # P2L3 policy: fall back to L2 where P2L3 has no result (timeout)
    L["hqc_P2L3_pol"] = L.hqc_P2L3.where(L.hqc_P2L3.notna(), L.hqc_P0)
    L["P2L3_fallback"] = L.hqc_P2L3.isna()
    return L


def loss_stats(sub, col):
    """Circuits where policy `col` costs more HQC than L2."""
    d = sub[col] - sub.hqc_P0
    pct = 100 * d / sub.hqc_P0
    lose = d > EPS
    win = d < -EPS
    out = {"n": len(sub), "n_lose": int(lose.sum()), "n_win": int(win.sum()),
           "n_tie": int((~lose & ~win).sum()),
           "lost_total": float(d[lose].sum())}
    if lose.any():
        i = d[lose].idxmax()
        j = pct[lose].idxmax()
        out.update(max_loss=float(d[i]), max_loss_pct=float(pct[i]),
                   max_loss_file=sub.file[i],
                   max_losspct=float(pct[j]), max_losspct_hqc=float(d[j]),
                   max_losspct_file=sub.file[j])
    return out


def policy_table(L):
    rows = []
    for fam in FAMS + ["pooled"]:
        sub = L if fam == "pooled" else L[L.family == fam]
        base = sub.hqc_P0.sum()
        r = {"family": fam, "n": len(sub), "L2": base}
        for name, col in [("L3", "hqc_L3"), ("P2L3", "hqc_P2L3_pol"),
                          ("PSEL4", "hqc_PSEL4")]:
            tot = sub[col].sum()
            r[name] = tot
            r[f"save_{name}"] = base - tot
            r[f"save_{name}_pct"] = 100 * (base - tot) / base
        rows.append(r)
    return pd.DataFrame(rows)


def loss_table(L):
    rows = []
    for name, col in [("L3", "hqc_L3"), ("P2L3", "hqc_P2L3_pol"),
                      ("PSEL4", "hqc_PSEL4")]:
        for fam in FAMS + ["pooled"]:
            sub = L if fam == "pooled" else L[L.family == fam]
            rows.append({"policy": name, "family": fam,
                         **loss_stats(sub.reset_index(drop=True), col)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ time

def load_times():
    """Long table: family, file, pipe (P0/P2/L3/P2L3), t_wall, t_total, status."""
    parts = []
    a = pd.read_csv(ROOT / "results/family_A_counts.csv")
    a = a[a.pipeline.isin(["P0", "P2"])].assign(family="A")
    parts.append(a.rename(columns={"pipeline": "pipe"}))
    for fam in ["B1", "C"]:
        f = pd.read_csv(ROOT / f"results/family_{fam}_counts.csv")
        f = f[f.pipeline == "P2"].assign(family=fam)
        parts.append(f.rename(columns={"pipeline": "pipe"}))
    sb = pd.read_csv(ROOT / "results/strong_baselines.csv")
    sb = sb[sb.variant.isin(["L2", "L3", "P2L3"])].copy()
    sb["pipe"] = sb.variant.replace({"L2": "P0"})
    parts.append(sb)
    runs = pd.read_csv(ROOT / "value/psel4_runs.csv")
    runs = runs.rename(columns={"variant": "pipe"}).assign(t_total=np.nan)
    parts.append(runs)
    cols = ["family", "file", "pipe", "t_wall", "t_total", "status"]
    T = pd.concat([p[cols] for p in parts], ignore_index=True)
    assert not T.duplicated(["family", "file", "pipe"]).any()
    return T


def wide_times(L, T, col):
    w = T.pivot(index=["family", "file"], columns="pipe", values=col)
    w = w.reindex(pd.MultiIndex.from_frame(L[["family", "file"]]))
    w = w.reindex(columns=["P0", "P2", "L3", "P2L3"])
    w["PSEL4"] = w[["P0", "P2", "L3", "P2L3"]].sum(axis=1, min_count=4)
    return w


def time_table(w):
    rows = []
    for fam in FAMS + ["pooled"]:
        sub = w if fam == "pooled" else w.xs(fam, level="family", drop_level=False)
        for p in ["P0", "L3", "P2L3", "PSEL4"]:
            x = sub[p].dropna()
            r = {"family": fam, "pipe": p, "n_timed": len(x), "n_missing": int(sub[p].isna().sum())}
            if len(x):
                r.update(median=float(x.median()), max=float(x.max()),
                         max_file=x.idxmax()[1], total=float(x.sum()))
            rows.append(r)
    return pd.DataFrame(rows)


def overhead_table(w):
    """PSEL4 and L3 time relative to L2, on circuits where both are timed."""
    rows = []
    for fam in FAMS + ["pooled"]:
        sub = w if fam == "pooled" else w.xs(fam, level="family", drop_level=False)
        for p in ["L3", "P2L3", "PSEL4"]:
            ok = sub[["P0", p]].dropna()
            if not len(ok):
                rows.append({"family": fam, "pipe": p, "n": 0})
                continue
            ratio = ok[p] / ok.P0
            rows.append({"family": fam, "pipe": p, "n": len(ok),
                         "n_slower": int((ok[p] > ok.P0).sum()),
                         "t_L2": float(ok.P0.sum()), "t_pipe": float(ok[p].sum()),
                         "ratio_total": float(ok[p].sum() / ok.P0.sum()),
                         "ratio_median": float(ratio.median()),
                         "ratio_max": float(ratio.max()),
                         "ratio_max_file": ratio.idxmax()[1]})
    return pd.DataFrame(rows)


def per_second(L, w, label):
    """Pooled HQC saved per extra second vs always L2 (circuits with both numbers)."""
    hq = L.set_index(["family", "file"])
    rows = []
    for name, col in [("L3", "hqc_L3"), ("PSEL4", "hqc_PSEL4")]:
        ok = w[["P0", name]].dropna().index
        ok = [i for i in ok if pd.notna(hq.loc[i, col])]
        saved = float((hq.loc[ok, "hqc_P0"] - hq.loc[ok, col]).sum())
        extra = float((w.loc[ok, name] - w.loc[ok, "P0"]).sum())
        fams = sorted({i[0] for i in ok})
        rows.append({"time_col": label, "policy": name, "n": len(ok),
                     "families": "+".join(fams), "hqc_saved": saved,
                     "extra_s": extra,
                     # undefined when the policy is not slower than L2 in total
                     "hqc_per_s": saved / extra if extra > 0 else np.nan,
                     "note": "" if extra > 0 else "policy faster than L2 in total: no extra time"})
    return rows


# ------------------------------------------------------------------ report

def fmt(x, nd=1):
    if isinstance(x, (float, np.floating)):
        return "" if np.isnan(x) else f"{x:,.{nd}f}"
    return str(x)


def md_table(df, nd=1, fmts=None):
    fmts = fmts or {}
    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(fmt(v, fmts.get(c, nd)) for c, v in r.items()) + " |"
            for r in df.to_dict("records")]
    return "\n".join([head, sep] + body)


def compute():
    L = load_ledger()
    T = load_times()
    ww = wide_times(L, T, "t_wall")
    wt = wide_times(L, T, "t_total")
    return dict(L=L, T=T, pol=policy_table(L), loss=loss_table(L),
                tw=time_table(ww), tt=time_table(wt),
                ow=overhead_table(ww), ot=overhead_table(wt),
                ps=pd.DataFrame(per_second(L, ww, "t_wall") + per_second(L, wt, "t_total")),
                ww=ww, wt=wt)


def report(R):
    L, pol, loss = R["L"], R["pol"], R["loss"]
    fb = L[L.P2L3_fallback]
    psel_bad = int((L.hqc_PSEL4 > L.hqc_P0 + EPS).sum())
    out = ["# Policy comparison: always L2, always L3, always P2L3, PSEL4", "",
           "Generated by `python3 value/policy_compare.py` from value/psel4_ledger.csv "
           "and the timing files named below. HQC = per-circuit job cost as in the "
           "ledger. Saving = HQC(always L2) - HQC(policy). Loss % = 100 * (HQC(policy) - "
           "HQC(L2)) / HQC(L2) for that circuit.", "",
           f"Circuits: {len(L)} ({', '.join(f'{f} {int((L.family == f).sum())}' for f in FAMS)}).",
           f"P2L3 fallback to L2 (no P2L3 result): {len(fb)} circuit(s): "
           + ", ".join(f"{r.family}/{r.file} (status {r.status_P2L3})" for r in fb.itertuples()) + ".",
           f"Circuits where PSEL4 costs more than L2: {psel_bad}.", "",
           "## 1. Total HQC per policy", ""]
    p = pol.copy()
    out.append(md_table(p, fmts={"n": 0}))
    out += ["", "## 1b. Circuits where a policy costs more than L2", "",
            "n_lose / n_win / n_tie against L2. max_loss = largest per-circuit HQC loss "
            "(with its %), max_losspct = largest per-circuit % loss (with its HQC). "
            "lost_total = sum of HQC lost on the losing circuits.", ""]
    cols = ["policy", "family", "n", "n_lose", "n_win", "n_tie", "lost_total",
            "max_loss", "max_loss_pct", "max_loss_file", "max_losspct",
            "max_losspct_hqc", "max_losspct_file"]
    out.append(md_table(loss.reindex(columns=cols),
                        fmts={"n": 0, "n_lose": 0, "n_win": 0, "n_tie": 0,
                              "max_loss_pct": 2, "max_losspct": 2}))
    # net figures used in prose
    pl = pol.set_index("family").loc["pooled"]
    l3 = loss[(loss.policy == "L3") & (loss.family == "pooled")].iloc[0]
    out += ["", "Pooled always-L3 decomposition: HQC gained on winning circuits = "
            f"{fmt(pl.save_L3 + l3.lost_total)}, HQC lost on losing circuits = "
            f"{fmt(l3.lost_total)}, net saving = {fmt(pl.save_L3)}.",
            f"PSEL4 minus always-L3 pooled saving = {fmt(pl.save_PSEL4 - pl.save_L3)} HQC "
            f"({fmt(100 * (pl.save_PSEL4 - pl.save_L3) / pl.L2, 2)} % of always-L2 total).", ""]

    out += ["## 2. Compile time per circuit", "",
            "Timing coverage (F): t_wall exists for every (circuit, pipeline) of A, B1 and C "
            "and for L3, P2L3 of usecase. usecase P0 and P2 have no timing column in "
            "value/usecase.csv, so usecase L2 and PSEL4 times are Unverifiable. "
            "t_total (compile only) exists for A P0/P2 and B1, C all four pipelines. "
            "A and usecase L3/P2L3 have no compile-only column (value/psel4_runs.csv "
            "t_compile_check includes the check), so their t_total is Unverifiable. "
            "B1 hwb8.qasm P2L3 timed out: t_wall is the 180 s timeout and counts toward "
            "PSEL4 wall time. Its t_total is missing, so hwb8 drops out of every "
            "t_total P2L3 and PSEL4 figure.", "",
            "Sources mix runs (O): A L2 comes from the family_A_counts run and A L3/P2L3 from "
            "the psel4_runs forked-process run. B1 and C L2/L3/P2L3 come from one "
            "strong_baselines run. P2 comes from the family counts runs. Check kinds differ "
            "per family (unitary, statevector, none), which enters t_wall.", "",
            "PSEL4 time = P0 + P2 + L3 + P2L3 (sequential). Pipe P0 = L2.", "",
            "### 2a. t_wall (s)", ""]
    tc = ["family", "pipe", "n_timed", "n_missing", "median", "max", "max_file", "total"]
    out.append(md_table(R["tw"].reindex(columns=tc), nd=3, fmts={"n_timed": 0, "n_missing": 0}))
    out += ["", "### 2b. t_total, compile only (s)", ""]
    out.append(md_table(R["tt"].reindex(columns=tc), nd=3, fmts={"n_timed": 0, "n_missing": 0}))
    oc = ["family", "pipe", "n", "n_slower", "t_L2", "t_pipe", "ratio_total", "ratio_median",
          "ratio_max", "ratio_max_file"]
    out += ["", "### 2c. Time relative to L2, t_wall (circuits with both timed)", "",
            "n_slower = circuits where the pipeline takes longer than L2. "
            "ratio_total = sum(t_pipe) / sum(t_L2). ratio_median and ratio_max are over "
            "per-circuit ratios.", ""]
    out.append(md_table(R["ow"].reindex(columns=oc), nd=2, fmts={"n": 0, "n_slower": 0, "t_L2": 1, "t_pipe": 1}))
    out += ["", "### 2d. Time relative to L2, t_total (circuits with both timed)", ""]
    out.append(md_table(R["ot"].reindex(columns=oc), nd=2,
                        fmts={"n": 0, "n_slower": 0, "t_L2": 1, "t_pipe": 1}))
    out += ["", "## 3. HQC saved per second of extra compile time, pooled vs always L2", "",
            "Only circuits where the policy HQC and both times exist. extra_s = "
            "sum(t_policy - t_L2). hqc_per_s is left empty when extra_s <= 0.", ""]
    out.append(md_table(R["ps"], nd=2, fmts={"n": 0, "hqc_saved": 1, "extra_s": 1}))
    out.append("")
    return "\n".join(out)


def main():
    R = compute()
    OUT_MD.write_text(report(R))
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
