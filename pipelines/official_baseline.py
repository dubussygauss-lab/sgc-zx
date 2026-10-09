"""Official pytket-quantinuum default pass compared with the reproduced P0.

The reproduced P0 of pipelines/compile.py (quantinuum_default_pass(2)) is
built pass by pass without a backend object.  This script builds the official
pass from an offline backend object of pytket-quantinuum 0.59.3:

    QuantinuumBackend(device_name="H2-1", api_handler=QuantinuumAPIOffline())

QuantinuumAPIOffline() carries the bundled OFFLINE_MACHINE_LIST
(api_wrappers.py), so no network, login, job or HQC is used.  Two variants
are compiled per circuit:

  P0off  backend.get_compiled_circuit(circ, optimisation_level=2)
  P2off  compile.zx_teleport_reduce(circ), then
         backend.default_compilation_pass(optimisation_level=2).apply

Metrics: n_2q = ZZPhase + ZZMax, n_1q = PhasedX, depth_2q over
{ZZPhase, ZZMax}, HQC = compile.hqc(comp, 1000, n_measure=n_qubits) (the
convention of run_bench.py / run_bench_B.py).  Exactness: compile.check
against P0ref of the input (unitary up to n = 8, statevector beyond), with
the stored reference distribution where one exists, for n <= 12 only.

Subcommands
  python pipelines/official_baseline.py run [--families A,B1,B1x,B2]
        [--files a.qasm,...] [--skip hwb8.qasm] [--variants P0off,P2off]
        [--workers N] [--timeout S]
      compiles and merges rows into results/official_baseline.csv
      (rows with the same (family, file, variant) are replaced).
  python pipelines/official_baseline.py report
      writes results/official_baseline.md from the CSV and the stored
      results/family_*_counts.csv rows.
  python pipelines/official_baseline.py passdiff
      prints the official pass and the reproduced pass as JSON and whether
      they are equal.
"""

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
from pytket import OpType  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT_CSV = os.path.join(RESULTS, "official_baseline.csv")
OUT_MD = os.path.join(RESULTS, "official_baseline.md")

FAMILIES = {
    "A": os.path.join(ROOT, "bench", "family_A"),
    "B1": os.path.join(ROOT, "bench", "family_B1"),
    "B1x": os.path.join(ROOT, "bench", "family_B1x"),
    "B2": os.path.join(ROOT, "bench", "family_B2"),
}
CHECK_MAX_QUBITS = 12
VARIANTS = ["P0off", "P2off"]
OURS = {"P0off": "P0", "P2off": "P2"}
METRICS = ["n_2q", "n_1q", "depth_2q", "hqc"]

_BACKEND = None


def backend():
    global _BACKEND
    if _BACKEND is None:
        from pytket.extensions.quantinuum import (QuantinuumAPIOffline,
                                                  QuantinuumBackend)
        _BACKEND = QuantinuumBackend(device_name="H2-1",
                                     api_handler=QuantinuumAPIOffline())
    return _BACKEND


def official_pass(optimisation_level: int = 2):
    return backend().default_compilation_pass(optimisation_level=optimisation_level)


def compile_official(variant: str, circ):
    """-> (compiled Circuit, timings)."""
    t0 = time.perf_counter()
    if variant == "P0off":
        t1 = time.perf_counter()
        comp = backend().get_compiled_circuit(circ, optimisation_level=2)
    elif variant == "P2off":
        c = C.zx_teleport_reduce(circ.copy())
        t1 = time.perf_counter()
        official_pass(2).apply(c)
        comp = c
    else:
        raise ValueError(variant)
    t2 = time.perf_counter()
    return comp, {"t_zx": t1 - t0, "t_tket": t2 - t1, "t_total": t2 - t0}


