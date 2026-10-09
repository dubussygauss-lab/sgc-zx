"""Confirmatory test of the H2-2E repeats r2, r3, r4 alone (Section 3.7.1).

Why r2-r4 alone
  The original run r1 (Table E2) covered vbe_adder_3, hwb6 and grover_5.  The two
  circuits that were repeated (vbe_adder_3, grover_5) were chosen after r1 was seen.
  The pooled test of submit/h22e_pooled.py (Table E3) includes r1 and so includes the
  data that drove the choice.  r2, r3 and r4 were submitted after the choice.  A test
  on r2-r4 alone is free of selection on its own data.

Inputs (all under results/)
  emulator/nexus_H2-2E_r<k>/<pipeline>/<file>.json   repeat runs r2, r3, r4
  compiled/P0ref/<file>                               ideal distribution (h22e_stats.reference_probs)
  emulator_nexus_H2-2E_r<k>.csv                       n_2q per (file, pipeline)
  emulator_jobs.csv                                   submission timestamps of r2-r4

What it computes for vbe_adder_3 and grover_5 under P0 and P2
  F_H        Hellinger fidelity of the summed r2-r4 counts (3000 shots per pipeline)
             to the P0ref ideal distribution.  Same functions as h22e_pooled.py.
  sd         binomial sqrt(F (1 - F) / N) when the ideal output has one basis state,
             otherwise sd over BOOT multinomial bootstrap resamples of the summed
             counts with a fresh numpy default_rng(SEED) per cell (h22e_pooled.py).
  dF         F_H(P2) - F_H(P0), sd = hypot, z = dF / sd.
  p          two-sided normal p = erfc(|z| / sqrt 2).  Primary.
  p_one      one-sided p for the direction P2 > P0, 0.5 erfc(z / sqrt 2).  The slope
             model of Section 3.7.1 (a = h22e_stats.SLOPE_LOG) predicts a positive gain
             for both circuits because P2 has fewer ZZ gates.  Secondary.
  p_holm     Holm adjustment of the two-sided p over the two confirmatory circuits.
  p_one_holm Holm adjustment of the one-sided p over the same two circuits.
  dF_pred    F_H(P0) (exp(a dN_2q) - 1), z_vs_pred = (dF - dF_pred) / sd.
  support    number of basis states with ideal probability > SUPPORT_TOL, the ideal
             bit string when the support is one, and the input state of the circuit
             (also printed for hwb6, the third Table E2 circuit, which was not repeated).

Writes results/h22e_confirmatory.csv.  Run from the repository root:

    python3 submit/h22e_confirmatory.py
"""

import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22e_pooled as hp  # noqa: E402
import h22e_stats as hs  # noqa: E402

ROOT = hs.ROOT
RESULTS = hs.RESULTS
FILES = hp.FILES                         # vbe_adder_3.qasm, grover_5.qasm
INFO_FILES = FILES + ["hwb6.qasm"]       # support and input also for the third Table E2 circuit
PIPELINES = hp.PIPELINES                 # P0, P2
CONF_RUNS = ["r2", "r3", "r4"]
BOOT = hs.BOOT
SEED = hs.SEED
SLOPE = hs.SLOPE_LOG
SUPPORT_TOL = hs.SUPPORT_TOL
OUT_CSV = os.path.join(RESULTS, "h22e_confirmatory.csv")


def input_state(file: str) -> dict:
    """Input of the circuit: OpenQASM 2 starts every qubit in |0>.  The input is the
    all-zero basis state when no compiled or source QASM contains a reset (a reset or
    a measurement before the final layer would be the only way to change it).  Gates
    such as the x q[5] of grover_5 belong to the circuit, not to its input."""
    paths = [os.path.join(ROOT, "bench", "family_B1", file)] + \
            [os.path.join(RESULTS, "compiled", p, file) for p in ["P0ref", "P0", "P2"]]
    n, resets = None, 0
    for p in paths:
        with open(p) as f:
            txt = f.read()
        m = re.search(r"qreg\s+q\[(\d+)\]", txt)
        k = int(m.group(1))
        assert n is None or n == k, (file, p)
        n = k
        resets += len(re.findall(r"^\s*reset\b", txt, flags=re.M))
    return {"n_qubits": n, "n_resets": resets, "input": "|0>^%d (all-zero)" % n if resets == 0 else "not all-zero"}


def support(file: str) -> dict:
    q = hs.reference_probs(file)
    n = int(np.log2(len(q)))
    sup = q > SUPPORT_TOL
    out = {"n_qubits_ref": n, "support": int(sup.sum()), "q_max": float(q.max())}
    out["ideal_bitstring"] = format(int(np.argmax(q)), "0%db" % n) if sup.sum() == 1 else ""
    return out


