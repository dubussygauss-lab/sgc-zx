"""Fast offline test of pipelines/strong_baselines.py on two small B1 circuits.

For tof_3 and barenco_tof_3: every variant compiles into the H2 native gate
set, passes the exactness check of compile.check, L2 reproduces the stored P0
HQC of value/selector_ledger_circuits.csv, and the stored rows of
results/strong_baselines.csv (when present) agree with a fresh run.

Run: python3 -m pytest pipelines/test_strong_baselines.py -q
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strong_baselines as SB  # noqa: E402

CASES = ["tof_3.qasm", "barenco_tof_3.qasm"]


@pytest.mark.parametrize("file", CASES)
@pytest.mark.parametrize("variant", SB.VARIANTS)
def test_variant_native_and_exact(file, variant):
    row = SB.run_one("B1", file, variant)
    assert row["native"], row
    assert row["check_ok"], row
    assert row["status"] == "ok"


@pytest.mark.parametrize("file", CASES)
def test_l2_equals_stored_p0(file):
    row = SB.run_one("B1", file, "L2")
    p0 = SB.ours().set_index(["family", "file"]).loc[("B1", file), "hqc_P0"]
    assert abs(row["hqc"] - p0) < 1e-9


@pytest.mark.parametrize("file", CASES)
def test_stored_rows_reproduce(file):
    if not os.path.exists(SB.OUT_CSV):
        pytest.skip("no stored CSV")
    df = pd.read_csv(SB.OUT_CSV)
    for v in SB.VARIANTS:
        s = df[(df.family == "B1") & (df.file == file) & (df.variant == v)]
        if not len(s):
            continue
        row = SB.run_one("B1", file, v)
        assert abs(row["hqc"] - s["hqc"].iloc[0]) < 1e-9, (file, v)


def test_timeout_row_is_kept():
    row = SB.run_with_timeout(("B1", "tof_3.qasm", "L3", 1e-6))
    assert row["status"] in ("timeout", "ok")
    assert row["file"] == "tof_3.qasm" and row["variant"] == "L3"