def counts(comp) -> dict:
    types = {cmd.op.type for cmd in comp.get_commands()}
    bad = types - C.NATIVE - {OpType.Barrier}
    return {
        "n_qubits": comp.n_qubits,
        "n_2q": comp.n_gates_of_type(OpType.ZZPhase) + comp.n_gates_of_type(OpType.ZZMax),
        "n_zzphase": comp.n_gates_of_type(OpType.ZZPhase),
        "n_zzmax": comp.n_gates_of_type(OpType.ZZMax),
        "n_1q": comp.n_gates_of_type(OpType.PhasedX),
        "n_rz": comp.n_gates_of_type(OpType.Rz),
        "depth_2q": comp.depth_by_type(C.NATIVE_2Q),
        "hqc": C.hqc(comp, shots=C.SHOTS, n_measure=comp.n_qubits),
        "native": len(bad) == 0,
        "non_native_ops": ",".join(sorted(t.name for t in bad)),
    }


def run_one(family: str, file: str, variant: str) -> dict:
    bench = FAMILIES[family]
    row = {"family": family, "file": file, "variant": variant}
    circ = circuit_from_qasm(os.path.join(bench, file))
    comp, times = compile_official(variant, circ)
    row.update(times)
    row.update(counts(comp))
    if circ.n_qubits <= CHECK_MAX_QUBITS:
        ref, _ = C.compile_pipeline("P0ref", circ)
        npy = os.path.join(bench, file.replace(".qasm", ".npy"))
        ref_probs = np.load(npy) if os.path.exists(npy) else None
        ck = C.check(comp, ref, ref_probs)
        row.update({k: ck[k] for k in ("check_kind", "check_dev", "dist_maxdiff", "check_ok")})
        row["status"] = "ok" if ck["check_ok"] and row["native"] else "FLAGGED"
    else:
        row.update({"check_kind": "none", "check_dev": float("nan"),
                    "dist_maxdiff": float("nan"), "check_ok": float("nan")})
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
        p.terminate()
        row = {"family": family, "file": file, "variant": variant, "status": "timeout"}
    p.join()
    row["t_wall"] = time.perf_counter() - t0
    return row


def manifest_files(family: str) -> list:
    return list(pd.read_csv(os.path.join(FAMILIES[family], "manifest.csv"))["file"])


def cmd_run(a):
    backend()  # build once before forking
    jobs = []
    files_wanted = {f if f.endswith(".qasm") else f + ".qasm"
                    for f in a.files.split(",") if f}
    skip = {f if f.endswith(".qasm") else f + ".qasm" for f in a.skip.split(",") if f}
    for fam in a.families.split(","):
        for f in manifest_files(fam):
            if files_wanted and f not in files_wanted:
                continue
            if f in skip:
                continue
            for v in a.variants.split(","):
                jobs.append((fam, f, v, a.timeout))
    print(f"{len(jobs)} jobs", flush=True)
    t0 = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                print(f"{i + 1}/{len(jobs)} done, {time.perf_counter() - t0:.0f}s", flush=True)
    new = pd.DataFrame(rows)
    if os.path.exists(OUT_CSV):
        old = pd.read_csv(OUT_CSV)
        key = set(zip(new["family"], new["file"], new["variant"]))
        old = old[[(r.family, r.file, r.variant) not in key for r in old.itertuples()]]
        new = pd.concat([old, new], ignore_index=True)
    new = attach_ours(new)
    new.to_csv(OUT_CSV, index=False)
    print(new.groupby(["family", "variant", "status"]).size())


def stored(family: str) -> pd.DataFrame:
    d = pd.read_csv(os.path.join(RESULTS, f"family_{family}_counts.csv"))
    d = d[d.pipeline.isin(["P0", "P2"])].copy()
    d["n_1q"] = d["n_phasedx"]
    d["variant"] = d["pipeline"].map({"P0": "P0off", "P2": "P2off"})
    d["family"] = family
    return d[["family", "file", "variant"] + METRICS]


