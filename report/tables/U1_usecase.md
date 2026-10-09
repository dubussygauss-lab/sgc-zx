`[F]` Grover use case. k is the number of Grover iterations. P_succ ideal is the noise-free success probability from the statevector. check is the exactness check of `pipelines/compile.py:check` on P0 and P2. HQC at 1000 shots with every qubit measured. Shots are those affordable within 10,000 HQC with at most 10,000 shots per job and 5 HQC per job. Hits are the expected marked-item hits within that budget at the ideal success probability. Source: `value/usecase.csv`.

| file | qubits | k | P_succ ideal | check | T written | T after ZX | n_2q P0 | n_2q PSEL | pick | HQC P0 | HQC PSEL | saved % | shots P0 | shots PSEL | hits P0 | hits PSEL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| grover_d5 | 7 | 4 | 0.999182 | unitary | 448 | 210 | 320 | 296 | P2 | 734.2 | 694.4 | 5.42 | 13699 | 14490 | 13687.8 | 14478.2 |
| grover_d6 | 9 | 6 | 0.996586 | statevector | 1008 | 436 | 720 | 672 | P2 | 1629.4 | 1548.6 | 4.96 | 6153 | 6475 | 6132.0 | 6452.9 |
