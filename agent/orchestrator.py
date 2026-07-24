"""LangChain agent orchestrator: coordinates MCP tool calls to reach an underwriting decision."""

import asyncio
import json
import sys
import time
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.logger import log_decision, log_tool_call

load_dotenv()

SERVER_SCRIPT = Path(__file__).resolve().parent.parent / "mcp_server" / "server.py"

SYSTEM_PROMPT = """You are an underwriting copilot for a consumer lending team. You will
be given a JSON object describing a loan applicant. For every applicant, call tools in
exactly this order:

1. calculate_dti - assess debt-to-income affordability. Pass annual_income,
   existing_debt, and requested_loan_amount as top-level arguments.
2. get_credit_score - get the model's default probability and risk tier. This tool takes
   ONE argument named applicant_data, whose value is an object containing ALL of the
   applicant's fields. Do NOT pass the applicant's fields as top-level arguments — nest
   them inside applicant_data, e.g. {"applicant_data": {"age": ..., "annual_income": ...,
   "employment_years": ..., "existing_debt": ..., "requested_loan_amount": ...,
   "credit_history_length": ..., "num_late_payments_last_2y": ..., "dti_ratio": ...}}.
3. fraud_risk_check - get the fraud risk score and its top contributing factors. Like
   get_credit_score, this tool takes ONE argument named applicant_data nested the same way.
4. policy_lookup - query the underwriting policy for anything relevant to red flags you
   found in the previous steps. Formulate the query yourself based on what you observed
   (e.g. if fraud_risk_check surfaced late payments, look up what the policy says about
   late payments; if the DTI check failed, look up the DTI thresholds; always look up at
   least the credit risk tier rules and DTI thresholds so your decision is grounded).

After calling all four tools, produce a final decision of exactly one of "approve",
"deny", or "manual_review", consistent with the policy passages you retrieved. Write a
rationale that explicitly references the specific numbers and findings from each tool
call: the DTI ratio, the default probability and risk tier, the fraud risk score and its
top factors, and the policy passage(s) that justify the decision.

End your final response in exactly this format, with no text after it:

DECISION: <approve|deny|manual_review>
REASONING: <your written rationale, as a single paragraph>
"""


class _AuditCallbackHandler(BaseCallbackHandler):
    """Logs every tool call the agent makes (name, input, output, latency) to the audit DB."""

    def __init__(self, application_id: str):
        self.application_id = application_id
        self.audit_trail: list[dict] = []
        self._starts: dict[UUID, tuple[str, object, float]] = {}

    def on_tool_start(self, serialized, input_str, *, run_id, inputs=None, **kwargs):
        tool_name = serialized.get("name", "unknown_tool")
        tool_input = inputs if inputs is not None else input_str
        self._starts[run_id] = (tool_name, tool_input, time.monotonic())

    def on_tool_end(self, output, *, run_id, **kwargs):
        if run_id not in self._starts:
            return
        tool_name, tool_input, start_time = self._starts.pop(run_id)
        latency_ms = (time.monotonic() - start_time) * 1000
        tool_output = getattr(output, "content", output)

        log_tool_call(
            application_id=self.application_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            latency_ms=latency_ms,
        )
        self.audit_trail.append(
            {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "latency_ms": latency_ms,
            }
        )

    def on_tool_error(self, error, *, run_id, **kwargs):
        if run_id not in self._starts:
            return
        tool_name, tool_input, start_time = self._starts.pop(run_id)
        latency_ms = (time.monotonic() - start_time) * 1000
        log_tool_call(
            application_id=self.application_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=f"ERROR: {error}",
            latency_ms=latency_ms,
        )


def _parse_decision(final_text: str) -> tuple[str, str]:
    decision = "manual_review"
    reasoning = final_text.strip()

    for line in final_text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DECISION:"):
            value = stripped.split(":", 1)[1].strip().lower()
            if value in {"approve", "deny", "manual_review"}:
                decision = value

    if "REASONING:" in final_text:
        reasoning = final_text.split("REASONING:", 1)[1].strip()

    return decision, reasoning


async def _run_underwriting_async(applicant_data: dict) -> dict:
    application_id = str(applicant_data.get("applicant_id", "UNKNOWN"))

    client = MultiServerMCPClient(
        {
            "underwriting": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_SCRIPT)],
            }
        }
    )

    model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    audit_handler = _AuditCallbackHandler(application_id)

    # One subprocess for the whole run: spawning a fresh `server.py` process per tool
    # call re-imports torch/sentence-transformers/xgboost each time, which is slow
    # enough that the subprocess can die mid-import before it answers ("Connection
    # closed"). Keeping one session alive for all 4 calls avoids that entirely.
    async with client.session("underwriting") as session:
        tools = await load_mcp_tools(session)
        agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT)

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": json.dumps(applicant_data)}]},
            config={"callbacks": [audit_handler]},
        )

    final_message = result["messages"][-1]
    final_text = final_message.content if hasattr(final_message, "content") else str(final_message)

    decision, reasoning = _parse_decision(final_text)
    tools_called = [entry["tool_name"] for entry in audit_handler.audit_trail]

    log_decision(
        application_id=application_id,
        decision=decision,
        reasoning=reasoning,
        tools_called=tools_called,
    )

    return {
        "decision": decision,
        "reasoning": reasoning,
        "audit_trail": audit_handler.audit_trail,
    }


def run_underwriting(applicant_data: dict) -> dict:
    return asyncio.run(_run_underwriting_async(applicant_data))


if __name__ == "__main__":
    sample_applicant = {
        "applicant_id": "APP00745",
        "age": 34,
        "annual_income": 62000,
        "employment_years": 3.5,
        "existing_debt": 18000,
        "requested_loan_amount": 25000,
        "credit_history_length": 6,
        "num_late_payments_last_2y": 3,
        "dti_ratio": round(18000 / 62000, 3),
    }
    outcome = run_underwriting(sample_applicant)
    print(json.dumps(outcome, indent=2))
