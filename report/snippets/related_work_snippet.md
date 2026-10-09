# Related work snippet (for report_short.md and report_v5.md)

Prepared 9 October 2026. Not applied to any report. Every reference below was checked on arXiv and, where a DOI exists, on Crossref on 9 October 2026. Numbers restated from the reports were recomputed from `results/certificates.csv` (see the end of this file).

## (a1) report_short.md, new Section 4.3 Related work

Placement: new subsection after 4.2, before Section 5. Reference numbers continue the short report's list (1 to 13).

```
### 4.3 Related work

`[F]` ZX-calculus optimisation rests on the graph-theoretic simplification of Duncan et al. (Reference 14) and on the phase teleportation of Kissinger and van de Wetering (Reference 3), which our P2 stage runs as PyZX teleport_reduce. `[F]` Staudacher et al. (Reference 15) and Chen et al. (Reference 16) change the ZX simplification to lower the two-qubit gate count. `[F]` Nägele and Marquardt train a graph-neural-network agent whose reward is the drop in the number of ZX-diagram nodes (Reference 17). `[F]` Riu et al. train an agent on the total or the two-qubit gate count of Clifford+T circuits and compare it with ZX heuristics (Reference 18). `[F]` Quarl learns rewrite sequences that cut the total and CNOT gate counts on the Nam and IBM gate sets (Reference 19), and Kremer et al. apply reinforcement learning to Clifford synthesis and routing (Reference 20). `[F]` AlphaTensor-Quantum minimises the T-count and can use gadgets (Reference 4). `[O]` In the parts of these works that we read, none prices its output with the H2 HQC formula or runs the pytket-quantinuum pass as a baseline. `[O]` This submission adds no new rewriting method. It adds a measured HQC ledger on H2 against the official pytket-quantinuum pass at optimisation levels 2 and 3. `[F]` Every output of families A, B1 and B2 passes an exactness check and a PyZX miter proves 18 of the 20 family C picks equal to their inputs.
```

## (a2) report_v5.md, related-work block

Placement: new subsection 3.4.1 at the end of Section 3.4, after the Table C2 discussion. Reference numbers continue the v5 list (1 to 17). Reference 16 (pytket documentation) and 17 (Gosset et al.) already exist.

```
### 3.4.1 Related work

`[F]` ZX-calculus circuit optimisation rests on two results. Duncan et al. simplify a ZX-diagram by local complementation and pivoting and extract a circuit from the reduced graph (Reference 18). Kissinger and van de Wetering move phases between spiders of a circuit without changing its two-qubit skeleton and so reduce the T-count (Reference 3). Our P2 stage runs this method as PyZX teleport_reduce. QuiZX is a Rust port of PyZX with Python bindings (Reference 26). We did not run it. pytket ships the pass ZXGraphlikeOptimisation (Reference 16), which Section 3.8.1 measures as ZXG.

`[F]` Two lines of work target the two-qubit gate count. Staudacher et al. add heuristics to ZX simplification that lower the two-qubit count of Clifford+T circuits and keep the T-count reduction (Reference 19). Chen et al. pursue the same count with dynamic grouping (Reference 20).

`[F]` Learned rewriting followed. Nägele and Marquardt encode the policy of a reinforcement-learning agent in a graph neural network. Its reward is the change in the number of ZX-diagram nodes. Their baselines are a greedy strategy, simulated annealing and PyZX full_reduce. Circuit extraction is not part of their training or evaluation (Reference 21). Riu et al. reward the total or the two-qubit gate count of Clifford+T circuits. They compare with ZX heuristics that include the one of Staudacher et al. and report circuits of up to 80 qubits and 2100 gates (Reference 22). Quarl is a learned optimiser on the Nam and IBM gate sets with total gate count as its cost. On the Nam gate set it reports geometric-mean reductions of 35.8 % in total gate count and 33.9 % in CNOT count (Reference 23). Kremer et al. use reinforcement learning to synthesise linear-function, Clifford and permutation circuits and to route circuits against SABRE (Reference 24). AlphaTensor-Quantum minimises the T-count through tensor decomposition and can use gadgets (Reference 25). Table C2 takes its values for the three Galois-field multipliers from that work.

`[O]` In the parts of these works that we read, the cost is a node count, a gate count or a T-count. None of them prices its output with the H2 HQC formula or runs the pytket-quantinuum pass as a baseline. `[O]` This submission adds no new rewriting method and no new selection mechanism. It adds a measured HQC ledger on H2. The baselines are the official pytket-quantinuum pass at optimisation levels 2 and 3, ZXGraphlikeOptimisation and Qiskit at level 3 (Section 3.8.1). `[F]` Every output of families A, B1 and B2 passes an exactness check against P0ref. A PyZX miter proves 18 of the 20 family C picks equal to their inputs (Section 3.8).

`[F]` Scope of the certificate. The floor is the least denominator exponent of the exact Pauli channel of the circuit (Reference 17). The channel of a unitary does not see its global phase. The floor therefore bounds from below the T-count of every Clifford+T circuit that realises the same unitary up to global phase on the same n qubits with no ancilla and no measurement. It says nothing about circuits that use ancillas, measurement or classical feedback. The "best with ancillas" column of Table C2 lies outside its scope. It was computed for 24 circuits with n at most 5. These are the 20 family B2 circuits at n = 2 and 3 and four family B1 circuits at n = 5. `[F]` T gates compile to Rz gates on H2 and the HQC formula of Section 1.2 charges no Rz gate. `[O]` The certificate therefore addresses the fault-tolerant layer only. It makes no statement about HQC cost.
```

