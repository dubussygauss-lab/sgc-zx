"""Density-matrix noisy simulator for Quantinuum native-gate circuits (numpy only).

Provisional stand-in for the H2-2E emulator.  Exact density-matrix
evolution for n <= 8 qubits with a simple parametric noise model.

Gate list format
----------------
A circuit is a flat Python list of tuples.  Angles are in HALF-TURNS,
exactly as pytket uses them (angle 1.0 means a rotation by pi).

    ("Rz", q, a)               Rz(a)          = exp(-i pi a Z / 2)
    ("PhasedX", q, a, b)       PhasedX(a, b)  = Rz(b) Rx(a) Rz(-b),
                                                Rx(a) = exp(-i pi a X / 2)
    ("ZZPhase", q0, q1, a)     ZZPhase(a)     = exp(-i pi a Z(x)Z / 2)
    ("ZZMax", q0, q1)          ZZMax          = ZZPhase(0.5)
    ("Measure", q)             terminal Z-basis measurement of qubit q

Raw gates accepted so that an unrebased OpenQASM-2 circuit can be
simulated with the same noise accounting (produced by qasm_to_gates):

    ("H", q)                   H  = (X + Z) / sqrt(2)
    ("Rx", q, a)               Rx(a) = exp(-i pi a X / 2)
    ("CX", q0, q1)             CNOT with control q0, target q1

Qubit/bitstring conventions
---------------------------
Qubits are integers 0..n-1.  Output bitstrings list the measured qubits
in ascending qubit index, qubit 0 leftmost (so the integer index of a
bitstring in the flat probability array is int(bitstring, 2) with the
first measured qubit as the most significant bit).  If a circuit contains
no "Measure" instruction every qubit is measured at the end.  Measured
qubits may not be acted on afterwards (measurements are terminal), and
unmeasured qubits are traced out.

Noise model (all probabilities, keyword arguments of NoiseModel)
----------------------------------------------------------------
    p1       single-qubit depolarising after every single-qubit gate:
             rho -> (1 - p1) rho + (p1/3) (X rho X + Y rho Y + Z rho Z)
             (with rz_virtual=True, default, Rz gates are noiseless and
             take no time, as Rz is a frame update on H-series)
    p2       two-qubit depolarising after every ZZPhase / ZZMax / CX:
             rho -> (1 - p2) rho + (p2/15) sum_{P != II} P rho P
             over the 15 non-identity two-qubit Paulis P = P_a (x) P_b
    p_spam   symmetric readout bit flip: each measured bit is flipped
             with probability p_spam, independently.  Setting p_spam sets
             both asymmetric rates below (p_meas_0 = p_meas_1 = p_spam)
             unless they are given explicitly.
    p_meas_0 asymmetric readout: a qubit whose outcome is 0 is read as 1
             with this probability (H2-2E "p_meas" first element)
    p_meas_1 asymmetric readout: a qubit whose outcome is 1 is read as 0
             with this probability (H2-2E "p_meas" second element)
    p_init   initialisation fault: every qubit starts in |1> instead of |0>
             with this probability, independently (bit-flip channel on the
             initial state, applied before any gate)
    p_idle   per-layer dephasing of every qubit NOT acted on in a layer:
             rho -> (1 - p_idle) rho + p_idle Z rho Z
             (off-diagonal elements of that qubit scale by 1 - 2 p_idle).
             Layers are built greedily (ASAP): a gate goes in the first
             layer after the last layer of any of its qubits.  Virtual
             Rz gates and measurements do not occupy a layer.

p1 and p2 default to None and must be given explicitly for a noisy run,
and so must the readout error, either as p_spam or as both p_meas_0 and
p_meas_1; p_idle and p_init default to 0.  A NoiseModel() with everything
None is "noise off" and reproduces the exact ideal evolution.

What is NOT modelled of the H2-2E emulator noise model (docs/platform_notes.md
section 3.2): the spontaneous-emission branch of the gate errors (X / Y /
leakage with the p1_emission_ratio, p2_emission_ratio weights), because
leakage needs a third level per qubit; the RZZ angle dependence of p2; the
measurement and initialisation crosstalk; and the memory (dephasing) error,
whose quadratic and linear rates are per unit idle/transport time, which
this simulator cannot convert into per-gate probabilities because it has no
gate-duration or transport model (p_idle is a per-layer stand-in only).

State representation
--------------------
rho is stored as a complex tensor of shape (2,)*2n; axis q is the ket
index of qubit q and axis n+q its bra index.  A unitary U is applied as
rho -> U rho U^dagger by one tensordot on the ket axes and one on the
bra axes.  The depolarising channels use the exact identities
    (1-p) rho + (p/3)  sum_{P=X,Y,Z} P rho P = (1-4p/3)  rho + (4p/3)  I/2 (x) tr_q rho
    (1-p) rho + (p/15) sum_{P!=II}   P rho P = (1-16p/15) rho + (16p/15) I/4 (x) tr_{q0q1} rho
(partial trace, then tensor with the maximally mixed state); the literal
Pauli sums are kept as depolarise_*_pauli_sum for reference and are tested
to agree.  Dephasing is the explicit two-term sum.  The evolution is exact
to floating-point rounding; no sampling is used except in sample().

Main entry points
-----------------
    simulate(gates, noise)          -> probability dict/array (one run)
    run(gates, noise, success=...)  -> SimResult with ideal + noisy
                                       distributions and metrics
    sample(probs, shots, seed)      -> finite-shot counts
    qasm_to_gates(qasm_text)        -> gate list from a QASM-2 subset
"""

