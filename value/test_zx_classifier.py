"""Fast checks for value/zx_classifier.py (no model training).

Run: python3 -m pytest -q value/test_zx_classifier.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import zx_classifier as zc  # noqa: E402


def test_qasm_features_toy(tmp_path):
    q = tmp_path / "toy.qasm"
    q.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\n'
                 "h q[0];\nt q[0];\ncx q[0],q[1];\nrz(0.2) q[1];\nrz(pi/4) q[2];\n"
                 "rz(pi/2) q[2];\ntdg q[2];\ncx q[1],q[2];\n")
    f = zc.qasm_features(q)
    assert f["n_qubits"] == 3 and f["n_gates"] == 8
    assert f["n_cx"] == 2 and f["n_h"] == 1
    assert f["n_t"] == 3          # t, rz(pi/4), tdg
    assert f["n_cont"] == 1       # rz(0.2)
    assert f["depth"] == 5        # h, t, cx, rz(0.2), cx on the q0-q1-q2 chain
    assert zc.zx_spiders(q) > 0


def test_scientific_notation_angle(tmp_path):
    q = tmp_path / "sci.qasm"
    q.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nrz(9.5e-05) q[0];\n')
    assert zc.qasm_features(q)["n_cont"] == 1
    assert zc.zx_spiders(q) > 0


def test_groups_do_not_leak_family_names():
    assert zc.group_of("A", "tfim_n8_r2_disorder_s3.qasm") == "A:tfim_n8"
    assert zc.group_of("B2", "haar_n3_eps1e-05_s4.qasm") == "B2:haar_n3"
    assert zc.group_of("B1", "vbe_adder_3.qasm") == zc.group_of("C", "vbe_adder_18.qasm")
    assert zc.group_of("B1", "tof_3.qasm") == zc.group_of("B1x", "tof_10.qasm")
    assert "family" not in zc.FEATURES


def test_evaluate_regret_toy():
    sub = pd.DataFrame({"hqc_P0": [10.0, 20.0, 30.0], "hqc_P2": [12.0, 15.0, 30.0]})
    sub["hqc_oracle"] = np.minimum(sub.hqc_P0, sub.hqc_P2)
    sub["pays"] = (sub.hqc_P2.round(6) < sub.hqc_P0.round(6)).astype(int)
    assert list(sub.pays) == [0, 1, 0]          # tie counts as does not pay
    r0 = zc.evaluate(sub, [0, 0, 0])
    r2 = zc.evaluate(sub, [1, 1, 1])
    assert r0["regret"] == 5.0 and r2["regret"] == 2.0
    assert r0["regret_gated"] == 5.0 and r0["skipped"] == 3
    perfect = zc.evaluate(sub, [0, 1, 0])
    assert perfect["regret"] == 0.0 and perfect["bal_acc"] == 1.0


def test_output_csv_consistent():
    p = HERE / "zx_classifier.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    assert len(d) == 245
    assert (d.pays == (d.hqc_P2.round(6) < d.hqc_P0.round(6)).astype(int)).all()
    assert d.groupby("family").size().to_dict() == {"A": 180, "B1": 15, "B1x": 8, "B2": 20, "C": 20, "U": 2}
    for s in ("lofo", "gcv"):
        assert d[f"{s}_logreg"].notna().all() and d[f"{s}_gbt"].notna().all()
    # grouped CV: no construction group appears in two folds
    assert (d.groupby("group").gcv_fold.nunique() == 1).all()
    m = pd.read_csv(HERE / "zx_classifier_metrics.csv")
    pooled = m[(m.family == "pooled") & (m.scheme == "gcv")].set_index("policy")
    assert np.isclose(pooled.loc["always_P0", "regret"], (d.hqc_P0 - d.hqc_oracle).sum())
    assert np.isclose(pooled.loc["always_P2", "regret"], (d.hqc_P2 - d.hqc_oracle).sum())
