"""MCP tool: heuristic and model-assisted fraud signal detection for applications."""

# Intentionally reuses credit_model.pkl rather than training a separate fraud model:
# one XGBoost model, read through a SHAP lens to explain which features drove an
# individual risk score, instead of a distinct fraud-specific classifier.

import shap

from .credit_score import FEATURE_COLUMNS, MODEL, _build_feature_row

_EXPLAINER = shap.TreeExplainer(MODEL)

_RANK_PHRASES = [
    "contributed most to this risk score",
    "was the second-largest contributor to this risk score",
    "was the third-largest contributor to this risk score",
]


def fraud_risk_check(applicant_data: dict) -> dict:
    row = _build_feature_row(applicant_data)
    risk_score = float(MODEL.predict_proba(row)[0, 1])

    shap_values = _EXPLAINER.shap_values(row)[0]
    ranked = sorted(zip(FEATURE_COLUMNS, shap_values), key=lambda pair: abs(pair[1]), reverse=True)

    top_factors = [
        f"{feature} {phrase}"
        for (feature, _), phrase in zip(ranked[:3], _RANK_PHRASES)
    ]

    return {"risk_score": risk_score, "top_factors": top_factors}


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
    print(fraud_risk_check(sample_applicant))
