# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "aqora==0.35.1",
#     "pytket==2.18.4",
#     "pytket-quantinuum==0.59.3",
#     "pyzx==0.10.7",
#     "pandas",
#     "matplotlib",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full", auto_download=["html", "markdown", "ipynb"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A pass selector keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2

    Team **Learned ZX Rewriting**, Quantinuum Singapore Grand Challenge, submission 1.

    This notebook is the executable companion of `report/report_v5.md`. It

    1. loads the result tables from `results/*.csv` and shows them with the figures,
    2. compiles one chosen circuit live with the four-candidate pass selector
       PSEL4 (`pipelines/pass_select.py`, candidates P0, L3, P2 and P2L3, lowest
       HQC estimate kept) and compares each candidate with
       `value/psel4_ledger.csv`,
    3. compiles `tof_3` (family B1) with PSEL4 and submits the pick to the
       free H2-2SC syntax checker through `aqora.QPU`, behind a gate that is
       closed by default.

    Every number shown here is read from the CSV files or computed in the cell
    that shows it. Nothing is typed in.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### What this notebook shows and what is open

    `[F]` The scoring map of `report/report_v5.md` assigns the technical-performance
    evidence to the count tables A1 to B2, the count-only table B1x, the proxy
    tables A4 and A5, the Selene tables S1 and S2, the emulator tables E1 to E3,
    the H2 hardware plan of Section 6 and this notebook.

    **Shown here, read from `results/*.csv`**

    | Artifact | Source file | Status |
    |---|---|---|
    | Table A1, A2 (family A counts) | `family_A_counts.csv` | checked rows |
    | Table B1 (family B1 counts, hwb8 merged) | `family_B1_counts.csv` | checked rows |
    | Table B1x (family B1x counts) | `family_B1x_counts.csv` | count-only, `ok-unchecked`, no exactness check |
    | Table B2 (family B2 means) | `family_B2_counts.csv` | checked rows |
    | Table B2-check (family B2 compiled QASM re-read) | `family_B2_compiled_check.csv` | 100 rows |
    | Table A4 (local noise proxy, family A) | `family_A_proxy_h22e.csv` | proxy, not emulator |
    | Table E1 (Nexus H2-Emulator runs) | `emulator_nexus_H2-Emulator.csv` | emulator, 1000 shots |
    | Table E2 (Nexus H2-2E runs) | `emulator_nexus_H2-2E.csv` | emulator, 1000 shots |
    | Jobs ledger | `emulator_jobs.csv` | every platform submission |
    | Table C (exactness-barrier certificates) | `certificates.csv` | computed |
    | Table S (Selene noiseless runs) | `selene_noiseless.csv` | local emulator |
    | Table M (cost model) | `cost_model_metrics.csv` | fitted on proxy rows |
    | Figures | `report/figures/*.png`, `results/fig_*.png` | from the CSVs above |

    Table A5 (proxy on family B1) and Table S1 (Selene summary with the
    depolarising runs) are in the report only.

    **Platform jobs**

    - `[F]` The jobs of Tables E1 and E2 were submitted by
      `submit/syntax_check.py` and `submit/run_emulator.py`.
    - `[F]` The submission cell of Section 3 submits only to the free H2-2SC
      syntax checker and refuses any platform whose name does not end in `SC`.
      `report/notebook_executed.html` is an export of this notebook with that
      gate open. It was executed on 10 October 2026 with PSEL4 in Sections 2
      and 3.
    - `[F]` Tables E1 and E2 below are read from the emulator CSVs. Nothing is
      submitted to show them.

    **Open**

    - `[F]` The cost model (Table M) was not refit on the emulator rows of
      Tables E1 and E2.
    - `[F]` The H2-2SC syntax check of tof_3 under P0 submitted by
      `submit/syntax_check.py` returned no cost (`duration` null). Section 3
      shows the cost fields returned for the notebook's own job. No official
      HQC from the syntax checker exists for the other compiled circuits.
    """)
    return


@app.cell
def _():
    import os
    import sys

    import marimo as mo
    import pandas as pd

    # Repository root. In the repository this file lives in <root>/report/ and
    # results/ is one level up. In the Aqora workspace the notebook sits next
    # to a results/ folder. Try the notebook's own directory first, then its
    # parent, then the working directory and its parent, and take the first
    # one that contains results/.
    def _find_root():
        _cands = []
        if "__file__" in globals():
            _here = os.path.dirname(os.path.abspath(__file__))
            _cands += [_here, os.path.dirname(_here)]
        _cwd = os.getcwd()
        _cands += [_cwd, os.path.dirname(_cwd)]
        for _c in _cands:
            if os.path.isdir(os.path.join(_c, "results")):
                return _c
        return _cands[0]

    ROOT = _find_root()
    sys.path.insert(0, os.path.join(ROOT, "pipelines"))
    sys.path.insert(0, os.path.join(ROOT, "report"))
    RESULTS = os.path.join(ROOT, "results")
    FIGURES = os.path.join(ROOT, "report", "figures")

    # Jobs are attributed to the team organization (aqora `as_entity`), read
    # from AQORA_TEAM_ORG as in submit/common.py. The only platform this
    # notebook submits to is the free syntax checker.
    TEAM_ORG = os.environ.get("AQORA_TEAM_ORG", "").strip() or None
    PLATFORM = "nexus:H2-2SC"
    return FIGURES, PLATFORM, RESULTS, ROOT, TEAM_ORG, mo, os, pd, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Result tables

    Columns follow `pipelines/compile.py:metrics`. `n_2q` is the ZZPhase plus
    ZZMax count of the compiled native circuit, `hqc` is the HQC estimate at
    1000 shots.
    """)
    return


