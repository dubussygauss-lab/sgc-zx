"""Learned cost model: predict the emulated Hellinger fidelity F_H of a compiled
circuit from compile-time features.

Input CSVs (one row per circuit x pipeline) with at least the columns
    n_qubits, n_2q, n_1q, depth_2q, support_size, F_H, model
as written by noise/run_proxy.py.  The script is written for the H2-2E
emulator CSVs that will replace the proxy CSVs; nothing in it depends on the
data being proxy data except the file names given on the command line.

Target
    y = -ln F_H.   For a product of independent small error channels
    F_H ~ exp(-sum_k p_k N_k), so y is linear in gate counts to first order.

Features (feature_matrix)
    n_2q            number of ZZPhase / ZZMax gates
    n_1q            number of PhasedX gates (Rz is virtual and noiseless)
    n_qubits        measured qubits (SPAM term, one readout + init per qubit)
    depth_2q        ASAP two-qubit depth (idle / memory error stand-in)
    support_size    number of bitstrings with ideal probability > 1e-12
    log2_support    log2(support_size); 0 for a deterministic output
    n_2q_offsupport n_2q * (1 - support_size / 2^n_qubits)
        Interaction justified by the Hellinger metric: a Pauli fault after a
        gate sends a fraction of the output mass to other bitstrings.  When
        the ideal distribution is spread over most of the 2^n strings the
        displaced mass lands mostly on strings that already carry ideal
        weight, and sqrt(p q) summed over the support barely changes.  When
        the ideal output is one string every fault removes its mass from the
        support entirely, so the full per-gate error shows in -ln F_H.  The
        factor (1 - support_size / 2^n) is the fraction of the space outside
        the support, a first-order proxy for the mass that is lost.

Models
    physics   y = p2 n_2q + p1 n_1q + (p_meas_avg + p_init) n_qubits with the
              H2-2E emulator defaults fixed (no fitting).  p_meas_avg is the
              mean of the two asymmetric readout flip rates.
    ols       ordinary least squares on the features, no intercept (an empty
              circuit has y = 0; the n_qubits column carries the SPAM floor).
    ridge     ridge regression, columns scaled to unit RMS on the training
              set, penalty lambda = RIDGE_LAMBDA on the scaled coefficients,
              no intercept.
    gbr       sklearn GradientBoostingRegressor (fixed hyperparameters below),
              skipped if sklearn is not importable.

Splits
    lofo      leave-one-family-out: train A -> test B1, train B1 -> test A
    lomo      leave-one-model-out within A: hold out tfim, xxz or ladder
    cv5       5-fold random CV on A + B1 pooled (rows shuffled, seed 0);
              out-of-fold predictions are also scored per family.  The five
              pipeline rows of one circuit can fall in different folds, so
              this split measures interpolation between pipelines of a
              circuit already seen.
    cv5g      5-fold CV with the folds drawn over circuit classes: the
              `file` name with the disorder-seed suffix _s<k> removed
              (family A seeds of one (model, n, r, disorder) have identical
              gate counts and F_H within 3e-3, so grouping by file alone
              would leak near-duplicates).  All pipelines and seeds of a
              class are in the same fold, so the test class is unseen.
              Used for the calibration figure and the GBR permutation
              importance.

Metrics (per model x split x test set)
    rmse_y, r2_y   on y = -ln F_H (R^2 about the mean of the test y, can be
                   negative for a model worse than the test-set mean)
    mae_F          mean |exp(-y_hat) - F_H|

Outputs
    results/cost_model_metrics.csv
    results/cost_model_coefficients.csv   OLS coefficients with OLS standard
                                          errors (train = A, B1, pooled), ridge
                                          coefficients, GBR permutation
                                          importance (out-of-fold, cv5g)
    results/fig_cost_model.{pdf,png}
    results/cost_model.md

    With --prefix TAG the four outputs are cost_model_TAGmetrics.csv,
    cost_model_TAGcoefficients.csv, cost_model_TAGfig.{pdf,png} and
    cost_model_TAGautoreport.md (see output_names).

Usage: python model/cost_model.py [--family-a CSV] [--family-b CSV] [--out DIR] [--prefix TAG]
"""

