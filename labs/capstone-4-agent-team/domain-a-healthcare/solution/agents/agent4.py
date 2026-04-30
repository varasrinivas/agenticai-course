"""
Communication Agent (Agent 4) — Healthcare Pre-Auth Pipeline (Solution)

Fully implemented: drafts notifications, formats letters, logs communication events.
"""

import json
import os
from datetime import datetime
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import LETTER_TEMPLATES, PREAUTH_REQUESTS, PROVIDER_NETWORK, CLINICAL_CRITERIA

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "draft_notification",
        "description": "Draft patient notification content based on the determination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "determination": {"type": "string", "enum": ["APPROVED", "DENIED", "PENDED"]},
                "reason": {"type": "string"},
                "conditions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["request_id", "determination", "reason"],
        },
    },
    {
        "name": "format_letter",
        "description": "Format notification into official letter template.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "template_type": {"type": "string", "enum": ["approval", "denial", "pended"]},
                "notification_content": {"type": "string"},
            },
            "required": ["request_id", "template_type"],
        },
    },
    {
        "name": "log_communication",
        "description": "Log the communication event for audit purposes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "letter_type": {"type": "string"},
                "recipient": {"type": "string"},
                "channel": {"type": "string", "enum": ["mail", "email", "portal"]},
            },
            "required": ["request_id", "letter_type", "recipient"],
        },
    },
]


def draft_notification(request_id: str, determination: str, reason: str, conditions: list[str] | None = None) -> dict:
    req = PREAUTH_REQUESTS.get(request_id, {})
    patient = req.get("patient_name", "Patient")
    cpt = req.get("cpt_code", "")
    criteria = CLINICAL_CRITERIA.get(cpt, {})
    procedure = criteria.get("procedure_name", cpt)

    cond_text = ""
    if conditions:
        cond_text = "\n".join(f"  - {c}" for c in conditions)

    content = (
        f"Notification for {patient} — Request {request_id}\n"
        f"Procedure: {procedure}\n"
        f"Determination: {determination}\n"
        f"Reason: {reason}\n"
    )
    if cond_text:
        content += f"Conditions:\n{cond_text}\n"

    return {"content": content, "determination": determination, "request_id": request_id}


def format_letter(request_id: str, template_type: str, notification_content: str = "") -> dict:
    req = PREAUTH_REQUESTS.get(request_id, {})
    cpt = req.get("cpt_code", "")
    criteria = CLINICAL_CRITERIA.get(cpt, {})
    provider = PROVIDER_NETWORK.get(req.get("provider_npi", ""), {})

    template = LETTER_TEMPLATES.get(template_type, "No template found for {template_type}")

    try:
        letter = template.format(
            patient_name=req.get("patient_name", "Patient"),
            request_id=request_id,
            procedure_name=criteria.get("procedure_name", cpt),
            provider_name=provider.get("name", "Provider"),
            facility_name=req.get("facility_id", "Facility"),
            validity_days=criteria.get("approval_validity_days", 0),
            decision_date=datetime.now().strftime("%Y-%m-%d"),
            conditions=notification_content or "None",
            reason=notification_content or "See determination letter",
        )
    except KeyError as e:
        letter = f"Template formatting error: missing key {e}"

    return {"letter_text": letter, "template_used": template_type}


def log_communication(request_id: str, letter_type: str, recipient: str, channel: str = "mail") -> dict:
    entry = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "letter_type": letter_type,
        "recipient": recipient,
        "channel": channel,
        "status": "sent",
    }
    return {"logged": True, "entry": entry}


TOOL_HANDLERS = {
    "draft_notification": lambda args: draft_notification(**args),
    "format_letter": lambda args: format_letter(**args),
    "log_communication": lambda args: log_communication(**args),
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

    system_prompt = """You are the Communication Agent in a healthcare pre-authorization pipeline.
You receive the final determination and must prepare and log patient communications.

You MUST:
1. FIRST draft notification content using draft_notification
2. THEN format it into an official letter using format_letter
3. FINALLY log the communication event using log_communication

Use the correct template: "approval" for APPROVED, "denial" for DENIED, "pended" for PENDED."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        decision = state.decision
        intake = state.intake
        return (
            f"Prepare communications for request {intake.request_id}:\n\n"
            f"Patient: {intake.patient_name}\n"
            f"Determination: {decision.determination}\n"
            f"Reason: {decision.reason}\n"
            f"Conditions: {decision.conditions}\n"
            f"Approval Validity: {decision.approval_validity_days} days"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[CommunicationAgent] Starting ReAct loop...")
        print(f"{'~'*60}")

        for step in range(1, MAX_ITERATIONS + 1):
            try:
                response = client.messages.create(
                    model=MODEL, max_tokens=4096,
                    system=self.system_prompt, tools=self.tool_schemas,
                    messages=messages,
                )
            except Exception as e:
                print(f"  [ERROR] API call failed: {e}")
                state.halted = True
                state.halt_reason = f"CommunicationAgent API error: {e}"
                return state

            tool_use_blocks = []
            for block in response.content:
                if block.type == "text":
                    print(f"  [THINK] Step {step}: {block.text[:200]}...")
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)
                    print(f"  [ACT] Step {step}: {block.name}({json.dumps(block.input)[:150]})")

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use" and tool_use_blocks:
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tb in tool_use_blocks:
                    result = self.execute_tool(tb.name, tb.input)
                    print(f"  [OBSERVE] {tb.name} -> {result[:200]}...")
                    tool_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": result})
                messages.append({"role": "user", "content": tool_results})

        # --- Populate state directly ---
        det = state.decision.determination
        template_type = {"APPROVED": "approval", "DENIED": "denial", "PENDED": "pended"}.get(det, "pended")

        notif = draft_notification(
            request_id=state.intake.request_id,
            determination=det,
            reason=state.decision.reason,
            conditions=state.decision.conditions,
        )
        state.communication.notification_drafted = True

        letter = format_letter(
            request_id=state.intake.request_id,
            template_type=template_type,
            notification_content=notif.get("content", ""),
        )
        state.communication.letter_text = letter.get("letter_text", "")
        state.communication.letter_format = template_type

        log = log_communication(
            request_id=state.intake.request_id,
            letter_type=template_type,
            recipient=state.intake.patient_name,
            channel="mail",
        )
        state.communication.communication_logged = log.get("logged", False)
        state.communication.log_entry = log.get("entry", {})

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": datetime.now().isoformat(),
            "letter_format": template_type,
            "communication_logged": state.communication.communication_logged,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
