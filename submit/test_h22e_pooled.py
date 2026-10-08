"""Offline tests for submit/h22e_pooled.py (Table E3, Section 3.7.1).

    python3 -m pytest submit/test_h22e_pooled.py -q
"""

import glob
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import h22e_pooled as hp  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return hp.compute()


def _payloads(file, pipeline):
    """Completed payloads of one cell, found independently of h22e_pooled."""
    out = []
    for d in [os.path.join(hp.EMU, "nexus_H2-2E")] + sorted(glob.glob(os.path.join(hp.EMU, "nexus_H2-2E_r*"))):
        p = os.path.join(d, pipeline, file[:-5] + ".json")
        if os.path.exists(p):
            x = json.load(open(p))
            if x.get("counts") and not x.get("error"):
                out.append(x)
    return out


def test_run_counts(res):
    for c in res["cells"].itertuples():
        assert c.runs == len(_payloads(c.file, c.pipeline))
        assert c.shots == 1000 * c.runs
    assert res["final"] == all(c.runs == 4 for c in res["cells"].itertuples())


def test_pooled_fh_is_fh_of_summed_counts(res):
    for c in res["cells"].itertuples():
        summed = {}
        for x in _payloads(c.file, c.pipeline):
            for k, v in x["counts"].items():
                summed[k] = summed.get(k, 0) + v
        ref = common.reference_probs("B1", c.file)
        emp = common.counts_to_probs(summed, int(np.log2(len(ref))))
        assert common.hellinger_fidelity(ref, emp) == pytest.approx(c.F_H, abs=1e-12)
        # sqrt(F_H) = sum sqrt(p q) is concave in p, so the pooled value is at least the
        # shot-weighted mean of the per-run sqrt(F_H).  It may exceed every single run.
        pr = res["per_run"]
        f = pr[(pr.file == c.file) & (pr.pipeline == c.pipeline)]
        assert math.sqrt(c.F_H) >= np.average(np.sqrt(f.F_H), weights=f.shots) - 1e-12


def test_per_run_fh_matches_payloads(res):
    for r in res["per_run"].itertuples():
        x = [p for p in _payloads(r.file, r.pipeline) if p["job_id"] == r.job_id]
        assert len(x) == 1 and abs(x[0]["F_H"] - r.F_H) < 1e-9


def test_sd_rule(res):
    c = res["cells"]
    v = c[c.file == "vbe_adder_3.qasm"]
    assert (v.sd_method == "binomial").all()
    assert np.allclose(v.sd, np.sqrt(v.F_H * (1 - v.F_H) / v.shots), rtol=0, atol=1e-15)
    assert (c[c.file == "grover_5.qasm"].sd_method == "bootstrap").all()


def test_pairs(res):
    c = res["cells"]
    for p in res["pairs"].itertuples():
        a0 = c[(c.file == p.file) & (c.pipeline == "P0")].iloc[0]
        a2 = c[(c.file == p.file) & (c.pipeline == "P2")].iloc[0]
        assert p.dF == pytest.approx(a2.F_H - a0.F_H, abs=1e-15)
        assert p.sd == pytest.approx(math.hypot(a0.sd, a2.sd), rel=1e-12)
        assert p.p == pytest.approx(2 * (1 - 0.5 * (1 + math.erf(abs(p.z) / math.sqrt(2)))), abs=1e-12)
        assert p.dF_pred == pytest.approx(a0.F_H * (math.exp(hp.SLOPE * (a0.n_2q - a2.n_2q)) - 1), rel=1e-12)


def test_hqc_sum(res):
    done = sub = 0.0
    for p in glob.glob(os.path.join(hp.EMU, "nexus_H2-2E*", "P*", "*.json")):
        x = json.load(open(p))
        sub += x["hqc_estimate"]
        if x.get("counts") and not x.get("error"):
            done += x["hqc_estimate"]
    assert res["hqc_completed"] == pytest.approx(done, abs=1e-9)
    assert res["hqc_submitted"] == pytest.approx(sub, abs=1e-9)
    assert res["hqc_pct"] == pytest.approx(100 * done / 10000, abs=1e-12)


def test_original_run_matches_table_e2(res):
    import h22e_stats
    e2 = h22e_stats.compute()["rows"]
    pr = res["per_run"]
    for r in pr[pr.run == "r1"].itertuples():
        x = e2[(e2.file == r.file) & (e2.pipeline == r.pipeline)].iloc[0]
        assert r.job_id == x.job_id and abs(r.F_H - x.F_H) < 1e-12


def test_prose_fill(res, tmp_path):
    out = tmp_path / "filled.md"
    text = hp.fill_prose(res, out=str(out))
    assert not re.search(r"\{[A-Za-z0-9_]+\}", text)
    body = [b for b in text.split("\n\n") if b.strip() and not b.startswith("<!--")]
    for b in body:
        assert b.startswith("`[F]`") or b.startswith("`[O]`"), b[:40]
    assert ";" not in text and "—" not in text and "rather than" not in text
    assert ("PARTIAL" in text) != res["final"]


def test_holm(res):
    p = res["pairs"].p.values
    lo, hi = sorted(p)
    expect = {lo: min(1, 2 * lo), hi: max(min(1, 2 * lo), hi)}
    for x in res["pairs"].itertuples():
        assert x.p_holm == pytest.approx(expect[x.p], abs=1e-15)


def test_holm_three_circuits(res):
    """Holm over vbe_adder_3 and grover_5 (pooled) and hwb6 (single run, Table E2)."""
    import h22e_stats
    hw = h22e_stats.compute()["pairs"]
    z = float(hw[hw.file == "hwb6.qasm"].z.iloc[0])
    p = dict(zip(res["pairs"].file, res["pairs"].p))
    p["hwb6.qasm"] = math.erfc(abs(z) / math.sqrt(2))
    order = sorted(p, key=p.get)
    adj, run = {}, 0.0
    for i, f in enumerate(order):
        run = max(run, min(1.0, (3 - i) * p[f]))
        adj[f] = run
    fam = res["family3"]
    assert len(fam) == 3
    for x in fam.itertuples():
        assert x.p_holm3 == pytest.approx(adj[x.file], abs=1e-15)
    for x in res["pairs"].itertuples():
        assert x.p_holm3 == pytest.approx(adj[x.file], abs=1e-15)
