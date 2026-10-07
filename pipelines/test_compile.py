"""Self-running tests for compile.py.  Run: python pipelines/test_compile.py"""

import os
import sys

import numpy as np
from pytket import Circuit, OpType
from pytket.qasm import circuit_from_qasm, circuit_from_qasm_str

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = C.CHECK_TOL


def _all_pipelines(circ, ref_probs=None):
    ref, _ = C.compile_pipeline("P0ref", circ)
    assert C.unitary_deviation(circ.get_unitary(), ref.get_unitary()) < TOL
    out = {}
    for p in C.PIPELINES:
        comp, _ = C.compile_pipeline(p, circ)
        m = C.metrics(comp, n_measure=comp.n_qubits)
        assert m["native"], (p, m["non_native_ops"])
        ck = C.check(comp, ref, ref_probs)
        assert ck["check_ok"], (p, ck)
        if ref_probs is not None:
            q = C.to_qasm(C.add_measure_all(comp))
            d = np.max(np.abs(C.probs_from_measured_qasm(q) - ref_probs))
            assert d < TOL, (p, d)
        out[p] = (comp, m)
    return out


def test_bell():
    c = Circuit(2)
    c.H(0)
    c.CX(0, 1)
    want = np.array([0.5, 0, 0, 0.5])
    res = _all_pipelines(c, want)
    for p, (comp, m) in res.items():
        assert m["n_2q"] == 1, (p, m["n_2q"])
        assert np.max(np.abs(C.probs(comp) - want)) < TOL


def test_cx_cx_cancels():
    c = Circuit(2)
    c.Rx(0.3, 0)
    c.CX(0, 1)
    c.CX(0, 1)
    c.Rz(0.2, 1)
    for p in ("P0", "P1"):
        comp, _ = C.compile_pipeline(p, c)
        assert C.metrics(comp)["n_2q"] == 0, p
    # P0ref merges the two rebased ZZPhase(0.5) into one ZZPhase(1) = -i ZZ,
    # a Clifford it does not remove
    ref, _ = C.compile_pipeline("P0ref", c)
    assert C.metrics(ref)["n_2q"] == 1


def test_random_clifford_t():
    rng = np.random.default_rng(7)
    c = Circuit(4)
    for _ in range(40):
        k = rng.integers(0, 6)
        q = int(rng.integers(0, 4))
        if k == 0:
            c.H(q)
        elif k == 1:
            c.S(q)
        elif k == 2:
            c.T(q)
        elif k == 3:
            c.Tdg(q)
        else:
            t = int(rng.integers(0, 4))
            if t != q:
                c.CX(q, t)
    ref_probs = C.probs(c)
    _all_pipelines(c, ref_probs)


def test_family_a_tfim_n4():
    f = os.path.join(ROOT, "bench", "family_A", "tfim_n4_r1_uniform_s1")
    circ = circuit_from_qasm(f + ".qasm")
    ref_probs = np.load(f + ".npy")
    res = _all_pipelines(circ, ref_probs)
    assert res["P0ref"][1]["n_2q"] == 6
    # HQC formula check: n_qubits=4, measured 4, shots 1000
    m = res["P0ref"][1]
    assert abs(m["hqc"] - (5 + (m["n_phasedx"] + 10 * m["n_2q"] + 5 * 8) / 5)) < 1e-12


def test_implicit_permutation_and_sim():
    # explicit SWAPs become implicit permutations under allow_swaps=True;
    # get_unitary, the numpy simulator and the measured QASM must all agree
    c = Circuit(12)
    for i in range(12):
        c.Rx(0.1 * i + 0.05, i)
    c.H(0); c.CX(0, 1); c.SWAP(1, 2); c.Rz(0.3, 2); c.CX(0, 2)  # noqa: E702
    c.SWAP(3, 11); c.Rx(0.2, 11); c.CX(11, 5)  # noqa: E702
    comp, _ = C.compile_pipeline("P0", c)
    perm = comp.implicit_qubit_permutation()
    assert any(k != v for k, v in perm.items())
    want = C.probs(c)
    assert C.state_infidelity(C.statevector(c), C.statevector(comp)) < TOL
    q = C.to_qasm(C.add_measure_all(comp))
    assert np.max(np.abs(C.probs_from_measured_qasm(q) - want)) < TOL
    # 10-qubit version: numpy path vs pytket path agree
    c10 = Circuit(10)
    for i in range(10):
        c10.Rx(0.1 * i + 0.05, i)
    c10.CX(0, 1); c10.SWAP(1, 2); c10.Rz(0.3, 2); c10.CX(0, 9)  # noqa: E702
    comp10, _ = C.compile_pipeline("P0", c10)
    n = 10
    t = np.zeros((2,) * n, dtype=complex)
    t[(0,) * n] = 1.0
    for cmd in comp10.get_commands():
        qs = [x.index[0] for x in cmd.args]
        k = len(qs)
        u = cmd.op.get_unitary().reshape((2,) * (2 * k))
        t = np.tensordot(u, t, axes=(list(range(k, 2 * k)), qs))
        t = np.moveaxis(t, list(range(k)), qs)
    perm = comp10.implicit_qubit_permutation()
    order = [None] * n
    for x in comp10.qubits:
        order[perm[x].index[0]] = x.index[0]
    sv = np.transpose(t, order).reshape(-1)
    assert C.state_infidelity(sv, comp10.get_statevector()) < TOL


def test_pyzx_angle_rounding():
    s = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nrz(-0.2) q[0];\n'
    c = circuit_from_qasm_str(s)
    err = C.pyzx_angle_rounding(c)
    assert 0 < err < 1e-6, err


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all tests passed")
