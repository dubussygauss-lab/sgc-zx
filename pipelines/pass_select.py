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

Exactness check (check(comp, circ, mode)):
  up to 8 qubits   compile.check: full unitary, 1 - |tr(U^dag V)| / 2^n.
  9 to `check_max_qubits` (default 20), mode "basis" (default): the output
                   states of comp and circ on K = 64 computational basis
                   inputs (fixed seed 20261010, drawn without replacement,
                   the all-zero input always included) must agree up to one
                   global phase common to all inputs (basis_check below).
  9 to `check_max_qubits`, mode "zero" (old behaviour, --check-zero):
                   compile.check, statevector on the all-zero input only.
  Tolerance: compile.CHECK_TOL, the tolerance of the all-zero check.  The
  implicit qubit permutation of L3 / P2L3 (allow_swaps=True) is applied to
  the output state exactly as compile.statevector does.
Above `check_max_qubits` no check is run; such a candidate is kept and marked
"ok-unchecked" in the record.

CLI: python3 pipelines/pass_select.py [--shots N] [--candidates P0,P2] [--psel4]
     [--check-zero] [--basis-k K] <qasm files...>
(--psel4 sets the candidates to P0,P2,L3,P2L3; --check-zero restores the
all-zero check for 9 to 20 qubits) prints one row per file.
"""

import argparse
import os
import re
import sys
from decimal import Decimal

import numba
import numpy as np
from pytket import Circuit, OpType

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402

DEFAULT_CANDIDATES = ("P0", "P2")
PSEL4_CANDIDATES = ("P0", "P2", "L3", "P2L3")
TIE_ORDER = {"P0": 0, "L3": 1, "P2": 2, "P2L3": 3}
CHECK_MAX_QUBITS = 20
UNITARY_MAX_QUBITS = 8
CHECK_MODES = ("basis", "zero")
DEFAULT_CHECK_MODE = "basis"
BASIS_K = 64
BASIS_SEED = 20261010

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


# ------------------------------------------------- basis-input exactness check

def basis_inputs(n: int, k: int = BASIS_K, seed: int = BASIS_SEED) -> np.ndarray:
    """K distinct computational basis inputs of n qubits as integers (ILO-BE,
    q[0] most significant): 0 first, then K-1 distinct nonzero inputs drawn
    without replacement with np.random.default_rng(seed).  All 2^n inputs
    when 2^n <= K."""
    total = 1 << n
    if total <= k:
        return np.arange(total, dtype=np.int64)
    rng = np.random.default_rng(seed)
    rest = rng.choice(total - 1, size=k - 1, replace=False).astype(np.int64) + 1
    return np.concatenate([np.zeros(1, dtype=np.int64), rest])


@numba.njit(cache=True)
def _run_gates(psi, us, pos, ks):
    """Apply gates in place.  Gate g acts on ks[g] <= 3 qubits at bit
    positions pos[g, :ks[g]] (pos[g, 0] = most significant index of the
    matrix, as in pytket's get_unitary) with matrix us[g, :d, :d]."""
    n_amp = psi.shape[0]
    tmp = np.empty(8, dtype=np.complex128)
    offs = np.empty(8, dtype=np.int64)
    srt = np.empty(3, dtype=np.int64)
    for g in range(us.shape[0]):
        k = ks[g]
        if k == 1:
            b = pos[g, 0]
            m = 1 << b
            u00, u01, u10, u11 = us[g, 0, 0], us[g, 0, 1], us[g, 1, 0], us[g, 1, 1]
            lo = m - 1
            for r in range(n_amp >> 1):
                i = ((r >> b) << (b + 1)) | (r & lo)
                a0 = psi[i]
                a1 = psi[i | m]
                psi[i] = u00 * a0 + u01 * a1
                psi[i | m] = u10 * a0 + u11 * a1
            continue
        if k == 2:
            b0 = pos[g, 0]
            b1 = pos[g, 1]
            m0 = 1 << b0  # matrix MSB
            m1 = 1 << b1
            lo_b = b0 if b0 < b1 else b1
            hi_b = b1 if b0 < b1 else b0
            for r in range(n_amp >> 2):
                i = ((r >> lo_b) << (lo_b + 1)) | (r & ((1 << lo_b) - 1))
                i = ((i >> hi_b) << (hi_b + 1)) | (i & ((1 << hi_b) - 1))
                a0 = psi[i]
                a1 = psi[i | m1]
                a2 = psi[i | m0]
                a3 = psi[i | m0 | m1]
                psi[i] = us[g, 0, 0] * a0 + us[g, 0, 1] * a1 + us[g, 0, 2] * a2 + us[g, 0, 3] * a3
                psi[i | m1] = us[g, 1, 0] * a0 + us[g, 1, 1] * a1 + us[g, 1, 2] * a2 + us[g, 1, 3] * a3
                psi[i | m0] = us[g, 2, 0] * a0 + us[g, 2, 1] * a1 + us[g, 2, 2] * a2 + us[g, 2, 3] * a3
                psi[i | m0 | m1] = (us[g, 3, 0] * a0 + us[g, 3, 1] * a1
                                    + us[g, 3, 2] * a2 + us[g, 3, 3] * a3)
            continue
        d = 1 << k
        for a in range(d):
            o = 0
            for j in range(k):
                if (a >> (k - 1 - j)) & 1:
                    o |= 1 << pos[g, j]
            offs[a] = o
        for j in range(k):
            srt[j] = pos[g, j]
        for j in range(k):  # insertion sort of the positions
            for m in range(j, 0, -1):
                if srt[m] < srt[m - 1]:
                    srt[m], srt[m - 1] = srt[m - 1], srt[m]
        for r in range(n_amp >> k):
            i = r
            for j in range(k):  # insert a zero bit at each gate position, lowest first
                b = srt[j]
                i = ((i >> b) << (b + 1)) | (i & ((1 << b) - 1))
            for a in range(d):
                tmp[a] = psi[i + offs[a]]
            for a in range(d):
                acc = 0j
                for b2 in range(d):
                    acc += us[g, a, b2] * tmp[b2]
                psi[i + offs[a]] = acc


class _Compiled:
    """Gate arrays of a pytket circuit for _run_gates, plus the output axis
    order of its implicit qubit permutation (as in compile.statevector)."""

    def __init__(self, circ: Circuit):
        qubits = list(circ.qubits)  # pytket order, ILO-BE: qubits[0] most significant
        n = len(qubits)
        ix = {q: i for i, q in enumerate(qubits)}
        cmds = [c for c in circ.get_commands() if c.op.type != OpType.Barrier]
        g = len(cmds)
        self.n = n
        self.qubits = qubits
        self.us = np.zeros((g, 8, 8), dtype=np.complex128)
        self.pos = np.zeros((g, 3), dtype=np.int64)
        self.ks = np.zeros(g, dtype=np.int64)
        for j, cmd in enumerate(cmds):
            qs = [ix[q] for q in cmd.args]
            k = len(qs)
            if k > 3:
                raise ValueError(f"{cmd.op.type.name} on {k} qubits not supported")
            u = cmd.op.get_unitary()
            self.us[j, :1 << k, :1 << k] = u
            self.pos[j, :k] = [n - 1 - i for i in qs]  # bit position of qubit i
            self.ks[j] = k
        perm = circ.implicit_qubit_permutation()
        order = [None] * n
        for q in qubits:
            order[ix[perm[q]]] = ix[q]
        self.order = order
        self.phase = complex(np.exp(1j * np.pi * float(circ.phase)))  # global phase, as get_unitary

    def state(self, x: int) -> np.ndarray:
        psi = np.zeros(1 << self.n, dtype=np.complex128)
        psi[int(x)] = 1.0
        _run_gates(psi, self.us, self.pos, self.ks)
        psi *= self.phase
        return np.transpose(psi.reshape((2,) * self.n), self.order).reshape(-1)


def statevector_from_basis(circ: Circuit, x: int) -> np.ndarray:
    """Output state of circ on basis input |x> (ILO-BE), with the implicit
    qubit permutation applied as compile.statevector applies it."""
    return _Compiled(circ).state(x)


def basis_check_many(ref: Circuit, cands: dict, k: int = BASIS_K,
                     seed: int = BASIS_SEED, tol: float = None) -> dict:
    """Compare every circuit of cands {name: Circuit} with ref on the inputs
    basis_inputs(n, k, seed).  Per input x: o_x = <ref x|cand x>.  phi =
    arg(sum_x o_x).  check_dev = max_x 1 - Re(e^{-i phi} o_x)^2 (1 when that
    real part is <= 0), which equals compile.state_infidelity on every input
    when all phases agree; check_ok = check_dev <= tol (compile.CHECK_TOL).
    Also reported: max_infid = max_x 1 - |o_x|^2 (per-input check without a
    common phase)."""
    tol = C.CHECK_TOL if tol is None else tol
    n = ref.n_qubits
    xs = basis_inputs(n, k, seed)
    R = _Compiled(ref)
    out, comp = {}, {}
    for name, c in cands.items():
        if set(c.qubits) != set(ref.qubits):
            out[name] = {"check_kind": f"basis{len(xs)}", "check_ok": False,
                         "check_dev": float("nan"), "max_infid": float("nan"),
                         "n_inputs": 0, "error": "qubit sets differ"}
        else:
            comp[name] = _Compiled(c)
    ov = {name: np.empty(len(xs), dtype=np.complex128) for name in comp}
    for j, x in enumerate(xs):
        r = R.state(x)
        for name, cc in comp.items():
            ov[name][j] = np.vdot(r, cc.state(x))
    for name, o in ov.items():
        s = o.sum()
        ph = s / abs(s) if abs(s) > 0 else 1.0
        re = np.real(o * np.conj(ph))
        dev = np.where(re > 0, 1 - re ** 2, 1.0)
        out[name] = {"check_kind": f"basis{len(xs)}",
                     "check_dev": float(dev.max()),
                     "max_infid": float((1 - np.abs(o) ** 2).max()),
                     "n_inputs": int(len(xs)),
                     "check_ok": bool(dev.max() <= tol), "error": ""}
    return out


def basis_check(comp: Circuit, ref: Circuit, k: int = BASIS_K,
                seed: int = BASIS_SEED) -> dict:
    """basis_check_many for one candidate."""
    return basis_check_many(ref, {"c": comp}, k, seed)["c"]


def check(comp: Circuit, ref: Circuit, mode: str = DEFAULT_CHECK_MODE,
          k: int = BASIS_K, seed: int = BASIS_SEED) -> dict:
    """Exactness check of comp against ref (module docstring)."""
    if mode not in CHECK_MODES:
        raise ValueError(f"check mode {mode!r} not in {CHECK_MODES}")
    if comp.n_qubits <= UNITARY_MAX_QUBITS or mode == "zero":
        return C.check(comp, ref, unitary_max_qubits=UNITARY_MAX_QUBITS)
    return basis_check(comp, ref, k, seed)


def n_2q(circ: Circuit) -> int:
    return (circ.n_gates_of_type(OpType.ZZPhase)
            + circ.n_gates_of_type(OpType.ZZMax))


def _key(name: str, rec: dict, order: int):
    return (round(rec["hqc"], 9), rec["n_2q"], TIE_ORDER.get(name, len(TIE_ORDER)), order)


def compile_select(circ: Circuit, shots: int = 1000,
                   candidates=DEFAULT_CANDIDATES,
                   check_max_qubits: int = CHECK_MAX_QUBITS,
                   compile_fn=None, check_fn=None,
                   check_mode: str = DEFAULT_CHECK_MODE, basis_k: int = BASIS_K):
    """-> (compiled Circuit or None, record).

    record = {"chosen": name or None,
              "candidates": {name: {"status", "hqc", "n_2q", "check_dev",
                                    "error"}}}
    status is "ok", "ok-unchecked", "dropped-error", "dropped-non-native" or
    "dropped-check".  compile_fn(name, circ) -> (Circuit, timings) and
    check_fn(comp, circ) -> dict with "check_ok", "check_dev" default to
    compile_candidate and check(comp, circ, check_mode, basis_k) (hooks for
    tests)."""
    if compile_fn is None:
        compile_fn = compile_candidate
    if check_fn is None:
        check_fn = lambda comp, ref: check(comp, ref, check_mode, basis_k)  # noqa: E731
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
    ap.add_argument("--check-zero", action="store_true",
                    help="9 to 20 qubits: old all-zero-input statevector check "
                         "instead of the basis-input check")
    ap.add_argument("--basis-k", type=int, default=BASIS_K,
                    help="number of basis inputs of the basis-input check")
    a = ap.parse_args(argv)
    mode = "zero" if a.check_zero else "basis"
    cands = PSEL4_CANDIDATES if a.psel4 else tuple(a.candidates.split(","))
    cols = ["file", "n_qubits", "chosen", "hqc"]
    for p in cands:
        cols += [f"hqc_{p}", f"n2q_{p}", f"status_{p}"]
    print("\t".join(cols))
    for path in a.files:
        circ = circuit_from_qasm(path)
        _, rec = compile_select(circ, shots=a.shots, candidates=cands,
                                check_mode=mode, basis_k=a.basis_k)
        ch = rec["chosen"]
        row = [os.path.basename(path), str(circ.n_qubits), str(ch),
               f"{rec['candidates'][ch]['hqc']:.1f}" if ch else "nan"]
        for p in cands:
            r = rec["candidates"][p]
            row += [f"{r['hqc']:.1f}", str(r["n_2q"]), r["status"]]
        print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
