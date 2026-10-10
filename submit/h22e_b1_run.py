"""H2-2E run of vbe_adder_3 (4 inputs) and hwb6 (3 inputs), non-zero inputs, P0 vs the PSEL4 pick.

Pre-registration: results/h22e_b1_prereg.md (committed alone before any submission).

Circuits and pipelines (PSEL4 picks from value/psel4_ledger.csv)
  vbe_adder_3  10 qubits  q[0] cin | a_i = q[1+3i] | b_i = q[2+3i] | c_{i+1} = q[3+3i] (i = 0, 1) | q[9] cout   P0, L3
  hwb6          7 qubits  reversible function on q[0..6] (hidden weighted bit, pyzx circuit as written)                   P0, P2L3
Inputs  rng = numpy.random.default_rng(20261012); vbe = rng.integers(1, 8, size=(4, 2)) rows (a, b), first draw;
        hwb6 = rng.integers(1, 128, size=3), second draw from the same generator (bit i of x -> q[i]).
Files   bench/family_B1_multi/<circuit>_i<k>.qasm = bench/family_B1/<circuit>.qasm with X on the 1-bits of the
        input after `qreg` (k in draw order).
Expected output  vbe_adder_3 by arithmetic (a unchanged, b <- (a + b) mod 8, q[9] = carry, cin and the carry
        ancillas q[3], q[6] back to 0); hwb6 by statevector simulation of the input-prepared circuit as written
        (bench/sv.py, cached), which must be a single basis state.

Steps
  --prepare   write the seven input-prepared files, check that bench/sv.py gives a single basis state
              (equal to the arithmetic result for vbe_adder_3), no network.
  --compile   compile each file with P0 and the pick, append measure-all, write
              results/compiled/<pipeline>/<file>; then --check.
  --check     native gate set, one Measure per qubit, ideal output of the stored measured QASM = the
              expected bitstring, HQC (400 shots) total <= 990.
  --submit    after quick_check (files byte-identical to those --check passed, recorded in
              results/compiled/h22e_b1_checked.json), one aqora job per program on nexus:H2-2E
              (400 shots, noisy), in the order of submission_order() (input by input, both arms of
              one input adjacent, vbe_adder_3 before hwb6), submitted without waiting; refuses if the
              ledger has any row for these files, a result JSON exists, or the HQC total exceeds 990.
              Needs EMU_RUN_TAG=famB1_multi.
  --fetch-all collect every SUBMITTED ledger row of these files with fetch_job.main (no resubmission).
  --fetch ID  collect one job.

Compiled circuits carry the implicit qubit permutation of L3 / P2L3 in their measurement map
(compile.add_measure_all); exact_probs and the scorer read the classical bits c[i], so the expected
bitstring is the same for every pipeline.
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

SEED = 20261012
CIRCUITS = {  # name -> (n_qubits, PSEL4 pick, number of inputs)
    "vbe_adder_3": (10, "L3", 4),
    "hwb6": (7, "P2L3", 3),
}
ORDER = ("vbe_adder_3", "hwb6")
VBE_A = (1, 4, 7)      # qubits holding a_0, a_1, a_2
VBE_B = (2, 5, 8)      # qubits holding b_0, b_1, b_2
VBE_COUT = 9
PLATFORM = "nexus:H2-2E"
FAMILY = "B1"
SHOTS = 400
RUN_TAG = "famB1_multi"
HQC_LIMIT = 990.0
IN_DIR = common.ROOT / "bench" / "family_B1_multi"
SRC_DIR = common.ROOT / "bench" / "family_B1"


def draw_inputs(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    vbe = [tuple(int(x) for x in r) for r in rng.integers(1, 8, size=(4, 2))]
    hwb = [(int(x),) for x in rng.integers(1, 128, size=3)]
    return {"vbe_adder_3": vbe, "hwb6": hwb}


INPUTS = draw_inputs()


def pipelines(circuit: str) -> tuple:
    return ("P0", CIRCUITS[circuit][1])


def file_name(circuit: str, k: int) -> str:
    return "%s_i%d.qasm" % (circuit, k)


def programs() -> list:
    """[(circuit, k, inp, file)] circuit by circuit, inputs in draw order; inp = (a, b) or (x,)."""
    return [(c, k, inp, file_name(c, k)) for c in ORDER for k, inp in enumerate(INPUTS[c], start=1)]


def submission_order() -> list:
    """[(circuit, k, inp, file, pipeline)]: input by input, both arms of one input adjacent,
    vbe_adder_3 i1 P0, i1 L3, hwb6 i1 P0, i1 P2L3, vbe i2 ..., vbe i4 last."""
    by = {(c, k): (c, k, inp, f) for c, k, inp, f in programs()}
    out = []
    for k in range(1, 5):
        for c in ORDER:
            if (c, k) in by:
                out += [by[(c, k)] + (pipe,) for pipe in pipelines(c)]
    return out


def x_qubits(circuit: str, inp: tuple) -> list:
    if circuit == "vbe_adder_3":
        a, b = inp
        return sorted([VBE_A[i] for i in range(3) if (a >> i) & 1] + [VBE_B[i] for i in range(3) if (b >> i) & 1])
    (x,) = inp
    return [i for i in range(7) if (x >> i) & 1]


def prepared_text(circuit: str, inp: tuple) -> str:
    lines = (SRC_DIR / (circuit + ".qasm")).read_text().splitlines()
    i = next(j for j, ln in enumerate(lines) if ln.startswith("qreg "))
    xs = ["x q[%d];" % q for q in x_qubits(circuit, inp)]
    return "\n".join(lines[: i + 1] + xs + lines[i + 1:]) + "\n"


def _sv():
    if str(common.ROOT / "bench") not in sys.path:
        sys.path.insert(0, str(common.ROOT / "bench"))
    import sv
    return sv


def sv_probs_text(text: str) -> np.ndarray:
    sv = _sv()
    return sv.probabilities(sv.run_qasm(text)).reshape(-1)


def sv_probs(file: str) -> np.ndarray:
    return sv_probs_text((IN_DIR / file).read_text())


_EXP = {}


def expected_bits(circuit: str, inp: tuple) -> str:
    """Expected output, character i = qubit q[i] = classical bit c[i].
    vbe_adder_3 by arithmetic; hwb6 by simulating the input-prepared circuit as written (single basis state)."""
    if circuit == "vbe_adder_3":
        a, b = inp
        s = a + b
        bits = [0] * 10
        for i in range(3):
            bits[VBE_A[i]] = (a >> i) & 1
            bits[VBE_B[i]] = (s >> i) & 1
        bits[VBE_COUT] = (s >> 3) & 1
        return "".join(map(str, bits))
    key = (circuit, inp)
    if key not in _EXP:
        pr = sv_probs_text(prepared_text(circuit, inp))
        nz = np.flatnonzero(pr > 1e-9)
        assert len(nz) == 1 and abs(pr[nz[0]] - 1) < 1e-9, (circuit, inp, nz[:5])
        _EXP[key] = format(int(nz[0]), "0%db" % CIRCUITS[circuit][0])
    return _EXP[key]


def prepare(write: bool = True, simulate: bool = True) -> list:
    """Write (or with write=False only compare) the input-prepared files; with
    simulate=True also check the bench/sv.py output of each file."""
    IN_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for c, k, inp, f in programs():
        p = IN_DIR / f
        txt = prepared_text(c, inp)
        if write:
            p.write_text(txt)
        assert p.read_text() == txt, f
        e = expected_bits(c, inp)
        if not simulate:
            out.append((c, k, inp, f, e))
            continue
        pr = sv_probs(f)
        nz = np.flatnonzero(pr > 1e-9)
        n = CIRCUITS[c][0]
        assert len(nz) == 1 and format(int(nz[0]), "0%db" % n) == e and abs(pr[nz[0]] - 1) < 1e-9, (f, nz[:5])
        out.append((c, k, inp, f, e))
    return out


_REF = {}


def install():
    """Make common / run_emulator / fetch_job know the input-prepared files."""
    orig_list, orig_ref = common.list_family, common.reference_probs
    files = {f: CIRCUITS[c][0] for c, _, _, f in programs()}
    expected = {f: expected_bits(c, inp) for c, _, inp, f in programs()}

    def list_family(family, max_n=None):
        out = orig_list(family, max_n)
        if family == FAMILY:
            out += [dict(file=f, model=f[:-5], n=n, r="", disorder="", instance="") for f, n in files.items()]
        return out

    def reference_probs(family, file):
        # The ideal output of the input-prepared circuit as written: the single basis
        # state expected_bits, which prepare() checked against bench/sv.py before the
        # pre-registration.
        if family == FAMILY and file in files:
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
    for c, _, _, f in programs():
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
    for c, k, inp, f in programs():
        e = expected_bits(c, inp)
        for pipe in pipelines(c):
            r = check_compiled(c, f, pipe, e)
            print(r)
            assert r["native"] and r["support"] == 1 and r["ideal_out"] == e and r["n_qubits"] == CIRCUITS[c][0], r
            recs.append(r)
    total = sum(r["hqc"] for r in recs)
    print("HQC total %.2f over %d programs (limit %.0f)" % (total, len(recs), HQC_LIMIT))
    assert total <= HQC_LIMIT
    CHECKED.write_text(json.dumps({"%s/%s" % (r["pipeline"], r["file"]): _sha(r["pipeline"], r["file"]) for r in recs},
                                  indent=1, sort_keys=True) + "\n")
    return recs


CHECKED = common.ROOT / "results" / "compiled" / "h22e_b1_checked.json"


def _sha(pipe: str, file: str) -> str:
    return hashlib.sha256(common.compiled_path(pipe, file).read_bytes()).hexdigest()


def quick_check() -> float:
    """Before --submit: every compiled file is byte-identical to the one that passed
    check_all (sha256 in CHECKED), native, one Measure per qubit; HQC total <= limit."""
    ok = json.loads(CHECKED.read_text())
    total = 0.0
    for c, _, _, f in programs():
        for pipe in pipelines(c):
            assert ok["%s/%s" % (pipe, f)] == _sha(pipe, f), (pipe, f)
            total += common.hqc_estimate(common.load_compiled(pipe, f), SHOTS)
    print("HQC total %.2f over %d programs (limit %.0f)" % (total, len(ok), HQC_LIMIT))
    assert len(ok) == 14 and total <= HQC_LIMIT
    return total


def submit_only(qpu, file: str, pipe: str, circ):
    options = {"noisy_simulation": True}
    k = common.append_ledger(dict(platform=PLATFORM, family=FAMILY, file=file, pipeline=pipe,
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
        for c, _, _, f, pipe in submission_order():
            if common.result_path(PLATFORM, pipe, f).is_file():
                raise SystemExit("result exists for %s %s" % (f, pipe))
        qpu = common.make_qpu(PLATFORM)
        for c, _, _, f, pipe in submission_order():
            if any(r["pipeline"] == pipe and r["file"] == f for r in ledger_rows()):
                raise SystemExit("ledger already has %s %s" % (f, pipe))
            submit_only(qpu, f, pipe, common.load_compiled(pipe, f))
        print("all jobs submitted; collect with --fetch-all")
    if a.fetch or a.fetch_all:
        import fetch_job
        ids = [a.fetch] if a.fetch else list(dict.fromkeys(r["job_id"] for r in ledger_rows() if r["status"] == "SUBMITTED"))
        for jid in ids:
            fetch_job.main(["--job-id", jid, "--family", FAMILY, "--timeout", str(a.timeout), "--poll", str(a.poll)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
