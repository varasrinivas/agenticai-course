"""
Router Agent — analyzes incoming queries and routes to specialist agents.
(Solution — fully implemented)
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

from config import (
    ANTHROPIC_API_KEY, SYSTEM_PROMPTS, ROUTING_RULES,
    COMPLEXITY_WEIGHTS, COMPLEXITY_THRESHOLDS,
)


TASK_KEYWORDS = {
    "filing_lookup": [
        "filing", "filings", "ucc-1", "ucc-3", "lien", "search",
        "look up", "lookup", "find filing", "filing number", "status",
        "active", "lapsed", "terminated", "amendment", "amendments",
        "details", "collateral", "secured party",
    ],
    "entity_resolution": [
        "entity", "company", "business", "match", "resolve", "who is",
        "same company", "related", "subsidiary", "parent", "dba",
        "name variation", "alias", "doing business as", "profile",
        "unified", "canonical",
    ],
    "risk_assessment": [
        "risk", "exposure", "collateral", "lien risk", "credit risk",
        "assess", "analysis", "total liens", "blanket lien", "priority",
        "how much", "what is the risk", "secured", "unsecured", "risk report",
        "portfolio", "rank", "compare risk",
    ],
}

# State abbreviations for complexity scoring
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}


class RouterAgent:
    """Routes incoming queries to the appropriate specialist agent."""

    def __init__(self, client: Optional[Anthropic] = None):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.system_prompt = SYSTEM_PROMPTS["router"]

    def classify_query(self, query: str) -> Tuple[str, float]:
        query_lower = query.lower()
        scores = {}
        for task_type, keywords in TASK_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            scores[task_type] = matches / len(keywords) if keywords else 0.0

        if not scores or max(scores.values()) == 0:
            return ("unknown", 0.0)

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        # Check for ties
        top_scores = [t for t, s in scores.items() if s == best_score]
        if len(top_scores) > 1 and best_score > 0:
            return (best_type, best_score * 0.7)  # Reduce confidence on ties

        return (best_type, best_score)

    def estimate_complexity(self, query: str, task_type: str) -> float:
        weights = COMPLEXITY_WEIGHTS

        # Token count factor
        token_count = min(len(query.split()) / 100, 1.0)

        # Tool count factor
        tool_estimates = {
            "filing_lookup": 1, "entity_resolution": 3,
            "risk_assessment": 4, "unknown": 2,
            "collateral_classification": 2, "data_validation": 1,
            "report_generation": 3,
        }
        tool_count = tool_estimates.get(task_type, 2) / 5

        # Entity count (capitalized multi-word phrases as rough proxy)
        cap_words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', query)
        entity_count = min(len(cap_words) / 5, 1.0)

        # State count
        words = set(re.findall(r'\b[A-Z]{2}\b', query))
        state_count = min(len(words & US_STATES) / 5, 1.0)

        # Ambiguity
        ambiguity = 0.3 if "?" in query else 0.0

        score = (
            weights["token_count"] * token_count
            + weights["tool_count"] * tool_count
            + weights["entity_count"] * entity_count
            + weights["state_count"] * state_count
            + weights["ambiguity_score"] * ambiguity
        )
        return min(score, 1.0)

    def select_model_tier(self, complexity: float) -> str:
        for tier, (low, high) in COMPLEXITY_THRESHOLDS.items():
            if low <= complexity < high:
                return tier
        return "powerful"

    def route(self, query: str) -> Dict[str, Any]:
        task_type, confidence = self.classify_query(query)

        if confidence < 0.1:
            task_type, confidence = self._llm_classify(query)

        complexity = self.estimate_complexity(query, task_type)
        model_tier = self.select_model_tier(complexity)

        agent_map = {
            "filing_lookup": ["filing_agent"],
            "entity_resolution": ["entity_agent"],
            "risk_assessment": ["entity_agent", "risk_agent"],
            "unknown": ["filing_agent"],
        }
        agents = agent_map.get(task_type, ["filing_agent"])

        return {
            "task_type": task_type,
            "confidence": round(confidence, 3),
            "complexity": round(complexity, 3),
            "model_tier": model_tier,
            "agents": agents,
            "reasoning": f"Classified as '{task_type}' (confidence={confidence:.2f}), "
                         f"complexity={complexity:.2f} -> tier='{model_tier}', "
                         f"agents={agents}",
        }

    def _llm_classify(self, query: str) -> Tuple[str, float]:
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=256,
                system=self.system_prompt,
                messages=[{"role": "user", "content": f"Classify this query into one of: filing_lookup, entity_resolution, risk_assessment. Query: {query}\n\nRespond with JSON: {{\"task_type\": \"...\", \"confidence\": 0.0-1.0}}"}],
            )
            text = response.content[0].text
            data = json.loads(text)
            return (data.get("task_type", "filing_lookup"), data.get("confidence", 0.5))
        except Exception:
            return ("filing_lookup", 0.5)
