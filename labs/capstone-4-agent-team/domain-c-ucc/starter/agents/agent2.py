"""
Transformation Agent (Agent 2) — UCC Data Engineering Pipeline

Responsibilities:
- Normalize entity names to canonical forms
- Classify collateral descriptions into standard categories
- Resolve entities across filings (match variations to canonical records)

Tools:
- normalize_entities: Standardize entity names (uppercase, strip suffixes, etc.)
- classify_collateral: Map free-text collateral descriptions to taxonomy categories
- resolve_entities: Match debtor names to canonical entity records via EIN or fuzzy match

YOUR TASK: Complete the TODO sections to build a working Transformation Agent.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import ENTITY_REGISTRY, COLLATERAL_TYPES

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
        "name": "normalize_entities",
        "description": (
            "Normalize entity names in a list of UCC filings. Standardizes names to "
            "uppercase, strips common suffixes (INC, LLC, CORP, etc.), normalizes "
            "whitespace, and removes DBA clauses. Returns the filings with a new "
            "'normalized_name' field added to each."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts to normalize entity names in",
                },
            },
            "required": ["filing_list"],
        },
    },
    {
        "name": "classify_collateral",
        "description": (
            "Classify collateral descriptions from UCC filings into standard taxonomy "
            "categories (inventory, equipment, receivables, intellectual_property, "
            "real_property, general_intangibles). Uses keyword matching against the "
            "collateral taxonomy. A single filing may match multiple categories."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts with collateral descriptions",
                },
            },
            "required": ["filing_list"],
        },
    },
    {
        "name": "resolve_entities",
        "description": (
            "Resolve entity names to canonical entity records from the entity registry. "
            "Matches by EIN (exact) or by checking if the debtor name appears in the "
            "entity's alias list. Returns resolution results with confidence scores. "
            "Flags low-confidence resolutions when no match is found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": (
                        "List of dicts with 'debtor_name', 'debtor_ein' (optional), "
                        "and 'filing_number' fields"
                    ),
                },
            },
            "required": ["entity_list"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def normalize_entities(filing_list: list[dict]) -> dict:
    """Normalize entity names in a list of filings."""
    # TODO: Implement this function
    # For each filing in filing_list:
    # 1. Get the debtor_name
    # 2. Convert to uppercase
    # 3. Strip leading/trailing whitespace
    # 4. Remove DBA clauses: strip " DBA ..." from the name
    # 5. Normalize common suffixes: replace variations like
    #    "CORPORATION" -> "CORP", "LIMITED LIABILITY COMPANY" -> "LLC",
    #    "INCORPORATED" -> "INC", ", L.L.C." -> " LLC"
    # 6. Collapse multiple spaces to single space
    # 7. Add "normalized_name" field to the filing dict
    # 8. Return {"normalized": updated_filing_list, "count": len(filing_list)}
    pass


def classify_collateral(filing_list: list[dict]) -> dict:
    """Classify collateral descriptions into taxonomy categories."""
    # TODO: Implement this function
    # For each filing:
    # 1. Get the "collateral" field, lowercase it
    # 2. For each category in COLLATERAL_TYPES:
    #    - Check if any keyword from that category appears in the collateral text
    #    - If yes, add the category to the filing's classification list
    # 3. If no categories matched, classify as "unclassified"
    # 4. Add "collateral_categories" field to each filing dict
    # 5. Return:
    #    {
    #        "classifications": updated_filing_list,
    #        "category_counts": {category: count, ...},
    #    }
    pass


def resolve_entities(entity_list: list[dict]) -> dict:
    """Resolve entity names to canonical records."""
    # TODO: Implement this function
    # For each entity in entity_list:
    # 1. First try EIN match: if debtor_ein is provided, search ENTITY_REGISTRY
    #    for an entity with matching ein. If found, confidence=1.0
    # 2. If no EIN match, try alias match: search ENTITY_REGISTRY for any entity
    #    whose "aliases" list contains the debtor_name. If found, confidence=0.9
    # 3. If no match at all, mark as unresolved with confidence=0.0
    # 4. Build resolution record:
    #    {
    #        "filing_number": ...,
    #        "debtor_name": ...,
    #        "resolved_entity_id": entity_id or None,
    #        "canonical_name": canonical_name or None,
    #        "confidence": float,
    #        "match_method": "ein" | "alias" | "unresolved",
    #    }
    # 5. Count low_confidence (confidence < 0.8) resolutions
    # 6. Return:
    #    {
    #        "resolutions": list of resolution records,
    #        "resolved_count": count of resolved,
    #        "unresolved_count": count of unresolved,
    #        "low_confidence_count": count of low confidence,
    #    }
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "normalize_entities": lambda args: normalize_entities(**args),
    "classify_collateral": lambda args: classify_collateral(**args),
    "resolve_entities": lambda args: resolve_entities(**args),
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
# Transformation Agent Class
# ---------------------------------------------------------------------------

class TransformationAgent(BaseAgent):
    """
    Agent 2: Normalizes entities, classifies collateral, and resolves
    entity identities across UCC filings.
    """

    name = "TransformationAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Transformation Agent in a UCC data engineering pipeline.
Your job is to normalize, classify, and resolve entity identities in parsed UCC filings.

You MUST:
1. FIRST normalize entity names using normalize_entities
2. THEN classify collateral descriptions using classify_collateral
3. FINALLY resolve entities to canonical records using resolve_entities

After calling all 3 tools, summarize your findings:
- Normalization: how many entities were normalized
- Classification: collateral category distribution
- Resolution: how many resolved vs unresolved, any low-confidence matches

Flag any low-confidence resolutions — the Quality Agent needs this for HITL gating."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build user message from ingestion results."""
        ing = state.ingestion
        return (
            f"Transform filings from batch {ing.batch_id}:\n\n"
            f"Source: {ing.source}\n"
            f"Format: {ing.format_detected}\n"
            f"Filing count: {ing.filing_count}\n"
            f"Schema valid: {ing.schema_valid}\n"
            f"Schema errors: {ing.schema_errors}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Transformation Agent's ReAct loop.

        Args:
            state: Pipeline state with ingestion results populated.

        Returns:
            Updated pipeline state with transformation results.
        """
        # TODO: Implement the ReAct loop (same pattern as Agent 1)
        # 1. Create Anthropic client
        # 2. Build user message from state
        # 3. ReAct loop up to MAX_ITERATIONS
        # 4. Update state.transformation with results
        # 5. Return updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with transformation results."""
        # TODO: Parse result_text and populate state.transformation fields
        return state
