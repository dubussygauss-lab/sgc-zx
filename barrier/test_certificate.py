"""Self-running tests for certificate.py.  Run: python3 test_certificate.py"""

import math
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import certificate as c  # noqa: E402

RESULTS = []


def check(name, cond, info=""):
    RESULTS.append((name, bool(cond)))
    print("%s  %s %s" % ("PASS" if cond else "FAIL", name, info))


def note(name, cond, info=""):
    """A documented discrepancy with the paper: passes when reproduced."""
    RESULTS.append((name, bool(cond)))
    print("%s  %s %s" % ("NOTE" if cond else "FAIL", name, info))


def np_gate(name):
    w = np.exp(1j * np.pi / 4)
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    tab = {"h": H, "s": np.diag([1, 1j]), "sdg": np.diag([1, -1j]),
           "t": np.diag([1, w]), "tdg": np.diag([1, np.conj(w)]),
           "x": np.array([[0, 1], [1, 0]]), "y": np.array([[0, -1j], [1j, 0]]),
           "z": np.diag([1, -1]), "id": np.eye(2),
           "cx": np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]]),
           "cz": np.diag([1, 1, 1, -1]),
           "swap": np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])}
    return tab[name].astype(complex)


def np_embed(G, qubits, n):
    """Embed a local gate (local index b0 + 2 b1) into n qubits, basis sum b_q 2^q."""
    N = 2 ** n
    M = np.zeros((N, N), dtype=complex)
    m = len(qubits)
    for a in range(N):
        for b in range(N):
            rest_a = a
            rest_b = b
            la = lb = 0
            for j, q in enumerate(qubits):
                la += ((a >> q) & 1) << j
                lb += ((b >> q) & 1) << j
                rest_a &= ~(1 << q)
                rest_b &= ~(1 << q)
            if rest_a == rest_b:
                M[a, b] = G[la, lb]
    return M


def np_unitary(word, n):
    w, n = c.normalize_word(word, n)
    U = np.eye(2 ** n, dtype=complex)
    for name, qs in w:
        U = U @ np_embed(np_gate(name), qs, n)
    return U


def random_word(n, length, rng, two_qubit_p=0.3):
    names1 = ["h", "s", "sdg", "t", "tdg", "x", "y", "z"]
    names2 = ["cx", "cz", "swap"]
    w = []
    for _ in range(length):
        if n > 1 and rng.random() < two_qubit_p:
            w.append((rng.choice(names2), tuple(rng.sample(range(n), 2))))
        else:
            w.append((rng.choice(names1), (rng.randrange(n),)))
    return w


def insert_identities(word, rng, n):
    """Insert HH, SSSS, TTTTTTTT (and CX CX for n > 1) at random places."""
    w, n = c.normalize_word(word, n)
    ids = [[("h", (q,))] * 2 for q in range(n)] + [[("s", (q,))] * 4 for q in range(n)] \
        + [[("t", (q,))] * 8 for q in range(n)]
    if n > 1:
        ids += [[("cx", (0, 1))] * 2, [("cz", (1, 0))] * 2]
    for _ in range(5):
        pos = rng.randrange(len(w) + 1)
        w[pos:pos] = rng.choice(ids)
    return w


# ---------------------------------------------------------------------------
# 1. ring arithmetic
# ---------------------------------------------------------------------------

