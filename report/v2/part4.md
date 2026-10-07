## 5. Reproducibility

`[F]` Environment, confirmed with `pip show` on 7 October 2026 in the development container:

| Package | Version |
|---|---|
| Python | 3.13.16 |
| pytket | 2.18.4 |
| pytket-quantinuum | 0.59.3 |
| pyzx (PyPI) | 0.10.7 |
| Quantinuum pyzx fork (family B1 sources only, `third_party/pyzx-fork/`) | commit e695d6d7 |
| qiskit | 2.5.2 |
| pygridsynth | 2.0.0 |
| selene-sim | 0.3.4 |
| guppylang | 1.1.2 |
| hugr | 0.18.8 |
| numpy | 2.5.3 |
| pandas | 2.3.3 |
| scipy | 1.18.1 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| aqora | 0.35.1 |
| qnexus | 0.51.1 |
| marimo | 0.25.1 |

`[F]` Seeds. `numpy.random.default_rng(20261006)` generates the family A couplings (`bench/gen_trotter.py`, `SEED`) and the family B2 Haar targets (`bench/gen_haar_b2.py`, `SEED`), with `seed_transpiler=0` in the qiskit transpile call of B2. Each generator draws from one stream in a fixed order, so the instance set does not depend on the order of writing. `noise/run_proxy.py` uses `default_rng(0)` only to pick the circuits of its parser self-check. `selene/run_selene.py` seeds every Selene run with `sha256("<pipeline>/<file>/<tag>")[:4]` and stores the value in the column `seed`. `model/cost_model.py` uses seed 0 for the fold assignment and `random_state=0` for the gradient-boosting model.

`[F]` Scripts, all run from the repository root. Inputs and outputs are the paths each script reads and writes.

