"""Count-only comparison of P2 / PSEL against stronger compiler baselines.

Every variant ends in the H2 native gate set {Rz, PhasedX, ZZPhase, ZZMax}, so
HQC = 5 + (N_1q + 10 N_2q + 5 N_SPAM) * 1000/5000 with N_SPAM = 2 n (the
convention of run_bench_B.py / run_family_C.py, compile.hqc with
n_measure = n_qubits) is comparable across variants.

Backend: QuantinuumBackend("H2-1", api_handler=QuantinuumAPIOffline())
(pytket-quantinuum 0.59.3, no network, no job, no HQC spent).

Variants
  L2     backend.get_compiled_circuit(circ, optimisation_level=2)  (= P0)
  L3     backend.get_compiled_circuit(circ, optimisation_level=3)
  ZXG    AutoRebase({CX, Rz, Rx, H}), ZXGraphlikeOptimisation(), then
         get_compiled_circuit(optimisation_level=2).  The rebase follows
         compile.py P3 (ZXGraphlikeOptimisation accepts CX, CZ, Rx, Rz, H, X,
         Z, SWAP only).
  QK3    qiskit.transpile(optimization_level=3,
         basis_gates=["rz", "sx", "x", "cx"], seed_transpiler=20261009),
         exported with qiskit.qasm2.dumps, read back with
         pytket.qasm.circuit_from_qasm_str, then
         get_compiled_circuit(optimisation_level=0) to rebase into H2 natives.
  QK3L1  same Qiskit output, rebased with optimisation_level=1 (adds the
         1q squash that level 0 omits).
  P2L3   compile.zx_teleport_reduce, then get_compiled_circuit(level 3).
         PSEL3 = min(L3, P2L3) per circuit.
P2 and PSEL are read from value/selector_ledger_circuits.csv (B1) and
value/family_C_selector.csv (family C).

Exactness: compile.check against P0ref of the input (unitary up to 8 qubits,
statevector on |0..0> from 9 to 12 qubits).  Above 12 qubits: unchecked.
Per (circuit, variant) timeout in seconds (default 180), one forked process
per job.  Timeouts and errors are kept as rows.

Usage
  python pipelines/strong_baselines.py run [--workers N] [--timeout S]
         [--families B1,C] [--files a.qasm,...] [--variants L2,L3,...]
  python pipelines/strong_baselines.py report
"""

import argparse
import multiprocessing as mp
import os
import re
from decimal import Decimal
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
from pytket import OpType  # noqa: E402
from pytket.passes import AutoRebase, ZXGraphlikeOptimisation  # noqa: E402
from pytket.qasm import circuit_from_qasm, circuit_from_qasm_str  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT_CSV = os.path.join(RESULTS, "strong_baselines.csv")
OUT_MD = os.path.join(RESULTS, "strong_baselines.md")
FAMILIES = {
    "B1": os.path.join(ROOT, "bench", "family_B1"),
    "C": os.path.join(ROOT, "bench", "family_C"),
}
VARIANTS = ["L2", "L3", "ZXG", "QK3", "QK3L1", "P2L3"]
QISKIT_BASIS = ["rz", "sx", "x", "cx"]
QISKIT_SEED = 20261009
CHECK_MAX_QUBITS = 12

_SCI = re.compile(r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?[eE][-+]?\d+)")


def _tket_to_pyzx_fixed(circ):
    """compile._tket_to_pyzx with scientific-notation angles rewritten as exact
    fixed decimals, as in run_family_C.py (pyzx rejects '6.103515625e-05*pi').
    The override applies to this script only; compile.py is unchanged."""
    qasm = C.circuit_to_qasm_str(circ)
    qasm = _SCI.sub(lambda m: format(Decimal(m.group(1)), "f"), qasm)
    return C.pyzx.Circuit.from_qasm(qasm)


C._tket_to_pyzx = _tket_to_pyzx_fixed

_BACKEND = None


def backend():
    global _BACKEND
    if _BACKEND is None:
        from pytket.extensions.quantinuum import (QuantinuumAPIOffline,
                                                  QuantinuumBackend)
        _BACKEND = QuantinuumBackend(device_name="H2-1",
                                     api_handler=QuantinuumAPIOffline())
    return _BACKEND


