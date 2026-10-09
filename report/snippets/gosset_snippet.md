# Gosset et al. citation snippets for report_v5.md, report_short.md and presentation.tex

Source checks behind these snippets (for the main agent, not for pasting):

- `[F]` Gosset, Kliuchnikov, Mosca, Russo, arXiv:1308.4134v1 (the only arXiv version). Section 2.3, eq. (2.3), defines the channel representation U^_rs = 2^-n Tr(P_r U P_s U^dag). Definition 1 (Section 4) defines sde of a matrix as the maximum sde of its entries. Theorem 1 (Section 4) reads "The T-count of a single-qubit unitary U ∈ J1 is T(U) = sde(U^)". Section 6 reads "This characterization does not appear to generalize to n > 1 qubits; for example, the sde of the channel representation of the Toffoli gate is 2 but its T-count is 7."
- `[F]` The paper states no numbered n-qubit inequality T(U) >= sde(U^). It follows in one line from Proposition 1 and the Remark eq. (3.6), which write U^ as T(U) factors R(P)^ times a Clifford channel. Each R(P)^ has sde 1 and a Clifford channel has sde 0.
- `[F]` `barrier/certificate.py` computes the same matrix (`channel_dense`, V^_στ = 2^-n tr(σ V τ V^dag)). Its `lde` equals the GKMR max-entry sde on 30 of 30 random words at n = 1 and 2 (check script in the session scratchpad, not committed). On the 7-T Toffoli word of GKMR Figure 5.1 (checked equal to Toffoli up to phase) `certificate()` returns floor 2, the GKMR value.
- `[F]` arXiv:2608.22801 does not cite arXiv:1308.4134 (no hit for "Gosset", "Russo" or "1308.4134" in the arXiv source or in `papers/barrier/main.tex`).
- `[F]` Label map. The arXiv PDF numbers the results. Corollary cert is Corollary 2, Theorem C is Theorem 6, Theorem B is Theorem 3, Lemma mqval is Lemma 8, Lemma bridge is Lemma 1. Section "Multi-Qubit Rigidity" is Section VII. `[O]` The reports cite the LaTeX labels, which a reader of the arXiv PDF cannot see. The snippets below add the PDF numbers once per section.
- `[F]` Numbers used below, recomputed from `results/certificates.csv`. Pooled B2 floor 41414 against 41534 T after ZX, ratio 0.99711. Largest B2 T written 4248. Worst B2 instance haar_n3_eps1e-03_s5, 2478 against 2496.

## (a) Reference entries

report_v5.md, append to the list under `## References` as entry 17 (after entry 16):

```
17. D. Gosset, V. Kliuchnikov, M. Mosca and V. Russo, An algorithm for the T-count, Quantum Inf. Comput. 14, 1261 (2014), arXiv:1308.4134. Channel representation in Section 2.3, Definition 1 and Theorem 1 in Section 4, Toffoli example in Section 6. `[F]` arXiv:1308.4134 resolves to this title, fetched 9 October 2026.
```

report_short.md, append to the list under `## References` as entry 13 (after entry 12):

```
13. D. Gosset, V. Kliuchnikov, M. Mosca and V. Russo, An algorithm for the T-count, Quantum Inf. Comput. 14, 1261 (2014), arXiv:1308.4134.
```

`[O]` The page number 1261 is from memory and was not checked against the journal. Drop ", 1261" if it cannot be confirmed before submission.

## (b) Report text

### report_v5.md, Section 2.5

FIND: `[F]` The barrier manuscript (arXiv:2608.22801) gives the floor in Theorem B(a) for one qubit and in Corollary cert for any n.

REPLACE WITH: `[F]` The floor is the channel-representation bound of Gosset, Kliuchnikov, Mosca and Russo (Reference 17). The barrier manuscript (arXiv:2608.22801) restates it in Theorem B(a) for one qubit and in Corollary cert for any n (Theorem 3(a) and Corollary 2 in the arXiv PDF).

INSERT AFTER: The floor is computed from any word realising C, in one exact channel multiplication per gate, and does not depend on the word chosen.

TEXT:

`[F]` Gosset et al. define the same matrix C^ (Reference 17, Section 2.3) and call lde(C^) its smallest denominator exponent (Definition 1). For one qubit their Theorem 1 states that the T-count equals it. They state no numbered bound for n qubits. The bound T-count >= lde(C^) follows from their Proposition 1. That proposition writes the unitary as a Clifford times one factor R(P) per T gate, and each factor raises the exponent by at most one. Gosset et al. also give a gate on which the bound is not tight. The Toffoli gate has exponent 2 and T-count 7 (their Section 6). `barrier/certificate.py` returns floor 2 on a 7-T Toffoli word. `[O]` The floor is therefore a known bound and this submission does not claim it as new. The submission adds its exact evaluation on synthesised circuits with up to 4248 T gates and the measured gap to the PyZX output. Parts (a) and (b) of Theorem C come from arXiv:2608.22801 and do not change the value of the floor.

