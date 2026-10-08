"""Tests for value/selector_ledger.py.  Run: python3 -m pytest value/test_selector_ledger.py

1. Per circuit the selector HQC is <= min(HQC_P0, HQC_P2) and equals one of them.
2. Every family total equals the sum of its circuit rows, and saved columns are consistent.
3. Families are never merged: one 'all' row per family, A also split by model, and the
   circuit counts match the source CSVs.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def out():
    subprocess.run([sys.executable, str(ROOT / "value/selector_ledger.py")], check=True,
                   capture_output=True)
    return (pd.read_csv(ROOT / "value/selector_ledger_circuits.csv"),
            pd.read_csv(ROOT / "value/selector_ledger.csv"))


def test_selector_never_dearer(out):
    r, _ = out
    m = np.minimum(r.hqc_P0, r.hqc_P2)
    assert (r.hqc_SEL <= m + 1e-9).all()
    assert np.isclose(r.hqc_SEL, m).all()
    assert (np.isclose(r.hqc_SEL, r.hqc_P0) | np.isclose(r.hqc_SEL, r.hqc_P2)).all()
    assert (r.saved_vs_P0 >= -1e-9).all() and (r.saved_vs_P2 >= -1e-9).all()


def test_tie_break(out):
    r, _ = out
    tie = r.hqc_P0.round(6) == r.hqc_P2.round(6)
    t = r[tie]
    exp = np.where(t.n2q_P2 < t.n2q_P0, "P2", "P0")
    assert (t.choice.values == exp).all()


def test_totals_equal_sums(out):
    r, s = out
    for _, row in s.iterrows():
        g = r[r.family == row.family]
        if row.group != "all":
            g = g[g.model == row.group]
        assert len(g) == row.circuits
        for c in ("hqc_P0", "hqc_P2", "hqc_SEL"):
            assert np.isclose(g[c].sum(), row[c]), (row.family, row.group, c)
        assert np.isclose(row.saved_vs_P0, row.hqc_P0 - row.hqc_SEL)
        assert np.isclose(row.saved_vs_P2, row.hqc_P2 - row.hqc_SEL)
        assert np.isclose(row.saved_vs_P0_pct, 100 * row.saved_vs_P0 / row.hqc_P0)
        assert row.n2q_SEL == g.n2q_SEL.sum()
        assert row.picks_P2 + row.picks_P0 == row.circuits


def test_families_unmerged(out):
    r, s = out
    alls = s[s.group == "all"]
    assert sorted(alls.family) == ["A", "B1", "B1x", "B2"]
    assert alls.family.is_unique
    assert set(s[s.family == "A"].group) == {"all", "tfim", "ladder", "xxz"}
    a = s[s.family == "A"].set_index("group")
    assert a.loc[["tfim", "ladder", "xxz"], "circuits"].sum() == a.loc["all", "circuits"]
    led = pd.read_csv(ROOT / "value/value_ledger.csv")
    led = led[(led.layer == "NISQ") & (led.row_kind == "circuit")]
    for fam in ("A", "B1", "B1x"):
        assert alls.set_index("family").loc[fam, "circuits"] == (led.family == fam).sum()
    b2 = pd.read_csv(ROOT / "results/family_B2_counts.csv")
    assert alls.set_index("family").loc["B2", "circuits"] == (b2.pipeline == "P0").sum()
