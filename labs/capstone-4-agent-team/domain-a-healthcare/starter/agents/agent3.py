"""
Decision Agent (Agent 3) — Healthcare Pre-Auth Pipeline

Responsibilities:
- Apply decision rules based on criteria results
- Generate a determination (APPROVED / DENIED / PENDED)
- Route for human review when confidence < 80%

Tools:
- apply_decision_rules: Evaluate all criteria and produce a preliminary decision
- generate_determination: Create the formal determination with justification
- route_for_review: Route low-confidence decisions for human review (HITL gate)

YOUR TASK: Complete the TODO sections. This agent includes the HITL gate.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import CLINICAL_CRITERIA, BENEFIT_PLANS, PROVIDER_NETWORK

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10
HITL_CONFIDENCE_THRESHOLD = 80.0  # Trigger HITL when confidence < this value

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "apply_decision_rules",
        "description": (
            "Apply pre-authorization decision rules based on clinical criteria results, "
            "network status, and benefit coverage. Returns a preliminary decision with "
            "confidence score. Rules check: diagnosis match, network coverage, benefit "
            "exclusions, and medical necessity score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {"type": "string", "description": "CPT procedure code"},
                "diagnosis_match": {"type": "boolean", "description": "Whether diagnoses matched"},
                "medical_necessity_score": {"type": "number", "description": "Score from 0-100"},
                "network_status": {
                    "type": "string",
                    "enum": ["in_network", "out_of_network", "not_covered", "unknown"],
                    "description": "Provider/facility network status",
                },
                "benefit_covered": {"type": "boolean", "description": "Whether procedure category is covered"},
                "plan_type": {"type": "string", "description": "HMO, PPO, etc."},
            },
            "required": ["cpt_code", "diagnosis_match", "medical_necessity_score", "network_status", "benefit_covered", "plan_type"],
        },
    },
    {
        "name": "generate_determination",
        "description": (
            "Generate a formal pre-authorization determination with justification. "
            "Takes the preliminary decision and produces the official determination "
            "record with reasons, conditions, and validity period."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "preliminary_decision": {
                    "type": "string",
                    "enum": ["APPROVED", "DENIED", "PENDED"],
                    "description": "The preliminary decision from apply_decision_rules",
                },
                "confidence": {"type": "number", "description": "Confidence score 0-100"},
                "reason": {"type": "string", "description": "Justification for the decision"},
                "cpt_code": {"type": "string", "description": "CPT code for validity lookup"},
            },
            "required": ["preliminary_decision", "confidence", "reason", "cpt_code"],
        },
    },
    {
        "name": "route_for_review",
        "description": (
            "Route a decision for human review (HITL gate). Called when the confidence "
            "score is below the threshold. Pauses the pipeline and presents the case "
            "summary to a human reviewer for approval or override."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The request ID"},
                "preliminary_decision": {"type": "string", "description": "The preliminary decision"},
                "confidence": {"type": "number", "description": "The confidence score"},
                "reason": {"type": "string", "description": "Reason for the decision"},
                "review_context": {"type": "string", "description": "Additional context for the reviewer"},
            },
            "required": ["request_id", "preliminary_decision", "confidence", "reason"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def apply_decision_rules(
    cpt_code: str,
    diagnosis_match: bool,
    medical_necessity_score: float,
    network_status: str,
    benefit_covered: bool,
    plan_type: str,
) -> dict:
    """Apply decision rules and return preliminary decision with confidence."""
    # TODO: Implement this function
    # Decision logic:
    # 1. If benefit not covered -> DENIED, confidence=95
    # 2. If network_status == "not_covered" (HMO out-of-network) -> DENIED, confidence=95
    # 3. If diagnosis_match is False -> PENDED, confidence=70
    # 4. If medical_necessity_score >= 80 and network in-network -> APPROVED, confidence=medical_necessity_score
    # 5. If medical_necessity_score >= 80 and out-of-network (PPO) -> APPROVED with OON notice, confidence=medical_necessity_score-10
    # 6. If medical_necessity_score >= 60 and < 80 -> PENDED for peer review, confidence=medical_necessity_score
    # 7. If medical_necessity_score < 60 -> DENIED, confidence=90-medical_necessity_score
    #
    # Return: {"decision": str, "confidence": float, "reason": str, "factors": [...]}
    pass


def generate_determination(
    preliminary_decision: str,
    confidence: float,
    reason: str,
    cpt_code: str,
) -> dict:
    """Generate the formal determination record."""
    # TODO: Implement this function
    # 1. Look up criteria for cpt_code to get approval_validity_days
    # 2. Build conditions list based on decision type
    # 3. Return:
    #    - "determination": the decision string
    #    - "confidence": the confidence score
    #    - "reason": the justification
    #    - "conditions": list of conditions
    #    - "peer_review_required": True if PENDED
    #    - "approval_validity_days": days from criteria (0 if DENIED)
    pass


def route_for_review(
    request_id: str,
    preliminary_decision: str,
    confidence: float,
    reason: str,
    review_context: str = "",
) -> dict:
    """
    Route for human review — this is the HITL gate.

    In a real system this would create a review task. In this lab,
    it simulates HITL by using input() to get the reviewer's decision.
    """
    # TODO: Implement this function
    # 1. Print a clear review summary to the console
    # 2. Use input() to ask the reviewer: "Approve (a), Reject (r), or Override (o)?"
    # 3. Return:
    #    - "hitl_triggered": True
    #    - "reviewer_decision": "approved" | "rejected" | "override"
    #    - "original_decision": preliminary_decision
    #    - "request_id": request_id
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "apply_decision_rules": lambda args: apply_decision_rules(**args),
    "generate_determination": lambda args: generate_determination(**args),
    "route_for_review": lambda args: route_for_review(**args),
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
# Decision Agent Class
# ---------------------------------------------------------------------------

class DecisionAgent(BaseAgent):
    """
    Agent 3: Applies decision rules, generates determinations,
    and routes for human review when confidence is low.
    """

    name = "DecisionAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = f"""You are the Decision Agent in a healthcare pre-authorization pipeline.
