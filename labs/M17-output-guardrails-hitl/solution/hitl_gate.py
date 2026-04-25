"""
M17: HITL Approval Gate — Solution
Routes decisions by confidence level: auto-approve, human review, or auto-deny.
Domain context: UCC entity matching where partial matches need human verification.
"""
import sys


# ── Confidence Thresholds ───────────────────────────────────
AUTO_APPROVE_THRESHOLD = 0.9   # > 90% confidence -> auto-approve
HITL_REVIEW_THRESHOLD = 0.7   # 70-90% confidence -> human review required
# < 70% confidence -> auto-deny


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
    entity = context.get("entity", "unknown")

    if confidence > AUTO_APPROVE_THRESHOLD:
        return {
            "action": "approve",
            "reason": f"High confidence ({confidence:.0%}) match for '{entity}' — auto-approved",
            "confidence": confidence,
            "requires_human": False,
        }
    elif confidence >= HITL_REVIEW_THRESHOLD:
        return {
            "action": "review",
            "reason": f"Medium confidence ({confidence:.0%}) match for '{entity}' — requires human review",
            "confidence": confidence,
            "requires_human": True,
        }
    else:
        return {
            "action": "deny",
            "reason": f"Low confidence ({confidence:.0%}) match for '{entity}' — auto-denied",
            "confidence": confidence,
            "requires_human": False,
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
    if auto_mode:
        return {
            "approved": True,
            "reviewer": "auto-test",
            "notes": "Auto-approved in test mode",
        }

    # Interactive mode — prompt the human reviewer
    print("\n" + "=" * 40)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 40)
    for key, value in context.items():
        print(f"  {key}: {value}")
    print("=" * 40)

    try:
        response = input("Approve this match? (y/n): ").strip().lower()
        notes = input("Reviewer notes (optional): ").strip()
    except (EOFError, KeyboardInterrupt):
        response = "n"
        notes = "Review cancelled"

    return {
        "approved": response in ("y", "yes"),
        "reviewer": "human",
        "notes": notes or "No notes provided",
    }


class HITLGate:
    """Manages the human-in-the-loop review queue and decision tracking."""

    def __init__(self, auto_mode: bool = True):
        """
        Args:
            auto_mode: If True, simulate human approvals automatically (for testing).
        """
        self.auto_mode = auto_mode
        self.decisions = []
        self.review_queue = []
        self.stats = {"approved": 0, "denied": 0, "reviewed": 0}

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
                "routed_action": str,
                "confidence": float,
                "human_reviewed": bool,
                "review_result": dict or None
            }
        """
        routing = route_decision(confidence, context)
        review_result = None
        human_reviewed = False

        if routing["action"] == "approve":
            final_action = "approve"
            self.stats["approved"] += 1
        elif routing["action"] == "deny":
            final_action = "deny"
            self.stats["denied"] += 1
        else:
            # Review needed
            review_result = simulate_human_review(context, self.auto_mode)
            human_reviewed = True
            self.stats["reviewed"] += 1
            if review_result["approved"]:
                final_action = "approve"
                self.stats["approved"] += 1
            else:
                final_action = "deny"
                self.stats["denied"] += 1

        decision = {
            "final_action": final_action,
            "routed_action": routing["action"],
            "confidence": confidence,
            "human_reviewed": human_reviewed,
            "review_result": review_result,
        }
        self.decisions.append(decision)

        return decision

    def get_stats(self) -> dict:
        """Return summary statistics for all decisions processed."""
        return {
            "total_decisions": len(self.decisions),
            "approved": self.stats["approved"],
            "denied": self.stats["denied"],
            "human_reviewed": self.stats["reviewed"],
            "decisions": self.decisions,
        }

    def get_pending_reviews(self) -> list:
        """Return any pending reviews (not yet resolved)."""
        return self.review_queue


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
    print("All tests complete.")
    print("=" * 60)
