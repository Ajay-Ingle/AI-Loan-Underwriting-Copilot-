"""ML training script: trains and MLflow-tracks the XGBoost credit-risk model."""

import pickle
from pathlib import Path

import mlflow
import mlflow.xgboost
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "ml" / "data" / "applicants.csv"
MODEL_OUT_PATH = ROOT_DIR / "mcp_server" / "models" / "credit_model.pkl"

# MLflow: SQLite backend store for run metadata, separate folder for artifacts
DB_PATH = ROOT_DIR / "mlflow.db"
ARTIFACT_DIR = ROOT_DIR / "mlartifacts"
EXPERIMENT_NAME = "credit-risk-xgboost"

FEATURE_COLUMNS = [
    "age",
    "annual_income",
    "employment_years",
    "existing_debt",
    "requested_loan_amount",
    "credit_history_length",
    "num_late_payments_last_2y",
    "dti_ratio",
]
TARGET_COLUMN = "default"

BASE_HYPERPARAMS = {
    "n_estimators": 200,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": 42,
    "eval_metric": "logloss",
}


def setup_mlflow():
    """Point MLflow at a SQLite backend store, with an explicit artifact location
    so the model file has a well-defined home instead of MLflow guessing a default."""
    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.resolve().as_posix()}")

    if mlflow.get_experiment_by_name(EXPERIMENT_NAME) is None:
        mlflow.create_experiment(
            EXPERIMENT_NAME,
            artifact_location=ARTIFACT_DIR.resolve().as_uri(),
        )
    mlflow.set_experiment(EXPERIMENT_NAME)


def load_data():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


def main():
    setup_mlflow()

    X_train, X_test, y_train, y_test = load_data()

    # --- class imbalance fix: weight the minority (default=1) class ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count

    hyperparams = {**BASE_HYPERPARAMS, "scale_pos_weight": scale_pos_weight}

    with mlflow.start_run(run_name="xgboost_credit_risk_model"):
        mlflow.log_params(hyperparams)
        mlflow.log_param("train_rows", len(X_train))
        mlflow.log_param("test_rows", len(X_test))
        mlflow.log_param("positive_rate_train", round(pos_count / len(y_train), 4))

        model = XGBClassifier(**hyperparams)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "pr_auc": average_precision_score(y_test, y_proba),
        }
        mlflow.log_metrics(metrics)

        # log_model signature differs across MLflow versions — artifact_path is the
        # stable arg name; if your version is very new it may also accept `name=`.
        mlflow.xgboost.log_model(model, name="credit_risk_model")

    # Save a plain pickle too — the MCP tools load this directly from disk,
    # independent of MLflow, so the server doesn't need MLflow installed at runtime.
    MODEL_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_OUT_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"scale_pos_weight used: {scale_pos_weight:.4f}")
    print("Test metrics:")
    for name, value in metrics.items():
        print(f"  {name}: {value:.4f}")


if __name__ == "__main__":
    main()