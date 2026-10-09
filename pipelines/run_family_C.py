"""Family C: compile with P0 and P2 count-only, then check the stored QASM on
64 random computational basis inputs (sparse simulation, all sizes).

Step 1 (compile): every (circuit, pipeline) pair is run through
run_bench_B.run_with_timeout with check=False (status "ok-unchecked", gate-set
check kept, compiled QASM + measure-all written to
results/compiled/<pipeline>/<file>), per-pair timeout 300 s, rows appended
to results/family_C_counts.csv as they finish (pairs already present are
skipped, so the script can be rerun after an interruption).

Step 2 (basis check, --check): every family C construction maps
computational basis states to basis states.  For every n_qubits (up to 56)
the input circuit and each stored compiled QASM are simulated with a sparse
statevector simulator (complex amplitudes on the nonzero basis states only,
any gate, exact up to float rounding) on the same 64 random basis inputs
(seed 20261009).  The simulation is abandoned, and the row marked
"unchecked-branching", when the number of nonzero amplitudes summed over
the 64 inputs exceeds MAX_AMPS (2^20) at any gate; this happens for QFT
circuits whose Fourier register is wide (draper 16, 28) and for the
dirty-ancilla and relative-phase constructions (modadd, mcx_dirty, mcx_b95_54)
whose ancillas sit in superposition across many gates.  For n <= 26 the
check equals a dense statevector check restricted to the 64 inputs.
Negative control (2026-10-09): deleting one RZZ from the P2 output of
cdkm_adder_20 gives deviation 0.29, i.e. FAIL.

Family-C-only overrides of compile.py (compile.py itself unchanged):
compile.to_qasm writes c[n] registers wider than 32 bits, and
compile._tket_to_pyzx rewrites pytket's scientific-notation angles
('6.103515625e-05*pi') as exact decimals that pyzx's QASM parser accepts.
The implicit qubit permutation of the compiled circuit is read from its
measurement map (measure q[j] -> c[i] puts wire j on bit i, compile.py
add_measure_all).  With o_k = <ref_k|out_k> for input k the circuit passes
when max_k |1 - o_k / o_0| <= 1e-8 and max_k |1 - |o_k|| <= 1e-8, i.e. the
compiled circuit acts on the 64 inputs as the input circuit does up to one
global phase.  Columns basis_check (pass / FAIL / unchecked-branching / not-compiled),
basis_check_dev (the larger of the two maxima), basis_check_inputs.
This check covers 64 of 2^n basis inputs, it is not a proof of equivalence.

Usage: python3 pipelines/run_family_C.py [--files a,b] [--workers 2] [--check]
"""

import argparse
import os
import re
from decimal import Decimal
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile as C  # noqa: E402
import run_bench_B as RB  # noqa: E402
from pytket import Circuit, OpType  # noqa: E402
from pytket.qasm import circuit_from_qasm, circuit_from_qasm_str, circuit_to_qasm_str  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "bench", "family_C")
OUTCSV = os.path.join(ROOT, "results", "family_C_counts.csv")
PIPES = ["P0", "P2"]
TIMEOUT = 300.0
N_INPUTS = 64
SEED = 20261009
TOL = 1e-8
PRUNE = 1e-12
MAX_AMPS = 2 ** 20


class TooManyAmplitudes(RuntimeError):
    pass
COLS = ["file", "pipeline", "n", "application", "construction", "n_gates",
        "t_count_as_written", "n_cx_as_written", "n_rz_non_cliffordT_as_written",
        "status", "error", "n_qubits", "n_2q", "n_zzphase", "n_zzmax", "depth_2q",
        "n_phasedx", "n_rz", "n_total", "depth", "hqc", "native", "non_native_ops",
        "t_count_written", "t_count_zx", "n_non_cliffordT_zx", "n_2q_zx",
        "n_gates_zx", "pyzx_angle_err", "t_zx", "t_tket", "t_total", "t_wall",
        "check_kind", "check_ok"]




def _to_qasm_wide(circ):
    """compile.to_qasm with maxwidth=64: pytket's QASM writer refuses classical
    registers wider than 32 bits by default, and measure-all on n > 32 qubits
    needs a c[n] register.  compile.py is left unchanged; the override applies
    to this script only (forked workers inherit it)."""
    return circuit_to_qasm_str(circ, header="hqslib1", maxwidth=64)


C.to_qasm = _to_qasm_wide

_SCI = re.compile(r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?[eE][-+]?\d+)")


def _fixed_decimal(qasm: str) -> str:
    """Rewrite numbers in scientific notation as exact fixed decimals.
    pytket writes Rz(pi/2^14) as '6.103515625e-05*pi' and pyzx's QASM parser
    rejects that ("contains unbound variables").  Decimal(str) -> 'f' format
    is exact, so the circuit handed to pyzx is unchanged."""
    return _SCI.sub(lambda m: format(Decimal(m.group(1)), "f"), qasm)


def _tket_to_pyzx_fixed(circ):
    """compile._tket_to_pyzx with _fixed_decimal applied (family C only,
    compile.py unchanged)."""
    return C.pyzx.Circuit.from_qasm(_fixed_decimal(circuit_to_qasm_str(circ)))