def test_ring():
    p = c.ONE
    for _ in range(8):
        p = p * c.OMEGA
    check("omega^8 = 1", p == 1)
    check("omega^4 = -1", c.OMEGA * c.OMEGA * c.OMEGA * c.OMEGA == -1)
    check("sqrt2^2 = 2", c.SQRT2 * c.SQRT2 == 2)
    check("i^2 = -1", c.IUNIT * c.IUNIT == -1)
    check("sqrt2 = omega + omega^-1", c.SQRT2 == c.OMEGA + c.W7)
    check("conj(omega) = omega^7", c.OMEGA.conj() == c.W7)
    check("|omega|^2 = 1", c.OMEGA * c.OMEGA.conj() == 1)
    # divisibility by sqrt2: brute-force against the definition
    rng = random.Random(0)
    ok = True
    for _ in range(2000):
        x = c.Zw(*[rng.randrange(-6, 7) for _ in range(4)])
        y = x * c.SQRT2
        ok &= y.divisible_by_sqrt2() and y.div_sqrt2() == x
        # x divisible iff some z with z*sqrt2 == x: search residues
        if x.divisible_by_sqrt2():
            ok &= x.div_sqrt2() * c.SQRT2 == x
    check("sqrt2 divisibility test and quotient", ok)
    # the residue criterion is exactly: a==c and b==d mod 2.  Check that
    # elements with a!=c or b!=d mod 2 are not of the form z*sqrt2.
    images = set()
    for a in range(-3, 4):
        for b in range(-3, 4):
            for cc in range(-3, 4):
                for d in range(-3, 4):
                    z = c.Zw(a, b, cc, d) * c.SQRT2
                    images.add(((z.a - z.c) % 2, (z.b - z.d) % 2))
    check("every multiple of sqrt2 has a==c, b==d mod 2", images == {(0, 0)})
    # complex evaluation
    ok = True
    for _ in range(200):
        x = c.Zw(*[rng.randrange(-5, 6) for _ in range(4)])
        y = c.Zw(*[rng.randrange(-5, 6) for _ in range(4)])
        ok &= abs((x * y).to_complex() - x.to_complex() * y.to_complex()) < 1e-9
        ok &= abs((x + y).to_complex() - x.to_complex() - y.to_complex()) < 1e-9
    check("Zw complex evaluation is a ring homomorphism", ok)
    # real elements -> Z[sqrt2]
    x = c.Zw(3, 2, 0, -2)
    check("real_sqrt2", x.real_sqrt2() == (3, 2) and abs(x.to_complex() - (3 + 2 * math.sqrt(2))) < 1e-12)


# ---------------------------------------------------------------------------
# 2. unitaries and sde
# ---------------------------------------------------------------------------

def test_unitaries():
    I = c.word_unitary("HH")
    check("H^2 = I exactly", I.sde == 0 and all(I.M[i, j] == (1 if i == j else 0) for i in range(2) for j in range(2)))
    check("sde(T) = 0", c.word_unitary("T").sde == 0)
    check("sde(H) = 1", c.word_unitary("H").sde == 1)
    check("sde(HTH) = 2 (derived: 1+omega not divisible by sqrt2)", c.word_unitary("HTH").sde == 2)
    check("sde(S)=sde(X)=sde(Z)=0", all(c.word_unitary(g).sde == 0 for g in "SXZ"))
    check("sde(HSH) = 1 (derived: HSH = [[w, w^7],[w^7, w]]/sqrt2)", c.word_unitary("HSH").sde == 1
          and c.word_unitary("HSH").M[0, 0] == c.OMEGA)
    # (HT)^k vs numpy
    ok = True
    for k in range(1, 30):
        U = c.word_unitary(["h", "t"] * k)
        ok &= np.abs(U.to_complex() - np_unitary(["h", "t"] * k, 1)).max() < 1e-12
    check("(HT)^k exact matrices agree with numpy, k<=29", ok)
    # adjoints
    for g, gd in (("s", "sdg"), ("t", "tdg")):
        U = c.word_unitary([g, gd])
        check("%s %s = I" % (g, gd), U.sde == 0 and U.M[0, 0] == 1 and U.M[1, 1] == 1 and not U.M[0, 1] and not U.M[1, 0])
    # dagger
    U = c.word_unitary("HTSH")
    P = np.dot(U.M, U.dagger().M)
    check("U U^dag = 2^k I", all(P[i, j] == (2 ** U.k if i == j else 0) for i in range(2) for j in range(2)))
    # multi-qubit against numpy, including qubit-order conventions
    rng = random.Random(3)
    ok = True
    for n in (2, 3, 4):
        for _ in range(4):
            w = random_word(n, 30, rng)
            U = c.word_unitary(w, n)
            ok &= np.abs(U.to_complex() - np_unitary(w, n)).max() < 1e-10
    check("random 2-4 qubit words agree with numpy to 1e-10", ok)
    # unitarity check of the sde: M M^dag = 2^k I
    w = random_word(3, 40, rng)
    U = c.word_unitary(w, 3)
    P = np.dot(U.M, U.dagger().M)
    check("3-qubit M M^dag = 2^k I", all(P[i, j] == (2 ** U.k if i == j else 0) for i in range(8) for j in range(8)))
    # sde invariant under the unit omega (global phase): multiply M by omega
    V = c.DMat(U.M * c.OMEGA, U.k, 3).reduce()
    check("sde invariant under global phase omega", V.sde == U.sde)
    # entrywise sde
    E = c.sde_entrywise(c.word_unitary("H"))
    check("entrywise sde of H is 1 everywhere", all(E[i, j] == 1 for i in range(2) for j in range(2)))


