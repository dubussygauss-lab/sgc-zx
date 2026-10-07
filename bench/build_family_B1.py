"""Build family B1: standard Clifford+T benchmark circuits (Amy et al. 2013 /
Nam et al. 2018 set) taken from the Quantinuum pyzx fork, n <= 12 qubits.

Source: third_party/pyzx-fork/circuits/qasm/<name>.qasm (Toffoli level: the
files are written with ccx, cx, h, x and, for qft_4, s/sdg/t/tdg).  Every
file is converted to Clifford+T with pyzx (Circuit.load -> to_basic_gates ->
to_qasm), which expands each ccx into the standard 7-T decomposition.  pytket's
QASM reader accepts ccx (as OpType.CCX), so the conversion is not forced by the
reader; it is done so that the family is Clifford+T as written and its T-count
is the one quoted in the literature (e.g. tof_3 = 21, mod5_4 = 28).

Outputs bench/family_B1/<name>.qasm and bench/family_B1/manifest.csv with
  file, n, n_gates, t_count_as_written, n_cx_as_written, n_ccx_source,
  n_gates_source, t_count_source, source_path, commit
where *_source refers to the Toffoli-level file in the fork and the other
counts refer to the converted file that is written here.

Usage: python bench/build_family_B1.py [--max-qubits 12]
"""

import argparse
import os
import re
import subprocess
from fractions import Fraction

import pandas as pd
import pyzx
from pytket import OpType
from pytket.qasm import circuit_from_qasm_str

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORK = os.path.join(ROOT, "third_party", "pyzx-fork")
SRC = os.path.join(FORK, "circuits", "qasm")
OUT = os.path.join(ROOT, "bench", "family_B1")


def t_count_tket(circ) -> int:
    """T, Tdg and Rz with angle an odd multiple of pi/4 (pytket params are in
    units of pi, so an odd multiple of 1/4)."""
    n = 0
    for cmd in circ.get_commands():
        t = cmd.op.type
        if t in (OpType.T, OpType.Tdg):
            n += 1
        elif t == OpType.Rz:
            f = Fraction(float(cmd.op.params[0])).limit_denominator(2 ** 20) % 2
            if f.denominator == 4:
                n += 1
    return n


def count_src(path):
    """Gate statistics of the Toffoli-level source file by line parsing."""
    n_ccx = n_t = n_gates = 0
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(("OPENQASM", "include", "qreg", "creg", "//")):
                continue
            n_gates += 1
            op = s.split()[0]
            if op == "ccx":
                n_ccx += 1
            elif op in ("t", "tdg"):
                n_t += 1
    return n_gates, n_ccx, n_t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-qubits", type=int, default=12)
    a = ap.parse_args()
    commit = subprocess.check_output(["git", "-C", FORK, "rev-parse", "HEAD"],
                                     text=True).strip()
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".qasm"):
            continue
        path = os.path.join(SRC, fn)
        with open(path) as f:
            head = f.read(4000)
        n = sum(int(m) for m in re.findall(r"qreg\s+\w+\[(\d+)\]", head))
        if n > a.max_qubits:
            continue
        pz = pyzx.Circuit.load(path)
        basic = pz.to_basic_gates()
        qasm = basic.to_qasm()
        name = fn.replace("^", "_pow_")  # keep file names shell-safe
        with open(os.path.join(OUT, name), "w") as f:
            f.write(qasm)
        tk = circuit_from_qasm_str(qasm)
        assert tk.n_qubits == n == pz.qubits, (fn, tk.n_qubits, n, pz.qubits)
        n_gates_src, n_ccx_src, n_t_src = count_src(path)
        rows.append({
            "file": name,
            "n": n,
            "n_gates": tk.n_gates,
            "t_count_as_written": t_count_tket(tk),
            "n_cx_as_written": tk.n_gates_of_type(OpType.CX),
            "n_h_as_written": tk.n_gates_of_type(OpType.H),
            "ops_as_written": ",".join(sorted({c.op.type.name for c in tk.get_commands()})),
            "pyzx_tcount": basic.tcount(),
            "n_gates_source": n_gates_src,
            "n_ccx_source": n_ccx_src,
            "t_count_source": n_t_src,
            "source_path": os.path.relpath(path, ROOT),
            "commit": commit,
        })
        print(f"{name:28s} n={n:2d} gates={tk.n_gates:6d} T={rows[-1]['t_count_as_written']:5d} "
              f"cx={rows[-1]['n_cx_as_written']:6d} (source: {n_gates_src} gates, {n_ccx_src} ccx)")
    man = pd.DataFrame(rows).sort_values(["n", "file"]).reset_index(drop=True)
    man.to_csv(os.path.join(OUT, "manifest.csv"), index=False)
    print(f"{len(man)} circuits, commit {commit}")


if __name__ == "__main__":
    main()
