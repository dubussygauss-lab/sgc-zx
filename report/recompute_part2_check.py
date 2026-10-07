"""Recompute every number quoted in report/v2/part2.md from results/*.csv.

Run from anywhere: python report/recompute_part2_check.py
"""
import numpy as np, pandas as pd, os
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# ---------------- family A counts (A6, 3.1)
a = pd.read_csv(f"{R}/family_A_counts.csv")
piv = a.pivot_table(index="file", columns="pipeline", values="n_2q")
print("A: circuits", piv.shape[0])
for p in ["P1", "P2", "P3", "P4", "P0ref"]:
    r = piv[p] / piv["P0"]
    print(f"A ratio {p}/P0: min {r.min():.4f} max {r.max():.4f} mean {r.mean():.3f} worse {(piv[p]>piv['P0']).sum()} equal {(piv[p]==piv['P0']).sum()} better {(piv[p]<piv['P0']).sum()}")
r134 = pd.concat([piv[p] / piv["P0"] for p in ["P1", "P3", "P4"]])
print(f"A P1/P3/P4 pooled ratio: min {r134.min():.4f} max {r134.max():.4f}")
meta = a[a.pipeline == "P0"].set_index("file")
print("A P0 == n_cx/2:", int((meta.n_2q == meta.n_cx / 2).sum()), "of", len(meta))
# factor grows with n: mean ratio by n for P1,P3,P4
for p in ["P1", "P3", "P4"]:
    r = piv[p] / piv["P0"]
    print(p, "mean ratio by n:", {int(n): round(float(r[meta.n == n].mean()), 2) for n in sorted(meta.n.unique())})

# ---------------- family A proxy h22e (A5, 3.5)
pr = pd.read_csv(f"{R}/family_A_proxy_h22e.csv")
print("\nproxy A rows", len(pr), "circuits", pr.file.nunique(), "pipelines", sorted(pr.pipeline.unique()), "n", sorted(pr.n.unique()))
m = pr.pivot_table(index="n", columns="pipeline", values="F_H", aggfunc="mean")
print(m.round(4))
# ordering check per n: P0 ~ P2 > P0ref > P1 ~ P3
for n, row in m.iterrows():
    ok = (row.P0 > row.P0ref) and (row.P2 > row.P0ref) and (row.P0ref > row.P1) and (row.P0ref > row.P3)
    print(f"n={n}: P0 {row.P0:.4f} P2 {row.P2:.4f} > P0ref {row.P0ref:.4f} > P1 {row.P1:.4f} P3 {row.P3:.4f} -> {ok}; |P0-P2| {abs(row.P0-row.P2):.4f}; |P1-P3| {abs(row.P1-row.P3):.4f}")
# per-circuit comparisons
pf = pr.pivot_table(index="file", columns="pipeline", values="F_H")
print("P0 > P0ref per circuit:", int((pf.P0 > pf.P0ref).sum()), "/", len(pf))
print("P2 > P0 per circuit:", int((pf.P2 > pf.P0).sum()), "P2 < P0:", int((pf.P2 < pf.P0).sum()), "ties", int((pf.P2 == pf.P0).sum()))
print("P0ref > P1:", int((pf.P0ref > pf.P1).sum()), "P0ref > P3:", int((pf.P0ref > pf.P3).sum()))
print("P1 vs P3: P1>P3", int((pf.P1 > pf.P3).sum()), "P1<P3", int((pf.P1 < pf.P3).sum()))
# per model and n means (for every (n, model) cell)
mm = pr.pivot_table(index=["model", "n"], columns="pipeline", values="F_H", aggfunc="mean")
allok = True
for idx, row in mm.iterrows():
    ok = (row.P0 > row.P0ref) and (row.P2 > row.P0ref) and (row.P0ref > row.P1) and (row.P0ref > row.P3)
    allok &= ok
print("ordering P0,P2 > P0ref > P1,P3 holds in every (model, n) cell:", allok)
print(mm.round(4))
# overall means
print(pr.groupby("pipeline")[["F_H", "TVD", "n_2q", "n_1q"]].mean().round(4))

