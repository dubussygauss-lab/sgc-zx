"""Family B2: Clifford+T circuits from Haar-random unitaries via QSD + gridsynth.

Construction (reproducing papers/barrier/main.tex, Sec. "Multi-qubit
rigidity" and App. "Numerical methodology and validation"):

  1. Haar target: scipy.stats.unitary_group.rvs(2**n, random_state=rng) with
     rng = numpy.random.default_rng(20261006), drawn in the order
     (n=2, k=1..5), (n=3, k=1..5).  scipy implements Mezzadri's QR of a
     complex Ginibre matrix with the diagonal phase fix.  The same target is
     used for both eps values.
  2. qiskit.synthesis.qs_decomposition(U)  (KAK at n=2, QSD at n=3), then
     qiskit.transpile(basis_gates=['rz','sx','x','cx'], optimization_level=1,
     seed_transpiler=0).  The only non-Clifford gates are rz(theta).
  3. Each rz(theta):
       - if theta/(pi/4) is within 1e-9 of an integer m, emit T^(m mod 8)
         written as a product of {z, s, sdg, t, tdg} (rz(theta) = T^m up to
         global phase); not counted as synthesised;
       - otherwise emit pygridsynth.gridsynth_gates(mpf(theta), mpf(eps))
         (Ross-Selinger, exact approximation of Rz(theta) =
         diag(e^{-i theta/2}, e^{i theta/2}), not up to phase).  The returned
         string is in matrix-product order (leftmost gate applied last;
         DOmegaUnitary.from_gates iterates reversed(gates)), so it is reversed
         for circuit order.  W = e^{i pi/4} global phase, dropped.
     sx -> h s h (exact), x -> x, cx -> cx.
  4. Output OpenQASM 2 over {h, s, sdg, t, tdg, x, z, cx} and a manifest.

Error: ||U_circ - e^{i phi} U_target||_2 (largest singular value), phi =
arg tr(U_target^dag U_circ).  U_circ is evaluated from the written QASM with
an independent numpy simulator in qiskit's little-endian convention (same as
Operator(qc) for the qs_decomposition input), and cross-checked against
qiskit.quantum_info.Operator of the final circuit.  Bound: n_rz_synth * eps
(triangle inequality; each gridsynth block is verified individually to be
within eps in operator norm of its target rz).
"""

import os
import re
import sys
import warnings

import mpmath
import numpy as np
import pandas as pd
import pygridsynth
import scipy.stats as st
from qiskit import transpile
from qiskit.quantum_info import Operator
from qiskit.synthesis import qs_decomposition

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "bench", "family_B2")
SEED = 20261006
NS = (2, 3)
EPSS = (1e-3, 1e-5)
K = 5
EXACT_TOL = 1e-9

warnings.filterwarnings("ignore", category=UserWarning, module="pygridsynth")

MA_RE = re.compile(r"^T?(HT|SHT)*[HSXW]*$")

H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
G1 = {
    "h": H,
    "s": np.diag([1, 1j]),
    "sdg": np.diag([1, -1j]),
    "t": np.diag([1, np.exp(1j * np.pi / 4)]),
    "tdg": np.diag([1, np.exp(-1j * np.pi / 4)]),
    "x": np.array([[0, 1], [1, 0]]),
    "z": np.diag([1, -1]),
}
CX = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])  # ctrl=q0 (index 0 of args)

T_POWER = {0: [], 1: ["t"], 2: ["s"], 3: ["s", "t"], 4: ["z"],
           5: ["z", "t"], 6: ["sdg"], 7: ["tdg"]}


def rz_matrix(theta):
    return np.diag([np.exp(-1j * theta / 2), np.exp(1j * theta / 2)])


def opnorm_phase_aligned(A, B):
    """||A - e^{i phi} B||_2 with phi = arg tr(B^dag A)."""
    phi = np.angle(np.trace(B.conj().T @ A))
    return float(np.linalg.norm(A - np.exp(1j * phi) * B, 2))


def gridsynth_word(theta, eps):
    """Circuit-order list of gate names approximating rz(theta); returns
    (names, block_error, ma_ok)."""
    word = pygridsynth.gridsynth_gates(mpmath.mpf(theta), mpmath.mpf(eps))
    ma_ok = bool(MA_RE.match(word))
    names = []
    m = np.eye(2, dtype=complex)
    nW = 0
    for ch in reversed(word):  # circuit order
        if ch == "W":
            nW += 1
            continue
        g = {"H": "h", "S": "s", "T": "t", "X": "x"}[ch]
        names.append(g)
        m = G1[g] @ m
    m = m * np.exp(1j * np.pi / 4 * nW)
    err = float(np.linalg.norm(m - rz_matrix(theta), 2))  # exact, no phase freedom
    return names, err, ma_ok


