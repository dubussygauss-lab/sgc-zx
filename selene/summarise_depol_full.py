"""Summarise results/selene_depolarizing_full.csv and append a section to
results/selene.md.  Every number is computed from the CSV."""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "results", "selene_depolarizing_full.csv")
MD = os.path.join(ROOT, "results", "selene.md")

d = pd.read_csv(CSV)
for a in sys.argv:
    if a.startswith("--pipelines="):
        d = d[d.pipeline.isin(a.split("=")[1].split(","))]
L = []
pipes_run = sorted(d.pipeline.unique())
L.append("\n## 6. Depolarising run on the full set (gates_meas_init)\n")
L.append(f"[F] Script `selene/run_selene_depol_full.py`, output `results/selene_depolarizing_full.csv`. "
         f"DepolarizingErrorModel(p_1q = {d.p_1q.iloc[0]:g}, p_2q = {d.p_2q.iloc[0]:g}, p_meas = {d.p_meas.iloc[0]:g}, "
         f"p_init = {d.p_init.iloc[0]:g}), {int(d.shots.iloc[0])} shots, seed = seed_for(pipe, file, \"depol\") as in run_selene.py, 2 processes.")
counts = d.groupby(["family", "pipeline"]).size().unstack(fill_value=0)
L.append(f"[F] Runs: {len(d)} rows, pipelines {', '.join(pipes_run)}; per family and pipeline: "
         + "; ".join(f"{fam}: " + ", ".join(f"{p}={int(counts.loc[fam, p])}" for p in counts.columns) for fam in counts.index) + ".")
L.append(f"[F] Sum of per-run wall times {d.t_total.sum():.0f} s; rows with a proxy comparison {int(d.z.notna().sum())}, "
         f"rows without (no proxy row for that (file, pipeline): family A n = 10, B1 n = 9, 10) {int(d.z.isna().sum())}.")

L.append("\n### 6.1 Mean F_H (Selene, depolarising) by family, n, pipeline\n")
g = d.groupby(["family", "n", "pipeline"]).agg(runs=("F_H_selene_depol", "size"),
                                              F_H_mean=("F_H_selene_depol", "mean"),
                                              F_H_sd=("F_H_selene_depol", lambda s: s.std(ddof=0)),
                                              n_2q_mean=("n_2q", "mean"),
                                              F_H_noiseless_sameseed=("F_H_selene_noiseless_sameseed", "mean")).reset_index()
L.append("| family | n | pipeline | runs | mean F_H | pop. sd F_H | mean n_2q | mean F_H noiseless same seed |")
L.append("|---|---|---|---|---|---|---|---|")
for _, r in g.iterrows():
    L.append(f"| {r.family} | {int(r.n)} | {r.pipeline} | {int(r.runs)} | {r.F_H_mean:.4f} | {r.F_H_sd:.4f} | {r.n_2q_mean:.1f} | {r.F_H_noiseless_sameseed:.4f} |")

L.append("\n### 6.2 Agreement with the density-matrix proxy (rows with a proxy row)\n")
p = d[d.z.notna()]
L.append(f"[F] {len(p)} rows. |z| <= 2: {int((p.z.abs() <= 2).sum())}/{len(p)} ({100 * (p.z.abs() <= 2).mean():.1f} %). "
         f"mean z = {p.z.mean():.3f}, population sd of z = {p.z.std(ddof=0):.3f}, max |z| = {p.z.abs().max():.2f}. "
         f"For independent draws from the proxy's sampling distribution one expects mean 0, sd 1 and about 95.4 % within 2.")
L.append("| family | n | pipeline | rows | agree (|z|<=2) | mean z | pop. sd z | mean (F_H_selene - F_H_proxy_exact) |")
L.append("|---|---|---|---|---|---|---|---|")
for (fam, n, pipe), s in p.groupby(["family", "n", "pipeline"]):
    L.append(f"| {fam} | {int(n)} | {pipe} | {len(s)} | {int((s.z.abs() <= 2).sum())} | {s.z.mean():.3f} | {s.z.std(ddof=0):.3f} | {(s.F_H_selene_depol - s.F_H_proxy_exact).mean():+.4f} |")
