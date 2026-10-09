"""Self-running tests for the PSEL4 candidates of pass_select.py.
Run: python3 pipelines/test_psel4.py

(a) default candidates are still ("P0", "P2"); PSEL4 candidates are
    ("P0", "P2", "L3", "P2L3").
(b) tie-break among four candidates with a fake compile function:
    lower HQC, then lower n_2q, then P0, L3, P2, P2L3, regardless of the
    candidate order; failures are dropped.
(c) on two small circuits (family_B1 tof_3, family_A tfim_n4_r1_uniform_s1)
    PSEL4 with the real compilers: every candidate passes, the chosen HQC is
    the minimum of the four and <= PSEL, and L3 / P2L3 of tof_3 equal the
    stored rows of results/strong_baselines.csv.
(d) the CLI flag --psel4 runs all four candidates.
"""

import contextlib
import importlib.util
import io
import os
import sys

import pandas as pd
from pytket import Circuit
from pytket.qasm import circuit_from_qasm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

_spec = importlib.util.spec_from_file_location(
    "pass_select", os.path.join(HERE, "pass_select.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

SHOTS = 1000
FOUR = ("P0", "P2", "L3", "P2L3")
SMALL = [("family_B1", "tof_3.qasm"), ("family_A", "tfim_n4_r1_uniform_s1.qasm")]


def test_a_candidate_sets():
    assert S.DEFAULT_CANDIDATES == ("P0", "P2")
    assert S.PSEL4_CANDIDATES == FOUR


def _fake_circ(n1q, n2q):
    c = Circuit(2)
    for _ in range(n1q):
        c.PhasedX(0.5, 0.0, 0)
    for _ in range(n2q):
        c.ZZMax(0, 1)
    return c


def _run_fake(spec, candidates=FOUR):
    def fake_compile(name, circ):
        s = spec[name]
        if isinstance(s, Exception):
            raise s
        return _fake_circ(*s), {}

    def fake_check(comp, ref):
        return {"check_ok": True, "check_dev": 0.0}

    return S.compile_select(Circuit(2), shots=SHOTS, candidates=candidates,
                            compile_fn=fake_compile, check_fn=fake_check)[1]


def test_b_tie_break():
    eq = (2, 2)
    # lower HQC wins
    assert _run_fake({"P0": (0, 3), "P2": (0, 3), "L3": (0, 3), "P2L3": (0, 2)})["chosen"] == "P2L3"
    # equal HQC (n1q + 10 n2q = 20), lower n_2q wins
    assert _run_fake({"P0": (0, 2), "P2": (0, 2), "L3": (10, 1), "P2L3": (0, 2)})["chosen"] == "L3"
    # full ties: P0, then L3, then P2, then P2L3, for any candidate order
    for order in (FOUR, tuple(reversed(FOUR))):
        assert _run_fake({c: eq for c in FOUR}, order)["chosen"] == "P0"
        assert _run_fake({"P0": (0, 3), "P2": eq, "L3": eq, "P2L3": eq}, order)["chosen"] == "L3"
        assert _run_fake({"P0": (0, 3), "P2": eq, "L3": (0, 3), "P2L3": eq}, order)["chosen"] == "P2"
    # a failing candidate is dropped
    rec = _run_fake({"P0": (0, 3), "P2": (0, 3), "L3": RuntimeError("x"), "P2L3": (0, 3)})
    assert rec["chosen"] == "P0" and rec["candidates"]["L3"]["status"] == "dropped-error"


def test_c_real_small():
    sb = pd.read_csv(os.path.join(ROOT, "results", "strong_baselines.csv"))
    for family, file in SMALL:
        circ = circuit_from_qasm(os.path.join(ROOT, "bench", family, file))
        comp, rec = S.compile_select(circ, shots=SHOTS, candidates=FOUR)
        cands = rec["candidates"]
        for c in FOUR:
            assert cands[c]["status"] == "ok", (file, c, cands[c])
        h = S.C.hqc(comp, shots=SHOTS, n_measure=comp.n_qubits)
        assert abs(h - min(cands[c]["hqc"] for c in FOUR)) < 1e-9, (file, rec)
        assert h <= min(cands["P0"]["hqc"], cands["P2"]["hqc"]) + 1e-9
        if family == "family_B1":
            for v in ("L3", "P2L3"):
                r = sb[(sb.family == "B1") & (sb.file == file) & (sb.variant == v)].iloc[0]
                assert abs(r.hqc - cands[v]["hqc"]) < 1e-9 and r.n_2q == cands[v]["n_2q"], (v, r.hqc, cands[v])
        print(f"  {file}: chosen {rec['chosen']} "
              + " ".join(f"{c}={cands[c]['hqc']:.1f}" for c in FOUR))


def test_d_cli():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        S.main(["--psel4", os.path.join(ROOT, "bench", "family_B1", "tof_3.qasm")])
    head, row = buf.getvalue().strip().split("\n")
    for c in FOUR:
        assert f"hqc_{c}" in head.split("\t"), head
    assert row.split("\t")[0] == "tof_3.qasm"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all tests passed")
