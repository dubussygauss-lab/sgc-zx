"""Build family C: application-scale arithmetic and Grover-oracle circuits,
20 to 56 qubits (H2 has 56 qubits), from published constructions as
implemented in qiskit 2.5.2.

Every circuit is built from qiskit's circuit library / synthesis module,
transpiled with optimization_level=0 to the basis
{cx, h, t, tdg, s, sdg, x, z, rz} (no optimisation, only unrolling) and
written as OPENQASM 2.0 on a single register q[n], the convention of the
other families.  Toffoli-based constructions come out Clifford+T.  The
QFT-based constructions (Draper adder, RGQFT multiplier) contain Rz
rotations by angles pi/2^k that are not multiples of pi/4, and the HRS
multiplier (default CDKM adder, controlled) unrolls to multi-controlled gates
whose qiskit decomposition also has such angles.  They are kept as continuous
Rz angles (columns n_rz_non_cliffordT_as_written, continuous_angles) and are
not synthesised to Clifford+T.

Constructions (source citations checked against the arXiv abstract pages):
  cdkm   CDKMRippleCarryAdder(n, kind="full"), 2n+2 qubits
         Cuccaro, Draper, Kutin, Moulton, "A new quantum ripple-carry
         addition circuit", arXiv:quant-ph/0410184 (2004)
  vbe    VBERippleCarryAdder(n, kind="full"), 3n+1 qubits
         Vedral, Barenco, Ekert, "Quantum Networks for Elementary Arithmetic
         Operations", arXiv:quant-ph/9511018 (1995)
  draper DraperQFTAdder(n, kind="fixed"), 2n qubits (addition mod 2^n)
         Draper, "Addition on a Quantum Computer", arXiv:quant-ph/0008033 (2000)
  modadd ModularAdderGate(n).definition = adder_modular_v17, 2n qubits,
         addition mod 2^n without ancillas
         Gidney, "Factoring with n+2 clean qubits and n-1 dirty qubits",
         arXiv:1706.07884 (2017)
  mcxc   synth_mcx_n_clean_m15(k): k-controlled X with k-2 clean ancillas,
         2k-1 qubits (relative-phase Toffoli V-chain)
         Maslov, "On the advantages of using relative phase Toffolis with an
         application to multiple control Toffoli optimization",
         arXiv:1508.03273 (2015)
  mcxd   synth_mcx_n_dirty_i15(k): k-controlled X with k-2 dirty ancillas,
         2k-1 qubits
         Iten, Colbeck, Kukuljan, Home, Christandl, "Quantum Circuits for
         Isometries", arXiv:1501.06911 (2015), after Barenco et al.
         arXiv:quant-ph/9503016
  mcxb   synth_mcx_1_clean_b95(k): k-controlled X with one clean ancilla,
         k+2 qubits (Barenco et al. Lemma 7.3 split into two MCX with dirty
         ancillas, Iten et al. Lemma 8)
         Barenco et al., "Elementary gates for quantum computation",
         arXiv:quant-ph/9503016 (1995); Iten et al. arXiv:1501.06911
  hrs    HRSCumulativeMultiplier(n), 4n+1 qubits, default adder CDKM; the
         controlled adders unroll to multi-controlled gates whose qiskit
         decomposition contains continuous Rz angles
         Haner, Roetteler, Svore, "Optimizing Quantum Circuits for
         Arithmetic", arXiv:1805.12445 (2018)
  rgqft  RGQFTMultiplier(n), 4n qubits (product mod 2^(2n))
         Ruiz-Perez, Garcia-Escartin, "Quantum arithmetic with the Quantum
         Fourier Transform", arXiv:1411.5949 (2014)

Not built: a modular adder or multiplier modulo an arbitrary N (Beauregard
type); qiskit 2.5.2 has none in its library.  ModularAdderGate is addition
modulo 2^n.

Outputs bench/family_C/<name>.qasm and bench/family_C/manifest.csv with
  file, n, n_qubits, application, construction, source_citation,
  qiskit_call, n_gates, t_count_as_written, n_cx_as_written,
  n_rz_non_cliffordT_as_written, ops_as_written, classical_reversible,
  qft_based, continuous_angles
(n = n_qubits, kept for run_bench_B.py compatibility.)

Usage: python3 bench/build_family_C.py
"""

import os
import warnings
from fractions import Fraction
import math

import pandas as pd
from pytket import OpType
from pytket.qasm import circuit_from_qasm_str
from qiskit import QuantumCircuit, QuantumRegister, qasm2, transpile
import qiskit.circuit.library as L
from qiskit.synthesis import synth_mcx_1_clean_b95, synth_mcx_n_clean_m15, synth_mcx_n_dirty_i15

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "bench", "family_C")
BASIS = ["cx", "h", "t", "tdg", "s", "sdg", "x", "z", "rz"]

