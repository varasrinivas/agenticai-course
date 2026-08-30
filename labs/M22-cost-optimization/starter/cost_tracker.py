"""
M22 Lab — Cost Tracker (Starter)
=================================
Track every API call's cost, compare against baselines, and generate
a formatted report showing exactly where your money goes.

KEY CONCEPT: You can't optimize what you don't measure. A cost tracker
turns vague "it seems expensive" into precise "we spent $4.23 on Opus
calls that could have been Haiku calls, wasting $3.89."

Usage:
    python cost_tracker.py
"""

from datetime import datetime


# Model pricing (same as model_router.py)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input_per_1m": 0.80, "output_per_1m": 4.00},
    "claude-sonnet-4": {"input_per_1m": 3.00, "output_per_1m": 15.00},
    "claude-opus-4": {"input_per_1m": 15.00, "output_per_1m": 75.00},
}

# Batch API gets 50% discount
BATCH_DISCOUNT = 0.50


class CostTracker:
    """
    Tracks API call costs and generates savings reports.

    Every call to `record()` logs the model, token counts, cost, and
    whether the result was served from cache. The tracker computes
    savings from caching (calls avoided) and routing (cheaper models).
    """

    def __init__(self):
        self.records = []  # List of call records
        self.cache_savings = 0.0  # Estimated $ saved by cache hits

    def record(self, model: str, input_tokens: int, output_tokens: int,
               cached: bool = False, batch: bool = False) -> dict:
        """
        Log an API call (or cache hit).

        Args:
            model: Model key string (e.g., "claude-sonnet-4")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached: If True, this was a cache hit (cost = $0)
            batch: If True, apply 50% batch discount

        Returns:
            Dict with: model, input_tokens, output_tokens, cost, cached, timestamp
        """
        # TODO: Implement cost recording
        # 1. Look up model pricing
        # 2. Calculate cost:
        #    - If cached: cost = 0.0, but estimate what it WOULD have cost
        #      and add to self.cache_savings
        #    - If batch: apply BATCH_DISCOUNT to the calculated cost
        #    - Otherwise: normal cost calculation
        # 3. Create a record dict with all fields + timestamp
        # 4. Append to self.records
        # 5. Return the record
        pass

    def get_total_cost(self) -> float:
        """Return total actual cost across all records."""
        # TODO: Sum the 'cost' field of all records
        pass

    def get_cost_by_model(self) -> dict:
        """
        Break down costs by model.

        Returns:
            Dict mapping model name to {calls, input_tokens, output_tokens, cost}
        """
        # TODO: Aggregate records by model
        pass

    def get_savings_from_cache(self) -> dict:
        """
        Calculate savings from cache hits.

        Returns:
            Dict with: cache_hits, cache_misses, estimated_savings
        """
        # TODO: Count cached vs non-cached records and return savings
        pass

    def get_savings_from_routing(self) -> dict:
        """
        Calculate savings vs. an all-Sonnet baseline.

        Compares actual cost to what it would have cost if every call
        used Sonnet instead of the routed model.

        Returns:
            Dict with: actual_cost, baseline_cost, savings, savings_pct
        """
        # TODO: For each non-cached record:
        # 1. Calculate what it would have cost with Sonnet
        # 2. Sum actual costs and baseline costs
        # 3. Calculate savings amount and percentage
        pass

    def generate_report(self) -> str:
        """
        Generate a formatted cost optimization report.

        Returns:
            Multi-line string with complete cost breakdown
        """
        # TODO: Build a formatted report string including:
        # 1. Total calls and total cost
        # 2. Per-model breakdown (calls, tokens, cost)
        # 3. Cache savings
        # 4. Routing savings vs baseline
        # 5. Batch savings if any
        # Use f-strings for formatting, align columns for readability
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Simulate 50 mixed calls and generate a cost report."""
    print("=" * 60)
    print("M22 Lab — Cost Tracker Self-Test")
    print("=" * 60)

    tracker = CostTracker()

    # Simulate 50 calls with realistic distribution
    import random
    random.seed(42)  # Reproducible results

    call_scenarios = [
        # (model, input_range, output_range, cache_prob, batch_prob)
        ("claude-haiku-4-5-20251001", (400, 1000), (200, 500), 0.3, 0.1),    # Filing lookups
        ("claude-haiku-4-5-20251001", (500, 900), (150, 400), 0.4, 0.2),     # Simple searches
        ("claude-sonnet-4", (800, 1500), (300, 800), 0.2, 0.05),    # Entity resolution
        ("claude-sonnet-4", (600, 1200), (200, 600), 0.25, 0.0),    # General queries
        ("claude-opus-4", (1500, 3000), (500, 1500), 0.1, 0.0),     # Risk analysis
    ]

    for i in range(50):
        scenario = call_scenarios[i % len(call_scenarios)]
        model = scenario[0]
        input_tokens = random.randint(*scenario[1])
        output_tokens = random.randint(*scenario[2])
        cached = random.random() < scenario[3]
        batch = random.random() < scenario[4]

        tracker.record(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached,
            batch=batch,
        )

    # Generate and print report
    print("\n--- Cost Report ---")
    report = tracker.generate_report()
    print(report)

    # Verify key metrics
    total = tracker.get_total_cost()
    by_model = tracker.get_cost_by_model()
    cache_info = tracker.get_savings_from_cache()
    routing_info = tracker.get_savings_from_routing()

    print("\n--- Verification ---")
    print(f"  Total cost: ${total:.4f}")
    assert total > 0, "FAIL: Total cost should be > 0"
    print(f"  PASS: Total cost is positive")

    print(f"  Models used: {list(by_model.keys())}")
    assert len(by_model) >= 2, "FAIL: Should have multiple models"
    print(f"  PASS: Multiple models tracked")

    print(f"  Cache hits: {cache_info['cache_hits']}, Savings: ${cache_info['estimated_savings']:.4f}")
    assert cache_info['cache_hits'] > 0, "FAIL: Should have cache hits"
    print(f"  PASS: Cache savings tracked")

    print(f"  Routing savings: ${routing_info['savings']:.4f} ({routing_info['savings_pct']:.1f}%)")
    assert routing_info['savings'] > 0, "FAIL: Routing should save vs all-Sonnet"
    print(f"  PASS: Routing savings tracked")

    print("\n" + "=" * 60)
    print("All cost tracker tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    self_test()