### report_v5.md, Section 3.4

FIND: The theorem bounds the T-count of every exact rewrite from below by the denominator exponent of the channel.

REPLACE WITH: The channel bound of Gosset et al. (Reference 17), restated as Corollary cert of arXiv:2608.22801, bounds the T-count of every exact rewrite from below by the denominator exponent of the channel.

INSERT AFTER: The manuscript's percentages are stated for synthesised circuits only and the B1 rows are not covered by them.

TEXT:

`[F]` Gosset et al. report the same looseness on the Toffoli gate, with exponent 2 against T-count 7 (Reference 17, Section 6). `barrier/certificate.py` gives floor 2 on a 7-T Toffoli word.

### report_short.md, Section 2.5

FIND: `[F]` Corollary cert and Theorem C(c) of the exactness-barrier manuscript of Kam et al. give a per-instance floor (arXiv:2608.22801).

REPLACE WITH: `[F]` The per-instance floor is the channel-representation bound of Gosset, Kliuchnikov, Mosca and Russo (Reference 13). Corollary cert and Theorem C(c) of the exactness-barrier manuscript of Kam et al. restate it for n qubits and as a bound on the removable fraction (arXiv:2608.22801, Corollary 2 and Theorem 6(c) in the PDF).

INSERT AFTER: The least denominator exponent of that matrix bounds from below the T-count of every rewrite that preserves C exactly.

TEXT:

`[F]` Gosset et al. call this exponent the smallest denominator exponent and prove that it equals the T-count for one qubit (Reference 13, Theorem 1). For n qubits the bound follows from their Proposition 1. It is not tight on every gate. The Toffoli gate has exponent 2 and T-count 7 (their Section 6).

### report_short.md, Section 4.1

INSERT AFTER: The floor is at or below the T-count after ZX on all 24 rows.

TEXT:

`[F]` The bound is that of Gosset et al. (Reference 13). `[O]` The contribution here is its exact evaluation on synthesised circuits with up to 4248 T gates and the measured gap to the PyZX output. The bound itself is not new.

## (b2) Other places in the same reports that carry the same attribution

These lie outside the four sections named in the task. Apply them only if the main agent approves the wider edit.

report_v5.md, Section 1.3:

FIND: `[F]` The exactness-barrier manuscript gives a per-instance floor (Kam et al., arXiv:2608.22801).

REPLACE WITH: `[F]` The per-instance floor is the channel bound of Gosset et al. (Reference 17), restated for n qubits in the exactness-barrier manuscript (Kam et al., arXiv:2608.22801).

report_v5.md, Section 7:

INSERT AFTER: An approximate resynthesis to a new precision is outside the scope of the certificate.

TEXT:

`[F]` The floor is the known channel bound of Gosset et al. (Reference 17). The certificate adds its evaluation on these 24 circuits and no new bound.

report_short.md, Summary:

FIND: `[F]` A certified T-count floor from the team's exactness-barrier theorem bounds what any exact rewrite can still remove on 24 circuits with at most 5 qubits.

REPLACE WITH: `[F]` The channel lower bound of Gosset et al. on the T-count, restated in the team's exactness-barrier manuscript, bounds what any exact rewrite can still remove on 24 circuits with at most 5 qubits.

report_short.md, Section 4.2:

FIND: `[O]` This submission pairs that comparison in HQC with a per-instance lower bound on the T-count.

REPLACE WITH: `[O]` This submission pairs that comparison in HQC with the known per-instance lower bound of Gosset et al. on the T-count, evaluated on 24 circuits.

## (c) presentation.tex, fault-tolerant slide

`[F]` The slide "A certified floor bounds what exact T optimisation can still gain" contains no novelty phrase. `[O]` No narrowing is required. The slide does not attribute the bound. The replacement below adds the attribution.

FIND:

```
    \item On 20 synthesised Haar circuits of 2 and 3 qubits the certified floor is 0.997 of the T-count after ZX, pooled. The worst instance keeps at least 2478 of its 2496 T gates.
```

REPLACE WITH:

```
    \item The floor is the channel bound of Gosset et al.\ (2014). On 20 synthesised Haar circuits of 2 and 3 qubits it is 0.997 of the T-count after ZX, pooled. The worst instance keeps at least 2478 of its 2496 T gates.
```
