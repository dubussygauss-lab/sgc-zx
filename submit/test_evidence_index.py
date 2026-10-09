"""Tests for submit/evidence_index.py: H2-2E totals (Section 3.7.1 subset and the family C run) and every job is listed once."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd  # noqa: E402
import evidence_index as ev  # noqa: E402


def test_h22e_totals():
    df = ev.payload_rows()
    ok = df[df.counts_ok & (df.platform == "nexus:H2-2E")]
    # all H2-2E jobs: Table E2/E3 runs (18 jobs, 5933.2) + family C vbe_adder_7 (2 jobs, 664.8)
    assert len(ok) == 20 and ok.job_id.nunique() == 20
    assert round(ok.hqc_estimate.sum(), 1) == 6598.0
    # Table E2/E3 subset: run dirs nexus_H2-2E and nexus_H2-2E_r*
    e23 = ok[ok.run_dir.str.fullmatch(r"nexus_H2-2E(_r\d+)?")]
    assert len(e23) == 18 and e23.job_id.nunique() == 18
    assert round(e23.hqc_estimate.sum(), 1) == 5933.2
    famc = ok[ok.run_dir == "nexus_H2-2E_famC"]
    assert len(famc) == 2 and famc.job_id.nunique() == 2
    assert round(famc.hqc_estimate.sum(), 1) == 664.8


def test_h2_emulator_batches():
    df = ev.payload_rows()
    ok = df[df.counts_ok & (df.platform == "nexus:H2-Emulator")]
    assert len(ok) == 22 and ok.job_id.nunique() == 3


def test_render_lists_every_payload():
    df = ev.payload_rows()
    text = ev.render(df, pd.read_csv(ev.LEDGER))
    for jid in df[df.counts_ok].job_id.unique():
        assert f"`{jid}`" in text
