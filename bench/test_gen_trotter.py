"""Tests for gen_trotter.py and sv.py.

Run with `python test_gen_trotter.py` (no pytest needed) or with pytest.

The reference simulator here is independent of sv.py: every gate is expanded
to a dense 2^n x 2^n matrix with Kronecker products, so the two codes agree
only if both implement the stated conventions (q[0] = most significant bit).
"""

import glob
import math
import os
import re
import sys

import numpy as np
from scipy.linalg import expm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_trotter as gt  # noqa: E402
import sv  # noqa: E402

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]])
Z = np.diag([1.0, -1.0]).astype(complex)
P0 = np.diag([1.0, 0.0]).astype(complex)
P1 = np.diag([0.0, 1.0]).astype(complex)
PAULI = {"X": X, "Y": Y, "Z": Z}


# ---------------------------------------------------------------- reference simulator

def kron_all(ops):
    out = np.array([[1.0 + 0j]])
    for o in ops:
        out = np.kron(out, o)
    return out


def embed(n, ops_at):
    """Dense operator with ops_at = {qubit: 2x2 matrix}, identity elsewhere."""
    return kron_all([ops_at.get(q, I2) for q in range(n)])


def dense_gate(name, qs, ps, n):
    ps = [sv.eval_angle(p) if isinstance(p, str) else float(p) for p in ps]
    if name == "h":
        return embed(n, {qs[0]: (X + Z) / math.sqrt(2)})
    if name == "rz":
        return embed(n, {qs[0]: expm(-0.5j * ps[0] * Z)})
    if name == "rx":
        return embed(n, {qs[0]: expm(-0.5j * ps[0] * X)})
    if name == "cx":
        c, t = qs
        return embed(n, {c: P0}) + embed(n, {c: P1, t: X})
    if name == "x":
        return embed(n, {qs[0]: X})
    raise ValueError(name)


def dense_unitary(gates, n):
    U = np.eye(2 ** n, dtype=complex)
    for name, qs, ps in gates:
        U = dense_gate(name, qs, ps, n) @ U
    return U


def dense_run(gates, n):
    psi = np.zeros(2 ** n, dtype=complex)
    psi[0] = 1.0
    for name, qs, ps in gates:
        psi = dense_gate(name, qs, ps, n) @ psi
    return psi


def hamiltonian(term_list, n):
    H = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for coef, label, qs in term_list:
        H += coef * embed(n, {q: PAULI[ch] for q, ch in zip(qs, label)})
    return H


def opnorm(A):
    return np.linalg.norm(A, 2)


# ---------------------------------------------------------------- tests

def test_primitives_are_exact_exponentials():
    # each primitive on qubits (0, 2) of 3 must equal expm(-i t P) including phase
    rng = np.random.default_rng(1)
    for label, prim in gt.PRIMITIVE.items():
        for _ in range(3):
            t = float(rng.uniform(-2, 2))
            if label == "X":
                gates, qs = prim(2, t), [2]
            else:
                gates, qs = prim(0, 2, t), [0, 2]
            P = embed(3, {q: PAULI[ch] for q, ch in zip(qs, label)})
            U = dense_unitary(gates, 3)
            assert opnorm(U - expm(-1j * t * P)) < 1e-12, (label, t)


def test_single_term_step_is_exact():
    # one Trotter step of a single-term Hamiltonian is exp(-i H dt) exactly
    for term in [(-1.3, "ZZ", [0, 1]), (0.7, "XX", [1, 2]), (0.4, "YY", [0, 2]), (-0.9, "X", [1])]:
        gates = gt.trotter_circuit([term], gt.DT, 1)
        U = dense_unitary(gates, 3)
        assert opnorm(U - expm(-1j * gt.DT * hamiltonian([term], 3))) < 1e-12, term


def test_commuting_terms_are_exact():
    # TFIM with h = 0 (only ZZ) and with J = 0 (only X) are exact for any r
    for c in [{"bonds": [[0, 1, 1.0], [1, 2, 0.7], [2, 3, 1.2]], "h": 0.0},
              {"bonds": [[0, 1, 0.0], [1, 2, 0.0], [2, 3, 0.0]], "h": 1.0}]:
        tl = gt.terms("tfim", 4, c)
        U = dense_unitary(gt.trotter_circuit(tl, gt.DT, 3), 4)
        assert opnorm(U - expm(-3j * gt.DT * hamiltonian(tl, 4))) < 1e-12


