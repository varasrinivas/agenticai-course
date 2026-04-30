"""
Exception Monitor Agent (Agent 3) — B2B Ecommerce (Solution)
"""

import json
from datetime import datetime
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, SLA_RULES, SLA_VIOLATIONS_LOG

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {"name": "track_sla_status", "description": "Check SLA compliance.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "estimated_delivery": {"type": "string"}, "requested_delivery": {"type": "string"}, "sla_tier": {"type": "string"}}, "required": ["order_id", "estimated_delivery", "requested_delivery", "sla_tier"]}},
    {"name": "detect_exceptions", "description": "Scan for order exceptions.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "escalate_issue", "description": "Escalate critical exception.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "issue_type": {"type": "string"}, "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]}, "description": {"type": "string"}}, "required": ["order_id", "issue_type", "severity", "description"]}},
]


def track_sla_status(order_id, estimated_delivery, requested_delivery, sla_tier):
    sla = SLA_RULES.get(sla_tier, SLA_RULES["standard"])
    if estimated_delivery <= requested_delivery:
        return {"status": "on_track", "estimated": estimated_delivery, "requested": requested_delivery, "max_days": sla["max_days"]}
    else:
        return {"status": "at_risk", "estimated": estimated_delivery, "requested": requested_delivery, "days_late": 1, "penalty_pct": sla["penalty_pct"]}


def detect_exceptions(order_id):
    exceptions = []
    recent = [v for v in SLA_VIOLATIONS_LOG if v.get("order_id") == order_id]
    for v in recent:
        exceptions.append({"type": v["violation_type"], "details": v})
    # Check if order has known issues
    order = ORDERS.get(order_id, {})
    if order.get("requested_delivery", "9999") < datetime.now().strftime("%Y-%m-%d"):
        exceptions.append({"type": "past_due_delivery", "details": f"Requested delivery {order['requested_delivery']} is in the past"})
    severity = "critical" if len(exceptions) > 1 else "medium" if exceptions else "low"
    return {"exceptions": exceptions, "count": len(exceptions), "severity": severity}


def escalate_issue(order_id, issue_type, severity, description):
    ticket_id = f"ESC-{order_id[-4:]}-{datetime.now().strftime('%H%M%S')}"
    return {"escalated": True, "ticket_id": ticket_id, "order_id": order_id, "issue_type": issue_type, "severity": severity, "description": description, "timestamp": datetime.now().isoformat()}


TOOL_HANDLERS = {
    "track_sla_status": lambda args: track_sla_status(**args),
    "detect_exceptions": lambda args: detect_exceptions(**args),
    "escalate_issue": lambda args: escalate_issue(**args),
}


def execute_tool(tool_name, tool_input):
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(handler(tool_input), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


class ExceptionMonitorAgent(BaseAgent):
    name = "ExceptionMonitorAgent"
    tool_schemas = TOOL_SCHEMAS
    system_prompt = "You are the Exception Monitor. Track SLA, detect exceptions, escalate issues. Call all 3 tools."

    def execute_tool(self, tool_name, tool_input):
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state):
        return f"Monitor {state.intake.order_id}:\nETA: {state.fulfillment.estimated_delivery_date}\nRequested: {state.raw_order.get('requested_delivery')}\nSLA: {state.raw_order.get('sla_tier')}"

    def run(self, state):
        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": self.build_user_message(state)}]
        print(f"\n[ExceptionMonitorAgent] Starting...")
        for step in range(1, MAX_ITERATIONS + 1):
            try:
                response = client.messages.create(model=MODEL, max_tokens=4096, system=self.system_prompt, tools=self.tool_schemas, messages=messages)
            except Exception as e:
                state.halted = True; state.halt_reason = str(e); return state
            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            for b in response.content:
                if b.type == "text": print(f"  [THINK] {b.text[:150]}...")
                elif b.type == "tool_use": print(f"  [ACT] {b.name}")
            if response.stop_reason == "end_turn": break
            if tool_blocks:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": self.execute_tool(b.name, b.input)} for b in tool_blocks]})

        sla = track_sla_status(state.intake.order_id, state.fulfillment.estimated_delivery_date, state.raw_order.get("requested_delivery", ""), state.raw_order.get("sla_tier", "standard"))
        state.exception.sla_status = sla.get("status", "unknown")
        exc = detect_exceptions(state.intake.order_id)
        state.exception.exceptions_detected = [e.get("type", "") for e in exc.get("exceptions", [])]
        state.exception.escalation_needed = exc.get("severity") in ("high", "critical")
        state.agent_trace.append({"agent": self.name, "sla_status": state.exception.sla_status, "exceptions": len(state.exception.exceptions_detected)})
        return state

    def update_state(self, state, result_text):
        return state
