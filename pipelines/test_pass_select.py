"""Self-running tests for pass_select.py.  Run: python3 pipelines/test_pass_select.py

pass_select.py is loaded by file path . The old name select.py clashed with the stdlib
module of the same name, which is built into this interpreter.

(a) on 6 circuits (family_B1: vbe_adder_3, qft_4, tof_3; family_A:
    xxz_n4_r2_disorder_s1, ladder_n4_r1_disorder_s3, ladder_n4_r1_disorder_s2)
    the selector's choice and HQC equal the choice derived from
    results/family_*_counts.csv, and the CSV HQC / n_2q of P0 and P2 equal
    those recomputed from results/compiled/{P0,P2}/<file>.
(b) selector HQC <= P0 HQC on every circuit of (a).
(c) tie-break rule with a fake compile function.
"""

import importlib.util
import os
import sys

import pandas as pd
from pytket import Circuit
from pytket.qasm import circuit_from_qasm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compile as C  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "pass_select", os.path.join(HERE, "pass_select.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

SHOTS = 1000
CASES = [
    ("family_B1", "vbe_adder_3.qasm"),
    ("family_B1", "qft_4.qasm"),
    ("family_B1", "tof_3.qasm"),
    ("family_A", "xxz_n4_r2_disorder_s1.qasm"),
    ("family_A", "ladder_n4_r1_disorder_s3.qasm"),
    ("family_A", "ladder_n4_r1_disorder_s2.qasm"),
]
_COUNTS = {}
_RESULTS = {}


def _counts(family):
    if family not in _COUNTS:
        _COUNTS[family] = pd.read_csv(
            os.path.join(ROOT, "results", f"{family}_counts.csv"))
    return _COUNTS[family]


def _derived(family, file):
    """Choice from the CSV with the selector's rule, after checking the CSV
    against the saved compiled QASM."""
    d = _counts(family)
    vals = {}
    for p in ("P0", "P2"):
        r = d[(d.file == file) & (d.pipeline == p)]
        assert len(r) == 1, (family, file, p, len(r))
        r = r.iloc[0]
        assert r.status == "ok", (file, p, r.status)
        q = circuit_from_qasm(os.path.join(ROOT, "results", "compiled", p, file))
        h_q, n_q = C.hqc(q, shots=SHOTS), S.n_2q(q)  # measure-all is in the file
        assert abs(h_q - r.hqc) < 1e-9 and n_q == r.n_2q, (file, p, h_q, r.hqc, n_q, r.n_2q)
        vals[p] = (float(r.hqc), int(r.n_2q))
    order = {"P0": 0, "P2": 1}
    best = min(vals, key=lambda p: (round(vals[p][0], 9), vals[p][1], order[p]))
    return best, vals


def _select(family, file):
    if (family, file) not in _RESULTS:
        circ = circuit_from_qasm(os.path.join(ROOT, "bench", family, file))
        _RESULTS[(family, file)] = S.compile_select(circ, shots=SHOTS)
    return _RESULTS[(family, file)]


def test_a_matches_saved_results():
    for family, file in CASES:
        best, vals = _derived(family, file)
        comp, rec = _select(family, file)
        assert rec["chosen"] == best, (file, rec, best, vals)
        h = C.hqc(comp, shots=SHOTS, n_measure=comp.n_qubits)
        assert abs(h - vals[best][0]) < 1e-9, (file, h, vals)
        for p in ("P0", "P2"):
            r = rec["candidates"][p]
            assert r["status"] == "ok", (file, p, r)
            assert abs(r["hqc"] - vals[p][0]) < 1e-9 and r["n_2q"] == vals[p][1], (file, p, r, vals[p])
        print(f"  {file}: chosen {best}  P0 {vals['P0']}  P2 {vals['P2']}")


def test_b_never_worse_than_p0():
    for family, file in CASES:
        comp, rec = _select(family, file)
        h = C.hqc(comp, shots=SHOTS, n_measure=comp.n_qubits)
        assert h <= rec["candidates"]["P0"]["hqc"] + 1e-9, (file, rec)
        assert h <= _derived(family, file)[1]["P0"][0] + 1e-9, (file, rec)


def _fake_circ(n1q, n2q):
    """2-qubit native circuit with n1q PhasedX and n2q ZZMax."""
    c = Circuit(2)
    for _ in range(n1q):
        c.PhasedX(0.5, 0.0, 0)
    for _ in range(n2q):
        c.ZZMax(0, 1)
    return c


def _run_fake(spec, candidates=("P0", "P2")):
    """spec: name -> (n1q, n2q) or an Exception to raise, or "bad-check"."""
    def fake_compile(name, circ):
        s = spec[name]
        if isinstance(s, Exception):
            raise s
        if s == "non-native":
            c = Circuit(2)
            c.CX(0, 1)
            return c, {}
        if s == "bad-check":
            return _fake_circ(0, 1), {}
        return _fake_circ(*s), {}

    def fake_check(comp, ref):
        bad = comp.n_gates == 1 and S.n_2q(comp) == 1
        return {"check_ok": not bad, "check_dev": 1.0 if bad else 0.0}

    return S.compile_select(Circuit(2), shots=SHOTS, candidates=candidates,
                            compile_fn=fake_compile, check_fn=fake_check)


def test_c_tie_break():
    # HQC = 5 + (n1q + 10 n2q + 5*2*2) * 0.2 for a 2-qubit circuit
    # lower HQC wins
    assert _run_fake({"P0": (0, 3), "P2": (0, 2)})[1]["chosen"] == "P2"
    assert _run_fake({"P0": (0, 2), "P2": (0, 3)})[1]["chosen"] == "P0"
    # equal HQC (n1q + 10 n2q = 20), lower n_2q wins
    _, rec = _run_fake({"P0": (0, 2), "P2": (10, 1)})
    assert rec["candidates"]["P0"]["hqc"] == rec["candidates"]["P2"]["hqc"], rec
    assert rec["chosen"] == "P2", rec
    _, rec = _run_fake({"P0": (10, 1), "P2": (0, 2)})
    assert rec["chosen"] == "P0", rec
    # equal HQC and n_2q -> P0, regardless of candidate order
    assert _run_fake({"P0": (2, 2), "P2": (2, 2)})[1]["chosen"] == "P0"
    assert _run_fake({"P0": (2, 2), "P2": (2, 2)},
                     candidates=("P2", "P0"))[1]["chosen"] == "P0"
    # failures are dropped and recorded
    _, rec = _run_fake({"P0": (0, 3), "P2": RuntimeError("boom")})
    assert rec["chosen"] == "P0" and rec["candidates"]["P2"]["status"] == "dropped-error"
    assert "boom" in rec["candidates"]["P2"]["error"]
    _, rec = _run_fake({"P0": "bad-check", "P2": (0, 3)})
    assert rec["chosen"] == "P2" and rec["candidates"]["P0"]["status"] == "dropped-check"
    _, rec = _run_fake({"P0": (0, 3), "P2": "non-native"})
    assert rec["chosen"] == "P0" and rec["candidates"]["P2"]["status"] == "dropped-non-native"
    comp, rec = _run_fake({"P0": RuntimeError("x"), "P2": "bad-check"})
    assert comp is None and rec["chosen"] is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all tests passed")
