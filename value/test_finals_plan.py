"""Tests for value/finals_plan.py.  Run: python3 -m pytest value/test_finals_plan.py

1. The inputs equal Table E3 (pooled) and the Table E2 2-sd shots quoted in Section 3.7.1.
2. The planned shots are the smallest multiple of ROUND at or above the 2-sd shots, and 2 sd of the
   difference at those shots does not exceed the effect (brute force over shot counts).
3. HQC per job equals the formula recomputed by hand from the hqslib1 QASM (U1q = PhasedX, RZZ and ZZ = two-qubit), and the total adds up.
4. The rendered Markdown tags every bullet [F] or [O] and avoids semicolons.
"""
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "value"))

import finals_plan as fp  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return fp.compute()


def test_inputs_match_tables(r):
    P, S = r["primary"], r["secondary"]
    assert round(P["dF"], 4) == 0.0108 and round(P["z"], 2) == 2.38 and round(P["sd"], 4) == 0.0045
    assert round(S["dF"], 4) == 0.0007 and round(S["z"], 2) == 0.10 and round(S["z_vs_pred"], 2) == -2.94
    assert r["shots_2sd_pred_E2"] == {"vbe_adder_3.qasm": 1147, "hwb6.qasm": 20462, "grover_5.qasm": 1974}
    assert round(r["hqc_used"], 1) == 5933.2 and round(r["hqc_left"], 1) == 4066.8


@pytest.mark.parametrize("key,effect", [("primary", "dF"), ("secondary", "shortfall")])
def test_shots_brute_force(r, key, effect):
    t = r[key]
    eff = t[effect]
    first = next(n for n in range(1, 100000) if 2 * t["sd"] * math.sqrt(fp.POOLED_SHOTS / n) <= eff)
    assert first == math.ceil(t["shots_2sd_raw"]) or first == math.floor(t["shots_2sd_raw"]) + 1
    assert t["shots"] % fp.ROUND == 0 and t["shots"] >= first and t["shots"] - fp.ROUND < first
    assert 2 * t["sd_planned"] <= eff


def _counts(qasm: str):
    n1 = len(re.findall(r"^\s*U1q\(", qasm, re.M))
    n2 = len(re.findall(r"^\s*(RZZ\(|ZZ\s)", qasm, re.M))
    nm = len(re.findall(r"^\s*measure\b", qasm, re.M))
    nq = sum(int(x) for x in re.findall(r"^\s*qreg\s+\w+\[(\d+)\]", qasm, re.M))
    return n1, n2, nm, nq


def test_hqc_by_hand(r):
    tot = 0.0
    for j in r["jobs"]:
        qasm = (ROOT / "results" / "compiled" / j["pipeline"] / j["file"]).read_text()
        n1, n2, nm, nq = _counts(qasm)
        assert (n1, n2, nq) == (j["n_1q"], j["n_2q"], j["n_qubits"])
        hand = 5 + (n1 + 10 * n2 + 5 * (nq + nm)) * j["shots"] / 5000
        assert abs(hand - j["hqc"]) < 1e-9
        tot += hand
    assert abs(tot - r["hqc_total"]) < 1e-9
    assert abs(r["hqc_primary"] + r["hqc_secondary"] - r["hqc_total"]) < 1e-9


def test_markdown_style(r):
    md = fp.render(r)
    bullets = [l for l in md.splitlines() if l.startswith("- ")]
    assert bullets and all(l.startswith("- [F] ") or l.startswith("- [O] ") for l in bullets)
    assert ";" not in md and "—" not in md
