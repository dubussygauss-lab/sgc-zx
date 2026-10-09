"""Use case: end-to-end Grover instances compiled with the pass selector PSEL.

Inputs: bench/usecase/grover_d5.qasm, grover_d6.qasm and manifest.csv, written by
bench/usecase/build_usecase.py (Grover quant-ph/9605043, Barenco et al.
quant-ph/9503016 Lemma 7.2, Toffoli of Nielsen-Chuang Fig. 4.9).
Outputs: value/usecase.csv and value/usecase.md.  Every number is computed here.

Steps per instance
  1. Ideal output distribution of the written circuit by statevector
     (compile.probs); success probability = P(data register = marked item),
     ancilla leakage = P(any ancilla = 1).
  2. PSEL = pipelines/pass_select.compile_select(circ, shots=1000,
     candidates=("P0", "P2")); its exactness check is compile.check (unitary up
     to 8 qubits, statevector beyond, tolerance 1e-8).
  3. HQC at 1000 shots (compile.hqc, measure-all convention), saving
     hqc_P0 - hqc_PSEL.
  4. Shots within the 10,000 HQC team budget: one job (value_ledger formula
     floor((B - 5) 5000 / k)) and with at most 10,000 shots per job and a 5 HQC
     fee per job (value_by_application formula); k = (hqc_1000 - 5) 5000 / 1000.
  5. Expected marked-item hits = shots x ideal success probability (ideal, no
     noise).
  6. Model-predicted fidelity ratio F(PSEL)/F(P0) = exp(a (n2q_P0 - n2q_PSEL)),
     a = 1.1801e-3 per ZZ gate (results/proxy_h22e_fits.log line 77).
  7. T-count as written (t/tdg in the QASM) and after the ZX stage of P2
     (compile.zx_teleport_reduce_pz, compile.pyzx_tcount).

Run: python3 value/usecase.py
"""
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
import compile as C  # noqa: E402
import pass_select as PS  # noqa: E402
from pytket.qasm import circuit_from_qasm  # noqa: E402

BENCH = ROOT / "bench/usecase"
OUT_CSV = ROOT / "value/usecase.csv"
OUT_MD = ROOT / "value/usecase.md"
SHOTS = 1000
BUDGET = 10_000
JOB_SHOT_CAP = 10_000
JOB_FEE = 5
SLOPE_A = 1.1801e-3


def per_shot_weight(hqc_1000):
    return (hqc_1000 - JOB_FEE) * 5000 / SHOTS


def shots_one_job(hqc_1000, budget=BUDGET):
    return int(math.floor((budget - JOB_FEE) * 5000 / per_shot_weight(hqc_1000)))


def shots_capped(hqc_1000, budget=BUDGET, cap=JOB_SHOT_CAP):
    k = per_shot_weight(hqc_1000)
    full_cost = JOB_FEE + cap * k / 5000
    n_full = int(math.floor(budget / full_cost))
    rem = budget - n_full * full_cost
    last = int(math.floor((rem - JOB_FEE) * 5000 / k)) if rem > JOB_FEE else 0
    return n_full * cap + min(max(last, 0), cap)


def t_count_qasm(path):
    n = 0
    for line in Path(path).read_text().splitlines():
        op = line.split(" ")[0]
        if op in ("t", "tdg"):
            n += 1
    return n


def ideal_success(circ, n_data, w):
    p = C.probs(circ).reshape(2 ** n_data, -1)    # q[0] most significant
    return float(p[w, 0]), float(p[:, 1:].sum()), float(p[:, 0].sum())


