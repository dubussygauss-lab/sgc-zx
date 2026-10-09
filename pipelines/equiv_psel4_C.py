"""Family C: full equivalence check of the PSEL4 picks that are L3 or P2L3.

PSEL4 keeps, per circuit, the lowest-HQC candidate among P0, P2, L3, P2L3.
Ties go to the lower n_2q, then to the order P0, L3, P2, P2L3.
  P0, P2      : value/family_C_selector.csv (hqc_P0, hqc_P2, n2q_P0, n2q_P2)
  L3, P2L3    : results/strong_baselines.csv (family C rows, columns hqc, n_2q)

For every pick that is L3 or P2L3 the compiled circuit is rebuilt with
strong_baselines.compile_variant (same backend QuantinuumBackend("H2-1",
QuantinuumAPIOffline()), optimisation_level=3, same zx_teleport_reduce for
P2L3), its HQC is recomputed with strong_baselines.counts and compared with the
CSV value, and it is written as results/compiled/<variant>/<file>
(add_measure_all + hqslib1 QASM, maxwidth 64, the convention of
results/compiled/P0 and P2, so the measurement map carries the implicit qubit
permutation).

The check is the PyZX miter of pipelines/equiv_family_C.py, reusing its
functions (load, input_grid, to_ops, ops_to_graph, miter_is_identity) and its
tolerance OFFGRID_TOL: angles are snapped to the dyadic grid 2^-G with
G = (largest dyadic exponent of the input's angles) + 4, the miter
input ; adjoint(compiled) is reduced with full_reduce, and the result is
"proven" when only the 2n boundary vertices remain, joined by simple edges
input i -> output i.  This proves equality of the full 2^n x 2^n unitaries up to
global phase (no ancilla is fixed).  Verdicts:
  proven                 max snap <= 1e-9 half-turns
  proven-up-to-rounding  1e-9 < max snap <= OFFGRID_TOL
  equal-up-to-rounding   P2L3 only: the exact check failed, but succeeds when the
                         input angles are rounded as pyzx's QASM parser rounds
                         them (Fraction.limit_denominator(2^20)), as in
                         equiv_family_C.pyzx_check for P2
  inconclusive           off-grid angles (max snap > OFFGRID_TOL; PyZX not run)
                         or full_reduce did not reach the identity
  timeout                miter killed after TIMEOUT s
Off-grid circuits get the 64-random-basis-input check of
run_family_C.basis_check (same seed, tolerance 1e-8) as a spot check.  That
check covers 64 of 2^n inputs and is not a proof; for branching circuits
(QFT-based) it reports "unchecked-branching".

Every compile and every check runs in its own forked process.  Compile timeout
COMPILE_TIMEOUT s, miter timeout TIMEOUT = 300 s, basis check timeout 300 s.

Output: results/family_C_equivalence_psel4.csv and
        results/family_C_equivalence_psel4.md (also via --summary).
Usage:  python3 pipelines/equiv_psel4_C.py [--workers 2] [--files a,b] [--reuse]
        python3 pipelines/equiv_psel4_C.py --summary
--reuse skips recompilation when results/compiled/<variant>/<file> exists (the
HQC check is still made on the stored file).
"""

import argparse
import math
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_family_C as RF  # noqa: E402  (sparse basis check; sets C.to_qasm wide)
import strong_baselines as SB  # noqa: E402  (imported after RF: its C._tket_to_pyzx wins)
import equiv_family_C as E  # noqa: E402
import compile as C  # noqa: E402
from pytket.qasm import circuit_from_qasm, circuit_to_qasm_str  # noqa: E402