You receive clinical criteria evaluation results and must make a determination.

You MUST:
1. FIRST apply decision rules using apply_decision_rules with the criteria results
2. IF the confidence score is below {HITL_CONFIDENCE_THRESHOLD}, use route_for_review to get human input
3. FINALLY generate the formal determination using generate_determination

Your decision must be justified based on ALL evidence gathered by prior agents.
If the confidence is low, always route for human review before finalizing."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from criteria results."""
        criteria = state.criteria
        intake = state.intake
        return (
            f"Make a determination for request {intake.request_id}:\n\n"
            f"CPT Code: {intake.cpt_code}\n"
            f"Diagnosis Match: {criteria.diagnosis_match}\n"
            f"Medical Necessity Score: {criteria.medical_necessity_score}\n"
            f"Network Status: {criteria.network_status}\n"
            f"Benefit Covered: {criteria.benefit_covered}\n"
            f"Procedure: {criteria.procedure_name} ({criteria.procedure_category})\n"
            f"Plan ID: {intake.plan_id}\n"
            f"Plan Type: {state.raw_request.get('plan_id', 'UNKNOWN')}\n"
            f"Clinical Notes: {intake.clinical_notes}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Decision Agent's ReAct loop.

        This agent includes the HITL gate — if confidence < threshold,
        route_for_review will pause for human input.

        Args:
            state: Pipeline state with criteria results populated.

        Returns:
            Updated pipeline state with decision results.
        """
        # TODO: Implement the ReAct loop (same pattern as prior agents)
        # Key difference: this agent may trigger the HITL gate via route_for_review
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop with HITL awareness
        # 4. Parse final response to update state.decision
        # 5. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with decision results."""
        # TODO: Parse result_text and populate state.decision fields
        return state