C._tket_to_pyzx = _tket_to_pyzx_fixed


# ------------------------------------------------------- sparse simulator

class _Gate:
    """One unitary command: qubit bit positions, unitary, monomial data."""

    def __init__(self, qs, U):
        self.qs = qs
        k = len(qs)
        self.k = k
        self.U = U
        self.mask = np.int64(0)
        for q in qs:
            self.mask |= np.int64(1) << q
        self.sbits = np.array([self._bits(s) for s in range(2 ** k)], dtype=np.int64)
        nz = np.abs(U) > 1e-14
        self.monomial = bool(np.all(nz.sum(axis=0) == 1))
        if self.monomial:
            target = nz.argmax(axis=0)                 # column -> row
            self.coeff = U[target, np.arange(2 ** k)]
            self.tbits = self.sbits[target]

    def _bits(self, s):
        b = np.int64(0)
        for m, q in enumerate(self.qs):  # pytket ILO-BE: first arg most significant
            if (s >> (self.k - 1 - m)) & 1:
                b |= np.int64(1) << q
        return b

    def apply(self, idx, amp):
        sub = np.zeros_like(idx)
        for m, q in enumerate(self.qs):
            sub |= ((idx >> q) & 1) << (self.k - 1 - m)
        base = idx & ~self.mask
        if self.monomial:
            return base | self.tbits[sub], amp * self.coeff[sub]
        new_idx, new_amp = [], []
        for s in range(2 ** self.k):
            c = self.U[s, sub]
            keep = np.abs(c) > 1e-14
            new_idx.append(base[keep] | self.sbits[s])
            new_amp.append(amp[keep] * c[keep])
        ni = np.concatenate(new_idx)
        na = np.concatenate(new_amp)
        u, inv = np.unique(ni, return_inverse=True)
        a = (np.bincount(inv, weights=na.real, minlength=len(u))
             + 1j * np.bincount(inv, weights=na.imag, minlength=len(u)))
        keep = np.abs(a) > PRUNE
        return u[keep], a[keep]


def sparse_run(circ: Circuit, idx: np.ndarray, amp: np.ndarray):
    """Apply `circ` to the sparse state (idx, amp).  Bit j of an index is
    qubit q[j] (circ.qubits are q[0..n-1]); bits >= n carry the input label
    and are never touched.  Exact up to float rounding; amplitudes below
    PRUNE in modulus are dropped after each branching gate.

    Gates are applied in an order consistent with the circuit DAG (every
    qubit sees its gates in circuit order, so the result is the same state),
    chosen to keep the number of nonzero amplitudes small: every ready
    monomial gate (permutation times phases, e.g. CX, Rz, ZZPhase, X) is
    applied first, and among ready branching gates (H, general PhasedX) the
    one giving the fewest amplitudes is applied.  This lets the
    H-T-CX-...-H blocks of Toffoli decompositions close one at a time even
    when the QASM interleaves them.  Raises TooManyAmplitudes above
    MAX_AMPS."""
    pos = {q: q.index[0] for q in circ.qubits}
    gates = []
    for cmd in circ.get_commands():
        if cmd.op.type in (OpType.Barrier, OpType.Measure):
            continue
        gates.append(_Gate([pos[q] for q in cmd.args],
                           np.asarray(cmd.op.get_unitary())))
    queues = {}
    for gi, g in enumerate(gates):
        for q in g.qs:
            queues.setdefault(q, []).append(gi)
    head = {q: 0 for q in queues}

    def ready(gi):
        return all(queues[q][head[q]] == gi for q in gates[gi].qs)

    front = {queues[q][0] for q in queues if ready(queues[q][0])}
    done = 0
    while front:
        mono = [gi for gi in front if gates[gi].monomial]
        if mono:
            pick = [(gi, None) for gi in mono]
        else:
            best = None
            for gi in sorted(front):
                res = gates[gi].apply(idx, amp)
                if best is None or len(res[0]) < len(best[1][0]):
                    best = (gi, res)
                    if len(res[0]) <= len(idx):
                        break
            pick = [best]
        for gi, res in pick:
            if res is None:
                idx, amp = gates[gi].apply(idx, amp)
            else:
                idx, amp = res
            if len(idx) > MAX_AMPS:
                raise TooManyAmplitudes(len(idx))
            front.discard(gi)
            done += 1
            for q in gates[gi].qs:
                head[q] += 1
            for q in gates[gi].qs:
                if head[q] < len(queues[q]) and ready(queues[q][head[q]]):
                    front.add(queues[q][head[q]])
    assert done == len(gates)
    return idx, amp

def strip_measures(qasm: str):
    """-> (unmeasured Circuit, perm) with perm[j] = classical bit of wire j."""
    c = circuit_from_qasm_str(qasm, maxwidth=64)
    u = Circuit(c.n_qubits)
    perm = {}
    for cmd in c.get_commands():
        if cmd.op.type == OpType.Measure:
            perm[cmd.args[0].index[0]] = cmd.args[1].index[0]
        elif cmd.op.type != OpType.Barrier:
            u.add_gate(cmd.op, [q.index[0] for q in cmd.args])
    assert len(perm) == c.n_qubits
    return u, perm


