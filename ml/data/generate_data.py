import numpy as np
import pandas as pd

np.random.seed(42)
N = 2000

df = pd.DataFrame({
    "applicant_id": [f"APP{i:05d}" for i in range(N)],
    "age": np.random.randint(21, 65, N),
    "annual_income": np.random.lognormal(mean=11.2, sigma=0.5, size=N).round(0),
    "employment_years": np.random.gamma(2, 2, N).round(1).clip(0, 40),
    "existing_debt": np.random.lognormal(mean=9.5, sigma=0.8, size=N).round(0),
    "requested_loan_amount": np.random.lognormal(mean=10.5, sigma=0.6, size=N).round(0),
    "credit_history_length": np.random.randint(0, 25, N),
    "num_late_payments_last_2y": np.random.poisson(0.8, N),
})

df["dti_ratio"] = (df["existing_debt"] / df["annual_income"]).round(3)

risk_score = (
    0.35 * (df["dti_ratio"] > 0.4).astype(int) +
    0.25 * (df["num_late_payments_last_2y"] > 2).astype(int) +
    0.20 * (df["credit_history_length"] < 3).astype(int) +
    0.20 * (df["employment_years"] < 1).astype(int)
)
df["default"] = (np.random.rand(N) < risk_score.clip(0.02, 0.9)).astype(int)

df.to_csv("ml/data/applicants.csv", index=False)
print(df["default"].value_counts(normalize=True))
print(df.head())
