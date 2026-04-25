"""
Router Agent — analyzes incoming queries and routes to specialist agents.

The router is the "front desk" of the system. It:
1. Classifies the query type (filing_lookup, entity_resolution, risk_assessment)
2. Estimates complexity
3. Routes to the appropriate specialist agent
4. May chain multiple agents for complex queries
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

from config import (
    ANTHROPIC_API_KEY,
    SYSTEM_PROMPTS,
    ROUTING_RULES,
    COMPLEXITY_WEIGHTS,
    COMPLEXITY_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# Query classification keywords — used for rule-based pre-classification
# ---------------------------------------------------------------------------
TASK_KEYWORDS = {
    "filing_lookup": [
        "filing", "filings", "ucc-1", "ucc-3", "lien", "search",
        "look up", "lookup", "find filing", "filing number", "status",
        "active", "lapsed", "terminated", "amendment",
    ],
    "entity_resolution": [
        "entity", "company", "business", "match", "resolve", "who is",
        "same company", "related", "subsidiary", "parent", "dba",
        "name variation", "alias", "doing business as",
    ],
    "risk_assessment": [
        "risk", "exposure", "collateral", "lien risk", "credit risk",
        "assess", "analysis", "total liens", "blanket lien", "priority",
        "how much", "what is the risk", "secured", "unsecured",
    ],
}


class RouterAgent:
    """
    Routes incoming queries to the appropriate specialist agent.

    Uses a two-phase approach:
    1. Rule-based pre-classification (fast, no API call)
    2. LLM-based classification for ambiguous cases
    """

    def __init__(self, client: Optional[Anthropic] = None):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.system_prompt = SYSTEM_PROMPTS["router"]

    # ------------------------------------------------------------------
    # TODO 1: Implement classify_query()
    # Use keyword matching to classify the query into a task type.
    # Steps:
    #   1. Lowercase the query
    #   2. For each task type in TASK_KEYWORDS, count how many keywords
    #      appear in the query
    #   3. Return the task type with the highest count
    #   4. If there's a tie or no matches, return "unknown"
    # Return: (task_type, confidence) where confidence = matches / total_keywords
    # ------------------------------------------------------------------
    def classify_query(self, query: str) -> Tuple[str, float]:
        """Classify a query into a task type using keyword matching."""
        # TODO: Implement keyword-based classification
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement estimate_complexity()
    # Estimate the complexity of a query on a 0.0-1.0 scale.
    # Factors (use COMPLEXITY_WEIGHTS from config):
    #   - token_count: len(query.split()) / 100 (capped at 1.0)
    #   - tool_count: estimated tools needed based on task_type
    #     filing_lookup=1, entity_resolution=3, risk_assessment=4, unknown=2
    #     Normalize: tool_count / 5
    #   - entity_count: count of capitalized multi-word phrases (rough proxy)
    #     Normalize: entity_count / 5 (capped at 1.0)
    #   - state_count: count of 2-letter state abbreviations found
    #     Normalize: state_count / 5 (capped at 1.0)
    #   - ambiguity_score: 1.0 if task_type is "unknown", else 0.0
    # Weighted sum using COMPLEXITY_WEIGHTS
    # ------------------------------------------------------------------
    def estimate_complexity(self, query: str, task_type: str) -> float:
        """Estimate query complexity on a 0.0-1.0 scale."""
        # TODO: Implement complexity estimation
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement select_model_tier()
    # Given a complexity score, return the appropriate model tier name.
    # Use COMPLEXITY_THRESHOLDS from config:
    #   "fast":     (0.0, 0.3)
    #   "balanced": (0.3, 0.7)
    #   "powerful": (0.7, 1.0)
    # ------------------------------------------------------------------
    def select_model_tier(self, complexity: float) -> str:
        """Select the model tier based on complexity score."""
        # TODO: Map complexity to tier using thresholds
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement route()
    # The main routing method. Given a query, return a routing decision.
    # Steps:
    #   1. classify_query() to get task_type and confidence
    #   2. If confidence < 0.1, use LLM to classify (call _llm_classify)
    #   3. estimate_complexity() to get complexity score
    #   4. select_model_tier() to get the model tier
    #   5. Determine which agent(s) to invoke:
    #      - filing_lookup → ["filing_agent"]
    #      - entity_resolution → ["entity_agent"]
    #      - risk_assessment → ["entity_agent", "risk_agent"] (need entity data first)
    #      - unknown → ["filing_agent"] (default)
    #   6. Return a RoutingDecision dict
    # ------------------------------------------------------------------
    def route(self, query: str) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent(s).

        Returns:
            dict with keys:
            - task_type: str
            - confidence: float
            - complexity: float
            - model_tier: str
            - agents: List[str]
            - reasoning: str
        """
        # TODO: Implement the routing pipeline
        pass

    # ------------------------------------------------------------------
    # TODO 5 (STRETCH): Implement _llm_classify()
    # For ambiguous queries, use the Claude API to classify.
    # Send the query to the LLM with the router system prompt.
    # Parse the JSON response to extract task_type.
    # This is a fallback — only called when keyword matching fails.
    # ------------------------------------------------------------------
    def _llm_classify(self, query: str) -> Tuple[str, float]:
        """Use LLM to classify an ambiguous query."""
        # TODO: Call Claude API with the router system prompt
        # TODO: Parse response to extract task_type and confidence
        # For now, return a default:
        return ("filing_lookup", 0.5)
