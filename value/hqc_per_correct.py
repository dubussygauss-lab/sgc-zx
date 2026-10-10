"""HQC per correct output on the H2-2E emulator runs: level-2 baseline P0 against the cheaper alternative.

Inputs (all under results/emulator/)
  nexus_H2-2E, _r2, _r3, _r4      vbe_adder_3, hwb6, grover_5   P0 vs P2
  nexus_H2-2E_famC                 vbe_adder_7 (all-zero input)  P0 vs P2
  nexus_H2-2E_famC_nz              vbe_adder_7_nz                P0 vs L3
  nexus_H2-2E_famC_multi           cdkm_adder_10_i1..3           P0 vs L3
                                   modadd_2n_10_i1..3            P0 vs P2L3
  Each payload <run>/<pipeline>/<file>.json carries counts, shots, hqc_estimate, F_H.

Ideal output (repository code only)
  B1 circuits      submit/common.reference_probs("B1", file) (P0ref compilation, exact_probs)
  vbe_adder_7      submit/common.reference_probs("C", file) (bench/sv.py on the written circuit)
  vbe_adder_7_nz   submit/h22e_famC_nz.expected_bits()
  famC_multi       submit/h22e_multi_run.expected_bits(circuit, a, b) for the drawn inputs
  A circuit enters only if its ideal distribution is a single bitstring. Then p = count of that
  bitstring / shots, checked against the stored F_H to 1e-9. grover_5 is excluded when its ideal
  distribution has more than one outcome (no unique marked item).

Statistics per (circuit, pipeline), pooled over repeats / inputs
  S shots, K correct, H = sum hqc_estimate, C = H / K (reported per 1000 correct outputs).
  z         pooled two-proportion statistic of p_alt - p_P0.
  R         C_alt / C_P0; 95 % interval by the delta method on log R with
            var(log p) = (1 - p) / (S p) per arm (H fixed), checked by a parametric
            bootstrap K* ~ Binomial(S, p_hat) per arm, 10,000 resamples, seed 20261010.
  pooled R  (sum H_alt / sum K_alt) / (sum H_P0 / sum K_P0) over all pairs.

Run from the repository root:  python3 value/hqc_per_correct.py
Writes value/hqc_per_correct.csv and value/hqc_per_correct.md.
"""

import glob
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "submit"))
import common  # noqa: E402
import h22e_famC_nz  # noqa: E402
import h22e_multi_run  # noqa: E402

EMU = ROOT / "results" / "emulator"
OUT_CSV = ROOT / "value" / "hqc_per_correct.csv"
OUT_MD = ROOT / "value" / "hqc_per_correct.md"
SEED = 20261010
N_BOOT = 10000
Z95 = 1.959963984540054
TOL = 1e-9

# (circuit, runs, P0 baseline, alternative)
PAIRS = [
    ("vbe_adder_3", ("nexus_H2-2E", "nexus_H2-2E_r2", "nexus_H2-2E_r3", "nexus_H2-2E_r4"), "P0", "P2"),
    ("hwb6", ("nexus_H2-2E",), "P0", "P2"),
    ("grover_5", ("nexus_H2-2E", "nexus_H2-2E_r2", "nexus_H2-2E_r3", "nexus_H2-2E_r4"), "P0", "P2"),
    ("vbe_adder_7", ("nexus_H2-2E_famC",), "P0", "P2"),
    ("vbe_adder_7_nz", ("nexus_H2-2E_famC_nz",), "P0", "L3"),
    ("cdkm_adder_10", ("nexus_H2-2E_famC_multi",), "P0", "L3"),
    ("modadd_2n_10", ("nexus_H2-2E_famC_multi",), "P0", "P2L3"),
]
B1 = {"vbe_adder_3", "hwb6", "grover_5"}


def circuit_of(file: str) -> str:
    return re.sub(r"_i\d+$", "", file[:-5] if file.endswith(".qasm") else file)


