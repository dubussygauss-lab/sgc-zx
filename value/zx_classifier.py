"""Learned gate for the pass selector: predict from the INPUT circuit whether
P2 (PyZX teleport_reduce then pytket L2) is cheaper than P0 (pytket L2) in HQC
at 1000 shots, so that the second compilation can be skipped.

No new compilation.  Labels come from HQC values already in the repository:
  value/selector_ledger_circuits.csv   families A (180), B1 (15), B1x (8, count-only), B2 (20)
  value/family_C_selector.csv          family C (20)
  value/usecase.csv                    use case U (2)
Features are computed from the input QASM in bench/ only (text parsing plus the
spider count of the unsimplified PyZX graph).  The family label is NOT a feature.

Label  pays = round(hqc_P2, 6) < round(hqc_P0, 6)   (ties count as "does not pay")
Target rel_saving = (hqc_P0 - hqc_P2) / hqc_P0

Evaluation (all predictions are held out):
  LOFO  leave-one-family-out over A, B1, B1x, B2, C, U
  GCV   grouped 5-fold CV, groups = construction (A: model and n, B: circuit
        construction shared across B1, B1x, C and U, B2: qubit count)
Models: logistic regression (standardised log features, class_weight balanced)
        and gradient-boosted trees (100 trees, depth 2), seed 20261009.
Baselines: always P0, always P2, majority class of the training fold.
Regret = sum over circuits of HQC(choice) - min(hqc_P0, hqc_P2).
Gated policy: always compile P0, compile P2 only when the model predicts
"pays", keep the cheaper.  Its regret is the loss on false negatives and it
skips one compilation per predicted "does not pay".

Run: python3 value/zx_classifier.py   (writes value/zx_classifier.csv, value/zx_classifier.md)
"""
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "value"
SEED = 20261009
DEC = 6
FAMILIES = ["A", "B1", "B1x", "B2", "C", "U"]
BENCH = {"A": "family_A", "B1": "family_B1", "B1x": "family_B1x", "B2": "family_B2",
         "C": "family_C", "U": "usecase"}
FEATURES = ["n_qubits", "n_gates", "n_cx", "n_t", "n_cont", "n_h", "n_ccx", "depth",
            "frac_cont", "t_density", "cx_density", "zx_spiders"]
LOG_FEATURES = ["n_qubits", "n_gates", "n_cx", "n_t", "n_cont", "n_h", "n_ccx", "depth", "zx_spiders"]
TWO_Q = {"cx", "cz", "swap"}
THREE_Q = {"ccx", "ccz"}
ROT = {"rz", "rx", "ry", "u1", "p"}
T_GATES = {"t", "tdg"}


# ---------------------------------------------------------------- data
def load_labels():
    led = pd.read_csv(OUT / "selector_ledger_circuits.csv")[["file", "family", "hqc_P0", "hqc_P2"]]
    c = pd.read_csv(OUT / "family_C_selector.csv")[["file", "hqc_P0", "hqc_P2"]].assign(family="C")
    u = pd.read_csv(OUT / "usecase.csv")[["file", "hqc_P0", "hqc_P2"]].assign(family="U")
    d = pd.concat([led, c, u], ignore_index=True)
    assert not d.duplicated(["family", "file"]).any()
    d["pays"] = (d.hqc_P2.round(DEC) < d.hqc_P0.round(DEC)).astype(int)
    d["rel_saving"] = (d.hqc_P0 - d.hqc_P2) / d.hqc_P0
    d["hqc_oracle"] = np.minimum(d.hqc_P0, d.hqc_P2)
    return d


def group_of(family, file):
    stem = file[:-5]
    if family == "A":
        m = re.match(r"(tfim|xxz|ladder)_n(\d+)_", stem)
        return f"A:{m.group(1)}_n{m.group(2)}"
    if family == "B2":
        return "B2:" + re.match(r"(haar_n\d+)_", stem).group(1)
    if stem.startswith("grover"):
        return "B:grover"
    if stem.startswith("ham15"):
        return "B:ham15"
    return "B:" + re.sub(r"\d+", "#", stem)