| Step | Command | Inputs | Outputs |
|---|---|---|---|
| Family A circuits | `python bench/gen_trotter.py` | none (seed 20261006) | `bench/family_A/*.qasm`, `*_meas.qasm`, `*.npy`, `manifest.csv` |
| Family B1 circuits | `python bench/build_family_B1.py` | `third_party/pyzx-fork/circuits/` | `bench/family_B1/*.qasm`, `manifest.csv` |
| Family B2 circuits | `python bench/gen_haar_b2.py` | none (seed 20261006) | `bench/family_B2/*.qasm`, `*_target.npy`, `manifest.csv` |
| Family A compilation | `python pipelines/run_bench.py --workers 2` | `bench/family_A/` | `results/family_A_counts.csv`, `results/family_A_summary.csv`, `results/compiled/<pipeline>/*.qasm` |
| Family B1 compilation | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900` | `bench/family_B1/` | `results/family_B1_counts.csv`, `results/family_B1_summary.csv`, `results/compiled/<pipeline>/*.qasm` |
| hwb8 long run | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --files hwb8 --pipelines P1,P2 --prefix family_B1_hwb8_long --timeout 5400 --workers 2` | `bench/family_B1/hwb8.qasm` | `results/family_B1_hwb8_long_counts.csv`, `results/family_B1_hwb8_long_summary.csv`, `results/family_B1_hwb8_long_run.log` |
| Family B2 compilation | `python pipelines/run_b2.py --workers 2` | `bench/family_B2/` | `results/family_B2_counts.csv` |
| Noise proxy, family A | `python noise/run_proxy.py --noise h22e --family A --workers 2` | `results/compiled/{P0ref,P0,P1,P2,P3}/`, `bench/family_A/*.npy` | `results/family_A_proxy_h22e.csv` |
| Noise proxy, family B1 | `python noise/run_proxy.py --noise h22e --family B1 --workers 2` | `results/compiled/{P0ref,P0,P1,P2,P3}/`, `bench/family_B1/manifest.csv` | `results/family_B1_proxy_h22e.csv` |
| Proxy figure | `python noise/run_proxy.py --figure-h22e` | the two proxy CSVs | `results/fig_proxy_h22e.{pdf,png}`, `results/proxy_h22e_fits.log` |
| Certificates | `python barrier/run_certificates.py` | `bench/family_B2/*.qasm`, `bench/family_B1/{barenco_tof_3,mod5_4,qft_4,tof_3}.qasm`, `results/family_B2_counts.csv`, `results/family_B1_counts.csv` | `results/certificates.csv`, `results/certificates.md` |
| Selene runs | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene.py --mode both --procs 2 --shots 2000` | `results/compiled/{P0,P1,P2}/`, `bench/family_A/*.npy`, `bench/family_B1/manifest.csv`, the two proxy CSVs | `results/selene_noiseless.csv`, `results/selene_depolarizing.csv`, `results/selene_run.log` |
| Selene summary | `python selene/make_summary.py` | the two Selene CSVs, `results/selene_calibration.txt`, `results/selene_recheck.txt` | `results/selene.md` |
| Cost model | `python model/cost_model.py` | `results/family_A_proxy_h22e.csv`, `results/family_B1_proxy_h22e.csv` | `results/cost_model_metrics.csv`, `results/cost_model_coefficients.csv`, `results/cost_model.md`, `results/fig_cost_model.{pdf,png}` |
| Tables and figures | `python report/make_tables.py` | `results/*.csv` | `report/tables/*.md`, `report/figures/*.png`, injected into the report |
| Emulator jobs | notebook section 3, gated behind the run button | `results/compiled/{P0,P2}/` | `[PENDING: emulator]` |

`[F]` The Selene command clears every proxy variable because Selene streams its results over a local TCP socket that the container proxy intercepts (`results/selene.md`, section 1).

`[F]` Tests. Each file was run once on 7 October 2026 with the versions above. Five files run as scripts and `selene/test_selene.py` runs under pytest.

| File | Command | Result | Wall time |
|---|---|---|---|
| `bench/test_gen_trotter.py` | `python bench/test_gen_trotter.py` | 12 of 12 passed | 58 s |
| `noise/test_dm_sim.py` | `python noise/test_dm_sim.py` | 17 of 17 passed | 3 s |
| `barrier/test_certificate.py` | `python barrier/test_certificate.py` | 69 of 69 checks passed | 29 s (44 s in `results/verification_2026-10-07.md`) |
| `pipelines/test_compile.py` | `python pipelines/test_compile.py` | 6 of 6 passed | 2 s |
| `selene/test_selene.py` | proxy variables cleared, `python -m pytest selene/test_selene.py -q` | 6 of 6 passed (5 functions, one parametrised twice) | 7 s |
| `model/test_cost_model.py` | `python model/test_cost_model.py` | 7 of 7 passed | under 1 s |

`[F]` The compile tests check every pipeline against the unitary of the input and check that the measured QASM encodes the implicit qubit permutation left by `allow_swaps=True`. The certificate tests reproduce the finite verifications of the barrier manuscript (the counts 24, 1536 and 18384). The Selene tests check the bit order of the returned array with a permuted measure map and check that a seed reproduces the counts. The cost-model tests check that OLS recovers a known law without noise and that the physics baseline is exact on its own law.

`[F]` Checks recorded per row in every counts CSV: `check_kind` and `check_dev`, `dist_maxdiff` and `qasm_dist_maxdiff`, `check_ok` and `status`, `pyzx_angle_err`, and the timings `t_zx`, `t_tket` and `t_total`.

`[F]` Timeouts. `pipelines/run_bench.py` and `pipelines/run_bench_B.py` default to 600 s per (circuit, pipeline) and `pipelines/run_b2.py` to 900 s. The family B1 run used 900 s, under which hwb8 timed out under P1 and P2, so `results/family_B1_counts.csv` carries `status = timeout` on those two rows (103 of 105 rows `ok`). A rerun with `--timeout 5400` on P1 and P2 only started on 7 October at 21:37 and completed both. P1 finished in 885.6 s wall with 8305 ZZPhase gates and P2 in 843.8 s wall with 5587 ZZPhase gates. Both rows have `status = ok` with `check_dev` at most 1.7e-13 and a T-count after the ZX stage of 3517 (`results/family_B1_hwb8_long_run.log`, `results/family_B1_hwb8_long_counts.csv`). `[F]` At the time of writing these two rows are in the long-run CSV only and have not been merged into `results/family_B1_counts.csv`, so every table built from the main CSV still shows hwb8 under five pipelines. `[O]` Both wall times lie under the earlier 900 s limit, so the earlier timeouts came from two workers sharing the two cores with the other 13 circuits, not from the circuit itself.

`[F]` Verification. Two reports by agents that did not produce the results are in the repository. `results/verification_2026-10-07.md` recomputed the seven claims of `claude/status-2026-10-06.md` from the raw CSVs and QASM files. Six were confirmed. One mismatched: the status document said P2 beats P0 on 13 of 14 completed B1 circuits and the recomputation gives 12 of 14 with two ties. One figure was unverifiable, a 1064-gate SK word length that depends on an unstated approximation depth. `results/verification_2026-10-07b.md` recomputed six further claims (family A files and manifest, `family_A_counts.csv`, the H2-2E proxy CSVs and their no-intercept fits, four proxy rows rerun, `certificates.csv` against a direct recomputation, ten report table cells): all confirmed, none mismatched. That report also diagnosed the crash of the first hwb8 rerun, in which `--files hwb8` matched against `hwb8.qasm` selected zero jobs, and fixed `pipelines/run_bench_B.py` before the 5400 s run above was started.

## 6. Limitations

`[F]` ZX extraction worsens the ZZPhase count. On family A, P1, P3 and P4 are above P0 on 180 of 180 circuits, with ZZ ratios from 1.28 to 10.32 (P1), 1.31 to 7.91 (P3) and 1.44 to 10.36 (P4). On family B1, in `results/family_B1_counts.csv`, P1 is above P0 on 13 of the 14 circuits it completed, P3 on 14 of 15 and P4 on 15 of 15. With the hwb8 long-run row added, P1 is above P0 on 14 of 15. Only teleport reduction, which does not extract, helps on H2.

`[F]` The Trotter family sits at its ZZPhase floor. Under P0 alone the ZZPhase count equals one gate per two-body term on 180 of 180 circuits, where `n_2q` equals `n_cx / 2` of the manifest. No pipeline has fewer ZZPhase gates than P0 on any family A circuit, 0 of 180 for each of P0ref, P0L1, P1, P2, P3 and P4. The family measures the cost of a rewrite instead of its benefit. `[O]` The Trotter family is the right control, because a Trotter circuit is what an H2 user runs most, and a method that damages it has to be caught.

`[F]` A single-qubit T gate is an Rz on H2, which is free in HQC and absent from the gate-noise model. The T-count layer of the ledger has no effect on any H2 number in this report. Its value is for a fault-tolerant target.

`[F]` The noise proxy is a density-matrix simulation with the published H2-2E default parameters (p1 = 7.3e-5, p2 = 1.29e-3, p_meas = (9e-4, 1.8e-3), p_init = 4e-5) and depolarising gate channels only. The published H2-2E model has in addition a spontaneous-emission branch that applies leakage half of the time, measurement and initialisation crosstalk, quadratic and linear dephasing during transport and idling, and a two-qubit fault probability that scales with the RZZ angle (`docs/platform_notes.md`, section 3.2). The proxy has none of these. The Selene cross-check in `results/selene.md` compares two depolarising models that share the same per-gate convention, so the agreement of 32 of 34 runs within two standard deviations for the like-for-like variant confirms the implementation of the proxy and its measure-map handling, not its fidelity to H2-2E. `[O]` On the family B1 circuits, whose ZZPhase angles are multiples of pi/2, the angle scaling changes little. On family A, whose angles are small, the published scaling lowers the two-qubit fault probability below p2, so the proxy is pessimistic there.

`[F]` Nothing in this report has run on the H2-2E emulator or on hardware. The 468 noiseless and 68 depolarising Selene runs are local, use the Quest statevector backend, and do not contain the H2-2E noise model. The emulator cell of the notebook has not been executed. `[PENDING: emulator]`

`[F]` The cost model is fitted on proxy fidelities, not on emulator output. Held-out whole circuit classes within the pooled data give R^2 = 0.990 on family A rows and 0.830 on family B1 rows (gradient boosting, `cv5g`), which measures interpolation within the families. Across families the evidence is one direction: trained on family A the best model predicts the 7 family B1 circuits with R^2 = 0.805 against 0.785 for the unfitted physics baseline, and trained on the 35 family B1 rows no model predicts family A (best R^2 = 0.326). `[O]` Seven B1 circuits do not establish generalisation, and learned rewriting itself is not attempted in this submission.

`[F]` The certificate bounds the T-count of exact rewrites and is computed on the channel of size 4^n x 4^n. It is applied to family B2 at n = 2 and n = 3 and to four family B1 circuits at n = 5. On family B2 the floor is at least 99.28 % of the post-ZX T-count on every instance. On the four B1 circuits the floor is 25.0 % (barenco_tof_3), 25.0 % (mod5_4), 55.2 % (qft_4) and 26.7 % (tof_3) of the post-ZX T-count, so there the certificate leaves most of the remaining T-count unaccounted for. `[O]` The B1 floors are loose because those circuits are hand-written with many Clifford collapses, not synthesised words, and the manuscript's near-rigidity result covers synthesised words only. An approximate resynthesis to a new precision is outside the scope of the certificate.

`[F]` hwb8 under P1 and P2 is complete only in `results/family_B1_hwb8_long_counts.csv` (P1 8305, P2 5587 ZZPhase gates). The main CSV and every table built from it still show hwb8 under five pipelines. `[F]` With the long-run row, P2 is below P0 on hwb8 by 5.50 % (5912 to 5587) and P2 is below P0 on 13 of 15 family B1 circuits with two ties.

`[F]` The implementation of the per-step bookkeeping of Lemma mqval(b) of the barrier manuscript found that the "reduction fires exactly once" half of that lemma fails on the word T T (`barrier/NOTES.md`, section 8), and the floor of Corollary cert does not use that half.

`[F]` Table B2 has five circuits per row against 50 and 8 in the manuscript. The agreement of the means is a consistency check, not a statistical result.

## 7. Team and roles

| Name | Role |
|---|---|
| C.-F. Kam | `[TBD]` |
| A. Mahasinghe | `[TBD]` |
| D. De Silva | `[TBD]` |
| Karunarathne | `[TBD]` |
| F. Cadet | `[TBD]` |
| Bessafi | `[TBD]` |
| K. De Silva | `[TBD]` |

## References

1. C.-F. Kam et al., An Exactness Barrier for ZX-Calculus Optimization of Synthesized Clifford+T Circuits, arXiv:2608.22801. Source in `papers/barrier/main.tex`. `[O: the arXiv number is not in the repository, audit item A10]`
2. D. De Silva et al., Numerical Evaluation of ZX-Calculus Optimization for Solovay-Kitaev Quantum Circuit Synthesis, arXiv:2608.22810. Source in `papers/skzx/DeSilva-SK-ZX-QIP.tex`. `[O: the arXiv number is not in the repository, audit item A10]`
3. A. Kissinger and J. van de Wetering, Reducing the number of non-Clifford gates in quantum circuits, Phys. Rev. A 102, 022406 (2020). `[O: check table before submission]`
4. Quantinuum, H2 Product Data Sheet, version 4.00, 17 September 2025, https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf.
5. Quantinuum, H2 emulators (H2-2E default noise parameters), https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/h2_emulators.html, and the emulator noise model page, https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/noise_model.html.
6. Quantinuum, Helios costing (HQC formula, equation 1), https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html. `[O: the H2 form of the formula is inferred from this page, docs/platform_notes.md section 3.4]`
7. Quantinuum, Singapore Grand Challenge code samples, https://github.com/Quantinuum/sg_grand_challenge.
8. Quantinuum, Selene emulation framework, https://docs.quantinuum.com/selene/ and https://github.com/quantinuum/selene.
9. pytket-quantinuum 0.59.3, `QuantinuumBackend.default_compilation_pass`, reproduced in `pipelines/compile.py:quantinuum_default_pass` with line references.
10. PyZX 0.10.7 and the Quantinuum pyzx fork, commit e695d6d7, for the family B1 sources.

<!-- CHANGELOG part4 -->
- Section 5: every version re-confirmed with `pip show` on 7 Oct (all match the brief). hugr 0.18.8 and scikit-learn 1.9.1 added because `selene/run_selene.py` and `model/cost_model.py` import them.
- Section 5: scripts table extended with the hwb8 long run, the two `run_proxy.py --noise h22e` family runs and the figure call, `barrier/run_certificates.py`, `selene/run_selene.py`, `selene/make_summary.py` and `model/cost_model.py`, each with inputs and outputs read from the script docstrings and `add_argument` calls.
- Section 5: test table with counts from one run of each file (12, 17, 69, 6, 6, 7). `selene/test_selene.py` is a pytest file, not a script.
- Section 5: hwb8 paragraph rewritten from `results/family_B1_hwb8_long_run.log` (completed, 886 s and 844 s under the 5400 s limit, not merged into the main CSV).
- Section 5: verification paragraph added for `results/verification_2026-10-07.md` and `_2026-10-07b.md`.
- Section 6, paragraph 1: audit item A8 fixed, "13 or 14 of the 15" replaced by the recomputed per-pipeline counts with the correct denominators (P1 13 of 14, P3 14 of 15, P4 15 of 15) and the hwb8 long-run count (P1 14 of 15).
- Section 6, proxy paragraph: audit item A5 fixed, "data-sheet parameters" and "being rerun" replaced by the H2-2E parameters now in `results/family_A_proxy_h22e.csv`. The omitted noise mechanisms are listed from `docs/platform_notes.md` section 3.2.
- Section 6: new paragraphs for the Selene local runs, the cost model, the loose B1 floors (25.0, 25.0, 55.2, 26.7 %), and the Lemma mqval(b) sentence moved here from Section 2.5 of v1.
- Section 6: the certificate application range corrected from "n <= 5" to "n = 2 and 3 (B2), n = 5 (B1)".
- References: items 3 to 8 added as instructed. arXiv numbers kept as given and flagged per audit item A10.
- Open: the hwb8 rows need merging into `results/family_B1_counts.csv` and `python report/make_tables.py` rerun before Table B1 and the Section 6 counts that depend on it are final.
