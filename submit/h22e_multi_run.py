"""H2-2E run of cdkm_adder_10 and modadd_2n_10 on three non-zero inputs each (P0 vs the PSEL4 pick).

Pre-registration: results/h22e_multi_prereg.md (committed alone before any submission).

Circuits and pipelines (PSEL4 picks from value/psel4_ledger.csv)
  cdkm_adder_10  22 qubits  q[0] cin | q[1..10] a | q[11..20] b | q[21] cout     P0, L3
  modadd_2n_10   20 qubits  q[0..9] a | q[10..19] b                              P0, P2L3
Inputs  rng = numpy.random.default_rng(20261011); cdkm = rng.integers(1, 2**10, size=(3, 2)),
        then modadd = rng.integers(1, 2**10, size=(3, 2)) from the same generator; rows (a, b), cin = 0.
Files   bench/family_C_multi/<circuit>_i<k>.qasm = bench/family_C/<circuit>.qasm with X on the
        1-bits of a and b after `qreg` (k = 1, 2, 3 in draw order).

Steps
  --prepare   write the six input-prepared files, check that bench/sv.py gives a single
              basis state equal to the arithmetic result (no network).
  --compile   compile each file with P0 and the pick, append measure-all, write
              results/compiled/<pipeline>/<file>; then --check.
  --check     native gate set, one Measure per qubit, ideal output of the stored
              measured QASM = the expected bitstring, HQC (400 shots) total < 1900.
  --submit    after quick_check (files byte-identical to those --check passed, recorded in
              results/compiled/h22e_multi_checked.json), one aqora job per program on
              nexus:H2-2E (400 shots, noisy), submitted without waiting; refuses if the ledger has any row for these files, a
              result JSON exists, or the HQC total is 1900 or more. Needs EMU_RUN_TAG=famC_multi.
  --fetch-all collect every SUBMITTED ledger row of these files with fetch_job.main (no resubmission).
  --fetch ID  collect one job.

Compiled circuits carry the implicit qubit permutation of L3 / P2L3 in their
measurement map (compile.add_measure_all); exact_probs and the scorer read the
classical bits c[i], so the expected bitstring is the same for every pipeline.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SEED = 20261011
NBITS = 10
CIRCUITS = {  # name -> (n_qubits, PSEL4 pick, a offset, b offset, has cin/cout)
    "cdkm_adder_10": (22, "L3", 1, 11, True),
    "modadd_2n_10": (20, "P2L3", 0, 10, False),
}
ORDER = ("cdkm_adder_10", "modadd_2n_10")
PLATFORM = "nexus:H2-2E"
SHOTS = 400
RUN_TAG = "famC_multi"
HQC_LIMIT = 1900.0
IN_DIR = common.ROOT / "bench" / "family_C_multi"


def draw_inputs(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    return {c: [tuple(int(x) for x in r) for r in rng.integers(1, 2 ** NBITS, size=(3, 2))] for c in ORDER}


INPUTS = draw_inputs()


def pipelines(circuit: str) -> tuple:
    return ("P0", CIRCUITS[circuit][1])


def file_name(circuit: str, k: int) -> str:
    return "%s_i%d.qasm" % (circuit, k)


def programs() -> list:
    """[(circuit, k, a, b, file)] in draw order."""
    return [(c, k, a, b, file_name(c, k)) for c in ORDER for k, (a, b) in enumerate(INPUTS[c], start=1)]


def x_qubits(circuit: str, a: int, b: int) -> list:
    _, _, oa, ob, _ = CIRCUITS[circuit]
    return sorted([oa + i for i in range(NBITS) if (a >> i) & 1] + [ob + i for i in range(NBITS) if (b >> i) & 1])


def expected_bits(circuit: str, a: int, b: int) -> str:
    """Arithmetic result, character i = qubit q[i] = classical bit c[i]."""
    n, _, oa, ob, carry = CIRCUITS[circuit]
    s = a + b
    bits = [0] * n
    for i in range(NBITS):
        bits[oa + i] = (a >> i) & 1
        bits[ob + i] = (s >> i) & 1
    if carry:
        bits[n - 1] = (s >> NBITS) & 1
    return "".join(map(str, bits))


def prepared_text(circuit: str, a: int, b: int) -> str:
    lines = (common.ROOT / "bench" / "family_C" / (circuit + ".qasm")).read_text().splitlines()
    i = next(j for j, ln in enumerate(lines) if ln.startswith("qreg "))
    xs = ["x q[%d];" % q for q in x_qubits(circuit, a, b)]
    return "\n".join(lines[: i + 1] + xs + lines[i + 1:]) + "\n"


def sv_probs(file: str) -> np.ndarray:
    if str(common.ROOT / "bench") not in sys.path:
        sys.path.insert(0, str(common.ROOT / "bench"))
    import sv
    return sv.probabilities(sv.run_qasm((IN_DIR / file).read_text())).reshape(-1)


def prepare(write: bool = True, simulate: bool = True) -> list:
    """Write (or with write=False only compare) the input-prepared files; with
    simulate=True also check the bench/sv.py output (about a minute per file)."""
    IN_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for c, k, a, b, f in programs():
        p = IN_DIR / f
        txt = prepared_text(c, a, b)
        if write:
            p.write_text(txt)
        assert p.read_text() == txt, f
        e = expected_bits(c, a, b)
        if not simulate:
            out.append((c, k, a, b, f, e))
            continue
        pr = sv_probs(f)
        nz = np.flatnonzero(pr > 1e-9)
        n = CIRCUITS[c][0]
        assert len(nz) == 1 and format(int(nz[0]), "0%db" % n) == e and abs(pr[nz[0]] - 1) < 1e-9, (f, nz[:5])
        out.append((c, k, a, b, f, e))
    return out


_REF = {}


def install():
    """Make common / run_emulator / fetch_job know the input-prepared files."""
    orig_list, orig_ref = common.list_family, common.reference_probs
    files = {f: CIRCUITS[c][0] for c, _, _, _, f in programs()}
    expected = {f: expected_bits(c, a, b) for c, _, a, b, f in programs()}

    def list_family(family, max_n=None):
        out = orig_list(family, max_n)
        if family == "C":
            out += [dict(file=f, model=f[:-5], n=n, r="", disorder="", instance="") for f, n in files.items()]
        return out

    def reference_probs(family, file):
        # The ideal output of the input-prepared circuit as written: the single basis
        # state expected_bits, which prepare() checked against bench/sv.py (the
        # reference of the earlier family C runs) before the pre-registration.
        if family == "C" and file in files:
            if file not in _REF:
                p = np.zeros(2 ** files[file])
                p[int(expected[file], 2)] = 1.0
                _REF[file] = p
            return _REF[file]
        return orig_ref(family, file)

    common.list_family = list_family
    common.reference_probs = reference_probs


def compile_all():
    sys.path.insert(0, str(common.ROOT / "pipelines"))
    import compile as C
    import pass_select as PS
    from pytket.qasm import circuit_from_qasm, circuit_to_qasm_str
    for c, _, _, _, f in programs():
        circ = circuit_from_qasm(str(IN_DIR / f))
        for pipe in pipelines(c):
            if pipe == "P0":
                comp, _ = C.compile_pipeline("P0", circ)
            else:
                comp, _ = PS.compile_candidate(pipe, circ)
            qasm = circuit_to_qasm_str(C.add_measure_all(comp), header="hqslib1", maxwidth=64)
            p = common.compiled_path(pipe, f)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(qasm)
            print("compiled", pipe, f)


def check_compiled(circuit: str, file: str, pipe: str, expected: str) -> dict:
    circ = common.load_compiled(pipe, file)          # raises on non-native ops / missing measures
    pr = common.exact_probs(pipe, file)
    nz = np.flatnonzero(pr > 1e-9)
    st = common.circuit_stats(pipe, file)
    n = CIRCUITS[circuit][0]
    return {"circuit": circuit, "file": file, "pipeline": pipe, "n_qubits": circ.n_qubits, "n_2q": st["n_2q"],
            "hqc": common.hqc_estimate(circ, SHOTS), "native": not common.native_violations(circ),
            "support": len(nz), "ideal_out": format(int(nz[0]), "0%db" % n) if len(nz) else None,
            "expected": expected, "p_expected": float(pr[int(expected, 2)])}


def check_all() -> list:
    recs = []
    for c, k, a, b, f in programs():
        e = expected_bits(c, a, b)
        for pipe in pipelines(c):
            r = check_compiled(c, f, pipe, e)
            print(r)
            assert r["native"] and r["support"] == 1 and r["ideal_out"] == e and r["n_qubits"] == CIRCUITS[c][0], r
            recs.append(r)
    total = sum(r["hqc"] for r in recs)
    print("HQC total %.1f over %d programs (limit %.0f)" % (total, len(recs), HQC_LIMIT))
    assert total < HQC_LIMIT
    CHECKED.write_text(json.dumps({"%s/%s" % (r["pipeline"], r["file"]): _sha(r["pipeline"], r["file"]) for r in recs},
                                  indent=1, sort_keys=True) + "\n")
    return recs


CHECKED = common.ROOT / "results" / "compiled" / "h22e_multi_checked.json"


def _sha(pipe: str, file: str) -> str:
    return hashlib.sha256(common.compiled_path(pipe, file).read_bytes()).hexdigest()


def quick_check() -> float:
    """Before --submit: every compiled file is byte-identical to the one that passed
    check_all (sha256 in CHECKED), native, one Measure per qubit; HQC total < limit."""
    ok = json.loads(CHECKED.read_text())
    total = 0.0
    for c, _, _, _, f in programs():
        for pipe in pipelines(c):
            assert ok["%s/%s" % (pipe, f)] == _sha(pipe, f), (pipe, f)
            total += common.hqc_estimate(common.load_compiled(pipe, f), SHOTS)
    print("HQC total %.2f over %d programs (limit %.0f)" % (total, len(ok), HQC_LIMIT))
    assert len(ok) == 12 and total < HQC_LIMIT
    return total


def submit_only(qpu, file: str, pipe: str, circ):
    options = {"noisy_simulation": True}
    k = common.append_ledger(dict(platform=PLATFORM, family="C", file=file, pipeline=pipe,
                                  shots=SHOTS, options=options, status="SUBMITTING"))
    key = {c: k[c] for c in ("timestamp", "platform", "file", "pipeline")}
    try:
        job = qpu.run([circ], shots=SHOTS, options=options)
    except Exception as e:  # noqa: BLE001
        common.update_ledger(key, status="SUBMIT_ERROR:" + repr(e)[:200])
        raise
    common.update_ledger(key, job_id=job.job_id, status="SUBMITTED")
    print("submitted job %s (%s %s) at %s" % (job.job_id, file, pipe, common.now_iso()), flush=True)
    return job.job_id


def ledger_rows() -> list:
    files = {f for *_, f in programs()}
    return [r for r in common.read_ledger() if r.get("file") in files]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare", action="store_true")
    g.add_argument("--compile", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--submit", action="store_true")
    g.add_argument("--fetch-all", action="store_true")
    g.add_argument("--fetch", metavar="JOB_ID")
    ap.add_argument("--timeout", type=float, default=1800.0)
    ap.add_argument("--poll", type=float, default=30.0)
    a = ap.parse_args(argv)
    if a.prepare:
        for row in prepare():
            print(row)
        return 0
    prepare(write=False, simulate=False)
    if a.compile:
        compile_all()
    if a.compile or a.check:
        check_all()
    if a.submit:
        quick_check()
    if a.submit or a.fetch or a.fetch_all:
        if os.environ.get("EMU_RUN_TAG", "") != RUN_TAG:
            raise SystemExit("set EMU_RUN_TAG=%s" % RUN_TAG)
        install()
    if a.submit:
        prior = ledger_rows()
        if prior:
            raise SystemExit("ledger already has rows: %s" % [(r["file"], r["pipeline"], r["job_id"], r["status"]) for r in prior])
        for c, _, _, _, f in programs():
            for pipe in pipelines(c):
                if common.result_path(PLATFORM, pipe, f).is_file():
                    raise SystemExit("result exists for %s %s" % (f, pipe))
        qpu = common.make_qpu(PLATFORM)
        for c, _, _, _, f in programs():
            for pipe in pipelines(c):
                if any(r["pipeline"] == pipe and r["file"] == f for r in ledger_rows()):
                    raise SystemExit("ledger already has %s %s" % (f, pipe))
                submit_only(qpu, f, pipe, common.load_compiled(pipe, f))
        print("all jobs submitted; collect with --fetch-all")
    if a.fetch or a.fetch_all:
        import fetch_job
        ids = [a.fetch] if a.fetch else list(dict.fromkeys(r["job_id"] for r in ledger_rows() if r["status"] == "SUBMITTED"))
        for jid in ids:
            fetch_job.main(["--job-id", jid, "--family", "C", "--timeout", str(a.timeout), "--poll", str(a.poll)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
