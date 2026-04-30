"""
Communication Agent (Agent 4) — Healthcare Pre-Auth Pipeline

Responsibilities:
- Draft the patient notification letter
- Format the letter according to determination type
- Log the communication event

Tools:
- draft_notification: Create the notification text based on the determination
- format_letter: Apply the correct letter template
- log_communication: Record the communication in the audit log

YOUR TASK: Complete the TODO sections to build a working Communication Agent.
"""

import json
import os
from datetime import datetime
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import LETTER_TEMPLATES, PREAUTH_REQUESTS, PROVIDER_NETWORK, CLINICAL_CRITERIA

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "draft_notification",
        "description": (
            "Draft the patient notification content based on the pre-authorization "
            "determination. Includes the decision, reason, conditions, and next steps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The request ID"},
                "determination": {
                    "type": "string",
                    "enum": ["APPROVED", "DENIED", "PENDED"],
                    "description": "The determination decision",
                },
                "reason": {"type": "string", "description": "Justification for the decision"},
                "conditions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of conditions or next steps",
                },
            },
            "required": ["request_id", "determination", "reason"],
        },
    },
    {
        "name": "format_letter",
        "description": (
            "Format the notification into the official letter template. "
            "Uses the appropriate template (approval, denial, or pended) "
            "and fills in patient, provider, and facility details."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The request ID"},
                "template_type": {
                    "type": "string",
                    "enum": ["approval", "denial", "pended"],
                    "description": "Which letter template to use",
                },
                "notification_content": {
                    "type": "string",
                    "description": "The drafted notification content",
                },
            },
            "required": ["request_id", "template_type"],
        },
    },
    {
        "name": "log_communication",
        "description": (
            "Log the communication event for audit purposes. Records "
            "the letter sent, timestamp, recipient, and channel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The request ID"},
                "letter_type": {"type": "string", "description": "Type of letter sent"},
                "recipient": {"type": "string", "description": "Patient name"},
                "channel": {
                    "type": "string",
                    "enum": ["mail", "email", "portal"],
                    "description": "Communication channel used",
                },
            },
            "required": ["request_id", "letter_type", "recipient"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def draft_notification(
    request_id: str,
    determination: str,
    reason: str,
    conditions: list[str] | None = None,
) -> dict:
    """Draft the notification content."""
    # TODO: Implement this function
    # 1. Look up the request in PREAUTH_REQUESTS for patient details
    # 2. Build notification content including:
    #    - Patient name
    #    - Request ID
    #    - Determination (APPROVED/DENIED/PENDED)
    #    - Reason
    #    - Conditions (if any)
    #    - Next steps based on determination type
    # 3. Return {"content": str, "determination": str, "request_id": str}
    pass


def format_letter(
    request_id: str,
    template_type: str,
    notification_content: str = "",
) -> dict:
    """Format notification into an official letter template."""
    # TODO: Implement this function
    # 1. Look up the request for patient/provider details
    # 2. Look up the template in LETTER_TEMPLATES
    # 3. Fill in template variables (patient_name, request_id, etc.)
    # 4. Return {"letter_text": str, "template_used": str}
    pass


def log_communication(
    request_id: str,
    letter_type: str,
    recipient: str,
    channel: str = "mail",
) -> dict:
    """Log the communication event."""
    # TODO: Implement this function
    # 1. Create a log entry with timestamp, request_id, letter_type, recipient, channel
    # 2. Return the log entry dict
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "draft_notification": lambda args: draft_notification(**args),
    "format_letter": lambda args: format_letter(**args),
    "log_communication": lambda args: log_communication(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# ---------------------------------------------------------------------------
# Communication Agent Class
# ---------------------------------------------------------------------------

class CommunicationAgent(BaseAgent):
    """
    Agent 4: Drafts notifications, formats letters,
    and logs communication events.
    """

    name = "CommunicationAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Communication Agent in a healthcare pre-authorization pipeline.
You receive the final determination and must prepare and log patient communications.

You MUST:
1. FIRST draft the notification content using draft_notification
2. THEN format it into an official letter using format_letter
3. FINALLY log the communication event using log_communication

Use the correct template type: "approval" for APPROVED, "denial" for DENIED, "pended" for PENDED.
Ensure all patient and provider details are accurate in the letter."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from decision results."""
        decision = state.decision
        intake = state.intake
        return (
            f"Prepare communications for request {intake.request_id}:\n\n"
            f"Patient: {intake.patient_name}\n"
            f"Determination: {decision.determination}\n"
            f"Reason: {decision.reason}\n"
            f"Conditions: {decision.conditions}\n"
            f"HITL Triggered: {decision.hitl_triggered}\n"
            f"HITL Decision: {decision.hitl_decision}\n"
            f"Approval Validity: {decision.approval_validity_days} days"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Communication Agent's ReAct loop.

        Args:
            state: Pipeline state with decision results populated.

        Returns:
            Updated pipeline state with communication results.
        """
        # TODO: Implement the ReAct loop (same pattern as prior agents)
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop
        # 4. Parse final response to update state.communication
        # 5. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with communication results."""
        # TODO: Parse result_text and populate state.communication fields
        return state
