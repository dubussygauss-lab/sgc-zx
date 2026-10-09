"""Tests for equiv_family_C: one positive and one deliberately broken case."""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
import equiv_family_C as E  # noqa: E402
from pytket import Circuit  # noqa: E402
from pytket.qasm import circuit_from_qasm_str  # noqa: E402

GRID = lambda x: Fraction(round(x * 2 ** 8), 2 ** 8)  # noqa: E731


def _toffoli_ish():
    c = Circuit(3)
    c.H(2).CX(1, 2).Tdg(2).CX(0, 2).T(2).CX(1, 2).Tdg(2).CX(0, 2)
    c.T(1).T(2).H(2).CX(0, 1).T(0).Tdg(1).CX(0, 1).CX(2, 0)
    return c


def _graphs(ref, comp_qasm):
    u_ref, p_ref = E.strip_measures(ref)
    u_cmp, p_cmp = E.strip_measures(circuit_from_qasm_str(comp_qasm, maxwidth=64))
    o_ref, _ = E.to_ops(u_ref, GRID)
    o_cmp, _ = E.to_ops(u_cmp, GRID)
    n = ref.n_qubits
    return E.ops_to_graph(o_ref, n, p_ref), E.ops_to_graph(o_cmp, n, p_cmp)


def _compiled_qasm(ref):
    comp, _ = C.compile_pipeline("P0", ref)
    return C.to_qasm(C.add_measure_all(comp))


def test_positive_P0_output_proven():
    ref = _toffoli_ish()
    gA, gB = _graphs(ref, _compiled_qasm(ref))
    assert E.miter_is_identity(gA, gB)[0]


def test_negative_broken_output_not_proven():
    ref = _toffoli_ish()
    q = _compiled_qasm(ref).splitlines()
    i = next(k for k, l in enumerate(q) if l.startswith("RZZ"))
    del q[i]                      # drop one two-qubit gate
    gA, gB = _graphs(ref, "\n".join(q) + "\n")
    assert not E.miter_is_identity(gA, gB)[0]
