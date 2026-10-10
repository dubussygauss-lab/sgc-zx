"""Family C: full equivalence check of the pytket-quantinuum level 3 output (L3).

L3 is the official pass
    QuantinuumBackend("H2-1", api_handler=QuantinuumAPIOffline())
        .get_compiled_circuit(c, optimisation_level=3)
as run by strong_baselines.compile_variant("L3", c).  This script checks, for
all 20 circuits of bench/family_C, that the L3 output equals its input as a
full 2^n x 2^n unitary up to global phase (no ancilla is assumed in |0>).

Compile step (one forked process per circuit, COMPILE_TIMEOUT s):
  the input is recompiled with strong_baselines.compile_variant("L3", .), its
  HQC is recomputed with strong_baselines.counts and compared with the L3 row
  of results/strong_baselines.csv, and it is exported as add_measure_all +
  hqslib1 QASM (maxwidth 64), the convention of results/compiled/P0, P2 and of
  equiv_psel4_C.py, so the measurement map carries the implicit qubit
  permutation.  If results/compiled/L3/<file> already exists with the same
  text it is left untouched ("stored file matches").  If it exists with
  different text it is replaced and the note says so.

Check step: equiv_psel4_C.miter_check(file, "L3"), i.e. the PyZX miter of
pipelines/equiv_family_C.py unchanged: measurements stripped and their map
applied as an output permutation (equiv_family_C.load / ops_to_graph), angles
snapped to the dyadic grid 2^-G with G = (largest dyadic exponent of the
input's angles) + 4, off-grid tolerance equiv_family_C.OFFGRID_TOL = 1e-6
half-turns, miter input ; adjoint(compiled) reduced with full_reduce, and
"proven" when only the 2n boundary vertices remain, joined by simple edges
input i -> output i.  Miter timeout TIMEOUT = 900 s, 2 workers, smallest
circuits first.  Verdicts:
  proven                 max snap <= 1e-9 half-turns
  proven-up-to-rounding  1e-9 < max snap <= OFFGRID_TOL
  not-provable-pyzx      off-grid angles (max snap > OFFGRID_TOL), PyZX not run.
                         The 64-random-basis-input check of
                         run_family_C.basis_check (same seed, tolerance 1e-8)
                         is run instead (method basis-spot-check).  It covers
                         64 of 2^n inputs and is not a proof.
  inconclusive           full_reduce did not reach the identity
  timeout                miter killed after TIMEOUT s
  not-compiled / not-run compile failure, or HQC differs from the CSV

Output: results/family_C_equivalence_L3.csv and
        results/family_C_equivalence_L3.md (also via --summary).
Usage:  python3 pipelines/equiv_L3_C.py [--workers 2] [--files a,b]
        python3 pipelines/equiv_L3_C.py --summary
Test:   python3 -m pytest pipelines/test_equiv_L3_C.py
"""

import argparse
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import equiv_psel4_C as Q  # noqa: E402  (imports run_family_C, strong_baselines, equiv_family_C in the right order)
from pytket.qasm import circuit_from_qasm, circuit_to_qasm_str  # noqa: E402

E, SB, RF, C = Q.E, Q.SB, Q.RF, Q.C
ROOT = E.ROOT
BENCH = E.BENCH
STRONG = os.path.join(ROOT, "results", "strong_baselines.csv")
OUTCSV = os.path.join(ROOT, "results", "family_C_equivalence_L3.csv")
OUTMD = os.path.join(ROOT, "results", "family_C_equivalence_L3.md")
VARIANT = "L3"
TIMEOUT = 900.0
COMPILE_TIMEOUT = 900.0
HQC_TOL = 1e-6
COLS = ["file", "n", "hqc", "n_2q", "hqc_csv", "hqc_L2_csv", "hqc_match", "method",
        "verdict", "max_snap_halfturns", "grid", "seconds", "t_compile", "stored",
        "spot_check", "spot_check_dev", "notes"]


def targets() -> pd.DataFrame:
    """One row per family C circuit: n, L2 and L3 HQC from strong_baselines.csv."""
    sb = pd.read_csv(STRONG)
    sb = sb[(sb.family == "C") & sb.variant.isin(["L2", "L3"])]
    assert not sb.duplicated(["file", "variant"]).any()
    assert sb.status.str.startswith("ok").all()
    w = sb.pivot(index="file", columns="variant", values="hqc")
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    assert sorted(man.file) == sorted(w.index), "manifest and strong_baselines disagree"
    out = pd.DataFrame({"file": man.file, "n": man.n_qubits.astype(int)})
    out["hqc_L3"] = [float(w.at[f, "L3"]) for f in out.file]
    out["hqc_L2"] = [float(w.at[f, "L2"]) for f in out.file]
    return out


