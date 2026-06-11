"""
M17 Lab: Output Guardrails & HITL — SOLUTION
=============================================
Run: python output_pipeline.py
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ── Part 1: Hallucination Detector (Mistral-as-Judge) ────────
HALLUCINATION_PROMPT = """You are a fact-checking judge. Compare the response
against the source documents. For each factual claim, classify it as:
- "supported": Directly backed by sources
- "unsupported": NOT in sources (possible hallucination)
- "contradicted": CONTRADICTS sources (definite error)

Respond with ONLY JSON:
{{"claims": [{{"text": "claim", "status": "supported|unsupported|contradicted"}}],
 "overall": "pass|flag|block", "unsupported_count": 0}}

Sources:

{sources}


Response to check:

{response}
"""


def check_hallucination(response_text: str, source_docs: list[str]) -> dict:
    """Verify an agent response against source documents."""
    sources = "\n---\n".join(source_docs)
    try:
        result = client.chat.completions.create(
            model="mistral",
            messages=[{
                "role": "user",
                "content": HALLUCINATION_PROMPT.format(
                    sources=sources, response=response_text
                ),
            }],
        )
        raw = (result.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)

        claims = parsed.get("claims", [])
        known = {"supported", "unsupported", "contradicted"}
        # Unknown/invented statuses count as unsupported
        for c in claims:
            if c.get("status") not in known:
                c["status"] = "unsupported"

        contradicted = [c for c in claims if c["status"] == "contradicted"]
        unsupported = [c for c in claims if c["status"] == "unsupported"]

        if contradicted:
            return {"result": "block",
                    "reason": f"{len(contradicted)} contradicted claim(s)",
                    "claims": claims}
        if len(unsupported) >= 2:
            return {"result": "flag",
                    "reason": f"{len(unsupported)} unsupported claim(s)",
                    "claims": claims}
        return {"result": "pass", "claims": claims}
    except Exception as e:
        # Quality gates degrade to HUMAN REVIEW, not silently to pass
        return {"result": "flag", "reason": f"Check failed: {e}", "claims": []}


# ── Part 2: Cost Tracker with Budget Enforcement ─────────────
@dataclass
class CostTracker:
    """Track token usage and enforce a per-request budget."""

    budget_dollars: float = 0.50
    input_tokens: int = 0
    output_tokens: int = 0

    INPUT_PRICE = 2.0 / 1_000_000    # ~$2/M input tokens (cloud)
    OUTPUT_PRICE = 6.0 / 1_000_000   # ~$6/M output tokens (cloud)

    @property
    def total_cost(self) -> float:
        return (self.input_tokens * self.INPUT_PRICE +
                self.output_tokens * self.OUTPUT_PRICE)

    @property
    def budget_remaining(self) -> float:
        return self.budget_dollars - self.total_cost

    def record_usage(self, input_toks: int, output_toks: int):
        self.input_tokens += input_toks
        self.output_tokens += output_toks

    def can_afford(self, estimated_input: int = 5000,
                   estimated_output: int = 1000) -> bool:
        """Pre-flight check BEFORE the next call."""
        estimated_cost = (estimated_input * self.INPUT_PRICE +
                          estimated_output * self.OUTPUT_PRICE)
        return self.total_cost + estimated_cost <= self.budget_dollars

    def summary(self) -> str:
        return (f"Tokens: {self.input_tokens} in / {self.output_tokens} out "
                f"| Cost: ${self.total_cost:.4f} / ${self.budget_dollars:.2f}")


# ── Part 3: Circuit Breaker ──────────────────────────────────
class BreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: float = 5.0
    state: BreakerState = field(default=BreakerState.CLOSED)
    failure_count: int = field(default=0)
    opened_at: float = field(default=0.0)

    def can_execute(self) -> bool:
        if self.state == BreakerState.CLOSED:
            return True
        if self.state == BreakerState.OPEN:
            if time.time() - self.opened_at >= self.cooldown_seconds:
                self.state = BreakerState.HALF_OPEN
                return True  # exactly one test request
            return False
        return False  # HALF_OPEN: a test request is already in flight

    def record_success(self):
        if self.state == BreakerState.HALF_OPEN:
            self.state = BreakerState.CLOSED
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        if self.state == BreakerState.HALF_OPEN:
            self.state = BreakerState.OPEN
            self.opened_at = time.time()
            self.cooldown_seconds *= 2  # exponential backoff on failed test
        elif self.failure_count >= self.failure_threshold:
            self.state = BreakerState.OPEN
            self.opened_at = time.time()


# ── Part 4: Approval Gate ────────────────────────────────────
def approval_gate(action: str, context: str, auto_approve: bool = False) -> dict:
    """Pause for human approval before irreversible actions."""
    print(f"\n{'=' * 50}")
    print("APPROVAL REQUIRED")
    print(f"Action: {action}")
    print(f"Context: {context}")
    print(f"{'=' * 50}")

    if auto_approve:
        print("  [Auto-approved for testing]")
        return {"approved": True, "modified": False}

    response = input("Approve? (y/n/e to edit): ").strip().lower()
    if response == "y":
        return {"approved": True, "modified": False}
    elif response == "e":
        new_action = input("Enter modified action: ").strip()
        return {"approved": True, "modified": True, "new_action": new_action}
    return {"approved": False, "reason": "Human denied"}


# ── Test Suite ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("OUTPUT GUARDRAILS - TEST SUITE")
    print("=" * 60)

    source_docs = [
        "UCC Filing #2024-NY-0042: Filed March 22, 2024 by Acme Corp. "
        "Collateral: $2.3M in manufacturing equipment. Status: Active.",
        "Amendment filed April 10, 2024: Added collateral description "
        "for warehouse inventory valued at $890K.",
    ]

    print("\n" + "-" * 60)
    print("TEST 1: Hallucination Detection — Contradicted Claim")
    agent_response = (
        "The UCC filing was submitted on March 15, 2024 by Acme Corp "
        "for $2.3M in equipment collateral. An amendment was filed "
        "on April 10, 2024 adding $890K in warehouse inventory."
    )
    result = check_hallucination(agent_response, source_docs)
    print(f"  Result: {result['result']}")
    print(f"  Reason: {result.get('reason', 'All claims supported')}")
    for claim in result.get("claims", []):
        print(f"    [{claim.get('status')}] {str(claim.get('text'))[:70]}")

    print("\n" + "-" * 60)
    print("TEST 2: Hallucination Detection — All Supported")
    correct_response = (
        "The UCC filing was submitted on March 22, 2024 by Acme Corp "
        "for $2.3M in equipment collateral."
    )
    result2 = check_hallucination(correct_response, source_docs)
    print(f"  Result: {result2['result']}")

    print("\n" + "-" * 60)
    print("TEST 3: Cost Tracking & Budget Enforcement")
    tracker = CostTracker(budget_dollars=0.10)
    for i in range(5):
        if not tracker.can_afford(estimated_input=8000, estimated_output=2000):
            print(f"  Iteration {i + 1}: BUDGET EXCEEDED — {tracker.summary()}")
            break
        tracker.record_usage(input_toks=8000, output_toks=2000)
        print(f"  Iteration {i + 1}: {tracker.summary()}")

    print("\n" + "-" * 60)
    print("TEST 4: Circuit Breaker State Transitions")
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=2)

    actions = [
        ("success", "Normal request 1"),
        ("failure", "API error 1"),
        ("failure", "API error 2"),
        ("failure", "API error 3 -> TRIPS"),
        ("blocked", "Request during OPEN state"),
    ]
    for action, label in actions:
        if not breaker.can_execute():
            print(f"  {label}: BLOCKED (state={breaker.state.value})")
            continue
        if action == "success":
            breaker.record_success()
            print(f"  {label}: OK (state={breaker.state.value})")
        else:
            breaker.record_failure()
            print(f"  {label}: FAIL (state={breaker.state.value}, "
                  f"failures={breaker.failure_count}/{breaker.failure_threshold})")

    print(f"  Waiting {breaker.cooldown_seconds}s for cooldown...")
    time.sleep(breaker.cooldown_seconds + 0.1)
    can_test = breaker.can_execute()
    print(f"  Half-open test: can_execute={can_test} (state={breaker.state.value})")
    breaker.record_success()
    print(f"  Test passed -> state={breaker.state.value}")

    print("\n" + "-" * 60)
    print("TEST 5: Approval Gate (auto-approved for testing)")
    gate_result = approval_gate(
        action="Send $450 refund to Order #12345",
        context="Customer received damaged item, within return window",
        auto_approve=True,
    )
    print(f"  Result: {gate_result}")