@app.cell
def _(RESULTS, os, pd):
    family_A = pd.read_csv(os.path.join(RESULTS, "family_A_counts.csv"))
    family_B1 = pd.read_csv(os.path.join(RESULTS, "family_B1_counts.csv"))
    family_B2 = pd.read_csv(os.path.join(RESULTS, "family_B2_counts.csv"))
    proxy_path = os.path.join(RESULTS, "family_A_proxy_h22e.csv")
    family_A_proxy = pd.read_csv(proxy_path) if os.path.exists(proxy_path) else None

    def _load(name):
        _p = os.path.join(RESULTS, name)
        return pd.read_csv(_p) if os.path.exists(_p) else None

    certificates = _load("certificates.csv")
    selene_noiseless = _load("selene_noiseless.csv")
    cost_model_metrics = _load("cost_model_metrics.csv")
    family_B1x = _load("family_B1x_counts.csv")
    family_B2_check = _load("family_B2_compiled_check.csv")
    emulator_E1 = _load("emulator_nexus_H2-Emulator.csv")
    emulator_E2 = _load("emulator_nexus_H2-2E.csv")
    emulator_jobs = _load("emulator_jobs.csv")
    return (certificates, cost_model_metrics, emulator_E1, emulator_E2,
            emulator_jobs, family_A, family_A_proxy, family_B1, family_B1x,
            family_B2, family_B2_check, selene_noiseless)


@app.cell
def _(family_A, mo):
    # Table A1: mean ZZPhase count by n and pipeline (36 circuits per n).
    _piv = family_A.pivot_table(index="n", columns="pipeline", values="n_2q", aggfunc="mean")
    _piv = _piv[["P0ref", "P0", "P0L1", "P1", "P2", "P3", "P4"]].round(1)
    mo.vstack([mo.md("**Table A1.** Family A, mean ZZPhase count by n and pipeline."),
               mo.ui.table(_piv.reset_index(), selection=None)])
    return


@app.cell
def _(family_A, mo, pd):
    # Table A2: each pipeline against P0 on the same circuit.
    _p = family_A.pivot_table(index="file", columns="pipeline", values="n_2q")
    _rows = []
    for _pl in ["P0ref", "P0L1", "P1", "P2", "P3", "P4"]:
        _r = _p[_pl] / _p["P0"]
        _rows.append({"pipeline": _pl,
                      "better than P0": int((_p[_pl] < _p["P0"]).sum()),
                      "equal to P0": int((_p[_pl] == _p["P0"]).sum()),
                      "worse than P0": int((_p[_pl] > _p["P0"]).sum()),
                      "mean ZZ ratio": round(float(_r.mean()), 2),
                      "max ZZ ratio": round(float(_r.max()), 2)})
    mo.vstack([mo.md("**Table A2.** Family A, pipelines against P0, 180 circuits."),
               mo.ui.table(pd.DataFrame(_rows), selection=None)])
    return


@app.cell
def _(family_B1, mo):
    _p = family_B1.pivot_table(index="file", columns="pipeline", values="n_2q")
    _t = family_B1.pivot_table(index="file", columns="pipeline", values="t_count_zx")
    _meta = family_B1[family_B1.pipeline == "P0ref"].set_index("file")[["n", "t_count_written"]]
    _tab = _meta.join(_p[["P0ref", "P0", "P1", "P2", "P3", "P4"]].add_prefix("ZZ "))
    _tab["P2 vs P0 %"] = (100 * (1 - _p["P2"] / _p["P0"])).round(1)
    _tab["T after ZX"] = _t["P1"].fillna(_t["P4"])
    _tab = _tab.sort_values(["n", "t_count_written"]).reset_index()
    mo.vstack([mo.md("**Table B1.** Family B1, ZZPhase count per circuit and pipeline. "
                     "hwb8 under P1 and P2 comes from the 5400 s run in "
                     "`results/family_B1_hwb8_long_counts.csv`, merged into the CSV."),
               mo.ui.table(_tab, selection=None)])
    return


