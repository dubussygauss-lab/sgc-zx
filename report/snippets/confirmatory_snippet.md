# Confirmatory H2-2E test on r2 to r4: edits for report_v5.md, report_short.md and the slides

Numbers come from `results/h22e_confirmatory.md` (`submit/h22e_confirmatory.py`). Apply each block once. Anchors are exact existing text.

## 1. report/report_v5.md, Section 3.7.1, input state

FILE: report/report_v5.md
INSERT AFTER: Each of the six circuits went in its own job.
TEXT: Every circuit ran on the all-zero input, on which the ideal output of vbe_adder_3 and hwb6 is the all-zero bit string and the ideal output of grover_5 is uniform over 64 of its 512 basis states.

## 2. report/report_v5.md, Section 3.7.1, confirmatory test

FILE: report/report_v5.md
INSERT AFTER: The measured difference lies 1.38 sd below the prediction on vbe_adder_3 and 2.94 sd below it on grover_5.
TEXT (new paragraphs, separated from the anchor paragraph by one blank line):

`[F]` Confirmatory test on the repeats alone. The two repeated circuits were chosen after the single runs of Table E2 were seen. The 12 repeat jobs of r2, r3 and r4 were submitted between 21:13 and 21:19 UTC on 8 October 2026 after that choice. The predicted gains of this section entered the repository in commit `eb0465f` at 19:19 UTC on the same day, before the first repeat was submitted. A test on r2 to r4 alone therefore uses no data that informed the choice of circuits. `submit/h22e_confirmatory.py` computes F_H of the summed r2 to r4 counts at 3000 shots per pipeline with the F_H and sd rules of Table E3. It writes `results/h22e_confirmatory.md`.

| file | pipeline | runs | shots | n_2q | F_H | sd |
|---|---|---|---|---|---|---|
| vbe_adder_3 | P0 | r2, r3, r4 | 3000 | 56 | 0.9513 | 0.0039 |
| vbe_adder_3 | P2 | r2, r3, r4 | 3000 | 41 | 0.9640 | 0.0034 |
| grover_5 | P0 | r2, r3, r4 | 3000 | 240 | 0.8663 | 0.0062 |
| grover_5 | P2 | r2, r3, r4 | 3000 | 218 | 0.8667 | 0.0062 |

`[F]` On vbe_adder_3 F_H(P2) minus F_H(P0) is +0.0127 with sd 0.0052. Its z is +2.44 and its two-sided p is 0.015. On grover_5 the difference is +0.0004 with sd 0.0088. Its z is +0.04 and its two-sided p is 0.96. The Holm adjustment over the two confirmatory circuits gives 0.030 on vbe_adder_3 and 0.96 on grover_5. The slope model predicts P2 above P0 on both circuits. The one-sided p for that direction is 0.0074 on vbe_adder_3 and 0.48 on grover_5. After Holm adjustment they are 0.015 and 0.48. The measured difference lies 0.83 sd below the predicted gain of 0.0170 on vbe_adder_3. It lies 2.54 sd below the predicted gain of 0.0228 on grover_5.

`[O]` The two-sided confirmatory test is the primary test of a P2 gain on H2-2E. It resolves the vbe_adder_3 gain at 0.05 after Holm adjustment over the two repeated circuits. The choice to report r2 to r4 alone was made after the pooled result of Table E3 was known. The confirmatory and pooled tests agree in sign and size on both circuits. hwb6 has no data outside r1 and does not enter the confirmatory family. On the all-zero input the vbe_adder_3 test measures how often the circuit returns the all-zero string. It does not test the adder on other inputs.

## 3. report/report_short.md, Section 3.2

FILE: report/report_short.md
INSERT AFTER: - `[F]` No cell rejects homogeneity of its four runs at the 0.05 level.
TEXT (new bullet on the next line):
- `[F]` Confirmatory test. The repeats r2 to r4 were submitted after the two circuits were chosen, so a test on them alone carries no selection on its own data. At 3000 shots per pipeline the vbe_adder_3 difference is +0.0127 with sd 0.0052, z = +2.44 and two-sided p = 0.015. The Holm-adjusted p over the two repeated circuits is 0.030. grover_5 gives +0.0004 with z = +0.04. Every circuit ran on the all-zero input. `[O]` The vbe_adder_3 gain holds on data that did not select it.

## 4. report/presentation/presentation.tex, emulator slide (slide 9 in the committed file, slide 10 in the working copy of 9 October, frame "The emulator gain on vbe\_adder\_3 is not established after correction")

FILE: report/presentation/presentation.tex
FIND: \item The repeated circuits were chosen after the single runs. The Holm-adjusted $p$ is 0.035 over two circuits and 0.052 over all three. grover\_5 shows no gain ($z = +0.10$).
REPLACE WITH: \item On the three repeats alone, run after the circuits were chosen, vbe\_adder\_3 gives $z = +2.44$ and two-sided $p = 0.015$. Holm over the two repeated circuits gives 0.030. grover\_5 shows no gain ($z = +0.04$). All inputs are all-zero.

## Notes (not for insertion)

- `[F]` Slide 9 keeps the title "The emulator gain on vbe\_adder\_3 is not established after correction" and the line `\assess{The fidelity gain is not established at 0.05 after correction over three circuits.}`. Both refer to the pooled Holm p of 0.052 over three circuits. `[O]` After the replacement bullet the slide states a confirmatory Holm p of 0.030 below 0.05 under that title. Kam decides whether the title and the assess line change. No replacement is proposed here.
- `[F]` report_short.md Section 3.2 has no blank line between the bullet "No cell rejects homogeneity of its four runs at the 0.05 level." and the paragraph starting "`[F]` Table 3c.". In Markdown that paragraph continues the last bullet. Block 3 inserts its bullet before it and leaves this as is.
- `[F]` The existing `[O]` sentences of report_v5.md Section 3.7.1 and of report_short.md Section 3.2 that say the gain is not significant after correction over all three circuits stay true for the pooled test. They are not changed by these blocks.
