"""Fast checks for value/policy_compare.py (about 1 s). Run: python3 -m pytest value/test_policy_compare.py"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))
import policy_compare as PC  # noqa: E402

R = PC.compute()
L = R["L"]


def test_ledger_shape():
    assert len(L) == 217
    assert L.family.value_counts().to_dict() == {"A": 180, "C": 20, "B1": 15, "usecase": 2}


def test_policy_totals_match_ledger_and_pool():
    pol = R["pol"].set_index("family")
    for col, key in [("hqc_P0", "L2"), ("hqc_L3", "L3"), ("hqc_PSEL4", "PSEL4")]:
        assert np.isclose(pol.loc["pooled", key], L[col].sum())
        assert np.isclose(pol.loc[PC.FAMS, key].sum(), pol.loc["pooled", key])
    # P2L3 fallback: exactly the one B1 timeout
    assert L.P2L3_fallback.sum() == 1
    assert L[L.P2L3_fallback].file.tolist() == ["hwb8.qasm"]


def test_psel4_is_min_and_never_loses():
    m = L[["hqc_P0", "hqc_P2", "hqc_L3", "hqc_P2L3"]].min(axis=1)
    assert np.allclose(L.hqc_PSEL4, m)
    assert (L.hqc_PSEL4 <= L.hqc_P0 + 1e-9).all()


def test_l3_loss_counts():
    d = L.hqc_L3 - L.hqc_P0
    row = R["loss"].query("policy == 'L3' and family == 'pooled'").iloc[0]
    assert row.n_lose == int((d > 1e-9).sum())
    assert np.isclose(row.lost_total, d[d > 1e-9].sum())
    assert np.isclose(row.max_loss, d.max())


def test_psel4_time_is_sum_of_candidates():
    w = R["ww"]
    ok = w.dropna()
    assert np.allclose(ok.PSEL4, ok[["P0", "P2", "L3", "P2L3"]].sum(axis=1))
    # usecase has no L2 timing
    assert w.xs("usecase", level="family").P0.isna().all()


def test_snippet_numbers_and_style():
    md = (ROOT / "value/policy_compare.md").read_text()
    sn = (ROOT / "report/snippets/policy_snippet.md").read_text()
    body = sn.split("## Report text", 1)[1]
    nums = re.findall(r"(?<![\w.,])\d[\d,]*(?:\.\d+)?(?![\w])", body)
    assert nums
    for n in nums:
        n = n.rstrip(",")
        assert re.search(r"(?<![\d.])" + re.escape(n) + r"(?![\d])", md), n
    for bad in [";", "—", "rather than", "usually", "in general"]:
        assert bad not in body, bad