ROOT = E.ROOT
BENCH = E.BENCH
COMPILED = E.COMPILED
SELECTOR = os.path.join(ROOT, "value", "family_C_selector.csv")
STRONG = os.path.join(ROOT, "results", "strong_baselines.csv")
OLD_EQ = os.path.join(ROOT, "results", "family_C_equivalence.csv")
OUTCSV = os.path.join(ROOT, "results", "family_C_equivalence_psel4.csv")
OUTMD = os.path.join(ROOT, "results", "family_C_equivalence_psel4.md")
TIMEOUT = 300.0
COMPILE_TIMEOUT = 600.0
ORDER = ["P0", "L3", "P2", "P2L3"]
HQC_TOL = 1e-6
COLS = ["file", "n", "pick", "hqc", "n_2q", "hqc_csv", "hqc_match", "method", "verdict",
        "max_snap_halfturns", "grid", "seconds", "t_compile", "spot_check",
        "spot_check_dev", "notes"]


# ------------------------------------------------------------------ picks

def candidates() -> pd.DataFrame:
    """One row per (file, candidate) with hqc and n_2q."""
    sel = pd.read_csv(SELECTOR)
    sb = pd.read_csv(STRONG)
    sb = sb[(sb.family == "C") & sb.variant.isin(["L3", "P2L3"])]
    assert not sb.duplicated(["file", "variant"]).any()
    rows = []
    for r in sel.itertuples():
        rows.append((r.file, "P0", float(r.hqc_P0), int(r.n2q_P0)))
        rows.append((r.file, "P2", float(r.hqc_P2), int(r.n2q_P2)))
    for r in sb.itertuples():
        assert r.status.startswith("ok"), (r.file, r.variant, r.status)
        rows.append((r.file, r.variant, float(r.hqc), int(r.n_2q)))
    return pd.DataFrame(rows, columns=["file", "cand", "hqc", "n_2q"])


def psel4_picks() -> pd.DataFrame:
    cand = candidates()
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    out = []
    for f, n in zip(man.file, man.n_qubits):
        c = cand[cand.file == f]
        assert sorted(c.cand) == sorted(ORDER), (f, list(c.cand))
        best = min(c.itertuples(),
                   key=lambda r: (round(r.hqc, 6), r.n_2q, ORDER.index(r.cand)))
        row = {"file": f, "n": int(n), "pick": best.cand, "hqc": best.hqc,
               "n_2q": best.n_2q}
        for r in c.itertuples():
            row[f"hqc_{r.cand}"] = r.hqc
        out.append(row)
    return pd.DataFrame(out)


# ------------------------------------------------------- compile and export

def compiled_path(variant, file):
    return os.path.join(COMPILED, variant, file)


def _compile_child(file, variant, reuse, conn):
    try:
        path = compiled_path(variant, file)
        t0 = time.perf_counter()
        if reuse and os.path.exists(path):
            u, _ = E.load(path)
            cnt = SB.counts(u)
            conn.send(("ok", cnt["hqc"], cnt["n_2q"], 0.0, "reused stored QASM"))
            return
        circ = circuit_from_qasm(os.path.join(BENCH, file))
        comp, _ = SB.compile_variant(variant, circ)
        cnt = SB.counts(comp)
        assert cnt["native"], cnt["non_native_ops"]
        qasm = circuit_to_qasm_str(C.add_measure_all(comp), header="hqslib1", maxwidth=64)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(qasm)
        # read back: the stored file must give the same counts
        u, _ = E.load(path)
        cnt2 = SB.counts(u)
        assert (cnt2["hqc"], cnt2["n_2q"]) == (cnt["hqc"], cnt["n_2q"]), (cnt, cnt2)
        conn.send(("ok", cnt["hqc"], cnt["n_2q"], time.perf_counter() - t0, ""))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", None, None, None, f"{type(e).__name__}: {e}"[:300]))


def _in_fork(target, args, timeout):
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=target, args=(*args, child))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(timeout):
        res = parent.recv()
    else:
        res = None
        p.kill()
    p.join()
    return res, time.perf_counter() - t0


# ------------------------------------------------------------------ miter

