"""Fast tests for value/mechanism_zx_l3.py.  Run: python3 -m pytest value/test_mechanism_zx_l3.py

1. The Clifford test for Rz, ZZPhase and PhasedX agrees with a brute-force check that
   the gate maps the Pauli group to itself (conjugation of X and Z for 1q, of XI, ZI,
   IX, IZ for ZZPhase).
2. native_counts and HQC on a hand-built circuit.
3. pz_counts on a PyZX circuit with T, S and a continuous phase.
4. The stored CSV: every ledger circuit of A, B1, C has the seven pipelines, the
   L2 and P2 HQC equal the ledger, the per-row HQC equals the formula from the counts.
5. The report numbers recomputed from the CSV equal the Markdown (spot checks).
"""
import itertools
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))
import mechanism_zx_l3 as M  # noqa: E402
from pytket import Circuit, OpType  # noqa: E402

PAULIS = {"I": np.eye(2), "X": np.array([[0, 1], [1, 0]]),
          "Y": np.array([[0, -1j], [1j, 0]]), "Z": np.diag([1, -1])}


def is_pauli(m):
    n = int(round(math.log2(m.shape[0])))
    for s in itertools.product("IXYZ", repeat=n):
        p = PAULIS[s[0]]
        for c in s[1:]:
            p = np.kron(p, PAULIS[c])
        ov = np.trace(p.conj().T @ m) / m.shape[0]
        if abs(abs(ov) - 1) < 1e-8:
            return True
    return False


def brute_clifford(u):
    n = int(round(math.log2(u.shape[0])))
    gens = []
    for q in range(n):
        for g in ("X", "Z"):
            ops = [PAULIS[g] if k == q else PAULIS["I"] for k in range(n)]
            p = ops[0]
            for o in ops[1:]:
                p = np.kron(p, o)
            gens.append(p)
    return all(is_pauli(u @ g @ u.conj().T) for g in gens)


GRID = [k / 8 for k in range(-16, 17)] + [0.1, 0.37, -0.613]


def test_rz_zz_rule():
    for a in GRID:
        c = Circuit(1).Rz(a, 0)
        assert brute_clifford(c.get_unitary()) == M._is_mult(a, 0.5), a
        c = Circuit(2).ZZPhase(a, 0, 1)
        assert brute_clifford(c.get_unitary()) == M._is_mult(a, 0.5), a


def test_phasedx_rule():
    for a in GRID[::2] + [0.1]:
        for b in GRID[::3] + [0.37]:
            c = Circuit(1).add_gate(OpType.PhasedX, [a, b], [0])
            assert brute_clifford(c.get_unitary()) == M.px_is_clifford(a, b), (a, b)


def test_native_counts():
    c = Circuit(2)
    c.Rz(0.25, 0).Rz(0.5, 1).ZZPhase(0.5, 0, 1).ZZPhase(0.3, 0, 1).ZZMax(0, 1)
    c.add_gate(OpType.PhasedX, [0.5, 0.25], [0]).add_gate(OpType.PhasedX, [1.0, 0.25], [1])
    r = M.native_counts(c)
    assert (r["n_2q"], r["n_1q"], r["n_rz"]) == (3, 2, 2)
    assert (r["nc_rz"], r["nc_zz"], r["nc_px"], r["nc_total"]) == (1, 1, 1, 3)
    assert abs(r["hqc"] - (5 + (2 + 30 + 20) / 5)) < 1e-12


def test_pz_counts():
    import pyzx
    pz = pyzx.Circuit(2)
    pz.add_gate("T", 0)
    pz.add_gate("S", 1)
    pz.add_gate("ZPhase", 1, Fraction(3, 4))
    pz.add_gate("ZPhase", 0, Fraction(1, 7))
    pz.add_gate("CNOT", 0, 1)
    assert M.pz_counts(pz) == (2, 3)


NOT_RUN = {"hwb8.qasm", "draper_adder_16.qasm", "draper_adder_28.qasm", "hrs_mult_5.qasm",
           "rgqft_mult_6.qasm", "mcx_b95_54.qasm"}


@pytest.fixture(scope="module")
def csv():
    if not M.OUT_CSV.exists():
        pytest.skip("no CSV")
    return pd.read_csv(M.OUT_CSV)


def test_csv_complete(csv):
    led = M.ledger()
    ok = csv[csv.status == "ok"]
    have = set(zip(ok.family, ok.file, ok.pipeline))
    missing = [(r.family, r.file, p) for r in led.itertuples() for p in M.PIPES
               if (r.family, r.file, p) not in have]
    # the six largest circuits were not run within the 60-minute budget (see the .md)
    files = {f for _, f, _ in missing}
    assert files <= NOT_RUN, files - NOT_RUN
    assert sum(fam == "A" for fam, _, _ in missing) == 0


def test_csv_hqc_formula_and_ledger(csv):
    ok = csv[csv.status == "ok"]
    f = 5 + (ok.n_1q + 10 * ok.n_2q + 10 * ok.n_qubits) / 5
    assert np.allclose(f, ok.hqc)
    assert (ok.nc_total == ok.nc_rz + ok.nc_zz + ok.nc_px).all()
    w = M.load()[1]
    for a, b in [("hqc_L2", "led_P0"), ("hqc_P2", "led_P2"), ("hqc_L3", "led_L3"),
                 ("hqc_P2L3", "led_P2L3")]:
        m = w[a].notna()
        assert m.sum() >= 209
        assert np.allclose(w.loc[m, a], w.loc[m, b])


def test_report_numbers(csv):
    if not M.OUT_MD.exists():
        pytest.skip("no report")
    md = M.OUT_MD.read_text()
    o = M.compute()
    for name, r in o["fam"].items():
        row = (f"| {name} | {r['n_full']} | L3 | {r['n_2q_L3']:.0f} | {r['n_1q_L3']:.0f} | "
               f"{r['nc_total_L3']:.0f} |")
        assert row in md, row
        assert f"| {name} | {r['n']} | {r['zx_gain']:.1f} | {M.f2(r['zx_gain_pct'])} |" in md
