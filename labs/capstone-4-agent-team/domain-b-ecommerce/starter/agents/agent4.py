"""
Communication Agent (Agent 4) — B2B Ecommerce Order Pipeline

Tools:
- draft_customer_update: Create customer-facing order status message
- generate_internal_alert: Create internal alert for ops team
- log_event: Log the communication event

YOUR TASK: Complete the TODO sections.
"""

import json
from datetime import datetime
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "draft_customer_update",
        "description": "Draft a customer-facing order status update message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "status": {"type": "string"},
                "details": {"type": "string"},
            },
            "required": ["order_id", "customer_name", "status"],
        },
    },
    {
        "name": "generate_internal_alert",
        "description": "Generate an internal alert for the operations team about exceptions or SLA issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "alert_type": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "message": {"type": "string"},
            },
            "required": ["order_id", "alert_type", "priority", "message"],
        },
    },
    {
        "name": "log_event",
        "description": "Log a communication or pipeline event for audit trail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "event_type": {"type": "string"},
                "details": {"type": "string"},
            },
            "required": ["order_id", "event_type"],
        },
    },
]


def draft_customer_update(order_id: str, customer_name: str, status: str, details: str = "") -> dict:
    """Draft customer update."""
    # TODO: Implement — build a professional customer-facing message
    pass


def generate_internal_alert(order_id: str, alert_type: str, priority: str, message: str) -> dict:
    """Generate internal ops alert."""
    # TODO: Implement — create structured internal alert
    pass


def log_event(order_id: str, event_type: str, details: str = "") -> dict:
    """Log event for audit."""
    # TODO: Implement — create timestamped log entry
    pass


TOOL_HANDLERS = {
    "draft_customer_update": lambda args: draft_customer_update(**args),
    "generate_internal_alert": lambda args: generate_internal_alert(**args),
    "log_event": lambda args: log_event(**args),
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


class CommunicationAgent(BaseAgent):
    name = "CommunicationAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Communication Agent for a B2B ecommerce pipeline.
Prepare customer updates, internal alerts, and log events.

You MUST:
1. draft_customer_update — send order status to customer
2. generate_internal_alert — notify ops team of any issues
3. log_event — record for audit trail"""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        return (
            f"Prepare communications for order {state.intake.order_id}:\n"
            f"Customer: {state.intake.customer_name}\n"
            f"SLA Status: {state.exception.sla_status}\n"
            f"Exceptions: {state.exception.exceptions_detected}\n"
            f"Carrier: {state.fulfillment.selected_carrier}\n"
            f"ETA: {state.fulfillment.estimated_delivery_date}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        # TODO: Implement ReAct loop
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
