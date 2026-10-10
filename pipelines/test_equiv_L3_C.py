"""Fast offline tests for equiv_L3_C (no compilation, < 30 s)."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import equiv_L3_C as Q  # noqa: E402

ALLOWED = {"proven", "proven-up-to-rounding", "not-provable-pyzx", "inconclusive",
           "timeout", "error", "not-compiled", "not-run"}


def test_csv_covers_family_C_and_matches_strong_baselines():
    eq = pd.read_csv(Q.OUTCSV)
    tg = Q.targets().set_index("file")
    assert len(eq) == 20 and sorted(eq.file) == sorted(tg.index)
    for r in eq.itertuples():
        assert r.verdict in ALLOWED, r.verdict
        assert r.n == tg.at[r.file, "n"]
        assert abs(r.hqc_csv - tg.at[r.file, "hqc_L3"]) < 1e-9
        assert abs(r.hqc_L2_csv - tg.at[r.file, "hqc_L2"]) < 1e-9
        if r.verdict.startswith("proven"):
            assert r.method == "pyzx-miter"
            assert bool(r.hqc_match) and abs(r.hqc - r.hqc_csv) < 1e-6
            assert r.max_snap_halfturns <= Q.E.OFFGRID_TOL
            assert os.path.exists(Q.Q.compiled_path("L3", r.file))
        if r.verdict == "proven":
            assert r.max_snap_halfturns <= 1e-9
        if r.verdict == "not-provable-pyzx":
            assert r.method == "basis-spot-check"
            assert r.max_snap_halfturns > Q.E.OFFGRID_TOL


def test_stored_qasm_hqc_matches_csv_for_proven():
    eq = pd.read_csv(Q.OUTCSV)
    for r in eq[eq.verdict == "proven"].itertuples():
        u, _ = Q.E.load(Q.Q.compiled_path("L3", r.file))
        assert abs(Q.SB.counts(u)["hqc"] - r.hqc_csv) < 1e-6, r.file


def test_summary_totals():
    F = Q.summary_facts()
    eq = F["table"]
    P = eq[eq.verdict == "proven"]
    assert F["n_proven"] == len(P)
    assert abs(F["L2_proven"] - P.hqc_L2_csv.sum()) < 1e-6
    assert abs(F["L3_proven"] - P.hqc_csv.sum()) < 1e-6
    assert abs(F["saving_all"] - 100 * (1 - eq.hqc_csv.sum() / eq.hqc_L2_csv.sum())) < 1e-9


def test_rerun_one_small_proof():
    """Rerun the miter on the stored L3 output of vbe_adder_7."""
    f = "vbe_adder_7.qasm"
    u, _ = Q.E.load(Q.Q.compiled_path("L3", f))
    assert abs(Q.SB.counts(u)["hqc"] - 232.2) < 1e-6
    res = Q.Q.miter_check(f, "L3")
    assert res["verdict"] == "proven", res