def ideal(file: str) -> dict:
    """{'bits': str or None, 'support': int, 'p_max': float, 'source': str} for one payload file."""
    c = circuit_of(file)
    if c in B1 or c == "vbe_adder_7":
        fam = "B1" if c in B1 else "C"
        p = common.reference_probs(fam, file)
        n = int(round(math.log2(len(p))))
        nz = np.flatnonzero(p > TOL)
        bits = format(int(nz[0]), "0%db" % n) if len(nz) == 1 else None
        return dict(bits=bits, support=len(nz), p_max=float(p.max()),
                    source="common.reference_probs(%r)" % fam)
    if c == "vbe_adder_7_nz":
        e = h22e_famC_nz.expected_bits()
        assert e == h22e_famC_nz.EXPECTED
        return dict(bits=e, support=1, p_max=1.0, source="h22e_famC_nz.expected_bits")
    for cc, k, a, b, f in h22e_multi_run.programs():
        if f == file:
            return dict(bits=h22e_multi_run.expected_bits(cc, a, b), support=1, p_max=1.0,
                        source="h22e_multi_run.expected_bits")
    raise KeyError(file)


def load_payloads() -> pd.DataFrame:
    rows, cache = [], {}
    for path in sorted(glob.glob(str(EMU / "nexus_H2-2E*" / "*" / "*.json"))):
        run, pipe = Path(path).parts[-3], Path(path).parts[-2]
        with open(path) as fh:
            d = json.load(fh)
        file = d["file"]
        if file not in cache:
            cache[file] = ideal(file)
        idl = cache[file]
        counts = {k.replace(" ", ""): v for k, v in d["counts"].items()}
        assert sum(counts.values()) == d["shots"], path
        k = counts.get(idl["bits"], 0) if idl["bits"] else None
        rows.append(dict(run=run, pipeline=pipe, file=file, circuit=circuit_of(file), shots=int(d["shots"]),
                         K=k, hqc=float(d["hqc_estimate"]), F_H=float(d["F_H"]), ideal_bits=idl["bits"],
                         ideal_support=idl["support"], ideal_pmax=idl["p_max"], ideal_source=idl["source"]))
    df = pd.DataFrame(rows)
    single = df.ideal_bits.notna()
    df.loc[single, "p_counts"] = df.loc[single, "K"] / df.loc[single, "shots"]
    df.loc[single, "absdiff_FH"] = (df.loc[single, "p_counts"] - df.loc[single, "F_H"]).abs()
    return df


def delta_se(S0, K0, S1, K1):
    """Standard error of log R by the delta method, HQC held fixed."""
    p0, p1 = K0 / S0, K1 / S1
    se = math.sqrt((1 - p0) / (S0 * p0) + (1 - p1) / (S1 * p1))
    return se


