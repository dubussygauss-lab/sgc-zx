import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd


def test_counts_match_ledger():
    L = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "value", "psel4_ledger.csv"))
    assert int((L.hqc_L3 > L.hqc_P0 + 1e-9).sum()) == 45
    assert int((L.hqc_PSEL4 > L.hqc_P0 + 1e-9).sum()) == 0
    assert abs(float((L.hqc_L3 / L.hqc_P0).max()) - 1.1295) < 1e-3


def test_figure_written():
    import fig_policy
    fig_policy.main()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for ext in (".png", ".pdf"):
        assert os.path.getsize(os.path.join(root, "report", "figures", "fig_policy" + ext)) > 1000