def load_cell(file: str, pipe: str, runs=CONF_RUNS) -> dict:
    q = hs.reference_probs(file)
    n_q = int(np.log2(len(q)))
    vecs, jobs, shots = [], [], []
    for run in runs:
        path = os.path.join(hp.run_dir(run), pipe, file[:-5] + ".json")
        with open(path) as f:
            d = json.load(f)
        assert hp.valid_counts(d), path
        assert d["platform"] == "nexus:H2-2E" and d["file"] == file and d["pipeline"] == pipe, path
        vecs.append(hs.counts_vector(d["counts"], n_q))
        jobs.append(d["job_id"])
        shots.append(int(d["shots"]))
    n2 = set()
    for run in runs:
        c = pd.read_csv(hp.run_csv(run))
        n2 |= set(c[(c.file == file) & (c.pipeline == pipe)].n_2q.astype(int))
    assert len(n2) == 1, (file, pipe, n2)
    return {"q": q, "counts": np.vstack(vecs), "jobs": jobs, "shots": shots, "n_2q": n2.pop()}


def cell_stats(q: np.ndarray, pooled: np.ndarray) -> tuple:
    """F_H and sd of summed counts, same rule as h22e_pooled.compute()."""
    N = int(pooled.sum())
    F = hs.hellinger_fidelity(pooled / N, q)
    if (q > SUPPORT_TOL).sum() == 1:
        return F, math.sqrt(F * (1 - F) / N), "binomial"
    rng = np.random.default_rng(SEED)
    b = rng.multinomial(N, pooled / N, size=BOOT) / N
    return F, float((np.sum(np.sqrt(b * q[None, :]), axis=1) ** 2).std(ddof=1)), "bootstrap"


def submission_window() -> dict:
    """First and last ledger timestamp (UTC) of the r2-r4 jobs."""
    led = pd.read_csv(hs.LEDGER)
    m = led.result_path.fillna("").str.contains(r"nexus_H2-2E_r[234]/", regex=True)
    return {"first_submit_utc": led[m].timestamp.min(), "last_submit_utc": led[m].timestamp.max(),
            "n_jobs": int(m.sum())}


def compute() -> dict:
    cells = []
    for file in FILES:
        for pipe in PIPELINES:
            c = load_cell(file, pipe)
            pooled = c["counts"].sum(axis=0)
            F, sd, method = cell_stats(c["q"], pooled)
            cells.append({"file": file, "pipeline": pipe, "runs": ",".join(CONF_RUNS),
                          "shots": int(pooled.sum()), "n_2q": c["n_2q"], "F_H": F, "sd": sd,
                          "sd_method": method, "job_ids": " ".join(c["jobs"])})
    cells = pd.DataFrame(cells)
    pairs = []
    for file in FILES:
        a0 = cells[(cells.file == file) & (cells.pipeline == "P0")].iloc[0]
        a2 = cells[(cells.file == file) & (cells.pipeline == "P2")].iloc[0]
        dN = int(a0.n_2q - a2.n_2q)
        dF = float(a2.F_H - a0.F_H)
        sd = float(math.hypot(a0.sd, a2.sd))
        z = dF / sd
        pred = float(a0.F_H * (math.exp(SLOPE * dN) - 1))
        pairs.append({"file": file, "shots_per_pipeline": int(a0.shots), "dN_2q": dN, "dF": dF, "sd": sd,
                      "z": z, "p": math.erfc(abs(z) / math.sqrt(2)),
                      "p_one": 0.5 * math.erfc(z / math.sqrt(2)),
                      "dF_pred": pred, "z_vs_pred": (dF - pred) / sd})
    pairs = pd.DataFrame(pairs)
    pairs["p_holm"] = hp.holm(pairs.p.values)
    pairs["p_one_holm"] = hp.holm(pairs.p_one.values)
    info = pd.DataFrame([{"file": f, **support(f), **input_state(f)} for f in INFO_FILES])
    return {"cells": cells, "pairs": pairs, "info": info, "window": submission_window()}


def to_csv(r: dict, path=OUT_CSV) -> pd.DataFrame:
    rows = []
    for c in r["cells"].itertuples():
        pr = r["pairs"][r["pairs"].file == c.file].iloc[0]
        inf = r["info"][r["info"].file == c.file].iloc[0]
        rows.append({"file": c.file, "pipeline": c.pipeline, "runs": c.runs, "shots": c.shots, "n_2q": c.n_2q,
                     "F_H": c.F_H, "sd": c.sd, "sd_method": c.sd_method,
                     "dF": pr.dF, "sd_dF": pr.sd, "z": pr.z, "p_two_sided": pr.p, "p_holm2": pr.p_holm,
                     "p_one_sided": pr.p_one, "p_one_sided_holm2": pr.p_one_holm,
                     "dF_pred": pr.dF_pred, "z_vs_pred": pr.z_vs_pred,
                     "ideal_support": inf.support, "ideal_bitstring": inf.ideal_bitstring,
                     "input": inf.input, "job_ids": c.job_ids})
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, float_format="%.10g")
    return df


def main():
    r = compute()
    pd.set_option("display.width", 220)
    print(r["cells"].drop(columns=["job_ids"]).to_string(index=False))
    print()
    print(r["pairs"].to_string(index=False))
    print()
    print(r["info"].to_string(index=False))
    print()
    print("r2-r4 submission window (ledger, UTC):", r["window"])
    to_csv(r)
    print("wrote", os.path.relpath(OUT_CSV, ROOT))


if __name__ == "__main__":
    main()