def compute() -> dict:
    df = load_payloads()
    used = df[df.ideal_bits.notna()]
    assert (used.absdiff_FH <= TOL).all(), used[used.absdiff_FH > TOL]
    rng = np.random.default_rng(SEED)
    out, excluded, boot_all = [], [], []
    for circ, runs, base, alt in PAIRS:
        sub = df[(df.circuit == circ) & df.run.isin(runs)]
        assert set(sub.pipeline) == {base, alt}, (circ, set(sub.pipeline))
        if sub.ideal_bits.isna().any():
            excluded.append(dict(circuit=circ, runs=len(runs), support=int(sub.ideal_support.iloc[0]),
                                 p_max=float(sub.ideal_pmax.iloc[0]),
                                 hqc_ratio=sub[sub.pipeline == alt].hqc.sum() / sub[sub.pipeline == base].hqc.sum()))
            continue
        a0, a1 = sub[sub.pipeline == base], sub[sub.pipeline == alt]
        S0, K0, H0 = int(a0.shots.sum()), int(a0.K.sum()), float(a0.hqc.sum())
        S1, K1, H1 = int(a1.shots.sum()), int(a1.K.sum()), float(a1.hqc.sum())
        assert S0 == S1 and len(a0) == len(a1)
        p0, p1 = K0 / S0, K1 / S1
        pp = (K0 + K1) / (S0 + S1)
        z = (p1 - p0) / math.sqrt(pp * (1 - pp) * (1 / S0 + 1 / S1))
        C0, C1 = H0 / K0, H1 / K1
        R = C1 / C0
        se = delta_se(S0, K0, S1, K1)
        k0b, k1b = rng.binomial(S0, p0, N_BOOT), rng.binomial(S1, p1, N_BOOT)
        boot_all.append((H0, H1, k0b, k1b))
        Rb = (H1 / k1b) / (H0 / k0b)
        out.append(dict(circuit=circ, runs="+".join(r.replace("nexus_", "") for r in runs), n_jobs_per_arm=len(a0),
                        alt=alt, shots_per_arm=S0, K_P0=K0, K_alt=K1, p_P0=p0, p_alt=p1, z=z,
                        hqc_P0=H0, hqc_alt=H1, hqc_ratio=H1 / H0,
                        hqc_per_1000_correct_P0=1000 * C0, hqc_per_1000_correct_alt=1000 * C1, R=R,
                        R_lo_delta=R * math.exp(-Z95 * se), R_hi_delta=R * math.exp(Z95 * se),
                        R_lo_boot=float(np.quantile(Rb, 0.025)), R_hi_boot=float(np.quantile(Rb, 0.975))))
    T = pd.DataFrame(out)
    sH0, sK0, sH1, sK1 = T.hqc_P0.sum(), T.K_P0.sum(), T.hqc_alt.sum(), T.K_alt.sum()
    Rpool = (sH1 / sK1) / (sH0 / sK0)
    Rpb = (sH1 / sum(b[3] for b in boot_all)) / (sH0 / sum(b[2] for b in boot_all))
    head = dict(n_pairs=len(T), n_alt_cheaper=int((T.R < 1).sum()),
                n_upper_delta_below_1=int((T.R_hi_delta < 1).sum()),
                n_upper_boot_below_1=int((T.R_hi_boot < 1).sum()),
                R_cdkm=float(T.set_index("circuit").loc["cdkm_adder_10", "R"]),
                R_pooled=Rpool, R_pooled_lo_boot=float(np.quantile(Rpb, 0.025)),
                R_pooled_hi_boot=float(np.quantile(Rpb, 0.975)),
                sum_H_P0=sH0, sum_K_P0=int(sK0), sum_H_alt=sH1, sum_K_alt=int(sK1),
                n_payloads=len(df), n_payloads_used=len(used), max_absdiff_FH=float(used.absdiff_FH.max()))
    return dict(df=df, T=T, excluded=excluded, head=head)