def miter_check(file, variant):
    """-> dict(verdict, snap, grid, note).  equiv_family_C.pyzx_check with the
    compiled side read from results/compiled/<variant>/<file>, returning the
    snap as a number."""
    G = E.input_grid(file)
    grid = lambda x: Fraction(round(x * 2 ** G), 2 ** G)  # noqa: E731
    uA, pA = E.load(E.side_path("input", file))
    uB, pB = E.load(compiled_path(variant, file))
    n = uA.n_qubits
    assert uB.n_qubits == n
    opsA, eA = E.to_ops(uA, grid)
    opsB, eB = E.to_ops(uB, grid)
    snap = max(eA, eB)
    res = {"snap": snap, "grid": f"2^-{G}"}
    if snap > E.OFFGRID_TOL:
        res.update(verdict="inconclusive",
                   note=f"off-grid angles: max distance to 2^-{G} grid {snap:.3g} half-turns; "
                        f"PyZX needs exact phases, not run")
        return res
    ok, nv, ne = E.miter_is_identity(E.ops_to_graph(opsA, n, pA), E.ops_to_graph(opsB, n, pB))
    if ok:
        if snap > 1e-9:
            res.update(verdict="proven-up-to-rounding",
                       note=f"max snap {snap:.3g} half-turns ({snap * math.pi:.3g} rad)")
        else:
            res.update(verdict="proven", note="")
        return res
    note = f"full_reduce left {nv} vertices, {ne} edges (2n={2 * n})"
    if variant == "P2L3":   # same retry as equiv_family_C.pyzx_check for P2
        rnd = lambda x: Fraction(x).limit_denominator(E.PYZX_MAXDEN)  # noqa: E731
        ops_in, e_in = E.to_ops(uA, rnd)
        if e_in > 0:
            ops2, e2 = E.to_ops(uB, lambda x: Fraction(x).limit_denominator(E.PYZX_MAXDEN * 64))
            ok2, nv2, _ = E.miter_is_identity(E.ops_to_graph(ops_in, n, pA),
                                              E.ops_to_graph(ops2, n, pB))
            if ok2:
                res.update(verdict="equal-up-to-rounding",
                           note=f"exact check: {note}; with input angles rounded as pyzx "
                                f"parses them: proven; max input angle error "
                                f"{e_in * math.pi:.3g} rad, compiled snap {e2:.3g} half-turns")
                return res
            note += f"; rounded-input retry left {nv2} vertices"
    res.update(verdict="inconclusive", note=note)
    return res


def _miter_child(file, variant, conn):
    try:
        conn.send(miter_check(file, variant))
    except Exception as e:  # noqa: BLE001
        conn.send({"verdict": "error", "snap": None, "grid": "",
                   "note": f"{type(e).__name__}: {e}"[:300]})


def _basis_child(file, variant, conn):
    try:
        dev, _ = RF.basis_check(file, variant)
        conn.send(("pass" if dev <= RF.TOL else "FAIL", dev))
    except RF.TooManyAmplitudes:
        conn.send(("unchecked-branching", None))
    except Exception as e:  # noqa: BLE001
        conn.send((f"error {type(e).__name__}: {e}"[:200], None))


# ----------------------------------------------------------------- driver

def run_one(row, reuse):
    f, v = row["file"], row["pick"]
    out = {"file": f, "n": row["n"], "pick": v, "hqc_csv": row["hqc"], "method": "pyzx-miter"}
    res, dt = _in_fork(_compile_child, (f, v, reuse), COMPILE_TIMEOUT)
    if res is None or res[0] != "ok":
        out.update(verdict="not-compiled", t_compile=round(dt, 2),
                   notes="compile timeout" if res is None else res[4])
        return out
    _, hqc, n2q, tc, cnote = res
    out.update(hqc=hqc, n_2q=n2q, t_compile=round(tc, 2),
               hqc_match=abs(hqc - row["hqc"]) <= HQC_TOL)
    if not out["hqc_match"]:
        out.update(verdict="not-run", notes=f"recompiled HQC {hqc} != CSV {row['hqc']}")
        return out
    m, dt = _in_fork(_miter_child, (f, v), TIMEOUT)
    out["seconds"] = round(dt, 2)
    if m is None:
        out.update(verdict="timeout", notes=f"killed after {TIMEOUT:.0f} s")
        return out
    out.update(verdict=m["verdict"], max_snap_halfturns=m["snap"], grid=m["grid"],
               notes="; ".join(x for x in (m["note"], cnote) if x))
    if m["verdict"] != "proven" and "off-grid" in m["note"]:
        b, _ = _in_fork(_basis_child, (f, v), TIMEOUT)
        out["spot_check"], out["spot_check_dev"] = ("timeout", None) if b is None else b
    return out