@app.cell
def _(family_B1x, mo):
    # Table B1x: count-only family, no exactness check (results/family_B1x_counts.csv).
    if family_B1x is None:
        _out = mo.callout(mo.md("`results/family_B1x_counts.csv` not found. Run "
                                "`python pipelines/run_bench_B.py --manifest bench/family_B1x/manifest.csv "
                                "--prefix family_B1x --pipelines P0ref,P0,P2 --no-check`."), kind="warn")
    else:
        _status = family_B1x["status"].value_counts().to_dict()
        _status_str = ", ".join(f"`{k}` on {v} of {len(family_B1x)} rows" for k, v in _status.items())
        _kinds = ", ".join(f"`{k}`" for k in family_B1x["check_kind"].astype(str).unique())
        _p = family_B1x.pivot_table(index="file", columns="pipeline", values="n_2q")
        _t = family_B1x.pivot_table(index="file", columns="pipeline", values="t_count_zx")
        _meta = family_B1x[family_B1x.pipeline == "P0ref"].set_index("file")[["n", "t_count_written"]]
        _tab = _meta.join(_p[["P0ref", "P0", "P2"]].add_prefix("ZZ "))
        _tab["P2 vs P0 %"] = (100 * (1 - _p["P2"] / _p["P0"])).round(1)
        _tab = _tab.rename(columns={"t_count_written": "T written"})
        _tab["T after ZX P2"] = _t["P2"]
        _tab = _tab.sort_values(["n", "T written"]).reset_index()
        _below = int((_p["P2"] < _p["P0"]).sum())
        _equal = int((_p["P2"] == _p["P0"]).sum())
        _above = int((_p["P2"] > _p["P0"]).sum())
        _out = mo.vstack([
            mo.md(f"`[F]` The rows of `results/family_B1x_counts.csv` are count-only. "
                  f"Status column: {_status_str}. `check_kind` column: {_kinds}. "
                  f"No unitary, statevector or distribution exactness check was run on them "
                  f"(compiled with `--no-check`), only the gate-set check. "
                  f"They are kept apart from the checked family B1 above."),
            mo.md(f"**Table B1x.** Family B1x, {len(_tab)} circuits, ZZPhase count per circuit under "
                  f"P0ref, P0 and P2, T-count as written and T-count after the ZX stage of P2. "
                  f"P2 below P0 on {_below}, equal on {_equal}, above on {_above}."),
            mo.ui.table(_tab, selection=None)])
    _out
    return


@app.cell
def _(family_B2, mo):
    _g = family_B2.groupby(["n", "eps", "pipeline"])
    _tab = _g[["t_count_written", "t_count_after_zx", "n_2q", "depth_2q", "hqc"]].mean().round(1)
    _tab["T red. %"] = (100 * (1 - _tab["t_count_after_zx"] / _tab["t_count_written"])).round(1)
    mo.vstack([mo.md("**Table B2.** Family B2, means over 5 circuits per (n, eps, pipeline)."),
               mo.ui.table(_tab.reset_index(), selection=None)])
    return


@app.cell
def _(family_B2_check, mo, pd):
    # Table B2-check: saved compiled QASM of family B2 re-read and re-simulated
    # (results/family_B2_compiled_check.csv).
    if family_B2_check is None:
        _out = mo.callout(mo.md("`results/family_B2_compiled_check.csv` not found."), kind="warn")
    else:
        _n = len(family_B2_check)
        _flags = ["metrics_match", "reread_native", "dist_ok"]
        _rows = [{"check": _f,
                  "True": int((family_B2_check[_f] == True).sum()),
                  "False": int((family_B2_check[_f] == False).sum()),
                  "rows": _n} for _f in _flags]
        _summary = pd.DataFrame(_rows)
        _bad = family_B2_check[~family_B2_check[_flags].all(axis=1)]
        _bad_tab = _bad[["file", "pipeline", "n", "eps", "instance", "status", "dist_maxdiff"] + _flags].reset_index(drop=True)
        _status = ", ".join(f"`{k}` {v}" for k, v in family_B2_check["status"].value_counts().items())
        _out = mo.vstack([
            mo.md(f"**Table B2-check.** Family B2 compiled circuits re-read from "
                  f"the `path` column (`results/compiled/`, one folder per pipeline), {_n} rows. `metrics_match` compares the "
                  f"re-read gate counts with the counts CSV, `reread_native` checks the gate set, "
                  f"`dist_ok` compares the output distribution of the re-read measured QASM on |0...0> with "
                  f"that of the uncompiled bench circuit at tolerance 1e-8 (`compile.CHECK_TOL`). Status column: {_status}."),
            mo.ui.table(_summary, selection=None),
            mo.md(f"Rows with any flag False: {len(_bad)}. The `dist_maxdiff` of each is shown; "
                  f"the largest `dist_maxdiff` over all {_n} rows is "
                  f"{family_B2_check['dist_maxdiff'].max():.3e}."),
            mo.ui.table(_bad_tab, selection=None) if len(_bad) else mo.md("None.")])
    _out
    return