## (b1) Reference entries for report_short.md (append after entry 13)

```
14. R. Duncan, A. Kissinger, S. Perdrix and J. van de Wetering, Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus, Quantum 4, 279 (2020), arXiv:1902.03178.
15. K. Staudacher, T. Guggemos, S. Grundner-Culemann and W. Gehrke, Reducing 2-QuBit Gate Count for ZX-Calculus based Quantum Circuit Optimization, EPTCS 394, 29 (2023), arXiv:2311.08881.
16. K. Chen et al., Quantum Circuit Optimization Based on Dynamic Grouping and ZX-Calculus for Reducing 2-Qubit Gate Count, arXiv:2507.14434.
17. M. Nägele and F. Marquardt, Optimizing ZX-diagrams with deep reinforcement learning, Mach. Learn.: Sci. Technol. 5, 035077 (2024), arXiv:2311.18588.
18. J. Riu, J. Nogué, G. Vilaplana, A. Garcia-Saez and M. P. Estarellas, Reinforcement Learning Based Quantum Circuit Optimization via ZX-Calculus, Quantum 9, 1758 (2025), arXiv:2312.11597.
19. Z. Li et al., Quarl: A Learning-Based Quantum Circuit Optimizer, Proc. ACM Program. Lang. 8, OOPSLA1 (2024), arXiv:2307.10120.
20. D. Kremer et al., Practical and efficient quantum circuit synthesis and transpiling with Reinforcement Learning, arXiv:2405.13196.
```

Optional FIND/REPLACE for entry 4 of report_short.md (adds the published venue of AlphaTensor-Quantum, which entry 4 cites by arXiv number only):

- FIND: `AlphaTensor-Quantum, arXiv:2402.14396.`
- REPLACE: `F. J. R. Ruiz et al., Quantum circuit optimization with AlphaTensor, Nat. Mach. Intell. 7, 374 (2025), arXiv:2402.14396.`

## (b2) Reference entries for report_v5.md (append after entry 17)

```
18. R. Duncan, A. Kissinger, S. Perdrix and J. van de Wetering, Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus, Quantum 4, 279 (2020), arXiv:1902.03178. Checked on arXiv and Crossref on 9 October 2026.
19. K. Staudacher, T. Guggemos, S. Grundner-Culemann and W. Gehrke, Reducing 2-QuBit Gate Count for ZX-Calculus based Quantum Circuit Optimization, EPTCS 394, 29-45 (2023), arXiv:2311.08881. Checked on arXiv and Crossref on 9 October 2026.
20. K. Chen, W. Liu, G. Xu, Y. Li, M. Li and S. He, Quantum Circuit Optimization Based on Dynamic Grouping and ZX-Calculus for Reducing 2-Qubit Gate Count, arXiv:2507.14434 (2025). No journal reference on the arXiv page on 9 October 2026.
21. M. Nägele and F. Marquardt, Optimizing ZX-diagrams with deep reinforcement learning, Mach. Learn.: Sci. Technol. 5, 035077 (2024), arXiv:2311.18588. Reward definition and baselines from the arXiv v3 HTML, read on 9 October 2026.
22. J. Riu, J. Nogué, G. Vilaplana, A. Garcia-Saez and M. P. Estarellas, Reinforcement Learning Based Quantum Circuit Optimization via ZX-Calculus, Quantum 9, 1758 (2025), arXiv:2312.11597. Rewards and baselines from the arXiv v4 HTML, read on 9 October 2026.
23. Z. Li, J. Peng, Y. Mei, S. Lin, Y. Wu, O. Padon and Z. Jia, Quarl: A Learning-Based Quantum Circuit Optimizer, Proc. ACM Program. Lang. 8, OOPSLA1, 555-582 (2024), arXiv:2307.10120. Reduction figures from the arXiv PDF, read on 9 October 2026.
24. D. Kremer, V. Villar, H. Paik, I. Duran, I. Faro and J. Cruz-Benito, Practical and efficient quantum circuit synthesis and transpiling with Reinforcement Learning, arXiv:2405.13196 (2024). No journal reference on the arXiv page on 9 October 2026.
25. F. J. R. Ruiz et al., Quantum circuit optimization with AlphaTensor, Nat. Mach. Intell. 7, 374-385 (2025), arXiv:2402.14396. Venue checked on Crossref on 9 October 2026.
26. QuiZX, Rust port of PyZX with Python bindings, https://github.com/zxcalc/quizx, read on 9 October 2026.
```

