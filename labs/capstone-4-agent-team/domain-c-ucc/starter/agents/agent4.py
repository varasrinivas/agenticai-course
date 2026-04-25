"""
Reporting Agent (Agent 4) — UCC Data Engineering Pipeline

Responsibilities:
- Generate lien risk profiles for resolved entities
- Generate a lien summary report for the batch
- Redact any PII that may have slipped through quality checks

Tools:
- generate_risk_profiles: Assess lien risk for each resolved entity
- generate_lien_summary: Create an aggregate summary of liens in the batch
- redact_pii: Scan and redact PII from report text

YOUR TASK: Complete the TODO sections to build a working Reporting Agent.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState

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
        "name": "generate_risk_profiles",
        "description": (
            "Generate lien risk profiles for each resolved entity. Considers the number "
            "of active liens, total collateral types, entity risk tier from the registry, "
            "and whether any anomalies were flagged. Returns a risk profile per entity "
            "with a risk_level (low, medium, high, critical)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of parsed filing dicts",
                },
                "entity_resolutions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of entity resolution records from Agent 2",
                },
            },
            "required": ["filings", "entity_resolutions"],
        },
    },
    {
        "name": "generate_lien_summary",
        "description": (
            "Generate an aggregate lien summary for the batch. Counts active vs terminated "
            "liens, groups by state, lists top secured parties, and summarizes collateral "
            "categories. Provides a high-level overview suitable for compliance reporting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of parsed filing dicts",
                },
            },
            "required": ["filings"],
        },
    },
    {
        "name": "redact_pii",
        "description": (
            "Scan text for PII patterns and redact them. Detects and replaces SSN "
            "patterns (XXX-XX-XXXX), date of birth references, driver's license numbers, "
            "and EIN numbers with redaction markers like [REDACTED-SSN]. Returns the "
            "redacted text and a count of redactions made."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to scan and redact PII from",
                },
            },
            "required": ["text"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def generate_risk_profiles(filings: list[dict], entity_resolutions: list[dict]) -> dict:
    """Generate lien risk profiles for resolved entities."""
    # TODO: Implement this function
    # 1. Group filings by resolved entity_id (use entity_resolutions to map)
    # 2. For each entity:
    #    a. Count active liens (status == "active")
    #    b. Count total liens
    #    c. Collect unique collateral categories
    #    d. Look up risk_tier from the entity resolution record
    #    e. Determine risk_level:
    #       - "critical" if active_liens >= 4 or risk_tier == "high"
    #       - "high" if active_liens >= 3
    #       - "medium" if active_liens >= 2
    #       - "low" otherwise
    # 3. Return:
    #    {
    #        "profiles": [
    #            {
    #                "entity_id": ..., "canonical_name": ...,
    #                "active_liens": int, "total_liens": int,
    #                "collateral_types": [...], "risk_tier": ...,
    #                "risk_level": ...,
    #            },
    #            ...
    #        ],
    #        "total_entities": int,
    #        "high_risk_count": int,
    #    }
    pass


def generate_lien_summary(filings: list[dict]) -> dict:
    """Generate aggregate lien summary for the batch."""
    # TODO: Implement this function
    # 1. Count active vs terminated filings
    # 2. Extract state from filing_number (e.g., "UCC-2024-CA-00101" -> "CA")
    #    and group counts by state
    # 3. Count filings per secured_party
    # 4. Collect all collateral_categories (if present from Agent 2)
    # 5. Return:
    #    {
    #        "total_filings": int,
    #        "active_count": int,
    #        "terminated_count": int,
    #        "by_state": {"CA": int, "NY": int, ...},
    #        "top_secured_parties": [{"name": ..., "filing_count": int}, ...],
    #        "collateral_distribution": {"equipment": int, ...},
    #    }
    pass


def redact_pii(text: str) -> dict:
    """Redact PII patterns from text."""
    # TODO: Implement this function
    # 1. Use regex to find and replace:
    #    a. SSN pattern (XXX-XX-XXXX) -> [REDACTED-SSN]
    #    b. DOB pattern (DOB: ...) -> [REDACTED-DOB]
    #    c. DL pattern (DL: ...) -> [REDACTED-DL]
    #    d. EIN pattern (XX-XXXXXXX) -> [REDACTED-EIN]
    # 2. Count total redactions
    # 3. Return:
    #    {
    #        "redacted_text": str,
    #        "redaction_count": int,
    #        "redaction_types": {"ssn": int, "dob": int, "dl": int, "ein": int},
    #    }
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "generate_risk_profiles": lambda args: generate_risk_profiles(**args),
    "generate_lien_summary": lambda args: generate_lien_summary(**args),
    "redact_pii": lambda args: redact_pii(**args),
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
# Reporting Agent Class
# ---------------------------------------------------------------------------

class ReportingAgent(BaseAgent):
    """
    Agent 4: Generates risk profiles, lien summaries, and handles
    PII redaction for final reporting.
    """

    name = "ReportingAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Reporting Agent in a UCC data engineering pipeline.
Your job is to generate risk profiles, summarize lien data, and ensure PII is redacted.

You MUST:
1. FIRST generate risk profiles using generate_risk_profiles
2. THEN generate a lien summary using generate_lien_summary
3. FINALLY redact any PII from the report text using redact_pii

Produce a clean, compliance-ready report. Flag any high-risk entities prominently.
All PII must be redacted before the report is considered complete."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from all prior agent results."""
        ing = state.ingestion
        trans = state.transformation
        qual = state.quality
        return (
            f"Generate reports for batch {ing.batch_id}:\n\n"
            f"Filing count: {ing.filing_count}\n"
            f"Quality score: {qual.quality_score}\n"
            f"Quality gate: {'PASS' if qual.quality_score >= 80 else 'HITL_REVIEW'}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}\n\n"
            f"Entity resolutions:\n{json.dumps(trans.entity_resolutions, indent=2)}\n\n"
            f"Collateral classifications:\n{json.dumps(trans.collateral_classifications, indent=2)}\n\n"
            f"Quality scorecard:\n{json.dumps(qual.scorecard, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Reporting Agent's ReAct loop.

        Args:
            state: Pipeline state with all prior agent results.

        Returns:
            Updated pipeline state with reporting results.
        """
        # TODO: Implement the ReAct loop (same pattern as prior agents)
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop up to MAX_ITERATIONS
        # 4. Update state.reporting with results
        # 5. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with reporting results."""
        # TODO: Parse result_text and populate state.reporting fields
        return state
