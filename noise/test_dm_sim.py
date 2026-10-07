"""Tests for dm_sim.  Run:  python3 test_dm_sim.py   (or pytest)."""

import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dm_sim as dm  # noqa: E402

NOISE_OFF = dm.NoiseModel()


def rho_of(gates, noise=NOISE_OFF, n=None):
    return dm.final_density_matrix(gates, noise, n)[0]


# --------------------------------------------------------------------------
# (0) gate definitions match the docstring formulas
# --------------------------------------------------------------------------

def test_gate_definitions():
    from scipy.linalg import expm
    a, b = 0.37, -0.81
    assert np.allclose(dm.rz(a), expm(-0.5j * math.pi * a * dm.Z))
    assert np.allclose(dm.rx(a), expm(-0.5j * math.pi * a * dm.X))
    assert np.allclose(dm.phasedx(a, b), dm.rz(b) @ dm.rx(a) @ dm.rz(-b))
    assert np.allclose(dm.zzphase(a), expm(-0.5j * math.pi * a * np.kron(dm.Z, dm.Z)))
    assert np.allclose(dm.zzmax(), dm.zzphase(0.5))
    # PhasedX(a, 0.5) = Ry(a):  Rz(pi/2) X Rz(-pi/2) = Y
    Ry = expm(-0.5j * math.pi * a * dm.Y)
    assert np.allclose(dm.phasedx(a, 0.5), Ry)
    # CZ = e^{-i pi/4} (Rz(-0.5) (x) Rz(-0.5)) ZZMax
    CZ = np.diag([1, 1, 1, -1]).astype(complex)
    assert np.allclose(np.exp(-0.25j * math.pi) * np.kron(dm.rz(-0.5), dm.rz(-0.5)) @ dm.zzmax(), CZ)


# --------------------------------------------------------------------------
# (1) native Bell circuit, noise off: exactly 1/2, 1/2 on 00 and 11
# --------------------------------------------------------------------------
# Derivation.  PhasedX(0.5, 0.5) = Rz(pi/2) Rx(pi/2) Rz(-pi/2) = Ry(pi/2)
# maps |0> -> |+>.  ZZMax |++> = e^{-i pi/4} (|00> + i|01> + i|10> + |11>)/2
#                              = (|0>|+i> + i|1>|-i>)/sqrt2
# with |+-i> = (|0> +- i|1>)/sqrt2.  PhasedX(0.5, 0) = Rx(pi/2) sends
# |+i> -> |0> and |-i> -> -i|1>, so on qubit 1 it gives (|00> + |11>)/sqrt2.

BELL_NATIVE = [("PhasedX", 0, 0.5, 0.5), ("PhasedX", 1, 0.5, 0.5),
               ("ZZMax", 0, 1), ("PhasedX", 1, 0.5, 0.0)]


def test_bell_native_exact():
    probs, d, measured = dm.simulate(BELL_NATIVE, NOISE_OFF)
    assert measured == [0, 1]
    # 1/2 up to double rounding (|e^{-i pi/4}|^2 is not exactly 1 in floats)
    assert abs(probs[0] - 0.5) < 1e-15 and abs(probs[3] - 0.5) < 1e-15, probs
    assert probs[1] == 0.0 and probs[2] == 0.0, probs
    assert set(d) == {"00", "11"} and all(abs(v - 0.5) < 1e-15 for v in d.values())
    # the state itself is |Phi+><Phi+| to rounding
    phi = np.array([1, 0, 0, 1]) / math.sqrt(2)
    assert np.allclose(rho_of(BELL_NATIVE), np.outer(phi, phi.conj()), atol=1e-14)
    # the circuit prepares |Phi+> from |00> up to a global phase (it is a
    # state-preparation circuit, not an implementation of CNOT (H (x) I))
    psi = dm.circuit_unitary(BELL_NATIVE)[:, 0]
    assert abs(abs(np.vdot(phi, psi)) - 1) < 1e-14


# --------------------------------------------------------------------------
# (2) physicality after noisy evolution
# --------------------------------------------------------------------------

def test_density_matrix_physical():
    n = 5
    gates = dm.random_native_circuit(n, 80, seed=3)
    noise = dm.NoiseModel(p1=0.01, p2=0.03, p_spam=0.02, p_idle=0.005)
    rho = rho_of(gates, noise, n)
    assert np.allclose(rho, rho.conj().T, atol=1e-12)
    assert abs(np.trace(rho) - 1) < 1e-12
    w = np.linalg.eigvalsh(rho)
    assert w.min() > -1e-12
    # noise-off: pure state
    rho0 = rho_of(gates, NOISE_OFF, n)
    assert abs(np.trace(rho0 @ rho0) - 1) < 1e-12


