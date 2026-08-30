"""
M22 Lab — Model Router (Starter)
=================================
Route queries to the cheapest Claude model that can handle the task.
Filing lookups go to Haiku ($0.25/1M input), entity resolution to
Sonnet ($3/1M input), and complex risk analysis to Opus ($15/1M input).

KEY CONCEPT: Not every query needs the most powerful model. A simple
"look up filing #12345" costs 60x more on Opus than on Haiku, with
identical results. Routing by complexity is free money.

Usage:
    python model_router.py
"""

import re


# =============================================================================
# MODEL PRICING (per 1M tokens, as of 2025)
# =============================================================================
# Source: https://docs.anthropic.com/en/docs/about-claude/models

MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {
        "name": "claude-haiku-4-5-20251001",
        "display_name": "Haiku 3.5",
        "input_per_1m": 0.80,
        "output_per_1m": 4.00,
    },
    "claude-sonnet-4": {
        "name": "claude-sonnet-4",
        "display_name": "Sonnet 4",
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
    },
    "claude-opus-4": {
        "name": "claude-opus-4",
        "display_name": "Opus 4",
        "input_per_1m": 15.00,
        "output_per_1m": 75.00,
    },
}


class ModelRouter:
    """
    Routes queries to the appropriate Claude model based on task complexity.

    The router classifies each query into a task type using keyword matching,
    then maps that task type to a model. Each routing decision includes a
    human-readable reason explaining why that model was chosen.
    """

    # Routing rules: (task_type, model_key, reason)
    ROUTING_RULES = [
        ("filing_lookup", "claude-haiku-4-5-20251001",
         "Simple data retrieval — Haiku handles lookups at 1/4 the cost of Sonnet"),
        ("entity_resolution", "claude-sonnet-4",
         "Moderate reasoning needed — Sonnet balances cost and capability for entity matching"),
        ("risk_analysis", "claude-opus-4",
         "Complex multi-factor analysis — Opus provides deepest reasoning for risk assessment"),
        ("general", "claude-sonnet-4",
         "General query — Sonnet is the default balanced choice"),
    ]

    # Task classification keywords
    TASK_KEYWORDS = {
        "filing_lookup": ["filing", "lookup", "search", "find", "list", "get", "fetch", "show"],
        "entity_resolution": ["entity", "match", "resolve", "identify", "deduplicate", "merge", "link"],
        "risk_analysis": ["risk", "analysis", "assess", "evaluate", "score", "exposure", "liability", "collateral"],
    }

    def classify_task(self, query: str) -> str:
        """
        Classify a query into a task type based on keyword matching.

        Args:
            query: The user query string

        Returns:
            Task type string: "filing_lookup", "entity_resolution",
            "risk_analysis", or "general"
        """
        # TODO: Implement task classification
        # 1. Lowercase the query
        # 2. For each task type in TASK_KEYWORDS:
        #    a. Check if any keyword appears in the query
        #    b. If match found, return that task type
        # 3. Check in priority order: risk_analysis first (most expensive),
        #    then entity_resolution, then filing_lookup
        # 4. If no keywords match, return "general"
        pass

    def route(self, query: str, task_type: str = None) -> dict:
        """
        Determine which model to use for a given query.

        Args:
            query: The user query
            task_type: Optional pre-classified task type. If None, classify automatically.

        Returns:
            Dict with: model, display_name, reason, cost_per_1m_input, cost_per_1m_output
        """
        # TODO: Implement routing
        # 1. If task_type is None, call classify_task(query)
        # 2. Find the matching routing rule for the task type
        # 3. Look up the model pricing
        # 4. Return a dict with:
        #    - model: the model key string
        #    - display_name: human-readable model name
        #    - task_type: the classified task type
        #    - reason: why this model was chosen
        #    - cost_per_1m_input: input cost per 1M tokens
        #    - cost_per_1m_output: output cost per 1M tokens
        pass

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> dict:
        """
        Calculate the dollar cost for a specific API call.

        Args:
            model: Model key string (e.g., "claude-sonnet-4")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dict with: input_cost, output_cost, total_cost (all in dollars)
        """
        # TODO: Implement cost estimation
        # 1. Look up the model in MODEL_PRICING
        # 2. Calculate: input_cost = (input_tokens / 1_000_000) * input_per_1m
        # 3. Calculate: output_cost = (output_tokens / 1_000_000) * output_per_1m
        # 4. Return dict with input_cost, output_cost, total_cost
        pass

    def compare_routing_vs_baseline(self, queries: list[dict]) -> dict:
        """
        Compare cost of routed queries vs. sending everything to Sonnet.

        Args:
            queries: List of dicts with "query", "input_tokens", "output_tokens"

        Returns:
            Dict with baseline_cost, routed_cost, savings, savings_pct
        """
        # TODO: Implement comparison
        # 1. For each query, estimate cost with the routed model
        # 2. For each query, estimate cost with Sonnet (baseline)
        # 3. Sum both totals and calculate savings
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test routing different queries to different models."""
    print("=" * 60)
    print("M22 Lab — Model Router Self-Test")
    print("=" * 60)

    router = ModelRouter()

    # Test queries with expected routing
    test_queries = [
        ("Find all UCC filings for Acme Corp", "filing_lookup", "claude-haiku-4-5-20251001"),
        ("Search for filings in Texas", "filing_lookup", "claude-haiku-4-5-20251001"),
        ("List all secured parties in New York", "filing_lookup", "claude-haiku-4-5-20251001"),
        ("Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?", "entity_resolution", "claude-sonnet-4"),
        ("Identify matching debtors across jurisdictions", "entity_resolution", "claude-sonnet-4"),
        ("Assess the risk exposure for Greenfield Logistics", "risk_analysis", "claude-opus-4"),
        ("Evaluate collateral coverage and liability risk", "risk_analysis", "claude-opus-4"),
        ("What is UCC Article 9?", "general", "claude-sonnet-4"),
    ]

    print("\n--- Routing Decisions ---")
    all_passed = True
    for query, expected_type, expected_model in test_queries:
        result = router.route(query)
        status = "PASS" if result["model"] == expected_model else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"\n  [{status}] \"{query[:50]}...\"")
        print(f"    Task: {result['task_type']} | Model: {result['display_name']}")
        print(f"    Reason: {result['reason']}")
        print(f"    Cost: ${result['cost_per_1m_input']:.2f}/$1M in, "
              f"${result['cost_per_1m_output']:.2f}/$1M out")

    # Cost estimation test
    print("\n--- Cost Estimation ---")
    cost = router.estimate_cost("claude-sonnet-4", input_tokens=1500, output_tokens=500)
    print(f"  Sonnet: 1500 input + 500 output tokens")
    print(f"  Input: ${cost['input_cost']:.6f}, Output: ${cost['output_cost']:.6f}, "
          f"Total: ${cost['total_cost']:.6f}")

    cost_haiku = router.estimate_cost("claude-haiku-4-5-20251001", input_tokens=1500, output_tokens=500)
    print(f"\n  Haiku:  1500 input + 500 output tokens")
    print(f"  Input: ${cost_haiku['input_cost']:.6f}, Output: ${cost_haiku['output_cost']:.6f}, "
          f"Total: ${cost_haiku['total_cost']:.6f}")

    savings = (1 - cost_haiku['total_cost'] / cost['total_cost']) * 100
    print(f"\n  Haiku vs Sonnet savings: {savings:.1f}%")

    # Routing comparison
    print("\n--- Routing vs Baseline Comparison ---")
    sample_queries = [
        {"query": "Find filings for Acme", "input_tokens": 800, "output_tokens": 400},
        {"query": "Search filings in Texas", "input_tokens": 900, "output_tokens": 350},
        {"query": "Resolve entity Acme Corp vs ACME Corporation", "input_tokens": 1200, "output_tokens": 600},
        {"query": "Assess risk for Greenfield Logistics portfolio", "input_tokens": 2000, "output_tokens": 1000},
        {"query": "What is a UCC filing?", "input_tokens": 500, "output_tokens": 300},
    ]
    comparison = router.compare_routing_vs_baseline(sample_queries)
    print(f"  Baseline (all Sonnet): ${comparison['baseline_cost']:.6f}")
    print(f"  Routed:                ${comparison['routed_cost']:.6f}")
    print(f"  Savings:               ${comparison['savings']:.6f} ({comparison['savings_pct']:.1f}%)")

    if all_passed:
        print("\n" + "=" * 60)
        print("All router tests passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Some tests FAILED — check routing rules")
        print("=" * 60)


if __name__ == "__main__":
    self_test()
