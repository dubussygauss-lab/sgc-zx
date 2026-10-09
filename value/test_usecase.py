"""Tests for bench/usecase/build_usecase.py and value/usecase.py.
Run: python3 -m pytest value/test_usecase.py

1. The Toffoli network equals CCX and the Barenco C^m X equals the ideal C^m X on
   every basis state, ancillas in any state (dirty) and restored.
2. The committed QASM files equal a fresh run of the generator.
3. Every derived column of value/usecase.csv is recomputed from its inputs, the shot
   formulas agree with value_ledger / value_by_application, and the T-count as
   written equals 7 per Toffoli.
4. value/usecase.py reproduces the committed CSV (slow: recompiles both instances).
"""
import csv
import itertools
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from pytket import Circuit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench/usecase"))
sys.path.insert(0, str(ROOT / "value"))
import build_usecase as B  # noqa: E402
import usecase as U  # noqa: E402

CSV = ROOT / "value/usecase.csv"


def _circ(gates, n):
    c = Circuit(n)
    one = {"h": c.H, "x": c.X, "t": c.T, "tdg": c.Tdg}
    for op, *qs in gates:
        if op == "cx":
            c.CX(*qs)
        else:
            one[op](qs[0])
    return c


def _ideal_mcx(n, ctrls, tgt):
    d = 2 ** n
    U_ = np.zeros((d, d))
    for i in range(d):
        bits = [(i >> (n - 1 - q)) & 1 for q in range(n)]
        if all(bits[c] for c in ctrls):
            bits[tgt] ^= 1
        j = sum(b << (n - 1 - q) for q, b in enumerate(bits))
        U_[j, i] = 1
    return U_


def _dev(U1, U2):
    return 1 - abs(np.trace(U1.conj().T @ U2)) / U1.shape[0]


def test_toffoli_is_ccx():
    U1 = _circ(B.toffoli(0, 1, 2), 3).get_unitary()
    assert _dev(U1, _ideal_mcx(3, [0, 1], 2)) < 1e-12
    assert np.allclose(U1, _ideal_mcx(3, [0, 1], 2), atol=1e-12)   # no global phase either


@pytest.mark.parametrize("m", [3, 4, 5])
def test_barenco_mcx_dirty(m):
    n = 2 * m - 1
    ctrls, tgt, anc = list(range(m)), m, list(range(m + 1, n))
    g = []
    for a, b, c in B.barenco_mcx(ctrls, tgt, anc):
        g += B.toffoli(a, b, c)
    U1 = _circ(g, n).get_unitary()
    assert np.allclose(U1, _ideal_mcx(n, ctrls, tgt), atol=1e-10)
    assert len(B.barenco_mcx(ctrls, tgt, anc)) == 4 * (m - 2)


def test_qasm_reproduced():
    for d in B.SIZES:
        gates, n = B.grover_gates(d)
        assert (ROOT / f"bench/usecase/grover_d{d}.qasm").read_text() == B.to_qasm(gates, n)


@pytest.fixture(scope="module")
def rows():
    with open(CSV) as f:
        return list(csv.DictReader(f))


def test_derived_columns(rows):
    import value_by_application as vba
    import value_ledger as vl
    for r in rows:
        f = {k: float(v) for k, v in r.items() if k not in
             ("file", "algorithm", "marked_bits", "check_kind", "status_P0", "status_P2", "chosen")}
        d = int(f["n_data"])
        assert f["iterations"] == math.floor(math.pi / 4 * math.sqrt(2 ** d))
        assert abs(f["p_success_ideal_sv"] - f["p_success_ideal_formula"]) < 1e-11
        assert f["ancilla_leak_sv"] < 1e-12
        assert f["t_count_written"] == 7 * 2 * f["iterations"] * 4 * (d - 3)
        assert r["status_P0"] == r["status_P2"] == "ok"
        assert abs(f["check_dev_P0"]) <= 1e-8 and abs(f["check_dev_P2"]) <= 1e-8
        assert r["check_kind"] == ("unitary" if f["n_qubits"] <= 8 else "statevector")
        hs = min(f["hqc_P0"], f["hqc_P2"])
        assert f["hqc_PSEL"] == hs and r["chosen"] == ("P0" if f["hqc_P0"] <= f["hqc_P2"] else "P2")
        assert f["n2q_PSEL"] == f["n2q_" + r["chosen"]]
        assert f["hqc_saving"] == pytest.approx(f["hqc_P0"] - hs)
        assert f["hqc_saving_pct"] == pytest.approx(100 * (f["hqc_P0"] - hs) / f["hqc_P0"])
        for p in ("P0", "PSEL"):
            h = f["hqc_" + p]
            k = (h - 5) * 5000 / 1000
            assert f["shots_one_job_" + p] == int(vl.shots_affordable(np.array([k]), 10_000)[0])
            assert f["shots_capped_" + p] == vba.shots_affordable_capped(h)
            assert f["hits_ideal_" + p] == pytest.approx(f["shots_capped_" + p] * f["p_success_ideal_sv"])
        assert f["extra_shots_capped"] == f["shots_capped_PSEL"] - f["shots_capped_P0"]
        assert f["dN2q"] == f["n2q_P0"] - f["n2q_PSEL"]
        assert f["fid_ratio_model"] == pytest.approx(math.exp(1.1801e-3 * f["dN2q"]))


def test_script_reproduces_csv(tmp_path, rows):
    subprocess.run([sys.executable, str(ROOT / "value/usecase.py")], check=True,
                   capture_output=True)
    with open(CSV) as f:
        new = list(csv.DictReader(f))
    assert new == rows