## (c) FIND/REPLACE for the certificate scope in report_short.md

Three sentences in report_short.md state the scope. The first is the one found by "every exact rewrite" and "99.7". The other two are optional for consistency.

1. Section 1.5, bullet "Where not to spend fault-tolerant compiler effort" (line 99).

- FIND: `The certified floor shows that every exact rewrite keeps at least 99.7 % of the pooled remaining T-count`
- REPLACE: `The certified floor shows that every Clifford+T circuit with the same unitary on the same qubits keeps at least 99.7 % of the pooled remaining T-count`

- FIND: `0.72 % on the worst instance. The certificate covers 24 circuits with n at most 5.` (the bare sentence also occurs in Section 7, line 359, so the FIND carries the preceding words)
- REPLACE: `0.72 % on the worst instance. The floor bounds the T-count of every Clifford+T circuit that realises the same unitary up to global phase on the same n qubits with no ancilla and no measurement. It covers 24 circuits with n at most 5. T gates compile to Rz on H2 and the HQC formula charges no Rz gate. The certificate therefore addresses the fault-tolerant layer only.`

2. Summary (line 16), optional.

- FIND: `bounds what any exact rewrite can still remove on 24 circuits with at most 5 qubits.`
- REPLACE: `bounds what any exact Clifford+T rewrite on the same qubits with no ancilla and no measurement can still remove. It covers 24 circuits with at most 5 qubits and addresses the fault-tolerant layer only, because the HQC formula charges no Rz gate.`

3. Section 2.5 (line 149), optional.

- FIND: `bounds from below the T-count of every rewrite that preserves C exactly.`
- REPLACE: `bounds from below the T-count of every Clifford+T circuit on the same n qubits that realises the unitary of C up to global phase with no ancilla and no measurement.`

## (d) Slide line

```
Related work. Learned ZX rewriters (Nägele and Marquardt 2024, Riu et al. 2025) and Quarl minimise node or gate counts. We add no new rewriter. We add an H2 HQC ledger against the official pytket-quantinuum pass with exactness proofs, and the known T-count floor of Gosset et al. on 24 circuits with n ≤ 5.
```

## Recomputation of restated numbers

`[F]` From `results/certificates.csv` (24 rows, all `invariant_ok = True`, largest n = 5, largest written T-count 4248). B2, 20 circuits at n = 2 and 3: pooled floor 41414 against pooled T after ZX 41534, fraction 0.99711, so at most 0.289 % removable. Worst B2 circuit haar_n3_eps1e-03_s5: 2478 of 2496, fraction 0.99279, so at most 0.721 % removable. B1, 4 circuits at n = 5: 47 against 106, fraction 0.44340. These agree with the 99.7 %, 0.3 %, 0.72 % and 0.443 of report_short.md.

## Unverifiable or not used

- "Tragler" and "Elsässer" as co-authors of the Staudacher paper: Unverifiable. arXiv:2311.08881 and Crossref list Staudacher, Guggemos, Grundner-Culemann and Gehrke. No paper with those co-authors was found.
- "IBM RL transpiler" as a named product and the IBM affiliation of Kremer et al.: not checked. The text names the authors only.
- "Google" as the origin of AlphaTensor-Quantum: affiliation not checked. The text names the method only.
- cflow-zx (Holker), cited by Riu et al. as their strongest ZX baseline: not checked, not used.
- A paper that introduces QuiZX: the README cites none, so the entry cites the repository.
- Year 2014 of Gosset et al. (existing entries 13 and 17): the Microsoft Research page gives Quantum Inf. Comput. 14, 1261-1276 and no year. The year was not rechecked.
- arXiv:1903.10477 carries the arXiv title "Reducing T-count with the ZX-calculus". Crossref gives the Phys. Rev. A 102, 022406 (2020) title "Reducing the number of non-Clifford gates in quantum circuits", which the reports already use.
