"""Depolarising Selene run (gates_meas_init variant) on the full noiseless set:
every family-A circuit with n <= 10 and every B1 circuit with n <= 10,
pipelines P0, P2 first and then P1, 2000 shots, seeded as run_selene.py
(seed_for(pipe, file, "depol")), 2 processes.

Same columns as results/selene_depolarizing.csv.  The density-matrix proxy
comparison (F_H_proxy_*, z, agree_2sd, TVD_selene_vs_proxy,
TVD_expected_sampling) is computed only where results/family_*_proxy_h22e.csv
has a row for (file, pipeline); otherwise those columns are NaN (agree_2sd -1).

Output: results/selene_depolarizing_full.csv (rewritten after every finished
row, so a partial file is usable if the run is cut short).

Usage (proxy variables must be unset):
    HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= \
        python3 selene/run_selene_depol_full.py [--procs 2] [--shots 2000]
"""
import argparse
import csv
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_selene as RS  # noqa: E402

OUT = os.path.join(RS.RESULTS, "selene_depolarizing_full.csv")
VARIANT = "gates_meas_init"
PIPE_ORDER = ["P0", "P2", "P1"]


def proxy_keys():
    keys = set()
    for name in ("family_A_proxy_h22e.csv", "family_B1_proxy_h22e.csv"):
        with open(os.path.join(RS.RESULTS, name)) as fh:
            for row in csv.DictReader(fh):
                keys.add((row["file"], row["pipeline"]))
    return keys


def job(args):
    family, f, model, n, pipe, shots, idx, has_proxy = args
    RS._unset_proxies()
    from pytket.qasm import circuit_from_qasm
    from selene_sim import DepolarizingErrorModel
    t0 = time.perf_counter()
    circ = circuit_from_qasm(os.path.join(RS.COMPILED, pipe, f))
    assert circ.n_qubits == n, (f, circ.n_qubits, n)
    ref = RS.reference_probs(family, f)
    st = RS.circuit_stats(circ)
    runner = RS.build_runner(circ, f"d{idx}")
    seed = RS.seed_for(pipe, f, "depol")
    params = RS.DEPOL_VARIANTS[VARIANT]
    em = DepolarizingErrorModel(random_seed=seed, **params)
    t1 = time.perf_counter()
    counts = RS.sample(runner, n, shots, seed, error_model=em)
    t2 = time.perf_counter()
    q = counts / shots
    counts0 = RS.sample(runner, n, shots, seed)
    q0 = counts0 / shots
    fh_sel = RS.hellinger_fidelity(ref, q)
    rng = np.random.default_rng(seed)
    fh_mc_ideal = np.array([RS.hellinger_fidelity(ref, rng.multinomial(shots, ref) / shots) for _ in range(RS.BOOT)])
    nan = float("nan")
    if has_proxy:
        pn = RS.proxy_noisy_probs(family, f, pipe)
        fh_mc = np.array([RS.hellinger_fidelity(ref, rng.multinomial(shots, pn) / shots) for _ in range(RS.BOOT)])
        e, sd = float(fh_mc.mean()), float(fh_mc.std(ddof=1))
        z = (fh_sel - e) / sd if sd > 0 else nan
        px = dict(F_H_proxy_exact=RS.hellinger_fidelity(ref, pn),
                  F_H_proxy_sampled_mean=e, F_H_proxy_sampled_sd=sd,
                  z=z, agree_2sd=int(abs(z) <= 2) if not math.isnan(z) else -1,
                  TVD_selene_vs_proxy=RS.tvd(pn, q),
                  TVD_expected_sampling=RS.expected_tvd_exact(pn, shots))
    else:
        px = dict(F_H_proxy_exact=nan, F_H_proxy_sampled_mean=nan, F_H_proxy_sampled_sd=nan,
                  z=nan, agree_2sd=-1, TVD_selene_vs_proxy=nan, TVD_expected_sampling=nan)
    return dict(family=family, file=f, model=model, n=n, pipeline=pipe, variant=VARIANT, **st,
                shots=shots, seed=seed, support_size=int((ref > RS.SUPPORT_TOL).sum()),
                p_1q=params["p_1q"], p_2q=params["p_2q"],
                p_meas=params.get("p_meas", 0.0), p_init=params.get("p_init", 0.0),
                F_H_selene_depol=fh_sel,
                F_H_selene_noiseless_sameseed=RS.hellinger_fidelity(ref, q0),
                F_H_proxy_exact=px["F_H_proxy_exact"],
                F_H_proxy_sampled_mean=px["F_H_proxy_sampled_mean"],
                F_H_proxy_sampled_sd=px["F_H_proxy_sampled_sd"],
                F_H_ideal_sampled_mean=float(fh_mc_ideal.mean()),
                z=px["z"], agree_2sd=px["agree_2sd"],
                TVD_selene_vs_proxy=px["TVD_selene_vs_proxy"], TVD_selene_vs_ideal=RS.tvd(ref, q),
                TVD_expected_sampling=px["TVD_expected_sampling"],
                t_run_depol=t2 - t1, t_total=time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--shots", type=int, default=RS.SHOTS)
    ap.add_argument("--pipelines", default=",".join(PIPE_ORDER))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    RS._unset_proxies()
    circuits = RS.list_circuits()
    pk = proxy_keys()
    jobs = []
    for pipe in a.pipelines.split(","):
        for fam, f, model, n in circuits:
            jobs.append((fam, f, model, n, pipe, a.shots, len(jobs), (f, pipe) in pk))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(circuits)} circuits; {len(jobs)} runs x {a.shots} shots, {a.procs} processes, "
          f"{sum(j[-1] for j in jobs)} with proxy row", flush=True)
    t0 = time.perf_counter()
    rows = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.procs) as pool:
        for r in pool.imap(job, jobs, chunksize=1):
            rows.append(r)
            RS.write_csv(OUT, rows)
            if len(rows) % 20 == 0 or len(rows) == len(jobs):
                print(f"{len(rows)}/{len(jobs)} done, {time.perf_counter() - t0:.0f} s", flush=True)
    print(f"done in {time.perf_counter() - t0:.1f} s; wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
