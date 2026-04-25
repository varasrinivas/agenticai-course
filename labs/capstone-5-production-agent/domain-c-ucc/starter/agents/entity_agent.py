"""
Entity Agent — entity resolution across UCC filings and states.

Handles:
- Name matching across filings (fuzzy matching)
- Cross-state entity identification
- Business registry lookups
- Unified entity profile creation
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS, BUSINESS_REGISTRY, ADDITIONAL_ENTITIES


# ---------------------------------------------------------------------------
# Tool definitions for the Entity Agent
# ---------------------------------------------------------------------------
ENTITY_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name across all states or a specific state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search for"},
                "state": {"type": "string", "description": "Optional 2-letter state code"},
            },
            "required": ["debtor_name"],
        },
    },
    {
        "name": "fuzzy_match",
        "description": "Compare two entity names and return a similarity score (0.0-1.0) with match analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name_a": {"type": "string", "description": "First entity name"},
                "name_b": {"type": "string", "description": "Second entity name"},
            },
            "required": ["name_a", "name_b"],
        },
    },
    {
        "name": "get_business_registry",
        "description": "Look up official business registration data by EIN or entity name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "Employer Identification Number (e.g., '94-3829471')"},
                "entity_name": {"type": "string", "description": "Business name to search for"},
            },
            "required": [],
        },
    },
    {
        "name": "merge_entity_profile",
        "description": "Combine filing data and registry data into a unified entity profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "filings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of filing numbers to include",
                },
            },
            "required": ["ein", "filings"],
        },
    },
]


class EntityAgent:
    """
    Specialist agent for entity resolution across UCC filings.

    Entity resolution is one of the hardest problems in UCC data —
    the same company can appear under different names, with different
    abbreviations, across different states.
    """

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "balanced"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["entity"]

    # ------------------------------------------------------------------
    # TODO 1: Implement _execute_tool()
    # Dispatch tool calls to the appropriate method.
    # ------------------------------------------------------------------
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as JSON string."""
        # TODO: Dispatch to _search_filings, _fuzzy_match, _get_business_registry, _merge_entity_profile
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement _search_filings()
    # Same as FilingAgent._search_filings but returns slightly different
    # fields (include debtor_ein for entity matching).
    # Case-insensitive substring search on debtor_name.
    # ------------------------------------------------------------------
    def _search_filings(
        self,
        debtor_name: str,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search filings by debtor name."""
        # TODO: Implement cross-state filing search
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement _fuzzy_match()
    # Compare two entity names using a simplified scoring system:
    #   1. Normalize both names: lowercase, strip punctuation, strip common
    #      suffixes (inc, llc, corp, corporation, company, co, ltd, lp, group)
    #   2. Exact match after normalization → 1.0
    #   3. One name contains the other → 0.85
    #   4. Token overlap (Jaccard on word tokens) → score * 0.8
    #   5. Return: {"score": float, "name_a_normalized": str,
    #      "name_b_normalized": str, "match_type": str}
    # ------------------------------------------------------------------
    def _fuzzy_match(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """Compare two entity names for similarity."""
        # TODO: Implement fuzzy name matching
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement _get_business_registry()
    # Look up by EIN first (exact match). If not found, search by name
    # across BUSINESS_REGISTRY and ADDITIONAL_ENTITIES.
    # Name search: case-insensitive match on legal_name and dba_names.
    # Return the registry entry or an error dict if not found.
    # ------------------------------------------------------------------
    def _get_business_registry(
        self,
        ein: Optional[str] = None,
        entity_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Look up business registration data."""
        # TODO: Implement registry lookup by EIN or name
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement _merge_entity_profile()
    # Given an EIN and list of filing numbers, create a unified profile:
    #   - Legal name and all name variations found in filings
    #   - Total active filings count
    #   - All secured parties
    #   - All collateral descriptions
    #   - States with filings
    #   - Registry data (if available)
    # ------------------------------------------------------------------
    def _merge_entity_profile(
        self,
        ein: str,
        filings: List[str],
    ) -> Dict[str, Any]:
        """Merge filing and registry data into a unified entity profile."""
        # TODO: Build unified profile from filings and registry
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement process()
    # Same agent loop pattern as FilingAgent.process() but using
    # ENTITY_TOOLS and the entity system prompt.
    # ------------------------------------------------------------------
    def process(self, query: str) -> Dict[str, Any]:
        """Process an entity resolution query using the agent loop."""
        # TODO: Implement the tool-use agent loop
        pass
