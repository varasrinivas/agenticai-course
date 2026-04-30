"""
Quality Agent (Agent 3) — UCC Data Engineering Pipeline

Responsibilities:
- Run quality checks against configured rules
- Detect anomalies (duplicates, PII in collateral, date issues)
- Generate a quality scorecard
- HITL gate: pause for human review if quality_score < 80% or low_confidence_resolutions > 0

Tools:
- run_quality_checks: Apply QUALITY_RULES to the filing data
- detect_anomalies: Scan for duplicates, PII leakage, and data anomalies
- generate_scorecard: Produce a summary scorecard from check results and anomalies

YOUR TASK: Complete the TODO sections. This agent includes the HITL gate.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import QUALITY_RULES

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10
QUALITY_SCORE_THRESHOLD = 80.0  # Trigger HITL when quality_score < this
LOW_CONFIDENCE_THRESHOLD = 0    # Trigger HITL when low_confidence_resolutions > this

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "run_quality_checks",
        "description": (
            "Run configured quality rules against parsed and transformed UCC filings. "
            "Checks include: filing_number_required, debtor_name_required, valid_date_format, "
            "no_pii_in_collateral, no_duplicate_filings, and supported_format. "
            "Returns pass/fail status for each rule across all filings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts to check",
                },
                "batch_format": {
                    "type": "string",
                    "description": "The detected format of the batch (csv, json, xml, etc.)",
                },
            },
            "required": ["filings", "batch_format"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": (
            "Detect anomalies in UCC filings including duplicate filing numbers, "
            "PII embedded in collateral descriptions (SSN, DOB, driver's license), "
            "future-dated filings, and terminated filings with recent dates. "
            "Returns a list of anomaly records with severity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts to scan for anomalies",
                },
            },
            "required": ["filings"],
        },
    },
    {
        "name": "generate_scorecard",
        "description": (
            "Generate a quality scorecard from the results of quality checks and "
            "anomaly detection. Calculates an overall quality score (0-100) and "
            "determines whether the batch passes the quality gate. If the score is "
            "below the threshold or there are low-confidence entity resolutions, "
            "triggers the HITL gate for human review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "check_results": {
                    "type": "object",
                    "description": "Results from run_quality_checks",
                },
                "anomalies": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of anomaly records from detect_anomalies",
                },
                "low_confidence_resolutions": {
                    "type": "integer",
                    "description": "Number of low-confidence entity resolutions from Agent 2",
                },
            },
            "required": ["check_results", "anomalies", "low_confidence_resolutions"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def run_quality_checks(filings: list[dict], batch_format: str) -> dict:
    """Run quality rules against filings."""
    # TODO: Implement this function
    # For each filing, check each rule in QUALITY_RULES:
    # 1. "filing_number_required": filing_number must be non-empty
    # 2. "debtor_name_required": debtor_name must be non-empty
    # 3. "valid_date_format": filing_date must match YYYY-MM-DD (use regex or string check)
    # 4. "no_pii_in_collateral": collateral must NOT contain SSN patterns (XXX-XX-XXXX),
    #    DOB patterns (DOB:), or DL patterns (DL:)
    # 5. "no_duplicate_filings": no duplicate filing_numbers in the batch
    # 6. "supported_format": batch_format must be in ["csv", "json", "xml"]
    #
    # Build results:
    #   checks_passed: count of (filing, rule) pairs that passed
    #   checks_failed: count that failed
    #   failures: list of {"filing_number": ..., "rule": ..., "severity": ...}
    #
    # Return:
    #   {
    #       "checks_passed": int,
    #       "checks_failed": int,
    #       "total_checks": int,
    #       "failures": [...]
    #   }
    pass


def detect_anomalies(filings: list[dict]) -> dict:
    """Detect anomalies in filings."""
    # TODO: Implement this function
    # Scan for:
    # 1. Duplicate filing numbers — group by filing_number, flag groups with > 1
    #    Severity: "high"
    # 2. PII in collateral — check for SSN (XXX-XX-XXXX), DOB, DL patterns
    #    Severity: "critical"
    # 3. Invalid dates — filing_date that doesn't match YYYY-MM-DD
    #    Severity: "high"
    # 4. Missing required fields — filing_number or debtor_name is empty
    #    Severity: "critical"
    #
    # Return:
    #   {
    #       "anomalies": [
    #           {"type": "duplicate_filing", "filing_number": "...", "severity": "high", "detail": "..."},
    #           {"type": "pii_detected", "filing_number": "...", "severity": "critical", "detail": "..."},
    #           ...
    #       ],
    #       "anomaly_count": int,
    #   }
    pass


def generate_scorecard(
    check_results: dict, anomalies: list[dict], low_confidence_resolutions: int
) -> dict:
    """Generate quality scorecard and determine if HITL is needed."""
    # TODO: Implement this function
    # 1. Calculate quality_score:
    #    base_score = (checks_passed / total_checks) * 100  (if total_checks > 0, else 0)
    #    Subtract 5 points per critical anomaly
    #    Subtract 2 points per high anomaly
    #    Subtract 1 point per medium anomaly
    #    Floor at 0
    # 2. Determine if HITL is needed:
    #    hitl_required = (quality_score < QUALITY_SCORE_THRESHOLD) or (low_confidence_resolutions > LOW_CONFIDENCE_THRESHOLD)
    # 3. Build scorecard:
    #    {
    #        "quality_score": float,
    #        "checks_passed": int,
    #        "checks_failed": int,
    #        "anomaly_count": len(anomalies),
    #        "critical_anomalies": count of critical,
    #        "low_confidence_resolutions": int,
    #        "hitl_required": bool,
    #        "hitl_reasons": list of reasons (e.g., "Quality score 65.0 < 80.0", "2 low-confidence resolutions"),
    #        "gate_status": "PASS" or "HITL_REVIEW"
    #    }
    # 4. If hitl_required, simulate HITL by calling _human_review(scorecard)
    # 5. Return the scorecard with review_decision if HITL was triggered
    pass


def _human_review(scorecard: dict) -> dict:
    """
    Simulate HITL gate — pause for human review.

    In production, this would create a review task. In this lab,
    it uses input() to get the reviewer's decision.
    """
    # TODO: Implement this function
    # 1. Print a clear review summary showing:
    #    - Quality score
    #    - Number of anomalies
    #    - HITL reasons
    # 2. Use input() to ask: "Approve (a), Reject (r), or Escalate (e)?"
    # 3. Handle EOFError for non-interactive mode (default to "a")
    # 4. Return {"review_decision": "approved"|"rejected"|"escalated", "hitl_triggered": True}
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "run_quality_checks": lambda args: run_quality_checks(**args),
    "detect_anomalies": lambda args: detect_anomalies(**args),
    "generate_scorecard": lambda args: generate_scorecard(**args),
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
# Quality Agent Class
# ---------------------------------------------------------------------------

class QualityAgent(BaseAgent):
    """
    Agent 3: Runs quality checks, detects anomalies, generates scorecards,
    and triggers HITL review when quality thresholds are not met.
    """

    name = "QualityAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = f"""You are the Quality Agent in a UCC data engineering pipeline.
