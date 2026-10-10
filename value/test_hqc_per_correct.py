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
    assert len(D) == 48
    assert D.groupby("run").size().to_dict() == {
        "nexus_H2-2E": 6, "nexus_H2-2E_r2": 4, "nexus_H2-2E_r3": 4, "nexus_H2-2E_r4": 4,
        "nexus_H2-2E_famC": 2, "nexus_H2-2E_famC_nz": 2, "nexus_H2-2E_famC_multi": 12,
        "nexus_H2-2E_famB1_multi": 14}


def test_counts_equal_FH():
    used = D[D.ideal_bits.notna()]
    assert len(used) == 40
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
    assert h["n_pairs"] == 8
    assert list(R["T"].circuit) == ["vbe_adder_3", "hwb6", "vbe_adder_7", "vbe_adder_7_nz", "cdkm_adder_10",
                                    "modadd_2n_10", "vbe_adder_3", "hwb6"]
    assert list(R["T"].psel4) == [False, False, False, True, True, True, True, True]
    assert h["n_pairs_psel4"] == 5
    P = R["T"][R["T"].psel4]
    assert h["n_alt_cheaper_psel4"] == int((P.R < 1).sum())
    assert h["n_upper_delta_below_1_psel4"] == int((P.R_hi_delta < 1).sum())
    assert h["n_alt_cheaper"] == int((R["T"].R < 1).sum())
    assert h["n_upper_delta_below_1"] == int((R["T"].R_hi_delta < 1).sum())
    assert np.isclose(h["R_pooled"], (R["T"].hqc_alt.sum() / R["T"].K_alt.sum())
                      / (R["T"].hqc_P0.sum() / R["T"].K_P0.sum()))


def test_b1_multi_rows_by_hand():
    import sys
    sys.path.insert(0, str(ROOT / "submit"))
    import h22e_b1_run as B
    sub = D[D.run == "nexus_H2-2E_famB1_multi"]
    assert len(sub) == 14 and (sub.ideal_source == "h22e_b1_run.expected_bits").all()
    for circ, alt in (("vbe_adder_3", "L3"), ("hwb6", "P2L3")):
        s = sub[sub.circuit == circ]
        k0, k1 = s[s.pipeline == "P0"].K.sum(), s[s.pipeline == alt].K.sum()
        h0, h1 = s[s.pipeline == "P0"].hqc.sum(), s[s.pipeline == alt].hqc.sum()
        row = R["T"][(R["T"].circuit == circ) & (R["T"].runs == "H2-2E_famB1_multi")].iloc[0]
        assert row.alt == alt and row.psel4 and row.shots_per_arm == 400 * B.CIRCUITS[circ][2]
        assert np.isclose(row.R, (h1 / k1) / (h0 / k0))
