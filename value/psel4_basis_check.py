"""Basis-input exactness check of PSEL4 candidates, 9 to 20 qubits.

Verification run, not a ledger rewrite: value/psel4_ledger.csv is read and
never written.

For every circuit of value/psel4_ledger.csv with 9 <= n_qubits <= 20:
  - every candidate P0, P2, L3, P2L3 is recompiled with
    pipelines/pass_select.compile_candidate, except a candidate whose ledger
    status is "timeout" (not recompiled, reported "skipped-ledger-timeout");
  - the recompiled HQC at 1000 shots is compared with the ledger HQC
    (hqc_match: |difference| <= 0.05, the ledger HQC is printed to 0.1);
  - pass_select.basis_check_many compares each recompiled candidate with the
    input circuit on K = 64 computational basis inputs (seed 20261010, drawn
    without replacement, all-zero input included), equality up to one global
    phase common to all inputs, tolerance compile.CHECK_TOL (1e-8), implicit
    qubit permutation applied as compile.statevector applies it.
Required set per circuit (the headline): the PSEL4 pick, plus every
candidate whose ledger status is "ok", "ok-unchecked" or contains "pass".
The other candidates (ledger status "stored", i.e. P0 / P2 reused from an
earlier ledger) are checked too and reported separately.

Run:  python3 value/psel4_basis_check.py run [--workers 2]
      python3 value/psel4_basis_check.py report
Output: value/psel4_basis_check.csv, value/psel4_basis_check.md
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
import compile as C  # noqa: E402
import pass_select as PS  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

LEDGER = ROOT / "value/psel4_ledger.csv"
OUT_CSV = ROOT / "value/psel4_basis_check.csv"
OUT_MD = ROOT / "value/psel4_basis_check.md"
DIRS = {"A": ROOT / "bench/family_A", "B1": ROOT / "bench/family_B1",
        "C": ROOT / "bench/family_C", "usecase": ROOT / "bench/usecase"}
CANDS = list(PS.PSEL4_CANDIDATES)
SHOTS = 1000
NMIN, NMAX = 9, 20
HQC_MATCH_TOL = 0.05


def required(row: dict, cand: str) -> bool:
    st = str(row[f"status_{cand}"])
    return cand == row["pick_PSEL4"] or st in ("ok", "ok-unchecked") or "pass" in st


def check_circuit(row: dict, k: int = PS.BASIS_K, seed: int = PS.BASIS_SEED,
                  compile_fn=None, extra: dict = None, skip=()) -> dict:
    """One output row for a ledger row.  compile_fn(name, circ) defaults to
    PS.compile_candidate; extra {name: Circuit} adds candidates (tests);
    candidates in skip are not run (reported "skipped-time-budget")."""
    compile_fn = compile_fn or PS.compile_candidate
    t0 = time.perf_counter()
    circ = circuit_from_qasm(str(DIRS[row["family"]] / row["file"]))
    out = {"family": row["family"], "file": row["file"], "n_qubits": circ.n_qubits,
           "pick_PSEL4": row["pick_PSEL4"]}
    comps = {}
    for c in CANDS:
        st = str(row[f"status_{c}"])
        out[f"ledger_status_{c}"] = st
        out[f"required_{c}"] = required(row, c)
        out[f"hqc_ledger_{c}"] = row[f"hqc_{c}"]
        out[f"hqc_recomp_{c}"] = float("nan")
        out[f"hqc_match_{c}"] = ""
        out[f"dev_{c}"] = float("nan")
        out[f"max_infid_{c}"] = float("nan")
        out[f"error_{c}"] = ""
        if st == "timeout":
            out[f"basis_{c}"] = "skipped-ledger-timeout"
            continue
        if c in skip:
            out[f"basis_{c}"] = "skipped-time-budget"
            continue
        try:
            comp, _ = compile_fn(c, circ)
        except Exception as e:  # noqa: BLE001
            out[f"basis_{c}"] = "compile-error"
            out[f"error_{c}"] = f"{type(e).__name__}: {e}"[:200]
            continue
        h = C.hqc(comp, shots=SHOTS, n_measure=comp.n_qubits)
        out[f"hqc_recomp_{c}"] = h
        try:
            out[f"hqc_match_{c}"] = bool(abs(h - float(row[f"hqc_{c}"])) <= HQC_MATCH_TOL)
        except (TypeError, ValueError):
            out[f"hqc_match_{c}"] = ""
        comps[c] = comp
    for name, comp in (extra or {}).items():
        comps[name] = comp
    res = PS.basis_check_many(circ, comps, k, seed)
    n_inputs = 0
    for name, r in res.items():
        out[f"basis_{name}"] = "pass" if r["check_ok"] else "FAIL"
        out[f"dev_{name}"] = r["check_dev"]
        out[f"max_infid_{name}"] = r["max_infid"]
        if r["error"]:
            out[f"error_{name}"] = r["error"]
        n_inputs = max(n_inputs, r["n_inputs"])
    out["n_inputs"] = n_inputs
    out["seconds"] = time.perf_counter() - t0
    return out


SKIP = {}  # file -> candidates not run, from --skip FILE:CAND


def _job(row):
    try:
        return check_circuit(row, skip=SKIP.get(row["file"], ()))
    except Exception as e:  # noqa: BLE001
        return {"family": row["family"], "file": row["file"], "n_qubits": row["n_qubits"],
                "pick_PSEL4": row["pick_PSEL4"], "job_error": f"{type(e).__name__}: {e}"[:300]}


def rows_in_range():
    d = pd.read_csv(LEDGER)
    d = d[(d.n_qubits >= NMIN) & (d.n_qubits <= NMAX)]
    return d.to_dict("records")


def _warm():
    from pytket import Circuit
    c = Circuit(9)
    c.H(0).CX(0, 1).CCX(0, 1, 2)
    return c


def cmd_run(a):
    for item in a.skip:
        f, c = item.split(":")
        SKIP.setdefault(f, set()).add(c)
    rows = rows_in_range()
    # largest first: C (20 qubits), then by n_qubits and file size
    rows.sort(key=lambda r: (-r["n_qubits"], -(DIRS[r["family"]] / r["file"]).stat().st_size))
    partial = OUT_CSV.with_suffix(".partial.jsonl")
    done = {}
    if partial.exists() and not a.fresh:
        for line in partial.read_text().splitlines():
            r = json.loads(line)
            done[(r["family"], r["file"])] = r
    todo = [r for r in rows if (r["family"], r["file"]) not in done]
    print(f"{len(rows)} circuits in {NMIN}-{NMAX} qubits, {len(todo)} to run, "
          f"{a.workers} workers", flush=True)
    PS.basis_check(_warm(), _warm())  # compile the numba kernel once
    t0 = time.perf_counter()
    with mp.get_context("fork").Pool(a.workers, maxtasksperchild=1) as pool, \
            open(partial, "a") as fh:
        for r in pool.imap_unordered(_job, todo):
            done[(r["family"], r["file"])] = r
            fh.write(json.dumps(r, default=str) + "\n")
            fh.flush()
            st = " ".join(f"{c}={r.get(f'basis_{c}')}" for c in CANDS)
            print(f"[{time.perf_counter() - t0:7.1f}s] {r['family']} {r['file']} "
                  f"n={r['n_qubits']} pick={r['pick_PSEL4']} {st} "
                  f"{r.get('seconds', float('nan')):.1f}s {r.get('job_error', '')}", flush=True)
    order = {(r["family"], r["file"]): i for i, r in enumerate(rows_in_range())}
    df = pd.DataFrame(sorted(done.values(), key=lambda r: order[(r["family"], r["file"])]))
    df.to_csv(OUT_CSV, index=False)
    partial.unlink()
    print(f"wrote {OUT_CSV} ({len(df)} rows), {time.perf_counter() - t0:.0f}s")


def cmd_report(_a):
    df = pd.read_csv(OUT_CSV)
    led = rows_in_range()
    n_led = len(led)
    pick_status = [r[f"basis_{r['pick_PSEL4']}"] for r in df.to_dict("records")]
    n_pick_pass = sum(s == "pass" for s in pick_status)
    req, req_pass, other, other_pass, fails = 0, 0, 0, 0, []
    skipped, mism = [], []
    for r in df.to_dict("records"):
        for c in CANDS:
            st = r[f"basis_{c}"]
            if st in ("skipped-ledger-timeout", "skipped-time-budget", "compile-error"):
                skipped.append((r["family"], r["file"], c, st))
                continue
            if bool(r[f"required_{c}"]):
                req += 1
                req_pass += st == "pass"
            else:
                other += 1
                other_pass += st == "pass"
            if st != "pass":
                fails.append((r["family"], r["file"], c, st, r[f"dev_{c}"],
                              c == r["pick_PSEL4"], bool(r[f"required_{c}"])))
            if str(r[f"hqc_match_{c}"]) == "False":
                mism.append((r["family"], r["file"], c, r[f"hqc_ledger_{c}"], r[f"hqc_recomp_{c}"]))
    pick_fails = [f for f in fails if f[5]]
    tot_s = df.seconds.sum()
    L = ["# PSEL4 basis-input check, 9 to 20 qubits", "",
         "Generated by `python3 value/psel4_basis_check.py report` from `value/psel4_basis_check.csv` "
         "(run: `python3 value/psel4_basis_check.py run`). Verification run only: "
         "`value/psel4_ledger.csv` is not changed. No number is typed by hand.", ""]
    if pick_fails:
        L += ["## PSEL4 PICK FAILURES", ""]
        for f in pick_fails:
            L.append(f"- **{f[0]} `{f[1]}`: pick {f[2]} {f[3]} (check_dev {f[4]:.3e})**")
        L += ["", "The ledger is not changed by this run.", ""]
    L += ["## Headline", "",
          f"`[F]` PSEL4 picks that pass on {int(df.n_inputs.min())}"
          + ("" if df.n_inputs.min() == df.n_inputs.max() else f" to {int(df.n_inputs.max())}")
          + f" basis inputs: {n_pick_pass} of {len(df)} circuits with 9 to 20 qubits "
          f"({n_led} such circuits in the ledger).",
          f"`[F]` Required candidates (pick, or ledger status ok / ok-unchecked / containing pass) "
          f"that pass: {req_pass} of {req}.",
          f"`[F]` Other candidates (ledger status stored, checked in addition) that pass: "
          f"{other_pass} of {other}.",
          f"`[F]` Failures (any candidate): {len(fails)}."
          + ("" if not fails else " Listed below."),
          f"`[F]` Not checked: {len(skipped)} candidate(s): "
          + ("none" if not skipped else ", ".join(f"{s[0]} `{s[1]}` {s[2]} ({s[3]})" for s in skipped))
          + ".", ""]
    if fails:
        L += ["| family | file | candidate | status | check_dev | PSEL4 pick | required |",
              "|---|---|---|---|---|---|---|"]
        for f in fails:
            L.append(f"| {f[0]} | `{f[1]}` | {f[2]} | {f[3]} | {f[4]:.3e} | {f[5]} | {f[6]} |")
        L.append("")
    L += ["## Method", "",
          "`[F]` Check: `pipelines/pass_select.basis_check_many`. Inputs: `basis_inputs(n, 64, 20261010)`, "
          "the all-zero input plus 63 distinct nonzero inputs drawn without replacement with "
          "`numpy.random.default_rng(20261010)`, the same inputs for every candidate of a circuit. "
          "Per input x, o_x = <ref x|cand x>; phi = arg(sum_x o_x); check_dev = max_x 1 - Re(e^{-i phi} o_x)^2; "
          "pass iff check_dev <= `compile.CHECK_TOL` = %g, the tolerance of the all-zero check. "
          "The implicit qubit permutation of each compiled circuit is applied to its output state "
          "as `compile.statevector` applies it." % C.CHECK_TOL,
          "`[F]` Candidates are recompiled with `pass_select.compile_candidate`. Recompiled HQC "
          f"(1000 shots) against the ledger HQC (|diff| <= {HQC_MATCH_TOL}): "
          f"{len(mism)} mismatch(es)"
          + ("" if not mism else ": " + ", ".join(f"{m[0]} `{m[1]}` {m[2]} ledger {m[3]} recompiled {m[4]:.1f}" for m in mism))
          + ".",
          f"`[F]` Wall time: {tot_s:.0f} s summed over circuits (per-circuit seconds in the table).", "",
          "## Per circuit", "",
          "| family | file | n | pick | P0 | P2 | L3 | P2L3 | seconds |",
          "|---|---|---|---|---|---|---|---|---|"]

    def cell(r, c):
        s = r[f"basis_{c}"]
        return s if bool(r[f"required_{c}"]) else f"({s})"
    for r in df.to_dict("records"):
        L.append(f"| {r['family']} | `{r['file']}` | {r['n_qubits']} | {r['pick_PSEL4']} | "
                 + " | ".join(cell(r, c) for c in CANDS) + f" | {r['seconds']:.1f} |")
    L += ["", "Status in parentheses: candidate outside the required set (ledger status stored), "
          "checked in addition.", ""]
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L[:20]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--fresh", action="store_true", help="ignore a partial run")
    r.add_argument("--skip", action="append", default=[],
                   help="FILE:CAND, candidate not run (time budget); repeatable")
    sub.add_parser("report")
    a = ap.parse_args()
    {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
