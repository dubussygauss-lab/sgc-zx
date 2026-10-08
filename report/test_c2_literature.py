"""Checks of Table C2 (report/make_tables.py:literature_c2).  Run: python3 report/test_c2_literature.py"""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tables as mt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lit = pd.read_csv(os.path.join(ROOT, "results", "literature_tcounts.csv"))
cert = pd.read_csv(os.path.join(ROOT, "results", "certificates.csv"))
r = mt.literature_c2()
t = r["t"]

# our columns match the count CSVs and the certificate
for fam, f in [("B1", "family_B1_counts.csv"), ("B1x", "family_B1x_counts.csv")]:
    d = pd.read_csv(os.path.join(ROOT, "results", f)); d = d[d.pipeline == "P2"]
    for x in d.itertuples():
        row = t[t.circuit == x.file[:-5]].iloc[0]
        assert row["T written"] == x.t_count_as_written and row["T after ZX"] == x.t_count_zx, x.file
assert len(t) == 23
c = cert[cert.family == "B1"]
for x in c.itertuples():
    row = t[t.circuit == x.file[:-5]].iloc[0]
    assert row["floor"] == x.lde_floor and row["T after ZX"] == x.t_zx_P2
# best = independent min over eligible rows
for row in t.itertuples():
    g = lit[(lit.circuit == row.circuit) & (lit.ancilla_free == "yes") & (lit.same_circuit == "yes") & (lit.reported_error == "no")]
    b = g.published_t.min() if len(g) else np.nan
    assert (np.isnan(b) and np.isnan(row._6)) or b == row._6, row.circuit
# decomposition identities
d = t[t.floor.notna()]
assert (d["T after ZX - best"] + d["best - floor"] == d["T after ZX"] - d.floor).all()
assert (d["best - floor"] >= 0).all(), "a published ancilla-free T-count lies below the certified floor"
assert (d["best ancilla-free"] <= d["T after ZX"]).all()
assert r["tot"] == {"T after ZX": 106, "best": 105, "floor": 47, "headroom": 1, "open": 58, "gap": 59}, r["tot"]
# spot values copied from the papers
def v(c, k): return set(lit[(lit.circuit == c) & (lit.source_key == k)].published_t)
assert v("mod5_4", "KvdW2020_PyZXTODD") == {7} and v("mod5_4", "AQ2024") == {7}
assert v("qft_4", "AM2016_Tpar") == {67} and v("qft_4", "TODD2018") == {55}
assert v("grover_5", "AM2016_Tpar") == {52}
assert (lit[lit.circuit == "grover_5"].same_circuit == "no").all()
print("test_c2_literature: all checks passed")