@app.cell
def _(family_A_proxy, mo):
    if family_A_proxy is None:
        _out = mo.callout(mo.md("`results/family_A_proxy_h22e.csv` not found."), kind="warn")
    else:
        _tab = family_A_proxy.pivot_table(index="n", columns="pipeline", values="F_H", aggfunc="mean").round(4)
        _out = mo.vstack([
            mo.md("**Table A4.** Local density-matrix noise proxy with the published H2-2E "
                  "default parameters (`results/family_A_proxy_h22e.csv`), mean Hellinger "
                  "fidelity by n and pipeline. Tables E1 and E2 below cover a subset of "
                  "circuits and this proxy stays the primary noise data for family A."),
            mo.ui.table(_tab.reset_index(), selection=None)])
    _out
    return


@app.cell
def _(emulator_E1, emulator_E2, emulator_jobs, mo):
    # Tables E1 and E2: emulator rows read from the CSVs. Nothing is submitted here.
    _cols = ["file", "pipeline", "n_qubits", "n_2q", "n_1q", "support_size",
             "F_H", "TVD", "shots", "job_id"]
    _items = []
    for _name, _df, _src in [("E1", emulator_E1, "emulator_nexus_H2-Emulator.csv"),
                             ("E2", emulator_E2, "emulator_nexus_H2-2E.csv")]:
        if _df is None:
            _items.append(mo.callout(mo.md(f"`results/{_src}` not found."), kind="warn"))
            continue
        _tab = _df[[c for c in _cols if c in _df.columns]].copy()
        _tab[["F_H", "TVD"]] = _tab[["F_H", "TVD"]].round(4)
        _items.append(mo.md(f"**Table {_name}.** `results/{_src}`, {len(_df)} rows from "
                            f"{_df['job_id'].nunique()} jobs, F_H and TVD of the counts "
                            f"against the ideal distribution."))
        _items.append(mo.ui.table(_tab, selection=None))
    if emulator_jobs is not None:
        _j = emulator_jobs.copy()
        _j["status"] = _j["status"].astype(str).str.split(":").str[0]
        _led = _j.groupby(["platform", "status"]).size().rename("submissions").reset_index()
        _items.append(mo.md(f"**Jobs ledger.** `results/emulator_jobs.csv`, {len(_j)} rows, "
                            f"by platform and status."))
        _items.append(mo.ui.table(_led, selection=None))
    mo.vstack(_items)
    return


@app.cell
def _(certificates, mo):
    # Table C: exactness-barrier certificates (results/certificates.csv).
    if certificates is None:
        _out = mo.callout(mo.md("`results/certificates.csv` not found. Run `python barrier/run_certificates.py`."), kind="warn")
    else:
        _cols = ["family", "file", "n", "t_written", "lde_floor", "t_zx_P2",
                 "floor_over_t_zx_P2", "collapse_count", "invariant_ok", "wall_s"]
        _tab = certificates[_cols].copy()
        _tab["floor_over_t_zx_P2"] = (100 * _tab["floor_over_t_zx_P2"]).round(2)
        _tab = _tab.rename(columns={"floor_over_t_zx_P2": "floor / T_zx (P2) %"})
        _n_viol = int((~certificates["invariant_ok"].astype(bool)).sum())
        _out = mo.vstack([
            mo.md(f"**Table C.** Certified T-count floor (lde of the exact Pauli channel) against the "
                  f"T-count after the ZX stage of P2, {len(certificates)} rows. "
                  f"Invariant floor <= T_zx violated on {_n_viol} rows."),
            mo.ui.table(_tab, selection=None)])
    _out
    return


