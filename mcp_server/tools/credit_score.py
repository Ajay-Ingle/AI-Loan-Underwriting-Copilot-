"""MCP tool: XGBoost-backed credit-risk scoring for loan applicants."""

import pickle
from pathlib import Path

import pandas as pd

_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "credit_model.pkl"

with open(_MODEL_PATH, "rb") as _f:
    MODEL = pickle.load(_f)

FEATURE_COLUMNS = list(MODEL.feature_names_in_)


def _build_feature_row(applicant_data: dict) -> pd.DataFrame:
    missing = [field for field in FEATURE_COLUMNS if field not in applicant_data]
    if missing:
        raise ValueError(f"Missing required applicant fields: {', '.join(missing)}")
    return pd.DataFrame([{col: applicant_data[col] for col in FEATURE_COLUMNS}])


def get_credit_score(applicant_data: dict) -> dict:
    row = _build_feature_row(applicant_data)
    probability = float(MODEL.predict_proba(row)[0, 1])

    if probability < 0.3:
        risk_tier = "low"
    elif probability < 0.6:
        risk_tier = "medium"
    else:
        risk_tier = "high"

    return {"default_probability": probability, "risk_tier": risk_tier}


if __name__ == "__main__":
    sample_applicant = {
        "age": 34,
        "annual_income": 62000,
        "employment_years": 3.5,
        "existing_debt": 18000,
        "requested_loan_amount": 25000,
        "credit_history_length": 6,
        "num_late_payments_last_2y": 3,
        "dti_ratio": round(18000 / 62000, 3),
    }
    print(get_credit_score(sample_applicant))
