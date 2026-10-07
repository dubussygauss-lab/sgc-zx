"""Per-instance exactness-barrier certificates for Clifford+T circuits.

Implements, in pure Python + numpy (object dtype, exact integers), the
quantities defined in Kam et al., "An Exactness Barrier for ZX-Calculus
Optimization of Synthesized Clifford+T Circuits" (main.tex):

  * exact arithmetic in Z[omega], omega = exp(i pi/4), and matrices over
    D[omega] = Z[omega][1/sqrt2] stored as (M, k) meaning M / sqrt2^k;
    sde = least such k (Table tab:barrier diagnostic);
  * matrices over Z[sqrt2] stored as (P + Q sqrt2)/sqrt2^e, Eq. (ringform),
    with the reduction criterion P == 0 mod 2, Eq. (redcrit); lde = least e;
  * the exact SO(3) Bloch representation (Lemma bridge) and the n-qubit
    Pauli-channel representation (Sec. multiqubit), accumulated gate by
    gate with the structured accumulator (Sec. numerics, Methods);
  * the floor of Theorem B(a) / Corollary cert, the per-step collapse
    bookkeeping of Lemma mqval(b) / Theorem C(b), the bound of Theorem C(c);
  * the single-qubit linkage procedure of Theorem linkage;
  * the mod-2 residue automaton of Lemma valuation;
  * a small OpenQASM-2 parser for the gate subset h s sdg t tdg x y z cx cz.

Conventions (see NOTES.md):
  A word is a Python list of gates; the unitary of the word is the matrix
  product in list order, U = g_1 g_2 ... g_t (so g_t acts first in time),
  matching the paper's W = g_1 ... g_t and V_j = g_1 ... g_j.  QASM input
  is in time order and is reversed by certificate_from_qasm.
  Basis index of an n-qubit register: sum_q b_q 2^q (qubit 0 = least
  significant bit).  Pauli index: sum_q 4^q p_q with p in {0:I,1:X,2:Y,3:Z}.
"""

from __future__ import annotations

import math
import re
from collections import deque
from functools import lru_cache

import numpy as np


# ---------------------------------------------------------------------------
# Z[omega]
# ---------------------------------------------------------------------------