def qiskit_o3(circ):
    """pytket Circuit -> Qiskit O3 transpile -> pytket Circuit."""
    import qiskit
    from qiskit import qasm2
    qc = qasm2.loads(C.circuit_to_qasm_str(circ),
                     custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    out = qiskit.transpile(qc, basis_gates=QISKIT_BASIS, optimization_level=3,
                           seed_transpiler=QISKIT_SEED)
    # no coupling map: the layout is trivial and no ancilla is added
    assert out.num_qubits == qc.num_qubits
    return circuit_from_qasm_str(qasm2.dumps(out))


def compile_variant(variant: str, circ):
    """-> (compiled Circuit, timings)."""
    b = backend()
    t0 = time.perf_counter()
    c = circ.copy()
    if variant == "L2":
        t1 = time.perf_counter()
        comp = b.get_compiled_circuit(c, optimisation_level=2)
    elif variant == "L3":
        t1 = time.perf_counter()
        comp = b.get_compiled_circuit(c, optimisation_level=3)
    elif variant == "ZXG":
        AutoRebase({OpType.CX, OpType.Rz, OpType.Rx, OpType.H}).apply(c)
        ZXGraphlikeOptimisation().apply(c)
        t1 = time.perf_counter()
        comp = b.get_compiled_circuit(c, optimisation_level=2)
    elif variant in ("QK3", "QK3L1"):
        c = qiskit_o3(c)
        t1 = time.perf_counter()
        comp = b.get_compiled_circuit(c, optimisation_level=0 if variant == "QK3" else 1)
    elif variant == "P2L3":
        c = C.zx_teleport_reduce(c)
        t1 = time.perf_counter()
        comp = b.get_compiled_circuit(c, optimisation_level=3)
    else:
        raise ValueError(variant)
    t2 = time.perf_counter()
    return comp, {"t_pre": t1 - t0, "t_tket": t2 - t1, "t_total": t2 - t0}


def counts(comp) -> dict:
    types = {cmd.op.type for cmd in comp.get_commands()}
    bad = types - C.NATIVE - {OpType.Barrier}
    return {
        "n_qubits": comp.n_qubits,
        "n_2q": comp.n_gates_of_type(OpType.ZZPhase) + comp.n_gates_of_type(OpType.ZZMax),
        "n_1q": comp.n_gates_of_type(OpType.PhasedX),
        "depth_2q": comp.depth_by_type(C.NATIVE_2Q),
        "hqc": C.hqc(comp, shots=C.SHOTS, n_measure=comp.n_qubits),
        "native": len(bad) == 0,
        "non_native_ops": ",".join(sorted(t.name for t in bad)),
    }


def run_one(family: str, file: str, variant: str) -> dict:
    row = {"family": family, "file": file, "variant": variant}
    circ = circuit_from_qasm(os.path.join(FAMILIES[family], file))
    comp, times = compile_variant(variant, circ)
    row.update(times)
    row.update(counts(comp))
    if circ.n_qubits <= CHECK_MAX_QUBITS:
        ref, _ = C.compile_pipeline("P0ref", circ)
        ck = C.check(comp, ref)
        row.update({k: ck[k] for k in ("check_kind", "check_dev", "check_ok")})
        row["status"] = "ok" if ck["check_ok"] and row["native"] else "FLAGGED"
    else:
        row.update({"check_kind": "none", "check_dev": float("nan"),
                    "check_ok": float("nan")})
        row["status"] = "ok-unchecked" if row["native"] else "FLAGGED-unchecked"
    return row


def _child(args, conn):
    try:
        conn.send(run_one(*args))
    except Exception as e:  # noqa: BLE001
        conn.send({"family": args[0], "file": args[1], "variant": args[2],
                   "status": "error", "error": repr(e)[:300]})


def run_with_timeout(job):
    family, file, variant, timeout = job
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=((family, file, variant), child))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(timeout):
        row = parent.recv()
    else:
        p.kill()
        row = {"family": family, "file": file, "variant": variant,
               "status": "timeout"}
    p.join()
    row["t_wall"] = time.perf_counter() - t0
    row["timeout_s"] = timeout
    return row


