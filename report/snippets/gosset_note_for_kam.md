# Gosset et al. and the barrier manuscript (note for Kam, changes nothing)

## Does arXiv:2608.22801 cite Gosset et al.?

`[F]` No. "Gosset", "Russo" and "1308.4134" do not occur in the arXiv source of 2608.22801 or in `papers/barrier/main.tex`.

## What Gosset et al. (arXiv:1308.4134, QIC 14, 2014) state

- `[F]` Section 2.3, eq. (2.3). Channel representation U^_rs = 2^-n Tr(P_r U P_s U^dag). This is the matrix of Corollary 2 (label cor:cert) in Section VII of 2608.22801.
- `[F]` Definition 1 (Section 4). sde of a matrix over Z[1/sqrt2] is the maximum entry sde. This equals the manuscript's lde. `barrier/certificate.py` agrees with the max-entry definition on 30 of 30 random words.
- `[F]` Theorem 1 (Section 4). "The T-count of a single-qubit unitary U ∈ J1 is T(U) = sde(U^)."
- `[F]` Section 6. "the sde of the channel representation of the Toffoli gate is 2 but its T-count is 7." `certificate.py` returns floor 2 on the 7-T Toffoli word.
- `[F]` No numbered n-qubit inequality T(U) >= sde(U^) appears. It follows in one line from their Proposition 1 and Remark eq. (3.6).
- `[F]` Mosca and Mukhopadhyay (arXiv:2006.12440v3), Section 3, Fact 5. For W^ = R(P)^ V^, "sde(W) = sde(V) ± 1 or sde(W) = sde(V)". Their T-count heuristic starts its search at m = sde(U^) (Section 5). The manuscript does not cite this paper either.

## How 2608.22801 positions its results

- `[F]` Section II, after Lemma 1 (label lem:bridge). Lemma 1 states T_min(V) = lde(V^) for one qubit. The text attributes it to Matsumoto-Amano, Giles-Selinger and Kliuchnikov-Maslov-Mosca. GKMR Theorem 1 is the same statement in the channel representation and is not cited.
- `[F]` Section VII, before Corollary 2. "What does survive is the inequality, and it survives with nothing attached". Corollary 2 then states T_min(V) >= lde(V^) for every n-qubit Clifford+T element, with no prior-work citation.
- `[F]` Section VII. "The single-qubit identity T_min = lde already fails at two qubits, and the smallest counterexample is a gate one would never suspect. The controlled-S gate has channel lde equal to 2 ... while its minimal T-count is 3." GKMR Section 6 makes the same point with the Toffoli gate.
- `[F]` Section V, before Theorem 3. "An invariant of the element is untouchable by transformations that preserve the element. This is the entire content of the barrier". `[O]` Semantic exactness of the optimiser therefore adds nothing to the bound itself.
- `[F]` Abstract. "We show that both behaviours follow from a single bound." Introduction. "Underlying this is a single bound, which we state first because both behaviours turn out to be instances of it."

## What the manuscript adds beyond Gosset et al.

- `[O]` The floor (Corollary 2) and Theorem 6(c) add nothing as bounds. Theorem 6(c) is Corollary 2 divided by t(C).
- `[O]` Theorem 6(a) combines known single-qubit facts (Matsumoto-Amano blocks are T-optimal, Lemma 1) with a tensor embedding. Theorem 6(b) is an attribution of collapses to cross-block residue. Neither changes the floor value.
- `[O]` The pair-constancy criterion of Lemma 8(b) is a mod-2 matrix form of the entry rule in Mosca-Mukhopadhyay Facts 2 and 3. I cannot decide from these sources whether it is new.
- `[O]` The new material is the per-instance application to QSD+gridsynth circuits and the explanation of the null ZX result of Hao, Xu and Tannu. Theorems 1, 2, 4 and 5 and Lemmas 2 to 7 are outside this check.

## Decisions for Kam

1. Cite Gosset et al. at Lemma 1 and at Corollary 2, and state that Corollary 2 is their channel bound written for n qubits.
2. Cite Gosset et al. Section 6 (Toffoli, sde 2 against 7) next to the controlled-S example. The claim "the smallest counterexample" is not checked here.
3. The pending correction of Lemma 8(b) (`barrier/NOTES.md` section 8, "= m" fails on T T) can cite Mosca-Mukhopadhyay Fact 5. Fact 5 already allows the drop by one that the implementation observed.
4. Decide whether the abstract and introduction keep "a single bound" as the headline or present it as a known bound with a new application.
5. The submission reports cite the LaTeX labels (Corollary cert, Theorem C). The arXiv PDF shows Corollary 2 and Theorem 6. The snippets add the PDF numbers.