# ---------------------------------------------------------------- features
def _angle(expr):
    return float(eval(expr, {"__builtins__": {}}, {"pi": math.pi}))


def qasm_features(path):
    nq = 0
    counts = dict(n_gates=0, n_cx=0, n_t=0, n_cont=0, n_h=0, n_ccx=0)
    level = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("OPENQASM", "include", "creg", "//", "barrier", "measure")):
            continue
        if line.startswith("qreg"):
            nq += int(re.search(r"\[(\d+)\]", line).group(1))
            continue
        m = re.match(r"([a-z0-9_]+)(\((.*)\))?\s+(.*);", line)
        name, arg, qs = m.group(1), m.group(3), m.group(4)
        qubits = re.findall(r"\w+\[\d+\]", qs)
        counts["n_gates"] += 1
        if name in TWO_Q:
            counts["n_cx"] += 1
        elif name in THREE_Q:
            counts["n_ccx"] += 1
        elif name in T_GATES:
            counts["n_t"] += 1
        elif name == "h":
            counts["n_h"] += 1
        elif name in ROT:
            k = _angle(arg) / (math.pi / 4)
            if abs(k - round(k)) > 1e-9:
                counts["n_cont"] += 1
            elif round(k) % 2:
                counts["n_t"] += 1
        layer = 1 + max(level.get(q, 0) for q in qubits)
        for q in qubits:
            level[q] = layer
    f = dict(n_qubits=nq, **counts, depth=max(level.values()) if level else 0)
    g = f["n_gates"]
    f["frac_cont"] = f["n_cont"] / g
    f["t_density"] = f["n_t"] / g
    f["cx_density"] = f["n_cx"] / g
    return f


def zx_spiders(path):
    import pyzx as zx
    # PyZX's parser rejects scientific notation, so angles are rewritten in fixed point first.
    txt = re.sub(r"\(([^)]*)\)", lambda m: "(" + _fixed(m.group(1)) + ")", path.read_text())
    return zx.Circuit.from_qasm(txt).to_graph().num_vertices()


def _fixed(expr):
    return re.sub(r"[-+]?\d*\.?\d+e[-+]?\d+", lambda m: f"{float(m.group(0)):.20f}", expr)


def build_table():
    d = load_labels()
    rows = []
    for fam, file in zip(d.family, d.file):
        p = ROOT / "bench" / BENCH[fam] / file
        f = qasm_features(p)
        f["zx_spiders"] = zx_spiders(p)
        rows.append(f)
    d = pd.concat([d, pd.DataFrame(rows)], axis=1)
    d["group"] = [group_of(a, b) for a, b in zip(d.family, d.file)]
    return d


# ---------------------------------------------------------------- models
def design(df):
    X = df[FEATURES].astype(float).copy()
    for c in LOG_FEATURES:
        X[c] = np.log1p(X[c])
    return X.values


def make_models():
    return {
        "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=5000, random_state=SEED)),
        "gbt": lambda: GradientBoostingClassifier(
            n_estimators=100, max_depth=2, learning_rate=0.1, random_state=SEED),
    }


def fit_predict(train, test):
    out = {}
    Xtr, Xte, ytr = design(train), design(test), train.pays.values
    for name, mk in make_models().items():
        if len(np.unique(ytr)) == 1:
            out[name] = np.full(len(test), ytr[0])
        else:
            out[name] = mk().fit(Xtr, ytr).predict(Xte)
    out["majority"] = np.full(len(test), int(ytr.mean() > 0.5))
    reg = GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=0.1,
                                    random_state=SEED).fit(Xtr, train.rel_saving.values)
    out["gbt_reg_saving"] = reg.predict(Xte)
    out["mean_saving"] = np.full(len(test), train.rel_saving.mean())
    return out