import argparse
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "noise"))
from h2_params import H2_2E_EMULATOR  # noqa: E402

FEATURES = ["n_2q", "n_1q", "n_qubits", "depth_2q", "support_size",
            "log2_support", "n_2q_offsupport"]
PHYSICS_FEATURES = ["n_2q", "n_1q", "n_qubits"]
RIDGE_LAMBDA = 1.0
GBR_PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.05,
                  subsample=0.8, random_state=0)
SEED = 0
N_FOLDS = 5


# ---------------------------------------------------------------- features

def feature_matrix(df):
    """DataFrame of the FEATURES columns.  Works for support_size = 1
    (log2_support = 0) and support_size = 2^n (n_2q_offsupport = 0)."""
    n = df["n_qubits"].to_numpy(float)
    s = df["support_size"].to_numpy(float)
    if np.any(s < 1) or np.any(s > 2.0 ** n):
        raise ValueError("support_size outside [1, 2^n]")
    X = pd.DataFrame(index=df.index)
    X["n_2q"] = df["n_2q"].to_numpy(float)
    X["n_1q"] = df["n_1q"].to_numpy(float)
    X["n_qubits"] = n
    X["depth_2q"] = df["depth_2q"].to_numpy(float)
    X["support_size"] = s
    X["log2_support"] = np.log2(s)
    X["n_2q_offsupport"] = X["n_2q"] * (1.0 - s / 2.0 ** n)
    return X[FEATURES]


def target(df):
    return -np.log(df["F_H"].to_numpy(float))


def physics_params(par=H2_2E_EMULATOR):
    """Fixed coefficients of the physics baseline on PHYSICS_FEATURES."""
    p_meas = 0.5 * (par["p_meas_0"] + par["p_meas_1"]) + par["p_init"]
    return np.array([par["p2"], par["p1"], p_meas])


# ------------------------------------------------------------------ models

class Physics:
    name = "physics"
    features = PHYSICS_FEATURES

    def __init__(self, par=H2_2E_EMULATOR):
        self.coef = physics_params(par)

    def fit(self, X, y):
        return self

    def predict(self, X):
        return X[self.features].to_numpy(float) @ self.coef


class OLS:
    name = "ols"
    features = FEATURES

    def fit(self, X, y):
        A = X[self.features].to_numpy(float)
        self.coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        res = y - A @ self.coef
        dof = len(y) - A.shape[1]
        s2 = float(res @ res) / dof if dof > 0 else float("nan")
        self.se = np.sqrt(np.diag(s2 * np.linalg.pinv(A.T @ A)))
        self.resid_sd = math.sqrt(s2) if dof > 0 else float("nan")
        return self

    def predict(self, X):
        return X[self.features].to_numpy(float) @ self.coef


class Ridge:
    name = "ridge"
    features = FEATURES

    def __init__(self, lam=RIDGE_LAMBDA):
        self.lam = lam

    def fit(self, X, y):
        A = X[self.features].to_numpy(float)
        self.scale = np.sqrt((A ** 2).mean(axis=0))
        self.scale[self.scale == 0] = 1.0
        As = A / self.scale
        k = As.shape[1]
        b = np.linalg.solve(As.T @ As + self.lam * np.eye(k), As.T @ y)
        self.coef = b / self.scale
        return self

    def predict(self, X):
        return X[self.features].to_numpy(float) @ self.coef


def make_gbr():
    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        return None

    class GBR:
        name = "gbr"
        features = FEATURES

        def __init__(self):
            self.m = GradientBoostingRegressor(**GBR_PARAMS)

        def fit(self, X, y):
            self.m.fit(X[self.features].to_numpy(float), y)
            return self

        def predict(self, X):
            return self.m.predict(X[self.features].to_numpy(float))

    return GBR


def model_factories():
    fs = {"physics": Physics, "ols": OLS, "ridge": Ridge}
    G = make_gbr()
    if G is not None:
        fs["gbr"] = G
    return fs


# ----------------------------------------------------------------- metrics

