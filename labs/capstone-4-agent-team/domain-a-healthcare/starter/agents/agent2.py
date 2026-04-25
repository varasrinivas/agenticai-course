"""
Clinical Criteria Agent (Agent 2) — Healthcare Pre-Auth Pipeline

Responsibilities:
- Look up clinical criteria for the requested procedure
- Match submitted diagnoses to required diagnoses
- Calculate a medical necessity score

Tools:
- lookup_clinical_criteria: Get criteria for a CPT code
- match_diagnosis_to_criteria: Compare submitted dx to required dx
- calculate_medical_necessity_score: Score clinical notes against criteria

YOUR TASK: Complete the TODO sections to build a working Clinical Criteria Agent.
"""

import json
import os
import re
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import CLINICAL_CRITERIA, PROVIDER_NETWORK, BENEFIT_PLANS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "lookup_clinical_criteria",
        "description": (
            "Look up the clinical criteria required for pre-authorization of a specific "
            "procedure. Returns required diagnoses, criteria checklist, medical necessity "
            "weights, and approval validity period."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code to look up",
                },
            },
            "required": ["cpt_code"],
        },
    },
    {
        "name": "match_diagnosis_to_criteria",
        "description": (
            "Match submitted diagnosis codes against the required diagnoses for a procedure. "
            "Returns match status, matched codes, unmatched codes, and descriptions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code",
                },
                "submitted_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ICD-10 diagnosis codes submitted",
                },
            },
            "required": ["cpt_code", "submitted_codes"],
        },
    },
    {
        "name": "calculate_medical_necessity_score",
        "description": (
            "Calculate a medical necessity score (0-100) based on clinical information "
            "extracted from the request. Uses weighted scoring against the procedure's "
            "clinical criteria. Score >= 80 supports approval; < 80 may need review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code",
                },
                "clinical_info": {
                    "type": "object",
                    "description": "Structured clinical data extracted by the Intake Agent",
                },
                "diagnosis_match": {
                    "type": "boolean",
                    "description": "Whether the diagnosis codes matched",
                },
            },
            "required": ["cpt_code", "clinical_info", "diagnosis_match"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def lookup_clinical_criteria(cpt_code: str) -> dict:
    """Look up clinical criteria for a CPT code."""
    # TODO: Implement this function
    # 1. Look up cpt_code in CLINICAL_CRITERIA
    # 2. If not found, return {"error": f"No criteria found for CPT code {cpt_code}"}
    # 3. Return the full criteria entry
    pass


def match_diagnosis_to_criteria(cpt_code: str, submitted_codes: list) -> dict:
    """Match submitted diagnosis codes against required codes."""
    # TODO: Implement this function
    # 1. Look up criteria for cpt_code
    # 2. Compare submitted_codes against criteria["required_diagnoses"]
    # 3. Return:
    #    - "match": bool (at least one match)
    #    - "matched_codes": list of matching codes
    #    - "unmatched_codes": list of non-matching submitted codes
    #    - "required_codes": full list of required codes
    #    - "details": dict of code -> description for matched codes
    pass


def calculate_medical_necessity_score(
    cpt_code: str, clinical_info: dict, diagnosis_match: bool
) -> dict:
    """Calculate medical necessity score from clinical data."""
    # TODO: Implement this function
    # 1. Look up criteria for cpt_code to get medical_necessity_weights
    # 2. Score each criterion based on clinical_info:
    #    For CPT 27447 (TKA):
    #      - conservative_treatment: full points if months >= 3
    #      - imaging_grade: full points if KL grade >= 3
    #      - functional_score: full points if WOMAC >= 39
    #      - bmi_compliance: full points if BMI < 40
    #      - diagnosis_match: full points if diagnosis_match is True
    #    For other CPTs, use similar logic based on available clinical_info
    # 3. Return:
    #    - "total_score": float (0-100)
    #    - "component_scores": dict of criterion -> score
    #    - "max_possible": 100
    #    - "recommendation_threshold": 80
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "lookup_clinical_criteria": lambda args: lookup_clinical_criteria(**args),
    "match_diagnosis_to_criteria": lambda args: match_diagnosis_to_criteria(**args),
    "calculate_medical_necessity_score": lambda args: calculate_medical_necessity_score(**args),
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
# Clinical Criteria Agent Class
# ---------------------------------------------------------------------------

class ClinicalCriteriaAgent(BaseAgent):
    """
    Agent 2: Looks up clinical criteria, matches diagnoses,
    and calculates medical necessity score.
    """

    name = "ClinicalCriteriaAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Clinical Criteria Agent in a healthcare pre-authorization pipeline.
You receive intake data from the Intake Agent and must evaluate clinical criteria.

You MUST:
1. FIRST look up clinical criteria for the CPT code using lookup_clinical_criteria
2. THEN match the submitted diagnosis codes using match_diagnosis_to_criteria
3. FINALLY calculate the medical necessity score using calculate_medical_necessity_score

Pass the clinical_info from the intake stage to calculate_medical_necessity_score.
Report your findings: criteria found, diagnosis match status, and the necessity score.
A score >= 80 supports approval. A score < 80 suggests the request needs additional review."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from intake results."""
        intake = state.intake
        return (
            f"Evaluate clinical criteria for request {intake.request_id}:\n\n"
            f"CPT Code: {intake.cpt_code}\n"
            f"Diagnosis Codes: {intake.diagnosis_codes}\n"
            f"Provider NPI: {intake.provider_npi}\n"
            f"Plan ID: {intake.plan_id}\n"
            f"Clinical Info Extracted: {json.dumps(intake.clinical_info_extracted, indent=2)}\n"
            f"Validation Status: {'PASSED' if intake.validation_passed else 'FAILED'}\n"
            f"Validation Errors: {intake.validation_errors}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Clinical Criteria Agent's ReAct loop.

        Args:
            state: Pipeline state with intake results populated.

        Returns:
            Updated pipeline state with criteria results.
        """
        # TODO: Implement the ReAct loop (same pattern as Agent 1)
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop: send to Claude, process tool calls, iterate
        # 4. Parse final response to update state.criteria
        # 5. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with criteria results."""
        # TODO: Parse result_text and populate state.criteria fields
        return state
