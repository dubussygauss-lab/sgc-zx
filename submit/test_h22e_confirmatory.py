"""Offline tests for submit/h22e_confirmatory.py (H2-2E repeats r2-r4 alone).

Recomputes every number of results/h22e_confirmatory.md from the stored payloads.

    python3 -m pytest submit/test_h22e_confirmatory.py -q
"""

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import h22e_confirmatory as hc  # noqa: E402
import h22e_pooled as hp  # noqa: E402

ROOT = Path(hc.ROOT)
MD = ROOT / "results" / "h22e_confirmatory.md"


@pytest.fixture(scope="module")
def res():
    return hc.compute()


def _summed(file, pipeline, runs=("r2", "r3", "r4")):
    """Summed counts of the repeat payloads, read independently of h22e_confirmatory."""
    summed, jobs = {}, []
    for r in runs:
        p = ROOT / "results" / "emulator" / ("nexus_H2-2E_" + r) / pipeline / (file[:-5] + ".json")
        x = json.load(open(p))
        assert x.get("counts") and not x.get("error") and sum(x["counts"].values()) == 1000
        jobs.append(x["job_id"])
        for k, v in x["counts"].items():
            summed[k] = summed.get(k, 0) + v
    return summed, jobs


def test_only_repeats_used(res):
    r1 = set()
    for pipe in ("P0", "P2"):
        for f in hc.FILES:
            r1.add(json.load(open(ROOT / "results/emulator/nexus_H2-2E" / pipe / (f[:-5] + ".json")))["job_id"])
    for c in res["cells"].itertuples():
        jobs = c.job_ids.split()
        assert len(jobs) == 3 and not (set(jobs) & r1)
        assert jobs == _summed(c.file, c.pipeline)[1]
        assert c.shots == 3000


def test_fh_and_sd(res):
    for c in res["cells"].itertuples():
        summed, _ = _summed(c.file, c.pipeline)
        ref = common.reference_probs("B1", c.file)
        n = int(np.log2(len(ref)))
        emp = common.counts_to_probs(summed, n)
        F = common.hellinger_fidelity(ref, emp)
        assert F == pytest.approx(c.F_H, abs=1e-12)
        if (ref > 1e-12).sum() == 1:
            assert c.sd_method == "binomial"
            assert c.sd == pytest.approx(math.sqrt(F * (1 - F) / 3000), abs=1e-15)
        else:
            assert c.sd_method == "bootstrap"
            rng = np.random.default_rng(20261008)
            b = rng.multinomial(3000, emp, size=4000) / 3000
            sd = (np.sum(np.sqrt(b * ref[None, :]), axis=1) ** 2).std(ddof=1)
            assert c.sd == pytest.approx(sd, rel=1e-9)


def test_pairs(res):
    c = res["cells"]
    for p in res["pairs"].itertuples():
        a0 = c[(c.file == p.file) & (c.pipeline == "P0")].iloc[0]
        a2 = c[(c.file == p.file) & (c.pipeline == "P2")].iloc[0]
        assert p.dF == pytest.approx(a2.F_H - a0.F_H, abs=1e-15)
        assert p.sd == pytest.approx(math.hypot(a0.sd, a2.sd), rel=1e-12)
        assert p.p == pytest.approx(2 * stats.norm.sf(abs(p.z)), rel=1e-9)
        assert p.p_one == pytest.approx(stats.norm.sf(p.z), rel=1e-9)
        assert p.dN_2q == a0.n_2q - a2.n_2q
        assert p.dF_pred == pytest.approx(a0.F_H * (math.exp(1.1801e-3 * p.dN_2q) - 1), rel=1e-12)
    lo, hi = sorted(res["pairs"].p)
    for p in res["pairs"].itertuples():
        exp = min(1, 2 * lo) if p.p == lo else max(min(1, 2 * lo), hi)
        assert p.p_holm == pytest.approx(exp, abs=1e-15)


def test_agrees_with_pooled_code_restricted_to_r2_r4(res, monkeypatch):
    """h22e_pooled.compute() with RUNS = r2-r4 gives the same cells and pairs."""
    monkeypatch.setattr(hp, "RUNS", ["r2", "r3", "r4"])
    monkeypatch.setattr(hp, "EXPECTED_RUNS", 3)
    r = hp.compute()
    for c in res["cells"].itertuples():
        x = r["cells"][(r["cells"].file == c.file) & (r["cells"].pipeline == c.pipeline)].iloc[0]
        assert x.runs == 3 and x.shots == c.shots
        assert x.F_H == pytest.approx(c.F_H, abs=1e-15) and x.sd == pytest.approx(c.sd, abs=1e-15)
    for p in res["pairs"].itertuples():
        x = r["pairs"][r["pairs"].file == p.file].iloc[0]
        for k in ("dF", "sd", "z", "p", "dF_pred", "z_vs_pred", "p_holm"):
            assert getattr(x, k) == pytest.approx(getattr(p, k), abs=1e-15), k


