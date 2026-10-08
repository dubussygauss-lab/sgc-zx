# Reproduction record

Team Learned ZX Rewriting. Recorded 8 October 2026 in the development container. `code.zip` is `git archive` of commit `41a0b3d5f99fe006b02e0b96c7c93deac49be39b`. Run every command from the repository root.

## Environment

Versions from `pip show` on 8 October 2026: Python 3.13.16, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, qiskit 2.5.2, pygridsynth 2.0.0, selene-sim 0.3.4, guppylang 1.1.2, hugr 0.18.8, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2, aqora 0.35.1, qnexus 0.51.1, marimo 0.25.1, pytest 9.1.1. Family B1 and B1x sources: Quantinuum pyzx fork in `third_party/pyzx-fork/` at commit e695d6d.

```
pip install pytket==2.18.4 pytket-quantinuum==0.59.3 pyzx==0.10.7 qiskit==2.5.2 pygridsynth==2.0.0 \
  selene-sim==0.3.4 guppylang==1.1.2 numpy==2.5.3 pandas==2.3.3 scipy==1.18.1 scikit-learn==1.9.1 \
  matplotlib==3.11.2 aqora==0.35.1 qnexus==0.51.1 marimo==0.25.1 pytest
```

Selene runs and `selene/test_selene.py` need every proxy variable unset, because Selene streams results over a local TCP socket (report Section 5).

## Seeds

- `numpy.random.default_rng(20261006)`: family A couplings (`bench/gen_trotter.py`, `SEED`) and family B2 Haar targets (`bench/gen_haar_b2.py`, `SEED`). `seed_transpiler=0` in the B2 qiskit transpile.
- `noise/run_proxy.py`: `default_rng(0)` for the parser self-check only.
- `selene/run_selene.py`: per run `sha256("<pipeline>/<file>/<tag>")[:4]`, stored in column `seed`.
- `model/cost_model.py`: fold seed 0 and `random_state=0` for gradient boosting.

## Commands, in order (report Section 5, README)

| Output | Command |
|---|---|
| Family A circuits | `python bench/gen_trotter.py` |
| Family B1 circuits | `python bench/build_family_B1.py` |
| Family B1x circuits | `python bench/build_family_B1x.py` |
| Family B2 circuits | `python bench/gen_haar_b2.py` |
| Tables A1 to A3, Figure 1 data | `python pipelines/run_bench.py --workers 2` |
| Table B1, Figure 2 data | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --prefix family_B1 --workers 2 --timeout 900` |
| hwb8 rows of Table B1 | `python pipelines/run_bench_B.py --manifest bench/family_B1/manifest.csv --files hwb8 --pipelines P1,P2 --prefix family_B1_hwb8_long --timeout 5400 --workers 2` |
| Table B1x | `python pipelines/run_bench_B.py --manifest bench/family_B1x/manifest.csv --prefix family_B1x --pipelines P0ref,P0,P2 --no-check` |
| Table B2, Figure 3 data | `python pipelines/run_b2.py --workers 2` |
| Table A4 | `python noise/run_proxy.py --noise h22e --family A --workers 2` |
| Table A5 | `python noise/run_proxy.py --noise h22e --family B1 --workers 2` |
| Proxy fits (Section 3.5) | `python noise/run_proxy.py --figure-h22e` |
| Table C1 | `python barrier/run_certificates.py` |
| Table S1 | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene.py --mode both --procs 2 --shots 2000`, then `python selene/make_summary.py` |
| Table S2 | `HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= NO_PROXY= no_proxy= python selene/run_selene_depol_full.py --procs 2 --shots 2000`, then `python selene/summarise_depol_full.py` |
| Tables M1, M2, Figure 4 | `python model/cost_model.py` |
| Section 4.7 table | `python model/build_selene_cost_inputs.py`, `python model/cost_model.py --family-a results/cost_model_selene_input_A.csv --family-b results/cost_model_selene_input_B1.csv --out <dir>`, then `python model/report_selene_cost.py` (see gap 1) |
| All report tables and figures | `python report/make_tables.py` |
| Emulator jobs | `submit/syntax_check.py` and `submit/run_emulator.py`, need team credentials, pending in report v3 |

## Tests, run once on 8 October 2026 (logs in `build_logs/`)

| File | Command | Result | Wall |
|---|---|---|---|
| `bench/test_gen_trotter.py` | `python bench/test_gen_trotter.py` | 12/12 passed | 80 s |
| `noise/test_dm_sim.py` | `python noise/test_dm_sim.py` | 17/17 passed | 13 s |
| `barrier/test_certificate.py` | `python barrier/test_certificate.py` | 69/69 checks passed | 47 s |
| `pipelines/test_compile.py` | `python pipelines/test_compile.py` | 6/6 passed | 3 s |
| `selene/test_selene.py` | proxy variables cleared, `python -m pytest selene/test_selene.py -q` | 6 passed | 61 s |
| `model/test_cost_model.py` | `python model/test_cost_model.py` | 7/7 passed | 1 s |
| `submit/test_submit.py` | `python -m pytest submit/test_submit.py -q` | 11 passed | 5 s |

Rerun all seven: `bash submission/run_tests.sh`. Rebuild this package: `bash submission/build.sh` (add `--tests` to rerun the tests).

## Rubric evidence map (Engineering and Reproducibility)

| Evidence | File |
|---|---|
| Repository | `code.zip` |
| README | `README.md` in `code.zip` |
| Test results | this page, `build_logs/tests_summary.txt`, `build_logs/test_*.log` |
| Reproduction record | this page, report Section 5 |

## Known gaps

1. `model/cost_model.py` always writes `cost_model_metrics.csv`, `cost_model_coefficients.csv` and `fig_cost_model.*` into `--out`. No tracked script writes `results/cost_model_selene_metrics.csv` or `results/cost_model_selene_coefficients.csv`, which `model/report_selene_cost.py` reads. Running the Section 4.7 command with the default `--out` overwrites the proxy outputs of Tables M1 and M2.
2. Emulator and syntax-checker runs are not in report v3.
