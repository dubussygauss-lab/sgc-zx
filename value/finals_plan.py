"""Pre-registered plan for H2 hardware in the Grand Finale.

Run: python3 value/finals_plan.py   (writes value/finals_plan.md)

Inputs
  * Table E3 (pooled H2-2E runs, 4000 shots per pipeline) from submit/h22e_pooled.compute().
  * Table E2 shots for a 2-sd resolution of the predicted gain from submit/h22e_stats.compute().
  * The compiled circuits results/compiled/{P0,P2}/{vbe_adder_3,grover_5}.qasm and the HQC formula
    pipelines/compile.py:hqc, 5 + (N_1q + 10 N_2q + 5 N_spam) C / 5000.

Rules (fixed before any hardware data exist)
  * The sd of F_H(P2) - F_H(P0) scales as 1 / sqrt(N) with N shots per pipeline, from the pooled sd at 4000.
  * Primary test, vbe_adder_3: shots per pipeline = the 2-sd shots of the MEASURED H2-2E gain,
    4000 (2 sd / dF)^2, rounded up to a multiple of ROUND. One-sided, alpha = ALPHA.
  * Secondary test, grover_5: shots per pipeline = the 2-sd shots of the MEASURED shortfall
    dF_pred - dF, rounded up the same way. One-sided, alpha = ALPHA. It does not enter the primary decision.
  * One job per (circuit, pipeline). HQC per job from the compiled circuit.
"""
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "submit"))

import h22e_pooled  # noqa: E402
import h22e_stats  # noqa: E402
import common  # noqa: E402
from scipy import stats  # noqa: E402

OUT = ROOT / "value" / "finals_plan.md"
ALPHA = 0.05
Z_CRIT = float(stats.norm.isf(ALPHA))  # one-sided critical value, 1.645
POWER_TARGET = 0.80
ROUND = 100
POOLED_SHOTS = 4000
QUOTA_HQC = h22e_stats.QUOTA_HQC
MAX_SHOTS_PER_JOB = 10000      # docs/platform_notes.md section 3.4, H2 hardware user guide
MAX_HQC_PER_SHOT = 50.0        # same source
PRIMARY = "vbe_adder_3.qasm"
SECONDARY = "grover_5.qasm"


def round_up(n: float, step: int = ROUND) -> int:
    return int(math.ceil(n / step) * step)


def shots_for(sd_ref: float, n_ref: int, effect: float, k: float) -> float:
    """Shots per pipeline at which k sd of the difference equals effect, sd ~ 1/sqrt(N)."""
    return n_ref * (k * sd_ref / effect) ** 2


def sd_at(sd_ref: float, n_ref: int, n: int) -> float:
    return sd_ref * math.sqrt(n_ref / n)


def power(effect: float, sd: float, z_crit: float = Z_CRIT) -> float:
    return float(stats.norm.cdf(effect / sd - z_crit))


def job_hqc(pipeline: str, file: str, shots: int) -> dict:
    circ = common.load_compiled(pipeline, file)
    from pytket import OpType
    n1 = circ.n_gates_of_type(OpType.PhasedX)
    n2 = circ.n_gates_of_type(OpType.ZZPhase) + circ.n_gates_of_type(OpType.ZZMax)
    hqc = common.hqc_estimate(circ, shots)
    per_shot = (hqc - 5) / shots
    return {"file": file, "pipeline": pipeline, "shots": shots, "n_1q": n1, "n_2q": n2,
            "n_qubits": circ.n_qubits, "hqc": hqc, "hqc_per_shot": per_shot,
            "hqc_1000": common.hqc_estimate(circ, 1000)}


