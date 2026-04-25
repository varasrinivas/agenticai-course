"""
Model Router — intelligent model selection based on task complexity.
(Solution — fully implemented)
"""

import re
from typing import Any, Dict, Optional, Tuple

from config import (
    MODEL_TIERS, ROUTING_RULES, COMPLEXITY_WEIGHTS,
    COMPLEXITY_THRESHOLDS, ModelTier,
)

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}


class ModelRouter:
    """Routes tasks to the optimal model tier based on complexity."""

    def __init__(self):
        self._routing_history: list = []
        self._cost_savings: float = 0.0

    def score_complexity(self, query: str, task_type: str) -> float:
        weights = COMPLEXITY_WEIGHTS

        token_count = min(len(query.split()) / 100, 1.0)

        tool_estimates = {
            "filing_lookup": 1, "entity_resolution": 3, "risk_assessment": 4,
            "collateral_classification": 2, "data_validation": 1, "report_generation": 3,
        }
        tool_count = tool_estimates.get(task_type, 2) / 5

        cap_words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', query)
        entity_count = min(len(cap_words) / 5, 1.0)

        words = set(re.findall(r'\b[A-Z]{2}\b', query))
        state_count = min(len(words & US_STATES) / 5, 1.0)

        ambiguity = 0.3 if "?" in query else 0.0

        score = (
            weights["token_count"] * token_count
            + weights["tool_count"] * tool_count
            + weights["entity_count"] * entity_count
            + weights["state_count"] * state_count
            + weights["ambiguity_score"] * ambiguity
        )
        return min(round(score, 3), 1.0)

    def select_tier(self, complexity_score: float) -> str:
        for tier, (low, high) in COMPLEXITY_THRESHOLDS.items():
            if low <= complexity_score < high:
                return tier
        return "powerful"

    def get_model(self, tier: str) -> ModelTier:
        return MODEL_TIERS[tier]

    def route(self, query: str, task_type: str) -> Dict[str, Any]:
        complexity = self.score_complexity(query, task_type)
        tier = self.select_tier(complexity)

        # Check override rules
        for rule in ROUTING_RULES:
            if rule.task_type == task_type:
                tier = rule.default_tier  # Start with rule's default
                # Check upgrade conditions
                words_upper = set(re.findall(r'\b[A-Z]{2}\b', query))
                state_count = len(words_upper & US_STATES)
                if "multi_state" in rule.upgrade_conditions and state_count > 1:
                    tier = rule.upgrade_conditions["multi_state"]
                if "multi_entity" in rule.upgrade_conditions:
                    cap_words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', query)
                    if len(cap_words) > 2:
                        tier = rule.upgrade_conditions["multi_entity"]
                break

        model = self.get_model(tier)

        record = {
            "query_length": len(query),
            "task_type": task_type,
            "complexity": complexity,
            "tier": tier,
            "model_id": model.model_id,
        }
        self._routing_history.append(record)

        return {
            "tier": tier,
            "model_id": model.model_id,
            "complexity_score": complexity,
            "estimated_cost_range": f"${model.input_cost_per_1k * 0.5:.4f}-${model.input_cost_per_1k * 2:.4f}",
            "reasoning": f"Task '{task_type}' with complexity {complexity:.2f} -> tier '{tier}'",
        }

    def estimate_cost(self, tier: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        model = self.get_model(tier)
        input_cost = (input_tokens / 1000) * model.input_cost_per_1k
        output_cost = (output_tokens / 1000) * model.output_cost_per_1k
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
        }

    def get_routing_stats(self) -> Dict[str, Any]:
        if not self._routing_history:
            return {"total_routed": 0, "routes_by_tier": {}, "avg_complexity": 0.0,
                    "estimated_cost_savings": 0.0}

        by_tier = {}
        total_complexity = 0
        for r in self._routing_history:
            by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
            total_complexity += r["complexity"]

        # Estimate savings vs always using "powerful"
        powerful_cost = MODEL_TIERS["powerful"].input_cost_per_1k
        actual_cost = sum(
            MODEL_TIERS[r["tier"]].input_cost_per_1k for r in self._routing_history
        )
        savings = (powerful_cost * len(self._routing_history)) - actual_cost

        return {
            "total_routed": len(self._routing_history),
            "routes_by_tier": by_tier,
            "avg_complexity": round(total_complexity / len(self._routing_history), 3),
            "estimated_cost_savings": round(savings, 6),
        }