def permute_bits(idx: np.ndarray, perm: dict, n: int) -> np.ndarray:
    hi = idx >> n << n
    out = np.zeros_like(idx)
    for j, b in perm.items():
        out |= ((idx >> j) & 1) << b
    return hi | out


def state_by_input(idx, amp, n):
    lab = idx >> n
    return {int(l): (idx[lab == l], amp[lab == l]) for l in np.unique(lab)}


def overlap(a, b):
    ia, aa = a
    ib, ab = b
    common, xa, xb = np.intersect1d(ia, ib, return_indices=True)
    return np.vdot(aa[xa], ab[xb])


def basis_check(file: str, pipeline: str):
    src = circuit_from_qasm(os.path.join(BENCH, file))
    n = src.n_qubits
    assert [q.index[0] for q in src.qubits] == list(range(n))
    rng = np.random.default_rng(SEED)
    inputs = rng.integers(0, 2 ** n, size=N_INPUTS, dtype=np.int64)
    idx0 = inputs | (np.arange(N_INPUTS, dtype=np.int64) << n)
    amp0 = np.ones(N_INPUTS, dtype=complex)
    ri, ra = sparse_run(src, idx0.copy(), amp0.copy())
    with open(os.path.join(ROOT, "results", "compiled", pipeline, file)) as f:
        comp, perm = strip_measures(f.read())
    assert comp.n_qubits == n
    ci, ca = sparse_run(comp, idx0.copy(), amp0.copy())
    ci = permute_bits(ci, perm, n)
    R, Cs = state_by_input(ri, ra, n), state_by_input(ci, ca, n)
    o = np.array([overlap(R[k], Cs[k]) for k in range(N_INPUTS)])
    dev = max(float(np.max(np.abs(1 - o / o[0]))), float(np.max(np.abs(1 - np.abs(o)))))
    return dev, int(max(len(ri), len(ci)))


# ---------------------------------------------------------------- driver

def compile_all(files, workers):
    done = set()
    if os.path.exists(OUTCSV):
        old = pd.read_csv(OUTCSV)
        done = set(zip(old.file, old.pipeline))
    man = pd.read_csv(os.path.join(BENCH, "manifest.csv"))
    if files:
        man = man[man.file.isin(files)]
    order = man.sort_values("n_gates", ascending=False).file
    jobs = [(BENCH, f, p, TIMEOUT, False) for f in order for p in PIPES
            if (f, p) not in done]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for row in ex.map(RB.run_with_timeout, jobs, chunksize=1):
            m = man.set_index("file").loc[row["file"]]
            for c in ["n", "application", "construction", "n_gates",
                      "t_count_as_written", "n_cx_as_written",
                      "n_rz_non_cliffordT_as_written"]:
                row[c] = m[c]
            df = pd.DataFrame([row]).reindex(columns=COLS)
            df.to_csv(OUTCSV, mode="a", header=not os.path.exists(OUTCSV), index=False)
            print(f"{row['file']} {row['pipeline']} {row['status']} hqc={row.get('hqc')} "
                  f"n_2q={row.get('n_2q')} {row['t_wall']:.1f}s "
                  f"[{time.perf_counter() - t0:.0f}s]", flush=True)


def check_all(files):
    df = pd.read_csv(OUTCSV)
    for c, v in [("basis_check", ""), ("basis_check_dev", np.nan),
                 ("basis_check_inputs", np.nan)]:
        if c not in df.columns:
            df[c] = v
    df["basis_check"] = df["basis_check"].astype(object)
    for i, r in df.iterrows():
        if files and r.file not in files:
            continue
        if not str(r.status).startswith("ok"):
            df.at[i, "basis_check"] = "not-compiled"
            continue
        t0 = time.perf_counter()
        try:
            dev, nmax = basis_check(r.file, r.pipeline)
        except TooManyAmplitudes as e:
            df.at[i, "basis_check"] = "unchecked-branching"
            df.at[i, "basis_check_inputs"] = 0
            print(f"{r.file} {r.pipeline} unchecked-branching ({e.args[0]} amplitudes) "
                  f"{time.perf_counter() - t0:.1f}s", flush=True)
            df.to_csv(OUTCSV, index=False)
            continue
        df.at[i, "basis_check_dev"] = dev
        df.at[i, "basis_check_inputs"] = N_INPUTS
        df.at[i, "basis_check"] = "pass" if dev <= TOL else "FAIL"
        print(f"{r.file} {r.pipeline} dev={dev:.2e} max_amps={nmax} "
              f"{df.at[i, 'basis_check']} {time.perf_counter() - t0:.1f}s", flush=True)
        df.to_csv(OUTCSV, index=False)
    df.to_csv(OUTCSV, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = [f if f.endswith(".qasm") else f + ".qasm" for f in a.files.split(",") if f]
    if a.check:
        check_all(files)
    else:
        compile_all(files, a.workers)


if __name__ == "__main__":
    main()