def test_hamiltonian_signs_match_spec():
    # TFIM n=3 uniform: H = -ZZ01 - ZZ12 - X0 - X1 - X2
    H = hamiltonian(gt.terms("tfim", 3, gt.uniform_couplings("tfim", 3)), 3)
    Hs = -(embed(3, {0: Z, 1: Z}) + embed(3, {1: Z, 2: Z})) - sum(embed(3, {q: X}) for q in range(3))
    assert opnorm(H - Hs) < 1e-12
    # xxz n=2 uniform: H = XX + YY + 0.5 ZZ
    H = hamiltonian(gt.terms("xxz", 2, gt.uniform_couplings("xxz", 2)), 2)
    assert opnorm(H - (np.kron(X, X) + np.kron(Y, Y) + 0.5 * np.kron(Z, Z))) < 1e-12
    # ladder n=4: bonds (0,1),(2,3) rails and (0,2),(1,3) rungs
    assert sorted(tuple(b[:2]) for b in gt.uniform_couplings("ladder", 4)["bonds"]) == \
        [(0, 1), (0, 2), (1, 3), (2, 3)]


def test_trotter_error_scales_as_one_over_r():
    # fixed total time T, dt = T / r: ||U_r - exp(-iHT)|| ~ C / r for first order
    rng = np.random.default_rng(7)
    T = 1.0
    for model, n in [("tfim", 4), ("xxz", 4), ("ladder", 4), ("tfim", 6), ("xxz", 6)]:
        c = gt.draw_couplings(model, n, rng)
        tl = gt.terms(model, n, c)
        exact = expm(-1j * T * hamiltonian(tl, n))
        rs = [8, 16, 32, 64]
        err = [opnorm(dense_unitary(gt.trotter_circuit(tl, T / r, r), n) - exact) for r in rs]
        ratios = [err[i] / err[i + 1] for i in range(len(rs) - 1)]
        assert all(1.8 < q < 2.2 for q in ratios), (model, n, err, ratios)
        assert err[-1] < 0.05, (model, n, err)
        assert err[-1] * rs[-1] > 1e-3, (model, n, err)   # not trivially zero


def test_sv_matches_dense_simulator():
    rng = np.random.default_rng(3)
    for model, n in [("tfim", 5), ("xxz", 4), ("ladder", 6)]:
        gates = gt.numeric_gates(gt.trotter_circuit(gt.terms(model, n, gt.draw_couplings(model, n, rng)), gt.DT, 2))
        assert opnorm(sv.unitary(gates, n) - dense_unitary(gates, n)) < 1e-12
        assert np.linalg.norm(sv.run(gates, n).reshape(-1) - dense_run(gates, n)) < 1e-12


def test_sv_extra_gates():
    # rzz and u3 (for later use) against their defining matrices, on 3 qubits
    gates = [("rzz", [0, 2], [0.37])]
    ref = expm(-0.5j * 0.37 * embed(3, {0: Z, 2: Z}))
    assert opnorm(sv.unitary(gates, 3) - ref) < 1e-12
    t, p, l = 0.3, 1.1, -0.4
    u3 = np.array([[math.cos(t / 2), -np.exp(1j * l) * math.sin(t / 2)],
                   [np.exp(1j * p) * math.sin(t / 2), np.exp(1j * (p + l)) * math.cos(t / 2)]])
    assert opnorm(sv.unitary([("u3", [1], [t, p, l])], 3) - embed(3, {1: u3})) < 1e-12
    # qubit order: x on q[0] of 2 qubits flips the MSB -> index 2
    psi = sv.run([("x", [0], [])], 2).reshape(-1)
    assert abs(psi[2]) == 1.0


def test_qasm_roundtrip_and_depth():
    rng = np.random.default_rng(5)
    gates = gt.trotter_circuit(gt.terms("xxz", 4, gt.draw_couplings("xxz", 4, rng)), gt.DT, 1)
    n, parsed = sv.parse_qasm(gt.to_qasm(gates, 4))
    assert n == 4 and len(parsed) == len(gates)
    assert opnorm(sv.unitary(parsed, 4) - dense_unitary(gates, 4)) < 1e-12
    meas = gt.to_qasm(gates, 4, measure=True)
    assert "creg c[4];" in meas and meas.rstrip().endswith("measure q -> c;")
    assert "measure" not in gt.to_qasm(gates, 4)
    assert all(not re.search(r"\b(rzz|u3)\b", line) for line in meas.splitlines())
    # depth: cx(0,1) rz(1) cx(0,1) rz(2) -> 3 layers
    assert gt.depth([("cx", [0, 1], []), ("rz", [1], [0.1]), ("cx", [0, 1], []), ("rz", [2], [0.1])]) == 3


_GEN = {}


def generated(tmp_dir=None):
    """Generator output in a scratch dir (run once per test session)."""
    import tempfile
    if "out" not in _GEN:
        out = tmp_dir or tempfile.mkdtemp()
        _GEN["out"] = out
        _GEN["rows"] = gt.main(out)
    return _GEN["out"], _GEN["rows"]


