"""Build family B1x: the benchmark circuits of the Quantinuum pyzx fork with
13 <= n <= 20 qubits and at most --max-gates gates after ccx expansion.
Same conversion as build_family_B1.py (pyzx Circuit.load -> to_basic_gates ->
to_qasm), same manifest columns.  Writes bench/family_B1x/.

Usage: python bench/build_family_B1x.py [--min-qubits 13] [--max-qubits 20]
                                        [--max-gates 3000]
"""

import argparse
import os
import re
import subprocess
import sys

import pandas as pd
import pyzx
from pytket import OpType
from pytket.qasm import circuit_from_qasm_str

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_family_B1 import FORK, ROOT, SRC, count_src, t_count_tket  # noqa: E402

OUT = os.path.join(ROOT, "bench", "family_B1x")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-qubits", type=int, default=13)
    ap.add_argument("--max-qubits", type=int, default=20)
    ap.add_argument("--max-gates", type=int, default=3000)
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
        if not (a.min_qubits <= n <= a.max_qubits):
            continue
        n_gates_src, n_ccx_src, n_t_src = count_src(path)
        # ccx -> 15 basic gates (6 cx, 7 t/tdg, 2 h); skip the huge ones
        # before loading them
        if n_gates_src + 14 * n_ccx_src > a.max_gates:
            print(f"skip {fn}: ~{n_gates_src + 14 * n_ccx_src} gates after expansion")
            continue
        pz = pyzx.Circuit.load(path)
        basic = pz.to_basic_gates()
        qasm = basic.to_qasm()
        name = fn.replace("^", "_pow_")
        tk = circuit_from_qasm_str(qasm)
        assert tk.n_qubits == n == pz.qubits, (fn, tk.n_qubits, n, pz.qubits)
        if tk.n_gates > a.max_gates:
            print(f"skip {fn}: {tk.n_gates} gates after expansion")
            continue
        with open(os.path.join(OUT, name), "w") as f:
            f.write(qasm)
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
