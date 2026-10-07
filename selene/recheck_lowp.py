"""Re-sample, with fresh seeds and 10x the shots, every noiseless run whose
pooled chi-square p-value is below 0.01, to separate a sampling fluctuation
from a wrong circuit.  Writes results/selene_recheck.txt.

    HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python3 selene/recheck_lowp.py
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_selene as RS  # noqa: E402

RS._unset_proxies()
from pytket.qasm import circuit_from_qasm  # noqa: E402

SHOTS = 20000
SEEDS = (777, 778)


def main():
    nl = pd.read_csv(os.path.join(RS.RESULTS, "selene_noiseless.csv"))
    low = nl[(nl["support_size"] <= RS.CHI2_MAX_SUPPORT) & (nl["chi2_p_pooled"] < 0.01)]
    out = [f"recheck of {len(low)} runs with pooled chi2 p < 0.01: {SHOTS} shots, seeds {SEEDS}"]
    for _, r in low.iterrows():
        pipe, f, n = r["pipeline"], r["file"], int(r["n"])
        circ = circuit_from_qasm(os.path.join(RS.COMPILED, pipe, f))
        p = RS.exact_probs(pipe, f)
        runner = RS.build_runner(circ, f"re_{pipe}_{f[:-5]}")
        out.append(f"{pipe}/{f}: original 2000 shots TVD {r['TVD']:.4f} (expected {r['TVD_expected_exact']:.4f}), pooled p {r['chi2_p_pooled']:.4f}")
        for seed in SEEDS:
            c = RS.sample(runner, n, SHOTS, seed)
            q = c / SHOTS
            pv, lowc, outside, pp = RS.chi2_pvalue(c, p, SHOTS)
            out.append(f"    seed {seed}: TVD {RS.tvd(p, q):.4f} (expected {RS.expected_tvd_exact(p, SHOTS):.4f}), "
                       f"TVD/expected {RS.tvd(p, q) / RS.expected_tvd_exact(p, SHOTS):.2f}, pooled p {pp:.3f}, raw p {pv:.3f}, cells<5 {lowc}, outside support {outside}")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(RS.RESULTS, "selene_recheck.txt"), "w") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main()