def test_written_files(tmp_dir=None):
    # generator output in a scratch dir: npy matches an independent simulation, manifest matches files
    import csv
    import json
    out, rows = generated(tmp_dir)
    assert len(rows) == len(gt.MODELS) * len(gt.SIZES) * len(gt.STEPS) * (1 + gt.N_DISORDER)
    assert len(glob.glob(os.path.join(out, "*.npy"))) == sum(1 for x in rows if x["n"] <= gt.NPY_MAX_N)
    with open(os.path.join(out, "manifest.csv")) as f:
        man = list(csv.DictReader(f))
    assert [m["file"] for m in man] == [x["file"] for x in rows]
    for m in man:
        text = open(os.path.join(out, m["file"])).read()
        n, gates = sv.parse_qasm(text)
        assert n == int(m["n"])
        for g in ("cx", "rz", "rx", "h"):
            assert int(m["n_" + g]) == sum(1 for name, _, _ in gates if name == g)
        assert int(m["depth"]) == gt.depth(gates)
        c = json.loads(m["couplings"])
        assert c["dt"] == gt.DT
        if m["disorder"] == "disorder":
            assert all(0.5 <= J <= 1.5 for b in c["bonds"] for J in b[2:])
        if m["model"] == "xxz":
            assert all(b[2] == b[3] for b in c["bonds"])   # Jy = Jx
        assert m["initial_state"] == ("neel" if m["model"] == "xxz" else "zero")
        xs = [(name, qs) for name, qs, _ in gates if name == "x"]
        if m["model"] == "xxz":
            assert xs == [("x", [i]) for i in range(1, n, 2)]
            assert [name for name, _, _ in gates[:len(xs)]] == ["x"] * len(xs)   # prepended
        else:
            assert xs == []
        if n <= 6:
            p = np.load(os.path.join(out, m["file"][:-5] + ".npy"))
            assert np.allclose(p, np.abs(dense_run(gates, n)) ** 2, atol=1e-12)
            assert abs(p.sum() - 1) < 1e-12


def neel_vector(n):
    psi = np.zeros(2 ** n, dtype=complex)
    psi[int("01" * (n // 2) + "0" * (n % 2), 2)] = 1.0    # q[0] = MSB, odd qubits set
    return psi


def test_xxz_neel_distribution_is_nondeterministic():
    # every written xxz file (n <= 10) has an ideal distribution with support > 1;
    # tfim and ladder files start from |0..0> and their npy is unchanged in kind
    out, rows = generated()
    for x in rows:
        if x["model"] != "xxz" or x["n"] > gt.NPY_MAX_N:
            continue
        p = np.load(os.path.join(out, x["file"][:-5] + ".npy"))
        support = int((p > 1e-12).sum())
        assert support > 1, (x["file"], support)


def test_xxz_circuit_matches_expm_on_neel_input():
    # (a) the written file = state preparation + Trotter gates, exactly:
    #     psi_file = U_trotter |neel>  with U_trotter the dense unitary of the
    #     Trotter gates alone;  (b) U_trotter |neel> -> expm(-i H T)|neel> with
    #     error ~ 1/r at fixed T (first-order Trotter), on the Neel input
    rng = np.random.default_rng(11)
    for n in (4, 6):
        for c in (gt.uniform_couplings("xxz", n), gt.draw_couplings("xxz", n, rng)):
            tl = gt.terms("xxz", n, c)
            for r in gt.STEPS:
                gates = gt.state_prep_gates("xxz", n) + gt.trotter_circuit(tl, gt.DT, r)
                psi_file = dense_run(gates, n)
                U = dense_unitary(gt.trotter_circuit(tl, gt.DT, r), n)
                assert np.linalg.norm(psi_file - U @ neel_vector(n)) < 1e-12, (n, r)
                # the file parses back to the same state
                nq, parsed = sv.parse_qasm(gt.to_qasm(gates, n))
                assert nq == n
                assert np.linalg.norm(sv.run(parsed, n).reshape(-1) - psi_file) < 1e-12
            if n > 4:
                continue    # the convergence check below is slow in the dense simulator
            H = hamiltonian(tl, n)
            T = 1.0
            exact = expm(-1j * T * H) @ neel_vector(n)
            rs = [8, 16, 32, 64]
            err = [np.linalg.norm(dense_run(gt.state_prep_gates("xxz", n)
                                            + gt.trotter_circuit(tl, T / r, r), n) - exact) for r in rs]
            ratios = [err[i] / err[i + 1] for i in range(len(rs) - 1)]
            assert all(1.7 < q < 2.3 for q in ratios), (n, err, ratios)
            assert err[-1] < 0.05 and err[-1] * rs[-1] > 1e-4, (n, err)


def test_draws_are_reproducible():
    a = gt.all_instances()
    b = gt.all_instances()
    assert all(x[4] == y[4] for x, y in zip(a, b))
    # uniform and disordered instances must not be identical
    assert a[0][4] != a[1][4]


if __name__ == "__main__":
    names = [k for k in list(globals()) if k.startswith("test_")]
    failed = 0
    for name in names:
        try:
            globals()[name]()
            print("PASS", name)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", name, repr(e))
    print("%d/%d passed" % (len(names) - failed, len(names)))
    sys.exit(1 if failed else 0)