# --------------------------------------------------------------------------
# (3) one ZZMax on |00> with p2 = p
# --------------------------------------------------------------------------
# ZZMax|00> = e^{-i pi/4}|00>, so rho = |00><00|.  The twirl gives
#   rho' = (1-p) rho + (p/15) sum_{P != II} P rho P
#        = (1 - 16p/15) rho + (16p/15) I/4,
# so for this (any pure) input state the fidelity is
#   F = <00|rho'|00> = 1 - 16p/15 + 16p/15 * 1/4 = 1 - 4p/5,
# also = 1 - p + 3p/15 (the 3 Paulis IZ, ZI, ZZ leave |00> fixed).
# The remaining weight 4p/5 is spread evenly: P(01)=P(10)=P(11)=4p/15.

def test_zzmax_depolarised():
    p = 0.1
    gates = [("ZZMax", 0, 1)]
    noise = dm.NoiseModel(p1=0.0, p2=p, p_spam=0.0)
    rho = rho_of(gates, noise, n=2)
    F = 1 - 4 * p / 5
    assert abs(rho[0, 0].real - F) < 1e-14
    expected = (1 - 16 * p / 15) * np.diag([1, 0, 0, 0]) + (16 * p / 15) * np.eye(4) / 4
    assert np.allclose(rho, expected, atol=1e-14)
    probs = dm.simulate(gates, noise, n=2)[0]
    assert np.allclose(probs, [F, 4 * p / 15, 4 * p / 15, 4 * p / 15], atol=1e-14)
    # same channel on an entangled input: Hellinger fidelity to ideal Bell
    res = dm.run(BELL_NATIVE, dm.NoiseModel(p1=0.0, p2=p, p_spam=0.0), success=["00", "11"])
    assert abs(res.metrics["success_noisy"] - (1 - 8 * p / 15)) < 1e-14  # 8 of 15 Paulis flip parity


# --------------------------------------------------------------------------
# (4) SPAM:  p_spam = p on |0> gives P(1) = p
# --------------------------------------------------------------------------

def test_spam():
    p = 0.013
    gates = [("Rz", 0, 0.3), ("Measure", 0)]
    probs = dm.simulate(gates, dm.NoiseModel(p1=0.0, p2=0.0, p_spam=p))[0]
    assert abs(probs[1] - p) < 1e-15 and abs(probs[0] - (1 - p)) < 1e-15
    # two qubits, independent flips: P(11 | 00 prepared) = p^2
    probs = dm.simulate([("Measure", 0), ("Measure", 1)], dm.NoiseModel(p1=0.0, p2=0.0, p_spam=p))[0]
    assert np.allclose(probs, [(1 - p) ** 2, p * (1 - p), p * (1 - p), p ** 2])


def test_asymmetric_spam():
    a, b = 0.011, 0.023     # 0 read as 1, 1 read as 0
    nm = dm.NoiseModel(p1=0.0, p2=0.0, p_meas_0=a, p_meas_1=b)
    assert nm.readout() == (a, b)
    # true 0: P(read 1) = a
    probs = dm.simulate([("Rz", 0, 0.3), ("Measure", 0)], nm)[0]
    assert abs(probs[1] - a) < 1e-15 and abs(probs[0] - (1 - a)) < 1e-15
    # true 1 (PhasedX(1, 0) = -iX): P(read 0) = b
    probs = dm.simulate([("PhasedX", 0, 1.0, 0.0), ("Measure", 0)], nm)[0]
    assert abs(probs[0] - b) < 1e-14 and abs(probs[1] - (1 - b)) < 1e-14
    # two qubits |01>: independent channels
    probs = dm.simulate([("PhasedX", 1, 1.0, 0.0), ("Measure", 0), ("Measure", 1)], nm)[0]
    assert np.allclose(probs, [(1 - a) * b, (1 - a) * (1 - b), a * b, a * (1 - b)], atol=1e-14)
    # p_spam alone fills both rates (old symmetric path); explicit values win
    assert dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.05).readout() == (0.05, 0.05)
    assert dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.05, p_meas_1=b).readout() == (0.05, b)
    p_sym = dm.simulate([("Measure", 0), ("Measure", 1)], dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.05))[0]
    p_asy = dm.simulate([("Measure", 0), ("Measure", 1)],
                        dm.NoiseModel(p1=0.0, p2=0.0, p_meas_0=0.05, p_meas_1=0.05))[0]
    assert np.allclose(p_sym, p_asy, atol=1e-15)
    # the tensor channel equals the explicit 2x2 stochastic matrix M[read, true]
    M = np.array([[1 - a, b], [a, 1 - b]])
    pt = np.array([0.7, 0.3])
    assert np.allclose(dm.spam_flip(pt, a, b), M @ pt)
    # incomplete readout spec is rejected
    try:
        dm.simulate([("Measure", 0)], dm.NoiseModel(p1=0.0, p2=0.0, p_meas_0=a))
        raise AssertionError("p_meas_1 missing should fail")
    except ValueError:
        pass


