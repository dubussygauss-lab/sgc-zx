"""Offline tests for submit/h22e_stats.py (Table E2, Section 3.7.1).

    python3 -m pytest submit/test_h22e_stats.py -q
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import h22e_stats  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return h22e_stats.compute()


def test_six_rows_complete(res):
    t = res["rows"]
    assert len(t) == 6
    assert sorted(zip(t.file, t.pipeline)) == sorted(
        (f, p) for f in h22e_stats.FILES for p in h22e_stats.PIPELINES)
    assert (t.shots == 1000).all()


def test_fh_recomputed_from_counts(res):
    assert res["max_abs_dF_csv"] < 1e-9
    assert res["max_abs_dF_json"] < 1e-9


def test_fh_matches_common_helpers(res):
    """Independent route through submit/common.py (counts_to_probs, reference_probs)."""
    for r in res["rows"].itertuples():
        with open(os.path.join(h22e_stats.PLATFORM_DIR, r.pipeline, r.file[:-5] + ".json")) as f:
            d = json.load(f)
        ref = common.reference_probs("B1", r.file)
        emp = common.counts_to_probs(d["counts"], int(np.log2(len(ref))))
        assert common.hellinger_fidelity(ref, emp) == pytest.approx(r.F_H, abs=1e-12)


def test_sd_rule(res):
    t = res["rows"]
    one = t[t.support == 1]
    assert set(one.file) == {"vbe_adder_3.qasm", "hwb6.qasm"}
    assert (one.sd_method == "binomial").all()
    assert np.allclose(one.sd, np.sqrt(one.F_H * (1 - one.F_H) / one.shots), rtol=0, atol=1e-15)
    g = t[t.file == "grover_5.qasm"]
    assert (g.support == 64).all() and (g.sd_method == "bootstrap").all()


def test_hqc_total(res):
    total = 0.0
    for f in h22e_stats.FILES:
        for p in h22e_stats.PIPELINES:
            total += h22e_stats.load_payload(p, f)["hqc_estimate"]
    assert total == pytest.approx(1840.0, abs=1e-9)
    assert res["hqc_total"] == pytest.approx(1840.0, abs=1e-9)
    assert res["quota_frac"] == pytest.approx(0.184, abs=1e-12)


def test_slope_and_pairs(res):
    assert res["slope"] == pytest.approx(1.1801e-3, abs=5e-8)
    p = res["pairs"].set_index("file")
    assert list(p.dN_2q.loc[h22e_stats.FILES]) == [15, 5, 22]
    assert np.allclose(p.ratio_pred, np.exp(res["slope"] * p.dN_2q))
    assert np.allclose(p.z, p.dF / p.sd_diff)
    # shots_2sd is the smallest shot count at which 2 sd <= predicted gain
    for r in p.itertuples():
        sd_at = lambda n: r.sd_diff * np.sqrt(1000 / n)  # noqa: E731
        assert 2 * sd_at(r.shots_2sd) <= r.dF_pred < 2 * sd_at(r.shots_2sd - 1)


def test_cross_uses_table_e1_sd(res):
    """The H2-Emulator sd of the cross-emulator z is the Table E1 bootstrap sd."""
    sd_e1 = h22e_stats.h2emulator_sd()
    for x in res["cross"].itertuples():
        assert x.sd_h2emulator == sd_e1[(x.file, x.pipeline)]
        assert x.z == pytest.approx((x.F_H_h22e - x.F_H_h2emulator) / np.hypot(x.sd_h22e, x.sd_h2emulator))