# ---------------------------------------------------------------------------
# 3. Bloch / channel representation
# ---------------------------------------------------------------------------

def test_channel():
    B = c.bloch(c.word_unitary("T"))
    check("Bloch(T) = (A + B sqrt2)/sqrt2 with A=[[1,-1],[1,1]] block, B=diag(0,0,1)",
          B.e == 1 and B.P.tolist() == [[1, -1, 0], [1, 1, 0], [0, 0, 0]] and B.Q.tolist() == [[0, 0, 0], [0, 0, 0], [0, 0, 1]])
    check("lde(T^) = 1 (Lemma mqval(a))", B.lde == 1)
    # Bloch vs float
    rng = random.Random(5)
    ok = True
    for _ in range(100):
        w = random_word(1, rng.randrange(1, 40), rng)
        U = c.word_unitary(w, 1)
        Uc = U.to_complex()
        sig = [np_gate("x"), np_gate("y"), np_gate("z")]
        F = np.array([[0.5 * np.trace(sig[i] @ Uc @ sig[j] @ Uc.conj().T).real for j in range(3)] for i in range(3)])
        ok &= np.abs(c.bloch(U).to_float() - F).max() < 1e-10
    check("exact Bloch matrix agrees with float on 100 random words", ok)
    # Clifford Bloch matrices are signed permutations of exponent 0; group order 24
    G = c.clifford_group()
    check("projective Clifford group has order 24", len(G) == 24)
    check("8 Cliffords lie in N(Z)", sum(c.in_normalizer(np.array(k).reshape(3, 3)) for k in G) == 8)
    # 4^n channel vs Bloch at n=1, and structured accumulator vs dense at n=1,2,3
    ok = True
    for _ in range(120):
        w = random_word(1, rng.randrange(1, 30), rng)
        U = c.word_unitary(w, 1)
        D = c.channel_dense(U)
        Bm = c.bloch(U)
        R, _ = c.channel_accumulate(w, 1)
        ok &= D.lde == Bm.lde == R.lde and D.key() == R.key()
    check("n=1: 4x4 channel lde == Bloch lde, structured == dense (120 words)", ok)
    ok = True
    for n in (2, 3):
        for _ in range(6):
            w = random_word(n, 30, rng)
            R, _ = c.channel_accumulate(w, n)
            D = c.channel_dense(c.word_unitary(w, n))
            ok &= R.key() == D.key()
    check("n=2,3: structured accumulator == dense channel (numerators and exponent)", ok)
    # channel of a product is the product of channels
    w1, w2 = random_word(2, 15, rng), random_word(2, 15, rng)
    R1, _ = c.channel_accumulate(w1, 2)
    R2, _ = c.channel_accumulate(w2, 2)
    R12, _ = c.channel_accumulate(w1 + w2, 2)
    check("channel(g1 g2) = channel(g1) channel(g2)", (R1 @ R2).key() == R12.key())
    # orthogonality of the channel: V^ V^T = I
    F = R12.to_float()
    check("channel is orthogonal (float check)", np.abs(F @ F.T - np.eye(16)).max() < 1e-9)


# ---------------------------------------------------------------------------
# 4. paper reproductions
# ---------------------------------------------------------------------------