def compute() -> dict:
    pooled = h22e_pooled.compute()
    pairs = pooled["pairs"].set_index("file")
    single = h22e_stats.compute()["pairs"].set_index("file")
    out = {"hqc_used": pooled["hqc_completed"], "quota": QUOTA_HQC}
    out["hqc_left"] = QUOTA_HQC - pooled["hqc_completed"]
    out["shots_2sd_pred_E2"] = {f: int(single.loc[f, "shots_2sd"]) for f in single.index}

    p = pairs.loc[PRIMARY]
    n_ref = int(p.shots_P0)
    assert n_ref == int(p.shots_P2) == POOLED_SHOTS
    prim = {"file": PRIMARY, "dF": float(p.dF), "sd": float(p.sd), "z": float(p.z),
            "dF_pred": float(p.dF_pred), "dN_2q": int(p.dN_2q)}
    prim["shots_2sd_raw"] = shots_for(prim["sd"], n_ref, prim["dF"], 2.0)
    prim["shots"] = round_up(prim["shots_2sd_raw"])
    prim["sd_planned"] = sd_at(prim["sd"], n_ref, prim["shots"])
    prim["z_expected"] = prim["dF"] / prim["sd_planned"]
    prim["power"] = power(prim["dF"], prim["sd_planned"])
    prim["shots_80_raw"] = shots_for(prim["sd"], n_ref, prim["dF"], Z_CRIT + stats.norm.isf(1 - POWER_TARGET))
    prim["mde"] = Z_CRIT * prim["sd_planned"]        # smallest difference that confirms

    s = pairs.loc[SECONDARY]
    sec = {"file": SECONDARY, "dF": float(s.dF), "sd": float(s.sd), "z": float(s.z),
           "dF_pred": float(s.dF_pred), "dN_2q": int(s.dN_2q), "z_vs_pred": float(s.z_vs_pred)}
    sec["shortfall"] = sec["dF_pred"] - sec["dF"]
    sec["shots_2sd_raw"] = shots_for(sec["sd"], n_ref, sec["shortfall"], 2.0)
    sec["shots"] = round_up(sec["shots_2sd_raw"])
    sec["sd_planned"] = sd_at(sec["sd"], n_ref, sec["shots"])
    sec["z_short_expected"] = sec["shortfall"] / sec["sd_planned"]
    sec["power_short"] = power(sec["shortfall"], sec["sd_planned"])
    sec["z_pred_expected"] = sec["dF_pred"] / sec["sd_planned"]

    jobs = []
    for t in (prim, sec):
        for pipe in ("P0", "P2"):
            j = job_hqc(pipe, t["file"], t["shots"])
            assert j["shots"] <= MAX_SHOTS_PER_JOB and j["hqc_per_shot"] <= MAX_HQC_PER_SHOT
            jobs.append(j)
    out.update(primary=prim, secondary=sec, jobs=jobs)
    out["hqc_primary"] = sum(j["hqc"] for j in jobs if j["file"] == PRIMARY)
    out["hqc_secondary"] = sum(j["hqc"] for j in jobs if j["file"] == SECONDARY)
    out["hqc_total"] = out["hqc_primary"] + out["hqc_secondary"]
    # The stored H2-2E estimates at 1000 shots (Table E2) must equal the formula on the same files.
    e2 = {("vbe_adder_3.qasm", "P0"): 151.6, ("vbe_adder_3.qasm", "P2"): 119.0,
          ("grover_5.qasm", "P0"): 565.6, ("grover_5.qasm", "P2"): 528.2}
    for j in jobs:
        assert abs(j["hqc_1000"] - e2[(j["file"], j["pipeline"])]) < 1e-6, j
    return out


def _name(f: str) -> str:
    return f[:-5]


