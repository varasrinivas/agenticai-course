"""
Risk Agent — lien risk assessment and collateral analysis.

Handles:
- Total lien exposure calculations
- Collateral classification and overlap detection
- Filing priority analysis (first-in-time rules)
- Risk score computation
- Portfolio-level risk reporting
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS, BUSINESS_REGISTRY, COLLATERAL_CATEGORIES


# ---------------------------------------------------------------------------
# Tool definitions for the Risk Agent
# ---------------------------------------------------------------------------
RISK_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name to find all liens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search"},
                "state": {"type": "string", "description": "Optional state filter"},
            },
            "required": ["debtor_name"],
        },
    },
    {
        "name": "classify_collateral",
        "description": "Classify a collateral description into standard categories and risk levels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "collateral_description": {
                    "type": "string",
                    "description": "The collateral description text from a UCC filing",
                },
            },
            "required": ["collateral_description"],
        },
    },
    {
        "name": "calculate_exposure",
        "description": "Calculate total lien exposure for an entity based on its filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "filing_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of filing numbers to include in the calculation",
                },
            },
            "required": ["ein", "filing_numbers"],
        },
    },
    {
        "name": "generate_risk_report",
        "description": "Generate a structured risk assessment report for an entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "entity_name": {"type": "string", "description": "Name of the entity"},
                "filings_summary": {
                    "type": "string",
                    "description": "JSON string with filing and collateral analysis results",
                },
            },
            "required": ["ein", "entity_name", "filings_summary"],
        },
    },
]


class RiskAgent:
    """
    Specialist agent for lien risk assessment.

    Analyzes UCC filings to determine:
    - Total number and nature of liens
    - Whether blanket liens exist (high risk)
    - Collateral overlap between filings
    - Filing priority based on first-in-time
    - Overall risk score (low/medium/high/critical)
    """

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "powerful"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["risk"]

    # ------------------------------------------------------------------
    # TODO 1: Implement _execute_tool()
    # ------------------------------------------------------------------
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as JSON string."""
        # TODO: Dispatch to appropriate method
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement _search_filings()
    # Same search logic as other agents — search UCC_FILINGS by debtor_name.
    # ------------------------------------------------------------------
    def _search_filings(
        self,
        debtor_name: str,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search filings by debtor name."""
        # TODO: Implement filing search
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement _classify_collateral()
    # Given a collateral description, classify it against
    # COLLATERAL_CATEGORIES. Check each category's keywords.
    # A filing can match multiple categories.
    # Return:
    #   - categories: list of matched category names
    #   - risk_level: highest risk level among matches
    #     (priority: "high" > "medium" > "low")
    #   - is_blanket_lien: bool (True if "all_assets" category matched)
    #   - details: list of {category, risk_level, matched_keywords}
    # ------------------------------------------------------------------
    def _classify_collateral(self, collateral_description: str) -> Dict[str, Any]:
        """Classify collateral into standard categories."""
        # TODO: Match against COLLATERAL_CATEGORIES keywords
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement _calculate_exposure()
    # Given an EIN and list of filing numbers, compute exposure summary:
    #   - total_active_filings: count of active filings in the list
    #   - unique_secured_parties: list of distinct secured parties
    #   - has_blanket_lien: True if any filing has "all assets" collateral
    #   - collateral_categories: aggregated across all filings
    #   - earliest_filing_date: date of oldest filing (first priority)
    #   - filing_details: list of {filing_number, secured_party,
    #     collateral_summary, status, filing_date}
    # ------------------------------------------------------------------
    def _calculate_exposure(
        self,
        ein: str,
        filing_numbers: List[str],
    ) -> Dict[str, Any]:
        """Calculate lien exposure for an entity."""
        # TODO: Aggregate filing data and compute exposure
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement _generate_risk_report()
    # Generate a structured risk report. Compute a risk score:
    #   - Start at 0
    #   - +30 if blanket lien exists
    #   - +10 per active filing (max +50)
    #   - +15 if > 3 unique secured parties
    #   - +20 if any lapsed filings (indicates possible credit issues)
    #   - +10 if filings in > 3 states (complex lien structure)
    # Score mapping: 0-25 = "LOW", 26-50 = "MEDIUM", 51-75 = "HIGH", 76+ = "CRITICAL"
    # Return a report dict with: entity info, risk_score, risk_level,
    #   risk_factors (list), recommendations (list), filing_summary
    # ------------------------------------------------------------------
    def _generate_risk_report(
        self,
        ein: str,
        entity_name: str,
        filings_summary: str,
    ) -> Dict[str, Any]:
        """Generate a structured risk assessment report."""
        # TODO: Compute risk score and generate report
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement process()
    # Same agent loop pattern but using RISK_TOOLS.
    # ------------------------------------------------------------------
    def process(self, query: str) -> Dict[str, Any]:
        """Process a risk assessment query using the agent loop."""
        # TODO: Implement the tool-use agent loop
        pass