def analyse(row):
    path = BENCH / row["file"]
    circ = circuit_from_qasm(str(path))
    d, w = int(row["n_data"]), int(row["marked"])
    p_succ, leak, _ = ideal_success(circ, d, w)
    checks = {}

    def check_fn(comp, ref):
        out = C.check(comp, ref)
        checks[len(checks)] = out
        return out
    _, rec = PS.compile_select(circ, shots=SHOTS, candidates=("P0", "P2"), check_fn=check_fn)
    cand = rec["candidates"]
    kinds = [checks[i]["check_kind"] for i in sorted(checks)]
    ch = rec["chosen"]
    h0, h2, hs = cand["P0"]["hqc"], cand["P2"]["hqc"], cand[ch]["hqc"]
    n0, n2, ns = cand["P0"]["n_2q"], cand["P2"]["n_2q"], cand[ch]["n_2q"]
    pz = C.zx_teleport_reduce_pz(circ)
    r = {
        "file": row["file"], "algorithm": row["algorithm"], "n_data": d,
        "n_qubits": circ.n_qubits, "iterations": int(row["iterations"]),
        "marked_bits": row["marked_bits"],
        "p_success_ideal_sv": p_succ,
        "p_success_ideal_formula": float(row["p_success_ideal_formula"]),
        "ancilla_leak_sv": leak,
        "t_count_written": t_count_qasm(path),
        "t_count_after_zx_P2": C.pyzx_tcount(pz),
        "check_kind": "/".join(sorted(set(kinds))),
        "status_P0": cand["P0"]["status"], "status_P2": cand["P2"]["status"],
        "check_dev_P0": cand["P0"]["check_dev"], "check_dev_P2": cand["P2"]["check_dev"],
        "chosen": ch,
        "n2q_P0": n0, "n2q_P2": n2, "n2q_PSEL": ns,
        "hqc_P0": h0, "hqc_P2": h2, "hqc_PSEL": hs,
        "hqc_saving": h0 - hs, "hqc_saving_pct": 100 * (h0 - hs) / h0,
        "shots_one_job_P0": shots_one_job(h0), "shots_one_job_PSEL": shots_one_job(hs),
        "shots_capped_P0": shots_capped(h0), "shots_capped_PSEL": shots_capped(hs),
    }
    r["extra_shots_capped"] = r["shots_capped_PSEL"] - r["shots_capped_P0"]
    r["extra_shots_capped_pct"] = 100 * r["extra_shots_capped"] / r["shots_capped_P0"]
    r["hits_ideal_P0"] = r["shots_capped_P0"] * p_succ
    r["hits_ideal_PSEL"] = r["shots_capped_PSEL"] * p_succ
    r["extra_hits_ideal"] = r["hits_ideal_PSEL"] - r["hits_ideal_P0"]
    r["dN2q"] = n0 - ns
    r["fid_ratio_model"] = math.exp(SLOPE_A * (n0 - ns))
    return r