def run_scheme(d, scheme):
    pred = pd.DataFrame(index=d.index, columns=["logreg", "gbt", "majority",
                                                "gbt_reg_saving", "mean_saving"], dtype=float)
    pred.insert(0, "fold", "")
    if scheme == "lofo":
        splits = [(fam, d.index[d.family != fam], d.index[d.family == fam]) for fam in FAMILIES]
    else:
        gkf = GroupKFold(n_splits=5, shuffle=True, random_state=SEED)
        splits = [(str(k), d.index[tr], d.index[te])
                  for k, (tr, te) in enumerate(gkf.split(d, d.pays, d.group))]
    for fold, tr, te in splits:
        assert set(d.group[tr]).isdisjoint(set(d.group[te])) or scheme == "lofo"
        o = fit_predict(d.loc[tr], d.loc[te])
        pred.loc[te, "fold"] = fold
        for k, v in o.items():
            pred.loc[te, k] = v
    return pred


# ---------------------------------------------------------------- metrics
def bal_acc(y, p):
    rec = [np.mean(p[y == c] == c) for c in (0, 1) if np.any(y == c)]
    return float(np.mean(rec))


def evaluate(sub, pred_col_values):
    y = sub.pays.values
    p = np.asarray(pred_col_values).astype(int)
    hqc = np.where(p == 1, sub.hqc_P2, sub.hqc_P0)
    regret = float(np.sum(hqc - sub.hqc_oracle))
    fn = (p == 0) & (y == 1)
    gated = float(np.sum((sub.hqc_P0 - sub.hqc_oracle)[fn]))
    return dict(acc=float(np.mean(p == y)), bal_acc=bal_acc(y, p), regret=regret,
                regret_gated=gated, skipped=int(np.sum(p == 0)))


POLICIES = ["always_P0", "always_P2", "majority", "rule_cont", "logreg", "gbt", "gbt_reg"]


def table(d, pred):
    rows = []
    for fam in FAMILIES + ["pooled"]:
        m = np.ones(len(d), bool) if fam == "pooled" else (d.family == fam).values
        sub, ps = d[m], pred[m]
        base = dict(family=fam, n=int(m.sum()), n_pays=int(sub.pays.sum()),
                    hqc_oracle=float(sub.hqc_oracle.sum()))
        choices = {"always_P0": np.zeros(len(sub)), "always_P2": np.ones(len(sub)),
                   "majority": ps.majority.values,
                   "rule_cont": (sub.n_cont.values == 0).astype(int),
                   "logreg": ps.logreg.values,
                   "gbt": ps.gbt.values, "gbt_reg": (ps.gbt_reg_saving.values > 0).astype(int)}
        for pol in POLICIES:
            r = dict(base, policy=pol, **evaluate(sub, choices[pol]))
            r["regret_pct_of_oracle"] = 100 * r["regret"] / r["hqc_oracle"]
            r["regret_gated_pct_of_oracle"] = 100 * r["regret_gated"] / r["hqc_oracle"]
            rows.append(r)
    return pd.DataFrame(rows)


def reg_table(d, pred):
    rows = []
    for fam in FAMILIES + ["pooled"]:
        m = np.ones(len(d), bool) if fam == "pooled" else (d.family == fam).values
        y = d.rel_saving[m].values
        rows.append(dict(family=fam, n=int(m.sum()),
                         mae_gbt_reg=float(np.mean(np.abs(pred.gbt_reg_saving[m].values - y))),
                         mae_train_mean=float(np.mean(np.abs(pred.mean_saving[m].values - y))),
                         mean_rel_saving=float(np.mean(y))))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- report
