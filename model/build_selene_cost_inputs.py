"""Build cost_model.py input CSVs from results/selene_depolarizing_full.csv.
Target F_H = F_H_selene_depol / F_H_selene_noiseless_sameseed (finite-shot corrected).
n_qubits and depth_2q joined from family_{A,B1}_counts.csv on (file, pipeline)."""
import os, pandas as pd, numpy as np
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
s = pd.read_csv(os.path.join(R, "selene_depolarizing_full.csv"))
for fam, cf in [("A", "family_A_counts.csv"), ("B1", "family_B1_counts.csv")]:
    c = pd.read_csv(os.path.join(R, cf))[["file", "pipeline", "n_qubits", "depth_2q", "n_2q", "n_phasedx"]]
    d = s[s.family == fam].merge(c, on=["file", "pipeline"], how="left", suffixes=("", "_c"), validate="1:1")
    assert d.n_qubits.notna().all() and (d.n_2q == d.n_2q_c).all() and (d.n_1q == d.n_phasedx).all()
    d["n_qubits"] = d.n_qubits.astype(int)
    d["F_H_raw"] = d.F_H_selene_depol
    d["F_H"] = d.F_H_selene_depol / d.F_H_selene_noiseless_sameseed
    out = d[["file", "model", "n", "pipeline", "n_qubits", "n_2q", "n_1q", "depth_2q", "support_size", "F_H", "F_H_raw"]]
    out.to_csv(os.path.join(R, "cost_model_selene_input_%s.csv" % fam), index=False)
    print(fam, len(out))