@app.cell
def _(mo, selene_noiseless):
    # Table S: local Selene (selene-sim) noiseless runs, summary per pipeline.
    if selene_noiseless is None:
        _out = mo.callout(mo.md("`results/selene_noiseless.csv` not found. Run `selene/run_selene.py`."), kind="warn")
    else:
        _g = selene_noiseless.groupby("pipeline")
        _tab = _g.agg(runs=("file", "size"),
                      max_TVD=("TVD", "max"),
                      max_TVD_over_scale=("TVD_over_scale", "max"),
                      median_TVD_over_expected=("TVD_over_expected", "median"),
                      flagged=("flag", "sum"),
                      shots_outside_support=("shots_outside_support", "sum"),
                      t_total_s=("t_total", "sum")).round(3).reset_index()
        _out = mo.vstack([
            mo.md(f"**Table S.** Selene noiseless runs of the compiled circuits, "
                  f"{len(selene_noiseless)} runs of {int(selene_noiseless['shots'].iloc[0])} shots, "
                  f"sampled distribution against the exact one (`results/selene_noiseless.csv`). "
                  f"`flagged` counts runs with TVD above 4 times the sampling scale."),
            mo.ui.table(_tab, selection=None)])
    _out
    return


@app.cell
def _(cost_model_metrics, mo):
    # Table M: cost-model generalisation metrics (results/cost_model_metrics.csv).
    if cost_model_metrics is None:
        _out = mo.callout(mo.md("`results/cost_model_metrics.csv` not found. Run `python model/cost_model.py`."), kind="warn")
    else:
        _tab = cost_model_metrics[cost_model_metrics["split"].isin(["lofo", "cv5g"])].copy()
        _tab[["rmse_y", "r2_y", "mae_F"]] = _tab[["rmse_y", "r2_y", "mae_F"]].round(4)
        _out = mo.vstack([
            mo.md("**Table M.** Learned cost model, y = -ln F_H from compile-time features, "
                  "fitted on the proxy CSVs. `lofo` trains on one family and tests on the other, "
                  "`cv5g` holds out whole circuit classes. The model was not refit on the "
                  "emulator rows of Tables E1 and E2."),
            mo.ui.table(_tab, selection=None)])
    _out
    return