def render(r: dict) -> str:
    P, S = r["primary"], r["secondary"]
    L = []
    L.append("# Plan for H2 hardware in the finals\n")
    L.append("Generated by `value/finals_plan.py` from `submit/h22e_pooled.py` (Table E3), "
             "`submit/h22e_stats.py` (Table E2) and the compiled circuits in `results/compiled/`. "
             "Tests: `value/test_finals_plan.py`.\n")
    L.append("## Inputs\n")
    L.append(f"- [F] {_name(PRIMARY)} at {POOLED_SHOTS} shots per pipeline on H2-2E: F_H(P2) - F_H(P0) "
             f"= {P['dF']:+.4f} with sd {P['sd']:.4f} and z {P['z']:+.2f}. The slope prediction is {P['dF_pred']:.4f}.")
    L.append(f"- [F] {_name(SECONDARY)} at {POOLED_SHOTS} shots per pipeline on H2-2E: F_H(P2) - F_H(P0) "
             f"= {S['dF']:+.4f} with sd {S['sd']:.4f} and z {S['z']:+.2f}. The slope prediction is "
             f"{S['dF_pred']:.4f}. The measured value lies {abs(S['z_vs_pred']):.2f} sd below it.")
    e2 = r["shots_2sd_pred_E2"]
    L.append(f"- [F] Shots per pipeline for a 2-sd resolution of the predicted gain from the single runs of "
             f"Table E2: {e2['vbe_adder_3.qasm']} on vbe_adder_3, {e2['hwb6.qasm']} on hwb6 and "
             f"{e2['grover_5.qasm']} on grover_5.")
    L.append(f"- [F] H2-2E HQC used by the 18 completed jobs {r['hqc_used']:.1f} of {r['quota']:.0f}. "
             f"The remainder is {r['hqc_left']:.1f} HQC. All values are formula estimates.")
    L.append("")
    L.append("## Primary test\n")
    L.append(f"- [O] Circuit {_name(PRIMARY)} under P0 and P2. PSEL picks P2 on this circuit.")
    L.append(f"- [F] Shots per pipeline for 2 sd at the measured gain: 4000 x (2 x {P['sd']:.6f} / "
             f"{P['dF']:.6f})^2 = {P['shots_2sd_raw']:.0f}. Rounded up to a multiple of {ROUND}: {P['shots']}.")
    L.append(f"- [F] At {P['shots']} shots the sd of the difference is {P['sd_planned']:.4f}. "
             f"The expected z at the measured gain is {P['z_expected']:.2f}.")
    L.append(f"- [O] The test is one-sided with alpha {ALPHA}. The alternative is F_H(P2) > F_H(P0) "
             f"because P2 has {P['dN_2q']} fewer ZZPhase gates. The critical z is {Z_CRIT:.3f}.")
    L.append(f"- [F] Power at the measured gain is {P['power']:.2f}. The smallest difference that "
             f"confirms is {P['mde']:.4f}. Power {POWER_TARGET:.2f} would need "
             f"{P['shots_80_raw']:.0f} shots per pipeline.")
    L.append(f"- [O] Confirms: z >= {Z_CRIT:.3f}. Refutes: z <= -{Z_CRIT:.3f}. Any other z is reported "
             "as not resolved and no hardware claim is made.")
    L.append("")
    L.append("## Secondary test\n")
    L.append(f"- [O] Circuit {_name(SECONDARY)} under P0 and P2. It tests the shortfall against the slope "
             "model and does not enter the primary decision.")
    L.append(f"- [F] Measured shortfall on H2-2E: {S['dF_pred']:.6f} - {S['dF']:.6f} = {S['shortfall']:.6f} "
             f"with sd {S['sd']:.6f}. "
             f"Shots per pipeline for 2 sd at this shortfall: {S['shots_2sd_raw']:.0f}. "
             f"Rounded up: {S['shots']}.")
    L.append(f"- [F] At {S['shots']} shots the sd of the difference is {S['sd_planned']:.4f}. "
             f"The expected z of the shortfall is {S['z_short_expected']:.2f} and its power is "
             f"{S['power_short']:.2f}.")
    L.append(f"- [O] The prediction on hardware is F_H(P0) (exp({S['dN_2q']} a) - 1) with a = "
             f"{h22e_stats.SLOPE_LOG:.4e} and F_H(P0) measured on hardware. The statistic is "
             "z_short = (prediction - measured difference) / sd. One-sided, alpha "
             f"{ALPHA}.")
    L.append(f"- [O] Model refuted on grover_5: z_short >= {Z_CRIT:.3f}. Model consistent: "
             f"z_short < {Z_CRIT:.3f} and z >= {Z_CRIT:.3f} for the gain. Any other outcome is not resolved.")
    L.append("")
    L.append("## HQC cost\n")
    L.append("| circuit | pipeline | shots | N_1q | N_2q | qubits | HQC per shot | HQC |")
    L.append("|---|---|---|---|---|---|---|---|")
    for j in r["jobs"]:
        L.append(f"| {_name(j['file'])} | {j['pipeline']} | {j['shots']} | {j['n_1q']} | {j['n_2q']} | "
                 f"{j['n_qubits']} | {j['hqc_per_shot']:.4f} | {j['hqc']:.1f} |")
    L.append("")
    L.append(f"- [F] Primary {r['hqc_primary']:.1f} HQC, secondary {r['hqc_secondary']:.1f} HQC, "
             f"total {r['hqc_total']:.1f} HQC in four jobs.")
    L.append(f"- [F] Each job stays under the H2 limits of {MAX_SHOTS_PER_JOB} shots per job and "
             f"{MAX_HQC_PER_SHOT:.0f} HQC per shot.")
    L.append("- [O] The HQC values assume that H2 hardware charges by the formula of "
             "`docs/platform_notes.md` section 3.4.")
    L.append("")
    return "\n".join(L)


def main():
    r = compute()
    OUT.write_text(render(r))
    print(OUT.read_text())


if __name__ == "__main__":
    main()
