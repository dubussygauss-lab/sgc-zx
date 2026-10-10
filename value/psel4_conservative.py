"""Conservative PSEL4: lowest-HQC candidate among the verified ones, else P0.

No new compilation.  Every number in value/psel4_conservative.md is computed
here from CSVs already in the repository.

Rule.  For each circuit and each PSEL4 candidate (P0, P2, L3, P2L3) the
candidate counts as verified if
  (a) its status in value/psel4_ledger.csv, traced to the script that wrote
      it, is a passed full unitary check (up to 8 qubits) or a passed state
      check (9 to 20 qubits), or
  (b) a PyZX miter verdict "proven" exists for that circuit and pipeline.
The variant keeps the verified candidate with the lowest HQC (ties as in
PSEL4: lower n_2q, then the order P0, L3, P2, P2L3).  With no verified
candidate it keeps P0, the pytket-quantinuum default output, and flags the
circuit "default, unverified".  This variant is not "proven-only": rule (a)
accepts numerical checks.

Status mapping (rule a), from value/psel4_ledger.py and pipelines/pass_select.py
  stored       (A, B1; P0, P2) placeholder written by psel4_ledger.load() for
               rows reused from value/selector_ledger_circuits.csv.  The check
               itself is in results/family_A_counts.csv and
               results/family_B1_counts.csv (compile.check: unitary up to 8
               qubits, statevector beyond).  Verified iff the matching row
               (same file, pipeline, HQC) has status ok, check_ok True and the
               check kind fits n_qubits.  Joined and asserted below.
  ok           (usecase; P0, P2) value/usecase.csv, written by
               pass_select.compile_select with check_max_qubits 20: ok =
               compile.check passed.  Verified.
  ok           (A, usecase; L3, P2L3) value/psel4_runs.csv, compile_select with
               check_max_qubits 12: ok = compile.check passed.  Verified.
  ok           (B1; L3, P2L3) results/strong_baselines.csv, check_ok True.
               Verified (asserted below).
  ok-unchecked (C; L3, P2L3) no check run (above the qubit limit).  Not verified.
  stored:pass  (C; P0, P2) value/family_C_selector.py: agreement on 64 random
               basis inputs, documented there as "not a proof of
               equivalence".  Neither a full unitary nor a state check of
               compile.check.  Not verified.
  stored:unchecked-branching (C; P0, P2) no check.  Not verified.
  timeout      (B1 hwb8; P2L3) no output, not a candidate.
PyZX verdicts (rule b), method pyzx / pyzx-miter, verdict "proven" only:
  P0, P2       results/family_C_equivalence.csv, comparison == pipeline
  L3           results/family_C_equivalence_L3.csv
  L3, P2L3     results/family_C_equivalence_psel4.csv (pipeline = pick)
QCEC verdicts (results/family_C_equivalence_qcec.csv and the qcec_* rows of
family_C_equivalence.csv) are not PyZX miter verdicts and are not used; the
report lists whether they would change any pick.

Run: python3 value/psel4_conservative.py
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDS = ["P0", "P2", "L3", "P2L3"]
TIE_ORDER = {"P0": 0, "L3": 1, "P2": 2, "P2L3": 3}  # pipelines/pass_select.TIE_ORDER
FAMILIES = ["A", "B1", "C", "usecase"]
OUT_MD = os.path.join(ROOT, "value", "psel4_conservative.md")
OUT_CSV = os.path.join(ROOT, "value", "psel4_conservative.csv")
FLAG = "default, unverified"

STATUS_MAP = [
    ("stored", "A, B1", "P0, P2",
     "joined to results/family_A_counts.csv / family_B1_counts.csv: status ok, check_ok True, "
     "unitary check up to 8 qubits, statevector beyond", "verified if the joined row passed"),
    ("ok", "usecase", "P0, P2", "value/usecase.csv, compile_select exactness check passed", "verified"),
    ("ok", "A, usecase", "L3, P2L3", "value/psel4_runs.csv, compile_select exactness check passed "
     "(check_max_qubits 12)", "verified"),
    ("ok", "B1", "L3, P2L3", "results/strong_baselines.csv, check_ok True", "verified"),
    ("ok-unchecked", "C", "L3, P2L3", "no check run", "not verified"),
    ("stored:pass", "C", "P0, P2", "64 random basis inputs agree (family_C_selector.py), "
     "not a unitary or state check", "not verified"),
    ("stored:unchecked-branching", "C", "P0, P2", "no check", "not verified"),
    ("timeout", "B1", "P2L3", "no output", "not a candidate"),
]


def _p(*a):
    return os.path.join(ROOT, *a)


def ledger():
    return pd.read_csv(_p("value", "psel4_ledger.csv"))


def stored_checks(d):
    """(file, pipeline) -> True for A/B1 'stored' rows whose source check passed."""
    src = pd.concat([pd.read_csv(_p("results", "family_A_counts.csv")).assign(family="A"),
                     pd.read_csv(_p("results", "family_B1_counts.csv")).assign(family="B1")])
    out = {}
    for r in d[d.family.isin(["A", "B1"])].itertuples():
        for c in ("P0", "P2"):
            assert getattr(r, f"status_{c}") == "stored", (r.file, c)
            m = src[(src.family == r.family) & (src.file == r.file) & (src.pipeline == c)]
            m = m[(m.hqc - getattr(r, f"hqc_{c}")).abs() < 1e-6]
            assert len(m) >= 1, ("no source row", r.family, r.file, c)
            kind = "unitary" if r.n_qubits <= 8 else "statevector"
            out[(r.file, c)] = bool(((m.status == "ok") & (m.check_ok == True)  # noqa: E712
                                     & (m.check_kind == kind)).all() and r.n_qubits <= 20)
    return out


def _assert_ok_sources(d):
    """The 'ok' statuses of L3/P2L3 and usecase P0/P2 come from checked rows."""
    runs = pd.read_csv(_p("value", "psel4_runs.csv"))
    sb = pd.read_csv(_p("results", "strong_baselines.csv"))
    uc = pd.read_csv(_p("value", "usecase.csv")).set_index("file")
    for r in d.itertuples():
        for c in ("L3", "P2L3"):
            if getattr(r, f"status_{c}") != "ok":
                continue
            if r.family in ("A", "usecase"):
                x = runs[(runs.family == r.family) & (runs.file == r.file) & (runs.variant == c)].iloc[-1]
                assert x.status == "ok" and np.isfinite(x.check_dev) and r.n_qubits <= 12, (r.file, c)
            else:
                x = sb[(sb.family == r.family) & (sb.file == r.file) & (sb.variant == c)].iloc[-1]
                assert x.status == "ok" and bool(x.check_ok), (r.file, c)
                assert x.check_kind == ("unitary" if r.n_qubits <= 8 else "statevector"), (r.file, c)
        if r.family == "usecase":
            u = uc.loc[r.file]
            assert u.check_kind == ("unitary" if r.n_qubits <= 8 else "statevector")
            assert u.status_P0 == r.status_P0 == "ok" and u.status_P2 == r.status_P2 == "ok"


def pyzx_proven():
    """set of (file, pipeline) with a PyZX miter verdict 'proven'."""
    s = set()
    e = pd.read_csv(_p("results", "family_C_equivalence.csv"))
    for r in e.itertuples():
        if r.comparison == r.pipeline and r.method == "pyzx" and r.verdict == "proven":
            s.add((r.file, r.pipeline))
    for r in pd.read_csv(_p("results", "family_C_equivalence_L3.csv")).itertuples():
        if r.method == "pyzx-miter" and r.verdict == "proven":
            s.add((r.file, "L3"))
    for r in pd.read_csv(_p("results", "family_C_equivalence_psel4.csv")).itertuples():
        if r.method == "pyzx-miter" and r.verdict == "proven":
            s.add((r.file, r.pick))
    return s


def other_proven():
    """(file, pipeline) proven by a non-PyZX method (QCEC), for the sensitivity note."""
    s = set()
    e = pd.read_csv(_p("results", "family_C_equivalence.csv"))
    for r in e.itertuples():
        if r.comparison == r.pipeline and r.method != "pyzx" and r.verdict == "proven":
            s.add((r.file, r.pipeline))
    q = pd.read_csv(_p("results", "family_C_equivalence_qcec.csv"))
    for r in q.itertuples():
        if r.verdict == "proven":
            s.add((r.file, r.candidate))
    return s


def verified_table(d):
    st = stored_checks(d)
    pz = pyzx_proven()
    _assert_ok_sources(d)
    known = {"stored", "ok", "ok-unchecked", "stored:pass", "stored:unchecked-branching", "timeout"}
    V = {}
    for r in d.itertuples():
        for c in CANDS:
            s = getattr(r, f"status_{c}")
            assert s in known, (r.file, c, s)
            h = getattr(r, f"hqc_{c}")
            if s == "timeout" or pd.isna(h):
                a = False
            elif s == "stored":
                a = st[(r.file, c)]
            elif s == "ok":
                a = r.n_qubits <= 20
            else:
                a = False
            b = (r.file, c) in pz
            V[(r.file, c)] = {"a": bool(a), "b": bool(b), "verified": bool(a or b),
                              "available": s != "timeout" and not pd.isna(h)}
    return V


def pick(r, ok):
    best = None
    for c in CANDS:
        if not ok(c):
            continue
        h = getattr(r, f"hqc_{c}")
        if pd.isna(h):
            continue
        key = (round(h, 9), getattr(r, f"n2q_{c}"), TIE_ORDER[c])
        if best is None or key < best[0]:
            best = (key, c)
    return None if best is None else best[1]


def pct(new, base):
    return 100.0 * (base - new) / base


def compute(extra_proven=frozenset()):
    d = ledger()
    V = verified_table(d)
    for k in extra_proven:
        if k in V and V[k]["available"]:
            V[k]["verified"] = True
    picks, flags, hq = [], [], []
    for r in d.itertuples():
        p = pick(r, lambda c: V[(r.file, c)]["verified"])
        if p is None:
            p, f = "P0", FLAG
        else:
            f = ""
        picks.append(p)
        flags.append(f)
        hq.append(getattr(r, f"hqc_{p}"))
    d["pick_cons"] = picks
    d["flag_cons"] = flags
    d["hqc_cons"] = hq
    for c in CANDS:
        d[f"ver_{c}"] = [V[(f, c)]["verified"] for f in d.file]
        d[f"ver_{c}_rule"] = ["a+b" if V[(f, c)]["a"] and V[(f, c)]["b"] else
                              "a" if V[(f, c)]["a"] else "b" if V[(f, c)]["b"] else "-" for f in d.file]
    # PSEL4 recomputed from the ledger statuses (sanity against the stored pick)
    okset = {"ok", "ok-unchecked", "stored"}
    d["pick_PSEL4_re"] = [pick(r, lambda c, r=r: isinstance(getattr(r, f"status_{c}"), str) and
                               (getattr(r, f"status_{c}") in okset or
                                getattr(r, f"status_{c}").startswith("stored"))) for r in d.itertuples()]
    return d


def summarise(d):
    tot = {k: float(d[f"hqc_{k}"].sum()) for k in ("P0", "L3", "PSEL4", "cons")}
    fam = []
    for f in FAMILIES + ["all"]:
        g = d if f == "all" else d[d.family == f]
        t = {k: float(g[f"hqc_{k}"].sum()) for k in ("P0", "L3", "PSEL4", "cons")}
        fam.append({"family": f, "n": len(g), **t,
                    "cons_vs_L2": pct(t["cons"], t["P0"]), "cons_vs_L3": pct(t["cons"], t["L3"]),
                    "psel4_vs_L2": pct(t["PSEL4"], t["P0"]), "psel4_vs_L3": pct(t["PSEL4"], t["L3"]),
                    "n_flag": int((g.flag_cons == FLAG).sum())})
    above_L2 = d[d.hqc_cons > d.hqc_P0 + 1e-9]
    above_L3 = d[d.hqc_cons > d.hqc_L3 + 1e-9]
    diff = d[d.pick_cons != d.pick_PSEL4]
    return {"tot": tot, "fam": pd.DataFrame(fam), "above_L2": above_L2, "above_L3": above_L3,
            "diff": diff, "flagged": d[d.flag_cons == FLAG],
            "save_L2": pct(tot["cons"], tot["P0"]), "save_L3": pct(tot["cons"], tot["L3"])}


def write_md(d, s, sens):
    tag = "`[F]`"
    L = ["# Conservative PSEL4: lowest HQC among verified candidates", "",
         "Generated by `python3 value/psel4_conservative.py` from `value/psel4_ledger.csv` and the PyZX "
         "miter verdicts in `results/family_C_equivalence*.csv`. No compilation. HQC at 1000 shots. "
         "Per-circuit rows: `value/psel4_conservative.csv`.", "",
         f"{tag} Rule. A candidate (P0, P2, L3, P2L3) counts as verified if (a) its ledger status is a passed "
         "full unitary check (up to 8 qubits) or a passed state check (9 to 20 qubits), or (b) a PyZX miter "
         "verdict \"proven\" exists for that circuit and pipeline. The variant keeps the verified candidate "
         "with the lowest HQC (ties as PSEL4: lower n_2q, then P0, L3, P2, P2L3). With no verified candidate "
         f"it keeps P0, the pytket-quantinuum default output, and flags the circuit \"{FLAG}\".", "",
         "`[O]` Rule (a) accepts numerical exactness checks, so this variant is not a proof-only selection.", "",
         "## Status mapping", "",
         "| ledger status | families | candidates | meaning (source) | counts as (a) |", "|---|---|---|---|---|"]
    for row in STATUS_MAP:
        L.append("| " + " | ".join(f"`{row[0]}`" if i == 0 else row[i] for i in range(5)) + " |")
    L += ["", f"{tag} `stored` is a placeholder written by `value/psel4_ledger.py` (load) for reused P0, P2 rows; "
          "the script joins each such row to its source counts row by file, pipeline and HQC and asserts the "
          "match. PyZX verdicts used: `family_C_equivalence.csv` rows with comparison = pipeline and method "
          "pyzx, `family_C_equivalence_L3.csv` (L3), `family_C_equivalence_psel4.csv` (the PSEL4 pick).", ""]
    n_ver = {c: int(d[f"ver_{c}"].sum()) for c in CANDS}
    L.append(f"{tag} Verified candidates out of {len(d)} circuits: " +
             ", ".join(f"{c} {n_ver[c]}" for c in CANDS) + ".")
    for f in FAMILIES:
        g = d[d.family == f]
        L.append(f"- {tag} {f} ({len(g)}): " + ", ".join(f"{c} {int(g[f'ver_{c}'].sum())}" for c in CANDS))
    t = s["tot"]
    L += ["", "## Totals", "",
          "| policy | total HQC | saving vs always L2 % | saving vs always L3 % |", "|---|---|---|---|"]
    for name, k in (("always L2 (P0)", "P0"), ("always L3", "L3"), ("PSEL4", "PSEL4"),
                    ("conservative PSEL4", "cons")):
        L.append(f"| {name} | {t[k]:.1f} | {pct(t[k], t['P0']):.2f} | {pct(t[k], t['L3']):.2f} |")
    L += ["", f"{tag} Saving % = 100 (base - policy) / base on totals over all {len(d)} circuits.", "",
          "## Per family", "",
          "| family | circuits | L2 | L3 | PSEL4 | conservative | cons. saving vs L2 % | cons. saving vs L3 % | "
          "PSEL4 saving vs L2 % | PSEL4 saving vs L3 % | flagged |", "|" + "---|" * 11]
    for r in s["fam"].itertuples():
        L.append(f"| {r.family} | {r.n} | {r.P0:.1f} | {r.L3:.1f} | {r.PSEL4:.1f} | {r.cons:.1f} | "
                 f"{r.cons_vs_L2:.2f} | {r.cons_vs_L3:.2f} | {r.psel4_vs_L2:.2f} | {r.psel4_vs_L3:.2f} | {r.n_flag} |")
    L += ["", "## Circuits where the conservative pick costs more than L2 or L3", ""]
    for lvl, key, col in (("L2", "above_L2", "P0"), ("L3", "above_L3", "L3")):
        x = s[key]
        L.append(f"{tag} Costlier than {lvl}: {len(x)} circuits.")
        if len(x):
            L += ["", f"| family | file | pick | HQC pick | HQC {lvl} | {lvl} output verified |", "|---|---|---|---|---|---|"]
            for r in x.itertuples():
                L.append(f"| {r.family} | {r.file} | {r.pick_cons} | {r.hqc_cons:.1f} | {getattr(r, f'hqc_{col}'):.1f} | "
                         f"{'yes' if getattr(r, f'ver_{col}') else 'no'} |")
        L.append("")
    x = s["diff"]
    L += ["## Picks that differ from PSEL4", "", f"{tag} {len(x)} circuits.", "",
          "| family | file | PSEL4 pick | PSEL4 HQC | conservative pick | conservative HQC | delta HQC | flag |",
          "|---|---|---|---|---|---|---|---|"]
    for r in x.itertuples():
        L.append(f"| {r.family} | {r.file} | {r.pick_PSEL4} | {r.hqc_PSEL4:.1f} | {r.pick_cons} | {r.hqc_cons:.1f} | "
                 f"{r.hqc_cons - r.hqc_PSEL4:+.1f} | {r.flag_cons} |")
    x = s["flagged"]
    L += ["", f"## Circuits flagged \"{FLAG}\"", "", f"{tag} {len(x)} circuits (pick = P0).", ""]
    for r in x.itertuples():
        L.append(f"- {tag} {r.family} `{r.file}` ({r.n_qubits} qubits), P0 HQC {r.hqc_P0:.1f}, PSEL4 {r.pick_PSEL4} "
                 f"{r.hqc_PSEL4:.1f}")
    L += ["", "## Notes", "",
          f"{tag} PSEL4 pick recomputed from the ledger statuses equals the stored `pick_PSEL4` on "
          f"{int((d.pick_PSEL4_re == d.pick_PSEL4).sum())} of {len(d)} circuits.",
          f"{tag} QCEC \"proven\" verdicts (not used): {', '.join(f'{f} {c}' for f, c in sorted(sens['keys'])) or 'none'}. "
          f"Counting them as well changes {sens['n_changed']} picks and the total by {sens['delta']:+.1f} HQC.",
          f"{tag} Counting `stored:pass` (64 random basis inputs) on the 20-qubit circuits as a state check "
          f"changes {sens['n_changed_pass20']} picks.", ""]
    with open(OUT_MD, "w") as fh:
        fh.write("\n".join(L))


def sensitivity(d):
    qs = other_proven()
    d2 = compute(extra_proven=frozenset(qs))
    pass20 = {(r.file, c) for r in d.itertuples() if r.family == "C" and r.n_qubits <= 20
              for c in ("P0", "P2") if getattr(r, f"status_{c}") == "stored:pass"}
    d3 = compute(extra_proven=frozenset(pass20))
    return {"keys": qs, "n_changed": int((d2.pick_cons != d.pick_cons).sum()),
            "delta": float(d2.hqc_cons.sum() - d.hqc_cons.sum()),
            "n_changed_pass20": int((d3.pick_cons != d.pick_cons).sum())}


def main():
    d = compute()
    s = summarise(d)
    sens = sensitivity(d)
    cols = ["family", "file", "n_qubits", "hqc_P0", "hqc_P2", "hqc_L3", "hqc_P2L3", "hqc_PSEL4", "pick_PSEL4",
            "pick_cons", "hqc_cons", "flag_cons"] + [f"ver_{c}_rule" for c in CANDS]
    d[cols].to_csv(OUT_CSV, index=False)
    write_md(d, s, sens)
    print(f"total cons {s['tot']['cons']:.1f}  vs L2 {s['save_L2']:.3f} %  vs L3 {s['save_L3']:.3f} %")
    print(s["fam"].to_string())
    print("above L2:", list(s["above_L2"].file), " above L3:", list(s["above_L3"].file))
    print("differ:", list(zip(s["diff"].file, s["diff"].pick_PSEL4, s["diff"].pick_cons)))
    print("flagged:", list(s["flagged"].file))
    print("sensitivity:", sens)


if __name__ == "__main__":
    main()
