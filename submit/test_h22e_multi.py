"""Offline tests for the H2-2E run of cdkm_adder_10 (P0 vs L3) and modadd_2n_10 (P0 vs P2L3) on three
non-zero inputs each (submit/h22e_multi.py, runner submit/h22e_multi_run.py).

Reloads the stored payloads, the compiled circuits and the input-prepared bench
files and recomputes every number without network.

    python3 -m pytest submit/test_h22e_multi.py -q
"""

import glob
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h22e_multi as hm  # noqa: E402
import h22e_multi_run as R  # noqa: E402
import h22e_pooled as hp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results" / "emulator" / "nexus_H2-2E_famC_multi"


@pytest.fixture(scope="module")
def res():
    return hm.compute()


def test_inputs_match_prereg():
    rng = np.random.default_rng(20261011)
    cdkm = [tuple(int(x) for x in r) for r in rng.integers(1, 2 ** 10, size=(3, 2))]
    mod = [tuple(int(x) for x in r) for r in rng.integers(1, 2 ** 10, size=(3, 2))]
    assert cdkm == R.INPUTS["cdkm_adder_10"] == [(692, 435), (502, 24), (710, 328)]
    assert mod == R.INPUTS["modadd_2n_10"] == [(396, 743), (460, 452), (335, 130)]
    pre = (ROOT / "results" / "h22e_multi_prereg.md").read_text()
    for c, k, a, b, f in R.programs():
        assert "| `%s` | %d | %d |" % (f, a, b) in pre
        assert "`%s` |" % R.expected_bits(c, a, b) in pre


def test_input_files():
    for c, k, a, b, f in R.programs():
        src = (ROOT / "bench" / "family_C" / (c + ".qasm")).read_text().splitlines()
        prep = (ROOT / "bench" / "family_C_multi" / f).read_text().splitlines()
        xs = [ln for ln in prep if ln.startswith("x ")]
        oa, ob = R.CIRCUITS[c][2], R.CIRCUITS[c][3]
        want = sorted([oa + i for i in range(10) if (a >> i) & 1] + [ob + i for i in range(10) if (b >> i) & 1])
        assert xs == ["x q[%d];" % q for q in want]
        assert [ln for ln in prep if not ln.startswith("x ")] == src


def test_expected_by_arithmetic():
    for c, k, a, b, f in R.programs():
        e = R.expected_bits(c, a, b)
        s = a + b
        if c == "cdkm_adder_10":
            assert len(e) == 22 and e[0] == "0"
            assert int(e[1:11][::-1], 2) == a and int(e[11:21][::-1], 2) == s % 1024 and int(e[21]) == s >> 10
        else:
            assert len(e) == 20
            assert int(e[0:10][::-1], 2) == a and int(e[10:20][::-1], 2) == s % 1024


def test_compiled_files_are_the_checked_ones():
    ok = json.loads(R.CHECKED.read_text())
    assert len(ok) == 12
    for c, _, _, _, f in R.programs():
        for pipe in R.pipelines(c):
            assert ok["%s/%s" % (pipe, f)] == R._sha(pipe, f)


def test_one_compiled_ideal_output():
    # full ideal-output check of all 12 is in h22e_multi_run.py --check (about a minute each);
    # here one permuted (P2L3) circuit is re-simulated.
    import common
    c, k, a, b, f = R.programs()[3]
    pr = common.exact_probs("P2L3", f)
    assert int((pr > 1e-9).sum()) == 1
    assert pr[int(R.expected_bits(c, a, b), 2)] == pytest.approx(1.0, abs=1e-9)


def test_payloads_and_ledger(res):
    t = res["rows"]
    assert len(t) == 12 and t.job_id.nunique() == 12
    led = pd.read_csv(ROOT / "results" / "emulator_jobs.csv")
    led = led[led.file.isin([f for *_, f in R.programs()])]
    assert len(led) == 12 and set(led.job_id) == set(t.job_id)
    assert (led.status == "COMPLETED").all() and (led.platform == "nexus:H2-2E").all()
    assert (led.shots == 400).all()


def test_success_by_hand(res):
    k = {}
    for c, i, a, b, f in R.programs():
        e = R.expected_bits(c, a, b)
        for pipe in R.pipelines(c):
            d = json.load(open(RUN / pipe / (f[:-5] + ".json")))
            assert sum(d["counts"].values()) == 400
            k[(c, i, pipe)] = sum(v for key, v in d["counts"].items() if key.replace(" ", "") == e)
            row = res["rows"][(res["rows"].file == f) & (res["rows"].pipeline == pipe)].iloc[0]
            assert row.k_success == k[(c, i, pipe)]
            assert row.F_H_payload == pytest.approx(k[(c, i, pipe)] / 400, abs=1e-12)
            assert row.F_H_csv == pytest.approx(k[(c, i, pipe)] / 400, abs=1e-12)

    def chk(v, k1, k0, n):
        p1, p0 = k1 / n, k0 / n
        sd = math.sqrt(p1 * (1 - p1) / n + p0 * (1 - p0) / n)
        assert v["d"] == pytest.approx(p1 - p0, abs=1e-12)
        assert v["sd"] == pytest.approx(sd, abs=1e-12)
        assert v["z"] == pytest.approx((p1 - p0) / sd, abs=1e-9)

    tot1 = tot0 = 0
    for c in R.ORDER:
        pick = R.CIRCUITS[c][1]
        k1 = sum(k[(c, i, pick)] for i in (1, 2, 3))
        k0 = sum(k[(c, i, "P0")] for i in (1, 2, 3))
        chk(res["primary"][c], k1, k0, 1200)
        tot1, tot0 = tot1 + k1, tot0 + k0
        for i in (1, 2, 3):
            v = res["per_input"][(res["per_input"].circuit == c) & (res["per_input"].input == i)].iloc[0]
            chk(v, k[(c, i, pick)], k[(c, i, "P0")], 400)
    chk(res["both"], tot1, tot0, 2400)


def test_hqc(res):
    t = res["rows"]
    assert (t.hqc == t.apply(lambda r: hm.hqc_from_counts(hm.qasm_counts(r.pipeline, r.file), 400), axis=1)).all()
    assert res["hqc_total"] < 1900


def test_outside_table_e3_glob():
    assert not any("famC" in p for p in hp.all_h22e_jsons())
    assert glob.glob(os.path.join(hp.EMU, "nexus_H2-2E_famC_multi", "*", "*.json"))
