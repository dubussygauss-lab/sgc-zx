# Mechanism snippet: ZX stage on top of pytket level 3

Source: value/mechanism_zx_l3.md (180 A, 14 B1, 15 C circuits with all pipelines).

## Report sentences

1. [F] pytket-quantinuum level 3 runs GreedyPauliSimp, which rebuilds the circuit as Pauli gadgets with phase folding and keeps the result only when it lowers the two-qubit count. It was kept on 180 of 180 A, 13 of 14 B1 and 9 of 15 family C circuits.
2. [F] PyZX teleport_reduce cuts the input T-count by 42.38 % on B1 and 36.20 % on family C and leaves the Trotter circuits of family A unchanged.
3. [F] On B1 level 3 leaves 746 non-Clifford gates against 656 after P2, so GreedyPauliSimp does not reproduce the phase merging of teleport_reduce there.
4. [F] Level 3 still beats P2 because it removes two-qubit gates: 196.0 of the 234.2 HQC that L3 saves over P2 on 11 B1 circuits and 486.0 of 554.8 on 8 family C circuits come from n_2q.
5. [F] Where P2L3 beats L3, the gap is 67.4 HQC on 4 B1 circuits and 23.6 on 3 family C circuits, again mostly from n_2q (60.0 and 20.0).
6. [F] The ZX-only gain falls with T-density across 29 B1 and C circuits (Spearman rho -0.44, p 0.016), with 0.20 % above the median T-density and 2.72 % below it.
7. [O] The hypothesis that level 3 already does what teleport_reduce does holds for the two-qubit count and fails for the non-Clifford count on B1, so the two passes merge different phases.

## Slide bullets

- [F] Level 3 beats P2 through two-qubit resynthesis (196.0 of 234.2 HQC on B1, 486.0 of 554.8 on C) and not through phase merging.
- [O] teleport_reduce still removes non-Clifford gates that level 3 keeps (746 after L3, 701 after P2L3 on B1), but this rarely lowers HQC.
