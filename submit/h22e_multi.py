"""Statistics of the H2-2E run of cdkm_adder_10 (P0 vs L3) and modadd_2n_10 (P0 vs P2L3) on three non-zero inputs each.

Pre-registration: results/h22e_multi_prereg.md.  Runner: submit/h22e_multi_run.py.

Inputs (all under results/)
  emulator/nexus_H2-2E_famC_multi/<pipeline>/<circuit>_i<k>.json   counts, job_id, hqc_estimate
  emulator_nexus_H2-2E_famC_multi.csv                               one row per job (run_emulator.score)
  emulator_jobs.csv                                                 job ledger
  compiled/<pipeline>/<circuit>_i<k>.qasm                           submitted circuits

What it computes (the pre-registered analysis)
  p        success probability = count of the expected bitstring / N (N = 400); for a
           single-outcome ideal distribution it equals the Hellinger fidelity F_H.
  sd       binomial sqrt(p (1 - p) / N).
  primary  per circuit, pooled over its 3 inputs: p_pick - p_P0 with
           sd = sqrt(p_pick (1 - p_pick) / 1200 + p_P0 (1 - p_P0) / 1200), z = d / sd.
  second.  per-input d, sd, z; pooled over both circuits (2400 shots per arm).
  hqc      5 + (n_1q + 10 n_2q + 5 (n_qubits + n_measure)) * N / 5000 from the
           compiled QASM, checked against the payload's hqc_estimate.
  grand    all stored H2-2E payloads with valid counts (evidence_index.payload_rows).

Run from the repository root:

    python3 submit/h22e_multi.py --md results/h22e_multi.md
"""

import json
import math
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evidence_index  # noqa: E402
import h22e_multi_run as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
PLATFORM = "nexus:H2-2E"
RUN_DIR = os.path.join(RESULTS, "emulator", "nexus_H2-2E_famC_multi")
CSV = os.path.join(RESULTS, "emulator_nexus_H2-2E_famC_multi.csv")
LEDGER = os.path.join(RESULTS, "emulator_jobs.csv")
SHOTS = 400
QUOTA_HQC = 10000.0


def load_payload(pipeline: str, file: str) -> dict:
    with open(os.path.join(RUN_DIR, pipeline, file[:-5] + ".json")) as f:
        return json.load(f)


def qasm_counts(pipeline: str, file: str) -> dict:
    with open(os.path.join(RESULTS, "compiled", pipeline, file)) as f:
        q = f.read()
    n1 = len(re.findall(r"^\s*U1q\(", q, re.M))
    n2 = len(re.findall(r"^\s*(RZZ\(|ZZ\s)", q, re.M))
    nm = len(re.findall(r"^\s*measure\b", q, re.M))
    nq = sum(int(x) for x in re.findall(r"^\s*qreg\s+\w+\[(\d+)\]", q, re.M))
    return {"n_1q": n1, "n_2q": n2, "n_measure": nm, "n_qubits": nq}


def hqc_from_counts(c: dict, shots: int) -> float:
    return 5 + (c["n_1q"] + 10 * c["n_2q"] + 5 * (c["n_qubits"] + c["n_measure"])) * shots / 5000


def diff(k1: int, n1: int, k0: int, n0: int) -> dict:
    """p1 - p0 with the binomial sd of the difference and z."""
    p1, p0 = k1 / n1, k0 / n0
    sd = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    d = p1 - p0
    return {"p_pick": p1, "p_P0": p0, "d": d, "sd": sd, "z": d / sd if sd > 0 else float("nan"), "N_arm": n1}


def compute(allow_missing: bool = False) -> dict:
    """allow_missing=True skips programs whose payload is not stored yet (job still
    queued); the circuits concerned are then flagged incomplete, not analysed."""
    e = pd.read_csv(CSV)
    led = pd.read_csv(LEDGER)
    led = led[led.platform == PLATFORM]
    rows, missing = [], []
    for c, k, a, b, f in R.programs():
        expected = R.expected_bits(c, a, b)
        n = R.CIRCUITS[c][0]
        for pipe in R.pipelines(c):
            if allow_missing and not os.path.isfile(os.path.join(RUN_DIR, pipe, f[:-5] + ".json")):
                missing.append((f, pipe))
                continue
            d = load_payload(pipe, f)
            assert d["platform"] == PLATFORM and d["file"] == f and d["pipeline"] == pipe
            assert d["options"] == {"noisy_simulation": True} and not d.get("error")
            counts = {key.replace(" ", ""): int(v) for key, v in d["counts"].items()}
            assert all(len(key) == n for key in counts)
            N = sum(counts.values())
            assert N == int(d["shots"]) == SHOTS
            ks = counts.get(expected, 0)
            p = ks / N
            qc = qasm_counts(pipe, f)
            hqc = hqc_from_counts(qc, N)
            assert abs(hqc - float(d["hqc_estimate"])) < 1e-9, (hqc, d["hqc_estimate"])
            r = e[(e.file == f) & (e.pipeline == pipe) & (e.job_id == d["job_id"])]
            assert len(r) == 1
            l = led[(led.file == f) & (led.pipeline == pipe) & (led.job_id == d["job_id"])]
            assert len(l) == 1 and l.status.iloc[0] == "COMPLETED"
            rows.append({"circuit": c, "input": k, "a": a, "b": b, "file": f, "expected": expected,
                         "pipeline": pipe, "arm": "P0" if pipe == "P0" else "pick",
                         "n_qubits": qc["n_qubits"], "n_2q": qc["n_2q"], "n_1q": qc["n_1q"], "hqc": hqc,
                         "shots": N, "k_success": ks, "p_success": p, "sd": math.sqrt(p * (1 - p) / N),
                         "F_H_payload": float(d["F_H"]), "F_H_csv": float(r.F_H.iloc[0]),
                         "n_outcomes": len(counts), "job_id": d["job_id"], "ledger_timestamp": l.timestamp.iloc[0]})
    t = pd.DataFrame(rows)

    def arm_sum(df, arm):
        s = df[df.arm == arm]
        return int(s.k_success.sum()), int(s.shots.sum())

    bad = {f for f, _ in missing}
    per_input, primary = [], {}
    for c in R.ORDER:
        tc = t[t.circuit == c]
        for k in (1, 2, 3):
            if R.file_name(c, k) in bad:
                continue
            ti = tc[tc.input == k]
            per_input.append(dict(circuit=c, input=k, pick=R.CIRCUITS[c][1],
                                  **diff(*arm_sum(ti, "pick"), *arm_sum(ti, "P0"))))
        if not any(f.startswith(c) for f in bad):
            primary[c] = dict(pick=R.CIRCUITS[c][1], **diff(*arm_sum(tc, "pick"), *arm_sum(tc, "P0")))
    both = diff(*arm_sum(t, "pick"), *arm_sum(t, "P0")) if not missing else None
    return {"rows": t, "per_input": pd.DataFrame(per_input), "primary": primary, "both": both,
            "hqc_total": float(t.hqc.sum()), "n_jobs": int(t.job_id.nunique()), "missing": missing}


