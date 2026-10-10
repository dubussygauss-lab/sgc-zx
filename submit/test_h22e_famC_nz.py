"""Offline tests for the H2-2E non-zero-input run of vbe_adder_7 (P0 vs L3, submit/h22e_famC_nz.py).

Reloads the stored payloads, the compiled circuits and the input-prepared bench
file and recomputes every number without network.

    python3 -m pytest submit/test_h22e_famC_nz.py -q
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
import h22e_famC_nz as nz  # noqa: E402
import h22e_pooled as hp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def res():
    return nz.compute()


def _payloads():
    return {p: json.load(open(ROOT / "results" / "emulator" / "nexus_H2-2E_famC_nz" / p / "vbe_adder_7_nz.json"))
            for p in nz.PIPELINES}


def test_input_preparation_matches_prereg():
    rng = np.random.default_rng(20261010)
    a, b = (int(x) for x in rng.integers(1, 2 ** 7, size=2))
    assert (a, b) == (nz.A, nz.B) == (28, 111)
    src = (ROOT / "bench" / "family_C" / "vbe_adder_7.qasm").read_text().splitlines()
    prep = (ROOT / "bench" / "family_C_nz" / "vbe_adder_7_nz.qasm").read_text().splitlines()
    xs = [ln for ln in prep if ln.startswith("x ")]
    want = sorted([1 + i for i in range(7) if (a >> i) & 1] + [8 + i for i in range(7) if (b >> i) & 1])
    assert xs == ["x q[%d];" % q for q in want]
    assert [ln for ln in prep if not ln.startswith("x ")] == src
    assert nz.expected_bits(a, b) == nz.EXPECTED
    s = a + b
    e = nz.EXPECTED
    assert int(e[1:8][::-1], 2) == a and int(e[8:15][::-1], 2) == s % 128 and int(e[15]) == s >> 7
    assert e[0] == "0" and e[16:] == "000000"


def test_compiled_ideal_is_expected():
    import common
    for p in nz.PIPELINES:
        pr = common.exact_probs(p, nz.FILE)
        assert int((pr > 1e-9).sum()) == 1
        assert pr[int(nz.EXPECTED, 2)] == pytest.approx(1.0, abs=1e-9)
        assert not common.native_violations(common.load_compiled(p, nz.FILE))


def test_payloads_and_ledger():
    pay = _payloads()
    ids = {p: d["job_id"] for p, d in pay.items()}
    assert len(set(ids.values())) == 2
    led = pd.read_csv(ROOT / "results" / "emulator_jobs.csv")
    led = led[led.file == nz.FILE]
    assert len(led) == 2 and set(led.job_id) == set(ids.values())
    assert (led.status == "COMPLETED").all() and (led.platform == "nexus:H2-2E").all()
    for p, d in pay.items():
        assert d["platform"] == "nexus:H2-2E" and d["shots"] == 1000
        assert d["options"] == {"noisy_simulation": True}
        assert sum(d["counts"].values()) == 1000 and not d.get("error")


def test_success_probability_by_hand(res):
    pay = _payloads()
    p, sd = {}, {}
    for pipe, d in pay.items():
        k = sum(v for key, v in d["counts"].items() if key.replace(" ", "") == nz.EXPECTED)
        p[pipe] = k / 1000
        sd[pipe] = math.sqrt(p[pipe] * (1 - p[pipe]) / 1000)
        row = res["rows"][res["rows"].pipeline == pipe].iloc[0]
        assert row.p_success == pytest.approx(p[pipe], abs=1e-12)
        assert row.sd == pytest.approx(sd[pipe], abs=1e-12)
        # single-outcome ideal: Hellinger fidelity stored by the runner = p_success
        assert row.F_H_payload == pytest.approx(p[pipe], abs=1e-12)
        assert row.F_H_csv == pytest.approx(p[pipe], abs=1e-12)
    d = p["L3"] - p["P0"]
    s = math.hypot(sd["P0"], sd["L3"])
    assert res["d"] == pytest.approx(d, abs=1e-12)
    assert res["sd_diff"] == pytest.approx(s, abs=1e-12)
    assert res["z"] == pytest.approx(d / s, abs=1e-9)


def test_n2q_and_hqc(res):
    t = res["rows"]
    assert t.n_2q.tolist() == [142, 79]
    assert t.hqc.round(1).tolist() == [372.2, 232.2]
    assert round(res["hqc_total"], 1) == 604.4 < 700


def test_outside_table_e3_glob():
    assert not any("famC" in p for p in hp.all_h22e_jsons())
    assert glob.glob(os.path.join(hp.EMU, "nexus_H2-2E_famC_nz", "*", "*.json"))
