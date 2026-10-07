# NOTES: what `certificate.py` implements, quoted from `papers/barrier/main.tex`

Line numbers refer to `/home/claude/sgc-zx/papers/barrier/main.tex` (4298 lines).
Everything in quotation blocks is verbatim from the tex. Items marked **CONVENTION**
are choices the tex does not fix and the user must check.

## 1. Rings and storage format

**Z[omega]** (lines 495-501):

> Unitary entries of single-qubit Clifford+$T$ words live in the ring $\Zb[\omega]$ with
> $\omega = e^{i\pi/4}$ ... The real $SO(3)$ Bloch representation and the $n$-qubit
> Pauli-channel representation live in the smaller ring $\Zb[\sqrt2]$, and it is there that
> our invariant lives.

Implemented: `Zw(a,b,c,d)` = a + b w + c w^2 + d w^3, w^4 = -1, Python ints.
sqrt2 = w + w^{-1} = w - w^3 (`SQRT2 = Zw(0,1,0,-1)`). Divisibility by sqrt2 is decided by
the residue map Z[w]/(sqrt2) = F_2[x]/(x^2-1): x = a + b w + c w^2 + d w^3 is divisible by
sqrt2 iff a = c (mod 2) and b = d (mod 2); the quotient is
x/sqrt2 = ((b-d) + (a+c) w + (b+d) w^2 + (c-a) w^3)/2. Both derived here (not in the tex)
and tested (`test_ring`).

Unitaries are stored as `DMat(M, k)` meaning M / sqrt2^k, M over Z[w]; `reduce()` lowers k
while every entry is divisible by sqrt2 (k >= 0). `DMat.sde` = that minimal k. The tex uses
"sde" only as a diagnostic (Table `tab:barrier` caption, lines 2890-2895):

> $\sde$, the mean smallest denominator exponent of the $\Zb[\omega]$ unitary matrix, is
> reported as a diagnostic and distinguished from the Bloch-image exponent
> $\mathrm{lde} = \tmin$ that certifies the floor.

**Z[sqrt2] storage and reduction**, Eq. (ringform) and (redcrit) (lines 503-521):

> every matrix $M$ over $\Zb[\sqrt2]$ can be written
> $M = \frac{P + Q\sqrt2}{\sqrt2^{\,e}}$,
> with $P$ and $Q$ integer matrices, and for a given $M$ the representation with $e$ least is
> unique. We call that minimal $e$ the \emph{least denominator exponent} $\mathrm{lde}(M)$.
> ... dividing numerator and denominator of~\eqref{eq:ringform} by $\sqrt2$ sends
> $(P, Q) \mapsto (Q, P/2)$, which stays integral exactly when
> $P \equiv 0 \pmod 2 \quad\text{entrywise}$,
> so a representation can be reduced precisely when~\eqref{eq:redcrit} holds, and repeating
> the step until it fails yields $\mathrm{lde}(M)$.

Implemented: `RMat(P, Q, e)`, `RMat.reduce()`, `RMat.lde`. Reduction stops at e = 0.

## 2. Bloch representation and Lemma bridge (lines 591-605)

> For a single-qubit Clifford+$T$ element $V$, write
> $\hat V_{ij} = \tfrac12\,\mathrm{tr}(\sigma_i V \sigma_j V^\dagger)$ for its exact $SO(3)$
> Bloch representation ...
> \begin{lemma}\label{lem:bridge} The minimal $T$-count of a single-qubit Clifford+$T$
> element $V$ is $\tmin(V) = \mathrm{lde}(\hat V)$.

Implemented: `bloch(U)` = rows/columns x,y,z of the 4x4 Pauli channel (the I row/column is
trivial and never obstructs reduction, checked in `test_channel`). With V = M/sqrt2^k,
tr(sigma_i M sigma_j M^dag) is a real element of Z[w], i.e. p + q sqrt2 (real iff c = 0 and
d = -b, then value a + b sqrt2); dividing by 2^{1+k} = sqrt2^{2(1+k)} gives the stored
form, then `reduce()`. Global phase: V enters only through V(.)V^dag, so the Bloch and
channel matrices are phase-insensitive (the tex, lines 1845-1849). The sde of the Z[w]
unitary is invariant under the unit w (tested) but is computed on the literal matrix
product of the gate matrices below, with no phase normalisation.