def h22e_grand_total() -> tuple:
    """(jobs, HQC) over every stored H2-2E payload with counts summing to shots, all run directories."""
    df = evidence_index.payload_rows()
    ok = df[df.counts_ok & (df.platform == PLATFORM)]
    return int(ok.job_id.nunique()), float(ok.hqc_estimate.sum())


def render_md(r: dict) -> str:
    jobs, hqc = h22e_grand_total()
    L = ["# H2-2E run of cdkm_adder_10 and modadd_2n_10 on three non-zero inputs each (P0 vs PSEL4 pick)", "",
         "Generated by `python3 submit/h22e_multi.py --md results/h22e_multi.md` from the stored payloads "
         "`results/emulator/nexus_H2-2E_famC_multi/<pipeline>/<circuit>_i<k>.json`. Pre-registration: "
         "`results/h22e_multi_prereg.md`. Platform nexus:H2-2E, noisy simulation, 400 shots per job, one program per job. "
         "PSEL4 pick: L3 for cdkm_adder_10, P2L3 for modadd_2n_10.", "",
         "## Primary metric (pre-registered): pooled over the 3 inputs of each circuit", "",
         "| Circuit | Pick | p(pick) | p(P0) | p(pick) - p(P0) | sd | z | Shots per arm |",
         "|---|---|---|---|---|---|---|---|"]
    for c, v in r["primary"].items():
        L.append("| %s | %s | %.4f | %.4f | %+.4f | %.4f | %.2f | %d |"
                 % (c, v["pick"], v["p_pick"], v["p_P0"], v["d"], v["sd"], v["z"], v["N_arm"]))
    b = r["both"]
    L += ["", "## Secondary", "",
          "Pooled over both circuits (pick minus P0): p(pick) = %.4f, p(P0) = %.4f, d = %+.4f, sd %.4f, z = %.2f, %d shots per arm."
          % (b["p_pick"], b["p_P0"], b["d"], b["sd"], b["z"], b["N_arm"]), "",
          "| Circuit | Input | Pick | p(pick) | p(P0) | d | sd | z |", "|---|---|---|---|---|---|---|---|"]
    for v in r["per_input"].itertuples():
        L.append("| %s | i%d | %s | %.4f | %.4f | %+.4f | %.4f | %.2f |"
                 % (v.circuit, v.input, v.pick, v.p_pick, v.p_P0, v.d, v.sd, v.z))
    L += ["", "## Jobs", "",
          "| File | a | b | Expected (c[0] first) | Pipeline | n_2q | n_1q | HQC | Successes / shots | p_success = F_H | sd | Job ID |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in r["rows"].itertuples():
        L.append("| %s | %d | %d | `%s` | %s | %d | %d | %.2f | %d / %d | %.4f | %.4f | `%s` |"
                 % (t.file, t.a, t.b, t.expected, t.pipeline, t.n_2q, t.n_1q, t.hqc, t.k_success, t.shots,
                    t.p_success, t.sd, t.job_id))
    L += ["",
          "- p_success = count of the expected bitstring / 400. The ideal output is a single basis state, so the Hellinger "
          "fidelity to it equals p_success. sd is binomial; the sd of a difference adds the two variances.",
          "- HQC estimate of this run: %.2f over %d jobs." % (r["hqc_total"], r["n_jobs"]),
          "- All H2-2E jobs with valid counts: %d jobs, %.1f HQC estimate, %.1f left of 10,000."
          % (jobs, hqc, QUOTA_HQC - hqc), ""]
    return "\n".join(L)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None, help="also write the Markdown report to this path")
    a = ap.parse_args()
    r = compute()
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(render_md(r))
    pd.set_option("display.width", 250)
    print(r["rows"].drop(columns=["expected", "ledger_timestamp"]).to_string(index=False))
    print(r["per_input"].to_string(index=False))
    for c, v in r["primary"].items():
        print("PRIMARY %s %s: p_pick %.4f p_P0 %.4f d %+.4f sd %.4f z %.2f" % (c, v["pick"], v["p_pick"], v["p_P0"], v["d"], v["sd"], v["z"]))
    b = r["both"]
    print("both circuits: d %+.4f sd %.4f z %.2f" % (b["d"], b["sd"], b["z"]))
    print("HQC run %.2f (%d jobs); H2-2E grand total %d jobs %.1f HQC" % ((r["hqc_total"], r["n_jobs"]) + h22e_grand_total()))


if __name__ == "__main__":
    main()
