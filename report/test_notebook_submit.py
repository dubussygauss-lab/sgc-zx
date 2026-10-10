"""The submission cell of report/notebook_skeleton.py refuses every platform
whose name does not end in "SC" (offline, no credentials, no network), and
the notebook's PSEL4 demo (pass_select.compile_select with
PSEL4_CANDIDATES) on its two circuits, family_B1/vbe_adder_3.qasm (Section 2
default) and family_B1/tof_3.qasm (Section 3), reproduces the per-candidate
HQC and the pick of value/psel4_ledger.csv. The executed export
report/notebook_executed.html shows that demo.

    python3 -m pytest report/test_notebook_submit.py -q
"""

import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

_NB = Path(__file__).resolve().parent / "notebook_skeleton.py"
_ROOT = _NB.parent.parent
_HTML = _NB.parent / "notebook_executed.html"
sys.path.insert(0, str(_ROOT / "pipelines"))
import pass_select  # noqa: E402
_spec = importlib.util.spec_from_file_location("notebook_skeleton", _NB)
nb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb)

PAID = ["nexus:H2-2E", "nexus:H2-Emulator", "nexus:H2-2", "H2-2E", "nexus:Selene",
        "nexus:H2-2SC ", "nexus:H2-2sc", "", None]


@pytest.mark.parametrize("platform", PAID)
def test_guard_refuses(platform):
    with pytest.raises(AssertionError, match="refusing platform"):
        nb.require_free_checker(platform)


@pytest.mark.parametrize("platform", PAID)
def test_submit_refuses_before_any_work(platform):
    # circuit=None and a missing root: any step after the guard would fail
    # with a different error, so the AssertionError shows the guard ran first.
    with pytest.raises(AssertionError, match="refusing platform"):
        nb.submit_free_check(platform, None, 1000, "/nonexistent", "B1", "tof_3.qasm", "psel4:P0")


def test_guard_accepts_syntax_checker():
    assert nb.require_free_checker("nexus:H2-2SC") == "nexus:H2-2SC"


def test_notebook_platform_is_syntax_checker():
    src = _NB.read_text()
    assert 'PLATFORM = "nexus:H2-2SC"' in src
    assert "require_free_checker(PLATFORM)" in src


# ---------------------------------------------------------------- PSEL4 demo

NB_CIRCUITS = [("family_B1", "vbe_adder_3.qasm"), ("family_B1", "tof_3.qasm")]
TIE = ["P0", "L3", "P2", "P2L3"]


def test_notebook_uses_psel4():
    src = _NB.read_text()
    assert "candidates=pass_select.PSEL4_CANDIDATES" in src
    assert '"family_B1/vbe_adder_3.qasm"' in src
    assert 'SC_FAMILY, SC_FILE = "B1", "tof_3.qasm"' in src
    assert 'psel4_demo(ROOT, "family_B1", SC_FILE' in src
    assert '"psel4:" + sc_record["chosen"]' in src
    assert "select:" not in src
    assert "compile_select(_input" not in src  # the old two-candidate call
    assert set(pass_select.PSEL4_CANDIDATES) == set(TIE)
    assert sorted(TIE, key=pass_select.TIE_ORDER.get) == TIE


@pytest.fixture(scope="module")
def ledger():
    return pd.read_csv(_ROOT / "value" / "psel4_ledger.csv")


@pytest.mark.parametrize("family_dir,file", NB_CIRCUITS)
def test_psel4_demo_matches_ledger(family_dir, file, ledger):
    comp, record, table, led = nb.psel4_demo(str(_ROOT), family_dir, file, shots=1000)
    rows = ledger[(ledger["family"] == family_dir.replace("family_", "")) & (ledger["file"] == file)]
    assert len(rows) == 1
    row = rows.iloc[0]
    assert led is not None and led["pick_PSEL4"] == row["pick_PSEL4"]
    assert comp is not None
    # one row per candidate, in the tie order P0, L3, P2, P2L3
    assert list(table["candidate"]) == TIE
    for name in TIE:
        r = record["candidates"][name]
        assert r["status"] == "ok", (name, r)
        assert abs(r["hqc"] - float(row[f"hqc_{name}"])) < 0.05, (name, r["hqc"], row[f"hqc_{name}"])
    assert bool(table["hqc_matches_ledger"].all())
    # the pick equals the ledger pick and has the ledger's PSEL4 HQC
    assert record["chosen"] == row["pick_PSEL4"]
    assert abs(record["candidates"][record["chosen"]]["hqc"] - float(row["hqc_PSEL4"])) < 0.05
    assert list(table.loc[table["PSEL4_pick"], "candidate"]) == [record["chosen"]]
    assert list(table.loc[table["ledger_pick"], "candidate"]) == [record["chosen"]]
    # the pick is the lowest HQC, ties broken by n_2q then the order P0, L3, P2, P2L3
    best = min(TIE, key=lambda n: (round(record["candidates"][n]["hqc"], 9),
                                   record["candidates"][n]["n_2q"], TIE.index(n)))
    assert record["chosen"] == best


def _html_text():
    s = _HTML.read_text()
    s = s.encode().decode("unicode_escape", errors="ignore")
    return " ".join(re.sub(r"<[^>]+>", " ", s).split())


@pytest.mark.parametrize("family_dir,file", NB_CIRCUITS)
def test_executed_export_shows_psel4(family_dir, file, ledger):
    text = _html_text()
    row = ledger[(ledger["family"] == family_dir.replace("family_", "")) & (ledger["file"] == file)].iloc[0]
    pick, hqc = row["pick_PSEL4"], float(row["hqc_PSEL4"])
    if file == "tof_3.qasm":
        head = f"PSEL4 on bench/{family_dir}/{file} at 1000 shots: pick {pick} , HQC {hqc:.1f}"
    else:
        head = f"Live PSEL4 compilation of {family_dir}/{file} at 1000 shots: pick {pick} , HQC {hqc:.1f}"
    i = text.find(head)
    assert i >= 0, head
    tail = text[i:i + 400]
    assert f"value/psel4_ledger.csv : pick {pick} , HQC {hqc:.1f}" in tail
    assert "agree on every candidate HQC and on the pick: True" in tail


def test_executed_export_submitted_psel4_pick(ledger):
    # The submission cell of the export ran on the free syntax checker and
    # submitted the PSEL4 pick of tof_3, the ledger pick, at the ledger HQC.
    text = _html_text()
    row = ledger[(ledger["family"] == "B1") & (ledger["file"] == "tof_3.qasm")].iloc[0]
    m = re.search(r"Job id (\S+) on nexus:H2-2SC \(reported platform H2-2SC \) as \S+ , "
                  r"status COMPLETED , 1000 shots, pipeline psel4:(\w+) \. .*? C = 1000: ([0-9.]+) \.",
                  text)
    assert m, "submission cell output with a psel4 pipeline label not found"
    assert m.group(2) == row["pick_PSEL4"]
    assert abs(float(m.group(3)) - float(row["hqc_PSEL4"])) < 0.005
    jobs = pd.read_csv(_ROOT / "results" / "emulator_jobs.csv")
    j = jobs[jobs["job_id"] == m.group(1)]
    assert len(j) == 1
    assert j.iloc[0]["platform"] == "nexus:H2-2SC"
    assert j.iloc[0]["pipeline"] == "psel4:" + row["pick_PSEL4"]
