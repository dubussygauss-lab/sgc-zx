"""PSEL4 ledger: lowest HQC among P0 (= L2), P2, L3 and P2L3 per circuit.

PSEL4 rule = pipelines/pass_select.compile_select with candidates
("P0", "P2", "L3", "P2L3"): drop a candidate that raised, timed out, left the
native gate set or failed the exactness check; keep the lowest HQC at 1000
shots; ties to lower n_2q, then the order P0, L3, P2, P2L3.

Stored rows are reused, not recompiled:
  P0, P2, PSEL  value/selector_ledger_circuits.csv (A, B1),
                value/family_C_selector.csv (C), value/usecase.csv (usecase)
  L3, P2L3      results/strong_baselines.csv (B1, C)
Compiled here (subcommand run) and stored in value/psel4_runs.csv:
  L3, P2L3      family A (the 180 circuits of value/selector_ledger.py, i.e.
                value_ledger.csv layer NISQ, family A) and bench/usecase.
  Each (circuit, variant) runs in a forked process with a 120 s timeout,
  2 workers.  Compilation goes through pass_select.compile_select with a
  single candidate, so the drop rules are the PSEL rules.  Exactness:
  compile.check against the input (unitary up to 8 qubits, statevector
  9 to 12), above 12 qubits ok-unchecked (check_max_qubits = 12).
  Jobs not started within the global budget (default 20 min) are written
  with status not-run.

Run:  python3 value/psel4_ledger.py run      (compile what is missing)
      python3 value/psel4_ledger.py report   (value/psel4_ledger.csv, .md)
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
import pass_select as PS  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

SHOTS = 1000
CHECK_MAX_QUBITS = 12
RUNS = ROOT / "value/psel4_runs.csv"
OUT_CSV = ROOT / "value/psel4_ledger.csv"
OUT_MD = ROOT / "value/psel4_ledger.md"
DIRS = {"A": ROOT / "bench/family_A", "B1": ROOT / "bench/family_B1",
        "C": ROOT / "bench/family_C", "usecase": ROOT / "bench/usecase"}
CANDS = ["P0", "P2", "L3", "P2L3"]
OK = {"ok", "ok-unchecked", "stored"}


def family_A_files():
    led = pd.read_csv(ROOT / "value/value_ledger.csv")
    led = led[(led.layer == "NISQ") & (led.row_kind == "circuit") & (led.family == "A")]
    return list(led.file)


def usecase_files():
    return list(pd.read_csv(DIRS["usecase"] / "manifest.csv").file)


# ------------------------------------------------------------------ run

def run_one(family, file, variant):
    circ = circuit_from_qasm(str(DIRS[family] / file))
    t0 = time.perf_counter()
    _, rec = PS.compile_select(circ, shots=SHOTS, candidates=(variant,),
                               check_max_qubits=CHECK_MAX_QUBITS)
    r = rec["candidates"][variant]
    return {"family": family, "file": file, "variant": variant,
            "n_qubits": circ.n_qubits, "status": r["status"], "hqc": r["hqc"],
            "n_2q": r["n_2q"], "check_dev": r["check_dev"], "error": r["error"],
            "t_compile_check": time.perf_counter() - t0}


def _child(args, conn):
    try:
        conn.send(run_one(*args))
    except Exception as e:  # noqa: BLE001
        conn.send({"family": args[0], "file": args[1], "variant": args[2],
                   "status": "dropped-error", "error": repr(e)[:300]})


def run_with_timeout(job):
    family, file, variant, timeout, deadline = job
    if time.time() > deadline:
        return {"family": family, "file": file, "variant": variant,
                "status": "not-run", "t_wall": 0.0, "timeout_s": timeout}
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


def cmd_run(a):
    PS.backend()  # build once before forking
    deadline = time.time() + a.budget
    jobs = []
    fams = a.families.split(",")
    if "usecase" in fams:
        jobs += [("usecase", f) for f in usecase_files()]
    if "A" in fams:
        fa = family_A_files()
        fa.sort(key=lambda f: os.path.getsize(DIRS["A"] / f))  # small first
        jobs += [("A", f) for f in fa]
    jobs = [(fam, f, v, a.timeout, deadline) for fam, f in jobs for v in ("L3", "P2L3")]
    print(f"{len(jobs)} jobs, {a.workers} workers, budget {a.budget:.0f} s", flush=True)
    rows = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, row in enumerate(ex.map(run_with_timeout, jobs, chunksize=1)):
            rows.append(row)
            print(f"{i + 1}/{len(jobs)} {row['family']} {row['file']} {row['variant']} "
                  f"{row['status']} hqc={row.get('hqc')} {row['t_wall']:.1f}s "
                  f"[{time.perf_counter() - t0:.0f}s]", flush=True)
            if (i + 1) % 20 == 0:
                _save(rows)
    _save(rows)
    print(f"wrote {RUNS}")


def _save(rows):
    new = pd.DataFrame(rows)
    if RUNS.exists():
        old = pd.read_csv(RUNS)
        key = set(zip(new.family, new.file, new.variant))
        old = old[[(r.family, r.file, r.variant) not in key for r in old.itertuples()]]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(RUNS, index=False)


# --------------------------------------------------------------- report

def _wide_from_long(df, fam):
    d = df[df.family == fam]
    out = {}
    for v in ("L3", "P2L3"):
        x = d[d.variant == v].set_index("file")
        out[v] = x
    return out


def load():
    """One row per circuit with hqc_/n2q_/status_ for P0, P2, L3, P2L3, PSEL."""
    rows = []
    sel = pd.read_csv(ROOT / "value/selector_ledger_circuits.csv")
    led = pd.read_csv(ROOT / "value/value_ledger.csv")
    nq = dict(zip(led.file, led.n_qubits))
    sb = pd.read_csv(ROOT / "results/strong_baselines.csv")
    runs = pd.read_csv(RUNS) if RUNS.exists() else pd.DataFrame(
        columns=["family", "file", "variant", "status", "hqc", "n_2q"])

    def lv(src, fam, file, v):
        x = src[(src.family == fam) & (src.file == file) & (src.variant == v)]
        if not len(x):
            return np.nan, np.nan, "missing"
        x = x.iloc[-1]
        st = x.status
        if st not in ("ok", "ok-unchecked"):
            return np.nan, np.nan, st
        return float(x.hqc), float(x.n_2q), st

    def add(fam, file, n, h0, h2, n0, n2, s0, s2, hsel, src):
        if n is None or pd.isna(n):
            n = circuit_from_qasm(str(DIRS[fam] / file)).n_qubits
        r = {"family": fam, "file": file, "n_qubits": n,
             "hqc_P0": h0, "hqc_P2": h2, "n2q_P0": n0, "n2q_P2": n2,
             "status_P0": s0, "status_P2": s2, "hqc_PSEL": hsel}
        for v in ("L3", "P2L3"):
            h, k, st = lv(src, fam, file, v)
            r[f"hqc_{v}"], r[f"n2q_{v}"], r[f"status_{v}"] = h, k, st
        rows.append(r)

    for x in sel[sel.family == "A"].itertuples():
        add("A", x.file, nq.get(x.file), x.hqc_P0, x.hqc_P2, x.n2q_P0, x.n2q_P2,
            "stored", "stored", x.hqc_SEL, runs)
    b1m = list(pd.read_csv(DIRS["B1"] / "manifest.csv").file)
    for x in sel[(sel.family == "B1") & sel.file.isin(b1m)].itertuples():
        add("B1", x.file, nq.get(x.file), x.hqc_P0, x.hqc_P2, x.n2q_P0, x.n2q_P2,
            "stored", "stored", x.hqc_SEL, sb)
    fc = pd.read_csv(ROOT / "value/family_C_selector.csv")
    for x in fc.itertuples():
        add("C", x.file, x.n_qubits, x.hqc_P0, x.hqc_P2, x.n2q_P0, x.n2q_P2,
            f"stored:{x.check_P0}", f"stored:{x.check_P2}", x.hqc_PSEL, sb)
    uc = pd.read_csv(ROOT / "value/usecase.csv")
    for x in uc.itertuples():
        add("usecase", x.file, x.n_qubits, x.hqc_P0, x.hqc_P2, x.n2q_P0, x.n2q_P2,
            x.status_P0, x.status_P2, x.hqc_PSEL, runs)
    return pd.DataFrame(rows)


def _passed(st):
    return isinstance(st, str) and (st in OK or st.startswith("stored"))


def psel4(r):
    best = None
    for c in CANDS:
        if not _passed(r[f"status_{c}"]) or pd.isna(r[f"hqc_{c}"]):
            continue
        key = (round(r[f"hqc_{c}"], 9), r[f"n2q_{c}"], PS.TIE_ORDER[c])
        if best is None or key < best[0]:
            best = (key, c)
    return (np.nan, None) if best is None else (r[f"hqc_{best[1]}"], best[1])


def pct(a, b):
    return 100.0 * (b - a) / b


def cmd_report(_a):
    df = load()
    df[["hqc_PSEL4", "pick_PSEL4"]] = df.apply(lambda r: pd.Series(psel4(r)), axis=1)
    df["hqc_L2"] = df["hqc_P0"]
    both = df.hqc_L2.notna() & df.hqc_L3.notna()
    df["L2_L3_both_passed"] = both
    df["saved_vs_L3_pct"] = np.where(both, pct(df.hqc_PSEL4, df.hqc_L3), np.nan)
    # PSEL recomputed from stored P0, P2 (sanity)
    psel_re = np.minimum(df.hqc_P0, df.hqc_P2)
    n_psel_diff = int(((psel_re - df.hqc_PSEL).abs() > 1e-9).sum())
    viol = df[both & (df.hqc_PSEL4 > np.minimum(df.hqc_L2, df.hqc_L3) + 1e-9)]
    assert len(viol) == 0, viol[["family", "file"]]
    cols = ["family", "file", "n_qubits", "hqc_P0", "hqc_P2", "hqc_L3", "hqc_P2L3",
            "hqc_PSEL", "hqc_PSEL4", "pick_PSEL4", "n2q_P0", "n2q_P2", "n2q_L3",
            "n2q_P2L3", "status_P0", "status_P2", "status_L3", "status_P2L3",
            "saved_vs_L3_pct"]
    df["n_qubits"] = df["n_qubits"].astype(int)
    df[cols].to_csv(OUT_CSV, index=False)
    # stored P0 against the L2 rows of strong_baselines.csv (B1, C)
    sb = pd.read_csv(ROOT / "results/strong_baselines.csv")
    sl2 = sb[sb.variant == "L2"].set_index(["family", "file"]).hqc
    bc = df[df.family.isin(["B1", "C"])]
    dl2 = np.array([abs(sl2.get((r.family, r.file), np.nan) - r.hqc_P0) for r in bc.itertuples()])

    man_c = pd.read_csv(DIRS["C"] / "manifest.csv")
    disc = set(man_c[~man_c.continuous_angles].file)
    groups = [
        ("A", df[df.family == "A"]),
        ("B1", df[df.family == "B1"]),
        ("B1 without hwb8", df[(df.family == "B1") & (df.file != "hwb8.qasm")]),
        ("C", df[df.family == "C"]),
        ("C without continuous angles", df[(df.family == "C") & df.file.isin(disc)]),
        ("usecase", df[df.family == "usecase"]),
    ]
    L = ["# PSEL4 ledger: lowest HQC of P0 (L2), P2, L3, P2L3", "",
         "Generated by `python3 value/psel4_ledger.py report`. No number is typed by hand.", "",
         "`[F]` PSEL4 keeps, per circuit, the lowest HQC at 1000 shots among P0 (pytket-quantinuum "
         "level 2 = L2), P2 (teleport_reduce then L2), L3 (level 3) and P2L3 (teleport_reduce then "
         "L3). A candidate that raised, timed out, left the native gate set or failed the "
         "exactness check is dropped. Ties go to lower n_2q, then the order P0, L3, P2, P2L3. "
         "PSEL = min(P0, P2) as stored.", "",
         "`[F]` Sources: P0, P2, PSEL from `value/selector_ledger_circuits.csv` (A, B1), "
         "`value/family_C_selector.csv` (C), `value/usecase.csv` (usecase). L3, P2L3 from "
         "`results/strong_baselines.csv` (B1, C) and `value/psel4_runs.csv` (A, usecase, compiled "
         "by `value/psel4_ledger.py run`, 120 s timeout per compile, exactness checked up to 12 "
         "qubits). Per-circuit rows: `value/psel4_ledger.csv`.", "",
         f"`[F]` PSEL recomputed as min(P0, P2) differs from the stored PSEL on {n_psel_diff} circuits.", "",
         f"`[F]` L2 rows of `results/strong_baselines.csv` against the stored P0 (B1, C): "
         f"{int(np.isfinite(dl2).sum())} circuits compared, {int((dl2 > 1e-9).sum())} differ by more "
         f"than 1e-9, {int(np.isnan(dl2).sum())} without an L2 row.", ""]
    # status
    L += ["## L3 and P2L3 status", "", "| family | variant | status | circuits |", "|---|---|---|---|"]
    for fam in ("A", "B1", "C", "usecase"):
        g = df[df.family == fam]
        for v in ("L3", "P2L3"):
            for st, n in g[f"status_{v}"].value_counts().sort_index().items():
                L.append(f"| {fam} | {v} | {st} | {n} |")
    bad = df[~df.status_L3.isin(OK) | ~df.status_P2L3.isin(OK)]
    L.append("")
    if len(bad):
        L.append("`[F]` Circuits with L3 or P2L3 not passed (PSEL4 is taken over the remaining "
                 "candidates):")
        L.append("")
        for r in bad.itertuples():
            L.append(f"- {r.family} `{r.file}`: L3 {r.status_L3}, P2L3 {r.status_P2L3}")
        L.append("")
    L += ["## Totals per family", "",
          "`[F]` Totals are over the circuits where both L2 (= P0) and L3 passed. saved vs X % = "
          "100 (X - PSEL4) / X on the totals. Per-circuit saving vs L3 % = 100 (L3 - PSEL4) / L3.", "",
          "| family | circuits | in totals | L2 | L3 | PSEL | PSEL4 | PSEL saved vs L2 % | "
          "PSEL saved vs L3 % | PSEL4 saved vs L2 % | PSEL4 saved vs L3 % | picks P0 | picks L3 | "
          "picks P2 | picks P2L3 | median saving vs L3 % | max saving vs L3 % | max at |",
          "|" + "---|" * 18]
    summ = []
    for name, g in groups:
        gb = g[g.L2_L3_both_passed]
        t = {k: gb[f"hqc_{k}"].sum() for k in ("L2", "L3", "PSEL", "PSEL4")}
        picks = {c: int((g.pick_PSEL4 == c).sum()) for c in CANDS}
        s = gb.saved_vs_L3_pct
        imax = s.idxmax() if len(s) else None
        rec = dict(group=name, circuits=len(g), in_totals=len(gb), **{f"total_{k}": v for k, v in t.items()},
                   psel_saved_vs_L2_pct=pct(t["PSEL"], t["L2"]), psel_saved_vs_L3_pct=pct(t["PSEL"], t["L3"]),
                   psel4_saved_vs_L2_pct=pct(t["PSEL4"], t["L2"]), psel4_saved_vs_L3_pct=pct(t["PSEL4"], t["L3"]),
                   **{f"picks_{c}": picks[c] for c in CANDS},
                   median_saved_vs_L3_pct=s.median(), max_saved_vs_L3_pct=s.max(),
                   max_at=df.loc[imax, "file"] if imax is not None else "")
        summ.append(rec)
        L.append(f"| {name} | {len(g)} | {len(gb)} | {t['L2']:.1f} | {t['L3']:.1f} | {t['PSEL']:.1f} | "
                 f"{t['PSEL4']:.1f} | {rec['psel_saved_vs_L2_pct']:.2f} | {rec['psel_saved_vs_L3_pct']:.2f} | "
                 f"{rec['psel4_saved_vs_L2_pct']:.2f} | {rec['psel4_saved_vs_L3_pct']:.2f} | "
                 f"{picks['P0']} | {picks['L3']} | {picks['P2']} | {picks['P2L3']} | "
                 f"{rec['median_saved_vs_L3_pct']:.2f} | {rec['max_saved_vs_L3_pct']:.2f} | {rec['max_at']} |")
    L.append("")
    L.append("`[F]` Pick counts are over all circuits of the group, including those not in the "
             "totals. Median and max per-circuit saving vs L3 are over the circuits in the totals; "
             "a negative value would mean PSEL4 above L3 on that circuit.")
    L.append("")
    L += ["## PSEL4 never costs more than min(L2, L3)", "",
          f"`[F]` Checked by assertion on every circuit where both L2 and L3 passed: "
          f"{int(both.sum())} circuits ({', '.join(f'{f} {int(both[df.family == f].sum())}' for f in ('A', 'B1', 'C', 'usecase'))}). "
          f"Violations: {len(viol)}. PSEL4 strictly below min(L2, L3) on "
          f"{int((both & (df.hqc_PSEL4 < np.minimum(df.hqc_L2, df.hqc_L3) - 1e-9)).sum())} of them.", ""]
    for fam in ("A", "B1", "C", "usecase"):
        g = df[(df.family == fam) & both]
        L.append(f"- `[F]` {fam}: PSEL4 strictly below min(L2, L3) on "
                 f"{int((g.hqc_PSEL4 < np.minimum(g.hqc_L2, g.hqc_L3) - 1e-9).sum())} of {len(g)} circuits.")
    L.append("")
    fcp = df[(df.family == "C") & df.pick_PSEL4.isin(["L3", "P2L3"])]
    L += ["## Family C circuits where PSEL4 picks L3 or P2L3", "",
          "`[F]` These outputs are unchecked in `results/strong_baselines.csv` (above 12 qubits) "
          "and need an equivalence proof.", "",
          "| file | n_qubits | continuous angles | pick | HQC P0 | HQC L3 | HQC P2L3 | HQC PSEL4 |",
          "|---|---|---|---|---|---|---|---|"]
    for r in fcp.itertuples():
        L.append(f"| {r.file} | {int(r.n_qubits)} | {r.file not in disc} | {r.pick_PSEL4} | {r.hqc_P0:.1f} | "
                 f"{r.hqc_L3:.1f} | {r.hqc_P2L3:.1f} | {r.hqc_PSEL4:.1f} |")
    L.append("")
    L += ["## Usecase per circuit", "", "| file | P0 | P2 | L3 | P2L3 | PSEL | PSEL4 | pick |",
          "|---|---|---|---|---|---|---|---|"]
    for r in df[df.family == "usecase"].itertuples():
        L.append(f"| {r.file} | {r.hqc_P0:.1f} | {r.hqc_P2:.1f} | {r.hqc_L3:.1f} | {r.hqc_P2L3:.1f} | "
                 f"{r.hqc_PSEL:.1f} | {r.hqc_PSEL4:.1f} | {r.pick_PSEL4} |")
    L.append("")
    OUT_MD.write_text("\n".join(L) + "\n")
    pd.set_option("display.width", 250)
    print(pd.DataFrame(summ).to_string())
    print("C picks L3/P2L3:", list(zip(fcp.file, fcp.pick_PSEL4)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--families", default="usecase,A")
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--timeout", type=float, default=120.0)
    r.add_argument("--budget", type=float, default=1200.0)
    r.set_defaults(func=cmd_run)
    p = sub.add_parser("report")
    p.set_defaults(func=cmd_report)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