def score(y, yhat, F):
    res = y - yhat
    rmse = float(np.sqrt(np.mean(res ** 2)))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(res @ res) / ss_tot if ss_tot > 0 else float("nan")
    mae_F = float(np.mean(np.abs(np.exp(-yhat) - F)))
    return dict(rmse_y=rmse, r2_y=r2, mae_F=mae_F, n_test=int(len(y)))


def run_split(factories, X_tr, y_tr, X_te, y_te, F_te, split, train, test):
    rows, preds = [], {}
    for name, M in factories.items():
        m = M().fit(X_tr, y_tr)
        yhat = m.predict(X_te)
        preds[name] = yhat
        rows.append(dict(model=name, split=split, train=train, test=test, **score(y_te, yhat, F_te)))
    return rows, preds


def evaluate(dfA, dfB, factories):
    """All splits.  Returns (metrics rows, out-of-fold cv5 predictions on the
    pooled frame, LOFO train-A predictions on B1, pooled frame)."""
    XA, yA, FA = feature_matrix(dfA), target(dfA), dfA["F_H"].to_numpy(float)
    XB, yB, FB = feature_matrix(dfB), target(dfB), dfB["F_H"].to_numpy(float)
    rows = []

    # leave-one-family-out
    r, pred_A_to_B = run_split(factories, XA, yA, XB, yB, FB, "lofo", "A", "B1")
    rows += r
    r, _ = run_split(factories, XB, yB, XA, yA, FA, "lofo", "B1", "A")
    rows += r

    # leave-one-model-out within A
    models = sorted(dfA["model"].unique())
    for mdl in models:
        te = (dfA["model"] == mdl).to_numpy()
        r, _ = run_split(factories, XA[~te], yA[~te], XA[te], yA[te], FA[te],
                         "lomo", "A minus %s" % mdl, "A %s" % mdl)
        rows += r

    # 5-fold CV on the pool: random over rows (cv5) and grouped by circuit (cv5g)
    pool = pd.concat([dfA.assign(family="A"), dfB.assign(family="B1")], ignore_index=True)
    Xp, yp, Fp = feature_matrix(pool), target(pool), pool["F_H"].to_numpy(float)
    oof = {}
    for split in ("cv5", "cv5g"):
        oof[split] = {name: np.full(len(pool), np.nan) for name in factories}
        for te in fold_masks(pool, grouped=(split == "cv5g")):
            _, preds = run_split(factories, Xp[~te], yp[~te], Xp[te], yp[te], Fp[te], split, "fold", "fold")
            for name, yhat in preds.items():
                oof[split][name][te] = yhat
        for name in factories:
            rows.append(dict(model=name, split=split, train="A+B1 (4/5)", test="A+B1 (1/5)",
                             **score(yp, oof[split][name], Fp)))
            for fam in ("A", "B1"):
                m = (pool["family"] == fam).to_numpy()
                rows.append(dict(model=name, split=split, train="A+B1 (4/5)", test="%s rows of fold" % fam,
                                 **score(yp[m], oof[split][name][m], Fp[m])))
    return rows, oof, pred_A_to_B, pool


def fold_masks(pool, grouped, n_folds=N_FOLDS, seed=SEED):
    """List of boolean test masks.  grouped=False: rows shuffled into folds;
    grouped=True: circuit classes (`file` without the _s<seed> suffix)
    shuffled into folds, every row of a class in the same fold."""
    rng = np.random.default_rng(seed)
    if grouped:
        cls = pool["file"].str.replace(r"_s\d+\.qasm$", ".qasm", regex=True)
        groups = np.array(sorted(cls.unique()))
        parts = np.array_split(rng.permutation(groups), n_folds)
        return [cls.isin(p).to_numpy() for p in parts]
    parts = np.array_split(rng.permutation(len(pool)), n_folds)
    masks = []
    for p in parts:
        te = np.zeros(len(pool), bool)
        te[p] = True
        masks.append(te)
    return masks


# ------------------------------------------------------- coefficients etc.

