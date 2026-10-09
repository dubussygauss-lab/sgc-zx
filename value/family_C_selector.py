"""Family C (application-scale circuits, 20 to 56 qubits): pass selector PSEL
count-only.  Reads results/family_C_counts.csv (pipelines/run_family_C.py)
and bench/family_C/manifest.csv, writes value/family_C_selector.csv (one row
per circuit), value/family_C_selector_apps.csv (one row per application and
one 'all' row) and value/family_C_selector.md.

PSEL rule (pipelines/pass_select.py and value/selector_ledger.py): keep the
lower HQC at 1000 shots of P0 (pytket L2) and P2 (PyZX teleport_reduce + L2),
HQC compared after rounding to 6 decimals, tie -> lower n_2q, then P0.
Count-only: no exactness check inside the selector (n > 20, "ok-unchecked");
the separate 64-input basis check of run_family_C.py --check is reported in
columns check_P0 / check_P2.

Columns
  hqc_P0, hqc_P2, hqc_PSEL   HQC at 1000 shots (compile.hqc, measure-all)
  saved_hqc = hqc_P0 - hqc_PSEL, saved_pct = 100 * saved_hqc / hqc_P0
  shots_P0, shots_PSEL       shots affordable at a 10,000 HQC budget with at most
                             10,000 shots per job and a 5 HQC fee per job
                             (value/usecase.shots_capped, same rule as
                             value/value_by_application.shots_affordable_capped)
  extra_shots = shots_PSEL - shots_P0 (per circuit only)
  pick                       P0 or P2
  n2q_P0, n2q_PSEL, d_n2q = n2q_PSEL - n2q_P0
  t_written                  T-count of the input circuit as written
  t_zx_P2                    T-count after the ZX stage of P2 (pyzx count)
  t_saved_zx = t_written - t_zx_P2 (what the ZX stage removes)
  t_saved_PSEL = t_saved_zx if pick == P2 else 0
Per-application rows sum the circuit rows (saved_pct recomputed from the
sums). They carry no shot column: a sum of shots of different circuits has no
single physical meaning.

Usage: python3 value/family_C_selector.py
"""
from pathlib import Path

import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ROOT / "results" / "family_C_counts.csv"
MANIFEST = ROOT / "bench" / "family_C" / "manifest.csv"
OUT = ROOT / "value"
SHOTS = 1000
DEC = 6
sys.path.insert(0, str(ROOT / "value"))
from usecase import BUDGET, JOB_FEE, JOB_SHOT_CAP, shots_capped  # noqa: E402


def select(hqc0, hqc2, n0, n2):
    h0, h2 = round(hqc0, DEC), round(hqc2, DEC)
    if h2 < h0:
        return "P2"
    if h2 > h0:
        return "P0"
    return "P2" if n2 < n0 else "P0"


def shots_affordable(hqc1000, budget=BUDGET):
    """Shots within `budget` HQC, at most JOB_SHOT_CAP per job, JOB_FEE per job."""
    return shots_capped(hqc1000, budget=budget)


def per_circuit():
    c = pd.read_csv(COUNTS)
    man = pd.read_csv(MANIFEST)
    assert set(c.pipeline) == {"P0", "P2"}
    assert c.status.str.startswith("ok").all(), c[~c.status.str.startswith("ok")]
    assert not c.duplicated(["file", "pipeline"]).any()
    p0 = c[c.pipeline == "P0"].set_index("file")
    p2 = c[c.pipeline == "P2"].set_index("file")
    assert set(p0.index) == set(p2.index) == set(man.file)
    rows = []
    for _, m in man.iterrows():
        f = m.file
        a, b = p0.loc[f], p2.loc[f]
        pick = select(a.hqc, b.hqc, a.n_2q, b.n_2q)
        s = b if pick == "P2" else a
        t_saved_zx = int(m.t_count_as_written - b.t_count_zx)
        r = {
            "file": f, "n_qubits": int(m.n_qubits), "application": m.application,
            "construction": m.construction,
            "hqc_P0": a.hqc, "hqc_P2": b.hqc, "hqc_PSEL": s.hqc, "pick": pick,
            "n2q_P0": int(a.n_2q), "n2q_P2": int(b.n_2q), "n2q_PSEL": int(s.n_2q),
            "depth2q_P0": int(a.depth_2q), "depth2q_PSEL": int(s.depth_2q),
            "n1q_P0": int(a.n_phasedx), "n1q_PSEL": int(s.n_phasedx),
            "t_written": int(m.t_count_as_written), "t_zx_P2": int(b.t_count_zx),
            "t_saved_zx": t_saved_zx,
            "t_saved_PSEL": t_saved_zx if pick == "P2" else 0,
            "wall_P0_s": a.t_wall, "wall_P2_s": b.t_wall,
            "check_P0": a.get("basis_check", ""), "check_P2": b.get("basis_check", ""),
            "pyzx_angle_err_rad": b.pyzx_angle_err,
        }
        r["saved_hqc"] = r["hqc_P0"] - r["hqc_PSEL"]
        r["saved_pct"] = 100 * r["saved_hqc"] / r["hqc_P0"]
        r["d_n2q"] = r["n2q_PSEL"] - r["n2q_P0"]
        r["shots_P0"] = shots_affordable(r["hqc_P0"])
        r["shots_PSEL"] = shots_affordable(r["hqc_PSEL"])
        r["extra_shots"] = r["shots_PSEL"] - r["shots_P0"]
        rows.append(r)
    return pd.DataFrame(rows).sort_values(["application", "n_qubits", "file"]).reset_index(drop=True)