CIT = {
    "cdkm": "Cuccaro, Draper, Kutin, Moulton, arXiv:quant-ph/0410184 (2004)",
    "vbe": "Vedral, Barenco, Ekert, arXiv:quant-ph/9511018 (1995)",
    "draper": "Draper, arXiv:quant-ph/0008033 (2000)",
    "modadd": "Gidney, arXiv:1706.07884 (2017)",
    "mcxc": "Maslov, arXiv:1508.03273 (2015)",
    "mcxd": "Iten, Colbeck, Kukuljan, Home, Christandl, arXiv:1501.06911 (2015); Barenco et al., arXiv:quant-ph/9503016",
    "mcxb": "Barenco et al., arXiv:quant-ph/9503016 (1995); Iten, Colbeck, Kukuljan, Home, Christandl, arXiv:1501.06911 (2015)",
    "hrs": "Haner, Roetteler, Svore, arXiv:1805.12445 (2018)",
    "rgqft": "Ruiz-Perez, Garcia-Escartin, arXiv:1411.5949 (2014)",
}

# (name, application, construction, qiskit call, builder)
SPECS = [
    ("cdkm_adder_10", "adder", "ripple-carry adder (CDKM), 10-bit, full", "cdkm",
     "CDKMRippleCarryAdder(10, kind='full')", lambda: L.CDKMRippleCarryAdder(10, kind="full")),
    ("cdkm_adder_15", "adder", "ripple-carry adder (CDKM), 15-bit, full", "cdkm",
     "CDKMRippleCarryAdder(15, kind='full')", lambda: L.CDKMRippleCarryAdder(15, kind="full")),
    ("cdkm_adder_20", "adder", "ripple-carry adder (CDKM), 20-bit, full", "cdkm",
     "CDKMRippleCarryAdder(20, kind='full')", lambda: L.CDKMRippleCarryAdder(20, kind="full")),
    ("cdkm_adder_27", "adder", "ripple-carry adder (CDKM), 27-bit, full", "cdkm",
     "CDKMRippleCarryAdder(27, kind='full')", lambda: L.CDKMRippleCarryAdder(27, kind="full")),
    ("vbe_adder_7", "adder", "ripple-carry adder (VBE), 7-bit, full", "vbe",
     "VBERippleCarryAdder(7, kind='full')", lambda: L.VBERippleCarryAdder(7, kind="full")),
    ("vbe_adder_11", "adder", "ripple-carry adder (VBE), 11-bit, full", "vbe",
     "VBERippleCarryAdder(11, kind='full')", lambda: L.VBERippleCarryAdder(11, kind="full")),
    ("vbe_adder_18", "adder", "ripple-carry adder (VBE), 18-bit, full", "vbe",
     "VBERippleCarryAdder(18, kind='full')", lambda: L.VBERippleCarryAdder(18, kind="full")),
    ("modadd_2n_10", "adder", "adder mod 2^n, no ancilla (v17), 10-bit", "modadd",
     "ModularAdderGate(10).definition", lambda: L.ModularAdderGate(10).definition),
    ("modadd_2n_20", "adder", "adder mod 2^n, no ancilla (v17), 20-bit", "modadd",
     "ModularAdderGate(20).definition", lambda: L.ModularAdderGate(20).definition),
    ("draper_adder_10", "QFT adder", "QFT adder (Draper), 10-bit, mod 2^n", "draper",
     "DraperQFTAdder(10, kind='fixed')", lambda: L.DraperQFTAdder(10, kind="fixed")),
    ("draper_adder_16", "QFT adder", "QFT adder (Draper), 16-bit, mod 2^n", "draper",
     "DraperQFTAdder(16, kind='fixed')", lambda: L.DraperQFTAdder(16, kind="fixed")),
    ("draper_adder_28", "QFT adder", "QFT adder (Draper), 28-bit, mod 2^n", "draper",
     "DraperQFTAdder(28, kind='fixed')", lambda: L.DraperQFTAdder(28, kind="fixed")),
    ("mcx_clean_11", "Grover oracle (MCX)", "11-controlled X, 9 clean ancillas", "mcxc",
     "synth_mcx_n_clean_m15(11)", lambda: synth_mcx_n_clean_m15(11)),
    ("mcx_clean_20", "Grover oracle (MCX)", "20-controlled X, 18 clean ancillas", "mcxc",
     "synth_mcx_n_clean_m15(20)", lambda: synth_mcx_n_clean_m15(20)),
    ("mcx_clean_28", "Grover oracle (MCX)", "28-controlled X, 26 clean ancillas", "mcxc",
     "synth_mcx_n_clean_m15(28)", lambda: synth_mcx_n_clean_m15(28)),
    ("mcx_b95_20", "Grover oracle (MCX)", "20-controlled X, 1 clean ancilla (Barenco)", "mcxb",
     "synth_mcx_1_clean_b95(20)", lambda: synth_mcx_1_clean_b95(20)),
    ("mcx_b95_54", "Grover oracle (MCX)", "54-controlled X, 1 clean ancilla (Barenco)", "mcxb",
     "synth_mcx_1_clean_b95(54)", lambda: synth_mcx_1_clean_b95(54)),
    ("mcx_dirty_28", "Grover oracle (MCX)", "28-controlled X, 26 dirty ancillas", "mcxd",
     "synth_mcx_n_dirty_i15(28)", lambda: synth_mcx_n_dirty_i15(28)),
    ("hrs_mult_5", "multiplier", "cumulative multiplier (HRS), 5x5-bit", "hrs",
     "HRSCumulativeMultiplier(5)", lambda: L.HRSCumulativeMultiplier(5)),
    ("rgqft_mult_6", "multiplier", "QFT multiplier (RG), 6x6-bit", "rgqft",
     "RGQFTMultiplier(6)", lambda: L.RGQFTMultiplier(6)),
]

