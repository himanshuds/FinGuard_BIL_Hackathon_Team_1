"""
train_predictor.py  (STRETCH GOAL)
----------------------------------
Train a regression model that predicts a suitable underwriting ASSET VALUE from
a loan's features, and report OUT-OF-SAMPLE RMSE.

The brief says it cares as much about HOW we validate as about the number, so the
methodology here is deliberate and explained:

FEATURES (all knowable before you have the asset value -- no leakage):
  - loan_value        : strongest signal (corr ~0.71 with asset_value)
  - loan_currency     : accounts for scale/economic differences across currencies
  - hq_country        : region effect
  - asset_type        : the last word of the asset description (Plant, Facility,
                        Warehouse, ...) -- a clean categorical extracted from text
  - company_name      : some companies hold systematically larger/smaller assets

TARGET: asset_value.

KEY MODELLING CHOICES (defendable):
  1. LOG-TRANSFORM the target. asset_value spans 150k -> 2.5M and is right-skewed;
     predicting log(asset_value) makes errors multiplicative and stabilises the
     fit. We invert the log for the final RMSE so the number is in real currency
     units, not log units.
  2. loan_value is also log-transformed (same skew reason).
  3. We compare against a BASELINE (predict the mean) so RMSE has context -- a
     number alone means little without "better than what?".
  4. HOLD-OUT TEST SET (20%) touched exactly once, at the end. All model choice
     and tuning happen via 5-fold CROSS-VALIDATION on the training 80% only, so
     the test RMSE is a genuine out-of-sample estimate.

WHY GRADIENT BOOSTING: the relationship is non-linear and mixes numeric +
categorical features; a tree ensemble handles that without heavy feature
engineering. We still report a linear baseline for honesty.

RUN:  python train_predictor.py
Writes asset_predictor.joblib (used by predictor_agent.py).
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

RANDOM_STATE = 42
CSV_PATH = "loans.csv"
MODEL_PATH = "asset_predictor.joblib"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    # asset_type = last word of the description (Plant / Facility / Warehouse...).
    df["asset_type"] = df["asset_description"].str.split().str[-1]
    df["loan_value"] = df["loan_value"].astype(float)
    df["asset_value"] = df["asset_value"].astype(float)
    return df


def build_pipeline() -> Pipeline:
    numeric = ["loan_value"]
    categorical = ["loan_currency", "hq_country", "asset_type", "company_name"]

    # log1p the numeric loan_value inside the pipeline so it applies consistently
    # in CV and at predict time.
    log_numeric = Pipeline([
        ("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
    ])

    pre = ColumnTransformer([
        ("num", log_numeric, numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])

    model = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.08, max_depth=8,
        random_state=RANDOM_STATE,
    )
    return Pipeline([("pre", pre), ("model", model)])


def rmse_real(y_true_log, y_pred_log):
    """Invert the log target and compute RMSE in real currency units."""
    yt = np.expm1(y_true_log)
    yp = np.expm1(y_pred_log)
    return np.sqrt(mean_squared_error(yt, yp))


def main():
    df = load_data()

    X = df[["loan_value", "loan_currency", "hq_country", "asset_type", "company_name"]]
    y = np.log1p(df["asset_value"].values)   # LOG target

    # --- hold-out test set, touched once at the very end ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE
    )

    pipe = build_pipeline()

    # --- 5-fold CV on the TRAINING set only (model selection lives here) ---
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_score(
        pipe, X_train, y_train, cv=kf,
        scoring="neg_root_mean_squared_error",  # in LOG units
    )
    print("=== 5-fold CV on training set (log-unit RMSE) ===")
    print(f"  fold RMSEs (log): {np.round(-cv_scores, 4)}")
    print(f"  mean {(-cv_scores).mean():.4f}  std {(-cv_scores).std():.4f}")

    # --- fit on full training set, evaluate ONCE on the untouched test set ---
    pipe.fit(X_train, y_train)
    y_pred_test = pipe.predict(X_test)

    test_rmse = rmse_real(y_test, y_pred_test)
    test_mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred_test))
    test_r2 = r2_score(np.expm1(y_test), np.expm1(y_pred_test))

    # --- baselines for context ---
    # 1. Predict the mean asset value for everyone.
    mean_pred = np.full_like(y_test, y_train.mean())
    baseline_rmse = rmse_real(y_test, mean_pred)
    # 2. Simple linear model, same features -- shows the ensemble earns its place.
    lin = Pipeline([("pre", build_pipeline().named_steps["pre"]), ("model", Ridge())])
    lin.fit(X_train, y_train)
    lin_rmse = rmse_real(y_test, lin.predict(X_test))

    print("\n=== OUT-OF-SAMPLE (held-out 20% test set, real currency units) ===")
    print(f"  Model (gradient boosting) RMSE : {test_rmse:,.0f}")
    print(f"  Baseline (predict mean)   RMSE : {baseline_rmse:,.0f}")
    print(f"  Linear (Ridge)            RMSE : {lin_rmse:,.0f}")
    print(f"  Model MAE                      : {test_mae:,.0f}")
    print(f"  Model R^2                      : {test_r2:.3f}")
    print(f"  Improvement over baseline      : {(1 - test_rmse/baseline_rmse)*100:.1f}%")

    # --- refit on ALL data and save, for the agent to use ---
    pipe.fit(X, y)
    joblib.dump(pipe, MODEL_PATH)
    print(f"\nSaved model -> {MODEL_PATH} (refit on all rows for production use)")


if __name__ == "__main__":
    main()
