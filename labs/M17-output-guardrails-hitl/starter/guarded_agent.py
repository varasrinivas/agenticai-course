"""
M17: Guarded Agent — Starter
Composes all four guardrails (output validator, cost controller, circuit breaker,
HITL gate) into a single protected agent runner.
"""
import json
import sys
import os

# Add parent directory so we can import sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from output_validator import validate_output
from cost_controller import CostController
from circuit_breaker import CircuitBreaker, CircuitState
from hitl_gate import HITLGate


# ── Mock Agent Responses ────────────────────────────────────
# Simulates different agent outputs for testing (no real API calls needed)
MOCK_RESPONSES = {
    "clean_query": {
        "entity": "Acme Corporation",
        "filing_number": "UCC-2024-CA-0001234",
        "response": "Acme Corporation has 3 active UCC filings in California. The most recent was filed on 2024-01-15.",
        "confidence": 0.95,
        "input_tokens": 500,
        "output_tokens": 200,
    },
    "low_confidence": {
        "entity": "XYZ Holdings",
        "filing_number": "UCC-2024-NY-0005678",
        "response": "I think XYZ Holdings might have some filings, but I'm not sure about the exact count.",
        "confidence": 0.55,
        "input_tokens": 600,
        "output_tokens": 250,
    },
    "medium_confidence": {
        "entity": "Smith Industries",
        "filing_number": "UCC-2024-TX-0009012",
        "response": "Smith Industries has filings in Texas matching the search criteria.",
        "confidence": 0.82,
        "input_tokens": 550,
        "output_tokens": 220,
    },
    "pii_leak": {
        "entity": "John Doe",
        "filing_number": "UCC-2024-FL-0003456",
        "response": "John Doe (SSN: 123-45-6789) has 2 filings. Contact: john@example.com or 555-867-5309.",
        "confidence": 0.90,
        "input_tokens": 700,
        "output_tokens": 300,
    },
    "expensive_query": {
        "entity": "MegaCorp International",
        "filing_number": "UCC-2024-WA-0007890",
        "response": "MegaCorp International has extensive filing history across 12 states.",
        "confidence": 0.92,
        "input_tokens": 80000,
        "output_tokens": 30000,
    },
}

EXPECTED_FIELDS = ["entity", "filing_number", "response", "confidence"]


def mock_agent_call(query_type: str) -> dict:
    """Simulate an agent API call returning predefined responses."""
    if query_type in MOCK_RESPONSES:
        return MOCK_RESPONSES[query_type]
    return MOCK_RESPONSES["clean_query"]


class GuardedAgent:
    """Agent runner with all four guardrails composed together."""

    def __init__(self, budget_limit: float = 0.50, failure_threshold: int = 3):
        """
        Args:
            budget_limit: Max cost per request session in dollars.
            failure_threshold: Consecutive failures before circuit breaker trips.
        """
        # TODO 1: Initialize all four guardrail components:
        #   self.cost_controller = CostController(budget_limit)
        #   self.circuit_breaker = CircuitBreaker(failure_threshold, reset_timeout=60.0)
        #   self.hitl_gate = HITLGate(auto_mode=True)
        #   self.results = []
        pass

    def run_guarded(self, query_type: str) -> dict:
        """
        Run an agent call with all guardrails active.

        Pipeline:
        1. Check circuit breaker — is the agent halted?
        2. Check budget — can we afford another call?
        3. Call the agent (mocked)
        4. Track the cost
        5. Validate the output
        6. Route by confidence through HITL gate
        7. Return the guarded result

        Args:
            query_type: Key into MOCK_RESPONSES dict.

        Returns:
            {
                "status": "allowed" | "blocked" | "denied" | "reviewed",
                "query_type": str,
                "reason": str,
                "agent_output": dict or None,
                "guardrail_details": {
                    "circuit_breaker": dict,
                    "cost": dict,
                    "validation": dict,
                    "hitl": dict or None
                }
            }
        """
        result = {
            "status": "allowed",
            "query_type": query_type,
            "reason": "",
            "agent_output": None,
            "guardrail_details": {
                "circuit_breaker": {},
                "cost": {},
                "validation": {},
                "hitl": None,
            },
        }

        # TODO 2: Check circuit breaker — if can_execute() is False, set status="blocked",
        # reason to explain circuit is open, and return early.

        # TODO 3: Get mock agent response. Check budget with would_exceed() using
        # the response's input_tokens and output_tokens. If would exceed, set
        # status="blocked", reason about budget, and return early.

        # TODO 4: Track the token usage with cost_controller.track_usage().

        # TODO 5: Validate the output with validate_output() using EXPECTED_FIELDS.
        # If validation fails (PII found or missing fields), record the failure
        # with circuit_breaker.record_failure() and set status="blocked".

        # TODO 6: Route through HITL gate using the response's confidence.
        # If HITL returns final_action="deny", set status="denied".
        # If HITL returns final_action="approve" and human_reviewed=True, set status="reviewed".
        # Otherwise status="allowed".

        # TODO 7: Record success with circuit_breaker.record_success() for non-blocked results.

        # TODO 8: Append result to self.results and return it.

        return result

    def get_summary(self) -> dict:
        """Return a summary of all guarded agent runs."""
        return {
            "total_runs": len(getattr(self, "results", [])),
            "results": getattr(self, "results", []),
            "cost_summary": getattr(self, "cost_controller", CostController()).get_summary(),
            "circuit_breaker_state": getattr(self, "circuit_breaker", CircuitBreaker()).get_state(),
            "hitl_stats": getattr(self, "hitl_gate", HITLGate()).get_stats(),
        }


# ── Self-Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("M17 Guarded Agent — Self-Test")
    print("=" * 60)

    agent = GuardedAgent(budget_limit=0.50, failure_threshold=3)

    # Scenario 1: Clean query — should be allowed
    print("\n" + "-" * 50)
    print("Scenario 1: Clean Query")
    print("-" * 50)
    result = agent.run_guarded("clean_query")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")

    # Scenario 2: Expensive query — should be blocked by budget
    print("\n" + "-" * 50)
    print("Scenario 2: Expensive Query (budget check)")
    print("-" * 50)
    result = agent.run_guarded("expensive_query")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")

    # Scenario 3: PII leak — should be blocked by validator
    print("\n" + "-" * 50)
    print("Scenario 3: PII Leak (output validation)")
    print("-" * 50)
    result = agent.run_guarded("pii_leak")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")

    # Scenario 4: Low confidence — should be auto-denied
    print("\n" + "-" * 50)
    print("Scenario 4: Low Confidence (auto-deny)")
    print("-" * 50)
    result = agent.run_guarded("low_confidence")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")

    # Scenario 5: Medium confidence — should go through HITL review
    print("\n" + "-" * 50)
    print("Scenario 5: Medium Confidence (HITL review)")
    print("-" * 50)
    result = agent.run_guarded("medium_confidence")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")

    # Final summary
    summary = agent.get_summary()
    print(f"\n{'=' * 60}")
    print("Guarded Agent Summary")
    print(f"{'=' * 60}")
    print(f"  Total runs: {summary['total_runs']}")
    print(f"  Cost: ${summary['cost_summary']['total_cost']:.6f}")
    print(f"  Circuit breaker: {summary['circuit_breaker_state']['state']}")
    print(f"  HITL decisions: {summary['hitl_stats']['total_decisions']}")

    print("\n" + "=" * 60)
    print("Self-test complete. Fill in TODOs to see all guardrails working together.")
    print("=" * 60)