def attach_ours(df: pd.DataFrame) -> pd.DataFrame:
    df = df[[c for c in df.columns if not c.endswith("_ours")
             and not c.startswith("diff_") and c != "identical"]]
    ours = pd.concat([stored(f) for f in FAMILIES], ignore_index=True)
    ours = ours.rename(columns={m: m + "_ours" for m in METRICS})
    df = df.merge(ours, on=["family", "file", "variant"], how="left")
    for m in METRICS:
        df[f"diff_{m}"] = df[m] - df[m + "_ours"]
    df["identical"] = np.isclose(df[[f"diff_{m}" for m in METRICS]].abs().sum(axis=1), 0.0) \
        & df[[f"diff_{m}" for m in METRICS]].notna().all(axis=1)
    order = {f: i for i, f in enumerate(FAMILIES)}
    return df.sort_values(["family", "file", "variant"],
                          key=lambda s: s.map(order) if s.name == "family" else s
                          ).reset_index(drop=True)


# -------------------------------------------------------------- report

def select(p0: dict, p2: dict) -> str:
    """PSEL rule of pipelines/pass_select.py: lower HQC, then lower n_2q, then P0."""
    k0 = (round(p0["hqc"], 9), p0["n_2q"], 0)
    k2 = (round(p2["hqc"], 9), p2["n_2q"], 1)
    return "P0" if k0 <= k2 else "P2"


def psel_table(df: pd.DataFrame, family: str, cols: tuple) -> dict:
    """cols = (P0 hqc/n2q source suffix, P2 suffix): '' for official, '_ours'."""
    sub = df[df.family == family]
    p0 = sub[sub.variant == "P0off"].set_index("file")
    p2 = sub[sub.variant == "P2off"].set_index("file")
    files = sorted(set(p0.index) & set(p2.index))
    s = cols
    # same circuit set for both bases: official and stored rows both present
    files = [f for f in files
             if not any(np.isnan(x.loc[f, "hqc" + t]) for x in (p0, p2) for t in ("", "_ours"))]
    tot0 = tot2 = totsel = 0.0
    picks = 0
    per = []
    for f in files:
        a = {"hqc": p0.loc[f, "hqc" + s], "n_2q": p0.loc[f, "n_2q" + s]}
        b = {"hqc": p2.loc[f, "hqc" + s], "n_2q": p2.loc[f, "n_2q" + s]}
        ch = select(a, b)
        sel = b if ch == "P2" else a
        picks += ch == "P2"
        tot0 += a["hqc"]
        tot2 += b["hqc"]
        totsel += sel["hqc"]
        per.append(100 * (a["hqc"] - sel["hqc"]) / a["hqc"])
    return {"circuits": len(files), "picks_P2": picks, "hqc_P0": tot0,
            "hqc_P2": tot2, "hqc_PSEL": totsel, "saved": tot0 - totsel,
            "saved_pct": 100 * (tot0 - totsel) / tot0 if tot0 else float("nan"),
            "median_pct": float(np.median(per)) if per else float("nan"),
            "files": files}


def fmt(x, nd=1):
    if isinstance(x, float) and np.isnan(x):
        return "n/a"
    return f"{x:,.{nd}f}"


