"""Tests for the Selene route used by selene/run_selene.py.

    HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= \
        python3 -m pytest selene/test_selene.py -q

1. Bell test: H, CX, measure -> only 00 and 11, each ~ 1/2.
2. Measure-map permutation test: X on q[0], measure q[0]->c[2], q[1]->c[0],
   q[2]->c[1].  The bitstring built from result("c") in array order must be
   "001" (c[0] most significant), and must agree with the index at which
   compile.probs_from_measured_qasm puts the mass for the same circuit written
   as hqslib1 QASM.  A second instance with a non-trivial qubit *and* bit
   permutation (X on q[2]) checks that no qubit/bit swap hides in the route.
3. Deterministic seeding: the same seed gives the same counts.
4. The noiseless sampling metrics on one compiled family-A circuit are within
   the expected sampling scale (TVD <= 4 x sqrt(k / (2 pi N))).
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pipelines"))

import run_selene as RS  # noqa: E402

RS._unset_proxies()

from pytket import Circuit  # noqa: E402
from pytket.qasm import circuit_to_qasm_str  # noqa: E402
import compile as C  # noqa: E402


def _counts(circ, name, shots=1000, seed=3):
    runner = RS.build_runner(circ, name)
    return RS.sample(runner, circ.n_qubits, shots, seed)


def test_bell():
    circ = Circuit(2, 2)
    circ.H(0).CX(0, 1).Measure(0, 0).Measure(1, 1)
    c = _counts(circ, "t_bell", shots=2000)
    assert c[0b01] == 0 and c[0b10] == 0
    assert c[0b00] + c[0b11] == 2000
    assert abs(c[0b00] - 1000) < 5 * np.sqrt(500)      # 5 sigma


@pytest.mark.parametrize("xq", [0, 2])
def test_measure_map_permutation(xq):
    circ = Circuit(3, 3)
    circ.X(xq)
    circ.Measure(0, 2).Measure(1, 0).Measure(2, 1)      # q[j] -> c[i]
    c = _counts(circ, f"t_perm{xq}", shots=200)
    # c[0] = q1 = 0, c[1] = q2, c[2] = q0 ; with X on q[xq]
    expect = {0: "001", 2: "010"}[xq]
    idx = int(expect, 2)
    assert c[idx] == 200, (xq, c)
    # same answer from the exact-distribution helper on the hqslib1 QASM text
    qasm = circuit_to_qasm_str(circ, header="hqslib1")
    p = C.probs_from_measured_qasm(qasm)
    assert p[idx] == pytest.approx(1.0)


def test_seed_reproducible():
    circ = Circuit(2, 2)
    circ.H(0).Rz(0.3, 0).CX(0, 1).Rx(0.2, 1).Measure(0, 0).Measure(1, 1)
    runner = RS.build_runner(circ, "t_seed")
    a = RS.sample(runner, 2, 500, 11)
    b = RS.sample(runner, 2, 500, 11)
    d = RS.sample(runner, 2, 500, 12)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, d)


def test_compiled_circuit_within_sampling_scale():
    row = RS.noiseless_job(("A", "ladder_n6_r2_disorder_s1.qasm", "ladder", 6, "P2", 2000, 999))
    assert row["flag"] == 0, row
    assert row["exact_vs_ref_maxdiff"] < 1e-8
    assert row["shots_outside_support"] == 0


def test_depolarizing_model_signature():
    from selene_sim import DepolarizingErrorModel
    em = DepolarizingErrorModel(random_seed=1, p_1q=7.3e-5, p_2q=1.29e-3, p_meas=1.35e-3, p_init=4e-5)
    assert em.p_1q == 7.3e-5 and em.p_2q == 1.29e-3