# ------------------------------------------------------------------ compile

def _compile_child(file, conn):
    try:
        path = Q.compiled_path(VARIANT, file)
        t0 = time.perf_counter()
        circ = circuit_from_qasm(os.path.join(BENCH, file))
        comp, _ = SB.compile_variant(VARIANT, circ)
        tc = time.perf_counter() - t0
        cnt = SB.counts(comp)
        assert cnt["native"], cnt["non_native_ops"]
        qasm = circuit_to_qasm_str(C.add_measure_all(comp), header="hqslib1", maxwidth=64)
        if os.path.exists(path):
            with open(path) as fh:
                old = fh.read()
            stored = "kept (matches)" if old == qasm else "replaced (differed)"
        else:
            stored = "new"
        if stored != "kept (matches)":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(qasm)
        # read back: the stored file must give the same counts
        u, _ = E.load(path)
        cnt2 = SB.counts(u)
        assert (cnt2["hqc"], cnt2["n_2q"]) == (cnt["hqc"], cnt["n_2q"]), (cnt, cnt2)
        conn.send(("ok", cnt["hqc"], cnt["n_2q"], tc, stored))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", None, None, None, f"{type(e).__name__}: {e}"[:300]))


# ----------------------------------------------------------------- driver

def run_one(row):
    f = row["file"]
    out = {"file": f, "n": row["n"], "hqc_csv": row["hqc_L3"], "hqc_L2_csv": row["hqc_L2"],
           "method": "pyzx-miter"}
    res, dt = Q._in_fork(_compile_child, (f,), COMPILE_TIMEOUT)
    if res is None or res[0] != "ok":
        out.update(verdict="not-compiled", t_compile=round(dt, 2),
                   notes="compile timeout" if res is None else res[4])
        return out
    _, hqc, n2q, tc, stored = res
    out.update(hqc=hqc, n_2q=n2q, t_compile=round(tc, 2), stored=stored,
               hqc_match=abs(hqc - row["hqc_L3"]) <= HQC_TOL)
    if not out["hqc_match"]:
        out.update(verdict="not-run", notes=f"recompiled HQC {hqc} != CSV {row['hqc_L3']}")
        return out
    m, dt = Q._in_fork(Q._miter_child, (f, VARIANT), TIMEOUT)
    out["seconds"] = round(dt, 2)
    if m is None:
        out.update(verdict="timeout", notes=f"killed after {TIMEOUT:.0f} s")
        return out
    out.update(verdict=m["verdict"], max_snap_halfturns=m["snap"], grid=m["grid"],
               notes=m["note"])
    if m["verdict"] == "inconclusive" and "off-grid" in m["note"]:
        out.update(verdict="not-provable-pyzx", method="basis-spot-check")
        b, _ = Q._in_fork(Q._basis_child, (f, VARIANT), TIMEOUT)
        out["spot_check"], out["spot_check_dev"] = ("timeout", None) if b is None else b
    return out


def run(files, workers):
    todo = targets()
    if files:
        todo = todo[todo.file.isin(files)]
    todo = todo.sort_values(["n", "file"])
    SB.backend()   # build once before forking
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for out in ex.map(run_one, todo.to_dict("records")):
            rows.append(out)
            print(f"{out['file']} hqc={out.get('hqc')} match={out.get('hqc_match')} "
                  f"{out['verdict']} {out.get('seconds')}s snap={out.get('max_snap_halfturns')} "
                  f"stored={out.get('stored')} spot={out.get('spot_check')} "
                  f"{out.get('notes', '')}", flush=True)
            # write after every circuit so a kill keeps the finished rows
            _save(rows, files)
    print(f"wrote {OUTCSV}")


def _save(rows, files):
    new = pd.DataFrame(rows).reindex(columns=COLS)
    if os.path.exists(OUTCSV):
        old = pd.read_csv(OUTCSV)
        old = old[~old.file.isin(new.file)]
        new = pd.concat([old, new], ignore_index=True)
    new = new.sort_values(["n", "file"]).reset_index(drop=True)
    new.to_csv(OUTCSV, index=False)


# ---------------------------------------------------------------- summary

def pct_saving(base, new):
    return 100.0 * (base - new) / base


def summary_facts():
    eq = pd.read_csv(OUTCSV)
    tg = targets().set_index("file")
    assert sorted(eq.file) == sorted(tg.index), "CSV must cover all 20 circuits"
    proven = eq.verdict == "proven"
    P = eq[proven]
    F = {"N": len(eq), "n_proven": int(proven.sum()),
         "n_proven_rounding": int((eq.verdict == "proven-up-to-rounding").sum()),
         "hqc_all_match": bool(eq.hqc_match.fillna(False).astype(bool).all()),
         "by_verdict": eq.verdict.value_counts().to_dict()}
    for key, sub in (("proven", P.file), ("all", eq.file)):
        l2 = float(sum(tg.at[f, "hqc_L2"] for f in sub))
        l3 = float(sum(tg.at[f, "hqc_L3"] for f in sub))
        F[f"L2_{key}"], F[f"L3_{key}"] = l2, l3
        F[f"saving_{key}"] = pct_saving(l2, l3) if l2 else float("nan")
    F["table"] = eq
    return F