@app.cell
def _(FIGURES, RESULTS, mo, os):
    _figs = [os.path.join(FIGURES, "fig_A_zz_ratio.png"),
             os.path.join(FIGURES, "fig_B1_zz.png"),
             os.path.join(FIGURES, "fig_B2_t.png"),
             os.path.join(RESULTS, "fig_proxy_h22e.png"),
             os.path.join(RESULTS, "fig_cost_model.png")]
    _items = []
    for _path in _figs:
        if os.path.exists(_path):
            _items.append(mo.image(src=_path, width=640))
        else:
            _items.append(mo.md(f"`{os.path.relpath(_path, os.path.dirname(RESULTS))}` not found. "
                                "Run `python report/make_tables.py`, `python noise/run_proxy.py --figure-h22e` "
                                "or `python model/cost_model.py`."))
    mo.vstack(_items)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Live compilation of one circuit

    Pick a circuit from family A or B1. The cell below compiles it with PSEL4,
    `pass_select.compile_select(..., candidates=pass_select.PSEL4_CANDIDATES)`.
    The four candidates are P0 (pytket-quantinuum level 2, reproduced in
    `pipelines/compile.py`), L3 (pytket-quantinuum level 3), P2 (PyZX
    `teleport_reduce`, then P0) and P2L3 (PyZX `teleport_reduce`, then L3).
    Each candidate is checked against the input circuit by `compile.check`. A
    candidate that fails the check or leaves the native gate set is dropped.
    PSEL4 keeps the surviving candidate with the lowest HQC estimate at 1000
    shots, then the lowest ZZ count, then the order P0, L3, P2, P2L3. The rows
    are listed in that tie order. The ledger columns are read from
    `value/psel4_ledger.csv` for the same file.
    """)
    return


@app.cell
def _(ROOT, mo, os):
    _choices = []
    for _fam in ["family_A", "family_B1"]:
        _d = os.path.join(ROOT, "bench", _fam)
        if os.path.isdir(_d):
            _choices += [f"{_fam}/{f}" for f in sorted(os.listdir(_d))
                         if f.endswith(".qasm") and not f.endswith("_meas.qasm")]
    _default = "family_B1/vbe_adder_3.qasm" if "family_B1/vbe_adder_3.qasm" in _choices else (_choices[0] if _choices else None)
    circuit_choice = mo.ui.dropdown(options=_choices, value=_default, label="Circuit")
    circuit_choice
    return (circuit_choice,)


@app.function
def psel4_demo(root, family_dir, file, shots=1000):
    """Compile bench/<family_dir>/<file> with PSEL4
    (pass_select.compile_select with candidates PSEL4_CANDIDATES) and compare
    each candidate with the row of value/psel4_ledger.csv for the same family
    and file. Returns (compiled circuit of the pick or None, record, table,
    ledger row as a dict or None). The table has one row per candidate in the
    tie order P0, L3, P2, P2L3."""
    import os
    import sys

    import pandas as pd

    _pip = os.path.join(root, "pipelines")
    if _pip not in sys.path:
        sys.path.insert(0, _pip)
    import pass_select  # pipelines/pass_select.py
    from pytket.qasm import circuit_from_qasm

    circ = circuit_from_qasm(os.path.join(root, "bench", family_dir, file))
    comp, record = pass_select.compile_select(
        circ, shots=shots, candidates=pass_select.PSEL4_CANDIDATES)

    ledger_row = None
    _lp = os.path.join(root, "value", "psel4_ledger.csv")
    if os.path.exists(_lp):
        _led = pd.read_csv(_lp)
        _m = _led[(_led["family"] == family_dir.replace("family_", "")) & (_led["file"] == file)]
        if len(_m) == 1:
            ledger_row = _m.iloc[0].to_dict()

    rows = []
    for name in sorted(pass_select.PSEL4_CANDIDATES, key=pass_select.TIE_ORDER.get):
        r = record["candidates"][name]
        row = {"candidate": name,
               "hqc": round(r["hqc"], 1),
               "n_2q": r["n_2q"],
               "check_status": r["status"],
               "check_dev": r["check_dev"],
               "PSEL4_pick": name == record["chosen"]}
        if ledger_row is not None:
            row["ledger_hqc"] = float(ledger_row[f"hqc_{name}"])
            row["hqc_matches_ledger"] = abs(row["hqc"] - row["ledger_hqc"]) < 0.05
            row["ledger_pick"] = name == ledger_row["pick_PSEL4"]
        if r["error"]:
            row["error"] = r["error"]
        rows.append(row)
    return comp, record, pd.DataFrame(rows), ledger_row


@app.cell
def _(ROOT, circuit_choice, mo):
    import compile as C  # pipelines/compile.py

    mo.stop(circuit_choice.value is None, mo.md("No benchmark circuits found under `bench/`."))
    _fam, _file = circuit_choice.value.split("/")
    _comp, live_record, live_table, _led = psel4_demo(ROOT, _fam, _file, shots=1000)
    _chosen = live_record["chosen"]
    _head = (f"Live PSEL4 compilation of `{circuit_choice.value}` at 1000 shots: "
             f"pick **{_chosen}**")
    if _chosen is not None:
        _head += f", HQC {live_record['candidates'][_chosen]['hqc']:.1f}"
    if _led is None:
        _head += ". No row for this file in `value/psel4_ledger.csv`."
    else:
        _agree = (_led["pick_PSEL4"] == _chosen) and bool(live_table["hqc_matches_ledger"].all())
        _head += (f". `value/psel4_ledger.csv`: pick **{_led['pick_PSEL4']}**, "
                  f"HQC {float(_led['hqc_PSEL4']):.1f}. Live run and ledger agree on every "
                  f"candidate HQC and on the pick: **{_agree}**.")
    mo.vstack([mo.md(_head), mo.ui.table(live_table, selection=None)])
    return C, live_record, live_table


@app.function
def require_free_checker(platform):
    """Return `platform` if its name ends in "SC" (a Quantinuum syntax
    checker, which costs no HQC, docs/platform_notes.md 3.4). Any other
    platform, such as nexus:H2-2E, nexus:H2-Emulator or hardware, raises
    AssertionError before any client or job is created."""
    if not (isinstance(platform, str) and platform.endswith("SC")):
        raise AssertionError(
            f"refusing platform {platform!r}: this notebook submits only to a "
            f"free syntax checker (platform name ending in 'SC')")
    assert platform.endswith("SC")
    return platform


@app.function
def submit_free_check(platform, circuit, shots, root, family, file, label,
                      timeout=300.0, poll=5.0):
    """Submit one measured native circuit to a syntax checker by the route of
    submit/syntax_check.py:submit_one (common.make_qpu with AQORA_TEAM_ORG as
    as_entity, ledger row appended before submission and updated after, raw
    job dump saved under results/emulator/<platform>/notebook_select/).
    The platform guard runs first. Returns a dict with job_id, status,
    counts, cost_fields, hqc_estimate, ledger_key, result_path, error."""
    require_free_checker(platform)
    import json
    import os
    import sys

    _sub = os.path.join(root, "submit")
    if _sub not in sys.path:
        sys.path.insert(0, _sub)
    import common  # submit/common.py

    bad = common.native_violations(circuit)
    if bad:
        raise ValueError(f"non-native ops {sorted(bad)}")
    hqc = common.hqc_estimate(circuit, shots)
    qpu = common.make_qpu(require_free_checker(platform))
    row = common.append_ledger(dict(platform=platform, family=family, file=file,
                                    pipeline=label, shots=shots, options="{}",
                                    status="SUBMITTING"))
    key = {k: row[k] for k in ("timestamp", "platform", "file", "pipeline")}
    out = dict(platform=platform, family=family, file=file, pipeline=label,
               shots=shots, hqc_estimate=hqc, job_id=None, status=None,
               counts=None, cost_fields=None, error=None, ledger_key=key,
               result_path=None, source="report/notebook_skeleton.py")
    try:
        job = qpu.run(circuit, shots=shots)
    except Exception as e:  # noqa: BLE001
        common.update_ledger(key, status="SUBMIT_ERROR:" + repr(e)[:200])
        out["status"] = "SUBMIT_ERROR"
        out["error"] = repr(e)
        return out
    out["job_id"] = job.job_id
    common.update_ledger(key, job_id=job.job_id, status="SUBMITTED")
    try:
        counts, t_wall = common.wait_counts(job, timeout=timeout, poll=poll)
        out["counts"] = counts
        out["t_wait"] = t_wall
        out["results"] = [common.result_raw(r) for r in job.results(raise_on_item_error=False)]
        status = "COMPLETED"
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)
        status = "FAILED:" + repr(e)[:200]
    raw = common.job_raw(job)
    out["job"] = raw
    out["platform_reported"] = (raw.get("payload", {}).get("platform") or {}).get("name")
    out["cost_fields"] = common.cost_fields(raw.get("payload", {}))
    out["status"] = status
    path = common.save_result(platform, "notebook_select", file, out)
    out["result_path"] = str(path.relative_to(common.ROOT))
    common.update_ledger(key, status=status,
                         hqc_or_seconds=json.dumps(out["cost_fields"], default=str) if out["cost_fields"] else "",
                         result_path=out["result_path"])
    return out


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Submission to the free H2-2SC syntax checker

    The cells below compile `bench/family_B1/tof_3.qasm` with PSEL4
    (`pipelines/pass_select.py`, candidates P0, L3, P2 and P2L3, lowest HQC
    estimate kept, ties in the order P0, L3, P2, P2L3), append measure-all
    to the pick and submit the measured circuit to `nexus:H2-2SC` as the
    team organization (`AQORA_TEAM_ORG`), by the route of
    `submit/syntax_check.py`. The syntax checker costs no HQC
    (`docs/platform_notes.md` 3.4). `require_free_checker` refuses any platform
    whose name does not end in `SC` before a client is built
    (`report/test_notebook_submit.py`).

    The gate is closed by default. It opens on the button, or when the notebook
    is run with the environment variable `SGC_NOTEBOOK_SUBMIT_SC=1`. The job is
    appended to `results/emulator_jobs.csv` (pipeline `psel4:<pick>`) and its
    raw dump is saved under `results/emulator/nexus_H2-2SC/notebook_select/`.
    """)
    return


