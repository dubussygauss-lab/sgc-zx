"""Pooled statistics of the repeated H2-2E runs (Section 3.7.1, Table E3).

Inputs (all under results/)
  emulator/nexus_H2-2E/<pipeline>/<file>.json      original run (run label r1)
  emulator/nexus_H2-2E_r<k>/<pipeline>/<file>.json repeat runs r2, r3, r4
  emulator_nexus_H2-2E.csv, emulator_nexus_H2-2E_r<k>.csv  one row per job
  emulator_jobs.csv                                 job ledger
  family_B1_proxy_h22e.csv                          for the slope a (h22e_stats.b1_slope)

A run counts for a cell (file, pipeline) only when its JSON holds counts that
sum to its shot count and carries no error.  A JSON with an error (a job still
waiting when it was fetched) is listed as pending and left out of every number.

What it computes for vbe_adder_3 and grover_5 under P0 and P2
  F_H per run    Hellinger fidelity of the run's counts to the P0ref reference
                 (h22e_stats.reference_probs).
  homogeneity    single-outcome circuits (vbe_adder_3): Pearson chi-square on the
                 runs x {success, failure} table, k - 1 dof.  grover_5: Pearson
                 chi-square on the runs x (64 support outcomes + one bin for every
                 outcome outside the support) table.  A Monte Carlo p from MC
                 tables drawn as multinomial(N_run, pooled frequencies) is printed
                 as a check of the asymptotic p.
  pooled F_H     F_H of the summed counts.
  sd             binomial sqrt(F (1 - F) / N) for vbe_adder_3, sd over BOOT
                 multinomial bootstrap resamples of the pooled counts for grover_5
                 with a fresh numpy default_rng(SEED) per cell.
  dF             pooled F_H(P2) - pooled F_H(P0), sd = hypot, z = dF / sd,
                 two-sided normal p = erfc(|z| / sqrt 2).
  dF_pred        pooled F_H(P0) (exp(a dN_2q) - 1) with a = h22e_stats.SLOPE_LOG.
  z_vs_pred      (dF - dF_pred) / sd.
  p_holm         Holm step-down adjustment of the two-sided p over the circuits.
  HQC            sum of hqc_estimate over every H2-2E JSON (original + repeats).
                 Completed-only and all-submitted totals are both printed.

The 'final' label is printed only when all four cells hold EXPECTED_RUNS runs.
fill_prose() fills report/sec371_pooled_v5.md into report/sec371_pooled_v5.filled.md.

Run from the repository root:

    python3 submit/h22e_pooled.py
"""

import glob
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22e_stats  # noqa: E402

ROOT = h22e_stats.ROOT
RESULTS = h22e_stats.RESULTS
EMU = os.path.join(RESULTS, "emulator")
LEDGER = h22e_stats.LEDGER
FILES = ["vbe_adder_3.qasm", "grover_5.qasm"]
PIPELINES = ["P0", "P2"]
RUNS = ["r1", "r2", "r3", "r4"]          # r1 is the original run of Table E2
EXPECTED_RUNS = len(RUNS)
BOOT = h22e_stats.BOOT
SEED = h22e_stats.SEED
MC = 4000                                # Monte Carlo tables for the homogeneity check
QUOTA_HQC = h22e_stats.QUOTA_HQC
SLOPE = h22e_stats.SLOPE_LOG
SUPPORT_TOL = h22e_stats.SUPPORT_TOL
TEMPLATE = os.path.join(ROOT, "report", "sec371_pooled_v5.md")
FILLED = os.path.join(ROOT, "report", "sec371_pooled_v5.filled.md")


def run_dir(run: str) -> str:
    return os.path.join(EMU, "nexus_H2-2E" if run == "r1" else "nexus_H2-2E_" + run)


def run_csv(run: str) -> str:
    return os.path.join(RESULTS, "emulator_nexus_H2-2E.csv" if run == "r1"
                        else "emulator_nexus_H2-2E_" + run + ".csv")


def valid_counts(d: dict) -> bool:
    c = d.get("counts")
    return (not d.get("error")) and isinstance(c, dict) and len(c) > 0 \
        and int(sum(c.values())) == int(d.get("shots", -1))


def all_h22e_jsons() -> list:
    """Every H2-2E payload of the original run and of every repeat directory."""
    dirs = [os.path.join(EMU, "nexus_H2-2E")] + sorted(glob.glob(os.path.join(EMU, "nexus_H2-2E_r*")))
    return sorted(p for d in dirs for p in glob.glob(os.path.join(d, "*", "*.json")))


