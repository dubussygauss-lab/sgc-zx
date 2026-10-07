"""Compilation pipelines for Quantinuum H2 and their metrics.

Native gate set: {Rz, PhasedX, ZZPhase, ZZMax, Measure, Reset}, all-to-all,
no routing.  Every pipeline takes a pytket Circuit and returns
(compiled Circuit, metrics dict).

Pipelines
  P0ref  AutoRebase(native) ; SquashRzPhasedX ; RemoveRedundancies
         (what the circuit costs as written, no optimisation)
  P0     pytket-quantinuum default_compilation_pass(optimisation_level=2)
  P0L1   same, optimisation_level=1
  P1     PyZX full_reduce -> extract -> basic_optimization -> P0
  P2     PyZX teleport_reduce -> Circuit.from_graph -> basic_optimization -> P0
  P3     pytket ZXGraphlikeOptimisation -> P0
  P4     PyZX full_reduce tail (as P1) -> P0 without FullPeepholeOptimise

P0 is reproduced from the installed pytket-quantinuum source without a
backend object; see `quantinuum_default_pass` for the citation.
"""

import math
import time
from fractions import Fraction

import numpy as np
import pyzx
from pytket import Circuit, OpType
from pytket.passes import (
    AutoRebase,
    AutoSquash,
    BasePass,
    DecomposeBoxes,
    DecomposeTK2,
    FlattenRelabelRegistersPass,
    FullPeepholeOptimise,
    NormaliseTK2,
    RemovePhaseOps,
    RemoveRedundancies,
    SequencePass,
    SquashRzPhasedX,
    SynthesiseTK,
    ZXGraphlikeOptimisation,
    ZZPhaseToRz,
    scratch_reg_resize_pass,
)
from pytket.qasm import circuit_from_qasm_str, circuit_to_qasm_str
from pyzx.utils import settings as pyzx_settings

NATIVE_1Q = {OpType.Rz, OpType.PhasedX}
NATIVE_2Q = {OpType.ZZPhase, OpType.ZZMax}
NATIVE = NATIVE_1Q | NATIVE_2Q | {OpType.Measure, OpType.Reset}
# Barrier is accepted by the device gate set too (quantinuum.py:_ADDITIONAL_GATES)
# but never produced here.

SHOTS = 1000
CHECK_TOL = 1e-8

PIPELINES = ["P0ref", "P0", "P0L1", "P1", "P2", "P3", "P4"]


# ----------------------------------------------------------------- pass sets

def p0ref_pass() -> BasePass:
    return SequencePass([
        DecomposeBoxes(),
        AutoRebase(NATIVE, allow_swaps=False),
        SquashRzPhasedX(),
        RemoveRedundancies(),
    ])


def quantinuum_default_pass(optimisation_level: int = 2,
                            skip_peephole: bool = False) -> BasePass:
    """pytket-quantinuum 0.59.3 QuantinuumBackend.default_compilation_pass.

    Source: pytket/extensions/quantinuum/backends/quantinuum.py (installed at
    /usr/local/lib/python3.13/dist-packages/...), lines 545-668:
      559-562  passlist = [DecomposeBoxes(), scratch_reg_resize_pass()]
      563      squash = AutoSquash({PhasedX, Rz})
      568-575  target_2qb_gate == ZZPhase -> [NormaliseTK2(),
               DecomposeTK2(allow_swaps=allow_implicit_swaps, ZZPhase_fidelity=1.0)]
      594-605  level 1: SynthesiseTK(); decomposition; rebase_pass();
               ZZPhaseToRz(); RemoveRedundancies(); squash; RemoveRedundancies()
      606-621  level 2: FullPeepholeOptimise(allow_swaps=allow_implicit_swaps,
               target_2qb_gate=TK2); decomposition; rebase_pass();
               RemoveRedundancies(); squash; RemoveRedundancies()
      669      RemovePhaseOps()
      687-688  FlattenRelabelRegistersPass("q")  (preserve_qubit_names=False)
    Backend-dependent inputs and the values used here:
      rebase_pass() (lines 537-543) = AutoRebase((gate_set - 2q gates)
        | {target_2qb_gate}, allow_swaps=allow_implicit_swaps).  gate_set comes
        from backend_info; for H2 it is {Rz, PhasedX, ZZPhase, ZZMax, TK2}
        plus _ADDITIONAL_GATES (Measure, Reset, Barrier, classical ops).
        We use {Rz, PhasedX, ZZPhase, Measure, Reset, Barrier}.
      target_2qb_gate default = ZZPhase (_default_2q_gate, lines 125-128).
      allow_implicit_swaps default = True (QuantinuumBackendCompilationConfig,
        line 221).
    Nothing was dropped.  Level 3 (GreedyPauliSimp) is not reproduced.
    """
    assert optimisation_level in (1, 2)
    allow_swaps = True
    squash = AutoSquash({OpType.PhasedX, OpType.Rz})
    rebase = AutoRebase(
        {OpType.Rz, OpType.PhasedX, OpType.ZZPhase,
         OpType.Measure, OpType.Reset, OpType.Barrier},
        allow_swaps=allow_swaps)
    decomposition = [
        NormaliseTK2(),
        DecomposeTK2(allow_swaps=allow_swaps, ZZPhase_fidelity=1.0),
    ]
    passlist = [DecomposeBoxes(), scratch_reg_resize_pass()]
    if optimisation_level == 1:
        passlist.append(SynthesiseTK())
        passlist.extend(decomposition)
        passlist.extend([rebase, ZZPhaseToRz(), RemoveRedundancies(),
                         squash, RemoveRedundancies()])
    else:
        if not skip_peephole:
            passlist.append(FullPeepholeOptimise(allow_swaps=allow_swaps,
                                                 target_2qb_gate=OpType.TK2))
        passlist.extend(decomposition)
        passlist.extend([rebase, RemoveRedundancies(),
                         squash, RemoveRedundancies()])
    passlist.append(RemovePhaseOps())
    passlist.append(FlattenRelabelRegistersPass("q"))
    return SequencePass(passlist)