def manifest_files(family: str) -> list:
    return list(pd.read_csv(os.path.join(FAMILIES[family], "manifest.csv"))["file"])


def cmd_run(a):
    backend()  # build once before forking
    want = {f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f}
    jobs = []
    for fam in a.families.split(","):
        for f in manifest_files(fam):
            if want and f not in want:
                continue
            for v in a.variants.split(","):
                jobs.append((fam, f, v, a.timeout))
    # long jobs first so the tail is short
    jobs.sort(key=lambda j: -os.path.getsize(os.path.join(FAMILIES[j[0]], j[1])))
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            print(f"{i + 1}/{len(jobs)} {row['family']} {row['file']} {row['variant']} "
                  f"{row['status']} hqc={row.get('hqc')} {row['t_wall']:.1f}s "
                  f"[{time.perf_counter() - t0:.0f}s]", flush=True)
    new = pd.DataFrame(rows)
    if os.path.exists(OUT_CSV):
        old = pd.read_csv(OUT_CSV)
        key = set(zip(new["family"], new["file"], new["variant"]))
        old = old[[(r.family, r.file, r.variant) not in key for r in old.itertuples()]]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}")


# ------------------------------------------------------------------ report

def ours() -> pd.DataFrame:
    """P0, P2, PSEL HQC per circuit from the stored selector tables."""
    led = pd.read_csv(os.path.join(ROOT, "value", "selector_ledger_circuits.csv"))
    b1 = led[led.family == "B1"][["file", "hqc_P0", "hqc_P2", "hqc_SEL"]].rename(
        columns={"hqc_SEL": "hqc_PSEL"})
    b1 = b1[b1.file.isin(manifest_files("B1"))]
    b1["family"] = "B1"
    fc = pd.read_csv(os.path.join(ROOT, "value", "family_C_selector.csv"))
    fc = fc[["file", "hqc_P0", "hqc_P2", "hqc_PSEL"]].copy()
    fc["family"] = "C"
    return pd.concat([b1, fc], ignore_index=True)


def wide() -> pd.DataFrame:
    df = pd.read_csv(OUT_CSV)
    w = df.pivot_table(index=["family", "file"], columns="variant", values="hqc",
                       aggfunc="first").reset_index()
    st = df.pivot_table(index=["family", "file"], columns="variant", values="status",
                        aggfunc="first").reset_index()
    w = w.merge(ours(), on=["family", "file"], how="outer")
    for v in VARIANTS:
        if v not in w:
            w[v] = np.nan
    w["PSEL_recomputed"] = np.minimum(w["hqc_P0"], w["hqc_P2"])
    w["PSEL3"] = np.fmin(w["L3"], w["P2L3"])
    w["PSEL3"] = w["PSEL3"].where(w["L3"].notna() & w["P2L3"].notna())
    return w, st, df


def pct(a, b):
    return 100.0 * (b - a) / b