def fit_no_intercept(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    a_ = (x @ y) / (x @ x)
    res = y - a_ * x
    dof = len(x) - 1
    se = np.sqrt((res @ res) / dof / (x @ x))
    r2c = 1 - (res @ res) / ((y - y.mean()) @ (y - y.mean()))
    r2u = 1 - (res @ res) / (y @ y)
    return a_, se, r2c, r2u, np.sqrt((res @ res) / dof)

y = -np.log(pr.F_H)
aA, seA, r2A, r2uA, sdA = fit_no_intercept(pr.n_2q, y)
print(f"A fit -lnF = a n_2q: a = {aA:.4e} +/- {seA:.2e}, centred R2 {r2A:.4f}, uncentred {r2uA:.4f}, resid sd {sdA:.2e}")

# support-size effect: regress with n_1q and support
X = np.column_stack([pr.n_2q, pr.n_1q, pr.support_size])
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
res = y - X @ beta
print("A fit a n_2q + b n_1q + u support:", beta, "centred R2", 1 - (res @ res) / ((y - y.mean()) @ (y - y.mean())))
X2 = np.column_stack([pr.n_2q, pr.n_1q])
b2, *_ = np.linalg.lstsq(X2, y, rcond=None); res2 = y - X2 @ b2
print("A fit a n_2q + b n_1q:", b2, "centred R2", 1 - (res2 @ res2) / ((y - y.mean()) @ (y - y.mean())))
# per-model slopes with n term
for mdl in ["ladder", "tfim", "xxz"]:
    g = pr[pr.model == mdl]; yy = -np.log(g.F_H)
    Xm = np.column_stack([g.n_2q, g.n]); bm, *_ = np.linalg.lstsq(Xm, yy, rcond=None)
    print(f"  {mdl}: a n_2q + s n -> a {bm[0]:.4e}, s {bm[1]:.4e}; mean support {g.support_size.mean():.1f}")
print("support by model:", pr.groupby("model").support_size.mean().round(1).to_dict())

# ---------------- family B1 proxy h22e
pb = pd.read_csv(f"{R}/family_B1_proxy_h22e.csv")
print("\nproxy B1 rows", len(pb), "circuits", pb.file.nunique())
yb = -np.log(pb.F_H)
aB, seB, r2B, r2uB, sdB = fit_no_intercept(pb.n_2q, yb)
print(f"B1 fit a = {aB:.4e} +/- {seB:.2e}, centred R2 {r2B:.4f}, uncentred {r2uB:.4f}")
print("a/p2 =", aB / 1.29e-3)
pbf = pb.pivot_table(index="file", columns="pipeline", values="F_H")
print("B1 P2 > P0:", int((pbf.P2 > pbf.P0).sum()), "/", len(pbf), "; P0 > P0ref:", int((pbf.P0 > pbf.P0ref).sum()))
print("B1 P1 < P0:", int((pbf.P1 < pbf.P0).sum()), "P3 < P0:", int((pbf.P3 < pbf.P0).sum()), "P3<P0 files:", list(pbf.index[pbf.P3 >= pbf.P0]))
print("B1 support sizes:", pb.groupby("file").support_size.first().to_dict())
# 1 - F_H / n_2q crude check for B1: per-row  -lnF / n_2q
print("B1 -lnF/n_2q per row: min %.3e max %.3e" % ((yb / pb.n_2q).min(), (yb / pb.n_2q).max()))
print("A  -lnF/n_2q per row: min %.3e max %.3e median %.3e" % ((y / pr.n_2q).min(), (y / pr.n_2q).max(), (y / pr.n_2q).median()))

# ---------------- family B1 counts (A8)
b = pd.read_csv(f"{R}/family_B1_counts.csv")
pv = b.pivot_table(index="file", columns="pipeline", values="n_2q")
print("\nB1 circuits", pv.shape[0])
for p in ["P1", "P2", "P3", "P4"]:
    done = pv[p].notna()
    print(f"B1 {p}: completed {int(done.sum())}, above P0 {int((pv[p] > pv.P0).sum())}, equal {int((pv[p] == pv.P0).sum())}, below {int((pv[p] < pv.P0).sum())}, below on {list(pv.index[(pv[p] < pv.P0)])}, equal on {list(pv.index[(pv[p] == pv.P0)])}")
done = pv.dropna(subset=["P2"])
print("P2 mean reduction % :", float((100 * (1 - done.P2 / done.P0)).mean()))
print("vbe_adder_3:", pv.loc["vbe_adder_3.qasm", ["P0", "P2"]].to_dict(), 100 * (1 - 41 / 56))
tz = b.pivot_table(index="file", columns="pipeline", values="t_count_zx")
tw = b[b.pipeline == "P0ref"].set_index("file").t_count_written
for f in ["tof_3.qasm", "mod5_4.qasm", "vbe_adder_3.qasm", "grover_5.qasm"]:
    print(f, "T written", int(tw[f]), "T zx P1", tz.loc[f, "P1"], "P2", tz.loc[f, "P2"])
h = pd.read_csv(f"{R}/family_B1_hwb8_long_counts.csv")
print("hwb8 long:", h[["pipeline", "status", "n_2q", "t_count_zx", "t_wall"]].to_dict("records"))

# ---------------- certificates (A4, 3.4)
c = pd.read_csv(f"{R}/certificates.csv")
print("\ncert rows", len(c), c.family.value_counts().to_dict())
print("floor <= T_zx P1:", int((c.lde_floor <= c.t_zx_P1).sum()), "P2:", int((c.lde_floor <= c.t_zx_P2).sum()), "P1==P2:", int((c.t_zx_P1 == c.t_zx_P2).sum()))
c["ratio"] = 100 * c.lde_floor / c.t_zx_P2
c["ach"] = 100 * (1 - c.t_zx_P2 / c.t_written)
c["eps"] = c.file.str.extract(r"eps(1e-\d+)")[0]
b2 = c[c.family == "B2"]
g = b2.groupby(["n", "eps"]).agg(N=("file", "size"), ratio_mean=("ratio", "mean"), ratio_min=("ratio", "min"), ach_mean=("ach", "mean"), tw=("t_written", "mean"), coll=("collapse_rate", "mean"))
print(g.round(3))
print("B2 ratio min over 20:", b2.ratio.min(), b2.loc[b2.ratio.idxmin(), "file"], "max", b2.ratio.max())
print("B2 config means range: %.2f to %.2f" % (g.ratio_mean.min(), g.ratio_mean.max()))
print("B2 collapse rate % by config:", (100 * g.coll).round(2).to_dict())
b1 = c[c.family == "B1"]
print(b1[["file", "t_written", "lde_floor", "t_zx_P2", "ratio", "ach"]].round(2))
print("B1 floor/T_zx range: %.2f to %.2f" % (b1.ratio.min(), b1.ratio.max()))
print("B1 floor/T_written %:", (100 * b1.lde_floor / b1.t_written).round(2).tolist())
print("wall s: B2 n=2 max", b2[b2.n == 2].wall_s.max(), "n=3 max", b2[b2.n == 3].wall_s.max(), "B1 max", b1.wall_s.max())

# ---------------- selene (3.6)
s = pd.read_csv(f"{R}/selene_noiseless.csv")
print("\nselene noiseless rows", len(s), s.family.value_counts().to_dict(), s.pipeline.value_counts().to_dict())
print("circuits:", s.file.nunique(), "A circuits", s[s.family == "A"].file.nunique(), "B1", s[s.family == "B1"].file.nunique())
print("n range A:", sorted(s[s.family == "A"].n.unique()), "B1:", sorted(s[s.family == "B1"].n.unique()))
print("shots", s.shots.unique())
print("max TVD", s.TVD.max(), "max TVD/scale", s.TVD_over_scale.max(), "flagged", int(s.flag.sum()), "outside", int(s.shots_outside_support.sum()))
print("max exact_vs_ref", s.exact_vs_ref_maxdiff.max())
print("median TVD/expected", s.TVD_over_expected.median(), "max", s.TVD_over_expected.max())
sp = s.groupby(["family", "pipeline"]).agg(runs=("file", "size"), max_TVD=("TVD", "max"), max_over_scale=("TVD_over_scale", "max"), flagged=("flag", "sum"), outside=("shots_outside_support", "sum"), med_over_exp=("TVD_over_expected", "median"))
print(sp.round(3))
pooled = s.chi2_p_pooled.dropna()
print("pooled chi2: n", len(pooled), "p<0.01", int((pooled < 0.01).sum()), "p<0.05", int((pooled < 0.05).sum()))
# support<=64 runs
print("support<=64 runs:", int((s.support_size <= 64).sum()), "support==1:", int((s.support_size == 1).sum()))
d = pd.read_csv(f"{R}/selene_depolarizing.csv")
print("\nselene depol rows", len(d), d.variant.value_counts().to_dict())
for v, gv in d.groupby("variant"):
    print(v, "runs", len(gv), "agree", int(gv.agree_2sd.sum()), "mean z %.2f sd z %.2f max|z| %.2f" % (gv.z.mean(), gv.z.std(ddof=0), gv.z.abs().max()),
          "mean(F_sel - F_proxy_exact) %.4f mean(F_sel - F_sampled) %.4f" % ((gv.F_H_selene_depol - gv.F_H_proxy_exact).mean(), (gv.F_H_selene_depol - gv.F_H_proxy_sampled_mean).mean()))
    print("   ddof=1 sd z %.2f" % gv.z.std(ddof=1))
    for fam, gf in gv.groupby("family"):
        print(f"   {fam}: runs {len(gf)} agree {int(gf.agree_2sd.sum())} mean z {gf.z.mean():.2f} sd {gf.z.std(ddof=0):.2f} max|z| {gf.z.abs().max():.2f}")
print("depol circuits", d.file.nunique(), d.groupby("family").file.nunique().to_dict(), "pipelines", sorted(d.pipeline.unique()))
print("p params:", d[["p_1q", "p_2q", "p_meas", "p_init"]].drop_duplicates().to_dict("records"))