import ast
import math
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

MAX_QUBITS = 8

Gate = tuple

# --------------------------------------------------------------------------
# Elementary matrices (pytket conventions, half-turn angles)
# --------------------------------------------------------------------------

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = (X + Z) / math.sqrt(2)
PAULIS = (I2, X, Y, Z)


def rz(a):
    """Rz(a) = exp(-i pi a Z / 2)."""
    ph = np.exp(-0.5j * math.pi * a)
    return np.array([[ph, 0], [0, np.conj(ph)]], dtype=complex)


def rx(a):
    """Rx(a) = exp(-i pi a X / 2)."""
    c, s = math.cos(math.pi * a / 2), math.sin(math.pi * a / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def phasedx(a, b):
    """PhasedX(a, b) = Rz(b) Rx(a) Rz(-b)."""
    return rz(b) @ rx(a) @ rz(-b)


def zzphase(a):
    """ZZPhase(a) = exp(-i pi a Z(x)Z / 2), as a 4x4 matrix (q0 is the
    most significant index)."""
    ph = np.exp(-0.5j * math.pi * a)
    return np.diag([ph, np.conj(ph), np.conj(ph), ph]).astype(complex)


def zzmax():
    """ZZMax = ZZPhase(0.5)."""
    return zzphase(0.5)


CX = np.array([[1, 0, 0, 0],
               [0, 1, 0, 0],
               [0, 0, 0, 1],
               [0, 0, 1, 0]], dtype=complex)

# the 15 non-identity two-qubit Paulis P_a (x) P_b as 4x4 matrices
TWO_QUBIT_PAULIS = [np.kron(Pa, Pb) for Pa in PAULIS for Pb in PAULIS][1:]


def gate_unitary(g):
    """Return (matrix, qubits) for a gate tuple; None for Measure."""
    name = g[0]
    if name == "Rz":
        return rz(g[2]), (g[1],)
    if name == "PhasedX":
        return phasedx(g[2], g[3]), (g[1],)
    if name == "Rx":
        return rx(g[2]), (g[1],)
    if name == "H":
        return H, (g[1],)
    if name == "ZZPhase":
        return zzphase(g[3]), (g[1], g[2])
    if name == "ZZMax":
        return zzmax(), (g[1], g[2])
    if name == "CX":
        return CX, (g[1], g[2])
    if name == "Measure":
        return None, (g[1],)
    raise ValueError("unknown gate %r" % (g,))


def gate_qubits(g):
    return gate_unitary(g)[1]


# --------------------------------------------------------------------------
# Density-matrix primitives
# --------------------------------------------------------------------------

def initial_state(n):
    """|0...0><0...0| as a (2,)*2n tensor."""
    rho = np.zeros((2,) * (2 * n), dtype=complex)
    rho[(0,) * (2 * n)] = 1.0
    return rho


def apply_1q(rho, U, q, n):
    """rho -> (U on qubit q) rho (U on qubit q)^dagger."""
    rho = np.moveaxis(np.tensordot(U, rho, axes=([1], [q])), 0, q)
    rho = np.moveaxis(np.tensordot(U.conj(), rho, axes=([1], [n + q])), 0, n + q)
    return rho


def apply_2q(rho, U4, q0, q1, n):
    """rho -> U rho U^dagger with U a 4x4 matrix on qubits (q0, q1),
    q0 being the most significant index of U."""
    T = U4.reshape(2, 2, 2, 2)
    rho = np.moveaxis(np.tensordot(T, rho, axes=([2, 3], [q0, q1])), [0, 1], [q0, q1])
    rho = np.moveaxis(np.tensordot(T.conj(), rho, axes=([2, 3], [n + q0, n + q1])),
                      [0, 1], [n + q0, n + q1])
    return rho


def replace_with_maximally_mixed(rho, qubits, n):
    """Return (I/2^k on `qubits`) (x) tr_{qubits} rho, k = len(qubits)."""
    k = len(qubits)
    ket = list(qubits)
    bra = [n + q for q in qubits]
    moved = np.moveaxis(rho, ket + bra, list(range(2 * k)))
    rest = moved.shape[2 * k:]
    reduced = np.trace(moved.reshape(2 ** k, 2 ** k, -1), axis1=0, axis2=1).reshape(rest)
    Ik = (np.eye(2 ** k, dtype=complex) / 2 ** k).reshape((2,) * (2 * k))
    out = np.tensordot(Ik, reduced, axes=0)
    return np.moveaxis(out, list(range(2 * k)), ket + bra)


def depolarise_1q(rho, p, q, n):
    """rho -> (1-p) rho + (p/3) (X rho X + Y rho Y + Z rho Z)
           = (1 - 4p/3) rho + (4p/3) (I/2 (x) tr_q rho)."""
    if p == 0:
        return rho
    return (1 - 4 * p / 3) * rho + (4 * p / 3) * replace_with_maximally_mixed(rho, (q,), n)


def depolarise_2q(rho, p, q0, q1, n):
    """rho -> (1-p) rho + (p/15) sum_{P != II} P rho P
           = (1 - 16p/15) rho + (16p/15) (I/4 (x) tr_{q0 q1} rho)."""
    if p == 0:
        return rho
    return (1 - 16 * p / 15) * rho + (16 * p / 15) * replace_with_maximally_mixed(rho, (q0, q1), n)


def depolarise_1q_pauli_sum(rho, p, q, n):
    """Reference implementation of depolarise_1q as the explicit Pauli sum."""
    out = (1 - p) * rho
    for P in (X, Y, Z):
        out = out + (p / 3) * apply_1q(rho, P, q, n)
    return out


def depolarise_2q_pauli_sum(rho, p, q0, q1, n):
    """Reference implementation of depolarise_2q as the explicit 15-Pauli sum."""
    out = (1 - p) * rho
    for P in TWO_QUBIT_PAULIS:
        out = out + (p / 15) * apply_2q(rho, P, q0, q1, n)
    return out


def dephase_1q(rho, p, q, n):
    """rho -> (1-p) rho + p Z rho Z."""
    if p == 0:
        return rho
    return (1 - p) * rho + p * apply_1q(rho, Z, q, n)


def probabilities(rho, n, measured):
    """Diagonal of rho, traced over unmeasured qubits, as a (2,)*m tensor
    ordered by ascending measured qubit index."""
    diag = np.real(np.diagonal(rho.reshape(2 ** n, 2 ** n))).reshape((2,) * n)
    keep = sorted(measured)
    drop = tuple(q for q in range(n) if q not in keep)
    if drop:
        diag = diag.sum(axis=drop)
    return diag


def spam_flip(ptensor, p, p1=None):
    """Apply the readout bit-flip channel to every axis of a probability
    tensor: a true 0 is read as 1 with probability p, a true 1 is read as 0
    with probability p1 (default p1 = p, the symmetric channel
    [[1-p, p], [p, 1-p]]).  M[read, true]."""
    if p1 is None:
        p1 = p
    if p == 0 and p1 == 0:
        return ptensor
    M = np.array([[1 - p, p1], [p, 1 - p1]])
    for ax in range(ptensor.ndim):
        ptensor = np.moveaxis(np.tensordot(M, ptensor, axes=([1], [ax])), 0, ax)
    return ptensor


def init_flip(rho, p, n):
    """Initialisation fault: rho -> (1-p) rho + p X rho X on every qubit
    (applied to |0..0><0..0| this gives the product state with each qubit
    |1><1| with probability p)."""
    if p == 0:
        return rho
    for q in range(n):
        rho = (1 - p) * rho + p * apply_1q(rho, X, q, n)
    return rho


# --------------------------------------------------------------------------
# Noise model and layering
# --------------------------------------------------------------------------

@dataclass
class NoiseModel:
    p1: Optional[float] = None       # 1q depolarising after each 1q gate
    p2: Optional[float] = None       # 2q depolarising after each 2q gate
    p_spam: Optional[float] = None   # symmetric readout flip (sets both below)
    p_idle: float = 0.0              # per-layer dephasing of idle qubits
    rz_virtual: bool = True          # Rz is noiseless and takes no time
    p_meas_0: Optional[float] = None  # 0 read as 1
    p_meas_1: Optional[float] = None  # 1 read as 0
    p_init: float = 0.0              # initial |0> -> |1> flip probability

    def is_off(self):
        return (self.p1 is None and self.p2 is None and self.p_spam is None
                and self.p_meas_0 is None and self.p_meas_1 is None
                and not self.p_idle and not self.p_init)

    def readout(self):
        """(p_meas_0, p_meas_1) actually used: explicit values win, p_spam
        fills in whichever is missing."""
        a = self.p_spam if self.p_meas_0 is None else self.p_meas_0
        b = self.p_spam if self.p_meas_1 is None else self.p_meas_1
        return a, b

    def check(self):
        if self.is_off():
            return
        for name in ("p1", "p2"):
            v = getattr(self, name)
            if v is None:
                raise ValueError("NoiseModel.%s must be a number for a noisy run" % name)
            if not (0 <= v <= 1):
                raise ValueError("NoiseModel.%s out of [0, 1]" % name)
        for name, v in zip(("p_meas_0", "p_meas_1"), self.readout()):
            if v is None:
                raise ValueError("NoiseModel.%s (or p_spam) must be a number for a noisy run" % name)
            if not (0 <= v <= 1):
                raise ValueError("NoiseModel.%s out of [0, 1]" % name)
        for name in ("p_idle", "p_init"):
            if not (0 <= getattr(self, name) <= 1):
                raise ValueError("NoiseModel.%s out of [0, 1]" % name)


NOISE_OFF = NoiseModel()


def infer_n(gates):
    qs = [q for g in gates for q in gate_qubits(g)]
    return (max(qs) + 1) if qs else 1


def assign_layers(gates, rz_virtual=True):
    """Greedy ASAP layering.  Returns a list of layer numbers (one per gate).
    Timed gates get layers 1, 2, ...; virtual Rz gates and measurements
    get the layer of the last timed gate on their qubit (0 if none), so
    they never occupy a layer of their own."""
    last = {}
    layers = []
    for g in gates:
        qs = gate_qubits(g)
        timed = not (g[0] == "Measure" or (g[0] == "Rz" and rz_virtual))
        prev = max(last.get(q, 0) for q in qs)
        if timed:
            L = prev + 1
            for q in qs:
                last[q] = L
        else:
            L = prev
        layers.append(L)
    return layers


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

def _check_circuit(gates, n):
    if n > MAX_QUBITS:
        raise ValueError("n = %d exceeds MAX_QUBITS = %d" % (n, MAX_QUBITS))
    measured = set()
    for g in gates:
        qs = gate_qubits(g)
        for q in qs:
            if not (0 <= q < n):
                raise ValueError("qubit %d out of range in %r" % (q, g))
            if q in measured:
                raise ValueError("qubit %d used after its measurement in %r" % (q, g))
        if len(qs) == 2 and qs[0] == qs[1]:
            raise ValueError("two-qubit gate on the same qubit twice: %r" % (g,))
        if g[0] == "Measure":
            measured.add(qs[0])
    if not measured:
        measured = set(range(n))
    return sorted(measured)


def final_density_matrix(gates, noise=NOISE_OFF, n=None):
    """Evolve |0..0> through the gate list (noise channels included) and
    return (rho as a 2^n x 2^n matrix, list of measured qubits)."""
    noise.check()
    if n is None:
        n = infer_n(gates)
    measured = _check_circuit(gates, n)
    off = noise.is_off()
    p1 = 0.0 if off else noise.p1
    p2 = 0.0 if off else noise.p2
    p_idle = 0.0 if off else noise.p_idle
    p_init = 0.0 if off else noise.p_init

    # Order gates by layer (stable, so same-qubit order is kept; gates in
    # one layer act on disjoint qubits and commute), then run layer by layer
    # and dephase the idle qubits at the end of each timed layer.
    layers = assign_layers(gates, noise.rz_virtual)
    order = sorted(range(len(gates)), key=lambda i: layers[i])
    rho = init_flip(initial_state(n), p_init, n)
    n_layers = max(layers) if layers else 0
    busy = {L: set() for L in range(n_layers + 1)}
    for i, L in enumerate(layers):
        busy[L].update(gate_qubits(gates[i]))

    current = 0
    for i in order:
        g, L = gates[i], layers[i]
        while current < L:
            if current >= 1 and p_idle:
                for q in range(n):
                    if q not in busy[current]:
                        rho = dephase_1q(rho, p_idle, q, n)
            current += 1
        U, qs = gate_unitary(g)
        if U is None:
            continue
        if len(qs) == 1:
            rho = apply_1q(rho, U, qs[0], n)
            if not (g[0] == "Rz" and noise.rz_virtual):
                rho = depolarise_1q(rho, p1, qs[0], n)
        else:
            rho = apply_2q(rho, U, qs[0], qs[1], n)
            rho = depolarise_2q(rho, p2, qs[0], qs[1], n)
    # dephase idle qubits of the final layer
    if n_layers >= 1 and p_idle:
        for q in range(n):
            if q not in busy[n_layers]:
                rho = dephase_1q(rho, p_idle, q, n)
    return rho.reshape(2 ** n, 2 ** n), measured


def simulate(gates, noise=NOISE_OFF, n=None, tol=1e-15):
    """Return (probs array of length 2^m, probs dict, measured qubits) for
    one run; m = number of measured qubits.  Probabilities below `tol`
    (rounding residue of exact zeros) are set to 0 and the array is
    renormalised."""
    noise.check()
    if n is None:
        n = infer_n(gates)
    rho, measured = final_density_matrix(gates, noise, n)
    pt = probabilities(rho.reshape((2,) * (2 * n)), n, measured)
    if not noise.is_off():
        pt = spam_flip(pt, *noise.readout())
    probs = pt.reshape(-1)
    probs = np.where(probs < tol, 0.0, probs)
    probs = probs / probs.sum()
    return probs, probs_to_dict(probs), measured


# --------------------------------------------------------------------------
# Distributions and metrics
# --------------------------------------------------------------------------

def bitstrings(m):
    return [format(i, "0%db" % m) for i in range(2 ** m)]


def probs_to_dict(probs, drop_zero=True):
    m = int(round(math.log2(len(probs))))
    bs = bitstrings(m)
    return {b: float(p) for b, p in zip(bs, probs) if (p > 0 or not drop_zero)}


def dict_to_probs(d, m):
    probs = np.zeros(2 ** m)
    for b, p in d.items():
        probs[int(b, 2)] = p
    return probs


def hellinger_fidelity(p, q):
    """F_H = (sum_i sqrt(p_i q_i))^2."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    return float(np.sum(np.sqrt(p * q)) ** 2)


def total_variation(p, q):
    """TVD = (1/2) sum_i |p_i - q_i|."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    return float(0.5 * np.sum(np.abs(p - q)))


def success_probability(probs, success, m=None):
    """Probability mass on the bitstrings in `success` (iterable of strings
    or integer indices)."""
    probs = np.asarray(probs, float)
    if m is None:
        m = int(round(math.log2(len(probs))))
    idx = [int(s, 2) if isinstance(s, str) else int(s) for s in success]
    return float(probs[idx].sum()) if idx else 0.0


def metrics(ideal, noisy, success=None):
    out = {"hellinger_fidelity": hellinger_fidelity(ideal, noisy),
           "tvd": total_variation(ideal, noisy)}
    if success is not None:
        out["success_ideal"] = success_probability(ideal, success)
        out["success_noisy"] = success_probability(noisy, success)
    return out


def sample(probs, shots, seed=0):
    """Draw `shots` samples from a probability array; returns a dict
    bitstring -> count (zero counts omitted)."""
    rng = np.random.default_rng(seed)
    probs = np.asarray(probs, float)
    counts = rng.multinomial(shots, probs / probs.sum())
    m = int(round(math.log2(len(probs))))
    return {b: int(c) for b, c in zip(bitstrings(m), counts) if c > 0}


def counts_to_probs(counts, m):
    probs = np.zeros(2 ** m)
    for b, c in counts.items():
        probs[int(b, 2)] += c
    return probs / probs.sum()


def metrics_from_counts(ideal, counts, success=None):
    m = int(round(math.log2(len(ideal))))
    return metrics(ideal, counts_to_probs(counts, m), success)


@dataclass
class SimResult:
    n: int
    measured: List[int]
    ideal: np.ndarray
    noisy: np.ndarray
    ideal_dict: Dict[str, float]
    noisy_dict: Dict[str, float]
    metrics: Dict[str, float] = field(default_factory=dict)
    counts: Optional[Dict[str, int]] = None
    metrics_sampled: Optional[Dict[str, float]] = None


def run(gates, noise, success=None, n=None, shots=None, seed=0):
    """Ideal and noisy distributions plus metrics.  If `shots` is given,
    also sample the noisy distribution and compute metrics from counts."""
    if n is None:
        n = infer_n(gates)
    ideal, ideal_d, measured = simulate(gates, NOISE_OFF, n)
    noisy, noisy_d, _ = simulate(gates, noise, n)
    res = SimResult(n, measured, ideal, noisy, ideal_d, noisy_d,
                    metrics(ideal, noisy, success))
    if shots:
        res.counts = sample(noisy, shots, seed)
        res.metrics_sampled = metrics_from_counts(ideal, res.counts, success)
    return res


# --------------------------------------------------------------------------
# OpenQASM-2 subset parser (h, rz, rx, cx, rzz, measure); no rebasing
# --------------------------------------------------------------------------

_QASM_ANGLE_OK = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
                  ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)