def write_summary():
    F = summary_facts()
    T = F["table"]
    name = lambda f: f.replace(".qasm", "")  # noqa: E731

    def fs(x):
        return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3g}"

    def st(x):
        return "" if x is None or (isinstance(x, float) and math.isnan(x)) else str(x)

    unproven = T[T.verdict != "proven"]
    L = ["# Family C: equivalence of the pytket-quantinuum level 3 output (L3)", "",
         "Written by `python3 pipelines/equiv_L3_C.py --summary` from "
         "`results/family_C_equivalence_L3.csv` and `results/strong_baselines.csv`. "
         "Method in the docstring of `pipelines/equiv_L3_C.py`. "
         "Test: `pipelines/test_equiv_L3_C.py`.", "",
         "## Method", "",
         "- [F] Every family C circuit was recompiled with `strong_baselines.compile_variant(\"L3\")` "
         "(QuantinuumBackend(\"H2-1\", QuantinuumAPIOffline()).get_compiled_circuit(c, "
         "optimisation_level=3)). Recomputed HQC equals the L3 value of "
         f"`results/strong_baselines.csv` for every circuit: {F['hqc_all_match']}. "
         "Outputs are stored as `results/compiled/L3/<file>` (column `stored`).",
         "- [F] Check: the PyZX miter of `pipelines/equiv_family_C.py` via "
         "`equiv_psel4_C.miter_check` (measurement map applied as output permutation, dyadic "
         "snap to 2^-(G_in+4), off-grid tolerance 1e-6 half-turns, `full_reduce`, identity-wire "
         "test). It proves equality of the full 2^n x 2^n unitary up to global phase with no "
         "ancilla fixed. 900 s per circuit, 2 workers.",
         "- [F] Circuits with off-grid angles are not provable with this PyZX method. They get the "
         "64-random-basis-input check of `run_family_C.basis_check` (tolerance 1e-8), which is a "
         "spot check and not a proof.", "",
         "## Result", "",
         f"- [F] L3 outputs proven equal to their input: {F['n_proven']} of {F['N']}.",
         f"- [F] Proven only up to angle rounding: {F['n_proven_rounding']}.",
         "- [F] Not proven: " + ("; ".join(
             f"{name(r.file)} ({r.verdict}"
             + (f", spot check {st(r.spot_check)}" if st(r.spot_check) else "") + ")"
             for r in unproven.itertuples()) or "none") + ".",
         f"- [F] Over the {F['n_proven']} proven circuits: total HQC L2 {F['L2_proven']:.1f}, "
         f"L3 {F['L3_proven']:.1f}, saving of L3 against L2 {F['saving_proven']:.2f} %.",
         f"- [F] Over all {F['N']} circuits: total HQC L2 {F['L2_all']:.1f}, "
         f"L3 {F['L3_all']:.1f}, saving of L3 against L2 {F['saving_all']:.2f} %.",
         "- [F] HQC values are those of `results/strong_baselines.csv` (variants L2, L3). "
         "Saving = (L2 - L3) / L2.", "",
         "## Per circuit", "",
         "| circuit | n | HQC L2 | HQC L3 | verdict | method | max snap (half-turns) | grid "
         "| time (s) | spot check (dev) | stored file | notes |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in T.itertuples():
        spot = st(r.spot_check)
        if spot and st(r.spot_check_dev):
            spot += f" ({fs(r.spot_check_dev)})"
        L.append(f"| {name(r.file)} | {r.n} | {r.hqc_L2_csv:.1f} | {r.hqc_csv:.1f} | "
                 f"{r.verdict} | {r.method} | {fs(r.max_snap_halfturns)} | {st(r.grid)} | "
                 f"{fs(r.seconds)} | {spot} | {st(r.stored)} | "
                 f"{st(r.notes).replace('|', '/')} |")
    L.append("")
    with open(OUTMD, "w") as fh:
        fh.write("\n".join(L))
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if not a.summary:
        files = [f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f]
        run(files, a.workers)
    if len(pd.read_csv(OUTCSV)) < len(targets()):
        print("CSV incomplete; summary not written")
        return
    F = write_summary()
    print({k: F[k] for k in F if k != "table"})


if __name__ == "__main__":
    main()