class Zw:
    """a + b w + c w^2 + d w^3 with w = exp(i pi/4), w^4 = -1, Python ints."""

    __slots__ = ("a", "b", "c", "d")

    def __init__(self, a=0, b=0, c=0, d=0):
        self.a, self.b, self.c, self.d = int(a), int(b), int(c), int(d)

    def coeffs(self):
        return (self.a, self.b, self.c, self.d)

    def __add__(self, o):
        if isinstance(o, int):
            return Zw(self.a + o, self.b, self.c, self.d)
        if not isinstance(o, Zw):
            return NotImplemented
        return Zw(self.a + o.a, self.b + o.b, self.c + o.c, self.d + o.d)

    __radd__ = __add__

    def __sub__(self, o):
        if isinstance(o, int):
            return Zw(self.a - o, self.b, self.c, self.d)
        if not isinstance(o, Zw):
            return NotImplemented
        return Zw(self.a - o.a, self.b - o.b, self.c - o.c, self.d - o.d)

    def __neg__(self):
        return Zw(-self.a, -self.b, -self.c, -self.d)

    def __mul__(self, o):
        if isinstance(o, int):
            return Zw(self.a * o, self.b * o, self.c * o, self.d * o)
        if not isinstance(o, Zw):
            return NotImplemented
        a0, a1, a2, a3 = self.a, self.b, self.c, self.d
        b0, b1, b2, b3 = o.a, o.b, o.c, o.d
        return Zw(a0 * b0 - a1 * b3 - a2 * b2 - a3 * b1,
                  a0 * b1 + a1 * b0 - a2 * b3 - a3 * b2,
                  a0 * b2 + a1 * b1 + a2 * b0 - a3 * b3,
                  a0 * b3 + a1 * b2 + a2 * b1 + a3 * b0)

    __rmul__ = __mul__

    def __eq__(self, o):
        if isinstance(o, int):
            o = Zw(o)
        if not isinstance(o, Zw):
            return NotImplemented
        return self.coeffs() == o.coeffs()

    def __hash__(self):
        return hash(self.coeffs())

    def __bool__(self):
        return any(self.coeffs())

    def conj(self):
        # conj(w) = w^7 = -w^3, conj(w^2) = -w^2, conj(w^3) = -w
        return Zw(self.a, -self.d, -self.c, -self.b)

    def divisible_by_sqrt2(self):
        # Z[w]/(sqrt2) = F_2[x]/(x^2 - 1): image is (a+c) + (b+d) x mod 2.
        return (self.a - self.c) % 2 == 0 and (self.b - self.d) % 2 == 0

    def div_sqrt2(self):
        # x / sqrt2 = x (w - w^3) / 2
        if not self.divisible_by_sqrt2():
            raise ValueError("not divisible by sqrt2: %r" % (self,))
        a, b, c, d = self.coeffs()
        return Zw((b - d) // 2, (a + c) // 2, (b + d) // 2, (c - a) // 2)

    def real_sqrt2(self):
        """Return (p, q) with self = p + q sqrt2; raise if not real."""
        if self.c != 0 or self.b + self.d != 0:
            raise ValueError("not real: %r" % (self,))
        return (self.a, self.b)

    def to_complex(self):
        s = 1 / math.sqrt(2)
        return (self.a + self.b * complex(s, s) + self.c * 1j
                + self.d * complex(-s, s))

    def __repr__(self):
        return "Zw(%d,%d,%d,%d)" % self.coeffs()


ZERO = Zw(0)
ONE = Zw(1)
OMEGA = Zw(0, 1, 0, 0)
IUNIT = Zw(0, 0, 1, 0)          # i = w^2
SQRT2 = Zw(0, 1, 0, -1)         # sqrt2 = w - w^3 = w + w^{-1}


def zw_matrix(rows):
    """List of lists of Zw/int -> object ndarray of Zw."""
    M = np.empty((len(rows), len(rows[0])), dtype=object)
    for i, r in enumerate(rows):
        for j, x in enumerate(r):
            M[i, j] = x if isinstance(x, Zw) else Zw(x)
    return M


def zw_eye(N):
    M = np.empty((N, N), dtype=object)
    M[:] = ZERO
    for i in range(N):
        M[i, i] = ONE
    return M


# ---------------------------------------------------------------------------
# Gate table: exact matrices over D[omega] as (M, k) meaning M / sqrt2^k.
# Two-qubit gates use local index b0 + 2 b1, local qubit 0 = first argument.
# ---------------------------------------------------------------------------

W2 = OMEGA * OMEGA              # i
W3 = W2 * OMEGA
W6 = -W2                        # -i
W7 = -W3                        # conj(w)

GATES = {
    # name: (rows, k, arity)
    "h":    ([[1, 1], [1, -1]], 1, 1),
    "s":    ([[1, 0], [0, W2]], 0, 1),
    "sdg":  ([[1, 0], [0, W6]], 0, 1),
    "t":    ([[1, 0], [0, OMEGA]], 0, 1),
    "tdg":  ([[1, 0], [0, W7]], 0, 1),
    "x":    ([[0, 1], [1, 0]], 0, 1),
    "y":    ([[0, W6], [W2, 0]], 0, 1),
    "z":    ([[1, 0], [0, -1]], 0, 1),
    "id":   ([[1, 0], [0, 1]], 0, 1),
    "cx":   ([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], 0, 2),
    "cz":   ([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], 0, 2),
    "swap": ([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], 0, 2),
}

ALIASES = {"H": "h", "S": "s", "Sdg": "sdg", "S†": "sdg", "T": "t",
           "Tdg": "tdg", "T†": "tdg", "X": "x", "Y": "y", "Z": "z",
           "CX": "cx", "CNOT": "cx", "cnot": "cx", "CZ": "cz", "SWAP": "swap",
           "I": "id", "ID": "id"}

# phase in units of pi/4 (map phi of Sec. prelim), for Z-rotation letters
PHASE = {"t": 1, "s": 2, "z": 4, "sdg": 6, "tdg": 7, "id": 0}
T_TYPE = {"t", "tdg"}           # the pi/8 rotations R_S with S = Z on a wire


def gate_name(name):
    n = ALIASES.get(name, name.lower())
    if n not in GATES:
        raise ValueError("unknown gate %r" % (name,))
    return n


@lru_cache(maxsize=None)
def gate_matrix(name):
    rows, k, _ = GATES[gate_name(name)]
    return zw_matrix(rows), k


def normalize_word(word, n=None):
    """Accept 'HTSH', ['H','T'], [('h',(0,)),('cx',(0,1))]; return
    (list of (name, qubits)), n)."""
    out = []
    maxq = -1
    if isinstance(word, str):
        word = list(word)
    for g in word:
        if isinstance(g, str):
            out.append((gate_name(g), (0,)))
        else:
            name, qs = g
            qs = tuple(int(q) for q in (qs if isinstance(qs, (tuple, list)) else (qs,)))
            name = gate_name(name)
            if len(qs) != GATES[name][2]:
                raise ValueError("gate %s takes %d qubits" % (name, GATES[name][2]))
            out.append((name, qs))
        maxq = max(maxq, *out[-1][1])
    if n is None:
        n = max(maxq + 1, 1)
    if maxq >= n:
        raise ValueError("gate on qubit %d but n = %d" % (maxq, n))
    return out, n


def t_count(word):
    w, _ = normalize_word(word)
    return sum(1 for name, _ in w if name in T_TYPE)


# ---------------------------------------------------------------------------
# Local right-multiplication X -> X . (G (x) I) on the column index,
# column index = sum_q base^q p_q, local index = sum_j base^j p_{q_j}.
# ---------------------------------------------------------------------------

def _local_right_mult(X, G, qubits, n, base):
    m = len(qubits)
    N = base ** n
    Xt = X.reshape((N,) + (base,) * n)
    axes = [1 + (n - 1 - q) for q in qubits]
    Xt = np.moveaxis(Xt, list(reversed(axes)), list(range(-m, 0)))
    shape = Xt.shape
    Y = np.dot(Xt.reshape(-1, base ** m), G).reshape(shape)
    Y = np.moveaxis(Y, list(range(-m, 0)), list(reversed(axes)))
    return np.ascontiguousarray(Y).reshape(N, N)


# ---------------------------------------------------------------------------
# Unitaries over D[omega]: (M, k) with M over Z[omega], U = M / sqrt2^k.
# ---------------------------------------------------------------------------

class DMat:
    def __init__(self, M, k, n):
        self.M, self.k, self.n = M, int(k), int(n)

    def copy(self):
        return DMat(self.M.copy(), self.k, self.n)

    def reduce(self):
        """Lower k while every entry is divisible by sqrt2 (and k > 0)."""
        while self.k > 0 and all(x.divisible_by_sqrt2() for x in self.M.flat):
            self.M = np.array([[x.div_sqrt2() for x in row] for row in self.M],
                              dtype=object).reshape(self.M.shape)
            self.k -= 1
        return self

    @property
    def sde(self):
        return self.k

    def to_complex(self):
        C = np.array([[x.to_complex() for x in row] for row in self.M],
                     dtype=complex).reshape(self.M.shape)
        return C / math.sqrt(2) ** self.k

    def dagger(self):
        Md = np.array([[x.conj() for x in row] for row in self.M.T],
                      dtype=object).reshape(self.M.T.shape)
        return DMat(Md, self.k, self.n)


def identity_unitary(n):
    return DMat(zw_eye(2 ** n), 0, n)


def apply_gate(U, name, qubits):
    """U <- U . g  (right multiplication, word order), then reduce."""
    G, kg = gate_matrix(name)
    M = _local_right_mult(U.M, G, qubits, U.n, 2)
    return DMat(M, U.k + kg, U.n).reduce()


def word_unitary(word, n=None):
    w, n = normalize_word(word, n)
    U = identity_unitary(n)
    for name, qs in w:
        U = apply_gate(U, name, qs)
    return U


def sde_entrywise(U):
    """Per-entry sde of U = M/sqrt2^k: k minus the sqrt2-adic valuation of
    the entry (None for a zero entry).  Diagnostic only; not used by any
    certificate in the paper."""
    out = np.empty(U.M.shape, dtype=object)
    for idx, x in np.ndenumerate(U.M):
        if not x:
            out[idx] = None
            continue
        v = 0
        while x.divisible_by_sqrt2():
            x = x.div_sqrt2()
            v += 1
        out[idx] = U.k - v
    return out


# ---------------------------------------------------------------------------
# Matrices over Z[sqrt2]: (P + Q sqrt2) / sqrt2^e, Eq. (ringform)
# ---------------------------------------------------------------------------

def _obj(A):
    out = np.empty(np.shape(A), dtype=object)
    out[...] = np.asarray(A, dtype=object)
    return out


class RMat:
    def __init__(self, P, Q, e):
        self.P, self.Q, self.e = _obj(P), _obj(Q), int(e)

    def reduce(self):
        """Eq. (redcrit): while P == 0 mod 2 entrywise, (P,Q) <- (Q, P/2)."""
        while self.e > 0 and not np.any(self.P % 2):
            self.P, self.Q = self.Q, self.P // 2
            self.e -= 1
        return self

    @property
    def lde(self):
        return self.e

    def key(self):
        return (self.e, tuple(self.P.flat), tuple(self.Q.flat))

    def to_float(self):
        return (self.P.astype(float) + math.sqrt(2) * self.Q.astype(float)) / math.sqrt(2) ** self.e

    def copy(self):
        return RMat(self.P.copy(), self.Q.copy(), self.e)

    def __matmul__(self, o):
        P = np.dot(self.P, o.P) + 2 * np.dot(self.Q, o.Q)
        Q = np.dot(self.P, o.Q) + np.dot(self.Q, o.P)
        return RMat(P, Q, self.e + o.e).reduce()


def rmat_identity(N):
    P = np.zeros((N, N), dtype=object)
    P[...] = 0
    for i in range(N):
        P[i, i] = 1
    Q = np.zeros((N, N), dtype=object)
    Q[...] = 0
    return RMat(P, Q, 0)


# ---------------------------------------------------------------------------
# Pauli basis and the exact channel  V^_{sigma tau} = 2^{-n} tr(sigma V tau V^dag)
# ---------------------------------------------------------------------------

PAULI1 = [zw_matrix([[1, 0], [0, 1]]),
          zw_matrix([[0, 1], [1, 0]]),
          zw_matrix([[0, W6], [W2, 0]]),
          zw_matrix([[1, 0], [0, -1]])]


def _kron(A, B):
    out = np.empty((A.shape[0] * B.shape[0], A.shape[1] * B.shape[1]), dtype=object)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            out[i * B.shape[0]:(i + 1) * B.shape[0], j * B.shape[1]:(j + 1) * B.shape[1]] = A[i, j] * B
    return out


@lru_cache(maxsize=None)
def pauli_matrix(idx, n):
    """Hermitian Pauli with per-qubit digits p_q = (idx // 4^q) % 4."""
    M = zw_matrix([[1]])
    for q in range(n - 1, -1, -1):
        M = _kron(M, PAULI1[(idx // 4 ** q) % 4])
    return M


def channel_dense(U):
    """Exact 4^n x 4^n Pauli channel of U = M/sqrt2^k as a reduced RMat.
    tr(sigma M tau M^dag) is a real element of Z[omega], i.e. in Z[sqrt2];
    dividing by 2^{n+k} = sqrt2^{2(n+k)} gives the stored form."""
    n, N = U.n, 4 ** U.n
    Md = U.dagger().M
    P = np.empty((N, N), dtype=object)
    Q = np.empty((N, N), dtype=object)
    for tau in range(N):
        Y = np.dot(np.dot(U.M, pauli_matrix(tau, n)), Md)
        for sig in range(N):
            tr = sum((pauli_matrix(sig, n) * Y.T).flat, ZERO)  # tr(sigma Y)
            P[sig, tau], Q[sig, tau] = tr.real_sqrt2()
    return RMat(P, Q, 2 * (n + U.k)).reduce()


def bloch(U):
    """Exact SO(3) Bloch matrix V^_ij = 1/2 tr(sigma_i V sigma_j V^dag),
    i,j in {x,y,z} (Lemma bridge); n must be 1."""
    if U.n != 1:
        raise ValueError("bloch() is for single-qubit unitaries")
    C = channel_dense(U)
    return RMat(C.P[1:, 1:], C.Q[1:, 1:], C.e).reduce()


# ---------------------------------------------------------------------------
# Structured accumulator: one channel multiplication per gate
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def local_channel(name):
    """Reduced local channel (A, B, f) of a gate, A + B sqrt2 over sqrt2^f,
    plus signed-permutation data (perm, sign) when f == 0."""
    name = gate_name(name)
    m = GATES[name][2]
    G, k = gate_matrix(name)
    U = DMat(G, k, m).reduce()
    C = channel_dense(U)
    A = C.P.astype(np.int64)
    B = C.Q.astype(np.int64)
    perm = sign = None
    if C.e == 0:
        assert not B.any()
        nz = (A != 0)
        assert (nz.sum(axis=0) == 1).all() and (nz.sum(axis=1) == 1).all()
        perm = np.argmax(nz, axis=0)            # row hit by column l
        sign = A[perm, np.arange(A.shape[0])]
        assert set(np.abs(sign)) == {1}
    return A, B, C.e, perm, sign


def _clifford_step(R, name, qubits, n):
    """R <- R . (g^ (x) I) for a signed-permutation channel g^."""
    _, _, _, perm, sign = local_channel(name)
    N = 4 ** n
    tau = np.arange(N)
    loc = np.zeros(N, dtype=np.int64)
    for j, q in enumerate(qubits):
        loc += ((tau // 4 ** q) % 4) * 4 ** j
    new_loc = perm[loc]
    pi = tau.copy()
    for j, q in enumerate(qubits):
        pi += (((new_loc // 4 ** j) % 4) - ((tau // 4 ** q) % 4)) * 4 ** q
    s = _obj(sign[loc])
    return RMat(R.P[:, pi] * s, R.Q[:, pi] * s, R.e)      # already reduced


def _general_step(R, name, qubits, n):
    A, B, f, _, _ = local_channel(name)
    A, B = _obj(A), _obj(B)
    PA = _local_right_mult(R.P, A, qubits, n, 4)
    QA = _local_right_mult(R.Q, A, qubits, n, 4)
    PB = _local_right_mult(R.P, B, qubits, n, 4)
    QB = _local_right_mult(R.Q, B, qubits, n, 4)
    return RMat(PA + 2 * QB, PB + QA, R.e + f).reduce()


def pair_constant(P, n, wire):
    """Lemma mqval(b) criterion for S = Z on `wire`: every row of P mod 2
    is constant on each pair {tau, S tau} of the anticommuting sector
    (X <-> Y on that wire)."""
    N = 4 ** n
    tau = np.arange(N)
    cols_x = tau[(tau // 4 ** wire) % 4 == 1]
    cols_y = cols_x + 4 ** wire
    return bool(np.all((P[:, cols_x] - P[:, cols_y]) % 2 == 0))


def channel_accumulate(word, n=None, record=True):
    """Accumulate V^ = g^_1 ... g^_t exactly (Cor. cert proof); return
    (RMat, steps) where steps lists per-gate records."""
    w, n = normalize_word(word, n)
    R = rmat_identity(4 ** n)
    steps = []
    for j, (name, qs) in enumerate(w):
        A, B, f, perm, _ = local_channel(name)
        before = R.e
        rec = {"index": j, "gate": name, "qubits": qs, "lde_before": before}
        if f == 0:
            R = _clifford_step(R, name, qs, n)
        else:
            if name in T_TYPE:
                rec["criterion_fired"] = pair_constant(R.P, n, qs[0])
            R = _general_step(R, name, qs, n)
        rec["lde_after"] = R.e
        if f != 0:
            rec["collapsed"] = R.e < before + 1
        if record:
            steps.append(rec)
    return R, steps


# ---------------------------------------------------------------------------
# Single-qubit Clifford group (projective, via 3x3 Bloch signed permutations)
# ---------------------------------------------------------------------------

def _bloch_int(word):
    """3x3 integer Bloch matrix of a single-qubit Clifford word."""
    Bm = bloch(word_unitary(word, 1))
    assert Bm.e == 0 and not np.any(Bm.Q)
    return Bm.P.astype(np.int64)


@lru_cache(maxsize=None)
def clifford_group():
    """Dict key(3x3 Bloch) -> shortest word over {h, s}; 24 elements."""
    start = ("id",)
    seen = {}
    q = deque([start])
    seen[tuple(_bloch_int(start).flat)] = start
    while q:
        w = q.popleft()
        for g in ("h", "s"):
            w2 = w + (g,)
            k = tuple(_bloch_int(w2).flat)
            if k not in seen:
                seen[k] = w2
                q.append(w2)
    assert len(seen) == 24
    return seen


def clifford_words():
    return list(clifford_group().values())


def in_normalizer(C):
    """C in N(Z): the Bloch matrix fixes the z axis up to sign."""
    C = np.asarray(C)
    return abs(C[2, 2]) == 1 and C[0, 2] == 0 and C[1, 2] == 0


def eps(C):
    """epsilon(D) = +1 if D^dag Z D = Z, -1 if = -Z (D in N); = Bloch (z,z)."""
    assert in_normalizer(C)
    return int(np.asarray(C)[2, 2])


@lru_cache(maxsize=None)
def rot_bloch(m):
    """Bloch matrix of Z_m (even m only -> integer signed permutation)."""
    m %= 8
    if m % 2:
        raise ValueError("odd phase is not a Clifford")
    c, s = [1, 0, -1, 0][m // 2], [0, 1, 0, -1][m // 2]
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.int64)


@lru_cache(maxsize=None)
def letter_bloch(name):
    return _bloch_int((gate_name(name),))


# ---------------------------------------------------------------------------
# Linkage procedure (Theorem linkage)
# ---------------------------------------------------------------------------

def linkage(word):
    """Bring a single-qubit word to C_0 Z_{m_1} C_1 ... Z_{m_n} C_n, run
    transport + absorption to saturation, return
    {'t_min': survivors, 'phases': [...], 'cliffords': [...], 'merges': k}."""
    w, n = normalize_word(word)
    if n != 1:
        raise ValueError("linkage() is for single-qubit words")
    I3 = np.eye(3, dtype=np.int64)
    cliffs, phases = [], []
    cur = I3
    for name, _ in w:
        if name in T_TYPE:
            cliffs.append(cur)
            phases.append(PHASE[name])
            cur = I3
        else:
            cur = cur @ letter_bloch(name)
    cliffs.append(cur)
    merges = 0
    changed = True
    while changed:
        changed = False
        for i in range(1, len(cliffs) - 1):          # interior Cliffords
            D = cliffs[i]
            if in_normalizer(D):
                # Z_{m_i} D Z_{m_{i+1}} = D Z_{eps(D) m_i + m_{i+1}}
                mnew = (eps(D) * phases[i - 1] + phases[i]) % 8
                assert mnew % 2 == 0
                newC = cliffs[i - 1] @ D @ rot_bloch(mnew) @ cliffs[i + 1]
                cliffs[i - 1:i + 2] = [newC]
                del phases[i - 1:i + 1]
                merges += 1
                changed = True
                break
    return {"t_min": len(phases), "phases": phases, "cliffords": cliffs,
            "merges": merges}


# ---------------------------------------------------------------------------
# Residue automaton of Lemma valuation (finite verification)
# ---------------------------------------------------------------------------

def residue_automaton(allow_normalizer=False, expand_reducible=True):
    """BFS over states (Pbar, Qbar) in F_2^{3x3} x F_2^{3x3}.  Seeds: the
    residues (Cbar_0, 0) of the 24 Clifford prefixes.  One transition per
    (state, interior Clifford, odd phase); the update does not depend on
    the phase.  Returns counts and the reducible states."""
    Ab = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]], dtype=np.int64)
    Bb = np.diag([0, 0, 1]).astype(np.int64)
    cliffs = [np.array(k, dtype=np.int64).reshape(3, 3) % 2 for k in clifford_group()]
    interior = []
    for k in clifford_group():
        C = np.array(k, dtype=np.int64).reshape(3, 3)
        if allow_normalizer or not in_normalizer(C):
            interior.append(C % 2)
    key = lambda P, Q: (tuple(P.flat), tuple(Q.flat))
    seeds = {}
    for C in cliffs:
        seeds[key(C, np.zeros((3, 3), dtype=np.int64))] = (C, np.zeros((3, 3), dtype=np.int64))
    seen = dict(seeds)
    q = deque(seeds.values())
    transitions = 0
    reducible = set()
    while q:
        P, Q = q.popleft()
        if not ((P @ Ab) % 2).any():
            reducible.add(key(P, Q))
            if not expand_reducible:
                continue
        for C in interior:
            transitions += 4
            P2 = (P @ Ab @ C) % 2
            Q2 = ((P @ Bb + Q @ Ab) @ C) % 2
            k = key(P2, Q2)
            if k not in seen:
                seen[k] = (P2, Q2)
                q.append((P2, Q2))
    return {"states": len(seen), "seed_states": len(seeds), "transitions": transitions,
            "reducible_states": len(reducible),
            "interior_cliffords": len(interior)}


# ---------------------------------------------------------------------------
# Matsumoto--Amano normal forms (T|eps)(HT|SHT)^l c
# ---------------------------------------------------------------------------

def matsumoto_amano_words(tmax):
    """All MA normal-form words with T-count <= tmax, as lists of letters
    (matrix-product order: (T|eps), then the syllables, then c)."""
    out = []
    cws = clifford_words()
    for t in range(tmax + 1):
        heads = [[]] + ([["t"]] if t >= 1 else [])
        for head in heads:
            l = t - len(head)
            for bits in range(2 ** l):
                body = []
                for i in range(l):
                    body += ["h", "t"] if (bits >> i) & 1 == 0 else ["s", "h", "t"]
                for c in cws:
                    out.append(head + body + [g for g in c if g != "id"])
    return out


# ---------------------------------------------------------------------------
# Certificates
# ---------------------------------------------------------------------------

def certificate(word, n=None, compute_unitary=True, max_unitary_qubits=6):
    """Per-instance certificate.

    Theorem B(a) / Corollary cert: floor = lde(channel) <= T-count of any
    semantics-exact optimizer's output.  Theorem C(c): removable fraction
    <= 1 - lde/t(C).  Single qubit adds Lemma bridge (t_min = lde(Bloch))
    and the linkage count (Theorem linkage)."""
    w, n = normalize_word(word, n)
    tc = sum(1 for name, _ in w if name in T_TYPE)
    R, steps = channel_accumulate(w, n)
    lde = R.lde
    tsteps = [s for s in steps if "collapsed" in s]
    collapses = sum(1 for s in tsteps if s["collapsed"])
    # Lemma mqval(b), proven half: criterion fails -> lde rises by exactly
    # one; criterion holds -> lde <= m.  Equivalently criterion <=> collapse.
    viol = [s for s in tsteps if "criterion_fired" in s
            and (s["criterion_fired"] != s["collapsed"]
                 or (not s["criterion_fired"] and s["lde_after"] != s["lde_before"] + 1))]
    # Lemma mqval(b), unproven refinement ("reduction fires exactly once",
    # i.e. lde_after == m when the criterion holds): count the exceptions.
    drops = [s["lde_before"] + 1 - s["lde_after"] for s in tsteps if s["collapsed"]]
    refinement_viol = sum(1 for d in drops if d != 1)
    out = {
        "n": n,
        "gate_count": len(w),
        "t_count": tc,
        "lde_channel": lde,
        "floor": lde,
        "max_removable_fraction": (1 - lde / tc) if tc else 0.0,
        "certified_incompressible_fraction": (lde / tc) if tc else 1.0,
        "collapse_count": collapses,
        "collapse_rate": (collapses / tc) if tc else 0.0,
        "collapse_sizes": drops,
        "criterion_violations": viol,
        "refinement_violations": refinement_viol,
        "steps": steps,
        "sound": tc >= lde,
    }
    if compute_unitary and n <= max_unitary_qubits:
        U = word_unitary(w, n)
        out["sde_unitary"] = U.sde
        out["unitary"] = U
        if n == 1:
            Bm = bloch(U)
            out["lde_bloch"] = Bm.lde
            out["t_min"] = Bm.lde
            out["bloch"] = Bm
            L = linkage(w)
            out["linkage_t_min"] = L["t_min"]
            out["linkage_merges"] = L["merges"]
            out["linkage_agrees"] = (L["t_min"] == Bm.lde == lde)
    return out


def block_rigidity(block_word):
    """Theorem C(a) for one single-wire block: returns (lde, t_count, rigid)."""
    w, _ = normalize_word(block_word)
    w1 = [(name, (0,)) for name, _ in w]
    R, _ = channel_accumulate(w1, 1)
    tc = sum(1 for name, _ in w1 if name in T_TYPE)
    return R.lde, tc, R.lde == tc


def is_matsumoto_amano(word):
    """Syntactic check of the grammar (T|eps)(HT|SHT)^l c, with c any
    T-free suffix (used by the paper to validate gridsynth output)."""
    w, _ = normalize_word(word)
    names = [name for name, _ in w]
    i = 0
    if names[:1] == ["t"]:
        i = 1
    while True:
        if names[i:i + 2] == ["h", "t"]:
            i += 2
        elif names[i:i + 3] == ["s", "h", "t"]:
            i += 3
        else:
            break
    return all(nm not in T_TYPE for nm in names[i:])


# ---------------------------------------------------------------------------
# OpenQASM 2 subset
# ---------------------------------------------------------------------------

QASM_GATES = {"h", "s", "sdg", "t", "tdg", "x", "y", "z", "cx", "cz", "swap", "id"}


def parse_qasm(text, ignore=("barrier",)):
    """Parse an OpenQASM-2 subset.  Returns (n, gates in time order)."""
    text = re.sub(r"//.*", "", text)
    regs, offset, gates = {}, 0, []
    for stmt in text.split(";"):
        s = stmt.strip()
        if not s:
            continue
        head = s.split()[0]
        if head in ("OPENQASM", "include", "creg"):
            continue
        if head == "qreg":
            m = re.match(r"qreg\s+(\w+)\s*\[\s*(\d+)\s*\]", s)
            regs[m.group(1)] = offset
            offset += int(m.group(2))
            continue
        if head in ignore:
            continue
        m = re.match(r"(\w+)\s*(\([^)]*\))?\s+(.*)", s)
        name, params, args = m.group(1), m.group(2), m.group(3)
        if name not in QASM_GATES:
            raise ValueError("unsupported statement (not in the Clifford+T subset): %r" % s)
        qs = []
        for a in args.split(","):
            m2 = re.match(r"\s*(\w+)\s*\[\s*(\d+)\s*\]\s*", a)
            if not m2:
                raise ValueError("register-wide gates are not supported: %r" % s)
            qs.append(regs[m2.group(1)] + int(m2.group(2)))
        gates.append((name, tuple(qs)))
    return offset, gates


def word_from_qasm(text, time_order_as_word=False):
    """QASM is in time order; the paper's word is the matrix product
    g_1 ... g_t, so the time-ordered list is reversed unless
    time_order_as_word=True (the lde is identical either way; only the
    per-step trajectory differs)."""
    n, gates = parse_qasm(text)
    return n, (gates if time_order_as_word else list(reversed(gates)))


def certificate_from_qasm(text_or_path, **kw):
    if "\n" not in text_or_path and text_or_path.endswith(".qasm"):
        with open(text_or_path) as f:
            text_or_path = f.read()
    n, word = word_from_qasm(text_or_path, kw.pop("time_order_as_word", False))
    return certificate(word, n, **kw)


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        c = certificate_from_qasm(path, compute_unitary=False)
        print(path, {k: c[k] for k in ("n", "t_count", "lde_channel", "floor",
                                       "max_removable_fraction", "collapse_count")})
