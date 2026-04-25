"""
Filing Agent — UCC filing lookup and analysis.

Handles:
- Filing searches by debtor name, state, or filing number
- Filing status checks (active, lapsed, terminated)
- Amendment history retrieval
- Cross-state filing aggregation
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS


# ---------------------------------------------------------------------------
# Tool definitions for the Filing Agent (Anthropic tool use format)
# ---------------------------------------------------------------------------
FILING_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state. Returns a list of matching filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Name of the debtor to search for (supports partial/fuzzy matching)",
                },
                "state": {
                    "type": "string",
                    "description": "Two-letter state code (e.g., 'NY', 'CA'). If omitted, searches all states.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_filing_details",
        "description": "Get complete details for a specific UCC filing by filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The filing number (e.g., 'NY-2023-0558291')",
                },
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "check_filing_status",
        "description": "Check the current status of a UCC filing (active, lapsed, terminated).",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The filing number to check",
                },
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "get_amendments",
        "description": "Get the amendment history for a specific UCC filing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The filing number to get amendments for",
                },
            },
            "required": ["filing_number"],
        },
    },
]


class FilingAgent:
    """
    Specialist agent for UCC filing lookups and analysis.

    Uses Claude's tool use to process filing queries, calling into
    the mock UCC filing database.
    """

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "fast"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["filing"]

    # ------------------------------------------------------------------
    # TODO 1: Implement _execute_tool()
    # Given a tool name and its input dict, execute the corresponding
    # local function and return the result as a JSON string.
    # Dispatch to:
    #   "search_filings" → self._search_filings(...)
    #   "get_filing_details" → self._get_filing_details(...)
    #   "check_filing_status" → self._check_filing_status(...)
    #   "get_amendments" → self._get_amendments(...)
    # If tool_name is unknown, return an error message.
    # ------------------------------------------------------------------
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as JSON string."""
        # TODO: Dispatch to the appropriate method based on tool_name
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement _search_filings()
    # Search UCC_FILINGS by debtor_name and/or state.
    # If state is provided, only search that state's filings.
    # If state is None, search all states.
    # Name matching: case-insensitive substring match on debtor_name.
    # Return a list of dicts with: filing_number, state, debtor_name,
    #   secured_party, filing_date, status
    # ------------------------------------------------------------------
    def _search_filings(
        self,
        debtor_name: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search filings by debtor name and/or state."""
        # TODO: Implement search logic
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement _get_filing_details()
    # Given a filing_number, find it in UCC_FILINGS and return the full
    # filing dict. The state prefix is the first two characters of the
    # filing number. Return an error dict if not found.
    # ------------------------------------------------------------------
    def _get_filing_details(self, filing_number: str) -> Dict[str, Any]:
        """Get full details for a specific filing."""
        # TODO: Parse state from filing number, look up in UCC_FILINGS
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement _check_filing_status()
    # Given a filing_number, return its status with additional context:
    # - If active: include lapse_date and days until lapse
    # - If lapsed: include lapse_date and days since lapse
    # - If terminated: include termination date
    # ------------------------------------------------------------------
    def _check_filing_status(self, filing_number: str) -> Dict[str, Any]:
        """Check the status of a filing with contextual information."""
        # TODO: Look up filing and compute status context
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement _get_amendments()
    # Given a filing_number, return its amendment history.
    # Include the original filing date and each amendment.
    # ------------------------------------------------------------------
    def _get_amendments(self, filing_number: str) -> Dict[str, Any]:
        """Get amendment history for a filing."""
        # TODO: Look up filing and return amendments
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement process()
    # The main agent loop using Claude's tool use.
    # Steps:
    #   1. Send the query to Claude with FILING_TOOLS
    #   2. If Claude responds with tool_use blocks, execute each tool
    #   3. Send tool results back to Claude
    #   4. Repeat until Claude responds with a text block (final answer)
    #   5. Return a dict with: answer, tool_calls_made, model_used
    # Keep a running list of messages for the conversation.
    # Limit to max 10 iterations to prevent infinite loops.
    # ------------------------------------------------------------------
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a filing query using the agent loop.

        Returns:
            dict with keys:
            - answer: str (the final text response)
            - tool_calls_made: List[dict] (tool name + input for each call)
            - model_used: str
        """
        # TODO: Implement the tool-use agent loop
        pass
