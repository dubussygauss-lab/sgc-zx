"""The submission cell of report/notebook_skeleton.py refuses every platform
whose name does not end in "SC" (offline, no credentials, no network).

    python3 -m pytest report/test_notebook_submit.py -q
"""

import importlib.util
from pathlib import Path

import pytest

_NB = Path(__file__).resolve().parent / "notebook_skeleton.py"
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
        nb.submit_free_check(platform, None, 1000, "/nonexistent", "B1", "tof_3.qasm", "select:P0")


def test_guard_accepts_syntax_checker():
    assert nb.require_free_checker("nexus:H2-2SC") == "nexus:H2-2SC"


def test_notebook_platform_is_syntax_checker():
    src = _NB.read_text()
    assert 'PLATFORM = "nexus:H2-2SC"' in src
    assert "require_free_checker(PLATFORM)" in src