def _eval_angle(expr):
    """Evaluate a QASM angle expression (radians) using only + - * / ** and pi."""
    tree = ast.parse(expr.strip(), mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _QASM_ANGLE_OK):
            raise ValueError("unsupported angle expression %r" % expr)
        if isinstance(node, ast.Name) and node.id != "pi":
            raise ValueError("unknown symbol %r in angle" % node.id)
    return float(eval(compile(tree, "<angle>", "eval"), {"__builtins__": {}}, {"pi": math.pi}))


_ARG = re.compile(r"^\s*(\w+)\s*\[\s*(\d+)\s*\]\s*$")


def _qidx(tok):
    m = _ARG.match(tok)
    if not m:
        raise ValueError("bad qubit argument %r" % tok)
    return int(m.group(2))


def qasm_to_gates(text):
    """Parse a small OpenQASM-2 subset into the gate-tuple list.

    Supported: OPENQASM/include/qreg/creg/barrier lines (ignored or used for
    sizing), h, rz(t), rx(t), cx, rzz(t), measure q[i] -> c[j] and the
    whole-register form `measure q -> c`.  Angles are radians in QASM and
    are converted to half-turns (t / pi).  Returns (gates, n).  Note that
    the classical register index of a measurement is ignored: outputs are
    ordered by qubit index."""
    gates = []
    n = 0
    body = re.sub(r"//.*", "", text)
    for stmt in body.split(";"):
        s = stmt.strip()
        if not s:
            continue
        if s.startswith("OPENQASM") or s.startswith("include"):
            continue
        m = re.match(r"^(\w+)\s*(\(([^)]*)\))?\s*(.*)$", s, re.S)
        if not m:
            raise ValueError("cannot parse %r" % s)
        op, params, args = m.group(1), m.group(3), m.group(4)
        if op == "qreg":
            n = int(_ARG.match(args).group(2))
            continue
        if op in ("creg", "barrier"):
            continue
        if op == "measure":
            left = args.split("->")[0].strip()
            if _ARG.match(left):
                gates.append(("Measure", _qidx(left)))
            else:
                for q in range(n):
                    gates.append(("Measure", q))
            continue
        qs = [_qidx(t) for t in args.split(",")]
        if op == "h":
            gates.append(("H", qs[0]))
        elif op == "rz":
            gates.append(("Rz", qs[0], _eval_angle(params) / math.pi))
        elif op == "rx":
            gates.append(("Rx", qs[0], _eval_angle(params) / math.pi))
        elif op == "cx":
            gates.append(("CX", qs[0], qs[1]))
        elif op == "rzz":
            gates.append(("ZZPhase", qs[0], qs[1], _eval_angle(params) / math.pi))
        else:
            raise ValueError("unsupported QASM op %r" % op)
    if n == 0:
        n = infer_n(gates)
    return gates, n


