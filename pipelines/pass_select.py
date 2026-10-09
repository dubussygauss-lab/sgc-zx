"""Pass selector: compile with every candidate pipeline, keep the lowest HQC.

compile_select(circ, shots=1000, candidates=("P0", "P2")) compiles `circ`
with each candidate through compile.compile_pipeline (unchanged), drops any
candidate that raises, leaves the native gate set or fails the exactness
check of compile.check, and returns the surviving compiled circuit with the
lowest HQC together with a record of every candidate.

HQC is compile.hqc(comp, shots, n_measure=n_qubits), the convention of
run_bench.py / run_bench_B.py (unmeasured circuit, measure-all appended at
submission).  n_2q = ZZPhase + ZZMax.

Tie-break: lower HQC, then lower n_2q, then the fixed order P0, L3, P2,
P2L3 (other names after these, in candidate order).  For the default
candidates ("P0", "P2") this is the original rule: P0 wins a full tie.

Candidate names: every pipeline of compile.compile_pipeline, plus
  L3    QuantinuumBackend("H2-1", QuantinuumAPIOffline()).get_compiled_circuit(
        circ, optimisation_level=3), as in pipelines/strong_baselines.py
  P2L3  compile.zx_teleport_reduce, then L3, as in strong_baselines.py (with
        its fixed-decimal rewrite of scientific-notation angles for pyzx,
        applied only inside the P2L3 call; P2 is unchanged)
PSEL4 = compile_select(..., candidates=PSEL4_CANDIDATES) with
PSEL4_CANDIDATES = ("P0", "P2", "L3", "P2L3").

Exactness check: compile.check(comp, circ), unitary up to 8 qubits and
statevector beyond.  Above `check_max_qubits` (default 20) no check is run;
such a candidate is kept and marked "ok-unchecked" in the record.

CLI: python3 pipelines/pass_select.py [--shots N] [--candidates P0,P2] [--psel4] <qasm files...>
(--psel4 sets the candidates to P0,P2,L3,P2L3)
prints one row per file.
"""

import argparse
import os
import re
import sys
from decimal import Decimal

from pytket import Circuit, OpType

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402

DEFAULT_CANDIDATES = ("P0", "P2")
PSEL4_CANDIDATES = ("P0", "P2", "L3", "P2L3")
TIE_ORDER = {"P0": 0, "L3": 1, "P2": 2, "P2L3": 3}
CHECK_MAX_QUBITS = 20

_BACKEND = None
_SCI = re.compile(r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?[eE][-+]?\d+)")


def backend():
    """Offline H2-1 backend (no network, no job), built once."""
    global _BACKEND
    if _BACKEND is None:
        from pytket.extensions.quantinuum import (QuantinuumAPIOffline,
                                                  QuantinuumBackend)
        _BACKEND = QuantinuumBackend(device_name="H2-1",
                                     api_handler=QuantinuumAPIOffline())
    return _BACKEND


def _tket_to_pyzx_fixed(circ):
    """compile._tket_to_pyzx with scientific-notation angles written as fixed
    decimals (copy of strong_baselines._tket_to_pyzx_fixed)."""
    qasm = C.circuit_to_qasm_str(circ)
    qasm = _SCI.sub(lambda m: format(Decimal(m.group(1)), "f"), qasm)
    return C.pyzx.Circuit.from_qasm(qasm)


def compile_candidate(name: str, circ: Circuit):
    """-> (compiled Circuit, timings) for any candidate name."""
    import time
    if name not in ("L3", "P2L3"):
        return C.compile_pipeline(name, circ)
    t0 = time.perf_counter()
    c = circ.copy()
    if name == "P2L3":
        orig = C._tket_to_pyzx
        C._tket_to_pyzx = _tket_to_pyzx_fixed
        try:
            c = C.zx_teleport_reduce(c)
        finally:
            C._tket_to_pyzx = orig
    t1 = time.perf_counter()
    comp = backend().get_compiled_circuit(c, optimisation_level=3)
    t2 = time.perf_counter()
    return comp, {"t_zx": t1 - t0, "t_tket": t2 - t1, "t_total": t2 - t0}


