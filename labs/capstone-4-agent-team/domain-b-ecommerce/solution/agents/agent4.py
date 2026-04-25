"""
Communication Agent (Agent 4) — B2B Ecommerce (Solution)
"""

import json
from datetime import datetime
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {"name": "draft_customer_update", "description": "Draft customer status message.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "customer_name": {"type": "string"}, "status": {"type": "string"}, "details": {"type": "string"}}, "required": ["order_id", "customer_name", "status"]}},
    {"name": "generate_internal_alert", "description": "Generate internal ops alert.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "alert_type": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}, "message": {"type": "string"}}, "required": ["order_id", "alert_type", "priority", "message"]}},
    {"name": "log_event", "description": "Log event for audit.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "event_type": {"type": "string"}, "details": {"type": "string"}}, "required": ["order_id", "event_type"]}},
]


def draft_customer_update(order_id, customer_name, status, details=""):
    msg = f"Dear {customer_name},\n\nOrder {order_id} status: {status}.\n"
    if details:
        msg += f"\n{details}\n"
    msg += "\nThank you for your business.\n— Order Management Team"
    return {"message": msg, "order_id": order_id, "status": status}


def generate_internal_alert(order_id, alert_type, priority, message):
    return {"alert_id": f"ALT-{order_id[-4:]}", "order_id": order_id, "type": alert_type, "priority": priority, "message": message, "timestamp": datetime.now().isoformat()}


def log_event(order_id, event_type, details=""):
    return {"logged": True, "entry": {"order_id": order_id, "event_type": event_type, "details": details, "timestamp": datetime.now().isoformat()}}


TOOL_HANDLERS = {
    "draft_customer_update": lambda args: draft_customer_update(**args),
    "generate_internal_alert": lambda args: generate_internal_alert(**args),
    "log_event": lambda args: log_event(**args),
}


def execute_tool(tool_name, tool_input):
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(handler(tool_input), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


class CommunicationAgent(BaseAgent):
    name = "CommunicationAgent"
    tool_schemas = TOOL_SCHEMAS
    system_prompt = "You are the Communication Agent. Draft customer updates, generate internal alerts, and log events."

    def execute_tool(self, tool_name, tool_input):
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state):
        return f"Prepare comms for {state.intake.order_id}:\nCustomer: {state.intake.customer_name}\nSLA: {state.exception.sla_status}\nExceptions: {state.exception.exceptions_detected}\nCarrier: {state.fulfillment.selected_carrier}"

    def run(self, state):
        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": self.build_user_message(state)}]
        print(f"\n[CommunicationAgent] Starting...")
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

        update = draft_customer_update(state.intake.order_id, state.intake.customer_name, state.exception.sla_status or "processing")
        state.communication.customer_update_sent = True
        state.communication.customer_message = update.get("message", "")
        if state.exception.escalation_needed:
            alert = generate_internal_alert(state.intake.order_id, "sla_risk", "high", f"Exceptions: {state.exception.exceptions_detected}")
            state.communication.internal_alert_sent = True
            state.communication.internal_alert = alert.get("message", "")
        log = log_event(state.intake.order_id, "pipeline_complete")
        state.communication.event_logged = True
        state.communication.log_entry = log.get("entry", {})
        state.agent_trace.append({"agent": self.name, "customer_updated": True, "alert_sent": state.communication.internal_alert_sent})
        return state

    def update_state(self, state, result_text):
        return state