def test_init_flip():
    p = 0.017
    nm = dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.0, p_init=p)
    # no gates, n = 2: product of independent flips on |00>
    probs = dm.simulate([("Measure", 0), ("Measure", 1)], nm)[0]
    assert np.allclose(probs, [(1 - p) ** 2, (1 - p) * p, p * (1 - p), p ** 2], atol=1e-15)
    rho = rho_of([("Measure", 0)], nm, n=1)
    assert np.allclose(rho, np.diag([1 - p, p]), atol=1e-15)
    # the flip happens BEFORE the gates: X then init flip would give P(1) = 1-p
    # from |0>, but init flip then X (= PhasedX(1, 0)) gives P(1) = 1 - p too;
    # distinguish with Ry(pi/2): flipped input |1> -> |-> has the same Z
    # statistics, so use a two-qubit CX: init flip on control then CX copies it
    probs = dm.simulate([("CX", 0, 1), ("Measure", 0), ("Measure", 1)], nm)[0]
    # control flipped (p): CX makes |11>; target flipped (p): |01>; both: |10>
    expect = [(1 - p) ** 2, (1 - p) * p, p * p, p * (1 - p)]
    assert np.allclose(probs, expect, atol=1e-15), probs
    # p_init alone is a noisy run (needs p1, p2, readout)
    try:
        dm.simulate([("Measure", 0)], dm.NoiseModel(p_init=p))
        raise AssertionError("partial noise model should fail")
    except ValueError:
        pass
    # p_init = 0 reproduces the ideal state exactly
    g = dm.random_native_circuit(4, 40, seed=9)
    r0 = rho_of(g, NOISE_OFF, 4)
    r1 = rho_of(g, dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.0, p_init=0.0), 4)
    assert np.allclose(r0, r1, atol=1e-13)


# --------------------------------------------------------------------------
# extra channel checks: p1 formula, Rz virtual flag, idle dephasing
# --------------------------------------------------------------------------

def test_p1_depolarising_formula():
    # PhasedX(1, 0) = Rx(pi) = -iX : |0> -> |1>;  then depolarise:
    #   P(1) = (1-p) + p/3 (X and Y keep |1>, Z leaves it) = 1 - 2p/3
    p = 0.07
    probs = dm.simulate([("PhasedX", 0, 1.0, 0.0)], dm.NoiseModel(p1=p, p2=0.0, p_spam=0.0))[0]
    assert abs(probs[1] - (1 - 2 * p / 3)) < 1e-14
    # channel on |+>: coherence scales by 1 - 4p/3
    rho = rho_of([("PhasedX", 0, 0.5, 0.5)], dm.NoiseModel(p1=p, p2=0.0, p_spam=0.0))
    assert abs(rho[0, 1] - 0.5 * (1 - 4 * p / 3)) < 1e-14


def test_rz_virtual_flag():
    p = 0.05
    g = [("PhasedX", 0, 1.0, 0.0), ("Rz", 0, 0.4)]
    pv = dm.simulate(g, dm.NoiseModel(p1=p, p2=0.0, p_spam=0.0, rz_virtual=True))[0]
    pt = dm.simulate(g, dm.NoiseModel(p1=p, p2=0.0, p_spam=0.0, rz_virtual=False))[0]
    assert abs(pv[1] - (1 - 2 * p / 3)) < 1e-14
    # two depolarising rounds: P(1) = 1/2 + 1/2 (1 - 4p/3)^2
    assert abs(pt[1] - (0.5 + 0.5 * (1 - 4 * p / 3) ** 2)) < 1e-14