# ------------------------------------------------------------- pyzx helpers

def _tket_to_pyzx(circ: Circuit) -> pyzx.Circuit:
    return pyzx.Circuit.from_qasm(circuit_to_qasm_str(circ))


def _pyzx_to_tket(pz: pyzx.Circuit) -> Circuit:
    return circuit_from_qasm_str(pz.to_qasm())


def pyzx_angle_rounding(circ: Circuit) -> float:
    """Max |angle error| in radians introduced by pyzx's float->Fraction
    conversion (qasmparser.parse_phase_arg: Fraction(x/pi).limit_denominator(
    settings.float_to_fraction_max_denominator), default 2**20)."""
    worst = 0.0
    for cmd in circ.get_commands():
        for p in cmd.op.params:
            if isinstance(p, (int, float)):
                f = Fraction(float(p)).limit_denominator(
                    pyzx_settings.float_to_fraction_max_denominator)
                worst = max(worst, abs(float(f) - float(p)) * math.pi)
    return worst


def _pyzx_tail(g) -> pyzx.Circuit:
    g.normalize()
    c = pyzx.extract_circuit(g.copy())
    c = pyzx.optimize.basic_optimization(c.to_basic_gates())
    return c.to_basic_gates()


def pyzx_tcount(pz: pyzx.Circuit) -> int:
    """Number of ZPhase/XPhase gates with phase an odd multiple of pi/4
    (pyzx phases are Fractions in units of pi; odd multiple of 1/4 mod 2 <=>
    denominator 4).  Undefined after rebasing to the H2 gate set."""
    n = 0
    for g in pz.gates:
        if isinstance(g, (pyzx.circuit.gates.ZPhase, pyzx.circuit.gates.XPhase)):
            if (Fraction(g.phase) % 2).denominator == 4:
                n += 1
    return n


def pyzx_non_cliffordT(pz: pyzx.Circuit) -> int:
    """Number of phase gates whose angle is not a multiple of pi/4."""
    n = 0
    for g in pz.gates:
        if isinstance(g, (pyzx.circuit.gates.ZPhase, pyzx.circuit.gates.XPhase)):
            if (Fraction(g.phase) % 2).denominator > 4:
                n += 1
    return n


def zx_full_reduce_pz(circ: Circuit) -> pyzx.Circuit:
    """ZX stage of P1 / P4 as a pyzx Circuit (before any pytket pass)."""
    pz = _tket_to_pyzx(circ)
    g = pz.to_graph()
    pyzx.simplify.full_reduce(g)
    return _pyzx_tail(g)


def zx_teleport_reduce_pz(circ: Circuit) -> pyzx.Circuit:
    """ZX stage of P2 as a pyzx Circuit (before any pytket pass)."""
    # teleport_reduce keeps the circuit structure and only moves phases, so
    # the graph is read back with Circuit.from_graph (the pyzx-documented
    # route); extract_circuit would resynthesise it.
    pz = _tket_to_pyzx(circ)
    g = pyzx.simplify.teleport_reduce(pz.to_graph())
    c = pyzx.Circuit.from_graph(g)
    c = pyzx.optimize.basic_optimization(c.to_basic_gates())
    return c.to_basic_gates()