def expand(qc, eps):
    """qiskit circuit over {rz, sx, x, cx} -> list of (name, qubits)."""
    gates = []
    n_synth = n_exact = 0
    worst_block = 0.0
    ma_all = True
    for inst in qc.data:
        name = inst.operation.name
        qs = [qc.find_bit(q).index for q in inst.qubits]
        if name == "cx":
            gates.append(("cx", qs))
        elif name == "x":
            gates.append(("x", qs))
        elif name == "sx":
            gates += [("h", qs), ("s", qs), ("h", qs)]
        elif name == "rz":
            theta = float(inst.operation.params[0])
            m = theta / (np.pi / 4)
            if abs(m - round(m)) < EXACT_TOL:
                n_exact += 1
                gates += [(g, qs) for g in T_POWER[int(round(m)) % 8]]
            else:
                n_synth += 1
                names, err, ma_ok = gridsynth_word(theta, eps)
                assert err <= eps, (theta, eps, err)
                worst_block = max(worst_block, err)
                ma_all &= ma_ok
                gates += [(g, qs) for g in names]
        else:
            raise ValueError(name)
    return gates, n_synth, n_exact, worst_block, ma_all


def to_qasm(gates, n):
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];"]
    for g, qs in gates:
        lines.append(f"{g} " + ",".join(f"q[{q}]" for q in qs) + ";")
    return "\n".join(lines) + "\n"


def simulate_qasm(path):
    """Unitary of the QASM file, little-endian (qiskit) convention."""
    gates, n = [], None
    with open(path) as f:
        for line in f:
            line = line.strip()
            m = re.match(r"qreg q\[(\d+)\];", line)
            if m:
                n = int(m.group(1))
                continue
            m = re.match(r"(\w+) (.*);", line)
            if m and m.group(1) in G1 or (m and m.group(1) == "cx"):
                qs = [int(x) for x in re.findall(r"q\[(\d+)\]", m.group(2))]
                gates.append((m.group(1), qs))
    t = np.eye(2 ** n, dtype=complex).reshape((2,) * (2 * n))
    for g, qs in gates:
        if g == "cx":
            u = CX.reshape(2, 2, 2, 2)
            k = 2
        else:
            u = G1[g]
            k = 1
        # qiskit little-endian: qubit j <-> tensor axis (n-1-j)
        axes = [n - 1 - q for q in qs]
        t = np.tensordot(u, t, axes=(list(range(k, 2 * k)), axes))
        t = np.moveaxis(t, list(range(k)), axes)
    return t.reshape(2 ** n, 2 ** n)


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(SEED)
    targets = {}
    for n in NS:
        for k in range(1, K + 1):
            targets[(n, k)] = st.unitary_group.rvs(2 ** n, random_state=rng)
    rows = []
    for n in NS:
        for k in range(1, K + 1):
            U = targets[(n, k)]
            qc = qs_decomposition(U)
            tq = transpile(qc, basis_gates=["rz", "sx", "x", "cx"],
                           optimization_level=1, seed_transpiler=0)
            dev_t = opnorm_phase_aligned(Operator(tq).data, U)
            for eps in EPSS:
                gates, n_synth, n_exact, worst_block, ma_all = expand(tq, eps)
                fname = f"haar_n{n}_eps{eps:.0e}_s{k}.qasm"
                path = os.path.join(OUT, fname)
                with open(path, "w") as f:
                    f.write(to_qasm(gates, n))
                np.save(os.path.join(OUT, fname.replace(".qasm", "_target.npy")), U)
                Uc = simulate_qasm(path)
                err = opnorm_phase_aligned(Uc, U)
                # cross-check the simulator against qiskit's Operator
                from qiskit import QuantumCircuit
                xq = QuantumCircuit.from_qasm_file(path)
                err_qiskit = opnorm_phase_aligned(Operator(xq).data, U)
                sim_vs_qiskit = opnorm_phase_aligned(Uc, Operator(xq).data)
                names = [g for g, _ in gates]
                row = dict(
                    file=fname, n=n, eps=eps, instance=k,
                    n_gates=len(gates),
                    t_count=names.count("t") + names.count("tdg"),
                    n_cx=names.count("cx"),
                    n_h=names.count("h"),
                    n_rz_transpiled=n_synth + n_exact,
                    n_rz_synthesised=n_synth,
                    n_rz_exact=n_exact,
                    worst_block_error=worst_block,
                    all_blocks_matsumoto_amano=ma_all,
                    transpile_dev=dev_t,
                    operator_norm_error=err,
                    operator_norm_error_qiskit=err_qiskit,
                    sim_vs_qiskit=sim_vs_qiskit,
                    bound=n_synth * eps,
                    below_bound=err <= n_synth * eps,
                )
                rows.append(row)
                print(f"{fname}: gates={row['n_gates']} T={row['t_count']} "
                      f"cx={row['n_cx']} rz_synth={n_synth} err={err:.3e} "
                      f"bound={row['bound']:.3e} MA={ma_all}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "manifest.csv"), index=False)
    print(df.to_string())
    assert df.below_bound.all()


if __name__ == "__main__":
    main()
