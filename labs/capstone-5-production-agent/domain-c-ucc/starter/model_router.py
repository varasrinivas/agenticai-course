"""
Model Router — intelligent model selection based on task complexity.

Routes tasks to the appropriate model tier:
- Fast (Haiku-class): Simple lookups, classification, formatting
- Balanced (Sonnet-class): Multi-step reasoning, entity resolution
- Powerful (Opus-class): Complex risk analysis, ambiguous cases

Uses a scoring system based on:
- Token count (query length)
- Expected tool count
- Entity count
- State count (cross-jurisdictional complexity)
- Ambiguity score
"""

from typing import Any, Dict, Optional, Tuple
import re

from config import (
    MODEL_TIERS,
    ROUTING_RULES,
    COMPLEXITY_WEIGHTS,
    COMPLEXITY_THRESHOLDS,
    ModelTier,
)


class ModelRouter:
    """
    Routes tasks to the optimal model tier based on complexity analysis.

    This is the cost optimization engine — it ensures simple tasks don't
    waste expensive model capacity, while complex tasks get the reasoning
    power they need.
    """

    def __init__(self):
        self._routing_history: list = []
        self._cost_savings: float = 0.0

    # ------------------------------------------------------------------
    # TODO 1: Implement score_complexity()
    # Compute a complexity score (0.0 - 1.0) for a query.
    # Use the COMPLEXITY_WEIGHTS from config:
    #   - token_count: len(query.split()) / 100, capped at 1.0
    #   - tool_count: estimated tools / 5, based on task_type
    #     (filing_lookup=1, entity_resolution=3, risk_assessment=4,
    #      collateral_classification=2, data_validation=1, report_generation=3)
    #   - entity_count: count unique capitalized words / 5, capped at 1.0
    #   - state_count: count 2-letter state abbreviations / 5, capped at 1.0
    #   - ambiguity_score: 0.3 if "?" in query, else 0.0
    # Return: weighted sum using COMPLEXITY_WEIGHTS
    # ------------------------------------------------------------------
    def score_complexity(self, query: str, task_type: str) -> float:
        """Score the complexity of a query."""
        # TODO: Implement complexity scoring
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement select_tier()
    # Given a complexity score, return the matching tier name.
    # Use COMPLEXITY_THRESHOLDS:
    #   "fast": (0.0, 0.3), "balanced": (0.3, 0.7), "powerful": (0.7, 1.0)
    # ------------------------------------------------------------------
    def select_tier(self, complexity_score: float) -> str:
        """Select model tier based on complexity score."""
        # TODO: Map score to tier
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement get_model()
    # Given a tier name, return the ModelTier object from MODEL_TIERS.
    # ------------------------------------------------------------------
    def get_model(self, tier: str) -> ModelTier:
        """Get the model configuration for a tier."""
        # TODO: Return MODEL_TIERS[tier]
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement route()
    # The main routing method. Given a query and task_type:
    #   1. Score complexity
    #   2. Check for override rules in ROUTING_RULES
    #   3. Select tier (with possible upgrade from rules)
    #   4. Get model config
    #   5. Record routing decision in history
    #   6. Return routing result dict
    # Override logic: if a ROUTING_RULE for this task_type has an
    # upgrade_condition that matches, upgrade the tier.
    # ------------------------------------------------------------------
    def route(self, query: str, task_type: str) -> Dict[str, Any]:
        """
        Route a query to the optimal model.

        Returns:
            dict with keys:
            - tier: str
            - model_id: str
            - complexity_score: float
            - estimated_cost_range: str
            - reasoning: str
        """
        # TODO: Implement routing pipeline
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement estimate_cost()
    # Estimate the cost of a request given:
    #   - tier name
    #   - estimated input tokens
    #   - estimated output tokens
    # Use MODEL_TIERS[tier].input_cost_per_1k and output_cost_per_1k
    # Return: {"input_cost": float, "output_cost": float, "total_cost": float}
    # ------------------------------------------------------------------
    def estimate_cost(
        self,
        tier: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, float]:
        """Estimate the cost of a request."""
        # TODO: Calculate cost based on tier pricing
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement get_routing_stats()
    # Return statistics from routing history:
    #   - total_routed, routes_by_tier, avg_complexity,
    #   - estimated_cost_savings (difference vs. always using powerful tier)
    # ------------------------------------------------------------------
    def get_routing_stats(self) -> Dict[str, Any]:
        """Return routing statistics."""
        # TODO: Compute stats from routing history
        pass