def zx_full_reduce(circ: Circuit, zx_out: dict = None) -> Circuit:
    """If `zx_out` is a dict, the pyzx circuit of the ZX stage is stored in
    zx_out["pyzx"] so callers can inspect it without re-running the stage."""
    pz = zx_full_reduce_pz(circ)
    if zx_out is not None:
        zx_out["pyzx"] = pz
    return _pyzx_to_tket(pz)


def zx_teleport_reduce(circ: Circuit, zx_out: dict = None) -> Circuit:
    pz = zx_teleport_reduce_pz(circ)
    if zx_out is not None:
        zx_out["pyzx"] = pz
    return _pyzx_to_tket(pz)


# ---------------------------------------------------------------- pipelines

def _run(circ: Circuit, zx_stage, tket_pass: BasePass, zx_out: dict = None):
    c = circ.copy()
    t0 = time.perf_counter()
    if zx_stage is not None:
        c = zx_stage(c) if zx_out is None else zx_stage(c, zx_out)
    t1 = time.perf_counter()
    tket_pass.apply(c)
    t2 = time.perf_counter()
    return c, {"t_zx": t1 - t0, "t_tket": t2 - t1, "t_total": t2 - t0}


def compile_pipeline(name: str, circ: Circuit, zx_out: dict = None):
    """Compile `circ` with pipeline `name` -> (Circuit, timings).  For P1, P2
    and P4, a dict passed as `zx_out` receives the pyzx circuit of the ZX
    stage under key "pyzx" (the stage is run once)."""
    if name == "P0ref":
        return _run(circ, None, p0ref_pass())
    if name == "P0":
        return _run(circ, None, quantinuum_default_pass(2))
    if name == "P0L1":
        return _run(circ, None, quantinuum_default_pass(1))
    if name == "P1":
        return _run(circ, zx_full_reduce, quantinuum_default_pass(2), zx_out)
    if name == "P2":
        return _run(circ, zx_teleport_reduce, quantinuum_default_pass(2), zx_out)
    if name == "P3":
        def zxg(c):
            # ZXGraphlikeOptimisation requires {CX, CZ, Rx, Rz, H, X, Z, SWAP};
            # family A circuits (h, cx, rz, rx) already satisfy it, so the
            # rebase only matters for other inputs (e.g. S, T in the tests).
            c = c.copy()
            AutoRebase({OpType.CX, OpType.Rz, OpType.Rx, OpType.H}).apply(c)
            ZXGraphlikeOptimisation().apply(c)
            return c
        return _run(circ, zxg, quantinuum_default_pass(2))
    if name == "P4":
        return _run(circ, zx_full_reduce,
                    quantinuum_default_pass(2, skip_peephole=True), zx_out)
    raise ValueError(name)


# ------------------------------------------------------------------ metrics

def hqc(circ: Circuit, shots: int = SHOTS, n_measure=None) -> float:
    """HQC estimate, Quantinuum sg_grand_challenge
    src/python/pytket_cost_estimation.py (estimate_cost):
      5 + (n1q + 10*n2q + 5*spam) * shots/5000,
    n1q = PhasedX count, n2q = ZZMax + ZZPhase, spam = n_qubits + Measure +
    Reset.  Rz is free.  n_measure defaults to the Measure count in the circuit,
    pass n_measure=n_qubits for an unmeasured circuit that will be measured."""
    n1q = circ.n_gates_of_type(OpType.PhasedX)
    n2q = circ.n_gates_of_type(OpType.ZZPhase) + circ.n_gates_of_type(OpType.ZZMax)
    if n_measure is None:
        n_measure = circ.n_gates_of_type(OpType.Measure)
    spam = circ.n_qubits + n_measure + circ.n_gates_of_type(OpType.Reset)
    return 5 + (n1q + 10 * n2q + 5 * spam) * shots / 5000


def metrics(circ: Circuit, n_measure=None) -> dict:
    types = {cmd.op.type for cmd in circ.get_commands()}
    bad = types - NATIVE - {OpType.Barrier}
    return {
        "n_qubits": circ.n_qubits,
        "n_2q": circ.n_gates_of_type(OpType.ZZPhase) + circ.n_gates_of_type(OpType.ZZMax),
        "n_zzphase": circ.n_gates_of_type(OpType.ZZPhase),
        "n_zzmax": circ.n_gates_of_type(OpType.ZZMax),
        "depth_2q": circ.depth_by_type(NATIVE_2Q),
        "n_phasedx": circ.n_gates_of_type(OpType.PhasedX),
        "n_rz": circ.n_gates_of_type(OpType.Rz),
        "n_total": circ.n_gates,
        "depth": circ.depth(),
        "hqc": hqc(circ, n_measure=n_measure),
        "native": len(bad) == 0,
        "non_native_ops": ",".join(sorted(t.name for t in bad)),
    }


