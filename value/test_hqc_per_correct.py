"""Checks for value/hqc_per_correct.py (about 25 s, the vbe_adder_7 reference simulation dominates).
Run: python3 -m pytest value/test_hqc_per_correct.py"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))
import hqc_per_correct as HP  # noqa: E402

R = HP.compute()
T = R["T"].set_index("circuit")
D = R["df"]


def test_payload_inventory():
    assert len(D) == 34
    assert D.groupby("run").size().to_dict() == {
        "nexus_H2-2E": 6, "nexus_H2-2E_r2": 4, "nexus_H2-2E_r3": 4, "nexus_H2-2E_r4": 4,
        "nexus_H2-2E_famC": 2, "nexus_H2-2E_famC_nz": 2, "nexus_H2-2E_famC_multi": 12}


def test_counts_equal_FH():
    used = D[D.ideal_bits.notna()]
    assert len(used) == 26
    assert (used.absdiff_FH <= 1e-9).all()


def test_grover_excluded_uniform():
    ex = R["excluded"]
    assert [e["circuit"] for e in ex] == ["grover_5"]
    assert ex[0]["support"] == 64 and abs(ex[0]["p_max"] - 1 / 64) < 1e-12


def test_pair_arithmetic():
    for c, t in T.iterrows():
        assert math.isclose(t.p_P0, t.K_P0 / t.shots_per_arm)
        assert math.isclose(t.R, (t.hqc_alt / t.K_alt) / (t.hqc_P0 / t.K_P0))
        assert math.isclose(t.R, t.hqc_per_1000_correct_alt / t.hqc_per_1000_correct_P0)
        assert t.R_lo_delta < t.R < t.R_hi_delta
        assert t.R_lo_boot < t.R < t.R_hi_boot
        assert abs(t.R_hi_delta - t.R_hi_boot) < 0.01


def test_cdkm_by_hand():
    sub = D[(D.circuit == "cdkm_adder_10")]
    k0 = sub[sub.pipeline == "P0"].K.sum()
    k1 = sub[sub.pipeline == "L3"].K.sum()
    h0 = sub[sub.pipeline == "P0"].hqc.sum()
    h1 = sub[sub.pipeline == "L3"].hqc.sum()
    assert np.isclose(T.loc["cdkm_adder_10", "R"], (h1 / k1) / (h0 / k0))
    assert abs(T.loc["cdkm_adder_10", "R"] - 0.92) < 0.01


def test_headline_consistent():
    h = R["head"]
    assert h["n_pairs"] == 6
    assert h["n_alt_cheaper"] == int((R["T"].R < 1).sum())
    assert h["n_upper_delta_below_1"] == int((R["T"].R_hi_delta < 1).sum())
    assert np.isclose(h["R_pooled"], (R["T"].hqc_alt.sum() / R["T"].K_alt.sum())
                      / (R["T"].hqc_P0.sum() / R["T"].K_P0.sum()))