def md(df, cols, nd=3):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (str, bool, np.bool_)):
                cells.append(str(v) if not isinstance(v, np.bool_) else str(bool(v)))
            elif isinstance(v, str):
                cells.append(v)
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{v:d}")
            else:
                cells.append(f"{v:.{nd}f}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def wide(t, metric, nd):
    w = t.pivot(index="family", columns="policy", values=metric).loc[FAMILIES + ["pooled"], POLICIES]
    w = w.reset_index()
    return md(w, ["family"] + POLICIES, nd)


def beats(t):
    """Per family: does the model have strictly lower regret than BOTH fixed baselines?"""
    out = []
    for fam in FAMILIES + ["pooled"]:
        g = t[t.family == fam].set_index("policy")
        best_fixed = min(g.loc["always_P0", "regret"], g.loc["always_P2", "regret"])
        out.append(dict(family=fam, best_fixed_regret=best_fixed,
                        logreg_regret=g.loc["logreg", "regret"], gbt_regret=g.loc["gbt", "regret"],
                        logreg_beats_both=bool(g.loc["logreg", "regret"] < best_fixed - 1e-9),
                        gbt_beats_both=bool(g.loc["gbt", "regret"] < best_fixed - 1e-9)))
    return pd.DataFrame(out)


def random_gate(t):
    """Expected gated regret of a gate that skips the same number of P2 compilations
    uniformly at random within the row: skipped / n * regret(always_P0)."""
    out = []
    for fam in FAMILIES + ["pooled"]:
        g = t[t.family == fam].set_index("policy")
        r = dict(family=fam, n=int(g.loc["always_P0", "n"]), regret_always_P0=g.loc["always_P0", "regret"])
        for pol in ("logreg", "gbt"):
            k = int(g.loc[pol, "skipped"])
            r[f"{pol}_skipped"] = k
            r[f"{pol}_gated"] = g.loc[pol, "regret_gated"]
            r[f"{pol}_random_same_skips"] = k / r["n"] * r["regret_always_P0"]
        out.append(r)
    return pd.DataFrame(out)


def main():
    d = build_table()
    res = {}
    for scheme in ("lofo", "gcv"):
        pred = run_scheme(d, scheme)
        for c in pred.columns:
            d[f"{scheme}_{c}"] = pred[c].values
        res[scheme] = (pred, table(d, pred), reg_table(d, pred))
    cols = (["file", "family", "group"] + FEATURES +
            ["hqc_P0", "hqc_P2", "hqc_oracle", "pays", "rel_saving"] +
            [c for c in d.columns if c.startswith(("lofo_", "gcv_"))])
    d[cols].to_csv(OUT / "zx_classifier.csv", index=False)
    pd.concat([t.assign(scheme=s) for s, (_, t, _) in res.items()]).to_csv(
        OUT / "zx_classifier_metrics.csv", index=False)

    # in-sample GBT feature importances (descriptive only)
    gbt = make_models()["gbt"]().fit(design(d), d.pays.values)
    imp = pd.DataFrame({"feature": FEATURES, "importance": gbt.feature_importances_}) \
        .sort_values("importance", ascending=False)

    n_groups = d.group.nunique()
    lab = d.groupby("family").agg(n=("pays", "size"), n_pays=("pays", "sum"),
                                  mean_rel_saving=("rel_saving", "mean")).loc[FAMILIES].reset_index()
    lab.loc[len(lab)] = ["pooled", len(d), int(d.pays.sum()), d.rel_saving.mean()]
    lab["n"] = lab["n"].astype(int)
    lab["n_pays"] = lab["n_pays"].astype(int)

    s = ["# Learned gate for the pass selector (does ZX pay?)\n",
         "`[F]` Generated by value/zx_classifier.py. No new compilation. Labels from "
         "value/selector_ledger_circuits.csv (A, B1, B1x, B2), value/family_C_selector.csv (C) and "
         "value/usecase.csv (U). B1x is count-only and unchecked. Features from the input QASM in bench/ only. "
         f"Seed {SEED}.\n",
         "## Method\n",
         "- Label `pays` = round(hqc_P2, 6) < round(hqc_P0, 6) at 1000 shots. Ties count as does not pay.\n",
         "- Features (input circuit, no compilation): " + ", ".join(FEATURES) +
         ". n_t counts T, Tdg and rotations at odd multiples of pi/4. n_cont counts rotations whose angle is "
         "not a multiple of pi/4. zx_spiders is the vertex count of the unsimplified PyZX graph. "
         "The family label is not a feature. Counts enter as log1p.\n",
         "- Models: logistic regression (standardised, class_weight balanced, C = 1) and gradient-boosted "
         "trees (100 trees, depth 2, learning rate 0.1). gbt_reg is a gradient-boosted regressor on "
         "rel_saving = (hqc_P0 - hqc_P2)/hqc_P0 that predicts pays when the predicted saving is positive. "
         "No hyperparameter search.\n",
         "- LOFO: train on all other families, predict the held-out family. GCV: GroupKFold(5, shuffle, "
         f"seed {SEED}) over {n_groups} construction groups (A: model and n. B1, B1x, C and U share groups "
         "by construction name, so vbe_adder, tof, barenco_tof, gf2_pow_mult, hwb and grover never straddle "
         "a fold. B2: qubit count).\n",
         "- Regret = sum of HQC(choice) - min(hqc_P0, hqc_P2) over the circuits. One compilation per circuit.\n",
         "- Gated policy: always compile P0, compile P2 only on a predicted pays, keep the cheaper. "
         "regret_gated is its regret (false negatives only). skipped = number of P2 compilations it skips.\n",
         "- B1x shares constructions (tof, barenco_tof, gf2_pow_mult) with B1, so its LOFO split is not "
         "construction-disjoint. The GCV split is.\n",
         "- Balanced accuracy is the mean recall over the classes present. B2 has no circuit where P2 pays "
         "and U has no circuit where it does not, so on those families it reduces to plain accuracy.\n",
         "- rule_cont is a fixed hand rule with no fitting: predict pays exactly when the input has no "
         "continuous-angle rotation (n_cont = 0). It is listed to show how much of any gain a single "
         "feature explains.\n",
         "- always_P2 under the gated policy is the existing two-compilation selector (regret 0, nothing skipped).\n",
         "## Labels\n", md(lab, ["family", "n", "n_pays", "mean_rel_saving"], 4),
         "Oracle HQC total (sum of min(hqc_P0, hqc_P2)): " +
         ", ".join(f"{f} {d[d.family == f].hqc_oracle.sum():.1f}" for f in FAMILIES) +
         f", pooled {d.hqc_oracle.sum():.1f}.\n"]
    for scheme, title in (("lofo", "Leave-one-family-out"), ("gcv", "Grouped 5-fold CV")):
        _, t, rt = res[scheme]
        s += [f"## {title}\n",
              "### Balanced accuracy\n", wide(t, "bal_acc", 3),
              "### Accuracy\n", wide(t, "acc", 3),
              "### Regret (HQC at 1000 shots, one compilation per circuit)\n", wide(t, "regret", 1),
              "### Regret as % of oracle HQC\n", wide(t, "regret_pct_of_oracle", 3),
              "### Gated policy regret (HQC)\n", wide(t, "regret_gated", 1),
              "### Gated policy regret as % of oracle HQC\n", wide(t, "regret_gated_pct_of_oracle", 3),
              "### Second compilations skipped by the gated policy\n", wide(t, "skipped", 0),
              "### Gated policy against a random gate with the same number of skips (expected regret)\n",
              md(random_gate(t), ["family", "n", "regret_always_P0", "logreg_skipped", "logreg_gated",
                                  "logreg_random_same_skips", "gbt_skipped", "gbt_gated",
                                  "gbt_random_same_skips"], 1),
              "### Does the model beat both fixed baselines on regret?\n",
              md(beats(t), ["family", "best_fixed_regret", "logreg_regret", "gbt_regret",
                            "logreg_beats_both", "gbt_beats_both"], 1),
              "### Regression of rel_saving (mean absolute error)\n",
              md(rt, ["family", "n", "mean_rel_saving", "mae_gbt_reg", "mae_train_mean"], 4)]
    s += ["## In-sample GBT feature importances (descriptive, not held out)\n",
          md(imp, ["feature", "importance"], 3)]
    (OUT / "zx_classifier.md").write_text("\n".join(s))
    print("\n".join(s))
    return d, res


if __name__ == "__main__":
    main()