def cmd_report(a):
    df = pd.read_csv(OUT_CSV)
    df = attach_ours(df)
    df.to_csv(OUT_CSV, index=False)
    import pytket
    import pytket.extensions.quantinuum as pq
    L = []
    L.append("# Official pytket-quantinuum default pass against the reproduced P0\n")
    L.append("Generated by `pipelines/official_baseline.py report` from "
             "`results/official_baseline.csv` and `results/family_{A,B1,B1x,B2}_counts.csv`. "
             "No number is typed by hand.\n")
    L.append(f"`[F]` Versions: pytket {pytket.__version__}, pytket-quantinuum "
             f"{pq._metadata.__extension_version__}. Backend "
             "`QuantinuumBackend(device_name=\"H2-1\", api_handler=QuantinuumAPIOffline())`, "
             "built from the device list bundled in the package. No network call, no job, no HQC.\n")
    L.append("`[F]` P0off = `backend.get_compiled_circuit(circ, optimisation_level=2)`. "
             "P2off = `compile.zx_teleport_reduce` then "
             "`backend.default_compilation_pass(optimisation_level=2)`. "
             "Ours = the P0 and P2 rows of `results/family_*_counts.csv` (reproduced pass, "
             "`compile.quantinuum_default_pass(2)`). HQC at 1000 shots with "
             "`compile.hqc(comp, n_measure=n_qubits)`. n_2q = ZZPhase + ZZMax, n_1q = PhasedX.\n")

    # pass structure
    off = official_pass(2).to_dict()
    rep = C.quantinuum_default_pass(2).to_dict()
    so = [p["StandardPass"]["name"] for p in off["SequencePass"]["sequence"]]
    sr = [p["StandardPass"]["name"] for p in rep["SequencePass"]["sequence"]]
    L.append("## Pass structure\n")
    L.append(f"`[F]` Official sequence: {', '.join(so)}.\n")
    L.append(f"`[F]` Reproduced sequence: {', '.join(sr)}. Same names in the same order: "
             f"{so == sr}.\n")
    diffs = []
    for i, (x, y) in enumerate(zip(off["SequencePass"]["sequence"], rep["SequencePass"]["sequence"])):
        if x != y:
            xs, ys = x["StandardPass"], y["StandardPass"]
            keys = sorted(set(xs) | set(ys))
            for k in keys:
                if xs.get(k) != ys.get(k):
                    if isinstance(xs.get(k), list) and isinstance(ys.get(k), list):
                        diffs.append(f"step {i} {xs['name']} `{k}`: official only "
                                     f"{sorted(set(xs[k]) - set(ys[k]))}, reproduced only "
                                     f"{sorted(set(ys[k]) - set(xs[k]))}")
                    else:
                        diffs.append(f"step {i} {xs['name']} `{k}`: official {xs.get(k)!r}, "
                                     f"reproduced {ys.get(k)!r}")
    if diffs:
        L.append("`[F]` Serialised parameter differences:\n")
        for d_ in diffs:
            L.append(f"- {d_}")
        L.append("")
        L.append("`[F]` The extra AutoRebase basis entries of the official pass are classical "
                 "and control-flow op types. AutoRebase leaves basis types untouched and no "
                 "benchmark input contains any of them, so they cannot change a count here.\n")
    else:
        L.append("`[F]` The serialised passes are identical.\n")

    # agreement
    L.append("## Agreement with the reproduced pipelines\n")
    L.append("`[F]` identical = n_2q, n_1q, depth_2q and HQC all equal to the stored row. "
             "Differences are official minus ours.\n")
    L.append("| family | variant | circuits compiled | with stored row | identical | "
             "max abs diff n_2q | mean diff n_2q | max abs diff n_1q | mean diff n_1q | "
             "max abs diff depth_2q | max abs diff HQC | mean diff HQC |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for fam in FAMILIES:
        for v in VARIANTS:
            s = df[(df.family == fam) & (df.variant == v)]
            ok = s[s["n_2q"].notna()]
            w = ok[ok["n_2q_ours"].notna()]
            if len(s) == 0:
                continue
            L.append(f"| {fam} | {v} | {len(ok)} | {len(w)} | {int(w.identical.sum())} | "
                     f"{fmt(w.diff_n_2q.abs().max(), 0)} | {fmt(w.diff_n_2q.mean(), 2)} | "
                     f"{fmt(w.diff_n_1q.abs().max(), 0)} | {fmt(w.diff_n_1q.mean(), 2)} | "
                     f"{fmt(w.diff_depth_2q.abs().max(), 0)} | {fmt(w.diff_hqc.abs().max(), 1)} | "
                     f"{fmt(w.diff_hqc.mean(), 2)} |")
    L.append("")
    nonid = df[df["n_2q"].notna() & df["n_2q_ours"].notna() & ~df.identical]
    if len(nonid):
        L.append("`[F]` Rows that differ:\n")
        L.append("| family | file | variant | n_2q off/ours | n_1q off/ours | depth_2q off/ours | HQC off/ours |")
        L.append("|---|---|---|---|---|---|---|")
        for r in nonid.itertuples():
            L.append(f"| {r.family} | {r.file} | {r.variant} | {r.n_2q:.0f}/{r.n_2q_ours:.0f} | "
                     f"{r.n_1q:.0f}/{r.n_1q_ours:.0f} | {r.depth_2q:.0f}/{r.depth_2q_ours:.0f} | "
                     f"{r.hqc:.1f}/{r.hqc_ours:.1f} |")
        L.append("")
    missing = df[df["n_2q"].isna()]
    if len(missing):
        L.append("`[F]` Rows without official counts (status): " + ", ".join(
            f"{r.family}/{r.file}/{r.variant} ({r.status})" for r in missing.itertuples()) + ".\n")

    # exactness
    L.append("## Exactness of the official output (n <= 12)\n")
    L.append("| family | variant | checked | check_ok | max check_dev | max dist_maxdiff | unchecked (n > 12) | status not ok |")
    L.append("|---|---|---|---|---|---|---|---|")
    for fam in FAMILIES:
        for v in VARIANTS:
            s = df[(df.family == fam) & (df.variant == v)]
            if len(s) == 0:
                continue
            ck = s[s.check_kind.isin(["unitary", "statevector"])]
            L.append(f"| {fam} | {v} | {len(ck)} | {int((ck.check_ok.astype(str) == 'True').sum())} | "
                     f"{ck.check_dev.max():.2e} | "
                     f"{fmt(ck.dist_maxdiff.max(), 2) if ck.dist_maxdiff.notna().any() else 'n/a'} | "
                     f"{int((s.check_kind == 'none').sum())} | "
                     f"{int((~s.status.isin(['ok', 'ok-unchecked'])).sum())} |")
    L.append("")

    # PSEL
    L.append("## PSEL and P2 savings against the official P0\n")
    L.append("`[F]` PSEL rule of `pipelines/pass_select.py`: per circuit keep the lower HQC, "
             "an HQC tie goes to the lower n_2q and a further tie to P0. Official = P0off and "
             "P2off. Ours = stored P0 and P2 rows restricted to the same circuits. "
             "saved = HQC_P0 - HQC_PSEL summed over the family. saved % = 100 saved / HQC_P0. "
             "P2 extra % = 100 (HQC_P2 - HQC_P0) / HQC_P0.\n")
    L.append("| family | basis | circuits | picks P2 | HQC P0 | HQC P2 | HQC PSEL | saved | saved % | median per-circuit % | P2 extra % |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for fam in FAMILIES:
        for basis, suf in (("official", ""), ("ours", "_ours")):
            t = psel_table(df, fam, suf)
            if t["circuits"] == 0:
                continue
            ex = 100 * (t["hqc_P2"] - t["hqc_P0"]) / t["hqc_P0"]
            L.append(f"| {fam} | {basis} | {t['circuits']} | {t['picks_P2']} | {fmt(t['hqc_P0'])} | "
                     f"{fmt(t['hqc_P2'])} | {fmt(t['hqc_PSEL'])} | {fmt(t['saved'])} | "
                     f"{fmt(t['saved_pct'], 2)} | {fmt(t['median_pct'], 2)} | {fmt(ex, 2)} |")
    L.append("")
    b1 = psel_table(df, "B1", "")
    b1_all = set(manifest_files("B1"))
    miss = sorted(b1_all - set(b1["files"]))
    if miss:
        L.append(f"`[F]` B1 circuits without both official variants: {', '.join(miss)}. "
                 "The B1 rows above cover the remaining circuits only.\n")
    if a.note:
        L.append(a.note + "\n")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(L))
    print("\n".join(L))


def cmd_passdiff(a):
    off = official_pass(2).to_dict()
    rep = C.quantinuum_default_pass(2).to_dict()
    print(json.dumps(off, indent=1))
    print(json.dumps(rep, indent=1))
    print("equal:", off == rep)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--families", default="A,B1,B1x,B2")
    r.add_argument("--files", default="")
    r.add_argument("--skip", default="")
    r.add_argument("--variants", default=",".join(VARIANTS))
    r.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    r.add_argument("--timeout", type=float, default=560.0)
    q = sp.add_parser("report")
    q.add_argument("--note", default="", help="extra Markdown paragraph appended to the report")
    sp.add_parser("passdiff")
    a = ap.parse_args()
    {"run": cmd_run, "report": cmd_report, "passdiff": cmd_passdiff}[a.cmd](a)


if __name__ == "__main__":
    main()
