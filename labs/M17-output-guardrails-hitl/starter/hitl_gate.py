"""
M17: HITL Approval Gate — Starter
Routes decisions by confidence level: auto-approve, human review, or auto-deny.
Domain context: UCC entity matching where partial matches need human verification.
"""
import sys


# ── Confidence Thresholds ───────────────────────────────────
AUTO_APPROVE_THRESHOLD = 0.9   # > 90% confidence → auto-approve
HITL_REVIEW_THRESHOLD = 0.7   # 70-90% confidence → human review required
# < 70% confidence → auto-deny


def route_decision(confidence: float, context: dict) -> dict:
    """
    Route a decision based on confidence score.

    Args:
        confidence: Float 0.0-1.0 representing match confidence.
        context: Dict with details about the match (entity, filing, etc.).

    Returns:
        {
            "action": "approve" | "review" | "deny",
            "reason": str,
            "confidence": float,
            "requires_human": bool
        }
    """
    # TODO 1: Implement confidence-based routing:
    # - confidence > AUTO_APPROVE_THRESHOLD → action="approve", requires_human=False
    # - confidence >= HITL_REVIEW_THRESHOLD → action="review", requires_human=True
    # - confidence < HITL_REVIEW_THRESHOLD → action="deny", requires_human=False
    # Include a descriptive reason for each case.
    return {
        "action": "review",
        "reason": "Not yet implemented",
        "confidence": confidence,
        "requires_human": True,
    }


def simulate_human_review(context: dict, auto_mode: bool = True) -> dict:
    """
    Simulate human review of a decision.

    In auto_mode (testing): automatically approves.
    In interactive mode: prompts via stdin.

    Args:
        context: The decision context to present to the human.
        auto_mode: If True, auto-approve without prompting (for tests).

    Returns:
        {
            "approved": bool,
            "reviewer": str,
            "notes": str
        }
    """
    # TODO 2: Implement human review simulation:
    # If auto_mode is True:
    #   Return approved=True, reviewer="auto-test", notes="Auto-approved in test mode"
    # If auto_mode is False:
    #   Print the context details to the console.
    #   Prompt the user: "Approve this match? (y/n): "
    #   Read input from stdin.
    #   Return approved based on input, reviewer="human", notes from user.
    return {
        "approved": True,
        "reviewer": "auto-test",
        "notes": "Not yet implemented",
    }


class HITLGate:
    """Manages the human-in-the-loop review queue and decision tracking."""

    def __init__(self, auto_mode: bool = True):
        """
        Args:
            auto_mode: If True, simulate human approvals automatically (for testing).
        """
        self.auto_mode = auto_mode
        # TODO 3: Initialize tracking state:
        #   self.decisions = []         # log of all decisions
        #   self.review_queue = []      # pending reviews
        #   self.stats = {"approved": 0, "denied": 0, "reviewed": 0}

    def process(self, confidence: float, context: dict) -> dict:
        """
        Process a decision through the HITL gate.

        1. Route by confidence
        2. If review needed, run human review
        3. Log the decision
        4. Return final result

        Args:
            confidence: Match confidence 0.0-1.0.
            context: Decision details.

        Returns:
            {
                "final_action": "approve" | "deny",
                "routed_action": str,  # original routing decision
                "confidence": float,
                "human_reviewed": bool,
                "review_result": dict or None
            }
        """
        # TODO 4: Use route_decision() to get initial routing.
        # If action is "review", call simulate_human_review().
        #   The final_action depends on whether the human approved.
        # If action is "approve", final_action = "approve".
        # If action is "deny", final_action = "deny".
        # Log to self.decisions and update self.stats.
        routing = route_decision(confidence, context)

        return {
            "final_action": routing["action"] if routing["action"] != "review" else "approve",
            "routed_action": routing["action"],
            "confidence": confidence,
            "human_reviewed": False,
            "review_result": None,
        }

    def get_stats(self) -> dict:
        """Return summary statistics for all decisions processed."""
        # TODO 5: Return stats dict with counts and decision log length.
        return {
            "total_decisions": 0,
            "approved": 0,
            "denied": 0,
            "human_reviewed": 0,
            "decisions": [],
        }

    def get_pending_reviews(self) -> list:
        """Return any pending reviews (not yet resolved)."""
        # TODO 6: Return self.review_queue.
        return []


# ── Self-Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("M17 HITL Approval Gate — Self-Test")
    print("=" * 60)

    gate = HITLGate(auto_mode=True)

    # Test scenarios with different confidence levels
    test_cases = [
        (0.95, {"entity": "Acme Corp", "match": "Acme Corporation", "filing": "UCC-2024-CA-0001234"}),
        (0.85, {"entity": "Smith Holdings", "match": "Smith Holding Co", "filing": "UCC-2024-NY-0005678"}),
        (0.75, {"entity": "Doe Industries", "match": "Doe Industrial LLC", "filing": "UCC-2024-TX-0009012"}),
        (0.60, {"entity": "XYZ Corp", "match": "XYZ Company Inc", "filing": "UCC-2024-FL-0003456"}),
        (0.45, {"entity": "Unknown LLC", "match": "Unknown Limited", "filing": "UCC-2024-WA-0007890"}),
    ]

    for confidence, context in test_cases:
        result = gate.process(confidence, context)
        print(f"\nConfidence {confidence:.0%} — {context['entity']} vs {context['match']}:")
        print(f"  Routed: {result['routed_action']}")
        print(f"  Final:  {result['final_action']}")
        print(f"  Human reviewed: {result['human_reviewed']}")
        if result["review_result"]:
            print(f"  Review: {result['review_result']}")

    # Print stats
    stats = gate.get_stats()
    print(f"\n{'=' * 60}")
    print(f"HITL Gate Stats:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Approved: {stats['approved']}")
    print(f"  Denied: {stats['denied']}")
    print(f"  Human reviewed: {stats['human_reviewed']}")

    print("\n" + "=" * 60)
    print("Self-test complete. Fill in TODOs for correct routing behavior.")
    print("=" * 60)
