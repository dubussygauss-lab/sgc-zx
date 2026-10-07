"""Exactness-barrier certificates (Corollary cert / Theorem C(c)) for the
benchmark circuits, joined with the ZX-stage T-counts of the compile runs.

Usage:  python3 barrier/run_certificates.py [--b2-only | --b1-only]

Inputs
  bench/family_B2/*.qasm            QSD+gridsynth Haar circuits, n = 2, 3
  bench/family_B1/{barenco_tof_3,mod5_4,qft_4,tof_3}.qasm   n = 5
  results/family_B2_counts.csv      t_count_after_zx for P1 (full_reduce) and
                                    P2 (teleport_reduce)
  results/family_B1_counts.csv      t_count_zx for P1 and P2
Outputs
  results/certificates.csv, results/certificates.md

Every number in the outputs is recomputed here from certificate.py and the
two counts CSVs.  The invariant floor <= T_zx (an exact rewrite cannot go
below the floor) is checked on every row and any violation is printed and
recorded in the column invariant_ok.
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import certificate as c  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B2_DIR = os.path.join(ROOT, "bench", "family_B2")
B1_DIR = os.path.join(ROOT, "bench", "family_B1")
B1_FILES = ["barenco_tof_3.qasm", "mod5_4.qasm", "qft_4.qasm", "tof_3.qasm"]
TIME_LIMIT = 30 * 60  # seconds per file; a file projected beyond this is not computed


def zx_counts_b2():
    out = {}
    with open(os.path.join(ROOT, "results", "family_B2_counts.csv")) as f:
        for r in csv.DictReader(f):
            if r["pipeline"] in ("P1", "P2") and r["status"] == "ok":
                out[(r["file"], r["pipeline"])] = int(float(r["t_count_after_zx"]))
    return out


def zx_counts_b1():
    out = {}
    with open(os.path.join(ROOT, "results", "family_B1_counts.csv")) as f:
        for r in csv.DictReader(f):
            if r["pipeline"] in ("P1", "P2") and r["status"] == "ok" and r["t_count_zx"]:
                out[(r["file"], r["pipeline"])] = int(float(r["t_count_zx"]))
    return out


def gate_set(word):
    return ",".join(sorted({name for name, _ in word}))


def run_file(path, family, zx):
    fn = os.path.basename(path)
    with open(path) as f:
        text = f.read()
    try:
        n, word = c.word_from_qasm(text)
    except ValueError as e:
        return {"family": family, "file": fn, "status": "skipped: %s" % e}
    t0 = time.time()
    r = c.certificate(word, n, compute_unitary=False)
    dt = time.time() - t0
    floor, tw = r["floor"], r["t_count"]
    row = {
        "family": family,
        "file": fn,
        "n": n,
        "gate_count": r["gate_count"],
        "gate_set": gate_set(word),
        "t_written": tw,
        "lde_floor": floor,
        "certified_incompressible_fraction": floor / tw if tw else 1.0,
        "max_removable_fraction": r["max_removable_fraction"],
        "collapse_count": r["collapse_count"],
        "collapse_rate": r["collapse_rate"],
        "criterion_violations": len(r["criterion_violations"]),
        "sound": r["sound"],
        "wall_s": round(dt, 1),
        "status": "ok",
    }
    for p in ("P1", "P2"):
        tz = zx.get((fn, p))
        row["t_zx_%s" % p] = tz
        row["achieved_fraction_removed_%s" % p] = (1 - tz / tw) if (tz is not None and tw) else None
        row["floor_over_t_zx_%s" % p] = (floor / tz) if tz else None
    oks = [floor <= zx[(fn, p)] for p in ("P1", "P2") if (fn, p) in zx]
    row["invariant_ok"] = all(oks) if oks else None
    return row


def main(argv):
    jobs = []
    if "--b1-only" not in argv:
        for fn in sorted(os.listdir(B2_DIR)):
            if fn.endswith(".qasm"):
                jobs.append((os.path.join(B2_DIR, fn), "B2"))
    if "--b2-only" not in argv:
        for fn in B1_FILES:
            jobs.append((os.path.join(B1_DIR, fn), "B1"))
    zx = {}
    zx.update(zx_counts_b2())
    zx.update(zx_counts_b1())
    rows = []
    for path, fam in jobs:
        row = run_file(path, fam, zx)
        rows.append(row)
        print({k: row[k] for k in row if k not in ("gate_set",)}, flush=True)
        if row.get("status") == "ok" and row["invariant_ok"] is False:
            print("INVARIANT VIOLATION: floor %d > T_zx on %s" % (row["lde_floor"], row["file"]), flush=True)

    cols = ["family", "file", "n", "gate_count", "gate_set", "t_written", "lde_floor",
            "certified_incompressible_fraction", "max_removable_fraction", "collapse_count",
            "collapse_rate", "criterion_violations", "sound", "t_zx_P1", "t_zx_P2",
            "achieved_fraction_removed_P1", "achieved_fraction_removed_P2",
            "floor_over_t_zx_P1", "floor_over_t_zx_P2", "invariant_ok", "wall_s", "status"]
    out_csv = os.path.join(ROOT, "results", "certificates.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})

    def pct(x):
        return "" if x is None or x == "" else "%.2f" % (100 * x)

    lines = ["# Exactness-barrier certificates", "",
             "Floor = lde of the exact Pauli channel (Corollary cert, Theorem C(c) of "
             "papers/barrier/main.tex), computed by barrier/certificate.py from the QASM as "
             "written. T_zx = T-count after the ZX stage of P1 (PyZX full_reduce) and P2 "
             "(PyZX teleport_reduce), from results/family_B2_counts.csv (t_count_after_zx) "
             "and results/family_B1_counts.csv (t_count_zx). incomp. = floor / T_written; "
             "removable = 1 - floor / T_written; achieved = 1 - T_zx / T_written; "
             "floor/T_zx is the quantity the manuscript's Table tab:e6 calls incomp. "
             "Invariant: floor <= T_zx.", "",
             "| family | file | n | gates | T_written | floor | incomp. % | removable % | collapses | T_zx P1 | T_zx P2 | achieved % P1 | achieved % P2 | floor/T_zx % P2 | floor<=T_zx | wall s |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r.get("status") != "ok":
            lines.append("| %s | %s | | | | | | | | | | | | | %s | |" % (r["family"], r["file"], r["status"]))
            continue
        lines.append("| %s | %s | %d | %d | %d | %d | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
            r["family"], r["file"], r["n"], r["gate_count"], r["t_written"], r["lde_floor"],
            pct(r["certified_incompressible_fraction"]), pct(r["max_removable_fraction"]),
            r["collapse_count"], r["t_zx_P1"], r["t_zx_P2"],
            pct(r["achieved_fraction_removed_P1"]), pct(r["achieved_fraction_removed_P2"]),
            pct(r["floor_over_t_zx_P2"]), r["invariant_ok"], r["wall_s"]))
    ok_rows = [r for r in rows if r.get("status") == "ok"]
    viol = [r["file"] for r in ok_rows if r["invariant_ok"] is False]
    lines += ["", "Invariant floor <= T_zx: %d rows checked, %d violations%s." % (
        sum(1 for r in ok_rows if r["invariant_ok"] is not None), len(viol),
        (" (" + ", ".join(viol) + ")") if viol else "")]
    # per-configuration summary for B2
    groups = {}
    for r in ok_rows:
        if r["family"] == "B2":
            key = (r["n"], r["file"].split("_")[2])
            groups.setdefault(key, []).append(r)
    if groups:
        lines += ["", "## B2 per configuration (mean over instances, min in brackets)", "",
                  "| n | eps | N | mean T_written | mean incomp. % (floor/T_written) | mean floor/T_zx % (P2) | mean achieved % (P2) | mean collapse rate % |",
                  "|---|---|---|---|---|---|---|---|"]
        for key in sorted(groups):
            g = groups[key]
            N = len(g)
            inc = [100 * r["certified_incompressible_fraction"] for r in g]
            ftz = [100 * r["floor_over_t_zx_P2"] for r in g if r["floor_over_t_zx_P2"] is not None]
            ach = [100 * r["achieved_fraction_removed_P2"] for r in g if r["achieved_fraction_removed_P2"] is not None]
            cr = [100 * r["collapse_rate"] for r in g]
            lines.append("| %d | %s | %d | %.0f | %.2f [%.2f] | %.2f [%.2f] | %.2f | %.2f |" % (
                key[0], key[1].replace("eps", ""), N, sum(r["t_written"] for r in g) / N,
                sum(inc) / N, min(inc), sum(ftz) / N if ftz else float("nan"), min(ftz) if ftz else float("nan"),
                sum(ach) / N if ach else float("nan"), sum(cr) / N))
    with open(os.path.join(ROOT, "results", "certificates.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out_csv)


if __name__ == "__main__":
    main(sys.argv[1:])
