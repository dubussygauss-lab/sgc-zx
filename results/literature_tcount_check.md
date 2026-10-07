# Literature T-count check for family B1 (2026-10-07)

Source: A. Kissinger and J. van de Wetering, arXiv:1903.10477v3 (arXiv title "Reducing T-count with the ZX-calculus"; DOI 10.1103/PhysRevA.102.022406, i.e. Phys. Rev. A 102, 022406 (2020)). PDF fetched from https://arxiv.org/pdf/1903.10477v3 and converted with `pdftotext -layout`. `[F]`

Table found: Table 1, page 4. Columns: `Circuit | n | T | Best prev. | Method | PyZX | PyZX+TODD`. Caption (quoted): "Benchmark circuits. The columns n and T contain the amount of qubits and T gates in the original circuit. Best prev. is the previous best-known ancilla-free T-count for that circuit and Method specifies which method was used: RMm and RMr refer to the maximum and recursive Reed-Muller decoder of Ref. [8], Tpar is Ref. [6], TODD is Ref. [21] and NRSCM refers to Ref. [28]. PyZX and PyZX + TODD specify the T-counts produced by the procedures outlined in the Methods section." `[F]`

Our values: `t_count_as_written` from `bench/family_B1/manifest.csv`; `t_count_zx` from `results/family_B1_counts.csv`, rows with `pipeline == P2`. `[F]`

## Comparison

| B1 circuit | Paper row (quoted) | n | T (orig) | Best prev. (method) | PyZX | PyZX+TODD | our t_count_as_written | our t_count_zx | orig match | PyZX match |
|---|---|---|---|---|---|---|---|---|---|---|
| barenco_tof_3 | `barenco-tof3 [27]  5  28  16  Tpar  16  16` | 5 | 28 | 16 (Tpar) | 16 | 16 | 28 | 16 | yes | yes |
| mod5_4 | `mod54 [27]  5  28  16  Tpar  8  7` | 5 | 28 | 16 (Tpar) | 8 | 7 | 28 | 8 | yes | yes |
| qft_4 | absent | - | - | - | - | - | 69 | 67 | absent | absent |
| tof_3 | `tof3 [27]  5  21  15  Tpar  15  15` | 5 | 21 | 15 (Tpar) | 15 | 15 | 21 | 15 | yes | yes |
| barenco_tof_4 | `barenco-tof4 [27]  7  56  28  Tpar  28  28` | 7 | 56 | 28 (Tpar) | 28 | 28 | 56 | 28 | yes | yes |
| hwb6 | `hwb6 [3]  7  105  75  Tpar  75  72` | 7 | 105 | 75 (Tpar) | 75 | 72 | 105 | 75 | yes | yes |
| tof_4 | `tof4 [27]  7  35  23  Tpar  23  23` | 7 | 35 | 23 (Tpar) | 23 | 23 | 35 | 23 | yes | yes |
| barenco_tof_5 | `barenco-tof5 [27]  9  84  40  Tpar  40  40` | 9 | 84 | 40 (Tpar) | 40 | 40 | 84 | 40 | yes | yes |
| grover_5 | absent | - | - | - | - | - | 336 | 166 | absent | absent |
| mod_mult_55 | `mod-mult-55 [27]  9  49  28  TODD  35  20` | 9 | 49 | 28 (TODD) | 35 | 20 | 49 | 35 | yes | yes |
| tof_5 | `tof5 [27]  9  49  31  Tpar  31  31` | 9 | 49 | 31 (Tpar) | 31 | 31 | 49 | 31 | yes | yes |
| vbe_adder_3 | `vbe-adder3 [27]  10  70  24  Tpar  24  24` | 10 | 70 | 24 (Tpar) | 24 | 24 | 70 | 24 | yes | yes |
| mod_red_21 | `mod-red-21 [27]  11  119  73  Tpar  73  73` | 11 | 119 | 73 (Tpar) | 73 | 73 | 119 | 73 | yes | yes |
| gf2^4_mult | `gf(24 )-mult [27]  12  112  56  TODD  68  52` | 12 | 112 | 56 (TODD) | 68 | 52 | 112 | 68 | yes | yes |
| hwb8 | `hwb8 [3]  12  5887  3531  RMm&r  3517  3501` | 12 | 5887 | 3531 (RMm&r) | 3517 | 3501 | 5887 | 3517 | yes | yes |

(`gf(24 )` is the pdftotext rendering of gf(2^4).) `[F]`

## Findings

1. `[F]` 13 of 15 B1 circuits appear in Table 1. For all 13, our `t_count_as_written` equals the paper's T column and our `t_count_zx` (P2) equals the paper's PyZX column. No value differs.
2. `[F]` The paper's PyZX column is worse than Best prev. for mod_mult_55 (35 vs 28) and gf2^4_mult (68 vs 56); our P2 values reproduce the PyZX numbers, not the best-known ones.
3. `[F]` grover_5 and qft_4 are absent from Table 1 of arXiv:1903.10477v3. The PyZX paper arXiv:1904.04735 has no T-count benchmark table and does not name these circuits (checked via WebFetch of the PDF). The upstream pyzx README (raw.githubusercontent.com/zxcalculus/pyzx/master/README.md and readme.md) returned 404 / empty, so no README benchmark table could be consulted.
4. `[F]` Secondary check, not the paper: the Quantinuum pyzx fork ships PyZX-optimised circuits at `third_party/pyzx-fork/circuits/optimized/<name>_pyzx.qc` (commit e695d6d7, 2023-01-23). Counting lines beginning with `T ` or `T* ` (all `Z` gates there have at most two arguments, so no CCZ is hidden) gives grover_5 166, qft_4 67, and for the other 13 circuits the same numbers as the paper's PyZX column. All 15 agree with our `t_count_zx`.
5. `[O]` Report Section 3.2 claim "tof_3 15, mod5_4 8, vbe_adder_3 24" is supported by Table 1. The grover_5 166 value is not attributable to the PRA paper; it should be cited to the pyzx repository's `circuits/optimized/grover_5_pyzx.qc` or marked as our own computation. The citation's arXiv title is "Reducing T-count with the ZX-calculus"; "Reducing the number of non-Clifford gates in quantum circuits" is the journal title.
