"""Statistics of the H2-2E emulator runs (Section 3.7.1 and Table E2 of the report).

Inputs (all under results/)
  emulator_nexus_H2-2E.csv              6 rows: vbe_adder_3, hwb6, grover_5 x P0, P2
  emulator/nexus_H2-2E/<pipeline>/<file>.json   raw counts, hqc_estimate, cost_fields
  emulator_jobs.csv                     job ledger
  family_B1_proxy_h22e.csv              proxy F_H (n <= 7 only, so hwb6 alone)
  selene_depolarizing_full.csv          Selene DepolarizingErrorModel F_H, 2000 shots

What it computes
  F_H        Hellinger fidelity of the returned counts to the ideal distribution
             (noise-free output of the P0ref compilation), recomputed from the counts.
  sd F_H     binomial sqrt(F (1 - F) / N) when the ideal distribution has a single
             outcome, otherwise the sd over BOOT multinomial bootstrap resamples
             of the counts with seed SEED.
  dF         F_H(P2) - F_H(P0) with sd = hypot of the two sds and z = dF / sd.
  slope a    no-intercept least-squares slope of -ln F_H on n_2q over the 35
             family B1 proxy rows (results/proxy_h22e_fits.log, "a n_2q only").
  dF_pred    F_H(P0) (exp(a dN_2q) - 1) with dN_2q = n_2q(P0) - n_2q(P2).
  shots_2sd  shots per pipeline at which 2 sd of the difference equals dF_pred,
             with the sd scaled from the measured one as 1 / sqrt(N):
             ceil(1000 (2 sd / dF_pred)^2).
  z_vs_pred  (dF - dF_pred) / sd.
  hqc_total  sum of hqc_estimate over the 6 JSON payloads.  The platform returned
             only a duration in cost_fields, so this is the formula estimate of
             pipelines/compile.py:hqc, not a charged amount.

Run from the repository root:

    python3 submit/h22e_stats.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
PLATFORM_DIR = os.path.join(RESULTS, "emulator", "nexus_H2-2E")
CSV = os.path.join(RESULTS, "emulator_nexus_H2-2E.csv")
LEDGER = os.path.join(RESULTS, "emulator_jobs.csv")

FILES = ["vbe_adder_3.qasm", "hwb6.qasm", "grover_5.qasm"]
PIPELINES = ["P0", "P2"]
BOOT = 4000
SEED = 20261008
SUPPORT_TOL = 1e-12          # noise/run_proxy.py:SUPPORT_TOL
QUOTA_HQC = 10000.0          # Aqora forum topic "Emulator Cost", per team on H2-1E and H2-2E
SLOPE_LOG = 1.1801e-3        # results/proxy_h22e_fits.log, family B1, "a n_2q only"


def reference_probs(file: str) -> np.ndarray:
    """Ideal distribution of a B1 circuit: noise-free output of the P0ref
    compilation, as in submit/common.py:reference_probs."""
    p = os.path.join(ROOT, "pipelines")
    if p not in sys.path:
        sys.path.insert(0, p)
    from compile import probs_from_measured_qasm
    with open(os.path.join(RESULTS, "compiled", "P0ref", file)) as f:
        return probs_from_measured_qasm(f.read())


def load_payload(pipeline: str, file: str) -> dict:
    with open(os.path.join(PLATFORM_DIR, pipeline, file[:-5] + ".json")) as f:
        return json.load(f)


def counts_vector(counts: dict, n: int) -> np.ndarray:
    """Counts keyed by bit strings with c[0] first -> vector indexed with c[0]
    most significant (submit/common.py:counts_to_probs convention)."""
    c = np.zeros(2 ** n)
    for key, v in counts.items():
        bits = key.replace(" ", "")
        assert len(bits) == n, (key, n)
        c[int(bits, 2)] += v
    return c


def hellinger_fidelity(p, q) -> float:
    return float(np.sum(np.sqrt(np.asarray(p, float) * np.asarray(q, float))) ** 2)


def b1_slope() -> float:
    pb = pd.read_csv(os.path.join(RESULTS, "family_B1_proxy_h22e.csv"))
    y, x = -np.log(pb.F_H.values), pb.n_2q.values.astype(float)
    return float(x @ y / (x @ x))


def compute() -> dict:
    """Return {"rows": DataFrame (one row per file and pipeline),
    "pairs": DataFrame (one row per file), "cross": DataFrame (rows also run
    on the H2-Emulator), "hqc_total", "quota_frac", "slope",
    "max_abs_dF_csv", "max_abs_dF_json"}."""
    e = pd.read_csv(CSV)
    assert len(e) == 6 and set(e.file) == set(FILES) and set(e.pipeline) == set(PIPELINES)
    ledger = pd.read_csv(LEDGER)
    ledger = ledger[ledger.platform == "nexus:H2-2E"]
    proxy = pd.read_csv(os.path.join(RESULTS, "family_B1_proxy_h22e.csv"))
    proxy = {(r.file, r.pipeline): float(r.F_H) for r in proxy.itertuples()}
    sel = pd.read_csv(os.path.join(RESULTS, "selene_depolarizing_full.csv"))
    sel = {(r.file, r.pipeline): (float(r.F_H_selene_depol), int(r.shots)) for r in sel.itertuples()}

    rng = np.random.default_rng(SEED)
    rows = []
    for file in FILES:
        q = reference_probs(file)
        n_q = int(np.log2(len(q)))
        support = int((q > SUPPORT_TOL).sum())
        for pipe in PIPELINES:
            r = e[(e.file == file) & (e.pipeline == pipe)].iloc[0]
            d = load_payload(pipe, file)
            assert d["job_id"] == r.job_id and d["platform"] == "nexus:H2-2E"
            assert int(r.support_size) == support and int(r.n_qubits) == n_q
            c = counts_vector(d["counts"], n_q)
            N = int(c.sum())
            assert N == int(r.shots) == int(d["shots"])
            phat = c / N
            f = hellinger_fidelity(phat, q)
            if support == 1:
                sd, method = float(np.sqrt(f * (1 - f) / N)), "binomial"
            else:
                boot = rng.multinomial(N, phat, size=BOOT) / N
                fb = np.sum(np.sqrt(boot * q[None, :]), axis=1) ** 2
                sd, method = float(fb.std(ddof=1)), "bootstrap"
            led = ledger[(ledger.file == file) & (ledger.pipeline == pipe) & (ledger.job_id == r.job_id)]
            assert len(led) == 1 and led.status.iloc[0] == "COMPLETED"
            sf, ss = sel.get((file, pipe), (np.nan, 0))
            rows.append({"file": file, "n": int(r.n), "pipeline": pipe, "n_2q": int(r.n_2q),
                         "support": support, "shots": N, "hqc": float(d["hqc_estimate"]),
                         "duration": d["cost_fields"].get("duration"),
                         "job_id": r.job_id, "F_H": f, "F_H_csv": float(r.F_H),
                         "F_H_json": float(d["F_H"]), "sd": sd, "sd_method": method,
                         "F_H_proxy": proxy.get((file, pipe), np.nan),
                         "F_H_selene": sf, "shots_selene": ss})
    t = pd.DataFrame(rows)
    slope = b1_slope()
    assert abs(slope - SLOPE_LOG) < 5e-8, slope

    # Comparisons with the proxy (exact, sd = emulator sd) and with Selene
    # (sampled, binomial or bootstrap sd scaled by sqrt(1000 / shots_selene)).
    t["z_proxy"] = (t.F_H - t.F_H_proxy) / t.sd
    t["sd_vs_selene"] = t.sd * np.sqrt(1 + t.shots / t.shots_selene.replace(0, np.nan))
    t["z_selene"] = (t.F_H - t.F_H_selene) / t.sd_vs_selene

    pairs = []
    for file in FILES:
        a0 = t[(t.file == file) & (t.pipeline == "P0")].iloc[0]
        a2 = t[(t.file == file) & (t.pipeline == "P2")].iloc[0]
        dN = int(a0.n_2q - a2.n_2q)
        dF = float(a2.F_H - a0.F_H)
        sd = float(np.hypot(a0.sd, a2.sd))
        pred = float(a0.F_H * (np.exp(slope * dN) - 1))
        pairs.append({"file": file, "dN_2q": dN, "ratio_pred": float(np.exp(slope * dN)),
                      "dF": dF, "sd_diff": sd, "z": dF / sd, "dF_pred": pred,
                      "pred_over_sd": pred / sd, "z_vs_pred": (dF - pred) / sd,
                      "shots_2sd": int(np.ceil(a0.shots * (2 * sd / pred) ** 2)),
                      "dF_proxy": float(a2.F_H_proxy - a0.F_H_proxy)})
    pairs = pd.DataFrame(pairs)

    # Same circuit and pipeline on the Nexus H2-Emulator (Table E1): grover_5 under P0.
    cross = []
    h2e = pd.read_csv(os.path.join(RESULTS, "emulator_nexus_H2-Emulator.csv"))
    rng_x = np.random.default_rng(SEED)
    for x in h2e[h2e.file.isin(FILES)].itertuples():
        a = t[(t.file == x.file) & (t.pipeline == x.pipeline)].iloc[0]
        q = reference_probs(x.file)
        with open(os.path.join(RESULTS, "emulator", "nexus_H2-Emulator", x.pipeline, x.file[:-5] + ".json")) as f:
            c = counts_vector(json.load(f)["counts"], int(x.n_qubits))
        N = int(c.sum())
        phat = c / N
        fx = hellinger_fidelity(phat, q)
        assert abs(fx - x.F_H) < 1e-9
        boot = rng_x.multinomial(N, phat, size=BOOT) / N
        sdx = float((np.sum(np.sqrt(boot * q[None, :]), axis=1) ** 2).std(ddof=1))
        cross.append({"file": x.file, "pipeline": x.pipeline, "F_H_h2emulator": fx, "sd_h2emulator": sdx,
                      "F_H_h22e": float(a.F_H), "sd_h22e": float(a.sd),
                      "z": float((a.F_H - fx) / np.hypot(a.sd, sdx))})
    cross = pd.DataFrame(cross)
    hqc_total = float(t.hqc.sum())
    return {"rows": t, "pairs": pairs, "cross": cross, "hqc_total": hqc_total,
            "quota_frac": hqc_total / QUOTA_HQC, "slope": slope,
            "max_abs_dF_csv": float((t.F_H - t.F_H_csv).abs().max()),
            "max_abs_dF_json": float((t.F_H - t.F_H_json).abs().max())}


def main():
    r = compute()
    pd.set_option("display.width", 200)
    cols = ["file", "pipeline", "n_2q", "support", "hqc", "duration", "F_H", "sd", "sd_method",
            "F_H_proxy", "z_proxy", "F_H_selene", "z_selene", "job_id"]
    print(r["rows"][cols].to_string(index=False))
    print()
    print(r["pairs"].to_string(index=False))
    print()
    print(r["cross"].to_string(index=False))
    t = r["rows"]
    d = t.F_H - t.F_H_selene
    print("vs Selene: mean %+.4f, min z %.2f, max z %.2f, within 2 sd %d of %d"
          % (d.mean(), t.z_selene.min(), t.z_selene.max(), int((t.z_selene.abs() <= 2).sum()), len(t)))
    print("slope a = %.4e per ZZ gate" % r["slope"])
    print("HQC estimate total %.1f of %.0f = %.2f %%" % (r["hqc_total"], QUOTA_HQC, 100 * r["quota_frac"]))
    print("max |F_H - CSV| %.2e, max |F_H - JSON| %.2e" % (r["max_abs_dF_csv"], r["max_abs_dF_json"]))


if __name__ == "__main__":
    main()