def write_md(rows):
    L = ["# Use case: Grover search compiled with the pass selector PSEL", "",
         "Generated by `value/usecase.py` from `bench/usecase/*.qasm` (generator "
         "`bench/usecase/build_usecase.py`). Do not edit by hand.", "",
         "## Instances", "",
         "- `[F]` Grover search (arXiv:quant-ph/9605043) with one marked item among N = 2^d, "
         "k = floor(pi/4 sqrt(N)) iterations. Oracle and diffusion each use one C^(d-1)Z, built as "
         "H C^(d-1)X H with the C^m X of Barenco et al. (arXiv:quant-ph/9503016, Lemma 7.2): "
         "4(m-2) Toffolis and m-2 ancillas restored in any state. Each Toffoli is the 7-T, 6-CX "
         "network of Nielsen and Chuang (2000), Fig. 4.9.",
         "- `[F]` HQC uses `compile.hqc` at 1000 shots with every qubit measured, ancillas included.",
         "- `[O]` The Barenco construction is not T-optimal. Relative-phase Toffolis would lower "
         "the written T-count. The instances are kept as written in the cited sources.", "",
         "## Table", ""]
    cols = [("file", "file"), ("n_qubits", "qubits"), ("iterations", "k"),
            ("p_success_ideal_sv", "P_succ ideal"), ("t_count_written", "T written"),
            ("t_count_after_zx_P2", "T after ZX"), ("n2q_P0", "n2q P0"), ("n2q_P2", "n2q P2"),
            ("chosen", "PSEL pick"), ("hqc_P0", "HQC P0"), ("hqc_P2", "HQC P2"),
            ("hqc_PSEL", "HQC PSEL"), ("hqc_saving", "saving"), ("hqc_saving_pct", "saving %"),
            ("shots_capped_P0", "shots P0"), ("shots_capped_PSEL", "shots PSEL"),
            ("hits_ideal_P0", "hits P0 (ideal)"), ("hits_ideal_PSEL", "hits PSEL (ideal)"),
            ("fid_ratio_model", "F ratio (model)")]

    def fmt(k, v):
        if isinstance(v, float):
            if k.startswith("p_"):
                return f"{v:.6f}"
            if k == "fid_ratio_model":
                return f"{v:.4f}"
            if k.startswith("hits"):
                return f"{v:.1f}"
            if k.endswith("pct"):
                return f"{v:.2f}"
            return f"{v:.1f}"
        return str(v)
    L.append("| " + " | ".join(h for _, h in cols) + " |")
    L.append("|" + "---|" * len(cols))
    for r in rows:
        L.append("| " + " | ".join(fmt(k, r[k]) for k, _ in cols) + " |")
    L += ["", "## Findings", ""]
    for r in rows:
        L += [
            f"- `[F]` {r['file']}: ideal success probability by statevector "
            f"{r['p_success_ideal_sv']:.6f}, closed form sin^2((2k+1)theta) "
            f"{r['p_success_ideal_formula']:.6f}, ancilla leakage {r['ancilla_leak_sv']:.1e}.",
            f"- `[F]` {r['file']}: exactness check ({r['check_kind']}) deviation "
            f"{r['check_dev_P0']:.1e} for P0 and {r['check_dev_P2']:.1e} for P2, status "
            f"{r['status_P0']} and {r['status_P2']}. PSEL keeps {r['chosen']}.",
            f"- `[F]` {r['file']}: HQC at 1000 shots {r['hqc_P0']:.1f} (P0), {r['hqc_P2']:.1f} (P2), "
            f"{r['hqc_PSEL']:.1f} (PSEL). Saving {r['hqc_saving']:.1f} HQC, "
            f"{r['hqc_saving_pct']:.2f} % of P0. Two-qubit gates {r['n2q_P0']} to {r['n2q_PSEL']}.",
            f"- `[F]` {r['file']}: T-count {r['t_count_written']} as written, "
            f"{r['t_count_after_zx_P2']} after the ZX stage of P2.",
            f"- `[F]` {r['file']}: shots within {BUDGET:,} HQC (at most {JOB_SHOT_CAP:,} per job, "
            f"{JOB_FEE} HQC per job) {r['shots_capped_P0']} under P0 and {r['shots_capped_PSEL']} "
            f"under PSEL, {r['extra_shots_capped']} more ({r['extra_shots_capped_pct']:.2f} %). "
            f"Single-job formula: {r['shots_one_job_P0']} and {r['shots_one_job_PSEL']}.",
            f"- `[F]` {r['file']}: expected marked-item hits within the budget, ideal (noise-free) "
            f"success probability: {r['hits_ideal_P0']:.1f} under P0 and {r['hits_ideal_PSEL']:.1f} "
            f"under PSEL.",
            f"- `[O]` {r['file']}: model prediction, not a measurement. exp(a dN_2q) with "
            f"a = {SLOPE_A:.4e} and dN_2q = {r['dN2q']} gives F(PSEL)/F(P0) = "
            f"{r['fid_ratio_model']:.4f}. The slope was fitted on family B1 proxy data.",
        ]
    L += ["", "## Limits", "",
          "- `[O]` Hit counts use the ideal success probability. On hardware each hit count is "
          "multiplied by the device success probability, which is lower and is not modelled here.",
          "- `[F]` No platform job was run for these instances.", ""]
    OUT_MD.write_text("\n".join(L))


def main():
    with open(BENCH / "manifest.csv") as f:
        man = list(csv.DictReader(f))
    rows = [analyse(m) for m in man]
    with open(OUT_CSV, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (repr(v) if isinstance(v, float) else v) for k, v in r.items()})
    write_md(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
