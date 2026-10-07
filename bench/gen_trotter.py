"""Family A benchmark generator: first-order Trotter circuits for spin chains.

Writes OpenQASM 2.0 files (gates h, rz, rx, cx, plus x for the xxz state
preparation) for

  tfim    transverse-field Ising chain, open boundary
              H = -sum_i J_i Z_i Z_{i+1} - h sum_i X_i
  xxz     Heisenberg chain, open boundary
              H = sum_i (Jx_i X_i X_{i+1} + Jy_i Y_i Y_{i+1} + Jz_i Z_i Z_{i+1})
  ladder  transverse-field Ising model on a 2 x (n/2) ladder
              rail 0 = q[0..m-1], rail 1 = q[m..2m-1], m = n/2,
              rail bonds (i,i+1) on each rail, rung bonds (i, m+i),
              H = -sum_bonds J_b Z Z - h sum_i X_i

Couplings: "uniform" uses J = 1 on every bond (xxz: Jx = Jy = 1, Jz = 0.5)
and h = 1; "disorder" draws bond couplings uniformly from [0.5, 1.5] with
rng = numpy.random.default_rng(20261006), h staying 1.  All draws are made
first, from one rng stream, in the fixed order

  for model in (tfim, xxz, ladder):
    for n in (4, 6, 8, 10, 12):
      for instance in (1, 2, 3):
        for bond in bonds(model, n):          # order given by bonds()
          tfim, ladder: one draw  -> J
          xxz:          three draws -> Jx, (discarded), Jz   and Jy = Jx

so the instance set does not depend on the order in which files are written.
The discarded xxz draw was Jy in an earlier version; it is still consumed so
that every other coupling in the set (tfim, ladder, xxz Jx and Jz) is
unchanged by the switch to Jy = Jx.

Initial state: tfim and ladder circuits start from |0...0> ("zero").  Every
xxz circuit (uniform and disordered) starts from the Neel state |0101...>
("neel"): the circuit begins with `x q[i]` for every odd i, before the first
Trotter step.  |0...0> is an eigenstate of the XXZ Hamiltonian (it conserves
total Z), so without this the xxz output distribution would be the
deterministic point mass on 0...0 and carry no information about the
Trotter circuit.  The state preparation does not touch the rng stream or
the couplings.  The x gates are not counted in n_cx/n_rz/n_rx/n_h but they
are counted in depth (they add one layer to every xxz circuit).

Time evolution: one Trotter step approximates exp(-i H dt), dt = 0.1, and the
circuit for r steps approximates exp(-i H r dt).  Each Hamiltonian term
c * P (P a Pauli string) becomes the exact exponential exp(-i c dt P):

  exp(-i t Z_i Z_j) = cx q[i],q[j]; rz(2t) q[j]; cx q[i],q[j];
  exp(-i t X_i X_j) = h q[i]; h q[j]; [exp(-i t Z_i Z_j)]; h q[i]; h q[j];
  exp(-i t Y_i Y_j) = rx(pi/2) q[i]; rx(pi/2) q[j]; [exp(-i t Z_i Z_j)];
                      rx(-pi/2) q[i]; rx(-pi/2) q[j];
  exp(-i t X_i)     = rx(2t) q[i];

with rz(a) = exp(-i a Z/2), rx(a) = exp(-i a X/2) (see sv.py; qelib1's rz
differs by a global phase only).  The factor 2 compensates the 1/2 in the
rz/rx definitions, and the sign of t follows the sign of the Hamiltonian
term, so the TFIM uses rz(-2 J dt) and rx(-2 h dt).  The identity for YY uses
rx(-pi/2) Z rx(+pi/2) = Y.  Within a step the terms are ordered: even bonds,
odd bonds (ladder: even rail bonds, odd rail bonds, rungs), then the field
terms; on an xxz bond the order is XX, YY, ZZ (these commute).

Outputs, in family_A/:
  <model>_n<n>_r<r>_<uniform|disorder>_s<k>.qasm       no measurements
  <model>_n<n>_r<r>_<uniform|disorder>_s<k>_meas.qasm  creg + measure q -> c
  <same stem>.npy   (n <= 10)  ideal Z-basis probabilities of the whole
                               file (state preparation included) run on
                               |0...0>, index = sum_i b_i 2^(n-1-i) (q[0] = MSB)
  manifest.csv      file, model, n, r, disorder, instance, initial_state
                    ("zero" / "neel"), n_cx, n_rz, n_rx, n_h, depth,
                    couplings (JSON)
"""