def test_paper_examples():
    # Fig. tiers: T H S S H T implements a Clifford, t_min = 0
    r = c.certificate("THSSHT")
    check("Fig. tiers: THSSHT has t_min = lde = 0", r["t_min"] == 0 and r["lde_channel"] == 0 and r["linkage_t_min"] == 0)
    # Fig. normalizer (a)-(c)
    check("Fig. normalizer (a): T S T -> t_min 0", c.certificate("TST")["t_min"] == 0)
    check("Fig. normalizer (b): T HSSH T -> t_min 0", c.certificate("THSSHT")["t_min"] == 0)
    rc = c.certificate("THT")
    check("Fig. normalizer (c): T H T -> lde 2, P != 0 mod 2", rc["t_min"] == 2 and np.any(rc["bloch"].P % 2))
    # (HZ)^4 projectively trivial (Sec. tier1)
    check("(HZ)^4 has lde 0", c.certificate("HZHZHZHZ")["t_min"] == 0)
    # planted family {T c T, T c T^dag}: 48 cases, fusion iff c in N
    ok = True
    nN = 0
    for k, cw in c.clifford_group().items():
        inN = c.in_normalizer(np.array(k).reshape(3, 3))
        nN += inN
        for tail in ("t", "tdg"):
            w = ["t"] + [g for g in cw if g != "id"] + [tail]
            r = c.certificate(w)
            expect = 0 if inN else 2
            ok &= r["t_min"] == expect and r["linkage_t_min"] == expect and r["lde_channel"] == expect
            ok &= (r["linkage_merges"] == 1) == inN
    check("planted family: 48 cases, t_min = 0 iff c in N (8 of 24), else 2", ok and nN == 8)
    # Lemma valuation residue automaton
    a = c.residue_automaton(allow_normalizer=False)
    check("residue automaton: 24 states, 6 seeds, 1536 transitions, 0 reducible",
          (a["states"], a["seed_states"], a["transitions"], a["reducible_states"]) == (24, 6, 1536, 0), str(a))
    b = c.residue_automaton(allow_normalizer=True)
    check("sharpness run: 34 states, 10 reducible", (b["states"], b["reducible_states"]) == (34, 10), str(b))
    # Separated words: lde = n (Lemma valuation), 400 per length 1..8 in the paper; 50 here
    rng = random.Random(11)
    G = c.clifford_group()
    nonN = [cw for k, cw in G.items() if not c.in_normalizer(np.array(k).reshape(3, 3))]
    allC = list(G.values())
    ok = True
    for n in range(1, 9):
        for _ in range(50):
            w = list(rng.choice(allC))
            for i in range(n):
                w.append(rng.choice(["t", "tdg"]))
                w += list(rng.choice(nonN) if i < n - 1 else rng.choice(allC))
            w = [g for g in w if g != "id"]
            r = c.certificate(w)
            ok &= r["t_min"] == n and r["linkage_t_min"] == n
    check("separated words have lde = n (n = 1..8, 50 each)", ok)
    # lifting the restriction: deficit n - lde is always even
    ok, deficits = True, []
    for n in range(2, 9):
        for _ in range(50):
            w = list(rng.choice(allC))
            for i in range(n):
                w.append(rng.choice(["t", "tdg"]))
                w += list(rng.choice(allC))
            w = [g for g in w if g != "id"]
            r = c.certificate(w)
            d = n - r["t_min"]
            deficits.append(d)
            ok &= d >= 0 and d % 2 == 0 and r["linkage_t_min"] == r["t_min"]
    frac = sum(1 for d in deficits if d > 0) / len(deficits)
    check("unrestricted words: deficit n - lde even, linkage agrees (paper: 69%% with lde<n; here %.0f%%)" % (100 * frac), ok)
    # Lemma bridge ground truth: MA normal forms, t <= 8 -> 18,384 distinct elements, t_min = lde
    t0 = time.time()
    ws = c.matsumoto_amano_words(8)
    keys, hist, ok = set(), {}, True
    for w in ws:
        B = c.bloch(c.word_unitary(w, 1))
        tc = c.t_count(w)
        ok &= (B.lde == tc)
        keys.add(B.key())
        hist[tc] = hist.get(tc, 0) + 1
    check("MA enumeration t<=8: 18,384 words", len(ws) == 18384)
    check("MA enumeration: 18,384 distinct projective elements", len(keys) == 18384)
    check("MA histogram 24*[1,3,6,12,24,48,96,192,384]", [hist[t] for t in range(9)] == [24 * x for x in (1, 3, 6, 12, 24, 48, 96, 192, 384)])
    check("t_min = lde on every MA element (Lemma bridge)", ok, "%.1fs" % (time.time() - t0))
    check("is_matsumoto_amano on grammar words", all(c.is_matsumoto_amano(w) for w in ws[:2000]) and not c.is_matsumoto_amano("THTT"))
    # Controlled-S: channel lde 2, minimal T-count 3 (Sec. multiqubit)
    cs = [("t", (0,)), ("t", (1,)), ("cx", (0, 1)), ("tdg", (1,)), ("cx", (0, 1))]
    U = c.word_unitary(cs, 2).to_complex()
    check("CS word implements diag(1,1,1,i)", np.abs(U - np.diag([1, 1, 1, 1j])).max() < 1e-12)
    r = c.certificate(cs, 2)
    check("controlled-S: channel lde = 2 with T-count 3", r["lde_channel"] == 2 and r["t_count"] == 3)
    # Theorem C(a): a single-wire MA block embedded on one wire is rigid
    ok = True
    for w in rng.sample(ws, 200):
        lde, tc, rigid = c.block_rigidity(w)
        ok &= rigid
        w2 = [(g, (1,)) for g in w]
        R, _ = c.channel_accumulate(w2, 3)
        ok &= R.lde == tc
    check("Theorem C(a): MA blocks rigid, also embedded on wire 1 of 3", ok)