def coefficient_table(dfA, dfB, pool, factories, oof):
    rows = []
    for train, df in (("A", dfA), ("B1", dfB), ("A+B1", pool)):
        X, y = feature_matrix(df), target(df)
        m = OLS().fit(X, y)
        for f, c, s in zip(FEATURES, m.coef, m.se):
            rows.append(dict(model="ols", train=train, feature=f, value=c, se=s,
                             t=c / s if s > 0 else float("nan"), kind="coefficient"))
        rows.append(dict(model="ols", train=train, feature="resid_sd", value=m.resid_sd,
                         se=float("nan"), t=float("nan"), kind="fit"))
        r = Ridge().fit(X, y)
        for f, c in zip(FEATURES, r.coef):
            rows.append(dict(model="ridge", train=train, feature=f, value=c, se=float("nan"),
                             t=float("nan"), kind="coefficient"))
    p = physics_params()
    for f, c in zip(PHYSICS_FEATURES, p):
        rows.append(dict(model="physics", train="none", feature=f, value=c, se=0.0,
                         t=float("nan"), kind="coefficient"))

    if "gbr" in factories:
        imp = permutation_importance_cv(pool, factories["gbr"])
        for f, (mu, sd) in zip(FEATURES, imp):
            rows.append(dict(model="gbr", train="A+B1 (cv5g out-of-fold)", feature=f, value=mu,
                             se=sd, t=float("nan"), kind="permutation_importance"))
    return pd.DataFrame(rows)


def permutation_importance_cv(pool, G, n_repeats=10):
    """Permutation importance of each feature for the GBR, measured as the
    increase of out-of-fold MSE of y when that feature is shuffled in the test
    fold of the circuit-grouped split cv5g; mean and sd over 5 folds x n_repeats."""
    Xp, yp = feature_matrix(pool), target(pool)
    rng = np.random.default_rng(SEED + 1)
    inc = {f: [] for f in FEATURES}
    for te in fold_masks(pool, grouped=True):
        m = G().fit(Xp[~te], yp[~te])
        base = np.mean((yp[te] - m.predict(Xp[te])) ** 2)
        for f in FEATURES:
            for _ in range(n_repeats):
                Xs = Xp[te].copy()
                Xs[f] = rng.permutation(Xs[f].to_numpy())
                inc[f].append(np.mean((yp[te] - m.predict(Xs)) ** 2) - base)
    return [(float(np.mean(inc[f])), float(np.std(inc[f]))) for f in FEATURES]


# ------------------------------------------------------------------ figure

def make_figure(pool, oof, pred_A_to_B, coefs, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8))
    F = pool["F_H"].to_numpy(float)
    fam = pool["family"].to_numpy()
    col = {"A": "#0072B2", "B1": "#D55E00"}
    best = "ols"
    oof = oof["cv5g"]
    for f in ("A", "B1"):
        m = fam == f
        ax1.scatter(F[m], np.exp(-oof[best][m]), s=14, alpha=0.7, c=col[f], linewidths=0,
                    label="%s, cv5g out-of-fold (%s)" % (f, best))
    mB = fam == "B1"
    ax1.scatter(F[mB], np.exp(-pred_A_to_B[best]), s=40, facecolors="none", edgecolors=col["B1"],
                marker="s", label="B1, trained on A only (%s)" % best)
    if "gbr" in oof:
        ax1.scatter(F[mB], np.exp(-pred_A_to_B["gbr"]), s=40, facecolors="none", edgecolors="#555555",
                    marker="^", label="B1, trained on A only (gbr)")
    lo = min(F.min(), min(np.exp(-oof[best]).min(), np.exp(-pred_A_to_B[best]).min())) - 0.01
    ax1.plot([lo, 1], [lo, 1], "k:", lw=1)
    ax1.set_xlabel("actual F_H")
    ax1.set_ylabel("predicted F_H = exp(-y_hat)")
    ax1.set_title("calibration; dotted = identity", fontsize=9)
    ax1.legend(fontsize=7, loc="upper left")
    ax1.grid(alpha=0.3)

    c = coefs[(coefs.model == "ols") & (coefs.train == "A+B1") & (coefs.kind == "coefficient")]
    Xp = feature_matrix(pool)
    sd = Xp.std().to_numpy()
    vals = c["value"].to_numpy() * sd
    errs = c["se"].to_numpy() * sd
    ypos = np.arange(len(FEATURES))
    ax2.barh(ypos, vals, xerr=errs, color="#0072B2", alpha=0.8, capsize=3,
             label="OLS (A+B1): coefficient x feature SD, +/- 1 SE")
    ax2.axvline(0, color="k", lw=0.8)
    ax2.set_yticks(ypos)
    ax2.set_yticklabels(FEATURES, fontsize=8)
    ax2.invert_yaxis()
    ax2.set_xlabel("contribution to y = -ln F_H per 1 SD of the feature")
    ax2.grid(alpha=0.3, axis="x")
    g = coefs[(coefs.model == "gbr") & (coefs.kind == "permutation_importance")]
    if len(g):
        ax3 = ax2.twiny()
        ax3.plot(g["value"].to_numpy(), ypos, "D", color="#D55E00", ms=6,
                 label="GBR permutation importance (cv5g, MSE increase)")
        ax3.set_xlabel("GBR permutation importance (increase of out-of-fold MSE of y)", fontsize=8)
        ax3.set_xlim(left=min(0, g["value"].min()))
        h1, l1 = ax2.get_legend_handles_labels()
        h2, l2 = ax3.get_legend_handles_labels()
        ax2.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.16),
                   ncol=1, frameon=False)
    else:
        ax2.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.16), frameon=False)
    fig.tight_layout()
    fig.savefig(out + ".pdf")
    fig.savefig(out + ".png", dpi=160)