# ------------------------------------------------------------- correctness

def unitary_deviation(U: np.ndarray, V: np.ndarray) -> float:
    """1 - |tr(U^dag V)| / 2^n, zero iff U = V up to global phase."""
    d = U.shape[0]
    return float(1 - abs(np.trace(U.conj().T @ V)) / d)


def state_infidelity(psi: np.ndarray, phi: np.ndarray) -> float:
    return float(1 - abs(np.vdot(psi, phi)) ** 2)


def statevector(circ: Circuit) -> np.ndarray:
    """Statevector on |0..0>, pytket ILO-BE (q[0] most significant), the
    convention of bench/sv.py and bench/family_A/*.npy.  pytket's own
    get_statevector refuses n > 11, so a numpy simulator is used there; it
    applies the implicit qubit permutation like pytket does."""
    n = circ.n_qubits
    if n <= 11:
        return circ.get_statevector()
    t = np.zeros((2,) * n, dtype=complex)
    t[(0,) * n] = 1.0
    for cmd in circ.get_commands():
        if cmd.op.type == OpType.Barrier:
            continue
        qs = [q.index[0] for q in cmd.args]
        k = len(qs)
        u = cmd.op.get_unitary().reshape((2,) * (2 * k))
        t = np.tensordot(u, t, axes=(list(range(k, 2 * k)), qs))
        # tensordot puts the k output axes first; move them back
        t = np.moveaxis(t, list(range(k)), qs)
    perm = circ.implicit_qubit_permutation()
    order = [None] * n
    for q in circ.qubits:
        order[perm[q].index[0]] = q.index[0]
    t = np.transpose(t, order)
    return t.reshape(-1)


def probs(circ: Circuit) -> np.ndarray:
    return np.abs(statevector(circ)) ** 2


def check(circ: Circuit, ref: Circuit, ref_probs=None, unitary_max_qubits: int = 8) -> dict:
    """Compare `circ` with `ref`.  Unitary check up to n=8, statevector check
    beyond.  pytket's get_unitary / get_statevector include the implicit qubit
    permutation left by allow_swaps=True, so no manual permutation is needed.
    """
    n = circ.n_qubits
    out = {}
    if n <= unitary_max_qubits:
        dev = unitary_deviation(ref.get_unitary(), circ.get_unitary())
        out["check_kind"] = "unitary"
    else:
        dev = state_infidelity(statevector(ref), statevector(circ))
        out["check_kind"] = "statevector"
    out["check_dev"] = dev
    if ref_probs is not None:
        out["dist_maxdiff"] = float(np.max(np.abs(probs(circ) - ref_probs)))
    else:
        out["dist_maxdiff"] = float("nan")
    out["check_ok"] = bool(dev <= CHECK_TOL and
                           (np.isnan(out["dist_maxdiff"]) or out["dist_maxdiff"] <= CHECK_TOL))
    return out


# -------------------------------------------------------------- QASM output

def add_measure_all(circ: Circuit) -> Circuit:
    """Append Measure q[i] -> c[i] for every qubit.  pytket attaches the
    measurement to the output wire labelled q[i], so when the circuit carries an
    implicit qubit permutation (allow_swaps=True) the command list and the QASM
    read "measure q[j] -> c[i]" with j the physical wire; the permutation,
    which pytket's QASM writer otherwise drops, is thereby encoded in the
    measurement map.  Checked by probs_from_measured_qasm in the tests."""
    c = circ.copy()
    c.add_c_register("c", c.n_qubits)
    for q in c.qubits:
        c.Measure(q, q.index[0])
    return c


def to_qasm(circ: Circuit) -> str:
    return circuit_to_qasm_str(circ, header="hqslib1")


def probs_from_measured_qasm(qasm: str) -> np.ndarray:
    """Z-basis distribution over the classical bits c[0..n-1] of a measured
    QASM circuit (what an emulator would return), in the .npy convention
    (c[0] most significant)."""
    c = circuit_from_qasm_str(qasm)
    n = c.n_qubits
    u = Circuit(n)
    bit_of = {}
    for cmd in c.get_commands():
        if cmd.op.type == OpType.Measure:
            bit_of[cmd.args[0].index[0]] = cmd.args[1].index[0]
        elif cmd.op.type == OpType.Barrier:
            continue
        else:
            u.add_gate(cmd.op, [q.index[0] for q in cmd.args])
    p = np.abs(statevector(u)) ** 2
    assert len(bit_of) == n
    # move axis of qubit j to position bit_of[j]
    t = p.reshape((2,) * n)
    order = [None] * n
    for j, b in bit_of.items():
        order[b] = j
    t = np.transpose(t, order)
    return t.reshape(-1)