def hqc_totals() -> dict:
    done = sub = 0.0
    n_done = n_sub = 0
    for p in all_h22e_jsons():
        with open(p) as f:
            d = json.load(f)
        assert d["platform"] == "nexus:H2-2E", p
        sub += float(d["hqc_estimate"])
        n_sub += 1
        if valid_counts(d):
            done += float(d["hqc_estimate"])
            n_done += 1
    return {"hqc_completed": done, "jobs_completed": n_done, "hqc_submitted": sub, "jobs_submitted": n_sub}


def chi2_homogeneity(table: np.ndarray, rng) -> tuple:
    """Pearson chi-square on a runs x categories table (columns with zero total
    dropped), asymptotic p and Monte Carlo p under multinomial(N_run, pooled_p)."""
    table = table[:, table.sum(axis=0) > 0]
    k, m = table.shape
    if k < 2:
        return np.nan, 0, np.nan, np.nan

    def stat(t):
        e = t.sum(axis=1, keepdims=True) * t.sum(axis=0, keepdims=True) / t.sum()
        with np.errstate(divide="ignore", invalid="ignore"):
            return float(np.nansum(np.where(e > 0, (t - e) ** 2 / e, 0.0)))

    x2 = stat(table)
    dof = (k - 1) * (m - 1)
    p = float(stats.chi2.sf(x2, dof))
    n_r = table.sum(axis=1).astype(int)
    pp = table.sum(axis=0) / table.sum()   # pooled frequencies
    sims = np.array([stat(np.vstack([rng.multinomial(n, pp) for n in n_r])) for _ in range(MC)])
    p_mc = float((1 + (sims >= x2 - 1e-12).sum()) / (MC + 1))
    return x2, dof, p, p_mc