@app.cell
def _(C, ROOT, mo):
    SC_FAMILY, SC_FILE = "B1", "tof_3.qasm"
    sc_shots = 1000
    _comp, sc_record, sc_table, _led = psel4_demo(ROOT, "family_B1", SC_FILE, shots=sc_shots)
    mo.stop(_comp is None, mo.callout(mo.md(f"PSEL4 kept no candidate for `{SC_FILE}`."), kind="danger"))
    sc_circuit = C.add_measure_all(_comp)
    _ledger = ("No row for this file in `value/psel4_ledger.csv`." if _led is None else
               f"`value/psel4_ledger.csv`: pick **{_led['pick_PSEL4']}**, HQC "
               f"{float(_led['hqc_PSEL4']):.1f}. Live run and ledger agree on every candidate "
               f"HQC and on the pick: **{(_led['pick_PSEL4'] == sc_record['chosen']) and bool(sc_table['hqc_matches_ledger'].all())}**.")
    mo.vstack([mo.md(f"PSEL4 on `bench/family_B1/{SC_FILE}` at {sc_shots} shots: "
                     f"pick **{sc_record['chosen']}**, HQC "
                     f"{sc_record['candidates'][sc_record['chosen']]['hqc']:.1f}, "
                     f"{sc_circuit.n_qubits} qubits. {_ledger}"),
               mo.ui.table(sc_table, selection=None)])
    return SC_FAMILY, SC_FILE, sc_circuit, sc_record, sc_shots, sc_table


