"""Offline tests for the family C H2-2E run (vbe_adder_7, P0 and P2, submit/h22e_famC.py).

Reloads the stored payloads and recomputes every number without network.

    python3 -m pytest submit/test_famC_h22e.py -q
"""

import glob
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import h22e_famC as fc  # noqa: E402
import h22e_pooled as hp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
N_Q = 22


@pytest.fixture(scope="module")
def ref():
    return common.written_probs("C", fc.FILE)


@pytest.fixture(scope="module")
def res(ref):
    return fc.compute(ref=ref)


def _payloads():
    return {p: json.load(open(ROOT / "results" / "emulator" / "nexus_H2-2E_famC" / p / "vbe_adder_7.json"))
            for p in fc.PIPELINES}


def test_reference_is_all_zero(ref):
    # VBE adder on |0..0>: 0 + 0 = 0, every register stays zero
    assert ref.shape == (2 ** N_Q,)
    assert abs(ref[0] - 1.0) < 1e-12 and abs(ref.sum() - 1.0) < 1e-12
    assert int((ref > 1e-12).sum()) == 1


def test_compiled_ideal_equals_reference(res):
    # run_emulator.score stores max |ideal(compiled) - reference| in the CSV
    assert (res["rows"].ideal_vs_ref_maxdiff < 1e-9).all()


def test_payloads_and_ledger():
    pay = _payloads()
    ids = {p: d["job_id"] for p, d in pay.items()}
    assert len(set(ids.values())) == 2
    led = pd.read_csv(ROOT / "results" / "emulator_jobs.csv")
    led = led[(led.platform == "nexus:H2-2E") & (led.family == "C") & (led.file == fc.FILE)]
    assert len(led) == 2 and set(led.job_id) == set(ids.values())
    assert (led.status == "COMPLETED").all()
    for p, d in pay.items():
        assert d["platform"] == "nexus:H2-2E" and d["shots"] == 1000
        assert d["options"] == {"noisy_simulation": True}
        assert sum(d["counts"].values()) == 1000 and not d.get("error")
        assert all(len(k.replace(" ", "")) == N_Q for k in d["counts"])


def test_fh_and_difference_by_hand(res):
    # single-outcome reference |0^22>: F_H = n(0^22) / N, sd = sqrt(F (1 - F) / N)
    pay = _payloads()
    f, sd = {}, {}
    for p, d in pay.items():
        n0 = sum(v for k, v in d["counts"].items() if set(k.replace(" ", "")) == {"0"})
        f[p] = n0 / d["shots"]
        sd[p] = math.sqrt(f[p] * (1 - f[p]) / d["shots"])
        row = res["rows"][res["rows"].pipeline == p].iloc[0]
        assert row.F_H == pytest.approx(f[p], abs=1e-12)
        assert row.F_H_csv == pytest.approx(f[p], abs=1e-12)
        assert row.F_H_json == pytest.approx(f[p], abs=1e-12)
        assert row.sd == pytest.approx(sd[p], abs=1e-12) and row.sd_method == "binomial"
    dF = f["P2"] - f["P0"]
    s = math.hypot(sd["P0"], sd["P2"])
    assert res["dF"] == pytest.approx(dF, abs=1e-12)
    assert res["sd_diff"] == pytest.approx(s, abs=1e-12)
    assert res["z"] == pytest.approx(dF / s, abs=1e-9)


def _counts(qasm: str):
    n1 = len(re.findall(r"^\s*U1q\(", qasm, re.M))
    n2 = len(re.findall(r"^\s*(RZZ\(|ZZ\s)", qasm, re.M))
    nm = len(re.findall(r"^\s*measure\b", qasm, re.M))
    nq = sum(int(x) for x in re.findall(r"^\s*qreg\s+\w+\[(\d+)\]", qasm, re.M))
    return n1, n2, nm, nq


def test_n2q_and_hqc_by_hand(res):
    fam = pd.read_csv(ROOT / "results" / "family_C_counts.csv")
    pay = _payloads()
    for p in fc.PIPELINES:
        qasm = (ROOT / "results" / "compiled" / p / fc.FILE).read_text()
        n1, n2, nm, nq = _counts(qasm)
        hand = 5 + (n1 + 10 * n2 + 5 * (nq + nm)) * 1000 / 5000
        c = fam[(fam.file == fc.FILE) & (fam.pipeline == p)].iloc[0]
        row = res["rows"][res["rows"].pipeline == p].iloc[0]
        assert nq == N_Q and n2 == int(c.n_2q) == row.n_2q
        assert hand == pytest.approx(float(c.hqc), abs=1e-9)
        assert hand == pytest.approx(pay[p]["hqc_estimate"], abs=1e-9)
    assert (res["rows"].n_2q.tolist()) == [142, 107]
    assert round(res["hqc_total"], 1) == 664.8


def test_famC_outside_table_e3_glob():
    # Table E3 and value/finals_plan.py read only nexus_H2-2E and nexus_H2-2E_r*
    assert not any("famC" in p for p in hp.all_h22e_jsons())
    assert glob.glob(os.path.join(hp.EMU, "nexus_H2-2E_famC", "*", "*.json"))