big = p[p.z.abs() > 2].sort_values("z", key=np.abs, ascending=False)
L.append(f"\n[F] Rows with |z| > 2 ({len(big)}): " + "; ".join(f"{r.pipeline}/{r.file} z={r.z:+.2f}" for _, r in big.iterrows()) + ".")
L.append(f"[F] z > 2: {int((p.z > 2).sum())}, z < -2: {int((p.z < -2).sum())}; z > 0: {int((p.z > 0).sum())}/{len(p)}.")

L.append("\n### 6.3 Fidelity ordering per circuit\n")
w = d.pivot_table(index=["family", "file", "n"], columns="pipeline", values="F_H_selene_depol").reset_index()
have = [q for q in ("P0", "P1", "P2") if q in w.columns]
if "P1" in have and "P0" in have and "P2" in have:
    w = w.dropna(subset=["P0", "P1", "P2"])
    both = ((w.P0 > w.P1) & (w.P2 > w.P1))
    L.append(f"[F] Circuits with all three pipelines: {len(w)}. P0 > P1 and P2 > P1 (both strict): {int(both.sum())}; "
             f"P0 > P1: {int((w.P0 > w.P1).sum())}; P2 > P1: {int((w.P2 > w.P1).sum())}; P2 > P0: {int((w.P2 > w.P0).sum())}; P2 == P0: {int((w.P2 == w.P0).sum())}.")
    L.append(f"[F] Mean F_H over these circuits: P0 {w.P0.mean():.4f}, P1 {w.P1.mean():.4f}, P2 {w.P2.mean():.4f}; "
             f"mean P0 - P1 = {(w.P0 - w.P1).mean():+.4f}, mean P2 - P1 = {(w.P2 - w.P1).mean():+.4f}, mean P2 - P0 = {(w.P2 - w.P0).mean():+.4f}.")
    for (fam, n), s in w.groupby(["family", "n"]):
        L.append(f"  - {fam} n={int(n)}: {len(s)} circuits; P0>P1 {int((s.P0 > s.P1).sum())}, P2>P1 {int((s.P2 > s.P1).sum())}, both {int(((s.P0 > s.P1) & (s.P2 > s.P1)).sum())}, P2>P0 {int((s.P2 > s.P0).sum())}; mean P0 {s.P0.mean():.4f}, P1 {s.P1.mean():.4f}, P2 {s.P2.mean():.4f}")
    viol = w[~both]
    L.append(f"[F] Circuits where P1 is not below both ({len(viol)}): " + "; ".join(f"{r.file} (P0 {r.P0:.4f}, P1 {r.P1:.4f}, P2 {r.P2:.4f})" for _, r in viol.iterrows()) + ".")
    # sampling resolution
    L.append(f"[F] Sampling resolution: mean F_H_ideal_sampled_mean (noiseless, 2000 shots) = {d.F_H_ideal_sampled_mean.mean():.4f}; "
             f"two draws of the same noisy circuit differ at the level of the proxy sampled sd, mean {p.F_H_proxy_sampled_sd.mean():.4f} (rows with proxy).")
elif "P0" in have and "P2" in have:
    w = w.dropna(subset=["P0", "P2"])
    L.append(f"[F] P1 was not run (pipelines present: {', '.join(have)}), so the ordering P0 ~ P2 above P1 cannot be tested from this CSV. "
             f"Circuits with P0 and P2: {len(w)}; P2 > P0: {int((w.P2 > w.P0).sum())}, P2 < P0: {int((w.P2 < w.P0).sum())}, equal: {int((w.P2 == w.P0).sum())}; "
             f"mean P2 - P0 = {(w.P2 - w.P0).mean():+.4f}.")
else:
    L.append(f"[F] Pipelines present: {', '.join(have)}; no ordering test possible.")

txt = "\n".join(L) + "\n"
print(txt)
if "--write" in sys.argv:
    with open(MD, "a") as fh:
        fh.write(txt)
    print("appended to", MD)