# ---------------------------------------------------------------------------
# 5. soundness and invariance
# ---------------------------------------------------------------------------

def test_soundness():
    rng = random.Random(7)
    ok_sound = ok_inv = ok_link = ok_crit = ok_drop = True
    ncol = nref = 0
    for _ in range(60):
        w = random_word(1, rng.randrange(1, 201), rng)
        r = c.certificate(w)
        ok_sound &= r["t_count"] >= r["floor"] and r["sound"]
        ok_link &= r["linkage_agrees"]
        ok_crit &= not r["criterion_violations"]
        ok_drop &= all(d == 2 for d in r["collapse_sizes"])
        ncol += r["collapse_count"]
        nref += r["refinement_violations"]
        r2 = c.certificate(insert_identities(w, rng, 1))
        ok_inv &= r2["floor"] == r["floor"] and r2["t_min"] == r["t_min"] and r2["sde_unitary"] == r["sde_unitary"]
    check("single-qubit random words (len<=200): T-count >= floor", ok_sound)
    check("single-qubit: linkage count == lde(Bloch) == lde(channel)", ok_link)
    check("single-qubit: floor and sde invariant under HH, SSSS, T^8 insertion", ok_inv)
    check("single-qubit: criterion fires iff lde fails to rise; otherwise rises by exactly 1", ok_crit)
    note("DISCREPANCY (Lemma mqval(b) refinement): at n=1 every criterion-positive step gives lde = m-1, not m "
         "(%d collapses, %d violate 'equals m')" % (ncol, nref), ok_drop and ncol > 0 and nref == ncol)
    _, st = c.channel_accumulate("TT", 1)
    note("DISCREPANCY: T T = S: criterion fires at step 2 with m=1 and lde drops to 0 (paper: 'equals m')",
         st[1]["criterion_fired"] and st[1]["lde_before"] == 1 and st[1]["lde_after"] == 0)
    # reversal and inverse invariance of the floor (paper: lde depends only on the element;
    # reversed word implements the transpose for symmetric gate matrices)
    ok = True
    for _ in range(30):
        w = random_word(1, rng.randrange(1, 100), rng)
        r = c.certificate(w)["floor"]
        ok &= c.certificate(list(reversed(w)))["floor"] == r
        inv = {"t": "tdg", "tdg": "t", "s": "sdg", "sdg": "s"}
        ok &= c.certificate([(inv.get(g, g), q) for g, q in reversed(w)])["floor"] == r
    check("floor invariant under word reversal and inversion", ok)
    # multi-qubit
    ok_sound = ok_inv = ok_crit = True
    sizes = {}
    for n in (2, 3, 4):
        for _ in range(8):
            w = random_word(n, rng.randrange(1, 80), rng)
            r = c.certificate(w, n)
            ok_sound &= r["t_count"] >= r["floor"] and 0 <= r["max_removable_fraction"] <= 1
            ok_crit &= not r["criterion_violations"]
            for d in r["collapse_sizes"]:
                sizes[d] = sizes.get(d, 0) + 1
            r2 = c.certificate(insert_identities(w, rng, n), n)
            ok_inv &= r2["floor"] == r["floor"]
    check("n=2,3,4 random circuits: T-count >= floor", ok_sound)
    check("n=2,3,4: floor invariant under identity insertion", ok_inv)
    check("n=2,3,4: criterion fires iff lde fails to rise; otherwise rises by exactly 1", ok_crit)
    note("DISCREPANCY: at n>=2 criterion-positive steps give lde in {m, m-1}; sizes (1+m-lde_after): %s" % sizes,
         set(sizes) <= {1, 2} and 2 in sizes)
    # Clifford steps never change the lde
    ok = True
    for n in (1, 2, 3):
        w = random_word(n, 60, rng)
        _, steps = c.channel_accumulate(w, n)
        for s in steps:
            if s["gate"] not in c.T_TYPE:
                ok &= s["lde_after"] == s["lde_before"]
            else:
                ok &= s["lde_after"] <= s["lde_before"] + 1
    check("Clifford steps leave lde unchanged; T steps raise it by at most one", ok)


