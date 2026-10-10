"""Fast tests of the basis-input check (pipelines/pass_select.py) and of
value/psel4_basis_check.py.  Run: python3 -m pytest value/test_psel4_basis_check.py -q

(a) basis_inputs: 64 distinct inputs, all-zero first, fixed by the seed.
(b) the simulator reproduces the columns of pytket's get_unitary, implicit
    qubit permutation and global phase included (L3 of qft_4 carries a
    nontrivial permutation).
(c) on 2 ledger circuits with 9 and 10 qubits (B1 mod_mult_55, family A
    ladder_n10_r1_disorder_s1) the PSEL4 pick and every required candidate
    pass the basis check on 64 inputs.
(d) negative controls on mod_mult_55: the input circuit with one CX
    reversed, the input circuit with an extra X, and the input circuit with
    an extra Z on an input qubit must fail.  The extra Z leaves the all-zero
    output unchanged, so the old all-zero check passes it and only the
    basis check with a common global phase catches it.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pytket import Circuit, OpType
from pytket.qasm import circuit_from_qasm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
sys.path.insert(0, str(ROOT / "value"))
import compile as C  # noqa: E402
import pass_select as PS  # noqa: E402
import psel4_basis_check as B  # noqa: E402

LED = pd.read_csv(ROOT / "value/psel4_ledger.csv")


def _row(file):
    r = LED[LED.file == file]
    assert len(r) == 1
    return r.iloc[0].to_dict()


def _circ(file):
    r = _row(file)
    return circuit_from_qasm(str(B.DIRS[r["family"]] / file))


def test_basis_inputs():
    xs = PS.basis_inputs(12)
    assert len(xs) == 64 and len(set(xs.tolist())) == 64
    assert xs[0] == 0 and (xs[1:] > 0).all() and (xs < 2 ** 12).all()
    assert (xs == PS.basis_inputs(12)).all()
    assert (PS.basis_inputs(5) == np.arange(32)).all()


def test_simulator_matches_unitary_columns():
    c = circuit_from_qasm(str(ROOT / "bench/family_B1/qft_4.qasm"))
    comp, _ = PS.compile_candidate("L3", c)
    perm = comp.implicit_qubit_permutation()
    assert any(k != v for k, v in perm.items())
    U = comp.get_unitary()
    for x in range(2 ** comp.n_qubits):
        assert np.abs(PS.statevector_from_basis(comp, x) - U[:, x]).max() < 1e-12


def test_ledger_circuits_pass():
    for file in ("mod_mult_55.qasm", "ladder_n10_r1_disorder_s1.qasm"):
        row = _row(file)
        assert 9 <= row["n_qubits"] <= 20
        out = B.check_circuit(row)
        assert out["n_inputs"] == 64
        assert out[f"basis_{row['pick_PSEL4']}"] == "pass", (file, out)
        for c in B.CANDS:
            if out[f"required_{c}"]:
                assert out[f"basis_{c}"] == "pass", (file, c, out[f"dev_{c}"])


def test_negative_controls():
    file = "mod_mult_55.qasm"
    ref = _circ(file)
    n = ref.n_qubits

    swapped = Circuit(n)
    done = False
    for cmd in ref.get_commands():
        qs = list(cmd.args)
        if cmd.op.type == OpType.CX and not done:
            qs = qs[::-1]
            done = True
        swapped.add_gate(cmd.op, qs)
    assert done

    extra_x = ref.copy()
    extra_x.X(ref.qubits[3])

    extra_z = Circuit(n)
    extra_z.Z(extra_z.qubits[0])
    extra_z.append(ref)

    res = PS.basis_check_many(ref, {"swapped_cx": swapped, "extra_x": extra_x,
                                    "extra_z": extra_z, "ref": ref.copy()})
    assert res["ref"]["check_ok"]
    for k in ("swapped_cx", "extra_x", "extra_z"):
        assert not res[k]["check_ok"], (k, res[k])
    # extra Z: every input matches up to its own phase, the common phase fails
    assert res["extra_z"]["max_infid"] < 1e-8
    assert C.check(extra_z, ref)["check_ok"]
    assert PS.check(extra_z, ref, mode="zero")["check_ok"]
    assert not PS.check(extra_z, ref)["check_ok"]

    # the runner reports a wrong candidate as FAIL
    out = B.check_circuit(_row(file), compile_fn=lambda name, c: PS.compile_candidate(name, c),
                          extra={"extra_x": extra_x})
    assert out["basis_extra_x"] == "FAIL"


def test_default_mode_is_basis():
    ref = _circ("mod_mult_55.qasm")
    assert PS.check(ref.copy(), ref)["check_kind"] == "basis64"
    assert PS.check(ref.copy(), ref, mode="zero")["check_kind"] == "statevector"
    small = circuit_from_qasm(str(ROOT / "bench/family_B1/qft_4.qasm"))
    assert PS.check(small.copy(), small)["check_kind"] == "unitary"