def render_md(r: dict) -> str:
    T, h = r["T"], r["head"]
    L = ["# HQC per correct output on the H2-2E emulator", "",
         "`[F]` Source: every H2-2E payload under `results/emulator/nexus_H2-2E*/` (%d payloads, %d used). "
         "Script: `value/hqc_per_correct.py`. HQC is the formula estimate `hqc_estimate` stored with each job, "
         "not a billed amount. All runs are on the H2-2E emulator, not hardware." % (h["n_payloads"], h["n_payloads_used"]),
         "",
         "`[F]` Success probability p = count of the ideal bitstring / shots. The ideal bitstring comes from the "
         "repository code (`common.reference_probs`, `h22e_famC_nz.expected_bits`, `h22e_multi_run.expected_bits`). "
         "On every used payload p equals the stored F_H (max |p - F_H| = %.1e)." % h["max_absdiff_FH"],
         "",
         "`[F]` Pooled per circuit and pipeline over repeats or inputs. Cost per correct output C = sum HQC / sum correct. "
         "R = C_alt / C_P0. The interval is the delta method on log R. The bootstrap column is a parametric "
         "bootstrap (10,000 resamples, seed %d). z is the pooled two-proportion statistic of p_alt - p_P0." % SEED,
         "",
         "| Circuit | Runs | Alt | Shots per arm | p_P0 | p_alt | z | HQC per 1000 correct, P0 | HQC per 1000 correct, alt | R | 95 % interval (delta) | 95 % interval (bootstrap) |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for t in T.itertuples():
        L.append("| %s | %s | %s | %d | %.4f | %.4f | %+.2f | %.1f | %.1f | %.4f | [%.4f, %.4f] | [%.4f, %.4f] |" % (
            t.circuit, t.runs, t.alt, t.shots_per_arm, t.p_P0, t.p_alt, t.z, t.hqc_per_1000_correct_P0,
            t.hqc_per_1000_correct_alt, t.R, t.R_lo_delta, t.R_hi_delta, t.R_lo_boot, t.R_hi_boot))
    L += ["", "## Headline", ""]
    L.append("- `[F]` The alternative costs fewer HQC per correct output than P0 (R < 1) in %d of %d pairs."
             % (h["n_alt_cheaper"], h["n_pairs"]))
    L.append("- `[F]` The upper 95 %% bound of R is below 1 in %d of %d pairs by the delta method and in %d of %d by the bootstrap."
             % (h["n_upper_delta_below_1"], h["n_pairs"], h["n_upper_boot_below_1"], h["n_pairs"]))
    c = T.set_index("circuit").loc["cdkm_adder_10"]
    L.append("- `[F]` cdkm_adder_10 (L3, three inputs pooled): R = %.4f, delta interval [%.4f, %.4f]."
             % (c.R, c.R_lo_delta, c.R_hi_delta))
    L.append("- `[F]` In percent: cdkm_adder_10 needs %.1f %% fewer HQC per correct output than P0 (95 %% interval %.1f to %.1f %%)."
             % (100 * (1 - c.R), 100 * (1 - c.R_hi_delta), 100 * (1 - c.R_lo_delta)))
    L.append("- `[F]` Pooled over the %d pairs: R = (%.2f / %d) / (%.2f / %d) = %.4f, bootstrap interval [%.4f, %.4f]."
             % (h["n_pairs"], h["sum_H_alt"], h["sum_K_alt"], h["sum_H_P0"], h["sum_K_P0"], h["R_pooled"],
                h["R_pooled_lo_boot"], h["R_pooled_hi_boot"]))
    L.append("- `[F]` In percent: pooled over the %d pairs the alternative needs %.1f %% fewer HQC per correct output "
             "(bootstrap 95 %% interval %.1f to %.1f %%)."
             % (h["n_pairs"], 100 * (1 - h["R_pooled"]), 100 * (1 - h["R_pooled_hi_boot"]), 100 * (1 - h["R_pooled_lo_boot"])))
    sS0 = sS1 = int(r["T"].shots_per_arm.sum())
    hq = h["sum_H_alt"] / h["sum_H_P0"]
    if sS0 and sS1:
        acc = (h["sum_K_alt"] / sS1) / (h["sum_K_P0"] / sS0)
        L.append("- `[F]` Decomposition of the pooled R: HQC ratio alt / P0 = %.2f / %.2f = %.4f, divided by the accuracy ratio "
                 "p_alt / p_P0 = (%d / %d) / (%d / %d) = %.4f. The per-answer gain is the HQC saving with no average loss "
                 "of accuracy over the pairs." % (h["sum_H_alt"], h["sum_H_P0"], hq, h["sum_K_alt"], sS1, h["sum_K_P0"], sS0, acc))
    for e in r["excluded"]:
        L.append("- `[F]` %s is excluded. Its ideal distribution (`common.reference_probs`) has %d outcomes with "
                 "largest probability %.6f, so it has no unique marked item. Its HQC ratio alt / P0 over %d runs is %.4f."
                 % (e["circuit"], e["support"], e["p_max"], e["runs"], e["hqc_ratio"]))
    L.append("- `[O]` Pooling the three inputs of cdkm_adder_10 and modadd_2n_10 treats them as one binomial. "
             "The intervals ignore variation between inputs and between emulator runs.")
    return "\n".join(L) + "\n"


def main():
    r = compute()
    r["T"].to_csv(OUT_CSV, index=False, float_format="%.6g")
    OUT_MD.write_text(render_md(r))
    print(render_md(r))


if __name__ == "__main__":
    main()
