"""Empirical probe of selene-sim's DepolarizingErrorModel conventions.

The Selene user guide (docs.quantinuum.com/selene/user_guide/error_model.html,
read 2026-10-07) says only that p_1q / p_2q / p_meas / p_init are "error
probabilities" and does not say (a) whether Rz receives 1-qubit noise, (b)
whether p_1q means "a uniformly random non-identity Pauli with probability p"
(the dm_sim convention: flip probability 2p/3 after an X gate) or "a uniformly
random Pauli including identity" (flip probability p/2), nor (c) whether
p_meas is a symmetric readout flip.  This script measures each with a large
probability and many shots and prints the flip rates next to the two
candidate predictions.

Run with every proxy variable unset:
    HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= python3 selene/calibrate_error_model.py
"""
import math
import sys
from collections import Counter

from pytket import Circuit
from guppylang import guppy
from guppylang.std.builtins import array, result
from guppylang.std.quantum import qubit, discard_array
from selene_sim import build, Quest, DepolarizingErrorModel

SHOTS = 20000
P = 0.3


def make(circ, name):
    n = circ.n_qubits
    fn = guppy.load_pytket(name, circ)

    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(n))
        c = fn(qs)
        discard_array(qs)
        result("c", c)

    return build(main.compile())


def counts(runner, n, em, seed=7):
    out = Counter()
    for shot in runner.run_shots(Quest(random_seed=seed), n_qubits=n, n_shots=SHOTS,
                                 error_model=em, random_seed=seed):
        out["".join(str(int(b)) for b in dict(shot)["c"])] += 1
    return out


def se(p):
    return math.sqrt(p * (1 - p) / SHOTS)


def main():
    rows = []
    # (a) Rz only: 20 Rz(0.3) on |0>, p_1q = P.  Any '1' outcome means Rz is noisy.
    c = Circuit(1, 1)
    for _ in range(20):
        c.Rz(0.3, 0)
    c.Measure(0, 0)
    k = counts(make(c, "rz_only"), 1, DepolarizingErrorModel(p_1q=P))
    f = k["1"] / SHOTS
    # P(odd number of X/Y flips in 20 gates) = (1 - (1 - 2f)^20) / 2, f = per-gate flip rate
    rows.append(("Rz x20, p_1q=0.3: P(1)", f, "0 if Rz noiseless; (1-(1-2f)^20)/2 = %.4f (f=2p/3) / %.4f (f=p/2) if noisy"
                 % ((1 - 0.6 ** 20) / 2, (1 - 0.7 ** 20) / 2)))
    # (a') PhasedX only: 20 PhasedX(0,0) (identity) -- does a 1q gate with zero angles still get noise?
    c = Circuit(1, 1)
    for _ in range(20):
        c.PhasedX(0.0, 0.0, 0)
    c.Measure(0, 0)
    k = counts(make(c, "px_zero"), 1, DepolarizingErrorModel(p_1q=P))
    f = k["1"] / SHOTS
    rows.append(("PhasedX(0,0) x20, p_1q=0.3: P(1)", f, "0 if zero-angle gates are free; (1-(1-2f)^20)/2 = %.4f (f=2p/3) / %.4f (f=p/2) if noisy"
                 % ((1 - 0.6 ** 20) / 2, (1 - 0.7 ** 20) / 2)))
    # (b) one X gate (PhasedX(1,0)) on |0>, p_1q = P: flip rate 2p/3 or p/2
    c = Circuit(1, 1)
    c.PhasedX(1.0, 0.0, 0)
    c.Measure(0, 0)
    k = counts(make(c, "one_x"), 1, DepolarizingErrorModel(p_1q=P))
    f = k["0"] / SHOTS
    rows.append(("X, p_1q=0.3: P(flip)", f, "2p/3=%.3f (non-identity Pauli) / p/2=%.3f (any Pauli)" % (2 * P / 3, P / 2)))
    # (c) one ZZPhase(0.5) on |00> (diagonal: ideal outcome 00), p_2q = P.
    # non-identity 2q Pauli convention: P(any flip) = p * 12/15 = 0.8p ; any-Pauli: p*12/16 = 0.75p
    c = Circuit(2, 2)
    c.ZZPhase(0.5, 0, 1)
    c.Measure(0, 0).Measure(1, 1)
    k = counts(make(c, "one_zz"), 2, DepolarizingErrorModel(p_2q=P))
    f = 1 - k["00"] / SHOTS
    rows.append(("ZZPhase, p_2q=0.3: P(not 00)", f, "12p/15=%.3f (non-identity Pauli) / 12p/16=%.3f (any Pauli)" % (0.8 * P, 0.75 * P)))
    # (d) p_meas on |0> and on |1>
    c = Circuit(1, 1)
    c.Measure(0, 0)
    k = counts(make(c, "meas0"), 1, DepolarizingErrorModel(p_meas=P))
    rows.append(("measure |0>, p_meas=0.3: P(1)", k["1"] / SHOTS, "p=0.300 if symmetric flip"))
    c = Circuit(1, 1)
    c.PhasedX(1.0, 0.0, 0)
    c.Measure(0, 0)
    k = counts(make(c, "meas1"), 1, DepolarizingErrorModel(p_meas=P))
    rows.append(("measure |1>, p_meas=0.3: P(0)", k["0"] / SHOTS, "p=0.300 if symmetric flip"))
    # (e) p_init on |0>
    c = Circuit(1, 1)
    c.Measure(0, 0)
    k = counts(make(c, "init0"), 1, DepolarizingErrorModel(p_init=P))
    rows.append(("init, p_init=0.3: P(1)", k["1"] / SHOTS, "p=0.300 if init flip; 2p/3=0.200 if depolarising"))
    print("shots per probe:", SHOTS)
    for name, f, pred in rows:
        print("%-42s %.4f +/- %.4f   predictions: %s" % (name, f, se(max(f, 1e-9)), pred))


if __name__ == "__main__":
    sys.exit(main())
