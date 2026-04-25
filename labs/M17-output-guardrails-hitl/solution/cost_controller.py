"""
M17: Cost Controller — Solution
Tracks token usage costs and enforces per-request budget limits.
Uses Claude Sonnet pricing: $3.00/1M input tokens, $15.00/1M output tokens.
"""


class CostController:
    """Tracks API call costs and enforces a per-request budget cap."""

    # Claude Sonnet pricing (per token)
    COST_PER_INPUT_TOKEN = 3.00 / 1_000_000    # $3.00 per 1M input tokens
    COST_PER_OUTPUT_TOKEN = 15.00 / 1_000_000  # $15.00 per 1M output tokens

    def __init__(self, budget_limit: float = 0.50):
        """
        Args:
            budget_limit: Maximum allowed cost per request in dollars (default $0.50).
        """
        self.budget_limit = budget_limit
        self.current_cost = 0.0
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def track_usage(self, input_tokens: int, output_tokens: int) -> dict:
        """
        Record token usage from an API call and update running cost.

        Args:
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens consumed.

        Returns:
            {
                "call_cost": float,
                "cumulative_cost": float,
                "budget_remaining": float,
                "budget_exceeded": bool
            }
        """
        call_cost = (input_tokens * self.COST_PER_INPUT_TOKEN) + (output_tokens * self.COST_PER_OUTPUT_TOKEN)
        self.current_cost += call_cost
        self.call_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        remaining = self.budget_limit - self.current_cost

        return {
            "call_cost": round(call_cost, 6),
            "cumulative_cost": round(self.current_cost, 6),
            "budget_remaining": round(remaining, 6),
            "budget_exceeded": self.current_cost > self.budget_limit,
        }

    def check_budget(self) -> dict:
        """
        Check current budget status without making a new call.

        Returns:
            {
                "current_cost": float,
                "budget_limit": float,
                "budget_remaining": float,
                "budget_exceeded": bool,
                "utilization_pct": float
            }
        """
        remaining = self.budget_limit - self.current_cost
        utilization = (self.current_cost / self.budget_limit * 100) if self.budget_limit > 0 else 0.0

        return {
            "current_cost": round(self.current_cost, 6),
            "budget_limit": self.budget_limit,
            "budget_remaining": round(remaining, 6),
            "budget_exceeded": self.current_cost > self.budget_limit,
            "utilization_pct": round(utilization, 1),
        }

    def would_exceed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> dict:
        """
        Pre-check: would a call with these token counts exceed the budget?

        Args:
            estimated_input_tokens: Expected input tokens for next call.
            estimated_output_tokens: Expected output tokens for next call.

        Returns:
            {
                "estimated_cost": float,
                "would_exceed": bool,
                "budget_after": float
            }
        """
        estimated_cost = (
            estimated_input_tokens * self.COST_PER_INPUT_TOKEN
            + estimated_output_tokens * self.COST_PER_OUTPUT_TOKEN
        )
        budget_after = self.budget_limit - self.current_cost - estimated_cost

        return {
            "estimated_cost": round(estimated_cost, 6),
            "would_exceed": (self.current_cost + estimated_cost) > self.budget_limit,
            "budget_after": round(budget_after, 6),
        }

    def reset(self):
        """Reset all counters for a new request."""
        self.current_cost = 0.0
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def get_summary(self) -> dict:
        """Return a summary of all usage tracking."""
        return {
            "total_cost": round(self.current_cost, 6),
            "budget_limit": self.budget_limit,
            "call_count": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }


# ── Self-Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("M17 Cost Controller — Self-Test")
    print("=" * 60)

    controller = CostController(budget_limit=0.50)

    # Simulate 5 API calls with increasing token counts
    calls = [
        (1000, 500),    # Small call
        (5000, 2000),   # Medium call
        (10000, 5000),  # Larger call
        (20000, 8000),  # Big call
        (50000, 20000), # Very big call — should exceed budget
    ]

    for i, (inp, out) in enumerate(calls, 1):
        # Pre-check
        pre = controller.would_exceed(inp, out)
        print(f"\nCall {i}: {inp} input + {out} output tokens")
        print(f"  Pre-check — estimated cost: ${pre['estimated_cost']:.6f}, would exceed: {pre['would_exceed']}")

        if pre["would_exceed"]:
            print(f"  BLOCKED — would exceed budget (${pre['budget_after']:.6f} remaining after)")
            continue

        # Track the usage
        result = controller.track_usage(inp, out)
        print(f"  Call cost: ${result['call_cost']:.6f}")
        print(f"  Cumulative: ${result['cumulative_cost']:.6f}")
        print(f"  Remaining: ${result['budget_remaining']:.6f}")
        print(f"  Exceeded: {result['budget_exceeded']}")

    # Final summary
    budget = controller.check_budget()
    print(f"\n{'=' * 60}")
    print(f"Budget Summary:")
    print(f"  Total cost: ${budget['current_cost']:.6f}")
    print(f"  Budget limit: ${budget['budget_limit']:.2f}")
    print(f"  Utilization: {budget['utilization_pct']:.1f}%")
    print(f"  Exceeded: {budget['budget_exceeded']}")

    summary = controller.get_summary()
    print(f"  Total calls: {summary['call_count']}")
    print(f"  Total tokens: {summary['total_input_tokens']} in / {summary['total_output_tokens']} out")

    print("\n" + "=" * 60)
    print("All tests complete.")
    print("=" * 60)