import csv
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sv  # noqa: E402

MODELS = ["tfim", "xxz", "ladder"]
SIZES = [4, 6, 8, 10, 12]
STEPS = [1, 2, 4]
DT = 0.1
SEED = 20261006
N_DISORDER = 3
NPY_MAX_N = 10
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "family_A")

PI_HALF = "pi/2"       # written symbolically so parsers see an exact Clifford angle


# ---------------------------------------------------------------- primitives

def exp_zz(i, j, t):
    """Gates for exp(-i t Z_i Z_j)."""
    return [("cx", [i, j], []), ("rz", [j], [2 * t]), ("cx", [i, j], [])]


def exp_xx(i, j, t):
    """Gates for exp(-i t X_i X_j)."""
    return [("h", [i], []), ("h", [j], [])] + exp_zz(i, j, t) + [("h", [i], []), ("h", [j], [])]


def exp_yy(i, j, t):
    """Gates for exp(-i t Y_i Y_j)."""
    return ([("rx", [i], [PI_HALF]), ("rx", [j], [PI_HALF])] + exp_zz(i, j, t)
            + [("rx", [i], ["-" + PI_HALF]), ("rx", [j], ["-" + PI_HALF])])


def exp_x(i, t):
    """Gates for exp(-i t X_i)."""
    return [("rx", [i], [2 * t])]


PRIMITIVE = {"ZZ": exp_zz, "XX": exp_xx, "YY": exp_yy, "X": exp_x}


# ---------------------------------------------------------------- initial state

def initial_state(model):
    """Name of the initial state a model's circuits start from."""
    return "neel" if model == "xxz" else "zero"


def state_prep_gates(model, n):
    """Gates that prepare the initial state from |0...0>: `x q[i]` on odd i
    for the Neel state |0101...>, nothing for |0...0>."""
    if initial_state(model) == "neel":
        return [("x", [i], []) for i in range(1, n, 2)]
    return []


# ---------------------------------------------------------------- models

def bonds(model, n):
    """Bond list (i, j) in the Trotter order described in the module docstring."""
    if model in ("tfim", "xxz"):
        chain = [(i, i + 1) for i in range(n - 1)]
        return chain[0::2] + chain[1::2]
    if model == "ladder":
        m = n // 2
        rails = [(i, i + 1) for i in range(m - 1)] + [(m + i, m + i + 1) for i in range(m - 1)]
        rungs = [(i, m + i) for i in range(m)]
        return rails[0::2] + rails[1::2] + rungs
    raise ValueError(model)


def uniform_couplings(model, n):
    """Coupling dict for the uniform instance."""
    if model == "xxz":
        return {"bonds": [[i, j, 1.0, 1.0, 0.5] for i, j in bonds(model, n)]}
    return {"bonds": [[i, j, 1.0] for i, j in bonds(model, n)], "h": 1.0}


def draw_couplings(model, n, rng):
    """Coupling dict for one disordered instance (consumes rng in bond order)."""
    if model == "xxz":
        b = []
        for i, j in bonds(model, n):
            Jx = float(rng.uniform(0.5, 1.5))
            rng.uniform(0.5, 1.5)          # consumed and discarded (keeps the stream fixed)
            Jz = float(rng.uniform(0.5, 1.5))
            b.append([i, j, Jx, Jx, Jz])   # Jy = Jx: true XXZ
        return {"bonds": b}
    b = [[i, j, float(rng.uniform(0.5, 1.5))] for i, j in bonds(model, n)]
    return {"bonds": b, "h": 1.0}


def terms(model, n, c):
    """Hamiltonian as a list of (coef, pauli_label, qubits): H = sum coef * P."""
    out = []
    if model in ("tfim", "ladder"):
        for i, j, J in c["bonds"]:
            out.append((-J, "ZZ", [i, j]))
        for i in range(n):
            out.append((-c["h"], "X", [i]))
    elif model == "xxz":
        for i, j, Jx, Jy, Jz in c["bonds"]:
            out.append((Jx, "XX", [i, j]))
            out.append((Jy, "YY", [i, j]))
            out.append((Jz, "ZZ", [i, j]))
    else:
        raise ValueError(model)
    return out


