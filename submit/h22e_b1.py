"""Statistics of the H2-2E run of vbe_adder_3 (P0 vs L3, 4 inputs) and hwb6 (P0 vs P2L3, 3 inputs), non-zero inputs.

Pre-registration: results/h22e_b1_prereg.md.  Runner: submit/h22e_b1_run.py.

Inputs (all under results/)
  emulator/nexus_H2-2E_famB1_multi/<pipeline>/<circuit>_i<k>.json   counts, job_id, hqc_estimate
  emulator_nexus_H2-2E_famB1_multi.csv                              one row per job (run_emulator.score)
  emulator_jobs.csv                                                 job ledger
  compiled/<pipeline>/<circuit>_i<k>.qasm                           submitted circuits

What it computes (the pre-registered analysis)
  p        success probability = count of the expected bitstring / N (N = 400); for a
           single-outcome ideal distribution it equals the Hellinger fidelity F_H.
  primary  per circuit, pooled over its inputs (S shots per arm, K successes): d = p_pick - p_P0,
           pooled two-proportion z = d / sqrt(pp (1 - pp) (2 / S)) with pp = (K_pick + K_P0) / (2 S),
           two-sided p = 2 (1 - Phi(|z|)), Holm step-down over the two circuits at alpha = 0.05.
  second.  R = (H_pick / K_pick) / (H_P0 / K_P0), HQC per correct output of the pick relative to P0, with the
           95 % delta-method interval on log R, var(log p) = (1 - p) / (S p) per arm, H fixed
           (as value/hqc_per_correct.py); per-input d and Wald z; pooled difference over both circuits.
  hqc      5 + (n_1q + 10 n_2q + 5 (n_qubits + n_measure)) * N / 5000 from the compiled QASM,
           checked against the payload's hqc_estimate.
  grand    all stored H2-2E payloads with valid counts (evidence_index.payload_rows).

Run from the repository root:

    python3 submit/h22e_b1.py --md results/h22e_b1.md
"""

import json
import math
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evidence_index  # noqa: E402
import h22e_b1_run as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
PLATFORM = "nexus:H2-2E"
RUN_DIR = os.path.join(RESULTS, "emulator", "nexus_H2-2E_famB1_multi")
CSV = os.path.join(RESULTS, "emulator_nexus_H2-2E_famB1_multi.csv")
LEDGER = os.path.join(RESULTS, "emulator_jobs.csv")
SHOTS = 400
QUOTA_HQC = 10000.0
ALPHA = 0.05
Z95 = 1.959963984540054


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


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_sided_p(z: float) -> float:
    return 2 * (1 - phi(abs(z)))


def pooled_z(k1: int, n1: int, k0: int, n0: int) -> dict:
    """Pooled two-proportion z of p1 - p0 (the primary test) with its two-sided p."""
    p1, p0 = k1 / n1, k0 / n0
    pp = (k1 + k0) / (n1 + n0)
    sd = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n0))
    d = p1 - p0
    z = d / sd if sd > 0 else float("nan")
    return {"p_pick": p1, "p_P0": p0, "d": d, "sd_pooled": sd, "z": z, "p_value": two_sided_p(z), "N_arm": n1,
            "k_pick": k1, "k_P0": k0}


def wald_diff(k1: int, n1: int, k0: int, n0: int) -> dict:
    """p1 - p0 with the unpooled (Wald) binomial sd of the difference and z (secondary)."""
    p1, p0 = k1 / n1, k0 / n0
    sd = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    d = p1 - p0
    return {"p_pick": p1, "p_P0": p0, "d": d, "sd": sd, "z": d / sd if sd > 0 else float("nan"), "N_arm": n1}


