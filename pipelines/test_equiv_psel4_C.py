"""Fast offline tests for equiv_psel4_C (no compilation, < 30 s)."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import equiv_psel4_C as Q  # noqa: E402

ALLOWED = {"proven", "proven-up-to-rounding", "equal-up-to-rounding", "inconclusive",
           "timeout", "error", "not-compiled", "not-run"}


def test_picks_are_minimal_and_complete():
    picks = Q.psel4_picks()
    assert len(picks) == 20
    for r in picks.itertuples():
        hqcs = [getattr(r, f"hqc_{c}") for c in Q.ORDER]
        assert abs(r.hqc - min(hqcs)) < 1e-9


def test_csv_rows_match_picks():
    eq = pd.read_csv(Q.OUTCSV)
    picks = Q.psel4_picks()
    want = picks[picks.pick.isin(["L3", "P2L3"])]
    assert sorted(eq.file) == sorted(want.file)
    m = dict(zip(want.file, want.pick))
    h = dict(zip(want.file, want.hqc))
    for r in eq.itertuples():
        assert r.pick == m[r.file]
        assert set([r.verdict]) <= ALLOWED
        if r.verdict.startswith("proven"):
            assert r.hqc_match and abs(r.hqc - h[r.file]) < 1e-6
            assert r.max_snap_halfturns <= Q.E.OFFGRID_TOL


def test_rerun_one_small_proof():
    """Rerun the miter on the stored compiled vbe_adder_7 (L3) if present."""
    f = "vbe_adder_7.qasm"
    if not os.path.exists(Q.compiled_path("L3", f)):
        return
    u, _ = Q.E.load(Q.compiled_path("L3", f))
    assert abs(Q.SB.counts(u)["hqc"] - 232.2) < 1e-6
    res = Q.miter_check(f, "L3")
    assert res["verdict"] == "proven", res
