"""Tests for submit/evidence_index.py: totals match Section 3.7.1 and every H2-2E job is listed once."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd  # noqa: E402
import evidence_index as ev  # noqa: E402


def test_h22e_totals():
    df = ev.payload_rows()
    ok = df[df.counts_ok & (df.platform == "nexus:H2-2E")]
    assert len(ok) == 18 and ok.job_id.nunique() == 18
    assert round(ok.hqc_estimate.sum(), 1) == 5933.2


def test_h2_emulator_batches():
    df = ev.payload_rows()
    ok = df[df.counts_ok & (df.platform == "nexus:H2-Emulator")]
    assert len(ok) == 22 and ok.job_id.nunique() == 3


def test_render_lists_every_payload():
    df = ev.payload_rows()
    text = ev.render(df, pd.read_csv(ev.LEDGER))
    for jid in df[df.counts_ok].job_id.unique():
        assert f"`{jid}`" in text
