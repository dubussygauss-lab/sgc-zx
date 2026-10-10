"""Tests for value/psel4_conservative.py (no compilation)."""
import ast
import os
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import psel4_conservative as PC  # noqa: E402


@pytest.fixture(scope="module")
def d():
    return PC.compute()


def test_tie_order_matches_pass_select():
    src = open(os.path.join(ROOT, "pipelines", "pass_select.py")).read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "TIE_ORDER":
            assert ast.literal_eval(node.value) == PC.TIE_ORDER
            return
    pytest.fail("TIE_ORDER not found")


def test_rows_and_statuses(d):
    assert len(d) == 217
    seen = set()
    for c in PC.CANDS:
        seen |= set(d[f"status_{c}"])
    assert seen <= {s[0] for s in PC.STATUS_MAP}


def test_psel4_recomputed(d):
    assert (d.pick_PSEL4_re == d.pick_PSEL4).all()


def test_pick_is_min_over_verified(d):
    for r in d.itertuples():
        ver = [c for c in PC.CANDS if getattr(r, f"ver_{c}") and pd.notna(getattr(r, f"hqc_{c}"))]
        if not ver:
            assert r.pick_cons == "P0" and r.flag_cons == PC.FLAG
            continue
        assert r.flag_cons == ""
        assert r.pick_cons in ver
        assert abs(r.hqc_cons - min(getattr(r, f"hqc_{c}") for c in ver)) < 1e-9


def test_equals_psel4_when_all_verified(d):
    for r in d.itertuples():
        avail = [c for c in PC.CANDS if pd.notna(getattr(r, f"hqc_{c}"))]
        if all(getattr(r, f"ver_{c}") for c in avail):
            assert r.pick_cons == r.pick_PSEL4


def test_never_above_verified_L2(d):
    x = d[d.ver_P0]
    assert (x.hqc_cons <= x.hqc_P0 + 1e-9).all()


def test_C_unchecked_needs_pyzx(d):
    c = d[d.family == "C"]
    for cand in PC.CANDS:
        assert set(c[f"ver_{cand}_rule"]) <= {"b", "-"}
    nonc = d[d.family != "C"]
    for cand in PC.CANDS:
        assert "b" not in set(nonc[f"ver_{cand}_rule"])


def test_headline_numbers(d):
    t0, t3, tc = d.hqc_P0.sum(), d.hqc_L3.sum(), d.hqc_cons.sum()
    assert abs(tc - 51628.8) < 1e-6
    assert abs(100 * (t0 - tc) / t0 - 12.2514) < 1e-3
    assert abs(100 * (t3 - tc) / t3 - (-1.9683)) < 1e-3
    assert list(d[d.flag_cons == PC.FLAG].file) == ["hrs_mult_5.qasm"]
    diff = d[d.pick_cons != d.pick_PSEL4]
    assert sorted(zip(diff.file, diff.pick_PSEL4, diff.pick_cons)) == [
        ("draper_adder_28.qasm", "P2L3", "L3"), ("hrs_mult_5.qasm", "P2", "P0"),
        ("rgqft_mult_6.qasm", "L3", "P2")]


def test_md_written_from_code(d):
    PC.main()
    md = open(PC.OUT_MD).read()
    assert "| conservative PSEL4 | 51628.8 | 12.25 | -1.97 |" in md
    assert "proven-only" not in md.lower()
