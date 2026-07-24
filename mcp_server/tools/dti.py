"""MCP tool: rule-based debt-to-income ratio calculator."""

DTI_THRESHOLD = 0.43


def calculate_dti(
    annual_income: float,
    existing_debt: float,
    requested_loan_amount: float,
    estimated_new_monthly_payment: float | None = None,
) -> dict:
    if estimated_new_monthly_payment is None:
        # Rough 5-year, no-interest amortization — just enough for a ballpark ratio.
        estimated_new_monthly_payment = requested_loan_amount / 60

    monthly_income = annual_income / 12
    # existing_debt is a total balance, not a monthly payment; de-annualize it the
    # same way annual_income is, so both sides of the ratio are monthly figures.
    existing_monthly_debt = existing_debt / 12

    dti_ratio = (existing_monthly_debt + estimated_new_monthly_payment) / monthly_income

    return {
        "dti_ratio": round(dti_ratio, 3),
        "meets_threshold": dti_ratio <= DTI_THRESHOLD,
    }


if __name__ == "__main__":
    sample_result = calculate_dti(
        annual_income=62000,
        existing_debt=18000,
        requested_loan_amount=25000,
    )
    print(sample_result)
