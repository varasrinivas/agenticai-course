"""
M17: Guarded Agent — Solution
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
        self.cost_controller = CostController(budget_limit)
        self.circuit_breaker = CircuitBreaker(failure_threshold, reset_timeout=60.0)
        self.hitl_gate = HITLGate(auto_mode=True)
        self.results = []

    def run_guarded(self, query_type: str) -> dict:
        """
        Run an agent call with all guardrails active.

        Pipeline:
        1. Check circuit breaker
        2. Get agent response and check budget
        3. Track cost
        4. Validate output
        5. Route by confidence through HITL gate
        6. Return guarded result
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

        # Step 1: Check circuit breaker
        cb_state = self.circuit_breaker.get_state()
        result["guardrail_details"]["circuit_breaker"] = cb_state

        if not self.circuit_breaker.can_execute():
            result["status"] = "blocked"
            result["reason"] = f"Circuit breaker is {cb_state['state']} — {cb_state['failure_count']} consecutive failures"
            self.results.append(result)
            return result

        # Step 2: Get mock response and pre-check budget
        agent_response = mock_agent_call(query_type)
        budget_check = self.cost_controller.would_exceed(
            agent_response["input_tokens"],
            agent_response["output_tokens"],
        )
        result["guardrail_details"]["cost"] = budget_check

        if budget_check["would_exceed"]:
            result["status"] = "blocked"
            result["reason"] = (
                f"Budget exceeded — call would cost ${budget_check['estimated_cost']:.6f}, "
                f"only ${budget_check['budget_after'] + budget_check['estimated_cost']:.6f} remaining"
            )
            self.results.append(result)
            return result

        # Step 3: Track the cost
        cost_result = self.cost_controller.track_usage(
            agent_response["input_tokens"],
            agent_response["output_tokens"],
        )
        result["guardrail_details"]["cost"] = cost_result

        # Step 4: Validate output
        # Build the output dict without token fields
        output_for_validation = {
            k: v for k, v in agent_response.items()
            if k not in ("input_tokens", "output_tokens")
        }
        validation = validate_output(output_for_validation, EXPECTED_FIELDS)
        result["guardrail_details"]["validation"] = validation

        if not validation["valid"]:
            self.circuit_breaker.record_failure()
            result["status"] = "blocked"
            reasons = []
            if not validation["checks"]["structure"]["valid"]:
                reasons.append(f"missing fields: {validation['checks']['structure']['missing_fields']}")
            if validation["checks"]["pii"]["has_pii"]:
                reasons.append(f"PII detected: {validation['checks']['pii']['pii_types']}")
            result["reason"] = f"Output validation failed — {'; '.join(reasons)}"
            result["agent_output"] = validation["output"]
            self.results.append(result)
            return result

        # Step 5: Route by confidence through HITL gate
        confidence = agent_response.get("confidence", 0.5)
        # Apply hallucination penalty to confidence
        hallucination_penalty = validation["checks"]["hallucination"]["confidence_penalty"]
        adjusted_confidence = max(0.0, confidence - hallucination_penalty)

        hitl_result = self.hitl_gate.process(adjusted_confidence, output_for_validation)
        result["guardrail_details"]["hitl"] = hitl_result

        if hitl_result["final_action"] == "deny":
            result["status"] = "denied"
            result["reason"] = f"Low confidence ({adjusted_confidence:.0%}) — auto-denied by HITL gate"
        elif hitl_result["human_reviewed"]:
            result["status"] = "reviewed"
            result["reason"] = f"Medium confidence ({adjusted_confidence:.0%}) — approved after HITL review"
        else:
            result["status"] = "allowed"
            result["reason"] = f"High confidence ({adjusted_confidence:.0%}) — auto-approved"

        result["agent_output"] = validation["output"]

        # Step 6: Record success for non-denied results
        if result["status"] != "denied":
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()

        self.results.append(result)
        return result

    def get_summary(self) -> dict:
        """Return a summary of all guarded agent runs."""
        return {
            "total_runs": len(self.results),
            "results": self.results,
            "cost_summary": self.cost_controller.get_summary(),
            "circuit_breaker_state": self.circuit_breaker.get_state(),
            "hitl_stats": self.hitl_gate.get_stats(),
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
    print("All tests complete.")
    print("=" * 60)
