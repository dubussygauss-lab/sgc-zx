"""Tests for pipelines/official_baseline.py on a few small circuits.

For each circuit: the official pytket-quantinuum pass (offline H2-1 backend)
gives the same counts as the reproduced P0 / P2 of compile.py, the official
output passes compile.check, and the stored row of results/official_baseline.csv
agrees with a fresh run.

Run: python3 -m pytest pipelines/test_official_baseline.py -q
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
import official_baseline as OB  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

CASES = [
    ("A", "tfim_n4_r1_uniform_s1.qasm"),
    ("B1", "tof_3.qasm"),
    ("B1", "vbe_adder_3.qasm"),
    ("B2", "haar_n2_eps1e-03_s1.qasm"),
]


def test_backend_is_offline_h2():
    b = OB.backend()
    assert b.backend_info.device_name == "H2-1"
    assert type(b.api_handler).__name__ == "QuantinuumAPIOffline"


def test_pass_sequence_matches_reproduction():
    off = OB.official_pass(2).to_dict()["SequencePass"]["sequence"]
    rep = C.quantinuum_default_pass(2).to_dict()["SequencePass"]["sequence"]
    assert [p["StandardPass"]["name"] for p in off] == \
        [p["StandardPass"]["name"] for p in rep]


@pytest.mark.parametrize("family,file", CASES)
def test_official_equals_reproduced(family, file):
    circ = circuit_from_qasm(os.path.join(OB.FAMILIES[family], file))
    for v, ours in (("P0off", "P0"), ("P2off", "P2")):
        comp, _ = OB.compile_official(v, circ)
        mine, _ = C.compile_pipeline(ours, circ)
        a, b = OB.counts(comp), OB.counts(mine)
        for k in ("n_2q", "n_1q", "depth_2q", "hqc"):
            assert a[k] == b[k], (file, v, k, a[k], b[k])
        assert a["native"]
        ref, _ = C.compile_pipeline("P0ref", circ)
        assert C.check(comp, ref)["check_ok"]


@pytest.mark.parametrize("family,file", CASES)
def test_stored_row_reproduces(family, file):
    if not os.path.exists(OB.OUT_CSV):
        pytest.skip("results/official_baseline.csv not present")
    df = pd.read_csv(OB.OUT_CSV)
    for v in OB.VARIANTS:
        row = OB.run_one(family, file, v)
        s = df[(df.family == family) & (df.file == file) & (df.variant == v)]
        assert len(s) == 1
        for k in ("n_2q", "n_1q", "depth_2q", "hqc"):
            assert row[k] == s.iloc[0][k]
        assert row["status"] == s.iloc[0]["status"] == "ok"