def holm(p) -> np.ndarray:
    """Holm step-down adjusted p values, same order as the input."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for i, j in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[j]))
        adj[j] = run
    return adj


def compute() -> dict:
    ledger = pd.read_csv(LEDGER)
    ledger = ledger[ledger.platform == "nexus:H2-2E"]
    rows, pending = [], []
    for run in RUNS:
        csv = pd.read_csv(run_csv(run)) if os.path.exists(run_csv(run)) else None
        for file in FILES:
            for pipe in PIPELINES:
                path = os.path.join(run_dir(run), pipe, file[:-5] + ".json")
                if not os.path.exists(path):
                    pending.append({"run": run, "file": file, "pipeline": pipe, "reason": "no JSON"})
                    continue
                with open(path) as f:
                    d = json.load(f)
                if not valid_counts(d):
                    pending.append({"run": run, "file": file, "pipeline": pipe, "job_id": d.get("job_id"),
                                    "reason": "no counts" if not d.get("error") else str(d["error"])[:60]})
                    continue
                assert d["platform"] == "nexus:H2-2E" and d["file"] == file and d["pipeline"] == pipe, path
                led = ledger[ledger.job_id == d["job_id"]]
                csv_row = None if csv is None else csv[(csv.file == file) & (csv.pipeline == pipe)]
                rows.append({"run": run, "file": file, "pipeline": pipe, "job_id": d["job_id"],
                             "shots": int(d["shots"]), "counts": d["counts"], "hqc": float(d["hqc_estimate"]),
                             "ledger_status": led.status.iloc[0] if len(led) else "MISSING",
                             "n_2q": int(csv_row.n_2q.iloc[0]) if csv_row is not None and len(csv_row) else None,
                             "F_H_csv": float(csv_row.F_H.iloc[0]) if csv_row is not None and len(csv_row) else np.nan,
                             "F_H_json": float(d.get("F_H", np.nan))})
    runs = pd.DataFrame(rows)
    assert runs.job_id.is_unique, "the same job id appears in two runs"

    warnings = []
    per_run, cells, refs = [], [], {}
    for file in FILES:
        q = h22e_stats.reference_probs(file)
        n_q = int(np.log2(len(q)))
        sup = q > SUPPORT_TOL
        refs[file] = q
        for pipe in PIPELINES:
            g = runs[(runs.file == file) & (runs.pipeline == pipe)].sort_values("run")
            n2 = set(g.n_2q.dropna().astype(int))
            assert len(n2) <= 1, (file, pipe, n2)  # same compiled circuit in every run
            vecs = []
            for r in g.itertuples():
                c = h22e_stats.counts_vector(r.counts, n_q)
                f = h22e_stats.hellinger_fidelity(c / c.sum(), q)
                for src, v in (("CSV", r.F_H_csv), ("JSON", r.F_H_json)):
                    if not np.isnan(v) and abs(v - f) > 1e-9:
                        warnings.append(f"{r.run} {file} {pipe}: F_H {src} {v} differs from counts {f}")
                    if np.isnan(v):
                        warnings.append(f"{r.run} {file} {pipe}: no F_H in {src}")
                if r.ledger_status != "COMPLETED":
                    warnings.append(f"{r.run} {file} {pipe}: ledger status {r.ledger_status} for {r.job_id}")
                if sup.sum() == 1:
                    sd = math.sqrt(f * (1 - f) / c.sum())
                else:
                    rng = np.random.default_rng(SEED)
                    b = rng.multinomial(int(c.sum()), c / c.sum(), size=BOOT) / c.sum()
                    sd = float((np.sum(np.sqrt(b * q[None, :]), axis=1) ** 2).std(ddof=1))
                per_run.append({"file": file, "pipeline": pipe, "run": r.run, "job_id": r.job_id,
                                "shots": int(c.sum()), "F_H": f, "sd": sd})
                vecs.append(c)
            k = len(vecs)
            if k == 0:
                cells.append({"file": file, "pipeline": pipe, "runs": 0})
                continue
            C = np.vstack(vecs)
            pooled = C.sum(axis=0)
            N = int(pooled.sum())
            F = h22e_stats.hellinger_fidelity(pooled / N, q)
            if sup.sum() == 1:
                sd, method = math.sqrt(F * (1 - F) / N), "binomial"
                table = np.column_stack([C[:, sup].sum(axis=1), C[:, ~sup].sum(axis=1)])
                test = "chi-square on success / failure counts"
            else:
                rng = np.random.default_rng(SEED)
                b = rng.multinomial(N, pooled / N, size=BOOT) / N
                sd, method = float((np.sum(np.sqrt(b * q[None, :]), axis=1) ** 2).std(ddof=1)), "bootstrap"
                table = np.column_stack([C[:, sup], C[:, ~sup].sum(axis=1)])
                test = "chi-square on %d support outcomes + 1 outside bin" % int(sup.sum())
            x2, dof, p, p_mc = chi2_homogeneity(table, np.random.default_rng(SEED))
            fr = [x["F_H"] for x in per_run if x["file"] == file and x["pipeline"] == pipe]
            sr = [x["sd"] for x in per_run if x["file"] == file and x["pipeline"] == pipe]
            # Secondary check: chi-square of the per-run F_H about their weighted mean.
            w = 1 / np.square(sr)
            fbar = float((w * fr).sum() / w.sum())
            qf = float((w * (np.array(fr) - fbar) ** 2).sum())
            cells.append({"file": file, "pipeline": pipe, "runs": k, "run_labels": ",".join(g.run),
                          "shots": N, "n_2q": int(next(iter(n2))) if n2 else None,
                          "F_H": F, "sd": sd, "sd_method": method,
                          "F_min": min(fr), "F_max": max(fr),
                          "hom_test": test, "chi2": x2, "dof": dof, "p_hom": p, "p_hom_mc": p_mc,
                          "Q_FH": qf, "p_Q_FH": float(stats.chi2.sf(qf, k - 1)) if k > 1 else np.nan})
    cells = pd.DataFrame(cells)
    per_run = pd.DataFrame(per_run)

    pairs = []
    for file in FILES:
        a0 = cells[(cells.file == file) & (cells.pipeline == "P0")].iloc[0]
        a2 = cells[(cells.file == file) & (cells.pipeline == "P2")].iloc[0]
        if a0.runs == 0 or a2.runs == 0:
            continue
        dN = int(a0.n_2q - a2.n_2q)
        dF = float(a2.F_H - a0.F_H)
        sd = float(math.hypot(a0.sd, a2.sd))
        z = dF / sd
        pred = float(a0.F_H * (math.exp(SLOPE * dN) - 1))
        pairs.append({"file": file, "shots_P0": int(a0.shots), "shots_P2": int(a2.shots), "dN_2q": dN,
                      "dF": dF, "sd": sd, "z": z, "p": math.erfc(abs(z) / math.sqrt(2)),
                      "dF_pred": pred, "z_vs_pred": (dF - pred) / sd})
    pairs = pd.DataFrame(pairs)
    if len(pairs):
        pairs["p_holm"] = holm(pairs.p.values)
    hq = hqc_totals()
    final = bool(len(cells) == len(FILES) * len(PIPELINES) and (cells.runs == EXPECTED_RUNS).all())
    return {"runs": runs.drop(columns=["counts"]), "per_run": per_run, "cells": cells, "pairs": pairs,
            "pending": pd.DataFrame(pending), "warnings": warnings, "final": final, **hq,
            "hqc_pct": 100 * hq["hqc_completed"] / QUOTA_HQC,
            "hqc_pct_submitted": 100 * hq["hqc_submitted"] / QUOTA_HQC}


# ------------------------------------------------------------------ prose

WORD = {1: "one", 2: "two", 3: "three", 4: "four"}
SHORT = {"vbe_adder_3.qasm": "vbe", "grover_5.qasm": "grover"}


def _f4(x):
    return "%.4f" % x


def _s4(x):
    return "%+.4f" % x


def _p(x):
    return "%.2g" % x if x < 0.1 else "%.2f" % x


def _shots_phrase(pr) -> str:
    if pr.shots_P0 == pr.shots_P2:
        return "%d shots per pipeline" % pr.shots_P0
    return "%d shots under P0 and %d under P2" % (pr.shots_P0, pr.shots_P2)


def prose_values(r: dict) -> dict:
    cells, pairs = r["cells"], r["pairs"]
    v = {}
    reps = r["runs"][r["runs"].run != "r1"]
    v["n_repeat_jobs"] = str(len(reps))
    v["hqc_repeats"] = "%.1f" % reps.hqc.sum()
    v["hqc_total"] = "%.1f" % r["hqc_completed"]
    v["n_jobs_total"] = str(r["jobs_completed"])
    v["hqc_pct"] = "%.1f" % r["hqc_pct"]
    v["slope"] = ("%.4e" % SLOPE).replace("e-0", "e-")
    if r["final"]:
        v["cell_shots_phrase"] = "Each of the four cells now holds %d shots from four runs of 1000." % int(cells.shots.iloc[0])
    else:
        parts = ["%s %s %d" % (c.file[:-5], c.pipeline, c.runs) for c in cells.itertuples()]
        v["cell_shots_phrase"] = ("PARTIAL. The runs per cell are " + ", ".join(parts[:-1]) + " and " + parts[-1]
                                  + " of %d." % EXPECTED_RUNS)
    for c in cells.itertuples():
        k = SHORT[c.file] + "_" + c.pipeline
        v[k + "_F"] = _f4(c.F_H)
        v[k + "_sd"] = _f4(c.sd)
        v[k + "_min"] = _f4(c.F_min)
        v[k + "_max"] = _f4(c.F_max)
        v[k + "_x2"] = "%.1f" % c.chi2
        v[k + "_dof"] = str(int(c.dof))
        v[k + "_phom"] = _p(c.p_hom)
    rej = [c for c in cells.itertuples() if c.p_hom < 0.05]
    if not rej:
        v["hom_phrase"] = "No cell rejects homogeneity at the 0.05 level."
    else:
        names = ["%s under %s" % (c.file[:-5], c.pipeline) for c in rej]
        v["hom_phrase"] = ("Homogeneity is rejected at the 0.05 level for " + " and ".join(names) + ".")
    above = [c for c in cells.itertuples() if c.F_H > c.F_max + 1e-12]
    if above:
        by_file = {}
        for c in above:
            by_file.setdefault(c.file[:-5], []).append(c.pipeline)
        parts = ["%s under %s" % (f, " and ".join(ps)) for f, ps in by_file.items()]
        v["bias_phrase"] = (" The pooled F_H of %s exceeds every single-run value. Finite sampling lowers the"
                            " measured F_H of a spread distribution and the summed counts sample it more finely."
                            % " and of ".join(parts))
    else:
        v["bias_phrase"] = ""
    concl = []
    for pr in pairs.itertuples():
        k = SHORT[pr.file]
        v[k + "_dN"] = str(pr.dN_2q)
        v[k + "_dF"] = _s4(pr.dF)
        v[k + "_dsd"] = _f4(pr.sd)
        v[k + "_z"] = "%+.2f" % pr.z
        v[k + "_p"] = _p(pr.p)
        v[k + "_p_holm"] = _p(pr.p_holm)
        v[k + "_pred"] = _f4(pr.dF_pred)
        side = "below" if pr.z_vs_pred < 0 else "above"
        v[k + "_vs_pred"] = "%.2f sd %s" % (abs(pr.z_vs_pred), side)
        name = pr.file[:-5]
        if abs(pr.z) >= 2:
            s = ("On %s the pooled data resolve the difference at %s. P2 is %s P0 by %.4f with z = %+.2f."
                 % (name, _shots_phrase(pr), "above" if pr.dF > 0 else "below", abs(pr.dF), pr.z))
        else:
            s = ("On %s the difference is not resolved at %s. Its z is %+.2f."
                 % (name, _shots_phrase(pr), pr.z))
        if abs(pr.z_vs_pred) >= 2:
            s += " The measured difference lies more than 2 sd %s the gain predicted by the slope." % side
        else:
            s += " The measured difference lies within 2 sd of the gain predicted by the slope."
        concl.append(s)
    m = len(pairs)
    sig = [pr.file[:-5] for pr in pairs.itertuples() if pr.p_holm < 0.05]
    res_ = [pr.file[:-5] for pr in pairs.itertuples() if abs(pr.z) >= 2]
    if res_:
        kept = [f for f in res_ if f in sig]
        lost = [f for f in res_ if f not in sig]
        if kept:
            concl.append("After Holm adjustment over the %s circuits the difference on %s stays below p = 0.05."
                         % (WORD.get(m, str(m)), " and ".join(kept)))
        if lost:
            concl.append("After Holm adjustment over the %s circuits the difference on %s is no longer below"
                         " p = 0.05." % (WORD.get(m, str(m)), " and ".join(lost)))
    else:
        concl.append("No circuit reaches p = 0.05 before or after Holm adjustment over the %s circuits."
                     % WORD.get(m, str(m)))
    v["conclusion"] = " ".join(concl)
    if rej:
        v["hom_caveat"] = (" The rejected homogeneity test means the runs vary by more than sampling error."
                           " The pooled sd then understates the uncertainty of the pooled F_H.")
    else:
        v["hom_caveat"] = ""
    return v


def fill_prose(r: dict, template=TEMPLATE, out=FILLED) -> str:
    with open(template) as f:
        text = f.read()
    v = prose_values(r)
    keys = set(re.findall(r"\{([A-Za-z0-9_]+)\}", text))
    missing = keys - set(v)
    if missing:
        raise KeyError("no value for placeholders %s" % sorted(missing))
    filled = re.sub(r"\{([A-Za-z0-9_]+)\}", lambda m: v[m.group(1)], text)
    if not r["final"]:
        filled = ("<!-- PARTIAL: not all cells hold %d runs. Do not splice. -->\n" % EXPECTED_RUNS) + filled
    with open(out, "w") as f:
        f.write(filled)
    return filled


def main():
    r = compute()
    pd.set_option("display.width", 220)
    cells = r["cells"]
    print("runs found per cell:")
    for c in cells.itertuples():
        print("  %-17s %s  %d of %d  (%s)" % (c.file, c.pipeline, c.runs, EXPECTED_RUNS,
                                              getattr(c, "run_labels", "")))
    if len(r["pending"]):
        print("pending or failed payloads (excluded):")
        print(r["pending"].to_string(index=False))
    print()
    print(r["per_run"].to_string(index=False))
    print()
    cols = ["file", "pipeline", "runs", "shots", "n_2q", "F_H", "sd", "sd_method", "F_min", "F_max",
            "chi2", "dof", "p_hom", "p_hom_mc", "Q_FH", "p_Q_FH"]
    print(cells[cols].to_string(index=False))
    print()
    print(r["pairs"].to_string(index=False))
    print()
    print("slope a = %.4e per ZZ gate" % SLOPE)
    print("HQC estimate, completed H2-2E jobs: %d jobs, %.1f HQC = %.2f %% of %.0f"
          % (r["jobs_completed"], r["hqc_completed"], r["hqc_pct"], QUOTA_HQC))
    print("HQC estimate, all submitted H2-2E jobs: %d jobs, %.1f HQC = %.2f %% of %.0f"
          % (r["jobs_submitted"], r["hqc_submitted"], r["hqc_pct_submitted"], QUOTA_HQC))
    for w in r["warnings"]:
        print("WARNING:", w)
    if os.path.exists(TEMPLATE):
        fill_prose(r)
        print("wrote", os.path.relpath(FILLED, ROOT))
    if r["final"]:
        print("STATUS: final (%d runs in all four cells)" % EXPECTED_RUNS)
    else:
        print("STATUS: PARTIAL, not final (runs per cell %s, %d required)"
              % (list(cells.runs), EXPECTED_RUNS))


if __name__ == "__main__":
    main()