def n_2q(circ: Circuit) -> int:
    return (circ.n_gates_of_type(OpType.ZZPhase)
            + circ.n_gates_of_type(OpType.ZZMax))


def _key(name: str, rec: dict, order: int):
    return (round(rec["hqc"], 9), rec["n_2q"], TIE_ORDER.get(name, len(TIE_ORDER)), order)


def compile_select(circ: Circuit, shots: int = 1000,
                   candidates=DEFAULT_CANDIDATES,
                   check_max_qubits: int = CHECK_MAX_QUBITS,
                   compile_fn=None, check_fn=None):
    """-> (compiled Circuit or None, record).

    record = {"chosen": name or None,
              "candidates": {name: {"status", "hqc", "n_2q", "check_dev",
                                    "error"}}}
    status is "ok", "ok-unchecked", "dropped-error", "dropped-non-native" or
    "dropped-check".  compile_fn(name, circ) -> (Circuit, timings) and
    check_fn(comp, circ) -> dict with "check_ok", "check_dev" default to
    compile_candidate and compile.check (hooks for tests)."""
    if compile_fn is None:
        compile_fn = compile_candidate
    if check_fn is None:
        check_fn = lambda comp, ref: C.check(comp, ref)  # noqa: E731
    if circ.n_gates_of_type(OpType.Measure):
        raise ValueError("compile_select expects an unmeasured circuit")

    record = {"chosen": None, "candidates": {}}
    kept = {}
    for name in candidates:
        rec = {"status": None, "hqc": float("nan"), "n_2q": None,
               "check_dev": float("nan"), "error": ""}
        record["candidates"][name] = rec
        try:
            comp, _ = compile_fn(name, circ)
            rec["hqc"] = C.hqc(comp, shots=shots, n_measure=comp.n_qubits)
            rec["n_2q"] = n_2q(comp)
            types = {cmd.op.type for cmd in comp.get_commands()}
            bad = types - C.NATIVE - {OpType.Barrier}
            if bad:
                rec["status"] = "dropped-non-native"
                rec["error"] = ",".join(sorted(t.name for t in bad))
                continue
            if comp.n_qubits > check_max_qubits:
                rec["status"] = "ok-unchecked"
            else:
                ck = check_fn(comp, circ)
                rec["check_dev"] = ck["check_dev"]
                if not ck["check_ok"]:
                    rec["status"] = "dropped-check"
                    continue
                rec["status"] = "ok"
        except Exception as e:  # noqa: BLE001 - any failure drops the candidate
            rec["status"] = "dropped-error"
            rec["error"] = f"{type(e).__name__}: {e}"
            continue
        kept[name] = comp

    if not kept:
        return None, record
    order = {n: i for i, n in enumerate(candidates)}
    best = min(kept, key=lambda n: _key(n, record["candidates"][n], order[n]))
    record["chosen"] = best
    return kept[best], record


def main(argv=None):
    from pytket.qasm import circuit_from_qasm
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--candidates", default=",".join(DEFAULT_CANDIDATES))
    ap.add_argument("--psel4", action="store_true",
                    help="candidates P0,P2,L3,P2L3 (PSEL4)")
    a = ap.parse_args(argv)
    cands = PSEL4_CANDIDATES if a.psel4 else tuple(a.candidates.split(","))
    cols = ["file", "n_qubits", "chosen", "hqc"]
    for p in cands:
        cols += [f"hqc_{p}", f"n2q_{p}", f"status_{p}"]
    print("\t".join(cols))
    for path in a.files:
        circ = circuit_from_qasm(path)
        _, rec = compile_select(circ, shots=a.shots, candidates=cands)
        ch = rec["chosen"]
        row = [os.path.basename(path), str(circ.n_qubits), str(ch),
               f"{rec['candidates'][ch]['hqc']:.1f}" if ch else "nan"]
        for p in cands:
            r = rec["candidates"][p]
            row += [f"{r['hqc']:.1f}", str(r["n_2q"]), r["status"]]
        print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
