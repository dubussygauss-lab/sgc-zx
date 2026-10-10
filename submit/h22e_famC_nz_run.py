"""H2-2E run of vbe_adder_7 on the non-zero input a = 28, b = 111 (P0 and L3).

Pre-registration: results/h22e_nonzero_prereg.md (committed before submission).

Input circuit  bench/family_C_nz/vbe_adder_7_nz.qasm  = bench/family_C/vbe_adder_7.qasm
               with X on q[3,4,5] (a = 28) and q[8,9,10,11,13,14] (b = 111) after `qreg`.
Expected       0001110011010001000000 (c[0] first), see the pre-registration.

Steps
  --compile   compile the input circuit with P0 (compile.compile_pipeline) and L3
              (pass_select.compile_candidate, optimisation_level=3), append
              measure-all, write results/compiled/<P0|L3>/vbe_adder_7_nz.qasm,
              check the H2 native gate set and that the ideal output of each
              stored QASM is the single expected bitstring; print n_2q and HQC.
  --submit    one aqora job per pipeline on nexus:H2-2E (1000 shots, noisy),
              submitted without waiting (submit_only); refuses if the ledger already has a
              row for this file and pipeline, or a result JSON exists, or the
              HQC total is 700 or more.  Needs EMU_RUN_TAG=famC_nz.
  --fetch ID  fetch an already submitted job with fetch_job.main (no resubmission).

The new file is not in bench/family_C/manifest.csv, so install() adds it to
common.list_family("C") and points common.reference_probs at the input-prepared
circuit (simulated by bench/sv.py, as for the earlier family C run).
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FILE = "vbe_adder_7_nz.qasm"
SRC = common.ROOT / "bench" / "family_C_nz" / FILE
EXPECTED = "0001110011010001000000"
A, B = 28, 111
PIPELINES = ("P0", "L3")
PLATFORM = "nexus:H2-2E"
SHOTS = 1000
RUN_TAG = "famC_nz"
HQC_LIMIT = 700.0


def expected_from_arithmetic(a: int = A, b: int = B) -> str:
    bits = [0] * 22
    s = a + b
    for i in range(7):
        bits[1 + i] = (a >> i) & 1
        bits[8 + i] = (s >> i) & 1
    bits[15] = (s >> 7) & 1
    return "".join(map(str, bits))


def input_probs() -> np.ndarray:
    if str(common.ROOT / "bench") not in sys.path:
        sys.path.insert(0, str(common.ROOT / "bench"))
    import sv
    return sv.probabilities(sv.run_qasm(SRC.read_text())).reshape(-1)


_REF = {}


def install():
    """Make common / run_emulator / fetch_job know the input-prepared file."""
    orig_list, orig_ref = common.list_family, common.reference_probs

    def list_family(family, max_n=None):
        out = orig_list(family, max_n)
        if family == "C":
            out.append(dict(file=FILE, model=FILE[:-5], n=22, r="", disorder="", instance=""))
        return out

    def reference_probs(family, file):
        if family == "C" and file == FILE:
            if "p" not in _REF:
                _REF["p"] = input_probs()
            return _REF["p"]
        return orig_ref(family, file)

    common.list_family = list_family
    common.reference_probs = reference_probs


def compile_all():
    sys.path.insert(0, str(common.ROOT / "pipelines"))
    import compile as C
    import pass_select as PS
    from pytket.qasm import circuit_from_qasm, circuit_to_qasm_str
    circ = circuit_from_qasm(str(SRC))
    out = {}
    for pipe in PIPELINES:
        if pipe == "P0":
            comp, _ = C.compile_pipeline("P0", circ)
        else:
            comp, _ = PS.compile_candidate("L3", circ)
        qasm = circuit_to_qasm_str(C.add_measure_all(comp), header="hqslib1", maxwidth=64)
        p = common.compiled_path(pipe, FILE)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(qasm)
        out[pipe] = p
    return out


def check_compiled(pipe: str) -> dict:
    circ = common.load_compiled(pipe, FILE)          # raises on non-native ops / missing measures
    pr = common.exact_probs(pipe, FILE)
    nz = np.flatnonzero(pr > 1e-9)
    st = common.circuit_stats(pipe, FILE)
    return {"pipeline": pipe, "n_qubits": circ.n_qubits, "n_2q": st["n_2q"],
            "hqc": common.hqc_estimate(circ, SHOTS), "native": not common.native_violations(circ),
            "support": len(nz), "ideal_out": format(int(nz[0]), "022b") if len(nz) else None,
            "p_expected": float(pr[int(EXPECTED, 2)])}


def submit_only(qpu, it):
    """First half of run_emulator.run_job: ledger row SUBMITTING, QPU.run,
    ledger row SUBMITTED with the job id.  The counts are collected with
    fetch_job.main, which scores, saves and updates the ledger exactly as
    run_job does, so the two jobs queue together instead of one after the other."""
    options = {"noisy_simulation": True}
    k = common.append_ledger(dict(platform=PLATFORM, family="C", file=FILE, pipeline=it["pipeline"],
                                  shots=SHOTS, options=options, status="SUBMITTING"))
    key = {c: k[c] for c in ("timestamp", "platform", "file", "pipeline")}
    try:
        job = qpu.run([it["circ"]], shots=SHOTS, options=options)
    except Exception as e:  # noqa: BLE001
        common.update_ledger(key, status="SUBMIT_ERROR:" + repr(e)[:200])
        raise
    common.update_ledger(key, job_id=job.job_id, status="SUBMITTED")
    print("submitted job %s (%s) at %s" % (job.job_id, it["pipeline"], common.now_iso()))
    return job.job_id


def ledger_rows():
    return [r for r in common.read_ledger() if r.get("file") == FILE]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--compile", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--submit", action="store_true")
    g.add_argument("--fetch", metavar="JOB_ID")
    ap.add_argument("--timeout", type=float, default=1800.0)
    ap.add_argument("--poll", type=float, default=30.0)
    a = ap.parse_args(argv)
    assert expected_from_arithmetic() == EXPECTED
    if a.compile:
        compile_all()
    if a.compile or a.check or a.submit:
        recs = [check_compiled(p) for p in PIPELINES]
        for r in recs:
            print(r)
            assert r["native"] and r["support"] == 1 and r["ideal_out"] == EXPECTED, r
        total = sum(r["hqc"] for r in recs)
        print("HQC total %.1f (limit %.0f)" % (total, HQC_LIMIT))
        assert total < HQC_LIMIT
    if a.submit or a.fetch:
        if os.environ.get("EMU_RUN_TAG", "") != RUN_TAG:
            raise SystemExit("set EMU_RUN_TAG=%s" % RUN_TAG)
        install()
    if a.submit:
        prior = ledger_rows()
        if prior:
            raise SystemExit("ledger already has rows for %s: %s" % (FILE, [(r["pipeline"], r["job_id"], r["status"]) for r in prior]))
        meta = [m for m in common.list_family("C") if m["file"] == FILE][0]
        qpu = common.make_qpu(PLATFORM)
        for pipe in PIPELINES:
            if common.result_path(PLATFORM, pipe, FILE).is_file():
                raise SystemExit("result exists for %s" % pipe)
            if any(r["pipeline"] == pipe for r in ledger_rows()):
                raise SystemExit("ledger already has %s" % pipe)
            circ = common.load_compiled(pipe, FILE)
            it = dict(meta=meta, file=FILE, pipeline=pipe, n=22, hqc=common.hqc_estimate(circ, SHOTS), circ=circ)
            print("submitting %s %s hqc %.1f" % (pipe, FILE, it["hqc"]))
            submit_only(qpu, it)
        print("both jobs submitted; collect with --fetch <job id> (fetch_job.main), one at a time")
    if a.fetch:
        import fetch_job
        fetch_job.main(["--job-id", a.fetch, "--family", "C", "--timeout", str(a.timeout), "--poll", str(a.poll)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