def test_idle_dephasing():
    p = 0.02
    # layer 1: PhasedX on q0 (|+>) and on q1; layer 2: PhasedX on q1 only, q0 idles
    g = [("PhasedX", 0, 0.5, 0.5), ("PhasedX", 1, 0.5, 0.5), ("PhasedX", 1, 0.5, 0.5)]
    assert dm.assign_layers(g) == [1, 1, 2]
    rho = rho_of(g, dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.0, p_idle=p), n=2)
    r0 = rho.reshape(2, 2, 2, 2)
    red0 = np.einsum("ijkj->ik", r0)  # reduced state of qubit 0
    assert abs(red0[0, 1] - 0.5 * (1 - 2 * p)) < 1e-14
    # virtual Rz does not open a layer; measurement neither
    g2 = [("PhasedX", 0, 0.5, 0.5), ("Rz", 0, 0.3), ("ZZMax", 0, 1), ("Measure", 0), ("Measure", 1)]
    assert dm.assign_layers(g2, rz_virtual=True) == [1, 1, 2, 2, 2]
    assert dm.assign_layers(g2, rz_virtual=False) == [1, 2, 3, 3, 3]


def test_layer_reordering_preserves_unitary():
    n = 6
    g = dm.random_native_circuit(n, 120, seed=11)
    r1 = rho_of(g, NOISE_OFF, n)
    # noise with all-zero rates goes through the layered path: must agree
    r2 = rho_of(g, dm.NoiseModel(p1=0.0, p2=0.0, p_spam=0.0, p_idle=0.0), n)
    assert np.allclose(r1, r2, atol=1e-13)
    U = dm.circuit_unitary(g, n)
    psi = U[:, 0]
    assert np.allclose(r1, np.outer(psi, psi.conj()), atol=1e-13)


def test_metrics_and_sampling():
    p = np.array([0.5, 0, 0, 0.5])
    q = np.array([0.4, 0.1, 0.1, 0.4])
    assert abs(dm.hellinger_fidelity(p, q) - (2 * math.sqrt(0.2)) ** 2) < 1e-15
    assert abs(dm.total_variation(p, q) - 0.2) < 1e-15
    assert dm.success_probability(q, ["00", "11"]) == 0.8
    counts = dm.sample(q, 10000, seed=1)
    assert sum(counts.values()) == 10000
    assert dm.sample(q, 10000, seed=1) == counts
    m = dm.metrics_from_counts(p, counts, success=["00", "11"])
    assert abs(m["success_noisy"] - 0.8) < 0.02


def test_qasm_parser():
    qasm = """OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0],q[1];
    rz(pi/2) q[1];
    rx(-0.5*pi) q[0];
    rzz(pi/4) q[0],q[1];
    barrier q[0],q[1];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    """
    gates, n = dm.qasm_to_gates(qasm)
    assert n == 2
    assert gates[:2] == [("H", 0), ("CX", 0, 1)]
    assert gates[2][0] == "Rz" and abs(gates[2][2] - 0.5) < 1e-15
    assert gates[3][0] == "Rx" and abs(gates[3][2] + 0.5) < 1e-15
    assert gates[4][0] == "ZZPhase" and abs(gates[4][3] - 0.25) < 1e-15
    assert gates[5:] == [("Measure", 0), ("Measure", 1)]
    bell, _ = dm.qasm_to_gates('qreg q[2]; h q[0]; cx q[0],q[1]; measure q -> c;')
    probs = dm.simulate(bell)[0]
    assert np.allclose(probs, [0.5, 0, 0, 0.5], atol=1e-15)
    # qasm Bell and native Bell agree, and CX gets 2q noise like ZZMax
    noise = dm.NoiseModel(p1=0.0, p2=0.1, p_spam=0.0)
    pq = dm.simulate(bell, noise)[0]
    pn = dm.simulate(BELL_NATIVE, noise)[0]
    assert np.allclose(pq, pn, atol=1e-14)


def test_measure_subset_and_errors():
    g = [("PhasedX", 0, 0.5, 0.5), ("ZZMax", 0, 1), ("Measure", 1)]
    probs, d, measured = dm.simulate(g, n=3)
    assert measured == [1] and len(probs) == 2 and abs(probs[0] - 1) < 1e-15
    try:
        dm.simulate([("Measure", 0), ("Rz", 0, 0.1)])
        raise AssertionError("gate after measurement should fail")
    except ValueError:
        pass
    try:
        dm.simulate([("Rz", 0, 0.1)], dm.NoiseModel(p1=0.01))
        raise AssertionError("partial noise model should fail")
    except ValueError:
        pass


# --------------------------------------------------------------------------
# (5) cross-check against bench/sv.py if present
# --------------------------------------------------------------------------

