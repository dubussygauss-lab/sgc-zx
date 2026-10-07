"""Recompute every family B1x number quoted in report/report_v3.md
(Sections 2.1, 3.2.1, 5, 6 and the changelog) from results/family_B1x_counts.csv,
results/family_B1x_summary.csv and bench/family_B1x/manifest.csv.

Run from anywhere: python report/recompute_b1x_check.py
"""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")

b = pd.read_csv(f"{R}/family_B1x_counts.csv")
s = pd.read_csv(f"{R}/family_B1x_summary.csv")
man = pd.read_csv(f"{ROOT}/bench/family_B1x/manifest.csv")

print("rows", len(b), "| circuits", b.file.nunique(), "| pipelines", sorted(b.pipeline.unique()))
print("status values:", sorted(b.status.unique()), "| native on all rows:", bool(b.native.all()))
print("check columns all NaN:", bool(b[["check_dev", "dist_maxdiff", "qasm_dist_maxdiff"]].isna().all().all()))
print("n range:", int(b.n.min()), "to", int(b.n.max()))
print("manifest: circuits", len(man), "| n range", int(man.n.min()), "to", int(man.n.max()),
      "| max gates after expansion", int(man.n_gates.max()),
      "| one commit:", man.commit.nunique() == 1, man.commit.iloc[0][:8])
print("manifest list by n:", [(f.replace('.qasm', ''), int(n)) for f, n in zip(man.file, man.n)])
print("summary status columns all ok-unchecked:",
      bool((s[["status_P0ref", "status_P0", "status_P2"]] == "ok-unchecked").all().all()))

piv = b.pivot_table(index="file", columns="pipeline", values="n_2q")
dep = b.pivot_table(index="file", columns="pipeline", values="depth_2q")
tz = b.pivot_table(index="file", columns="pipeline", values="t_count_zx")
meta = b[b.pipeline == "P0ref"].set_index("file")[["n", "t_count_written", "n_cx_as_written"]].reindex(piv.index)
order = meta.sort_values(["n", "t_count_written"]).index

print("\nper circuit (file, n, ZZ P0ref, P0, P2, P2 vs P0 %, depth_2q P0, P2, T written, T after ZX P2):")
for f in order:
    red = 100 * (1 - piv.loc[f, "P2"] / piv.loc[f, "P0"])
    print(f"  {f.replace('.qasm',''):16s} n={int(meta.loc[f,'n']):2d} "
          f"{int(piv.loc[f,'P0ref']):4d} {int(piv.loc[f,'P0']):4d} {int(piv.loc[f,'P2']):4d} "
          f"{red:6.1f}  {int(dep.loc[f,'P0']):4d} {int(dep.loc[f,'P2']):4d}  "
          f"{int(meta.loc[f,'t_count_written']):4d} {int(tz.loc[f,'P2']):4d}")

below = int((piv.P2 < piv.P0).sum())
equal = int((piv.P2 == piv.P0).sum())
above = int((piv.P2 > piv.P0).sum())
print(f"\nP2 vs P0 on {len(piv)} circuits: below {below}, equal {equal}, above {above}")
print("equal on:", sorted(f.replace(".qasm", "") for f in piv.index[piv.P2 == piv.P0]))
red = 100 * (1 - piv.P2 / piv.P0)
print(f"mean P2 reduction vs P0 over the 8 circuits: {red.mean():.1f} %")
fmax = red.idxmax()
print(f"largest reduction: {fmax.replace('.qasm','')} {int(piv.loc[fmax,'P0'])} to {int(piv.loc[fmax,'P2'])}, {red.max():.1f} %")
zz0, zz2, zzref = int(piv.P0.sum()), int(piv.P2.sum()), int(piv.P0ref.sum())
print(f"aggregate ZZ: P0ref {zzref}, P0 {zz0}, P2 {zz2}, P2 vs P0 {100*(1-zz2/zz0):.1f} %, P0 vs P0ref {100*(1-zz0/zzref):.1f} %")
print("P0 below P0ref on", int((piv.P0 < piv.P0ref).sum()), "of", len(piv))
print("P2 depth_2q below P0 on", int((dep.P2 < dep.P0).sum()), "equal", int((dep.P2 == dep.P0).sum()),
      "above", int((dep.P2 > dep.P0).sum()), "| above on:",
      sorted(f.replace(".qasm", "") for f in dep.index[dep.P2 > dep.P0]))
print("P0ref n_2q == n_cx_as_written on", int((piv.P0ref == meta.n_cx_as_written).sum()), "of", len(piv))
for f in piv.index[piv.P0ref != meta.n_cx_as_written]:
    print(f"  {f.replace('.qasm','')}: n_cx written {int(meta.loc[f,'n_cx_as_written'])}, P0ref ZZ {int(piv.loc[f,'P0ref'])}, "
          f"difference {int(meta.loc[f,'n_cx_as_written'] - piv.loc[f,'P0ref'])}")
tred = 100 * (1 - tz.P2 / meta.t_count_written)
print(f"T after ZX P2 vs T written: min {tred.min():.1f} %, max {tred.max():.1f} %, mean {tred.mean():.1f} %; "
      f"total T written {int(meta.t_count_written.sum())}, total T after ZX {int(tz.P2.sum())}")
print("n_non_cliffordT_zx max:", float(b.n_non_cliffordT_zx.max()))
print(f"wall time: sum t_wall {b.t_wall.sum():.1f} s, max t_wall {b.t_wall.max():.1f} s ({b.loc[b.t_wall.idxmax(),'file']} {b.loc[b.t_wall.idxmax(),'pipeline']})")
print("summary n_2q columns agree with counts pivot:",
      bool((s.set_index("file").loc[piv.index, ["n_2q_P0ref", "n_2q_P0", "n_2q_P2"]].values == piv[["P0ref", "P0", "P2"]].values).all()))

try:
    from pytket.qasm import circuit_from_qasm
    from pytket.passes import RemoveRedundancies
    from pytket import OpType
    for f in ["rc_adder_6", "csla_mux_3"]:
        c = circuit_from_qasm(f"{ROOT}/bench/family_B1x/{f}.qasm")
        before = c.n_gates_of_type(OpType.CX)
        RemoveRedundancies().apply(c)
        print(f"RemoveRedundancies alone on {f}: CX {before} to {c.n_gates_of_type(OpType.CX)}")
except ImportError as e:
    print("pytket not available, RemoveRedundancies check skipped:", e)