def run(files, workers, reuse):
    picks = psel4_picks()
    todo = picks[picks.pick.isin(["L3", "P2L3"])]
    if files:
        todo = todo[todo.file.isin(files)]
    todo = todo.sort_values("n", ascending=False)
    SB.backend()   # build once before forking
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for out in ex.map(lambda r: run_one(r, reuse), todo.to_dict("records")):
            rows.append(out)
            print(f"{out['file']} {out['pick']} hqc={out.get('hqc')} "
                  f"match={out.get('hqc_match')} {out['verdict']} "
                  f"{out.get('seconds')}s snap={out.get('max_snap_halfturns')} "
                  f"spot={out.get('spot_check')} {out.get('notes', '')}", flush=True)
    new = pd.DataFrame(rows).reindex(columns=COLS)
    if os.path.exists(OUTCSV) and files:
        old = pd.read_csv(OUTCSV)
        old = old[~old.file.isin(new.file)]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(OUTCSV, index=False)
    print(f"wrote {OUTCSV}")


# ---------------------------------------------------------------- summary

def summary_facts():
    picks = psel4_picks()
    eq = pd.read_csv(OUTCSV)
    old = pd.read_csv(OLD_EQ)
    old = old[old.method == "pyzx"]
    oldv = {(f, c): (v, s, nt) for f, c, v, s, nt in
            zip(old.file, old.comparison, old.verdict, old.seconds, old.notes)}
    newv = {r.file: r for r in eq.itertuples()}
    sel = pd.read_csv(SELECTOR).set_index("file")
    table = []
    for p in picks.itertuples():
        if p.pick in ("P0", "P2"):
            v, s, nt = oldv.get((p.file, p.pick), ("not run", None, ""))
            snap = E._snap(nt)
            table.append(dict(file=p.file, n=p.n, pick=p.pick, hqc=p.hqc,
                              source="family_C_equivalence.csv", verdict=v,
                              snap=snap, seconds=s,
                              spot="" if v == "proven" else
                              f"{sel.at[p.file, 'check_' + p.pick]} (run_family_C)",
                              note=nt))
        else:
            r = newv.get(p.file)
            if r is None:
                table.append(dict(file=p.file, n=p.n, pick=p.pick, hqc=p.hqc,
                                  source="this run", verdict="not run", snap=None,
                                  seconds=None, spot="", note=""))
                continue
            assert r.pick == p.pick
            spot = "" if pd.isna(r.spot_check) else str(r.spot_check)
            table.append(dict(file=p.file, n=p.n, pick=p.pick, hqc=p.hqc,
                              source="this run", verdict=r.verdict,
                              snap=None if pd.isna(r.max_snap_halfturns) else r.max_snap_halfturns,
                              seconds=r.seconds, spot=spot,
                              note="" if pd.isna(r.notes) else r.notes,
                              hqc_match=r.hqc_match))
    T = pd.DataFrame(table)
    proven = T.verdict.isin(["proven"])
    F = {"N": len(T), "n_proven": int(proven.sum()),
         "n_proven_rounding": int(T.verdict.isin(["proven-up-to-rounding",
                                                    "equal-up-to-rounding"]).sum()),
         "by_pick": T.groupby("pick").size().to_dict(),
         "proven_by_pick": T[proven].groupby("pick").size().to_dict(),
         "unproven": T[~proven][["file", "pick", "verdict", "spot", "note"]],
         "n_new": int(T.source.eq("this run").sum()),
         "n_new_proven": int((T.source.eq("this run") & proven).sum()),
         "hqc_all_match": bool(eq.hqc_match.fillna(False).astype(bool).all()),
         "table": T}
    return F