QFT_BASED = {"draper", "rgqft"}


def t_count_tket(circ) -> int:
    """T, Tdg and Rz with angle an odd multiple of pi/4 (as bench/build_family_B1.py)."""
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


def n_rz_non_cliffordT(circ) -> int:
    """Rz whose angle (units of pi) is not a multiple of 1/4."""
    n = 0
    for cmd in circ.get_commands():
        if cmd.op.type == OpType.Rz:
            x = float(cmd.op.params[0]) * 4
            if abs(x - round(x)) > 1e-9:
                n += 1
    return n


def to_single_register(qc: QuantumCircuit) -> QuantumCircuit:
    q = QuantumRegister(qc.num_qubits, "q")
    out = QuantumCircuit(q, global_phase=qc.global_phase)
    out.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
    return out


def main():
    warnings.simplefilter("ignore", DeprecationWarning)
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, app, constr, key, call, build in SPECS:
        qc = build()
        if not isinstance(qc, QuantumCircuit):
            qc = qc.definition
        tq = transpile(to_single_register(qc), basis_gates=BASIS, optimization_level=0)
        tq = to_single_register(tq)
        qasm = qasm2.dumps(tq)
        fn = name + ".qasm"
        with open(os.path.join(OUT, fn), "w") as f:
            f.write(qasm)
        tk = circuit_from_qasm_str(qasm)
        assert tk.n_qubits == tq.num_qubits
        ops = sorted({c.op.type.name for c in tk.get_commands()})
        assert set(ops) <= {"CX", "H", "T", "Tdg", "S", "Sdg", "X", "Z", "Rz"}, ops
        rows.append({
            "file": fn,
            "n": tk.n_qubits,
            "n_qubits": tk.n_qubits,
            "application": app,
            "construction": constr,
            "source_citation": CIT[key],
            "qiskit_call": call,
            "n_gates": tk.n_gates,
            "t_count_as_written": t_count_tket(tk),
            "n_cx_as_written": tk.n_gates_of_type(OpType.CX),
            "n_rz_non_cliffordT_as_written": n_rz_non_cliffordT(tk),
            "ops_as_written": ",".join(ops),
            "classical_reversible": True,  # every construction maps basis states to basis states
            "qft_based": key in QFT_BASED,
            # continuous Rz angles (not multiples of pi/4) as written: QFT
            # rotations (draper, rgqft) or qiskit's unrolling of the
            # controlled CDKM adder inside HRSCumulativeMultiplier
            "continuous_angles": n_rz_non_cliffordT(tk) > 0,
        })
        r = rows[-1]
        print(f"{fn:22s} n={r['n']:2d} gates={r['n_gates']:6d} T={r['t_count_as_written']:5d} "
              f"cx={r['n_cx_as_written']:5d} rz_cont={r['n_rz_non_cliffordT_as_written']}", flush=True)
    man = pd.DataFrame(rows).sort_values(["n", "file"]).reset_index(drop=True)
    man.to_csv(os.path.join(OUT, "manifest.csv"), index=False)
    print(f"{len(man)} circuits")


if __name__ == "__main__":
    main()