def trotter_circuit(term_list, dt, r):
    """r first-order Trotter steps; each term c*P becomes exp(-i c dt P)."""
    gates = []
    for _ in range(r):
        for coef, label, qs in term_list:
            gates += PRIMITIVE[label](*qs, coef * dt)
    return gates


# ---------------------------------------------------------------- output helpers

def fmt_param(p):
    return p if isinstance(p, str) else repr(float(p))


def to_qasm(gates, n, measure=False):
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[%d];" % n]
    if measure:
        lines.append("creg c[%d];" % n)
    for name, qs, ps in gates:
        head = name if not ps else "%s(%s)" % (name, ",".join(fmt_param(p) for p in ps))
        lines.append("%s %s;" % (head, ",".join("q[%d]" % q for q in qs)))
    if measure:
        lines.append("measure q -> c;")
    return "\n".join(lines) + "\n"


def numeric_gates(gates):
    """Same gate list with symbolic angles evaluated to floats (for sv.run)."""
    return [(name, qs, [sv.eval_angle(p) if isinstance(p, str) else float(p) for p in ps])
            for name, qs, ps in gates]


def depth(gates):
    """Longest path with every gate counted as 1 (ASAP layer scheduler)."""
    ready = {}
    d = 0
    for _, qs, _ in gates:
        layer = max(ready.get(q, 0) for q in qs) + 1
        for q in qs:
            ready[q] = layer
        d = max(d, layer)
    return d


def gate_counts(gates):
    """Counts of the Trotter gate types (state-preparation x gates are not
    counted)."""
    c = {"cx": 0, "rz": 0, "rx": 0, "h": 0}
    for name, _, _ in gates:
        if name in c:
            c[name] += 1
    return c


# ---------------------------------------------------------------- main

def all_instances():
    """(model, n, label, instance, couplings) for every instance, draws made first."""
    rng = np.random.default_rng(SEED)
    inst = []
    for model in MODELS:
        for n in SIZES:
            inst.append((model, n, "uniform", 1, uniform_couplings(model, n)))
            for k in range(1, N_DISORDER + 1):
                inst.append((model, n, "disorder", k, draw_couplings(model, n, rng)))
    return inst


def main(out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for model, n, label, k, c in all_instances():
        tl = terms(model, n, c)
        for r in STEPS:
            stem = "%s_n%d_r%d_%s_s%d" % (model, n, r, label, k)
            gates = state_prep_gates(model, n) + trotter_circuit(tl, DT, r)
            with open(os.path.join(out_dir, stem + ".qasm"), "w") as f:
                f.write(to_qasm(gates, n))
            with open(os.path.join(out_dir, stem + "_meas.qasm"), "w") as f:
                f.write(to_qasm(gates, n, measure=True))
            if n <= NPY_MAX_N:
                psi = sv.run(numeric_gates(gates), n)
                np.save(os.path.join(out_dir, stem + ".npy"), sv.probabilities(psi))
            cnt = gate_counts(gates)
            rows.append({
                "file": stem + ".qasm", "model": model, "n": n, "r": r,
                "disorder": label, "instance": k,
                "initial_state": initial_state(model),
                "n_cx": cnt["cx"], "n_rz": cnt["rz"], "n_rx": cnt["rx"], "n_h": cnt["h"],
                "depth": depth(gates),
                "couplings": json.dumps(dict(c, dt=DT), separators=(",", ":")),
            })
    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def summary(rows):
    print("%d circuits written" % len(rows))
    print("n   files  cx(min-max)   depth(min-max)")
    for n in SIZES:
        sub = [x for x in rows if x["n"] == n]
        cx = [x["n_cx"] for x in sub]
        dp = [x["depth"] for x in sub]
        print("%-3d %-6d %4d-%-9d %4d-%d" % (n, len(sub), min(cx), max(cx), min(dp), max(dp)))
    for model in MODELS:
        print("%-7s %d files" % (model, sum(1 for x in rows if x["model"] == model)))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else OUT_DIR
    summary(main(out))
