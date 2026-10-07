"""Minimal numpy statevector simulator for small OpenQASM 2.0 circuits.

Conventions (shared with gen_trotter.py and the benchmark reference data)
------------------------------------------------------------------------
* The state of n qubits is a complex array of shape (2,)*n; axis i is qubit
  q[i].  Flattened in C order the basis index is sum_i b_i 2^(n-1-i), so q[0]
  is the most significant bit ("ILO-BE", the pytket default; qiskit's default
  is the reverse).
* Gate matrices (theta in radians):
    rz(t)  = exp(-i t Z/2)               = diag(e^{-it/2}, e^{+it/2})
    rx(t)  = exp(-i t X/2)
    h      = (X + Z)/sqrt(2)
    cx     = |0><0| (x) I + |1><1| (x) X   (first qubit = control)
    rzz(t) = exp(-i t Z(x)Z/2)           (qiskit / pytket ZZPhase(t/pi))
    u3(t,p,l) = [[cos(t/2), -e^{il} sin(t/2)],
                 [e^{ip} sin(t/2), e^{i(p+l)} cos(t/2)]]   (OpenQASM 2 U)
  qelib1.inc defines rz(t) as u1(t) = diag(1, e^{it}), which differs from the
  rz above by a global phase only.  Probabilities are unaffected; compare
  unitaries up to global phase if that matters.
* A circuit is a list of gates (name, qubits, params) with params as floats.

The parser accepts OPENQASM 2.0 files that use qelib1.inc gates from the set
{h, rz, rx, cx, rzz, u3, x, y, z, s, sdg, t, tdg, u1, u2, cz} on one or more
qregs; measure, barrier and creg lines are ignored.  Angle expressions may
use numbers, pi, + - * / and parentheses.
"""

import math
import re

import numpy as np


# ---------------------------------------------------------------- gate matrices

def _rz(t):
    return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])


def _rx(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -1j * s], [-1j * s, c]])


def _u3(t, p, l):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -np.exp(1j * l) * s],
                     [np.exp(1j * p) * s, np.exp(1j * (p + l)) * c]])


_H = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]])
_Z = np.diag([1.0, -1.0]).astype(complex)
_CX = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
_CZ = np.diag([1, 1, 1, -1]).astype(complex)

ONE_QUBIT = {"h", "rz", "rx", "u3", "x", "y", "z", "s", "sdg", "t", "tdg", "u1", "u2"}
TWO_QUBIT = {"cx", "rzz", "cz"}


def gate_matrix(name, params=()):
    """Return the unitary of a named gate as a (2,2) or (4,4) array."""
    p = list(params)
    if name == "h":
        return _H.astype(complex)
    if name == "rz":
        return _rz(p[0])
    if name == "rx":
        return _rx(p[0])
    if name == "u3":
        return _u3(p[0], p[1], p[2])
    if name == "u2":
        return _u3(math.pi / 2, p[0], p[1])
    if name == "u1":
        return np.diag([1.0, np.exp(1j * p[0])])
    if name == "x":
        return _X
    if name == "y":
        return _Y
    if name == "z":
        return _Z
    if name == "s":
        return np.diag([1.0, 1j])
    if name == "sdg":
        return np.diag([1.0, -1j])
    if name == "t":
        return np.diag([1.0, np.exp(1j * math.pi / 4)])
    if name == "tdg":
        return np.diag([1.0, np.exp(-1j * math.pi / 4)])
    if name == "cx":
        return _CX
    if name == "cz":
        return _CZ
    if name == "rzz":
        t = p[0]
        return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t), np.exp(0.5j * t), np.exp(-0.5j * t)])
    raise ValueError("unknown gate: %s" % name)


# ---------------------------------------------------------------- state updates

def zero_state(n):
    psi = np.zeros((2,) * n, dtype=complex)
    psi[(0,) * n] = 1.0
    return psi


