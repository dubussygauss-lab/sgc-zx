"""Tests for model/cost_model.py.  Run: python -m pytest model/test_cost_model.py
or python model/test_cost_model.py."""

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cost_model as cm  # noqa: E402

B1_CSV = os.path.join(ROOT, "results", "family_B1_proxy_h22e.csv")


def synthetic(n_rows=2000, seed=1, noise_sd=1e-4):
    """Rows whose F_H follows a known exponential law in the features."""
    rng = np.random.default_rng(seed)
    n = rng.integers(3, 9, size=n_rows)
    n_2q = rng.integers(2, 200, size=n_rows)
    n_1q = rng.integers(2, 250, size=n_rows)
    depth = np.minimum(n_2q, rng.integers(1, 150, size=n_rows))
    support = np.array([rng.integers(1, 2 ** k + 1) for k in n])
    df = pd.DataFrame(dict(n_qubits=n, n_2q=n_2q, n_1q=n_1q, depth_2q=depth,
                           support_size=support, model="synthetic",
                           file=["c%d" % i for i in range(n_rows)]))
    X = cm.feature_matrix(df)
    true = np.array([1.0e-3, 7.0e-5, 1.4e-3, -1.0e-4, -2.0e-6, -3.0e-3, 5.0e-4])
    y = X.to_numpy() @ true + rng.normal(0, noise_sd, size=n_rows)
    df["F_H"] = np.exp(-y)
    return df, true


def test_ols_recovers_known_law():
    df, true = synthetic()
    X, y = cm.feature_matrix(df), cm.target(df)
    m = cm.OLS().fit(X, y)
    z = (m.coef - true) / m.se
    assert np.all(np.abs(z) < 4), z
    assert np.allclose(m.coef, true, rtol=0.05, atol=2e-6), (m.coef, true)


def test_ols_exact_without_noise():
    df, true = synthetic(noise_sd=0.0)
    X, y = cm.feature_matrix(df), cm.target(df)
    m = cm.OLS().fit(X, y)
    assert np.allclose(m.coef, true, rtol=1e-8, atol=1e-12)


def test_ridge_close_to_ols_for_small_lambda():
    df, true = synthetic()
    X, y = cm.feature_matrix(df), cm.target(df)
    r = cm.Ridge(lam=cm.RIDGE_LAMBDA).fit(X, y)
    assert np.allclose(r.coef, true, rtol=0.1, atol=5e-6), (r.coef, true)


def test_physics_baseline_exact_on_its_own_law():
    df, _ = synthetic(noise_sd=0.0)
    X = cm.feature_matrix(df)
    p = cm.physics_params()
    y = X[cm.PHYSICS_FEATURES].to_numpy() @ p
    yhat = cm.Physics().predict(X)
    assert np.allclose(y, yhat)
    assert np.isclose(p[0], 1.29e-3) and np.isclose(p[1], 7.3e-5)
    assert np.isclose(p[2], 0.5 * (9e-4 + 1.8e-3) + 4e-5)


def test_physics_baseline_matches_b1_fit_slope():
    """The B1 fit y = a n_2q + b n_1q + s n (results/proxy_h22e_fits.log) has
    a = 1.5128e-03 +/- 2.6e-04, b = -3.2295e-04 +/- 2.1e-04, s = 9.9836e-04 +/- 4.4e-04.
    Recompute it and check the fixed H2-2E values lie within 2 SE of each."""
    if not os.path.exists(B1_CSV):
        import pytest
        pytest.skip("B1 CSV not present")
    df = pd.read_csv(B1_CSV)
    X = cm.feature_matrix(df)[cm.PHYSICS_FEATURES]
    y = cm.target(df)
    A = X.to_numpy()
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ beta
    s2 = res @ res / (len(y) - 3)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(A.T @ A)))
    logged = np.array([1.5128e-03, -3.2295e-04, 9.9836e-04])
    logged_se = np.array([2.6e-04, 2.1e-04, 4.4e-04])
    assert np.allclose(beta, logged, rtol=1e-3), (beta, logged)
    assert np.allclose(se, logged_se, rtol=0.05), (se, logged_se)
    z = (cm.physics_params() - beta) / se
    assert np.all(np.abs(z) < 2), z


def test_features_support_extremes():
    df = pd.DataFrame(dict(n_qubits=[5, 5, 1, 8], n_2q=[10, 10, 0, 3], n_1q=[4, 4, 0, 1],
                           depth_2q=[3, 3, 0, 1], support_size=[1, 32, 1, 256], F_H=[0.9] * 4))
    X = cm.feature_matrix(df)
    assert np.all(np.isfinite(X.to_numpy()))
    assert X.loc[0, "log2_support"] == 0.0
    assert np.isclose(X.loc[0, "n_2q_offsupport"], 10 * (1 - 1 / 32))
    assert X.loc[1, "log2_support"] == 5.0
    assert X.loc[1, "n_2q_offsupport"] == 0.0
    assert X.loc[2, "n_2q_offsupport"] == 0.0
    assert X.loc[3, "log2_support"] == 8.0 and X.loc[3, "n_2q_offsupport"] == 0.0
    bad = df.copy()
    bad.loc[0, "support_size"] = 33
    try:
        cm.feature_matrix(bad)
        raise AssertionError("support_size > 2^n accepted")
    except ValueError:
        pass


def test_score_identity():
    y = np.array([0.01, 0.02, 0.05])
    s = cm.score(y, y, np.exp(-y))
    assert s["rmse_y"] == 0 and s["r2_y"] == 1 and s["mae_F"] == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