def holm(pvals: dict, alpha: float = ALPHA) -> dict:
    """Holm step-down adjusted p-values (monotone) and rejection at alpha."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adj[k] = running
    return {k: {"p_holm": adj[k], "reject": adj[k] <= alpha} for k in pvals}


def ratio_R(h1: float, k1: int, n1: int, h0: float, k0: int, n0: int) -> dict:
    """HQC per correct output of the pick relative to P0 with the delta-method 95 % interval."""
    p1, p0 = k1 / n1, k0 / n0
    R_ = (h1 / k1) / (h0 / k0)
    se = math.sqrt((1 - p1) / (n1 * p1) + (1 - p0) / (n0 * p0))
    return {"H_pick": h1, "H_P0": h0, "C_pick": h1 / k1, "C_P0": h0 / k0, "R": R_,
            "R_lo": R_ * math.exp(-Z95 * se), "R_hi": R_ * math.exp(Z95 * se)}


def compute(allow_missing: bool = False) -> dict:
    """allow_missing=True skips programs whose payload is not stored yet (job still
    queued); the circuits concerned are then flagged incomplete, not analysed."""
    e = pd.read_csv(CSV)
    led = pd.read_csv(LEDGER)
    led = led[led.platform == PLATFORM]
    rows, missing = [], []
    for c, k, inp, f in R.programs():
        expected = R.expected_bits(c, inp)
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
            rows.append({"circuit": c, "input": k, "inp": " ".join(map(str, inp)), "file": f, "expected": expected,
                         "pipeline": pipe, "arm": "P0" if pipe == "P0" else "pick",
                         "n_qubits": qc["n_qubits"], "n_2q": qc["n_2q"], "n_1q": qc["n_1q"], "hqc": hqc,
                         "shots": N, "k_success": ks, "p_success": p, "sd": math.sqrt(p * (1 - p) / N),
                         "F_H_payload": float(d["F_H"]), "F_H_csv": float(r.F_H.iloc[0]),
                         "n_outcomes": len(counts), "job_id": d["job_id"], "ledger_timestamp": l.timestamp.iloc[0]})
    t = pd.DataFrame(rows)

    def arm_sum(df, arm):
        s = df[df.arm == arm]
        return int(s.k_success.sum()), int(s.shots.sum())

    def arm_hqc(df, arm):
        return float(df[df.arm == arm].hqc.sum())

    bad = {f for f, _ in missing}
    per_input, primary, ratio = [], {}, {}
    for c in R.ORDER:
        tc = t[t.circuit == c]
        for k in range(1, R.CIRCUITS[c][2] + 1):
            if R.file_name(c, k) in bad:
                continue
            ti = tc[tc.input == k]
            per_input.append(dict(circuit=c, input=k, pick=R.CIRCUITS[c][1],
                                  **wald_diff(*arm_sum(ti, "pick"), *arm_sum(ti, "P0"))))
        if not any(f.startswith(c) for f in bad):
            k1, n1 = arm_sum(tc, "pick")
            k0, n0 = arm_sum(tc, "P0")
            primary[c] = dict(pick=R.CIRCUITS[c][1], **pooled_z(k1, n1, k0, n0))
            ratio[c] = dict(pick=R.CIRCUITS[c][1], **ratio_R(arm_hqc(tc, "pick"), k1, n1, arm_hqc(tc, "P0"), k0, n0))
    if len(primary) == len(R.ORDER):
        hl = holm({c: v["p_value"] for c, v in primary.items()})
        for c in primary:
            primary[c].update(hl[c])
    both = wald_diff(*arm_sum(t, "pick"), *arm_sum(t, "P0")) if not missing else None
    return {"rows": t, "per_input": pd.DataFrame(per_input), "primary": primary, "ratio": ratio, "both": both,
            "hqc_total": float(t.hqc.sum()), "n_jobs": int(t.job_id.nunique()), "missing": missing}


def h22e_grand_total() -> tuple:
    """(jobs, HQC) over every stored H2-2E payload with counts summing to shots, all run directories."""
    df = evidence_index.payload_rows()
    ok = df[df.counts_ok & (df.platform == PLATFORM)]
    return int(ok.job_id.nunique()), float(ok.hqc_estimate.sum())


def render_md(r: dict) -> str:
    jobs, hqc = h22e_grand_total()
    L = ["# H2-2E run of vbe_adder_3 and hwb6 on non-zero inputs (P0 vs PSEL4 pick)", "",
         "Generated by `python3 submit/h22e_b1.py --md results/h22e_b1.md` from the stored payloads "
         "`results/emulator/nexus_H2-2E_famB1_multi/<pipeline>/<circuit>_i<k>.json`. Pre-registration: "
         "`results/h22e_b1_prereg.md`. Platform nexus:H2-2E, noisy simulation, 400 shots per job, one program per job. "
         "PSEL4 pick: L3 for vbe_adder_3 (4 inputs), P2L3 for hwb6 (3 inputs). The result is reported whatever it is.", "",
         "## Primary test (pre-registered): pooled two-proportion z per circuit, Holm over the two circuits", "",
         "| Circuit | Pick | Shots per arm | K(pick) | K(P0) | p(pick) | p(P0) | p(pick) - p(P0) | pooled sd | z | p (two-sided) | Holm p | Reject at 0.05 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, v in r["primary"].items():
        L.append("| %s | %s | %d | %d | %d | %.4f | %.4f | %+.4f | %.4f | %+.2f | %.4f | %.4f | %s |"
                 % (c, v["pick"], v["N_arm"], v["k_pick"], v["k_P0"], v["p_pick"], v["p_P0"], v["d"], v["sd_pooled"],
                    v["z"], v["p_value"], v.get("p_holm", float("nan")), "yes" if v.get("reject") else "no"))
    L += ["", "## Secondary: HQC per correct output, pick relative to P0", "",
          "| Circuit | Pick | HQC(pick) | HQC(P0) | HQC per correct, pick | HQC per correct, P0 | R | 95 % interval (delta) |",
          "|---|---|---|---|---|---|---|---|"]
    for c, v in r["ratio"].items():
        L.append("| %s | %s | %.2f | %.2f | %.4f | %.4f | %.4f | [%.4f, %.4f] |"
                 % (c, v["pick"], v["H_pick"], v["H_P0"], v["C_pick"], v["C_P0"], v["R"], v["R_lo"], v["R_hi"]))
    b = r["both"]
    L += ["", "## Secondary: per input and pooled over both circuits", "",
          "Pooled over both circuits (pick minus P0, Wald sd): p(pick) = %.4f, p(P0) = %.4f, d = %+.4f, sd %.4f, z = %.2f, %d shots per arm."
          % (b["p_pick"], b["p_P0"], b["d"], b["sd"], b["z"], b["N_arm"]), "",
          "| Circuit | Input | Pick | p(pick) | p(P0) | d | sd (Wald) | z |", "|---|---|---|---|---|---|---|---|"]
    for v in r["per_input"].itertuples():
        L.append("| %s | i%d | %s | %.4f | %.4f | %+.4f | %.4f | %.2f |"
                 % (v.circuit, v.input, v.pick, v.p_pick, v.p_P0, v.d, v.sd, v.z))
    L += ["", "## Jobs", "",
          "| File | Input | Expected (c[0] first) | Pipeline | n_2q | n_1q | HQC | Successes / shots | p_success = F_H | sd | Job ID |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in r["rows"].itertuples():
        L.append("| %s | %s | `%s` | %s | %d | %d | %.2f | %d / %d | %.4f | %.4f | `%s` |"
                 % (t.file, t.inp, t.expected, t.pipeline, t.n_2q, t.n_1q, t.hqc, t.k_success, t.shots,
                    t.p_success, t.sd, t.job_id))
    L += ["",
          "- Input column: `a b` for vbe_adder_3 (a_i on q[1+3i], b_i on q[2+3i], cin = q[0] = 0, carry ancillas q[3], q[6] = 0, "
          "cout = q[9]), `x` for hwb6 (bit i of x on q[i]). Inputs drawn with numpy default_rng(20261012), see the pre-registration.",
          "- p_success = count of the expected bitstring / 400. The ideal output is a single basis state, so the Hellinger "
          "fidelity to it equals p_success. sd is binomial.",
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
        print("PRIMARY %s %s: p_pick %.4f p_P0 %.4f d %+.4f z %.2f p %.4f Holm %.4f reject %s"
              % (c, v["pick"], v["p_pick"], v["p_P0"], v["d"], v["z"], v["p_value"], v["p_holm"], v["reject"]))
    for c, v in r["ratio"].items():
        print("R %s %s: %.4f [%.4f, %.4f]" % (c, v["pick"], v["R"], v["R_lo"], v["R_hi"]))
    b = r["both"]
    print("both circuits: d %+.4f sd %.4f z %.2f" % (b["d"], b["sd"], b["z"]))
    print("HQC run %.2f (%d jobs); H2-2E grand total %d jobs %.1f HQC" % ((r["hqc_total"], r["n_jobs"]) + h22e_grand_total()))


if __name__ == "__main__":
    main()