def apply_1q(psi, U, q):
    """Apply a 2x2 unitary to qubit q (axis q of psi)."""
    out = np.tensordot(U, psi, axes=([1], [q]))   # new axis 0 is qubit q
    return np.moveaxis(out, 0, q)


def apply_2q(psi, U, q1, q2):
    """Apply a 4x4 unitary in the |q1 q2> basis (q1 most significant)."""
    U4 = U.reshape(2, 2, 2, 2)                      # [out1, out2, in1, in2]
    out = np.tensordot(U4, psi, axes=([2, 3], [q1, q2]))
    return np.moveaxis(out, [0, 1], [q1, q2])


def apply_gate(psi, name, qubits, params=()):
    U = gate_matrix(name, params)
    if name in ONE_QUBIT:
        return apply_1q(psi, U, qubits[0])
    if name in TWO_QUBIT:
        return apply_2q(psi, U, qubits[0], qubits[1])
    raise ValueError("unknown gate: %s" % name)


def run(gates, n, psi=None):
    """Run a gate list on |0...0> (or on psi) and return the final state."""
    if psi is None:
        psi = zero_state(n)
    for name, qubits, params in gates:
        psi = apply_gate(psi, name, qubits, params)
    return psi


def probabilities(psi):
    """Z-basis outcome probabilities, index = sum_i b_i 2^(n-1-i)."""
    return np.abs(psi.reshape(-1)) ** 2


def unitary(gates, n):
    """Full 2^n x 2^n unitary of the circuit (small n only)."""
    dim = 2 ** n
    U = np.zeros((dim, dim), dtype=complex)
    for k in range(dim):
        psi = np.zeros(dim, dtype=complex)
        psi[k] = 1.0
        U[:, k] = run(gates, n, psi.reshape((2,) * n)).reshape(-1)
    return U


# ---------------------------------------------------------------- qasm parsing

_ANGLE_OK = re.compile(r"^[0-9.eE+\-*/() ]*(pi[0-9.eE+\-*/() ]*)*$")


def eval_angle(expr):
    """Evaluate an OpenQASM angle expression such as '-pi/2' or '2*0.1'."""
    expr = expr.strip()
    if not _ANGLE_OK.match(expr):
        raise ValueError("bad angle expression: %r" % expr)
    return float(eval(expr, {"__builtins__": {}}, {"pi": math.pi}))


_GATE_RE = re.compile(r"^(\w+)\s*(?:\(([^)]*)\))?\s*(.*)$")
_ARG_RE = re.compile(r"^(\w+)\[(\d+)\]$")


def parse_qasm(text):
    """Parse an OpenQASM 2.0 string. Returns (n_qubits, gates)."""
    regs = {}          # qreg name -> offset into the flat qubit index
    n = 0
    gates = []
    body = re.sub(r"//[^\n]*", "", text)
    for stmt in body.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        if stmt.startswith("OPENQASM") or stmt.startswith("include"):
            continue
        if stmt.startswith("qreg"):
            m = re.match(r"qreg\s+(\w+)\[(\d+)\]", stmt)
            regs[m.group(1)] = n
            n += int(m.group(2))
            continue
        if stmt.startswith(("creg", "measure", "barrier")):
            continue
        if stmt.startswith("gate "):
            raise ValueError("custom gate definitions are not supported")
        m = _GATE_RE.match(stmt)
        name, pstr, qstr = m.group(1), m.group(2), m.group(3)
        params = [eval_angle(p) for p in pstr.split(",")] if pstr else []
        qubits = []
        for a in qstr.split(","):
            am = _ARG_RE.match(a.strip())
            if am is None:
                raise ValueError("unsupported operand in: %r" % stmt)
            qubits.append(regs[am.group(1)] + int(am.group(2)))
        if name not in ONE_QUBIT and name not in TWO_QUBIT:
            raise ValueError("unsupported gate %r" % name)
        gates.append((name, qubits, params))
    return n, gates


def run_qasm(text):
    """Simulate a qasm string from |0...0>; returns the final state."""
    n, gates = parse_qasm(text)
    return run(gates, n)
