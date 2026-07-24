"""Unit tests for MCP tool functions, isolated from the trained model file and GROQ_API_KEY."""

import importlib
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

FEATURE_NAMES = [
    "age",
    "annual_income",
    "employment_years",
    "existing_debt",
    "requested_loan_amount",
    "credit_history_length",
    "num_late_payments_last_2y",
    "dti_ratio",
]


class _FakeModel:
    """Stands in for the real XGBClassifier so tests don't need the (gitignored,
    not present in CI) trained model pickle on disk."""

    feature_names_in_ = FEATURE_NAMES

    def predict_proba(self, X):
        return np.array([[0.35, 0.65]])


@pytest.fixture
def credit_score_module():
    with patch("pickle.load", return_value=_FakeModel()), patch("builtins.open", MagicMock()):
        import mcp_server.tools.credit_score as credit_score

        importlib.reload(credit_score)
    return credit_score


def test_calculate_dti_returns_valid_dict_for_known_input():
    from mcp_server.tools.dti import calculate_dti

    result = calculate_dti(
        annual_income=62000,
        existing_debt=18000,
        requested_loan_amount=25000,
    )

    assert set(result.keys()) == {"dti_ratio", "meets_threshold"}
    assert result["dti_ratio"] == pytest.approx(0.371, abs=0.001)
    assert result["meets_threshold"] is True


def test_get_credit_score_returns_probability_between_0_and_1(credit_score_module):
    sample_applicant = {name: 1 for name in FEATURE_NAMES}

    result = credit_score_module.get_credit_score(sample_applicant)

    assert "default_probability" in result
    assert "risk_tier" in result
    assert 0.0 <= result["default_probability"] <= 1.0
    assert result["risk_tier"] in {"low", "medium", "high"}


def test_policy_lookup_returns_at_least_one_result():
    from mcp_server.tools.policy_rag import policy_lookup

    results = policy_lookup("what is the maximum DTI ratio", k=3)

    assert isinstance(results, list)
    assert len(results) >= 1
