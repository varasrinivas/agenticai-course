"""
Exception Monitor Agent (Agent 3) — B2B Ecommerce Order Pipeline

Tools:
- track_sla_status: Check if order is on track to meet SLA
- detect_exceptions: Scan for exceptions (late, wrong item, damaged, etc.)
- escalate_issue: Escalate critical exceptions

Circuit breaker: trips when > 3 consecutive SLA violations detected.

YOUR TASK: Complete the TODO sections.
"""

import json
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, SLA_RULES, SLA_VIOLATIONS_LOG

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "track_sla_status",
        "description": "Check whether the order is on track to meet its SLA delivery commitment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "estimated_delivery": {"type": "string"},
                "requested_delivery": {"type": "string"},
                "sla_tier": {"type": "string"},
            },
            "required": ["order_id", "estimated_delivery", "requested_delivery", "sla_tier"],
        },
    },
    {
        "name": "detect_exceptions",
        "description": "Scan for order exceptions: SLA violations, inventory shortages, pricing disputes.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "escalate_issue",
        "description": "Escalate a critical exception to management. Used for SLA violations and customer-impacting issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "issue_type": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "description": {"type": "string"},
            },
            "required": ["order_id", "issue_type", "severity", "description"],
        },
    },
]


def track_sla_status(order_id: str, estimated_delivery: str, requested_delivery: str, sla_tier: str) -> dict:
    """Check SLA status."""
    # TODO: Implement
    # 1. Compare estimated_delivery to requested_delivery
    # 2. Check against SLA_RULES max_days
    # 3. Return {"status": "on_track"|"at_risk"|"violated", "days_margin": int}
    pass


def detect_exceptions(order_id: str) -> dict:
    """Detect order exceptions."""
    # TODO: Implement
    # 1. Check SLA_VIOLATIONS_LOG for this order or recent patterns
    # 2. Check if order has validation errors or inventory issues
    # 3. Return {"exceptions": [...], "severity": str}
    pass


def escalate_issue(order_id: str, issue_type: str, severity: str, description: str) -> dict:
    """Escalate a critical issue."""
    # TODO: Implement
    # 1. Create an escalation record
    # 2. Return {"escalated": True, "ticket_id": str, ...}
    pass


TOOL_HANDLERS = {
    "track_sla_status": lambda args: track_sla_status(**args),
    "detect_exceptions": lambda args: detect_exceptions(**args),
    "escalate_issue": lambda args: escalate_issue(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


class ExceptionMonitorAgent(BaseAgent):
    name = "ExceptionMonitorAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Exception Monitor Agent for a B2B ecommerce pipeline.
Monitor order SLA compliance and detect/escalate exceptions.

You MUST:
1. track_sla_status — check delivery timeline
2. detect_exceptions — scan for problems
3. escalate_issue — escalate critical issues

Report all findings. Flag consecutive SLA violations for circuit breaker."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        return (
            f"Monitor order {state.intake.order_id}:\n"
            f"Estimated Delivery: {state.fulfillment.estimated_delivery_date}\n"
            f"Requested Delivery: {state.raw_order.get('requested_delivery')}\n"
            f"SLA Tier: {state.raw_order.get('sla_tier')}\n"
            f"Split Shipment: {state.fulfillment.split_shipment_needed}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        # TODO: Implement ReAct loop
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