# ---------------------------------------------------------------------------
# 6. QASM
# ---------------------------------------------------------------------------

def test_qasm():
    text = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
t q[0];
t q[1];
cx q[0],q[1];
tdg q[1]; // comment
cx q[0],q[1];
barrier q[0],q[1];
"""
    n, gates = c.parse_qasm(text)
    check("qasm parse: n=2, 5 gates", n == 2 and len(gates) == 5 and gates[0] == ("t", (0,)))
    r = c.certificate_from_qasm(text)
    check("qasm certificate (controlled-S): lde 2, t 3", r["lde_channel"] == 2 and r["t_count"] == 3)
    # time-order vs matrix-product order give the same unitary up to transpose and the same floor
    n, wt = c.word_from_qasm(text, time_order_as_word=True)
    n, wm = c.word_from_qasm(text)
    Ut = c.word_unitary(wt, n).to_complex()
    Um = c.word_unitary(wm, n).to_complex()
    check("qasm: word = reversed time order (unitary of circuit)", np.abs(Um - Ut.T).max() < 1e-12
          and c.certificate(wt, n)["floor"] == c.certificate(wm, n)["floor"])
    try:
        c.parse_qasm('OPENQASM 2.0;\nqreg q[1];\nrz(0.3) q[0];\n')
        check("qasm rejects rz", False)
    except ValueError:
        check("qasm rejects rz", True)
    # a longer random circuit round-trips through the parser
    rng = random.Random(9)
    w = random_word(3, 50, rng)
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[3];"]
    for g, qs in reversed(w):
        lines.append("%s %s;" % (g, ",".join("q[%d]" % q for q in qs)))
    n2, w2 = c.word_from_qasm("\n".join(lines))
    check("qasm round trip of a random 3-qubit word", n2 == 3 and w2 == w)


if __name__ == "__main__":
    t0 = time.time()
    test_ring()
    test_unitaries()
    test_channel()
    test_paper_examples()
    test_soundness()
    test_qasm()
    npass = sum(1 for _, ok in RESULTS if ok)
    print("\n%d/%d checks passed in %.1fs" % (npass, len(RESULTS), time.time() - t0))
    sys.exit(0 if npass == len(RESULTS) else 1)
