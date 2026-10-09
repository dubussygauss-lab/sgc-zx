"""Tests for value/family_C_selector.py.  Run: python3 -m pytest value/test_family_C_selector.py

1. Per circuit PSEL HQC equals min(HQC_P0, HQC_P2) and one of them, saving >= 0.
2. Derived columns are recomputed here from the raw counts CSV (HQC, n_2q, capped shots, T).
3. Application rows are sums of circuit rows; 'all' covers every circuit once.
4. Family C bench: 10 to 20 circuits, 20 to 56 qubits, every circuit compiled by P0 and P2.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def job_cost(s, h):
    k = (h - 5) * 5
    return 5 * int(np.ceil(s / 10_000)) + s * k / 5000


def shots_capped_ref(h, budget=10_000):
    """Largest s with 5 ceil(s / 10,000) + s k / 5000 <= budget, by bisection."""
    lo, hi = 0, 10 ** 7
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if job_cost(mid, h) <= budget + 1e-9:
            lo = mid
        else:
            hi = mid - 1
    return lo


@pytest.fixture(scope="module")
def out():
    subprocess.run([sys.executable, str(ROOT / "value/family_C_selector.py")], check=True,
                   capture_output=True)
    return (pd.read_csv(ROOT / "value/family_C_selector.csv"),
            pd.read_csv(ROOT / "value/family_C_selector_apps.csv"),
            pd.read_csv(ROOT / "results/family_C_counts.csv"),
            pd.read_csv(ROOT / "bench/family_C/manifest.csv"))


def test_bench_scope(out):
    r, _, c, man = out
    assert 10 <= len(man) <= 20
    assert man.n_qubits.min() >= 20 and man.n_qubits.max() <= 56
    assert len(c) == 2 * len(man)
    assert c.status.str.startswith("ok").all()
    assert set(r.file) == set(man.file)


def test_selector_min(out):
    r, _, _, _ = out
    m = np.minimum(r.hqc_P0, r.hqc_P2)
    assert np.allclose(r.hqc_PSEL, m)
    assert (np.isclose(r.hqc_PSEL, r.hqc_P0) | np.isclose(r.hqc_PSEL, r.hqc_P2)).all()
    assert (r.saved_hqc >= -1e-9).all()
    tie = r.hqc_P0.round(6) == r.hqc_P2.round(6)
    exp = np.where(r[tie].n2q_P2 < r[tie].n2q_P0, "P2", "P0")
    assert (r[tie].pick.values == exp).all()


def test_recompute_from_counts(out):
    r, _, c, man = out
    shots = 1000
    for _, row in r.iterrows():
        sel = c[(c.file == row.file) & (c.pipeline == row.pick)].iloc[0]
        p0 = c[(c.file == row.file) & (c.pipeline == "P0")].iloc[0]
        p2 = c[(c.file == row.file) & (c.pipeline == "P2")].iloc[0]
        n = sel.n_qubits
        # compile.hqc with n_measure = n_qubits
        h = 5 + (sel.n_phasedx + 10 * sel.n_2q + 5 * (n + n)) * shots / 5000
        assert np.isclose(h, row.hqc_PSEL)
        assert sel.n_2q == sel.n_zzphase + sel.n_zzmax == row.n2q_PSEL
        assert row.d_n2q == row.n2q_PSEL - p0.n_2q
        assert np.isclose(row.saved_pct, 100 * (p0.hqc - sel.hqc) / p0.hqc)
        # capped shots: at most 10,000 per job, 5 HQC per job, budget 10,000 HQC
        assert row.shots_P0 == shots_capped_ref(p0.hqc)
        assert row.shots_PSEL == shots_capped_ref(sel.hqc)
        assert row.extra_shots == row.shots_PSEL - row.shots_P0
        tw = man.set_index("file").loc[row.file, "t_count_as_written"]
        assert row.t_saved_PSEL == ((tw - p2.t_count_zx) if row.pick == "P2" else 0)


def test_application_sums(out):
    r, s, _, _ = out
    for _, a in s[s.application != "all"].iterrows():
        g = r[r.application == a.application]
        assert a.n_circuits == len(g)
        for col in ["hqc_P0", "hqc_P2", "hqc_PSEL", "saved_hqc",
                    "t_saved_PSEL", "d_n2q"]:
            assert np.isclose(a[col], g[col].sum()), col
        assert a.p2_picks == (g.pick == "P2").sum()
    tot = s[s.application == "all"].iloc[0]
    assert tot.n_circuits == len(r)
    assert np.isclose(tot.hqc_PSEL, s[s.application != "all"].hqc_PSEL.sum())
    assert np.isclose(tot.saved_pct, 100 * tot.saved_hqc / tot.hqc_P0)
    assert "extra_shots" not in s.columns  # shots are per circuit only


def test_capped_shots_values(out):
    r, _, _, _ = out
    exp = {"modadd_2n_10.qasm": (26056, 1180), "cdkm_adder_10.qasm": (27236, 3116),
           "vbe_adder_7.qasm": (27326, 7159), "mcx_dirty_28.qasm": (17047, 59)}
    for f, (s0, ex) in exp.items():
        row = r.set_index("file").loc[f]
        assert (row.shots_P0, row.extra_shots) == (s0, ex)
