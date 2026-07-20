"""FastAPI application entrypoint: serves loan underwriting endpoints."""

import json
import sqlite3
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.orchestrator import run_underwriting
from audit.logger import DB_PATH

app = FastAPI(title="AI Loan Underwriting Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApplicantRequest(BaseModel):
    applicant_id: str
    age: int
    annual_income: float
    employment_years: float
    existing_debt: float
    requested_loan_amount: float
    credit_history_length: int
    num_late_payments_last_2y: int
    dti_ratio: float


def _safe_json_loads(value: str):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/underwrite")
def underwrite(applicant: ApplicantRequest):
    try:
        return run_underwriting(applicant.model_dump())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Underwriting agent failed to process the application.",
        ) from exc


@app.get("/audit/{application_id}")
def get_audit_trail(application_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        tool_call_rows = conn.execute(
            "SELECT id, timestamp, tool_name, tool_input, tool_output, latency_ms "
            "FROM tool_calls WHERE application_id = ? ORDER BY id",
            (application_id,),
        ).fetchall()
        decision_rows = conn.execute(
            "SELECT id, timestamp, decision, reasoning, tools_called "
            "FROM decisions WHERE application_id = ? ORDER BY id",
            (application_id,),
        ).fetchall()
    finally:
        conn.close()

    if not tool_call_rows and not decision_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No audit records found for application_id '{application_id}'.",
        )

    return {
        "application_id": application_id,
        "tool_calls": [
            {
                **dict(row),
                "tool_input": _safe_json_loads(row["tool_input"]),
                "tool_output": _safe_json_loads(row["tool_output"]),
            }
            for row in tool_call_rows
        ],
        "decisions": [
            {**dict(row), "tools_called": _safe_json_loads(row["tools_called"])}
            for row in decision_rows
        ],
    }