# --------------------------------------------------------------------------
# Small helpers for checks
# --------------------------------------------------------------------------

def circuit_unitary(gates, n=None):
    """Full 2^n x 2^n unitary of the gate list (ideal, Measure ignored).
    Qubit 0 is the most significant index."""
    if n is None:
        n = infer_n(gates)
    U_full = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for col in range(2 ** n):
        psi = np.zeros(2 ** n, dtype=complex)
        psi[col] = 1.0
        psi = psi.reshape((2,) * n)
        for g in gates:
            U, qs = gate_unitary(g)
            if U is None:
                continue
            if len(qs) == 1:
                psi = np.moveaxis(np.tensordot(U, psi, axes=([1], [qs[0]])), 0, qs[0])
            else:
                T = U.reshape(2, 2, 2, 2)
                psi = np.moveaxis(np.tensordot(T, psi, axes=([2, 3], list(qs))), [0, 1], list(qs))
        U_full[:, col] = psi.reshape(-1)
    return U_full


def random_native_circuit(n, n_gates, seed=0, measure=True):
    """Random circuit in the native gate set, for timing and cross-checks."""
    rng = np.random.default_rng(seed)
    gates = []
    for _ in range(n_gates):
        kind = rng.integers(3)
        if kind == 0:
            gates.append(("Rz", int(rng.integers(n)), float(rng.uniform(-1, 1))))
        elif kind == 1:
            gates.append(("PhasedX", int(rng.integers(n)), float(rng.uniform(-1, 1)),
                          float(rng.uniform(-1, 1))))
        else:
            q0, q1 = [int(x) for x in rng.choice(n, 2, replace=False)]
            if rng.integers(2):
                gates.append(("ZZMax", q0, q1))
            else:
                gates.append(("ZZPhase", q0, q1, float(rng.uniform(-1, 1))))
    if measure:
        gates += [("Measure", q) for q in range(n)]
    return gates