def cmd_report(_a):
    w, st, df = wide()
    L = []
    L.append("# Strong baselines: HQC at 1000 shots, families B1 (15) and C (20)\n")
    L.append("Generated by `python pipelines/strong_baselines.py report` from "
             "`results/strong_baselines.csv` (variants L2, L3, ZXG, QK3, QK3L1, P2L3) "
             "and the stored P2 / PSEL columns of `value/selector_ledger_circuits.csv` "
             "and `value/family_C_selector.csv`. Definitions are in the docstring of "
             "`pipelines/strong_baselines.py`. QK3 uses Qiskit "
             f"{__import__('qiskit').__version__} `transpile(optimization_level=3, "
             f"basis_gates={QISKIT_BASIS}, seed_transpiler={QISKIT_SEED})`, then the "
             "official H2-1 compilation at optimisation level 0 (rebase only). QK3L1 "
             "is the same Qiskit output rebased at level 1. HQC = 5 + (N_1q + 10 N_2q + "
             "5 * 2n) / 5.\n")

    # status
    L.append("## Run status\n")
    L.append(f"Timeout per (circuit, variant): {df['timeout_s'].max():.0f} s. Exactness is "
             f"checked for circuits with at most {CHECK_MAX_QUBITS} qubits (all of B1); "
             "family C circuits are larger and unchecked (status ok-unchecked).\n")
    sc = df.groupby(["family", "variant", "status"]).size().reset_index(name="n")
    L.append("| family | variant | status | circuits |")
    L.append("|---|---|---|---|")
    for r in sc.itertuples():
        L.append(f"| {r.family} | {r.variant} | {r.status} | {r.n} |")
    bad = df[~df.status.isin(["ok", "ok-unchecked"])]
    L.append("")
    if len(bad):
        L.append("Rows not ok (timeout, error or FLAGGED):\n")
        for r in bad.itertuples():
            L.append(f"- {r.family} `{r.file}` {r.variant}: {r.status}"
                     + (f" ({r.error})" if isinstance(getattr(r, 'error', None), str) else ""))
        L.append("")
    else:
        L.append("All rows are ok or ok-unchecked (no timeout, no error).\n")

    if "rerun" in df:
        rr = df[df["rerun"].notna()]
        if len(rr):
            L.append(f"First pass: 3 workers on {os.cpu_count()} cores. The {len(rr)} jobs "
                     "that timed out or failed there were rerun with 2 workers and the "
                     "same timeout (first-pass rows kept in "
                     "`results/strong_baselines_run1.csv`). The two P2L3 errors of the "
                     "first pass came from pyzx rejecting angles written in scientific "
                     "notation and were fixed by the fixed-decimal rewrite of "
                     "run_family_C.py. Rerun rows:\n")
            for r in rr.itertuples():
                L.append(f"- {r.family} `{r.file}` {r.variant}: {r.status}, "
                         f"wall {r.t_wall:.1f} s")
            L.append("")

    # L2 vs P0
    d = (w["L2"] - w["hqc_P0"]).abs()
    L.append("## L2 against the stored P0\n")
    L.append(f"Circuits with both values: {int(d.notna().sum())}. "
             f"Circuits where L2 HQC differs from the stored P0 HQC by more than 1e-9: "
             f"{int((d > 1e-9).sum())}. Max |L2 - P0| = {d.max():.6g}.\n")
    dps = (w["PSEL_recomputed"] - w["hqc_PSEL"]).abs()
    L.append(f"PSEL recomputed as min(P0, P2) from the stored columns differs from the "
             f"stored PSEL on {int((dps > 1e-9).sum())} circuits.\n")

    cols = ["L2", "L3", "ZXG", "QK3", "QK3L1", "hqc_P2", "hqc_PSEL", "P2L3", "PSEL3"]
    main = ["L2", "L3", "ZXG", "QK3", "hqc_P2", "hqc_PSEL"]
    names = {"hqc_P2": "P2", "hqc_PSEL": "PSEL"}
    base = ["L2", "L3", "ZXG", "QK3"]
    comp = base + ["hqc_PSEL"]
    for fam, g in w.groupby("family"):
        g = g.copy()
        complete = g[main].notna().all(axis=1)
        nc = int(complete.sum())
        L.append(f"## Family {fam}: totals\n")
        L.append(f"Circuits: {len(g)}. Circuits with L2, L3, ZXG, QK3, P2 and PSEL all "
                 f"available: {nc}. Totals in the table are over these {nc} circuits"
                 + ("" if nc == len(g) else ", excluded: " + ", ".join(
                     f"`{f}`" for f in g[~complete].file)) + ".\n")
        gc = g[complete]
        tot = {c: gc[c].sum() for c in main + ["QK3L1"]}
        best_base = gc[base].min(axis=1)
        mins = gc[comp].min(axis=1)
        L.append("| compiler | total HQC | saved vs L2 (%) | saved vs L3 (%) | "
                 "circuits where it is the unique lowest of L2, L3, ZXG, QK3, PSEL | "
                 "circuits where it is lowest or tied lowest |")
        L.append("|---|---|---|---|---|---|")
        for c in main + ["QK3L1"]:
            if c in comp:
                others = [o for o in comp if o != c]
                uniq = int((gc[c] < gc[others].min(axis=1) - 1e-9).sum())
                n_min = int(((gc[c] - mins).abs() < 1e-9).sum())
                wtxt, ttxt = str(uniq), str(n_min)
            else:
                wtxt, ttxt = "n/a", "n/a"
            L.append(f"| {names.get(c, c)} | {tot[c]:.1f} | {pct(tot[c], tot['L2']):.2f} | "
                     f"{pct(tot[c], tot['L3']):.2f} | {wtxt} | {ttxt} |")
        L.append("")
        if nc < len(g):
            sub = ["L2", "L3", "QK3", "hqc_P2", "hqc_PSEL"]
            ok5 = g[sub].notna().all(axis=1)
            g5 = g[ok5]
            t5 = {c: g5[c].sum() for c in sub}
            L.append(f"Over the {int(ok5.sum())} circuits with L2, L3, QK3, P2 and PSEL "
                     "(ZXG left out): " + ", ".join(
                         f"{names.get(c, c)} {t5[c]:.1f}" for c in sub) +
                     f". PSEL saved {pct(t5['hqc_PSEL'], t5['L2']):.2f} % against L2 and "
                     f"{pct(t5['hqc_PSEL'], t5['L3']):.2f} % against L3.\n")
        L.append("P2 and QK3L1 are not in the win count (P2 is one arm of PSEL, QK3L1 "
                 "is a supplementary variant of QK3).\n")
        ps = gc["hqc_PSEL"]
        L.append("### PSEL against BEST = min(L2, L3, ZXG, QK3) per circuit\n")
        L.append(f"BEST total {best_base.sum():.1f}. PSEL total {ps.sum():.1f}: saved "
                 f"{pct(ps.sum(), best_base.sum()):.2f} % against BEST. PSEL below BEST on "
                 f"{int((ps < best_base - 1e-9).sum())} circuits, equal on "
                 f"{int(((ps - best_base).abs() <= 1e-9).sum())}, above on "
                 f"{int((ps > best_base + 1e-9).sum())}. With QK3L1 added to BEST the "
                 f"BEST total is {gc[base + ['QK3L1']].min(axis=1).sum():.1f}.\n")
        c3 = g["L3"].notna() & g["P2L3"].notna()
        g3 = g[c3]
        n3 = int(c3.sum())
        L.append("### PSEL3 = min(L3, P2L3)\n")
        L.append(f"Over the {n3} circuits with both L3 and P2L3 available: L3 total "
                 f"{g3['L3'].sum():.1f}, P2L3 total {g3['P2L3'].sum():.1f}, PSEL3 total "
                 f"{g3['PSEL3'].sum():.1f}, saved {pct(g3['PSEL3'].sum(), g3['L3'].sum()):.2f} % "
                 f"against L3. P2L3 below L3 on {int((g3['P2L3'] < g3['L3'] - 1e-9).sum())} "
                 f"circuits, above on {int((g3['P2L3'] > g3['L3'] + 1e-9).sum())}.\n")
        L.append("### Per circuit\n")
        L.append("| file | " + " | ".join(names.get(c, c) for c in cols) +
                 " | BEST | BEST from | PSEL - BEST |")
        L.append("|---|" + "---|" * (len(cols) + 3))
        for r in g.itertuples():
            vals = [getattr(r, c) for c in cols]
            bb = [getattr(r, c) for c in base]
            if all(pd.notna(v) for v in bb):
                bmin = min(bb)
                who = ",".join(c for c in base if abs(getattr(r, c) - bmin) < 1e-9)
                diff = f"{r.hqc_PSEL - bmin:+.1f}"
                btxt = f"{bmin:.1f}"
            else:
                btxt, who, diff = "n/a", "n/a", "n/a"
            cells = []
            for c, v in zip(cols, vals):
                if pd.notna(v):
                    cells.append(f"{v:.1f}")
                else:
                    s = st[(st.family == fam) & (st.file == r.file)]
                    s = s[c].iloc[0] if c in s and len(s) else "missing"
                    cells.append(str(s))
            L.append(f"| {r.file} | " + " | ".join(cells) + f" | {btxt} | {who} | {diff} |")
        L.append("")
    with open(OUT_MD, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {OUT_MD}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--families", default="B1,C")
    r.add_argument("--files", default="")
    r.add_argument("--variants", default=",".join(VARIANTS))
    r.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    r.add_argument("--timeout", type=float, default=180.0)
    r.set_defaults(func=cmd_run)
    p = sub.add_parser("report")
    p.set_defaults(func=cmd_report)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
