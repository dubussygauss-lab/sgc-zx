"""Tests for value/value_ledger.py.  Run: python3 -m pytest value/test_value_ledger.py

1. HQC recomputed with pipelines/compile.py hqc() from the compiled QASM in
   results/compiled/<pipeline>/ matches the ledger (P0 and P2, 3 circuits).
2. Every TOTAL row equals the sum of its circuit rows.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pytket.qasm import circuit_from_qasm  # noqa: E402
from pipelines.compile import hqc  # noqa: E402


@pytest.fixture(scope="module")
def ledger():
    subprocess.run([sys.executable, str(ROOT / "value/value_ledger.py")], check=True,
                   capture_output=True)
    return pd.read_csv(ROOT / "value/value_ledger.csv")


@pytest.mark.parametrize("family,file", [
    ("B1", "barenco_tof_3.qasm"),
    ("B1", "vbe_adder_3.qasm"),
    ("B1x", "rc_adder_6.qasm"),
])
def test_hqc_from_compiled_qasm(ledger, family, file):
    row = ledger[(ledger.layer == "NISQ") & (ledger.family == family) & (ledger.file == file)]
    assert len(row) == 1
    for pipe in ("P0", "P2"):
        circ = circuit_from_qasm(str(ROOT / "results/compiled" / pipe / file))
        assert np.isclose(hqc(circ, shots=1000), row[f"hqc_{pipe}"].iloc[0]), (file, pipe)


def test_totals_equal_sums(ledger):
    sum_cols = {"NISQ": ["n2q_P0", "n2q_P2", "hqc_P0", "hqc_P2", "hqc_saved", "dN2q"],
                "FT": ["T_written", "T_zx_P2", "T_saved", "magic_written", "magic_zx_P2",
                       "magic_saved"]}
    n_checked = 0
    for (layer, fam), g in ledger.groupby(["layer", "family"]):
        circ = g[g.row_kind == "circuit"]
        tot = g[g.row_kind == "total"]
        assert len(tot) == 1
        for c in sum_cols[layer]:
            assert np.isclose(circ[c].sum(), tot[c].iloc[0]), (layer, fam, c)
        assert np.allclose(circ.hqc_saved if layer == "NISQ" else circ.T_saved,
                           (circ.hqc_P0 - circ.hqc_P2) if layer == "NISQ"
                           else (circ.T_written - circ.T_zx_P2))
        if layer == "FT" and circ.cert_floor.notna().any():
            cc = circ.dropna(subset=["cert_floor"])
            assert np.isclose(cc.cert_floor.sum(), tot.cert_floor.iloc[0])
            assert np.isclose(cc.cert_floor.sum() / cc.T_zx_P2.sum(),
                              tot.cert_incompressible_frac_of_remaining.iloc[0])
        n_checked += 1
    assert n_checked == 6  # NISQ: A, B1, B1x ; FT: B1, B1x, B2


def test_families_not_merged(ledger):
    assert set(ledger[ledger.layer == "NISQ"].family) == {"A", "B1", "B1x"}
    assert set(ledger[ledger.layer == "FT"].family) == {"B1", "B1x", "B2"}
    b1 = set(ledger[ledger.family == "B1"].file) - {"TOTAL"}
    b1x = set(ledger[ledger.family == "B1x"].file) - {"TOTAL"}
    assert not (b1 & b1x)