@app.cell
def _(mo):
    submit = mo.ui.run_button(label="Submit to the H2-2SC syntax checker", kind="success")
    submit
    return (submit,)


@app.cell
def _(PLATFORM, ROOT, SC_FAMILY, SC_FILE, TEAM_ORG, mo, os, pd, sc_circuit, sc_record, sc_shots, submit):
    from pytket import OpType as _Op

    # The platform check runs before the gate, so a paid platform set in the
    # setup cell stops the notebook even with the gate closed.
    require_free_checker(PLATFORM)
    _gate = bool(submit.value) or os.environ.get("SGC_NOTEBOOK_SUBMIT_SC", "") == "1"
    mo.stop(not _gate, mo.callout(mo.md(
        "Gate closed. Press the button, or run with `SGC_NOTEBOOK_SUBMIT_SC=1`, to submit "
        f"`{SC_FILE}` to `{PLATFORM}`."), kind="info"))
    mo.stop(TEAM_ORG is None, mo.callout(mo.md("`AQORA_TEAM_ORG` is not set. Nothing was submitted."), kind="warn"))

    sc_job = submit_free_check(PLATFORM, sc_circuit, sc_shots, ROOT, SC_FAMILY, SC_FILE,
                               "psel4:" + sc_record["chosen"])

    # HQC estimate recomputed here from the gate counts of the submitted circuit.
    _n1 = sc_circuit.n_gates_of_type(_Op.PhasedX)
    _n2 = sc_circuit.n_gates_of_type(_Op.ZZPhase) + sc_circuit.n_gates_of_type(_Op.ZZMax)
    _nm = sc_circuit.n_gates_of_type(_Op.Measure)
    _spam = sc_circuit.n_qubits + _nm + sc_circuit.n_gates_of_type(_Op.Reset)
    _hqc = 5 + (_n1 + 10 * _n2 + 5 * _spam) * sc_shots / 5000
    assert abs(_hqc - sc_job["hqc_estimate"]) < 1e-9

    _items = [mo.md(
        f"Job id **`{sc_job['job_id']}`** on `{PLATFORM}` (reported platform "
        f"`{sc_job.get('platform_reported')}`) as `{TEAM_ORG}`, status **{sc_job['status']}**, "
        f"{sc_shots} shots, pipeline `{'psel4:' + sc_record['chosen']}`.\n\n"
        f"HQC estimate from the formula 5 + (N_1q + 10 N_2q + 5 N_spam) C / 5000 with "
        f"N_1q = {_n1}, N_2q = {_n2}, N_spam = {_spam} (qubits {sc_circuit.n_qubits} + measures {_nm}), "
        f"C = {sc_shots}: **{_hqc:.2f}**. This is what H2-2E would charge by the formula. "
        f"The syntax checker charges nothing.\n\n"
        f"Cost fields returned with the job: `{sc_job['cost_fields']}`.")]
    if sc_job["error"]:
        _items.append(mo.callout(mo.md(f"Error: `{sc_job['error']}`"), kind="danger"))
    if sc_job["counts"]:
        _rows = []
        for _i, _c in enumerate(sc_job["counts"]):
            _top = sorted(_c.items(), key=lambda kv: -kv[1])[:5]
            _rows.append({"program": _i, "shots_returned": sum(_c.values()),
                          "distinct_outcomes": len(_c),
                          "top_outcomes": ", ".join(f"{k}: {v}" for k, v in _top)})
        _items.append(mo.md("Counts summary. The syntax checker returns all-zero outcomes by design."))
        _items.append(mo.ui.table(pd.DataFrame(_rows), selection=None))
    _items.append(mo.md(f"Ledger row appended to `results/emulator_jobs.csv` with key "
                        f"`{sc_job['ledger_key']}`. Raw dump: `{sc_job['result_path']}`."))
    mo.vstack(_items)
    return (sc_job,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Status

    - `[F]` Hellinger fidelity and TVD of the emulator counts against the ideal
      distribution are in Tables E1 and E2 above for the 22 H2-Emulator rows
      and the six H2-2E rows.
    - `[F]` The learned cost model (Table M) is fitted on proxy rows only.
    - `[F]` hwb8 under P1 and P2 from `results/family_B1_hwb8_long_counts.csv`
      is merged into `results/family_B1_counts.csv` (Table B1).

    ### Picking a job back up

    ```python
    from aqora import QPUJob

    QPUJob.from_id("<job id>").counts()
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
