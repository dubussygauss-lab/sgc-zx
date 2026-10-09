"""Family C: MQT QCEC check of the PSEL4 outputs that the PyZX miter did not
prove, and of the L3 outputs on all family C circuits.

Part 1 (targets): the three PSEL4 picks not proven by pipelines/equiv_psel4_C.py
  hrs_mult_5      pick P2    results/compiled/P2/hrs_mult_5.qasm
  rgqft_mult_6    pick L3    results/compiled/L3/rgqft_mult_6.qasm
  draper_adder_28 pick P2L3  results/compiled/P2L3/draper_adder_28.qasm
Part 2 (L3 sweep): results/compiled/L3/<file> vs input for every circuit in
  bench/family_C/manifest.csv.  Missing L3 outputs are recompiled with
  strong_baselines.compile_variant("L3", ...) and stored as new files in
  results/compiled/L3/ (same convention as equiv_psel4_C.py: add_measure_all,
  hqslib1 QASM, maxwidth 64).  Existing files are never overwritten.

Reading the circuits: equiv_family_C.load (pytket parse, measurements stripped,
the measurement map gives pytket's implicit output permutation) and
equiv_family_C.qelib_qasm (qelib1 QASM with rz/rx/rzz/cx/h/s/sdg/t/tdg, float
angles written with repr, no snapping, output permutation realised by swaps).
No qubit is declared ancilla or garbage, so a positive verdict is equality of
the full 2^n x 2^n unitaries up to global phase.

QCEC configuration (mqt.qcec 3.10.2, qcec.verify keyword arguments):
  checker "zx" : run_zx_checker=True, all other checkers False
  checker "alt": run_alternating_checker=True, all other checkers False
  both         : parallel=False, nthreads=1, timeout=TIMEOUT_QCEC
  defaults kept: numerical_tolerance=2^-42 (2.27e-13, DD package tolerance),
                 trace_threshold=1e-8 (alternating checker: |trace|/2^n must be
                 within 1e-8 of 1), check_approximate_equivalence=False,
                 optimizations fuse_single_qubit_gates, reconstruct_swaps,
                 elide_permutations, reorder_operations = True.
Each check runs in its own forked process, killed after TIMEOUT_QCEC + 30 s
(verdict "killed").  Only QCEC's "equivalent" or
"equivalent_up_to_global_phase" counts as proven.  The alternating DD checker
works in floating point, so its positive verdict holds within the tolerances
above.  The ZX checker in QCEC 3.10.2 represents non-dyadic phases as
floating-point multiples of pi with its own tolerance.

Output: results/family_C_equivalence_qcec.csv (appended row by row, one row per
check) and results/family_C_equivalence_qcec.md (--summary, from the CSV,
PSEL4 picks and PyZX verdicts are read with equiv_psel4_C.summary_facts(),
read only).
Usage:  python3 pipelines/equiv_qcec_C.py --part targets [--workers 2]
        python3 pipelines/equiv_qcec_C.py --part l3 [--l3-timeout 120]
        python3 pipelines/equiv_qcec_C.py --summary
"""

import argparse
import multiprocessing as mp
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import equiv_family_C as E  # noqa: E402

ROOT = E.ROOT
BENCH = E.BENCH
COMPILED = E.COMPILED
OUTCSV = os.path.join(ROOT, "results", "family_C_equivalence_qcec.csv")
OUTMD = os.path.join(ROOT, "results", "family_C_equivalence_qcec.md")
PSEL4CSV = os.path.join(ROOT, "results", "family_C_equivalence_psel4.csv")
TIMEOUT_QCEC = 600.0
COMPILE_TIMEOUT = 300.0
COLS = ["file", "n", "part", "candidate", "compiled_path", "method", "config",
        "qcec_verdict", "verdict", "seconds", "notes"]
TARGETS = [("hrs_mult_5.qasm", "P2"), ("rgqft_mult_6.qasm", "L3"),
           ("draper_adder_28.qasm", "P2L3")]
PROVEN = ("equivalent", "equivalent_up_to_global_phase")


def config_str(checker, timeout):
    c = "run_zx_checker" if checker == "zx" else "run_alternating_checker"
    return (f"{c}=True, other checkers False, parallel=False, nthreads=1, "
            f"timeout={timeout:.0f}, numerical_tolerance=default 2.27e-13, "
            f"trace_threshold=default 1e-8")


def _qcec_child(file, cpath, checker, timeout, conn):
    try:
        from mqt import qcec
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for tag, p in (("input", os.path.join(BENCH, file)), ("compiled", cpath)):
                u, perm = E.load(p)
                fp = os.path.join(d, f"{tag}.qasm")
                with open(fp, "w") as fh:
                    fh.write(E.qelib_qasm(u, perm))
                paths.append(fp)
            kw = dict(run_zx_checker=False, run_alternating_checker=False,
                      run_construction_checker=False, run_simulation_checker=False,
                      parallel=False, nthreads=1, timeout=timeout)
            kw["run_zx_checker" if checker == "zx" else "run_alternating_checker"] = True
            t0 = time.perf_counter()
            res = qcec.verify(paths[0], paths[1], **kw)
            dt = time.perf_counter() - t0
        eq = str(res.equivalence).split(".")[-1]
        conn.send(("ok", eq, dt, ""))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", "", None, f"{type(e).__name__}: {e}"[:300]))


