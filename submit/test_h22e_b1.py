"""Offline tests for the H2-2E run of vbe_adder_3 (P0 vs L3, 4 inputs) and hwb6 (P0 vs P2L3, 3 inputs) on
non-zero inputs (submit/h22e_b1.py, runner submit/h22e_b1_run.py).

Reloads the stored payloads, the compiled circuits and the input-prepared bench
files and recomputes every number without network.

    python3 -m pytest submit/test_h22e_b1.py -q
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
import h22e_b1 as hb  # noqa: E402
import h22e_b1_run as R  # noqa: E402
import h22e_pooled as hp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results" / "emulator" / "nexus_H2-2E_famB1_multi"
HAVE_PAYLOADS = len(glob.glob(str(RUN / "*" / "*.json"))) == 14


@pytest.fixture(scope="module")
def res():
    if not HAVE_PAYLOADS:
        pytest.skip("payloads of the famB1_multi run not stored")
    return hb.compute()


def test_inputs_match_prereg():
    rng = np.random.default_rng(20261012)
    vbe = [tuple(int(x) for x in r) for r in rng.integers(1, 8, size=(4, 2))]
    hwb = [(int(x),) for x in rng.integers(1, 128, size=3)]
    assert vbe == R.INPUTS["vbe_adder_3"] == [(4, 5), (6, 3), (3, 7), (7, 5)]
    assert hwb == R.INPUTS["hwb6"] == [(126,), (78,), (40,)]
    pre = (ROOT / "results" / "h22e_b1_prereg.md").read_text()
    for c, k, inp, f in R.programs():
        assert "| `%s` | %s |" % (f, " | ".join(map(str, inp))) in pre
        assert "`%s` |" % R.expected_bits(c, inp) in pre


def test_expected_hwb6_fixed():
    assert [R.expected_bits("hwb6", inp) for inp in R.INPUTS["hwb6"]] == ["1001011", "0111111", "0100010"]


def test_submission_order():
    o = [(c, k, pipe) for c, k, _, _, pipe in R.submission_order()]
    assert o == [("vbe_adder_3", 1, "P0"), ("vbe_adder_3", 1, "L3"), ("hwb6", 1, "P0"), ("hwb6", 1, "P2L3"),
                 ("vbe_adder_3", 2, "P0"), ("vbe_adder_3", 2, "L3"), ("hwb6", 2, "P0"), ("hwb6", 2, "P2L3"),
                 ("vbe_adder_3", 3, "P0"), ("vbe_adder_3", 3, "L3"), ("hwb6", 3, "P0"), ("hwb6", 3, "P2L3"),
                 ("vbe_adder_3", 4, "P0"), ("vbe_adder_3", 4, "L3")]


def test_input_files():
    for c, k, inp, f in R.programs():
        src = (ROOT / "bench" / "family_B1" / (c + ".qasm")).read_text().splitlines()
        prep = (ROOT / "bench" / "family_B1_multi" / f).read_text().splitlines()
        i = next(j for j, ln in enumerate(prep) if ln.startswith("qreg "))
        n_x = len(R.x_qubits(c, inp))
        xs = prep[i + 1: i + 1 + n_x]
        if c == "vbe_adder_3":
            a, b = inp
            want = sorted([(1, 4, 7)[j] for j in range(3) if (a >> j) & 1] + [(2, 5, 8)[j] for j in range(3) if (b >> j) & 1])
        else:
            want = [j for j in range(7) if (inp[0] >> j) & 1]
        assert xs == ["x q[%d];" % q for q in want]
        assert prep[: i + 1] + prep[i + 1 + n_x:] == src


def test_expected_by_arithmetic_vbe():
    for c, k, inp, f in R.programs():
        if c != "vbe_adder_3":
            continue
        a, b = inp
        e = R.expected_bits(c, inp)
        s = a + b
        assert len(e) == 10 and e[0] == "0" and e[3] == "0" and e[6] == "0"
        assert int(e[7] + e[4] + e[1], 2) == a
        assert int(e[8] + e[5] + e[2], 2) == s % 8 and int(e[9]) == s >> 3


def test_expected_by_simulation():
    # independent of expected_bits: bench/sv.py on the stored input file
    for c, k, inp, f in R.programs():
        pr = R.sv_probs(f)
        nz = np.flatnonzero(pr > 1e-9)
        assert len(nz) == 1 and format(int(nz[0]), "0%db" % R.CIRCUITS[c][0]) == R.expected_bits(c, inp)


def test_compiled_files_are_the_checked_ones():
    ok = json.loads(R.CHECKED.read_text())
    assert len(ok) == 14
    for c, _, _, f in R.programs():
        for pipe in R.pipelines(c):
            assert ok["%s/%s" % (pipe, f)] == R._sha(pipe, f)


def test_compiled_ideal_output_and_hqc_budget():
    import common
    total = 0.0
    for c, _, inp, f in R.programs():
        for pipe in R.pipelines(c):
            pr = common.exact_probs(pipe, f)
            assert int((pr > 1e-9).sum()) == 1
            assert pr[int(R.expected_bits(c, inp), 2)] == pytest.approx(1.0, abs=1e-9)
            total += common.hqc_estimate(common.load_compiled(pipe, f), 400)
    assert total <= 990


def test_holm():
    h = hb.holm({"a": 0.01, "b": 0.04})
    assert h["a"]["p_holm"] == pytest.approx(0.02) and h["a"]["reject"]
    assert h["b"]["p_holm"] == pytest.approx(0.04) and h["b"]["reject"]
    h = hb.holm({"a": 0.03, "b": 0.5})
    assert h["a"]["p_holm"] == pytest.approx(0.06) and not h["a"]["reject"]
    assert h["b"]["p_holm"] == pytest.approx(0.5) and not h["b"]["reject"]


def test_payloads_and_ledger(res):
    t = res["rows"]
    assert len(t) == 14 and t.job_id.nunique() == 14
    led = pd.read_csv(ROOT / "results" / "emulator_jobs.csv")
    led = led[led.file.isin([f for *_, f in R.programs()])]
    assert len(led) == 14 and set(led.job_id) == set(t.job_id)
    assert (led.status == "COMPLETED").all() and (led.platform == "nexus:H2-2E").all()
    assert (led.shots == 400).all() and (led.family == "B1").all()


def test_success_by_hand(res):
    k = {}
    for c, i, inp, f in R.programs():
        e = R.expected_bits(c, inp)
        for pipe in R.pipelines(c):
            d = json.load(open(RUN / pipe / (f[:-5] + ".json")))
            assert sum(d["counts"].values()) == 400
            k[(c, i, pipe)] = sum(v for key, v in d["counts"].items() if key.replace(" ", "") == e)
            row = res["rows"][(res["rows"].file == f) & (res["rows"].pipeline == pipe)].iloc[0]
            assert row.k_success == k[(c, i, pipe)]
            assert row.F_H_payload == pytest.approx(k[(c, i, pipe)] / 400, abs=1e-12)
            assert row.F_H_csv == pytest.approx(k[(c, i, pipe)] / 400, abs=1e-12)

    pv = {}
    for c in R.ORDER:
        pick, m = R.CIRCUITS[c][1], R.CIRCUITS[c][2]
        k1 = sum(k[(c, i, pick)] for i in range(1, m + 1))
        k0 = sum(k[(c, i, "P0")] for i in range(1, m + 1))
        n = 400 * m
        p1, p0, pp = k1 / n, k0 / n, (k1 + k0) / (2 * n)
        z = (p1 - p0) / math.sqrt(pp * (1 - pp) * 2 / n)
        v = res["primary"][c]
        assert v["N_arm"] == n and v["k_pick"] == k1 and v["k_P0"] == k0
        assert v["z"] == pytest.approx(z, abs=1e-9)
        pv[c] = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
        assert v["p_value"] == pytest.approx(pv[c], abs=1e-12)
        for i in range(1, m + 1):
            w = res["per_input"][(res["per_input"].circuit == c) & (res["per_input"].input == i)].iloc[0]
            q1, q0 = k[(c, i, pick)] / 400, k[(c, i, "P0")] / 400
            assert w["d"] == pytest.approx(q1 - q0, abs=1e-12)
            assert w["sd"] == pytest.approx(math.sqrt(q1 * (1 - q1) / 400 + q0 * (1 - q0) / 400), abs=1e-12)
    lo, hi = sorted(pv, key=pv.get)
    assert res["primary"][lo]["p_holm"] == pytest.approx(min(1.0, 2 * pv[lo]))
    assert res["primary"][hi]["p_holm"] == pytest.approx(max(min(1.0, 2 * pv[lo]), pv[hi]))
    for c in R.ORDER:
        assert res["primary"][c]["reject"] == (res["primary"][c]["p_holm"] <= 0.05)


def test_ratio_by_hand(res):
    t = res["rows"]
    for c in R.ORDER:
        tc = t[t.circuit == c]
        a1, a0 = tc[tc.arm == "pick"], tc[tc.arm == "P0"]
        H1, K1, S1 = a1.hqc.sum(), a1.k_success.sum(), a1.shots.sum()
        H0, K0, S0 = a0.hqc.sum(), a0.k_success.sum(), a0.shots.sum()
        Rv = (H1 / K1) / (H0 / K0)
        p1, p0 = K1 / S1, K0 / S0
        se = math.sqrt((1 - p1) / (S1 * p1) + (1 - p0) / (S0 * p0))
        v = res["ratio"][c]
        assert v["R"] == pytest.approx(Rv, abs=1e-12)
        assert v["R_lo"] == pytest.approx(Rv * math.exp(-1.959963984540054 * se), abs=1e-12)
        assert v["R_hi"] == pytest.approx(Rv * math.exp(1.959963984540054 * se), abs=1e-12)


def test_hqc(res):
    t = res["rows"]
    assert (t.hqc == t.apply(lambda r: hb.hqc_from_counts(hb.qasm_counts(r.pipeline, r.file), 400), axis=1)).all()
    assert res["hqc_total"] <= 990


def test_outside_table_e3_glob():
    assert not any("famB1" in p for p in hp.all_h22e_jsons())
    if HAVE_PAYLOADS:
        assert glob.glob(os.path.join(hp.EMU, "nexus_H2-2E_famB1_multi", "*", "*.json"))
