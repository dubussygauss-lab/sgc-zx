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
    # A certified resource ledger shows where ZX rewriting pays on Quantinuum H2

    Team **Learned ZX Rewriting**, Quantinuum Singapore Grand Challenge, submission 1.

    This notebook is the executable companion of `report/report_v1.md`. It

    1. loads the result tables from `results/*.csv` and shows them with the figures,
    2. compiles one chosen circuit live through the baseline P0 (pytket level 2)
       and through P2 (PyZX `teleport_reduce` followed by P0),
    3. submits the compiled circuits to the H2-2E emulator through `aqora.QPU`,
       gated behind a run button.

    Every number shown here is read from the CSV files or computed in the cell
    that shows it. Nothing is typed in.
    """)
    return


@app.cell
def _():
    import os
    import sys

    import marimo as mo
    import pandas as pd

    # Repository root: this file lives in <root>/report/.
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) \
        if "__file__" in globals() else os.getcwd()
    if not os.path.isdir(os.path.join(ROOT, "results")):
        ROOT = os.getcwd()
    sys.path.insert(0, os.path.join(ROOT, "pipelines"))
    sys.path.insert(0, os.path.join(ROOT, "report"))
    RESULTS = os.path.join(ROOT, "results")
    FIGURES = os.path.join(ROOT, "report", "figures")

    TEAM_ORG = "[TEAM_ORG placeholder: aqora organization username of the team]"
    PLATFORM = "nexus:H2-2E"
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
    proxy_path = os.path.join(RESULTS, "family_A_proxy.csv")
    family_A_proxy = pd.read_csv(proxy_path) if os.path.exists(proxy_path) else None
    return family_A, family_A_proxy, family_B1, family_B2


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
                     "Empty cells are timeouts (hwb8 under P1 and P2)."),
               mo.ui.table(_tab, selection=None)])
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
def _(family_A_proxy, mo):
    if family_A_proxy is None:
        _out = mo.callout(mo.md("`[PENDING: emulator]` no proxy or emulator fidelity file found."), kind="warn")
    else:
        _tab = family_A_proxy.pivot_table(index="n", columns="pipeline", values="F_H", aggfunc="mean").round(4)
        _out = mo.vstack([
            mo.md("**Table A4.** Provisional local noise proxy, mean Hellinger fidelity. "
                  "To be replaced by H2-2E emulator results. `[PENDING: emulator]`"),
            mo.ui.table(_tab.reset_index(), selection=None)])
    _out
    return


@app.cell
def _(FIGURES, mo, os):
    _figs = ["fig_A_zz_ratio.png", "fig_B1_zz.png", "fig_B2_t.png"]
    _items = []
    for _f in _figs:
        _path = os.path.join(FIGURES, _f)
        if os.path.exists(_path):
            _items.append(mo.image(src=_path, width=640))
        else:
            _items.append(mo.md(f"`{_f}` not found. Run `python report/make_tables.py`."))
    mo.vstack(_items)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Live compilation of one circuit

    Pick a circuit from family A or B1. The cell below compiles it through P0
    (pytket-quantinuum level 2, reproduced in `pipelines/compile.py`) and through
    P2 (PyZX `teleport_reduce`, then P0), checks both against the rebased input,
    and reports the metrics.
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


@app.cell
def _(ROOT, circuit_choice, mo, os, pd):
    import compile as C  # pipelines/compile.py
    from pytket.qasm import circuit_from_qasm

    mo.stop(circuit_choice.value is None, mo.md("No benchmark circuits found under `bench/`."))
    _path = os.path.join(ROOT, "bench", circuit_choice.value)
    input_circuit = circuit_from_qasm(_path)
    ref_circuit, _ = C.compile_pipeline("P0ref", input_circuit)

    compiled = {}
    _rows = []
    for _pl in ["P0", "P2"]:
        _c, _times = C.compile_pipeline(_pl, input_circuit)
        _m = C.metrics(_c, n_measure=_c.n_qubits)
        _ck = C.check(_c, ref_circuit)
        compiled[_pl] = _c
        _rows.append({"pipeline": _pl, **{k: _m[k] for k in ["n_qubits", "n_2q", "depth_2q", "n_phasedx", "n_rz", "hqc"]},
                      "check_kind": _ck["check_kind"], "check_dev": _ck["check_dev"],
                      "check_ok": _ck["check_ok"], "t_total_s": round(_times["t_total"], 3)})
    live_table = pd.DataFrame(_rows)
    mo.vstack([mo.md(f"Live compilation of `{circuit_choice.value}`"),
               mo.ui.table(live_table, selection=None)])
    return C, compiled, input_circuit, live_table, ref_circuit


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Submission to the H2-2E emulator

    `aqora.QPU` submits programs exactly as given, so the circuits are rebased by
    the pipeline above and measured here. Jobs are attributed to the team
    organization through `as_entity`. The `noisy_simulation` option selects the
    emulator's noise model. Press the button to submit. Nothing is sent before
    that.
    """)
    return


@app.cell
def _(C, compiled):
    # Measure-all appended the way results/compiled/<pipeline>/*.qasm were written,
    # so the implicit qubit permutation left by allow_swaps=True is encoded in the
    # measurement map.
    to_submit = {pl: C.add_measure_all(c) for pl, c in compiled.items()}
    return (to_submit,)


@app.cell
def _(mo):
    shots = mo.ui.number(start=1, stop=10000, step=100, value=1000, label="Shots")
    noisy = mo.ui.checkbox(value=True, label="noisy_simulation")
    submit = mo.ui.run_button(label="Submit to QPU", kind="success")

    mo.hstack([shots, noisy, submit], justify="start")
    return noisy, shots, submit


@app.cell
def _(PLATFORM, TEAM_ORG, mo, noisy, shots, submit, to_submit):
    # Gate the job on the run button.
    mo.stop(not submit.value, mo.callout(mo.md("Press **Submit to QPU** to run the Job"), kind="info"))

    from aqora import QPU

    qpu = QPU(platform=PLATFORM, as_entity=TEAM_ORG)
    programs = [to_submit["P0"], to_submit["P2"]]
    job = qpu.run(programs, shots=int(shots.value),
                  options={"noisy_simulation": bool(noisy.value)})

    mo.md(f"Submitted job **{job.job_id}** to `{PLATFORM}` as `{TEAM_ORG}` "
          f"with shots={int(shots.value)}, noisy_simulation={bool(noisy.value)}")
    return QPU, job, programs, qpu


@app.cell
def _(job):
    # `counts()` waits on results and returns one mapping per submitted program:
    # index 0 is P0, index 1 is P2.
    counts = job.counts(timeout=600)
    counts
    return (counts,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Pending

    - `[PENDING: emulator]` Hellinger fidelity and TVD of the emulator counts
      against the ideal distribution, for every (circuit, pipeline) in the budget.
    - `[PENDING: certificates]` Certified T-count floors for family B1 at n = 5
      and family B2, from `barrier/certificate.py`.
    - The learned cost model is trained only after the emulator rows exist.

    ### Picking a job back up

    ```python
    from aqora import QPUJob

    QPUJob.from_id("<job id>").counts()
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