Your job is to validate data quality, detect anomalies, and gate the pipeline.

You MUST:
1. FIRST run quality checks using run_quality_checks
2. THEN detect anomalies using detect_anomalies
3. FINALLY generate a scorecard using generate_scorecard

The HITL gate triggers when:
- Quality score < {QUALITY_SCORE_THRESHOLD}%
- Low-confidence entity resolutions > {LOW_CONFIDENCE_THRESHOLD}

If HITL is triggered, the pipeline pauses for human review.
Report all findings clearly — the Reporting Agent depends on clean data."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from ingestion and transformation results."""
        ing = state.ingestion
        trans = state.transformation
        return (
            f"Run quality checks on batch {ing.batch_id}:\n\n"
            f"Format: {ing.format_detected}\n"
            f"Filing count: {ing.filing_count}\n"
            f"Schema valid: {ing.schema_valid}\n"
            f"Parse errors: {ing.parse_error_count}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}\n\n"
            f"Entity resolutions:\n{json.dumps(trans.entity_resolutions, indent=2)}\n"
            f"Low-confidence resolutions: {trans.low_confidence_resolutions}\n"
            f"Resolution conflicts: {json.dumps(trans.resolution_conflicts, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Quality Agent's ReAct loop.

        This agent includes the HITL gate — if quality_score < threshold
        or low_confidence_resolutions > 0, _human_review() will pause for input.

        Args:
            state: Pipeline state with ingestion and transformation results.

        Returns:
            Updated pipeline state with quality results.
        """
        # TODO: Implement the ReAct loop (same pattern as prior agents)
        # Key difference: this agent may trigger the HITL gate via generate_scorecard
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop with HITL awareness
        # 4. Parse final response to update state.quality
        # 5. If HITL triggered and reviewer rejects, set state.halted = True
        # 6. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with quality results."""
        # TODO: Parse result_text and populate state.quality fields
        return state