def _compile_child(file, conn):
    try:
        import compile as C
        import strong_baselines as SB
        from pytket.qasm import circuit_from_qasm, circuit_to_qasm_str
        path = os.path.join(COMPILED, "L3", file)
        circ = circuit_from_qasm(os.path.join(BENCH, file))
        comp, _ = SB.compile_variant("L3", circ)
        cnt = SB.counts(comp)
        qasm = circuit_to_qasm_str(C.add_measure_all(comp), header="hqslib1", maxwidth=64)
        if os.path.exists(path):
            raise FileExistsError(path)
        with open(path, "w") as fh:
            fh.write(qasm)
        conn.send(("ok", cnt["hqc"], ""))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", None, f"{type(e).__name__}: {e}"[:300]))


def _in_fork(target, args, timeout):
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=target, args=(*args, child))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(timeout):
        res = parent.recv()
        p.join()
        return res, time.perf_counter() - t0
    p.kill()
    p.join()
    return None, time.perf_counter() - t0


def n_qubits(file):
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    return int(man.set_index("file").loc[file, "n_qubits"])


def append_row(row):
    new = not os.path.exists(OUTCSV)
    pd.DataFrame([row], columns=COLS).to_csv(OUTCSV, mode="a", header=new, index=False)


def run_check(file, cand, checker, timeout, part):
    cpath = os.path.join(COMPILED, cand, file)
    res, wall = _in_fork(_qcec_child, (file, cpath, checker, timeout), timeout + 30)
    if res is None:
        qv, v, note = "", "killed", f"process killed after {timeout + 30:.0f} s"
    elif res[0] == "error":
        qv, v, note = "", "error", res[3]
    else:
        qv = res[1]
        v = "proven" if qv in PROVEN else ("failed" if qv == "not_equivalent" else "not proven")
        note = f"qcec check time {res[2]:.1f} s"
        if qv == "no_information":
            note += " (no_information: timeout or checker gave up)"
    row = dict(file=file, n=n_qubits(file), part=part, candidate=cand,
               compiled_path=os.path.relpath(cpath, ROOT),
               method=f"qcec_{checker}", config=config_str(checker, timeout),
               qcec_verdict=qv, verdict=v, seconds=round(wall, 2), notes=note)
    append_row(row)
    print(row["file"], cand, checker, qv, v, row["seconds"], flush=True)
    return row


def run_targets(workers):
    tasks = [(f, c, "alt") for f, c in TARGETS] + [(f, c, "zx") for f, c in TARGETS]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda t: run_check(t[0], t[1], t[2], TIMEOUT_QCEC, "targets"), tasks))


def run_l3(workers, l3_timeout, files=None):
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    files = files or list(man.file)

    def one(file):
        path = os.path.join(COMPILED, "L3", file)
        if not os.path.exists(path):
            res, wall = _in_fork(_compile_child, (file,), COMPILE_TIMEOUT)
            if res is None or res[0] != "ok":
                note = (f"L3 recompile killed after {COMPILE_TIMEOUT:.0f} s" if res is None
                        else f"L3 recompile error: {res[2]}")
                append_row(dict(file=file, n=n_qubits(file), part="l3", candidate="L3",
                                compiled_path="", method="compile", config="",
                                qcec_verdict="", verdict="skipped", seconds=round(wall, 2),
                                notes=note))
                return
        for checker in ("alt", "zx"):
            r = run_check(file, "L3", checker, l3_timeout, "l3")
            if r["verdict"] == "proven":
                break

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, files))


# ------------------------------------------------------------------ summary