def test_pooled_r1_r4_values_quoted_in_md():
    r = hp.compute()
    v = {p.file: p for p in r["pairs"].itertuples()}
    text = MD.read_text()
    for f, short in (("vbe_adder_3.qasm", "vbe_adder_3"), ("grover_5.qasm", "grover_5")):
        p = v[f]
        row = "| %s | pooled r1 to r4 | 4000 | %+.4f | %.4f | %+.2f | %s | %s |" % (
            short, p.dF, p.sd, p.z, hp._p(p.p) if p.p < 0.1 else "%.2f" % p.p,
            "%.3f" % p.p_holm if p.p_holm < 0.1 else "%.2f" % p.p_holm)
        assert row in text, row


def test_support_and_input(res):
    info = res["info"].set_index("file")
    assert info.loc["vbe_adder_3.qasm", "support"] == 1
    assert info.loc["vbe_adder_3.qasm", "ideal_bitstring"] == "0" * 10
    assert info.loc["hwb6.qasm", "support"] == 1
    assert info.loc["hwb6.qasm", "ideal_bitstring"] == "0" * 7
    q = common.reference_probs("B1", "grover_5.qasm")
    s = q[q > 1e-12]
    assert len(q) == 512 and len(s) == 64 and np.allclose(s, 1 / 64, atol=1e-12)
    assert info.loc["grover_5.qasm", "support"] == 64
    for f in info.index:
        assert info.loc[f, "n_resets"] == 0 and "all-zero" in info.loc[f, "input"]


def test_repeats_submitted_after_prediction_commit(res):
    w = res["window"]
    assert w["n_jobs"] == 12
    first = pd.Timestamp(w["first_submit_utc"])
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "show", "-s", "--format=%cI", "eb0465f"],
                             capture_output=True, text=True, check=True).stdout.strip()
        body = subprocess.run(["git", "-C", str(ROOT), "show", "eb0465f:report/report_v5.md"],
                              capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git history not available")
    assert "predicted gains of 0.0170, 0.0055 and 0.0228" in body
    assert pd.Timestamp(out).tz_convert("UTC") < first


def test_md_table(res):
    text = MD.read_text()
    for c in res["cells"].itertuples():
        row = "| %s | %s | r2, r3, r4 | %d | %d | %.4f | %.4f | %s |" % (
            c.file[:-5], c.pipeline, c.shots, c.n_2q, c.F_H, c.sd, c.sd_method)
        assert row in text, row
    for p in res["pairs"].itertuples():
        fp = lambda x: "%.3f" % x if x < 0.1 else "%.2f" % x  # noqa: E731
        p1 = "%.4f" % p.p_one if p.p_one < 0.01 else fp(p.p_one)
        row = "| %s | %d | %+.4f | %.4f | %+.2f | %s | %s | %s | %s | %.4f | %+.2f |" % (
            p.file[:-5], p.dN_2q, p.dF, p.sd, p.z, fp(p.p), fp(p.p_holm), p1, fp(p.p_one_holm),
            p.dF_pred, p.z_vs_pred)
        assert row in text, row


def test_csv_written(res, tmp_path):
    df = hc.to_csv(res, path=str(tmp_path / "c.csv"))
    on_disk = pd.read_csv(ROOT / "results" / "h22e_confirmatory.csv", dtype={"ideal_bitstring": str})
    assert len(df) == 4 and len(on_disk) == 4
    assert np.allclose(df.F_H, on_disk.F_H, atol=1e-9) and np.allclose(df.z, on_disk.z, atol=1e-9)


def test_snippet_numbers_have_a_source():
    """Every decimal number in the snippet appears in the md, in report_v5.md or in the slide source."""
    snip = (ROOT / "report" / "snippets" / "confirmatory_snippet.md").read_text()
    pool = MD.read_text() + (ROOT / "report" / "report_v5.md").read_text() \
        + (ROOT / "report" / "presentation" / "presentation.tex").read_text()
    for x in set(re.findall(r"(?<![\w.])[+-]?\d+\.\d+", snip)):
        assert x.lstrip("+") in pool, x
    assert ";" not in re.sub(r"`[^`]*`", "", snip.split("## Notes")[0])
    assert "—" not in snip and "rather than" not in snip