def write_summary():
    F = summary_facts()
    T = F["table"]
    name = lambda f: f.replace(".qasm", "")  # noqa: E731
    fs = lambda x: "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3g}"  # noqa: E731
    L = ["# Family C: equivalence of the PSEL4 picks", "",
         "Written by `python3 pipelines/equiv_psel4_C.py --summary` from "
         "`results/family_C_equivalence_psel4.csv` (L3 / P2L3 picks, this run), "
         "`results/family_C_equivalence.csv` (P0 / P2 picks, PyZX rows), "
         "`value/family_C_selector.csv` and `results/strong_baselines.csv`. "
         "Method in the docstring of `pipelines/equiv_psel4_C.py`. "
         "Test: `pipelines/test_equiv_psel4_C.py`.", "",
         "## Selector", "",
         "- [F] PSEL4 keeps the lowest HQC of P0, P2, L3, P2L3 per circuit. Ties go to the lower "
         "n_2q, then to the order P0, L3, P2, P2L3.",
         "- [F] Picks: " + ", ".join(f"{k} {v}" for k, v in sorted(F["by_pick"].items()))
         + f" (of {F['N']}).", "",
         "## Method", "",
         "- [F] L3 and P2L3 picks were recompiled with `strong_baselines.compile_variant` "
         "(QuantinuumBackend(\"H2-1\", QuantinuumAPIOffline()), optimisation_level=3). "
         "The recomputed HQC equals the `results/strong_baselines.csv` value for every "
         f"recompiled circuit: {F['hqc_all_match']}. Outputs are stored as "
         "`results/compiled/{L3,P2L3}/<file>`.",
         "- [F] Check: the PyZX miter of `pipelines/equiv_family_C.py` (dyadic snap to "
         "2^-(G_in+4), off-grid tolerance 1e-6 half-turns, `full_reduce`, identity-wire test), "
         "full 2^n x 2^n unitary up to global phase, 300 s per circuit, 2 workers. "
         "Off-grid circuits get the 64-random-basis-input check of `run_family_C.basis_check` "
         "as a spot check, which is not a proof.",
         "- [F] P0 and P2 picks are taken from the existing PyZX rows of "
         "`results/family_C_equivalence.csv`; nothing was rerun for them.", "",
         "## Result", "",
         f"- [F] PSEL4 output proven equal to its input: {F['n_proven']} of {F['N']} circuits.",
         f"- [F] L3 / P2L3 picks proven in this run: {F['n_new_proven']} of {F['n_new']}.",
         f"- [F] Proven only up to angle rounding: {F['n_proven_rounding']}.",
         "- [F] Not proven: " + ("; ".join(
             f"{name(r.file)} ({r.pick}, {r.verdict}"
             + (f", spot check {r.spot}" if r.spot else "") + ")"
             for r in F["unproven"].itertuples()) or "none") + ".", "",
         "## Per circuit", "",
         "| circuit | n | PSEL4 pick | HQC | method / source | verdict | max snap (half-turns) "
         "| time (s) | spot check | notes |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in T.itertuples():
        L.append(f"| {name(r.file)} | {r.n} | {r.pick} | {r.hqc:.1f} | pyzx miter, "
                 f"{r.source} | {r.verdict} | {fs(r.snap)} | {fs(r.seconds)} | {r.spot} | "
                 f"{str(r.note).replace('|', '/')} |")
    L.append("")
    with open(OUTMD, "w") as fh:
        fh.write("\n".join(L))
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if not a.summary:
        files = [f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f]
        run(files, a.workers, a.reuse)
    F = write_summary()
    print({k: F[k] for k in F if k not in ("table", "unproven")})
    print(F["unproven"].to_string())


if __name__ == "__main__":
    main()