def native_to_sv(gates):
    """Translate native tuples (half-turns) to bench/sv.py gates (radians)."""
    out = []
    for g in gates:
        if g[0] == "Rz":
            out.append(("rz", [g[1]], [g[2] * math.pi]))
        elif g[0] == "PhasedX":   # Rz(b) Rx(a) Rz(-b): Rz(-b) acts first
            out += [("rz", [g[1]], [-g[3] * math.pi]), ("rx", [g[1]], [g[2] * math.pi]),
                    ("rz", [g[1]], [g[3] * math.pi])]
        elif g[0] == "Rx":
            out.append(("rx", [g[1]], [g[2] * math.pi]))
        elif g[0] == "H":
            out.append(("h", [g[1]], []))
        elif g[0] == "ZZPhase":
            out.append(("rzz", [g[1], g[2]], [g[3] * math.pi]))
        elif g[0] == "ZZMax":
            out.append(("rzz", [g[1], g[2]], [math.pi / 2]))
        elif g[0] == "CX":
            out.append(("cx", [g[1], g[2]], []))
        elif g[0] == "Measure":
            pass
        else:
            raise ValueError(g)
    return out


def test_against_sv_module():
    bench = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bench")
    if not os.path.exists(os.path.join(bench, "sv.py")):
        print("  [skip] bench/sv.py not present")
        return
    sys.path.insert(0, bench)
    import sv
    for seed in range(3):
        n = 6
        g = dm.random_native_circuit(n, 100, seed=seed)
        psi = sv.run(native_to_sv(g), n).reshape(-1)
        rho = rho_of(g, NOISE_OFF, n)
        assert np.allclose(rho, np.outer(psi, psi.conj()), atol=1e-12)
        assert np.allclose(dm.simulate(g, n=n)[0], sv.probabilities(psi), atol=1e-12)
    # same qasm string through both parsers
    qasm = ("OPENQASM 2.0; include \"qelib1.inc\"; qreg q[3]; creg c[3]; h q[0]; rx(0.3) q[1];"
            " cx q[0],q[1]; rzz(pi/3) q[1],q[2]; rz(-pi/5) q[2]; h q[2]; cx q[2],q[0];"
            " measure q[0] -> c[0]; measure q[1] -> c[1]; measure q[2] -> c[2];")
    g, n = dm.qasm_to_gates(qasm)
    n2, g2 = sv.parse_qasm(qasm)
    assert n == n2 == 3
    psi = sv.run(g2, n2).reshape(-1)
    assert np.allclose(dm.simulate(g, n=n)[0], sv.probabilities(psi), atol=1e-12)
    assert np.allclose(rho_of(g, NOISE_OFF, n), np.outer(psi, psi.conj()), atol=1e-12)


def test_depolarising_equals_pauli_sum():
    n = 4
    g = dm.random_native_circuit(n, 30, seed=2, measure=False)
    rho = rho_of(g, NOISE_OFF, n).reshape((2,) * (2 * n))
    for p in (0.0, 0.05, 0.3):
        a = dm.depolarise_1q(rho, p, 2, n)
        b = dm.depolarise_1q_pauli_sum(rho, p, 2, n)
        assert np.allclose(a, b, atol=1e-14)
        a = dm.depolarise_2q(rho, p, 3, 1, n)
        b = dm.depolarise_2q_pauli_sum(rho, p, 3, 1, n)
        assert np.allclose(a, b, atol=1e-14)
    # fully depolarising (p = 15/16) leaves I/4 on the pair
    full = dm.depolarise_2q(rho, 15 / 16, 0, 1, n).reshape(16, 16)
    red = np.trace(full.reshape(4, 4, 4, 4), axis1=1, axis2=3)
    assert np.allclose(red, np.eye(4) / 4, atol=1e-14)


# --------------------------------------------------------------------------
# timing at n = 8 with 500 gates
# --------------------------------------------------------------------------

def test_timing_n8():
    n = 8
    g = dm.random_native_circuit(n, 500, seed=5)
    noise = dm.NoiseModel(p1=1e-4, p2=1e-3, p_spam=2e-3, p_idle=1e-4)
    t0 = time.time()
    res = dm.run(g, noise, success=["0" * n], shots=1000, seed=0)
    dt = time.time() - t0
    print("  n=8, 500 gates (ideal + noisy run): %.2f s, F_H=%.4f, TVD=%.4f"
          % (dt, res.metrics["hellinger_fidelity"], res.metrics["tvd"]))
    assert dt < 60
    assert abs(res.noisy.sum() - 1) < 1e-12 and abs(res.ideal.sum() - 1) < 1e-12


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS %s" % name)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL %s: %r" % (name, e))
    print("%d/%d passed" % (len(tests) - failed, len(tests)))
    sys.exit(1 if failed else 0)
