"""
Intake Agent (Agent 1) — Healthcare Pre-Auth Pipeline

Responsibilities:
- Validate the incoming pre-authorization request
- Extract structured clinical information from notes
- Check patient eligibility

Tools:
- validate_request: Check request completeness and field validity
- extract_clinical_info: Parse clinical notes for key data points
- check_eligibility: Verify patient eligibility and plan status

YOUR TASK: Complete the TODO sections to build a working Intake Agent.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import PREAUTH_REQUESTS, CLINICAL_CRITERIA, ELIGIBILITY, PROVIDER_NETWORK

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
        "name": "validate_request",
        "description": (
            "Validate a pre-authorization request for completeness and correctness. "
            "Checks that all required fields are present, CPT code exists in the criteria "
            "database, diagnosis codes are non-empty, and provider NPI is recognized. "
            "Returns validation status and any errors found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "The pre-authorization request ID to validate",
                },
            },
            "required": ["request_id"],
        },
    },
    {
        "name": "extract_clinical_info",
        "description": (
            "Extract structured clinical information from the free-text clinical notes "
            "in a pre-authorization request. Parses out key data points like BMI, WOMAC score, "
            "imaging grades, treatment history, and symptom duration."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "The pre-authorization request ID",
                },
            },
            "required": ["request_id"],
        },
    },
    {
        "name": "check_eligibility",
        "description": (
            "Check patient eligibility status. Verifies the patient is currently eligible "
            "for benefits under their plan and that the plan is active."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The patient ID to check eligibility for",
                },
            },
            "required": ["patient_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def validate_request(request_id: str) -> dict:
    """Validate a pre-auth request for completeness."""
    # TODO: Implement this function
    # 1. Look up request_id in PREAUTH_REQUESTS
    # 2. If not found, return {"valid": False, "errors": ["Request not found"]}
    # 3. Check required fields: cpt_code, diagnosis_codes, provider_npi, patient_id, plan_id
    # 4. Verify cpt_code exists in CLINICAL_CRITERIA
    # 5. Verify diagnosis_codes is non-empty
    # 6. Verify provider_npi exists in PROVIDER_NETWORK
    # 7. Return {"valid": True/False, "errors": [...], "request": {...}}
    pass


def extract_clinical_info(request_id: str) -> dict:
    """Extract structured clinical info from free-text notes."""
    # TODO: Implement this function
    # 1. Look up request_id in PREAUTH_REQUESTS
    # 2. Parse the clinical_notes string for key data points
    #    Use simple keyword matching (not NLP) to find:
    #    - bmi: float or None (look for "BMI" followed by a number)
    #    - womac_score: int or None (look for "WOMAC" followed by a number)
    #    - kl_grade: int or None (look for "Kellgren-Lawrence grade" or "KL grade")
    #    - pt_sessions: int or None (look for "PT" + number + "sessions")
    #    - conservative_treatment_months: int or None
    #    - steroid_injections: int or None
    #    - urgency_indicators: list of strings (e.g., "weight loss", "dysphagia")
    # 3. Return the structured dict
    pass


def check_eligibility(patient_id: str) -> dict:
    """Check patient eligibility."""
    # TODO: Implement this function
    # 1. Look up patient_id in ELIGIBILITY
    # 2. If not found, return {"eligible": False, "reason": "Patient not found"}
    # 3. Return the eligibility record
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "validate_request": lambda args: validate_request(**args),
    "extract_clinical_info": lambda args: extract_clinical_info(**args),
    "check_eligibility": lambda args: check_eligibility(**args),
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
# Intake Agent Class
# ---------------------------------------------------------------------------

class IntakeAgent(BaseAgent):
    """
    Agent 1: Validates incoming requests, extracts clinical info,
    and checks patient eligibility.
    """

    name = "IntakeAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Intake Agent in a healthcare pre-authorization pipeline.
Your job is to validate incoming requests, extract structured clinical data, and verify eligibility.

You MUST:
1. FIRST validate the request using validate_request
2. THEN extract clinical information using extract_clinical_info
3. FINALLY check eligibility using check_eligibility

After calling all 3 tools, summarize your findings in a structured format:
- Validation: PASS or FAIL (with reasons)
- Clinical Info: key data points extracted
- Eligibility: CONFIRMED or DENIED

If validation fails, note the specific errors. The downstream agents need accurate data."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build the user message from the raw request."""
        req = state.raw_request
        return (
            f"Process intake for pre-authorization request {req.get('request_id', 'UNKNOWN')}:\n\n"
            f"Patient: {req.get('patient_name', 'N/A')} (ID: {req.get('patient_id', 'N/A')})\n"
            f"Plan: {req.get('plan_id', 'N/A')}\n"
            f"Provider: {req.get('provider_npi', 'N/A')}\n"
            f"Facility: {req.get('facility_id', 'N/A')}\n"
            f"CPT Code: {req.get('cpt_code', 'N/A')}\n"
            f"Diagnosis Codes: {req.get('diagnosis_codes', [])}\n"
            f"Clinical Notes: {req.get('clinical_notes', 'N/A')}\n"
            f"Urgency: {req.get('urgency', 'routine')}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Intake Agent's ReAct loop.

        Args:
            state: The current pipeline state.

        Returns:
            Updated pipeline state with intake results.
        """
        # TODO: Implement the ReAct loop for the Intake Agent
        # 1. Create an Anthropic client
        # 2. Build the initial user message using self.build_user_message(state)
        # 3. Loop up to MAX_ITERATIONS:
        #    a. Call client.messages.create() with model, system prompt, tools, messages
        #    b. Process response content blocks (text and tool_use)
        #    c. If stop_reason == "end_turn", break
        #    d. If stop_reason == "tool_use", execute tools and continue
        # 4. Parse the agent's final response to update state.intake
        # 5. Return the updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with intake results."""
        # TODO: Parse result_text and populate state.intake fields
        # This is called by the coordinator after run() completes
        return state