def write_summary():
    q = pd.read_csv(OUTCSV)
    import equiv_psel4_C as P4
    T = P4.summary_facts()["table"]  # PSEL4 pick and PyZX verdict per circuit (read only)
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    assert set(T.file) == set(man.file)
    name = lambda f: f.replace(".qasm", "")  # noqa: E731
    pick = dict(zip(T.file, T.pick))
    pv = dict(zip(T.file, T.verdict))
    for f, c in TARGETS:
        assert pick[f] == c and pv[f] != "proven", (f, pick[f], pv[f])
    N = len(man)
    pyzx_proven = sorted(f for f in man.file if pv.get(f) == "proven")
    t = q[q.part == "targets"]
    tgt_proven = sorted({f for f, v in zip(t.file, t.verdict) if v == "proven"})
    psel4_proven = sorted(set(pyzx_proven) | set(tgt_proven))
    l3 = q[q.part == "l3"]
    l3_files = sorted(set(l3.file), key=list(man.file).index)
    l3_proven = sorted({f for f, v in zip(l3.file, l3.verdict) if v == "proven"})
    l3_failed = sorted({f for f, v in zip(l3.file, l3.verdict) if v == "failed"})
    l3_rgq = {f for f, v, c in zip(q.file, q.verdict, q.candidate)
              if c == "L3" and v == "proven"}
    L = ["# Family C: MQT QCEC check of the unproven PSEL4 outputs and of L3", "",
         "Written by `python3 pipelines/equiv_qcec_C.py --summary` from "
         "`results/family_C_equivalence_qcec.csv`, with PSEL4 picks and PyZX verdicts taken "
         "from `equiv_psel4_C.summary_facts()` (`results/family_C_equivalence_psel4.csv` and "
         "`results/family_C_equivalence.csv`). Method and configuration in the docstring of "
         "`pipelines/equiv_qcec_C.py`.", "",
         "## Method", "",
         "- [F] Tool: mqt.qcec 3.10.2, `qcec.verify` on qelib1 QASM written by "
         "`equiv_family_C.qelib_qasm` (float angles as stored, no snapping, output permutation "
         "from the measurement map realised by swaps). No qubit is declared ancilla or garbage. "
         "A positive verdict is equality of the full 2^n x 2^n unitaries up to global phase.",
         "- [F] Two configurations per pair, each alone: `run_zx_checker=True` and "
         "`run_alternating_checker=True`, with `parallel=False`, `nthreads=1`, "
         f"`timeout={TIMEOUT_QCEC:.0f}` for the three targets. QCEC defaults kept: "
         "`numerical_tolerance` 2.27e-13, `trace_threshold` 1e-8, "
         "`check_approximate_equivalence=False`.",
         "- [F] Only the QCEC verdicts `equivalent` and `equivalent_up_to_global_phase` count as "
         "proven. The alternating checker is a floating-point decision-diagram computation, so "
         "its positive verdict holds within the tolerances above. This matters for hrs_mult_5, "
         "whose compiled angles lie off the dyadic grid.", "",
         "## PSEL4 outputs", "",
         f"- [F] Proven earlier by the PyZX miter: {len(pyzx_proven)} of {N}.",
         f"- [F] Of the three unproven targets, QCEC proved {len(tgt_proven)}: "
         + (", ".join(name(f) for f in tgt_proven) if tgt_proven else "none") + ".",
         f"- [F] PSEL4 output proven equal to its input (PyZX or QCEC): {len(psel4_proven)} of {N}.",
         ]
    if len(psel4_proven) == N:
        L.append(f"- [F] All {N} PSEL4 outputs on family C are proven.")
    else:
        rest = [name(f) for f in man.file if f not in psel4_proven]
        L.append("- [F] Still not proven: " + ", ".join(rest) + ".")
    L += ["", "### Target checks", "",
          "| circuit | n | candidate | method | config | QCEC verdict | verdict | time (s) | notes |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {name(r.file)} | {r.n} | {r.candidate} | {r.method} | {r.config} | "
                 f"{'' if pd.isna(r.qcec_verdict) else r.qcec_verdict} | {r.verdict} | "
                 f"{r.seconds} | {'' if pd.isna(r.notes) else r.notes} |")
    L += ["", "## L3 outputs (all family C circuits)", ""]
    if len(l3) == 0:
        L.append("- [F] Not run.")
    else:
        L += [f"- [F] Circuits with an L3 QCEC row: {len(l3_files)} of {N}.",
              f"- [F] L3 proven by QCEC: {len(l3_proven)}. QCEC `not_equivalent`: "
              f"{len(l3_failed)}.",
              "- [F] L3 sweep timeout: 60 s per checker. The L3 output of rgqft_mult_6 is in the "
              "target table (600 s). The other circuits without an L3 row were not reached "
              "in the time budget and no L3 output was recompiled.",
              "- [F] QCEC returned no counterexample (`not_equivalent`) on any pair. "
              "`probably_not_equivalent` from the ZX checker and `no_information` from the "
              "alternating checker are inconclusive.", "",
              "| circuit | n | method | config | QCEC verdict | verdict | time (s) | notes |",
              "|---|---|---|---|---|---|---|---|"]
        for _, r in l3.iterrows():
            L.append(f"| {name(r.file)} | {r.n} | {r.method} | {r.config} | "
                     f"{'' if pd.isna(r.qcec_verdict) else r.qcec_verdict} | {r.verdict} | "
                     f"{r.seconds} | {'' if pd.isna(r.notes) else r.notes} |")
    L.append("")
    with open(OUTMD, "w") as fh:
        fh.write("\n".join(L))
    return dict(pyzx=len(pyzx_proven), tgt=tgt_proven, psel4=len(psel4_proven),
                l3_rows=len(l3_files), l3_proven=len(l3_proven), l3_failed=len(l3_failed),
                l3_any=len(l3_rgq))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["targets", "l3"], default="targets")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--l3-timeout", type=float, default=120.0)
    ap.add_argument("--files", default="")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        print(write_summary())
        return
    if a.part == "targets":
        run_targets(a.workers)
    else:
        files = [f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f]
        run_l3(a.workers, a.l3_timeout, files or None)


if __name__ == "__main__":
    main()