## 3. Theorem B(a), the floor (lines 1813-1826)

> \item[(a)] For every semantics-exact optimizer $\mathcal{O}$ and every single-qubit
> Clifford+$T$ circuit $W$,
> $T\text{-count of } \mathcal{O}(W) \;\ge\; \tmin(\llbracket W \rrbracket) \;=\;
> \mathrm{lde}\big(\hat{W}\big)$,
> where $\hat W$ abbreviates the exact Bloch representation of $\llbracket W \rrbracket$, an
> exact floor computable per instance in $O(|W|)$ exact ring operations.

Implemented: `certificate(word)['floor']` (= `lde_channel`; for n = 1 also `lde_bloch` and
`t_min`, all equal). Part (b) (resynthesis benchmark 3 log2(1/eps)) needs the accuracy eps
of the word against a target, which is not a property of the circuit alone; not implemented.

## 4. Lemma valuation and Theorem linkage (lines 1995-2235)

Separated words and the Valuation Lemma (lines 1998-2010):

> Call a word \emph{separated} if it has the form
> $V = C_0\, Z_{m_1}\, C_1\, Z_{m_2}\, C_2 \cdots Z_{m_n}\, C_n$,
> where every $m_i$ is odd, the outer Cliffords $C_0, C_n$ are arbitrary, and every interior
> Clifford $C_1, \ldots, C_{n-1}$ lies outside $N$.
> \begin{lemma}[Valuation Lemma] Every separated word satisfies $\mathrm{lde}(\hat V) = n$,
> and hence $\tmin(V) = n$.

Normalizer (lines 1976-1981): `N = {C in C_1 : C Z C^dag = +-Z}`, "acting in $SO(3)$ as the
signed permutations fixing the axis $\pm\hat e_z$". Implemented: `in_normalizer(C)` tests
that column z of the 3x3 Bloch matrix is +-e_z. `eps(D)` (lines 2203-2206):

> Writing $\varepsilon(D) = +1$ if $D^\dagger Z D = Z$ projectively and $-1$ if
> $D^\dagger Z D = -Z$, one has $Z_m D = D\, Z_{\varepsilon(D)\,m}$

Implemented as the (z,z) entry of the Bloch matrix of D.

The finite verification of the lemma (lines 2070-2099) is reproduced by
`residue_automaton()`: states (Pbar, Qbar) in F_2^{3x3}, update
`(Pbar, Qbar) -> (Pbar Abar Cbar, (Pbar Bbar + Qbar Abar) Cbar)` with Abar the all-ones
upper 2x2 block and Bbar = diag(0,0,1), seeds (Cbar_0, 0) for the 24 Cliffords, criterion
`Pbar Abar = 0`. Results: 24 states (6 seed residues), 1536 transitions, 0 reducible; with
normalizer Cliffords admitted: 34 states, 10 reducible. All four numbers match lines
2080-2099. **CONVENTION**: the 34-state count is obtained when reducible states are also
expanded with the formal update (expanding only irreducible states gives 33 / 9).

Linkage procedure (lines 2196-2235):

> Bring an arbitrary single-qubit Clifford+$T$ word into phase--Clifford alternating form by
> Tier-1 fusion and by classifying every even phase as the Clifford it is, so that
> $w = C_0 Z_{m_1} C_1 \cdots Z_{m_n} C_n$ with all $m_i$ odd. Two moves are then available.
> \emph{Transport:} if some interior Clifford $D = C_i$ lies in $N$, use the conjugation
> identity to slide the phase through it. ...
> $Z_{m_i}\, D\, Z_{m_{i+1}} = D\, Z_{\varepsilon(D)\,m_i}\, Z_{m_{i+1}} =
> D\, Z_{\varepsilon(D)\,m_i + m_{i+1}}$ ... \emph{Absorption:} since two odd phases have an
> even signed sum, every merge produces an even phase, which is a Clifford; absorb it into
> the skeleton. ... Run the two moves in any order until neither applies, and call the
> result \emph{saturated}.
> \begin{theorem}[Linkage Theorem] For every single-qubit Clifford+$T$ word $w$,
> $\tmin(\llbracket w \rrbracket) = \#\{\text{odd phases surviving at saturation}\}$