# ------------------------------------------------------------------ report

def fmt_metrics(df):
    lines = ["| model | split | train | test | n | RMSE(y) | R^2(y) | MAE(F_H) |", "|---|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        lines.append("| %s | %s | %s | %s | %d | %.4f | %.3f | %.4f |" % (
            r.model, r.split, r.train, r.test, r.n_test, r.rmse_y, r.r2_y, r.mae_F))
    return "\n".join(lines)


def fmt_coefs(df):
    lines = ["| model | train | feature | value | SE | t |", "|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        se = "" if np.isnan(r.se) else "%.2e" % r.se
        t = "" if np.isnan(r.t) else "%.1f" % r.t
        lines.append("| %s | %s | %s | %.3e | %s | %s |" % (r.model, r.train, r.feature, r.value, se, t))
    return "\n".join(lines)


def verdict_text(m, n_b1_circuits=None):
    """Generalisation verdict written from the metric rows."""
    def r(model, split, test):
        return m[(m.model == model) & (m.split == split) & (m.test == test)].iloc[0]
    fitted = [x for x in sorted(m.model.unique()) if x != "physics"]
    ab = {x: r(x, "lofo", "B1") for x in fitted}
    ba = {x: r(x, "lofo", "A") for x in fitted}
    best_ab = min(ab, key=lambda x: ab[x].mae_F)
    best_ba = min(ba, key=lambda x: ba[x].mae_F)
    phys_ab, phys_ba = r("physics", "lofo", "B1"), r("physics", "lofo", "A")
    xxz = {x: r(x, "lomo", "A xxz") for x in fitted}
    out = ["", "### Verdict", ""]
    out.append("- Train A, test B1: best fitted model %s, R^2 = %.3f, MAE(F_H) = %.4f; the unfitted physics "
               "baseline gives R^2 = %.3f, MAE(F_H) = %.4f. Fitting on A changes the B1 error by %+.4f in "
               "MAE(F_H) relative to the baseline." % (
                   best_ab, ab[best_ab].r2_y, ab[best_ab].mae_F, phys_ab.r2_y, phys_ab.mae_F,
                   ab[best_ab].mae_F - phys_ab.mae_F))
    out.append("- Train B1, test A: best fitted model %s, R^2 = %.3f, MAE(F_H) = %.4f; physics baseline "
               "R^2 = %.3f, MAE(F_H) = %.4f. %s" % (
                   best_ba, ba[best_ba].r2_y, ba[best_ba].mae_F, phys_ba.r2_y, phys_ba.mae_F,
                   "No model reaches R^2 = 0.5 in this direction." if max(v.r2_y for v in ba.values()) < 0.5
                   else "At least one model reaches R^2 >= 0.5."))
    out.append("- Hold out xxz within A: " + "; ".join("%s R^2 = %.3f" % (x, xxz[x].r2_y) for x in fitted) + ".")
    ok_ab = ab[best_ab].r2_y >= 0.8 and ab[best_ab].mae_F < phys_ab.mae_F
    ok_ba = max(v.r2_y for v in ba.values()) >= 0.8
    if ok_ab and ok_ba:
        out.append("- Reading: the fitted models transfer across families in both directions.")
    elif ok_ab:
        out.append("- Reading: transfer is one-directional. Trained on A (%d rows), the best model predicts "
                   "B1 with R^2 = %.3f against %.3f for the unfitted baseline and MAE(F_H) %.4f against "
                   "%.4f. Trained on B1 (%d rows) no model predicts A. Within a family the models "
                   "interpolate (cv5g); across families the evidence is one direction on %d B1 circuits, "
                   "which does not establish generalisation." % (
                       int(m[(m.split == "lofo") & (m.test == "A")].n_test.iloc[0]),
                       ab[best_ab].r2_y, phys_ab.r2_y, ab[best_ab].mae_F, phys_ab.mae_F,
                       int(m[(m.split == "lofo") & (m.test == "B1")].n_test.iloc[0]),
                       n_b1_circuits))
    else:
        out.append("- Reading: the fitted models interpolate within a family only; neither direction of the "
                   "leave-one-family-out split reaches R^2 = 0.8.")
    out.append("")
    return out


def write_report(path, metrics, coefs, dfA, dfB, a_path, b_path, fig):
    p = physics_params()
    m = metrics
    lofo = m[m.split == "lofo"]
    cv = m[(m.split == "cv5g")]
    lomo = m[m.split == "lomo"]

    def get(split_df, model, test):
        r = split_df[(split_df.model == model) & (split_df.test == test)].iloc[0]
        return r

    verdict = []
    for model in sorted(m.model.unique()):
        ab = get(lofo, model, "B1")
        ba = get(lofo, model, "A")
        cvb = get(cv, model, "B1 rows of fold")
        cva = get(cv, model, "A rows of fold")
        verdict.append("| %s | %.3f / %.4f | %.3f / %.4f | %.3f / %.4f | %.3f / %.4f |" % (
            model, ab.r2_y, ab.mae_F, ba.r2_y, ba.mae_F, cva.r2_y, cva.mae_F, cvb.r2_y, cvb.mae_F))

    txt = []
    txt.append("# Learned cost model: F_H from compile-time features\n")
    txt.append("Generated by `model/cost_model.py` from `%s` (%d rows) and `%s` (%d rows). "
               "Every number below is computed by that script.\n" % (
                   os.path.relpath(a_path, ROOT), len(dfA), os.path.relpath(b_path, ROOT), len(dfB)))
    txt.append("Data status: these are PROXY fidelities (local density-matrix model, H2-2E default "
               "parameters, `noise/run_proxy.py`), not emulator output. The script reruns unchanged on "
               "emulator CSVs with the same columns.\n")
    txt.append("## Target and features\n")
    txt.append("y = -ln F_H. Features: n_2q, n_1q, n_qubits, depth_2q, support_size, "
               "log2_support = log2(support_size), n_2q_offsupport = n_2q (1 - support_size / 2^n_qubits). "
               "The last term is the interaction between gate count and the fraction of the output space "
               "outside the ideal support: a fault moves output mass off the ideal distribution, and the "
               "Hellinger overlap only loses the part of that mass that lands outside the support, so the "
               "per-gate cost in -ln F_H grows with (1 - support_size / 2^n).\n")
    txt.append("## Models\n")
    txt.append("- physics (no fitting): y = p2 n_2q + p1 n_1q + (p_meas_avg + p_init) n_qubits with "
               "p2 = %.3g, p1 = %.3g, p_meas_avg + p_init = %.3g (H2-2E defaults, `noise/h2_params.py`).\n"
               "- ols: least squares on the seven features, no intercept.\n"
               "- ridge: unit-RMS column scaling on the training set, lambda = %g, no intercept.\n"
               "- gbr: sklearn GradientBoostingRegressor(%s).\n" % (
                   p[0], p[1], p[2], RIDGE_LAMBDA, ", ".join("%s=%s" % kv for kv in GBR_PARAMS.items())))
    txt.append("## Metrics (all splits)\n")
    txt.append(fmt_metrics(m) + "\n")
    txt.append("## Generalisation summary (R^2 of y / MAE of F_H)\n")
    txt.append("cv5g holds out whole circuit classes (all pipelines and disorder seeds of one (model, n, r, "
               "disorder) of A, or one B1 circuit, in the test fold); cv5 in the full table above holds out "
               "rows, so the same circuit under another pipeline or seed is in the training set and its scores "
               "measure interpolation only.\n")
    txt.append("| model | train A, test B1 | train B1, test A | cv5g, A rows | cv5g, B1 rows |\n|---|---|---|---|---|")
    txt += verdict
    txt += verdict_text(m, n_b1_circuits=int(dfB["file"].nunique()))
    txt.append("## Leave-one-model-out within A\n")
    txt.append(fmt_metrics(lomo) + "\n")
    txt.append("## Coefficients\n")
    txt.append("OLS standard errors are homoscedastic OLS errors; the rows of one circuit under five "
               "pipelines are not independent, so the SEs are optimistic. Permutation importance of the "
               "GBR is the mean increase of out-of-fold MSE of y over the 5 circuit-grouped folds x 10 shuffles (SE column = sd).\n")
    txt.append(fmt_coefs(coefs) + "\n")
    txt.append("## Figure\n")
    txt.append("`%s.pdf` / `.png`: (a) predicted vs actual F_H per family, out-of-fold cv5g predictions of the "
               "OLS model (filled) and B1 predictions of models trained on A only (hollow); (b) OLS "
               "coefficients scaled by the feature SD with 1 SE bars, GBR permutation importance as diamonds.\n"
               % os.path.relpath(fig, ROOT))
    with open(path, "w") as fh:
        fh.write("\n".join(txt))


# -------------------------------------------------------------------- main

def output_names(prefix: str = "") -> dict:
    """Output file names.  The empty prefix gives the original names."""
    if not prefix:
        return {"metrics": "cost_model_metrics.csv", "coefficients": "cost_model_coefficients.csv",
                "figure": "fig_cost_model", "report": "cost_model.md"}
    return {"metrics": f"cost_model_{prefix}metrics.csv",
            "coefficients": f"cost_model_{prefix}coefficients.csv",
            "figure": f"cost_model_{prefix}fig", "report": f"cost_model_{prefix}autoreport.md"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family-a", default=os.path.join(ROOT, "results", "family_A_proxy_h22e.csv"))
    ap.add_argument("--family-b", default=os.path.join(ROOT, "results", "family_B1_proxy_h22e.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--prefix", default="",
                    help="output name tag. Empty (default) writes cost_model_metrics.csv, "
                         "cost_model_coefficients.csv, fig_cost_model.{pdf,png} and cost_model.md. "
                         "A tag such as selene_ writes cost_model_selene_metrics.csv, "
                         "cost_model_selene_coefficients.csv, cost_model_selene_fig.{pdf,png} and "
                         "cost_model_selene_autoreport.md.")
    args = ap.parse_args()
    names = output_names(args.prefix)

    dfA = pd.read_csv(args.family_a)
    dfB = pd.read_csv(args.family_b)
    factories = model_factories()
    print("models:", list(factories))
    rows, oof, pred_A_to_B, pool = evaluate(dfA, dfB, factories)
    metrics = pd.DataFrame(rows)
    coefs = coefficient_table(dfA, dfB, pool, factories, oof)

    os.makedirs(args.out, exist_ok=True)
    metrics.to_csv(os.path.join(args.out, names["metrics"]), index=False)
    coefs.to_csv(os.path.join(args.out, names["coefficients"]), index=False)
    fig = os.path.join(args.out, names["figure"])
    make_figure(pool, oof, pred_A_to_B, coefs, fig)
    write_report(os.path.join(args.out, names["report"]), metrics, coefs, dfA, dfB,
                 args.family_a, args.family_b, fig)
    pd.set_option("display.width", 200)
    print(metrics.to_string(index=False, float_format=lambda v: "%.4g" % v))
    print(coefs.to_string(index=False, float_format=lambda v: "%.3e" % v))


if __name__ == "__main__":
    main()
