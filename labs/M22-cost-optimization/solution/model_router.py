"""
M22 Lab — Model Router (Solution)
===================================
Complete model router that classifies queries by complexity and
routes to Haiku, Sonnet, or Opus based on task type.

Usage:
    python model_router.py
"""

import re


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
    """Routes queries to the appropriate Claude model based on task complexity."""

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

    TASK_KEYWORDS = {
        "filing_lookup": ["filing", "lookup", "search", "find", "list", "get", "fetch", "show"],
        "entity_resolution": ["entity", "match", "resolve", "identify", "deduplicate", "merge", "link"],
        "risk_analysis": ["risk", "analysis", "assess", "evaluate", "score", "exposure", "liability", "collateral"],
    }

    def classify_task(self, query: str) -> str:
        """Classify a query into a task type based on keyword matching."""
        query_lower = query.lower()

        # Check in priority order: most expensive task first
        # This ensures "assess risk for filings" routes to risk, not filing_lookup
        for task_type in ["risk_analysis", "entity_resolution", "filing_lookup"]:
            keywords = self.TASK_KEYWORDS[task_type]
            if any(kw in query_lower for kw in keywords):
                return task_type

        return "general"

    def route(self, query: str, task_type: str = None) -> dict:
        """Determine which model to use for a given query."""
        if task_type is None:
            task_type = self.classify_task(query)

        # Find matching routing rule
        for rule_type, model_key, reason in self.ROUTING_RULES:
            if rule_type == task_type:
                pricing = MODEL_PRICING[model_key]
                return {
                    "model": model_key,
                    "display_name": pricing["display_name"],
                    "task_type": task_type,
                    "reason": reason,
                    "cost_per_1m_input": pricing["input_per_1m"],
                    "cost_per_1m_output": pricing["output_per_1m"],
                }

        # Fallback to general/Sonnet
        pricing = MODEL_PRICING["claude-sonnet-4"]
        return {
            "model": "claude-sonnet-4",
            "display_name": pricing["display_name"],
            "task_type": "general",
            "reason": "Fallback — Sonnet is the default balanced choice",
            "cost_per_1m_input": pricing["input_per_1m"],
            "cost_per_1m_output": pricing["output_per_1m"],
        }

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> dict:
        """Calculate the dollar cost for a specific API call."""
        pricing = MODEL_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }

    def compare_routing_vs_baseline(self, queries: list[dict]) -> dict:
        """Compare cost of routed queries vs. sending everything to Sonnet."""
        baseline_total = 0.0
        routed_total = 0.0

        for q in queries:
            # Baseline: everything goes to Sonnet
            baseline = self.estimate_cost("claude-sonnet-4", q["input_tokens"], q["output_tokens"])
            baseline_total += baseline["total_cost"]

            # Routed: use the appropriate model
            routing = self.route(q["query"])
            routed = self.estimate_cost(routing["model"], q["input_tokens"], q["output_tokens"])
            routed_total += routed["total_cost"]

        savings = baseline_total - routed_total
        savings_pct = (savings / baseline_total * 100) if baseline_total > 0 else 0.0

        return {
            "baseline_cost": baseline_total,
            "routed_cost": routed_total,
            "savings": savings,
            "savings_pct": savings_pct,
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test routing different queries to different models."""
    print("=" * 60)
    print("M22 Lab — Model Router Self-Test")
    print("=" * 60)

    router = ModelRouter()

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


if __name__ == "__main__":
    self_test()
