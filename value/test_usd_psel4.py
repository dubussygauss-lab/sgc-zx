"""Fast checks for value/usd_psel4.py (about 1 s). Run: python3 -m pytest value/test_usd_psel4.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))
import usd_psel4 as U  # noqa: E402

R = U.compute()
T = R["T"].set_index("family")
L = pd.read_csv(ROOT / "value" / "psel4_ledger.csv")


def test_prices():
    assert np.isclose(R["p_std"], 12.5)
    assert np.isclose(R["p_prem"], 175000 / 17000)


def test_totals_from_ledger():
    assert T.loc["total", "n"] == len(L) == 217
    assert np.isclose(T.loc["total", "saved_vs_L2"], (L.hqc_P0 - L.hqc_PSEL4).sum())
    assert np.isclose(T.loc["total", "saved_vs_L3"], (L.hqc_L3 - L.hqc_PSEL4).sum())
    d = L.hqc_L3 - L.hqc_P0
    assert np.isclose(T.loc["total", "l3_loss"], d[d > 0].sum())
    fam = T.drop(index="total")
    for c in ("saved_vs_L2", "saved_vs_L3", "l3_loss", "n"):
        assert np.isclose(fam[c].sum(), T.loc["total", c])


def test_usd_and_monthly():
    t = T.loc["total"]
    assert np.isclose(t.saved_vs_L2_usd_standard, t.saved_vs_L2 * 12.5)
    assert t.saved_vs_L2_usd_premium < t.saved_vs_L2_usd_standard
    m = R["monthly"]
    assert np.isclose(m["freed_hqc"], 10000 * (1 - L.hqc_PSEL4.sum() / L.hqc_P0.sum()))
    assert np.isclose(m["freed_usd_standard"], m["freed_hqc"] * 12.5)


def test_psel4_never_above_l2_or_l3():
    assert (L.hqc_PSEL4 <= L.hqc_P0 + 1e-9).all()
    assert (L.hqc_PSEL4 <= L.hqc_L3 + 1e-9).all()
