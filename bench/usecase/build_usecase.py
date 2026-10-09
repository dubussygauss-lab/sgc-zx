"""Use-case instances: Grover search written in Clifford+T.

Writes bench/usecase/grover_d<d>.qasm (d = number of data qubits) and
bench/usecase/manifest.csv.  Run: python3 bench/usecase/build_usecase.py

Construction (every subroutine from a cited source)
  * Grover search, one marked item w among N = 2^d, k = floor(pi/4 sqrt(N))
    iterations of (oracle, diffusion) after H^d on |0^d>.
    L. K. Grover, "A fast quantum mechanical algorithm for database search",
    arXiv:quant-ph/9605043.  Ideal success probability sin^2((2k+1) theta),
    sin(theta) = 1/sqrt(N).
  * Oracle I - 2|w><w|: X on the data qubits where w has a 0, a multi-controlled
    Z on all d data qubits, the same X gates again.
  * Diffusion 2|s><s| - I, up to a global phase -1: H^d X^d (C^{d-1}Z) X^d H^d.
  * C^{d-1}Z = H(t) C^{d-1}X H(t) on the last data qubit t.
  * C^m X with m = d-1 controls, built from 4(m-2) Toffoli gates with m-2
    ancillas whose state is restored whatever it is (Barenco et al.,
    "Elementary gates for quantum computation", arXiv:quant-ph/9503016,
    Lemma 7.2; n = 2m-1 qubits, m <= ceil(n/2)).
  * Toffoli = 7 T/Tdg, 6 CX, 2 H (Nielsen and Chuang, Quantum Computation and
    Quantum Information, 2000, Fig. 4.9).
Qubits: q[0..d-1] data (q[0] most significant bit of w), q[d..2d-4] ancillas,
all starting in |0>.  Gate set of the QASM: h, x, cx, t, tdg.
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = (5, 6)                 # data qubits
PATTERN = "1011010"            # marked item w = int(PATTERN[:d], 2)


def marked(d):
    return int(PATTERN[:d], 2)


def n_iter(d):
    return int(math.floor(math.pi / 4 * math.sqrt(2 ** d)))


def p_success_ideal(d):
    th = math.asin(1 / math.sqrt(2 ** d))
    return math.sin((2 * n_iter(d) + 1) * th) ** 2


def toffoli(a, b, c):
    """Nielsen-Chuang Fig. 4.9: controls a, b, target c."""
    return [("h", c), ("cx", b, c), ("tdg", c), ("cx", a, c), ("t", c),
            ("cx", b, c), ("tdg", c), ("cx", a, c), ("t", b), ("t", c),
            ("h", c), ("cx", a, b), ("t", a), ("tdg", b), ("cx", a, b)]


def barenco_mcx(ctrls, tgt, anc):
    """Barenco et al. Lemma 7.2: C^m X with m = len(ctrls) >= 3 controls and
    m-2 ancillas (any state, restored), 4(m-2) Toffolis.  Returns a list of
    Toffoli triples (c1, c2, target)."""
    m = len(ctrls)
    assert m >= 3 and len(anc) == m - 2
    chain = list(anc) + [tgt]           # chain[j] = a_{j+1}, chain[m-2] = target
    # down[i]: Toffoli(x_i, a_{i-2}, a_{i-1}) for i = m..3 (1-based x, a)
    down = [(ctrls[i - 1], chain[i - 3], chain[i - 2]) for i in range(m, 2, -1)]
    base = (ctrls[0], ctrls[1], chain[0])
    seq = down + [base] + down[::-1] + down[1:] + [base] + down[1:][::-1]
    assert len(seq) == 4 * (m - 2)
    return seq


def mcz(data, anc):
    t = data[-1]
    g = [("h", t)]
    for a, b, c in barenco_mcx(data[:-1], t, anc):
        g += toffoli(a, b, c)
    g += [("h", t)]
    return g


def grover_gates(d):
    data = list(range(d))
    anc = list(range(d, 2 * d - 3))
    w = format(marked(d), f"0{d}b")
    flip = [("x", q) for q, bit in zip(data, w) if bit == "0"]
    g = [("h", q) for q in data]
    for _ in range(n_iter(d)):
        g += flip + mcz(data, anc) + flip                       # oracle
        g += [("h", q) for q in data] + [("x", q) for q in data]
        g += mcz(data, anc)
        g += [("x", q) for q in data] + [("h", q) for q in data]  # diffusion
    return g, 2 * d - 3


def to_qasm(gates, n):
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];"]
    for op, *qs in gates:
        lines.append(f"{op} " + ",".join(f"q[{q}]" for q in qs) + ";")
    return "\n".join(lines) + "\n"


def main():
    rows = []
    for d in SIZES:
        gates, n = grover_gates(d)
        name = f"grover_d{d}.qasm"
        with open(os.path.join(HERE, name), "w") as f:
            f.write(to_qasm(gates, n))
        n_tof = 2 * n_iter(d) * 4 * (d - 3)
        rows.append({
            "file": name, "algorithm": "grover", "n_data": d, "n_ancilla": n - d,
            "n_qubits": n, "marked": marked(d), "marked_bits": format(marked(d), f"0{d}b"),
            "iterations": n_iter(d), "n_toffoli": n_tof,
            "t_count_written": sum(1 for g in gates if g[0] in ("t", "tdg")),
            "n_cx_written": sum(1 for g in gates if g[0] == "cx"),
            "p_success_ideal_formula": f"{p_success_ideal(d):.12f}",
        })
        print(rows[-1])
    with open(os.path.join(HERE, "manifest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
