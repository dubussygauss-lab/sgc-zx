"""Tests for value/value_by_application.py.  Run: python3 -m pytest value/test_value_by_application.py

1. Every B1 and B1x circuit of the ledger is assigned to exactly one primary area.
2. Each area row equals the sum of the ledger rows of its circuits (HQC and T columns).
3. Families are never merged: every area row holds circuits of one family only, and the
   family totals equal the ledger TOTAL rows.
4. The control and B2 blocks equal the ledger values.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))

import value_by_application as vba  # noqa: E402


@pytest.fixture(scope="module")
def out():
    subprocess.run([sys.executable, str(ROOT / "value/value_by_application.py")], check=True,
                   capture_output=True)
    return pd.read_csv(ROOT / "value/value_by_application.csv")


@pytest.fixture(scope="module")
def led():
    return pd.read_csv(ROOT / "value/value_ledger.csv")


@pytest.fixture(scope="module")
def amap(led):
    files = sorted(led[(led.layer == "NISQ") & led.family.isin(vba.FAMILIES)
                       & (led.row_kind == "circuit")].file)
    return vba.assign_areas(files, vba.read_summary_table())


def test_each_circuit_assigned_once(led, amap):
    files = set(led[(led.layer == "NISQ") & led.family.isin(vba.FAMILIES) & (led.row_kind == "circuit")].file)
    assert set(amap.file) == files
    assert amap.file.is_unique
    # the three adders are double-listed and go to integer factoring
    for f in ("vbe_adder_3.qasm", "rc_adder_6.qasm", "csla_mux_3.qasm"):
        r = amap[amap.file == f].iloc[0]
        assert r.area.startswith("Integer factoring")
        assert "chemistry" in r.secondary_areas
    # mod5_4 is a Grover oracle, not Shor arithmetic
    assert amap[amap.file == "mod5_4.qasm"].area.iloc[0].startswith("Unstructured search")


def test_area_rows_equal_ledger_sums(out, led, amap):
    rows = out[(out.block == "area") & (out.area != "ALL (family total)")]
    assert len(rows) > 0
    for r in rows.itertuples():
        files = set(amap[amap.area == r.area].file)
        nisq = led[(led.layer == "NISQ") & (led.family == r.family) & led.file.isin(files)]
        ft = led[(led.layer == "FT") & (led.family == r.family) & led.file.isin(files)]
        assert len(nisq) == r.n_circuits == len(ft)
        assert np.isclose(nisq.hqc_P0.sum(), r.hqc_P0)
        assert np.isclose(nisq.hqc_P2.sum(), r.hqc_P2)
        assert np.isclose(nisq.hqc_saved.sum(), r.hqc_saved)
        assert np.isclose(ft.T_written.sum(), r.T_written)
        assert np.isclose(ft.T_zx_P2.sum(), r.T_after_zx)
        assert np.isclose(ft.magic_saved.sum(), r.magic_saved)
        assert np.isclose(100 * (r.hqc_P0 - r.hqc_P2) / r.hqc_P0, r.hqc_saved_pct)


def test_families_unmerged(out, led):
    rows = out[out.block == "area"]
    assert set(rows.family) == {"B1", "B1x"}
    for r in rows[rows.area != "ALL (family total)"].itertuples():
        names = {c.strip() + ".qasm" for c in r.circuits.split(",")}
        fam = set(led[(led.layer == "NISQ") & led.file.isin(names) & (led.row_kind == "circuit")].family)
        assert fam == {r.family}, (r.area, fam)
    for fam in ("B1", "B1x"):
        tot = rows[(rows.family == fam) & (rows.area == "ALL (family total)")].iloc[0]
        lt = led[(led.layer == "NISQ") & (led.family == fam) & (led.row_kind == "total")].iloc[0]
        ft = led[(led.layer == "FT") & (led.family == fam) & (led.row_kind == "total")].iloc[0]
        assert np.isclose(tot.hqc_P0, lt.hqc_P0) and np.isclose(tot.hqc_P2, lt.hqc_P2)
        assert np.isclose(tot.magic_saved, ft.magic_saved)
        parts = rows[(rows.family == fam) & (rows.area != "ALL (family total)")]
        assert np.isclose(parts.hqc_saved.sum(), tot.hqc_saved)
        assert parts.n_circuits.sum() == tot.n_circuits


def test_control_and_b2_blocks(out, led):
    a = out[(out.block == "family_A_control") & (out.area == "Trotter control (ALL)")].iloc[0]
    la = led[(led.layer == "NISQ") & (led.family == "A") & (led.row_kind == "total")].iloc[0]
    assert np.isclose(a.hqc_P0, la.hqc_P0) and np.isclose(a.hqc_P2, la.hqc_P2)
    assert a.hqc_P2 > a.hqc_P0
    b2 = out[out.block == "family_B2_certified"].iloc[0]
    lb = led[(led.layer == "FT") & (led.family == "B2") & (led.row_kind == "total")].iloc[0]
    assert np.isclose(b2.cert_floor / b2.T_after_zx, lb.cert_incompressible_frac_of_remaining)
    b1 = out[out.block == "family_B1_certified"].iloc[0]
    lb1 = led[(led.layer == "FT") & (led.family == "B1") & (led.row_kind == "total")].iloc[0]
    assert np.isclose(b1.certified_fraction, lb1.cert_incompressible_frac_of_remaining)


def test_shots_affordable_capped_brute_force():
    """The capped shot count is the largest S whose cost with ceil(S / cap) job fees fits the budget."""
    for h in (151.6, 119.0, 68.4, 64.0, 565.6, 528.2):
        k = (h - vba.JOB_FEE) * 5000 / vba.SHOTS_CSV
        cost = lambda s: vba.JOB_FEE * int(np.ceil(s / vba.JOB_SHOT_CAP)) + s * k / 5000  # noqa: E731
        s = vba.shots_affordable_capped(h)
        assert cost(s) <= vba.BUDGET + 1e-9
        assert cost(s + 1) > vba.BUDGET