def per_application(r):
    out = []
    groups = [(a, g) for a, g in r.groupby("application", sort=True)] + [("all", r)]
    for app, g in groups:
        d = {"application": app, "n_circuits": len(g),
             "qubits": f"{g.n_qubits.min()}-{g.n_qubits.max()}",
             "hqc_P0": g.hqc_P0.sum(), "hqc_P2": g.hqc_P2.sum(), "hqc_PSEL": g.hqc_PSEL.sum(),
             "p2_picks": int((g.pick == "P2").sum()),
             "n2q_P0": int(g.n2q_P0.sum()), "n2q_PSEL": int(g.n2q_PSEL.sum()),
             "t_written": int(g.t_written.sum()), "t_saved_PSEL": int(g.t_saved_PSEL.sum()),
             "n_checked_both": int(((g.check_P0 == "pass") & (g.check_P2 == "pass")).sum())}
        d["saved_hqc"] = d["hqc_P0"] - d["hqc_PSEL"]
        d["saved_pct"] = 100 * d["saved_hqc"] / d["hqc_P0"]
        d["d_n2q"] = d["n2q_PSEL"] - d["n2q_P0"]
        out.append(d)
    return pd.DataFrame(out)


def fmt(x, nd=1):
    if isinstance(x, (float, np.floating)):
        return f"{x:.{nd}f}"
    return str(x)


def md_table(df, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return lines


def main():
    r = per_circuit()
    s = per_application(r)
    r.to_csv(OUT / "family_C_selector.csv", index=False)
    s.to_csv(OUT / "family_C_selector_apps.csv", index=False)
    md = ["# Family C: pass selector PSEL on application-scale circuits (count-only)", "",
          "`[F]` Generated by value/family_C_selector.py from results/family_C_counts.csv. "
          "HQC at 1000 shots. PSEL = lower HQC of P0 (pytket L2) and P2 "
          "(PyZX teleport_reduce + L2), tie to lower n_2q then P0. "
          f"Extra shots at a {BUDGET:,} HQC budget per circuit, at most {JOB_SHOT_CAP:,} shots per job "
          f"and a {JOB_FEE} HQC fee per job (value/usecase.shots_capped). "
          "Shots are given per circuit only and are not summed across circuits. "
          "T saved = T-count as written minus T-count after the P2 ZX stage, counted only when PSEL picks P2.", "",
          "`[F]` Check columns: 'pass' = compiled circuit agrees with the input circuit on 64 random "
          "basis inputs up to one global phase (sparse simulation, run_family_C.py --check). "
          "'unchecked-branching' = simulation exceeded 2^20 amplitudes, no check. "
          "A pass covers 64 of 2^n inputs and is not a proof of equivalence.", "",
          "## Per application", ""]
    md += md_table(s, ["application", "n_circuits", "qubits", "hqc_P0", "hqc_P2", "hqc_PSEL",
                       "saved_hqc", "saved_pct", "p2_picks", "d_n2q",
                       "t_saved_PSEL", "n_checked_both"])
    man = pd.read_csv(MANIFEST).set_index("file")
    cont = r.file.map(man.continuous_angles).astype(bool)
    md += [""]
    for lab, g in [("without continuous angles", r[~cont]), ("with continuous angles", r[cont])]:
        line = (f"`[F]` Circuits {lab}: {len(g)} with {int((g.pick == 'P2').sum())} P2 picks. "
                f"HQC P0 {g.hqc_P0.sum():.1f} and HQC PSEL {g.hqc_PSEL.sum():.1f}. "
                f"Saved {g.saved_hqc.sum():.1f} HQC or {100 * g.saved_hqc.sum() / g.hqc_P0.sum():.2f} %.")
        if lab.startswith("with "):
            line += " The saving comes from " + " and ".join(g[g.saved_hqc > 0].file) + " only."
        md += [line, ""]
    md += ["## Per circuit", ""]
    md += md_table(r, ["file", "n_qubits", "application", "hqc_P0", "hqc_P2", "hqc_PSEL",
                       "pick", "saved_hqc", "saved_pct", "shots_P0", "extra_shots", "n2q_P0", "n2q_PSEL",
                       "d_n2q", "t_written", "t_zx_P2", "t_saved_PSEL", "check_P0", "check_P2"])
    bad = r[r.pyzx_angle_err_rad > 0]
    if len(bad):
        md += ["", "`[F]` PyZX angle rounding (float to Fraction, max denominator 2^20) changes the "
               "P2 input of: " + ", ".join(f"{f} (max {e:.2e} rad per angle)"
                                         for f, e in zip(bad.file, bad.pyzx_angle_err_rad))
               + ". P2 output for these circuits is approximate at that level."]
    (OUT / "family_C_selector.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
