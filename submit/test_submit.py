"""Offline tests for the submit/ scripts (no network, no credentials).

    python3 -m pytest submit/test_submit.py -q
"""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import run_emulator  # noqa: E402
import syntax_check  # noqa: E402
import read_rubric  # noqa: E402

THREE = [("P0", "tfim_n4_r1_disorder_s1.qasm", "A"), ("P2", "barenco_tof_3.qasm", "B1"),
         ("P1", "xxz_n8_r4_uniform_s1.qasm", "A")]


def test_gate_set_three_circuits():
    for pipe, f, _ in THREE:
        circ = common.load_compiled(pipe, f)
        assert common.native_violations(circ) == set()
        assert circ.n_gates_of_type(common.OpType.Measure) == circ.n_qubits


def test_hqc_matches_formula():
    circ = common.load_compiled("P0", "tfim_n4_r1_disorder_s1.qasm")
    n1 = circ.n_gates_of_type(common.OpType.PhasedX)
    n2 = circ.n_gates_of_type(common.OpType.ZZPhase) + circ.n_gates_of_type(common.OpType.ZZMax)
    spam = 2 * circ.n_qubits
    assert common.hqc_estimate(circ, 1000) == pytest.approx(5 + (n1 + 10 * n2 + 5 * spam) * 1000 / 5000)


def test_exact_distribution_loading():
    for pipe, f, fam in THREE:
        p = common.exact_probs(pipe, f)
        ref = common.reference_probs(fam, f)
        assert p.shape == ref.shape
        assert abs(p.sum() - 1) < 1e-9
        assert np.max(np.abs(p - ref)) < 1e-6, (pipe, f)


def test_counts_to_probs_bit_order():
    # key 'b0b1b2' with b0 = c[0]; '100' -> index 4 (c[0] MSB)
    p = common.counts_to_probs({"100": 3, "0 01": 1}, 3)
    assert p[4] == 0.75 and p[1] == 0.25
    with pytest.raises(ValueError):
        common.counts_to_probs({"10": 1}, 3)


def test_fh_tvd_sampled():
    pipe, f, fam = THREE[0]
    ref = common.reference_probs(fam, f)
    rng = np.random.default_rng(0)
    n = int(np.log2(len(ref)))
    draws = rng.choice(len(ref), size=20000, p=ref)
    counts = {}
    for d in draws:
        counts[format(d, "0%db" % n)] = counts.get(format(d, "0%db" % n), 0) + 1
    emp = common.counts_to_probs(counts, n)
    assert common.hellinger_fidelity(ref, emp) > 0.99
    assert common.total_variation(ref, emp) < 0.05
    assert common.hellinger_fidelity(ref, ref) == pytest.approx(1.0)


def test_ledger_append_update(tmp_path):
    path = tmp_path / "ledger.csv"
    k = common.append_ledger(dict(platform="nexus:H2-2E", family="A", file="x.qasm", pipeline="P0",
                                  shots=1000, options={"noisy_simulation": True}, status="SUBMITTING"),
                             path=path)
    common.append_ledger(dict(platform="nexus:H2-2E", family="A", file="y.qasm", pipeline="P0",
                              shots=1000, options="{}", status="SUBMITTING"), path=path)
    rows = common.read_ledger(path)
    assert len(rows) == 2 and list(rows[0]) == common.LEDGER_COLUMNS
    assert rows[0]["options"] == '{"noisy_simulation": true}'
    key = {c: k[c] for c in ("timestamp", "platform", "file", "pipeline")}
    n = common.update_ledger(key, path=path, job_id="J1", status="COMPLETED",
                             hqc_or_seconds={"duration": 3.5}, result_path="r.json")
    assert n == 1
    rows = common.read_ledger(path)
    assert rows[0]["job_id"] == "J1" and rows[0]["status"] == "COMPLETED"
    assert rows[0]["hqc_or_seconds"] == '{"duration": 3.5}'
    assert rows[1]["job_id"] == ""


def test_syntax_check_plan():
    items, missing = syntax_check.plan(["A", "B1"], ["P0", "P2"], 1000, select=r"n4_r1|tof_3")
    files = {(i["pipeline"], i["file"]) for i in items}
    assert ("P0", "tfim_n4_r1_disorder_s1.qasm") in files
    assert ("P2", "tof_3.qasm") in files
    assert all(i["native"] for i in items)
    assert all(i["hqc"] > 5 for i in items)
    assert missing == []
    items2, _ = syntax_check.plan(["A"], ["P0"], 1000, max_jobs=3)
    assert len(items2) == 3
    assert all(i["n"] <= 8 for i in syntax_check.plan(["A"], ["P0"], 1000)[0])


def test_emulator_plan_batches_and_total():
    jobs, missing, options = run_emulator.plan("nexus:H2-2E", "A", ["P0", "P2"], 1000, False,
                                               select=r"tfim_n4_", batch_size=5, skip_done=False)
    n = sum(len(b) for b in jobs)
    assert n == 24 and len(jobs) == 5           # 12 tfim n=4 circuits x 2 pipelines
    assert options == {"noisy_simulation": False}
    tot = sum(it["hqc"] for b in jobs for it in b)
    circs = [common.load_compiled(it["pipeline"], it["file"]) for b in jobs for it in b]
    assert tot == pytest.approx(sum(common.hqc_estimate(c, 1000) for c in circs))
    jobs3, _, _ = run_emulator.plan("nexus:H2-2E", "A", ["P0"], 1000, True, select=r"tfim_n4_",
                                    batch_size=5, max_jobs=1, skip_done=False)
    assert len(jobs3) == 1 and len(jobs3[0]) == 5


def test_score_row_columns():
    pipe, f, fam = THREE[0]
    ref = common.reference_probs(fam, f)
    n = int(np.log2(len(ref)))
    counts = {format(i, "0%db" % n): int(round(1000 * p)) for i, p in enumerate(ref) if p > 0}
    meta = [m for m in common.list_family("A") if m["file"] == f][0]
    row = run_emulator.score(fam, pipe, f, counts, meta, 1000, "J", 1.0)
    assert set(common.EMULATOR_COLUMNS) <= set(row)
    assert row["F_H"] > 0.999 and row["n_2q"] > 0 and row["support_size"] >= 1


def test_credentials_detection(monkeypatch, tmp_path):
    monkeypatch.delenv("AQORA_TOKEN", raising=False)
    monkeypatch.setenv("AQORA_CONFIG_HOME", str(tmp_path))
    assert common.credential_source() == ""
    with pytest.raises(RuntimeError):
        common.get_client()
    (tmp_path / "credentials.json").write_text("{}")
    assert common.credential_source() == "file"
    monkeypatch.setenv("AQORA_TOKEN", "abc")
    assert common.credential_source() == "token"
    monkeypatch.delenv("AQORA_TEAM_ORG", raising=False)
    with pytest.raises(RuntimeError):
        common.team_org()


def test_rubric_render():
    data = {"eventBySlug": {"id": "E", "title": "T", "competitions": {"nodes": [{"competition": {
        "id": "C", "slug": "s", "title": "track", "currentStage": {
            "noCode": True, "requiresApproval": False, "submissionPreamble": "pre", "validUntil": "2026-10-15",
            "scoringCriteria": [{"title": "a", "weight": 0.5, "description": "d|x"}]}}}]}}}
    txt = read_rubric.render("s", data)
    assert "| 1 | a | 0.5 | d\\|x |" in txt and "noCode: `True`" in txt and "2026-10-15" in txt
    assert "null" in read_rubric.render("s", {"eventBySlug": None})
