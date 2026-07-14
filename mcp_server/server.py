"""MCP server entrypoint: registers and serves financial reasoning tools over MCP."""

import sys
from pathlib import Path

# Lets `python mcp_server/server.py` resolve the mcp_server package regardless of
# the caller's working directory (the package isn't installed, just run in place).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.credit_score import get_credit_score as _get_credit_score
from mcp_server.tools.dti import calculate_dti as _calculate_dti
from mcp_server.tools.fraud_check import fraud_risk_check as _fraud_risk_check
from mcp_server.tools.policy_rag import policy_lookup as _policy_lookup

mcp = FastMCP("loan-underwriting-copilot")


@mcp.tool()
def get_credit_score(applicant_data: dict) -> dict:
    """Predict default probability and risk tier for a loan applicant."""
    return _get_credit_score(applicant_data)


@mcp.tool()
def calculate_dti(
    annual_income: float,
    existing_debt: float,
    requested_loan_amount: float,
    estimated_new_monthly_payment: float = None,
) -> dict:
    """Calculate an applicant's debt-to-income ratio against the standard 43% cutoff."""
    return _calculate_dti(
        annual_income, existing_debt, requested_loan_amount, estimated_new_monthly_payment
    )


@mcp.tool()
def fraud_risk_check(applicant_data: dict) -> dict:
    """Score fraud risk and explain the top SHAP-driven contributing factors."""
    return _fraud_risk_check(applicant_data)


@mcp.tool()
def policy_lookup(query: str, k: int = 3) -> list[str]:
    """Retrieve the top-k underwriting policy sections most relevant to a query."""
    return _policy_lookup(query, k)


if __name__ == "__main__":
    mcp.run(transport="stdio")
