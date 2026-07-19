"""Audit logger: persists decision rationale, tool calls, and SHAP explanations for compliance."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "audit_log.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            application_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            tool_input TEXT NOT NULL,
            tool_output TEXT NOT NULL,
            latency_ms REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            application_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            tools_called TEXT NOT NULL
        )
        """
    )
    return conn


def log_tool_call(
    application_id: str,
    tool_name: str,
    tool_input: dict | str,
    tool_output: dict | str,
    latency_ms: float,
) -> None:
    tool_input_json = tool_input if isinstance(tool_input, str) else json.dumps(tool_input)
    tool_output_json = tool_output if isinstance(tool_output, str) else json.dumps(tool_output)

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tool_calls
                (timestamp, application_id, tool_name, tool_input, tool_output, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                application_id,
                tool_name,
                tool_input_json,
                tool_output_json,
                latency_ms,
            ),
        )


def log_decision(
    application_id: str,
    decision: str,
    reasoning: str,
    tools_called: list[str],
) -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO decisions
                (timestamp, application_id, decision, reasoning, tools_called)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                application_id,
                decision,
                reasoning,
                json.dumps(tools_called),
            ),
        )