Implemented: `linkage(word)`. Cliffords are carried as 3x3 integer Bloch matrices
(projective, exact). Odd letters t (m=1) and tdg (m=7) open a phase; every other letter is
multiplied into the current Clifford (Tier-1 fusion of a run of Z-rotations is subsumed:
the identity Clifford lies in N). Merges are applied left to right until none applies.
`certificate()` reports `linkage_t_min` and `linkage_agrees` (= lde of Bloch = lde of
channel), which is the content of the theorem and is checked on every test word.

## 5. Multi-qubit channel, Lemma mqval, Corollary cert, Theorem C (lines 2433-2747)

Channel (lines 2433-2439):

> for an $n$-qubit Clifford+$T$ operator $V$ and Pauli-group elements $\sigma, \tau$, set
> $\hat V_{\sigma\tau} \;=\; 2^{-n}\,\mathrm{tr}\big(\sigma\, V \tau V^\dagger\big)$,
> a $4^n \times 4^n$ matrix with entries in $\Zb[\sqrt2]$

Implemented twice: `channel_dense(U)` from the exact unitary (validation), and the
structured accumulator `channel_accumulate(word)` (Sec. numerics, lines 2852-2863: Clifford
channels applied as signed column permutations, pi/8 channels by local contraction of the
wire's 4x4 local channel with the column index). The two agree bit for bit on random n = 1,
2, 3 circuits (`test_channel`), as the tex requires at lines 4004-4011.

**CONVENTION**: Paulis are the Hermitian i^{x.z} X^x Z^z, indexed by
tau = sum_q 4^q p_q with p in {0:I, 1:X, 2:Y, 3:Z}; the register basis index is
sum_q b_q 2^q (qubit 0 = least significant bit, Qiskit order). Relabelling qubits or
changing the Pauli order permutes rows and columns of the channel and leaves lde unchanged.

Lemma mqval (lines 2454-2472):

> \item[(a)] The channel $\hat R_S$ acts as the identity on the commuting sector and as
> $\tfrac{1}{\sqrt2}(\mathrm{id} \pm T_S)$ on the anticommuting sector ... in particular
> $\mathrm{lde}(\hat R_S) = 1$.
> \item[(b)] Let $\hat V = (P + Q\sqrt2)/\sqrt2^{\,m}$ be reduced, and say that $P$ is
> \emph{pair-constant} if every row of $P \bmod 2$ is constant on each pair
> $\{\tau, S\tau\}$ of the anticommuting sector. Then $\mathrm{lde}(\hat V \hat R_S) = m$ if
> $P$ is pair-constant, and $\mathrm{lde}(\hat V \hat R_S) = m + 1$ otherwise.

Implemented: `pair_constant(P, n, wire)` for S = Z on one wire (the only pi/8 rotations in
the gate set are t and tdg); the criterion is evaluated before each T-type step and recorded
in `steps[j]['criterion_fired']`, with `lde_before`, `lde_after`, `collapsed`.
See Section 8 below: the "= m" half of (b) is **not** what the arithmetic gives.

Corollary cert (lines 2568-2575):

> For every $n$-qubit Clifford+$T$ element $V$, $\tmin(V) \;\ge\; \mathrm{lde}(\hat V)$,
> and the right-hand side is computable exactly from any word realizing $V$, in one channel
> multiplication per gate.

Theorem C (lines 2662-2688):

> \item[(a)] Each block is individually rigid: the channel of $B_i$ has
> $\mathrm{lde}(\hat B_i) = t(B_i)$ ...
> \item[(b)] Consequently every collapse along the assembled circuit, that is, every step at
> which the criterion of Lemma~\ref{lem:mqval}(b) fires, is a cross-block effect ...
> \item[(c)] For every semantics-exact optimizer $\mathcal{O}$, the fraction of $T$-count it
> can remove satisfies
> $\frac{t(C) - t(\mathcal{O}(C))}{t(C)} \;\le\; 1 - \frac{\mathrm{lde}(\hat C)}{t(C)}$

Implemented: `certificate(word, n)` returns `lde_channel` (= `floor`), `t_count`,
`max_removable_fraction` = 1 - lde/t(C), `certified_incompressible_fraction` = lde/t(C)
(the tex's Table `tab:e6` uses lde/T_tel with T_tel the post-`teleport_reduce` count, which
needs PyZX; from the circuit alone only lde/t(C) is available), `collapse_count`,
`collapse_rate` (collapses per T gate; tex lines 2766-2768 report "1.0--2.3%"),
`collapse_sizes`, and the per-step `steps`. Theorem C(a) for one block: `block_rigidity()`;
the MA grammar check used at lines 3923-3928: `is_matsumoto_amano()`.

## 6. Word order

**CONVENTION**: a word is the list g_1, ..., g_t and its unitary is the matrix product
g_1 g_2 ... g_t (the tex: "$W = g_1 g_2 \cdots g_t$ ... $\hat V_j = \hat g_1 \cdots \hat g_j$",
lines 2578-2581, and the channel is accumulated by right multiplication, lines 2501-2506).
OpenQASM lists gates in time order, so `word_from_qasm` reverses the list. For the gate set
used here every gate matrix is symmetric, so the reversed word implements the transpose,
whose channel is a signed-permutation conjugate of the transpose channel; the lde is
identical either way (tested), only the per-step trajectory differs.

## 7. Gate matrices

h = [[1,1],[1,-1]]/sqrt2, s = diag(1, w^2), sdg = diag(1, -w^2), t = diag(1, w),
tdg = diag(1, -w^3), x, y = [[0,-w^2],[w^2,0]], z, cx (control = first argument, local index
b_control + 2 b_target), cz, swap, id. Phases phi(T)=1, phi(S)=2, phi(Z)=4 as at lines
334-337; tdg = 7, sdg = 6.

## 8. Discrepancy with the tex found by the implementation

Lemma mqval(b) claims lde(V^ R^_S) = m when P is pair-constant, with the "exactly once"
refinement justified at lines 2524-2530:

> The remaining claim, that the reduction fires exactly once, so that the criterion never
> overshoots to $\mathrm{lde} < m$, is the one component we establish by exhaustive
> verification rather than structurally: on $400$ random step trials at $n = 1$ and $150$ at
> $n = 2$, the computed lde after a criterion-positive step equals $m$ in every case, with
> zero exceptions

This is contradicted by the simplest instance. V^ = T^ (m = 1), R_S = T: P of T^ is
[[1,-1,0],[1,1,0],[0,0,0]], every row is constant mod 2 on the pair {X,Y}, the criterion
fires, and T^ T^ = S^ has lde 0, not 1 (two reductions fire). At n = 1 this is forced by the
Linkage Theorem itself: a criterion-positive step merges the new phase with an earlier one,
the survivor count drops by one, and lde = t_min = m - 1 in every such case (625 of 625 in
the random test). At n = 2, 3, 4 both lde = m and lde = m - 1 occur (51 collapses: 44 of
size 2, 7 of size 1). The proven halves of the lemma hold in every test: the criterion
fires iff the lde fails to rise, and when it does not fire the lde rises by exactly one.
Nothing downstream in the tex uses the "= m" half (lines 2530-2535 say so), but the
statement of Lemma mqval(b) and the 400/150-trial claim need correction. The tests report
this under `NOTE  DISCREPANCY`.

## 9. Quoted numbers reproduced / not reproducible

Reproduced exactly: Clifford group order 24 and |N| = 8; residue automaton 24 / 6 / 1536 /
0 and 34 / 10; MA enumeration t <= 8 gives 18,384 words, 18,384 distinct projective elements,
histogram 24.[1,3,6,12,24,48,96,192,384], t_min = lde on each (lines 3934-3942); planted
family {T c T, T c T^dag}, 48 cases, fusion iff c in N (lines 2398-2402); separated words lde
= n (lines 3979-3984); unrestricted words: deficit n - lde always even (lines 3984-3989; the
69% figure depends on the random sample, 73% here); controlled-S channel lde 2 with
T-count 3 (lines 2556-2557); Fig. tiers THSSHT t_min 0; Fig. normalizer TST 0, T(HSSH)T 0,
THT lde 2; (HZ)^4 lde 0; lde(T^) = 1.

Not reproducible from the tex: Table `tab:barrier` (L, sde, t_min floor 22/89/497/2462,
separation factors) and the 24 instances with floors up to 568, because they are means over
Solovay--Kitaev words synthesised from undisclosed Haar targets on the coarse net; Table
`tab:e6` (needs qiskit QSD, pygridsynth and PyZX). `certificate_from_qasm` will take those
circuits when they are available as QASM.
