"""
M18 — Claude-as-Judge Scorer (Solution)
==========================================
Uses a SEPARATE Claude call to evaluate response quality on a rubric.
Supports mock mode for testing without API calls.
"""

import json
import os
import re

# Try to import anthropic — not required for mock mode
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for a UCC filing research agent.
Your job is to score the agent's response on three dimensions.

Score each dimension from 0 to 5:

**Accuracy (0-5)**:
- 5: All facts are correct, all filing numbers accurate, all entity names exact
- 3: Mostly correct with minor errors (wrong date, slightly off collateral description)
- 1: Significant factual errors (wrong filings, wrong entities)
- 0: Completely wrong or fabricated information

**Completeness (0-5)**:
- 5: Covers all expected filings, entities, and key facts; nothing missing
- 3: Covers most expected items but misses 1-2 key details
- 1: Major omissions — misses most expected filings or key facts
- 0: Almost nothing relevant included

**Clarity (0-5)**:
- 5: Well-structured, easy to read, professional formatting
- 3: Readable but could be better organized
- 1: Confusing, poorly structured, hard to extract key information
- 0: Incoherent or unreadable

Respond with ONLY a JSON object (no markdown, no explanation outside the JSON):
{
    "accuracy": <0-5>,
    "completeness": <0-5>,
    "clarity": <0-5>,
    "reasoning": "<1-2 sentence explanation of your scores>"
}"""


def score_with_judge(
    query: str,
    response: str,
    expected: dict,
    mock_mode: bool = True,
) -> dict:
    """
    Use Claude to evaluate response quality on a 3-dimension rubric.

    Returns:
        {"score": 0.0-1.0, "accuracy": 0-5, "completeness": 0-5, "clarity": 0-5, "reasoning": str}
    """
    if mock_mode:
        return _mock_judge_score(query, response, expected)

    # Live mode: call Claude
    if not HAS_ANTHROPIC:
        return {
            "score": 0.0,
            "accuracy": 0,
            "completeness": 0,
            "clarity": 0,
            "reasoning": "Error: anthropic package not installed. Run: pip install anthropic",
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "score": 0.0,
            "accuracy": 0,
            "completeness": 0,
            "clarity": 0,
            "reasoning": "Error: ANTHROPIC_API_KEY not set in environment.",
        }

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build the judge prompt with context
        expected_str = json.dumps(expected, indent=2)
        user_prompt = (
            f"## User Query\n{query}\n\n"
            f"## Agent Response\n{response}\n\n"
            f"## Expected Output (ground truth)\n{expected_str}\n\n"
            f"Score the agent's response using the rubric. "
            f"Respond with ONLY a JSON object."
        )

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Parse the response
        response_text = message.content[0].text.strip()
        # Try to extract JSON from the response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
        else:
            scores = json.loads(response_text)

        accuracy = int(scores.get("accuracy", 0))
        completeness = int(scores.get("completeness", 0))
        clarity = int(scores.get("clarity", 0))
        reasoning = scores.get("reasoning", "No reasoning provided.")

        # Clamp values to 0-5
        accuracy = max(0, min(5, accuracy))
        completeness = max(0, min(5, completeness))
        clarity = max(0, min(5, clarity))

        overall = (accuracy + completeness + clarity) / 15.0

        return {
            "score": round(overall, 3),
            "accuracy": accuracy,
            "completeness": completeness,
            "clarity": clarity,
            "reasoning": reasoning,
        }

    except Exception as e:
        return {
            "score": 0.0,
            "accuracy": 0,
            "completeness": 0,
            "clarity": 0,
            "reasoning": f"Error calling Claude judge: {str(e)}",
        }


def _mock_judge_score(query: str, response: str, expected: dict) -> dict:
    """
    Return a mock judge score using simple heuristics.
    """
    # Heuristic 1: Accuracy — check if expected filings appear in response
    expected_filings = expected.get("expected_filings", [])
    if expected_filings:
        filings_found = sum(1 for f in expected_filings if f in response)
        accuracy_ratio = filings_found / len(expected_filings)
    else:
        # If no filings expected, check that response doesn't contain filing numbers
        has_filings = bool(re.search(r"UCC-\d{4}-[A-Z]{2}-\d{7}", response))
        accuracy_ratio = 0.0 if has_filings else 1.0

    accuracy = round(accuracy_ratio * 5)

    # Heuristic 2: Completeness — check key_facts
    key_facts = expected.get("key_facts", [])
    if key_facts:
        facts_found = sum(
            1 for fact in key_facts if fact.lower() in response.lower()
        )
        completeness_ratio = facts_found / len(key_facts)
    else:
        completeness_ratio = 1.0 if len(response) > 20 else 0.5

    completeness = round(completeness_ratio * 5)

    # Heuristic 3: Clarity — check response length and structure
    if len(response) > 100 and ("\n" in response or "**" in response or "-" in response):
        clarity = 5
    elif len(response) > 50:
        clarity = 4
    elif len(response) > 20:
        clarity = 3
    else:
        clarity = 1

    # Clamp values
    accuracy = max(0, min(5, accuracy))
    completeness = max(0, min(5, completeness))
    clarity = max(0, min(5, clarity))

    overall = (accuracy + completeness + clarity) / 15.0

    reasoning = (
        f"Mock judge: accuracy based on {len(expected_filings)} expected filings, "
        f"completeness based on {len(key_facts)} key facts, "
        f"clarity based on response structure."
    )

    return {
        "score": round(overall, 3),
        "accuracy": accuracy,
        "completeness": completeness,
        "clarity": clarity,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Claude-as-Judge Scorer — Self-Test")
    print("=" * 50)

    query = "Find all UCC filings for Acme Corporation in New York."
    response_good = (
        "I found 2 UCC filings for Acme Corporation in New York:\n\n"
        "1. **UCC-2024-NY-0012847** (UCC-1, Active)\n"
        "   - Secured Party: Atlantic Capital Partners\n"
        "   - Collateral: All accounts receivable, inventory, equipment\n\n"
        "2. **UCC-2024-NY-0015921** (UCC-1, Active)\n"
        "   - Secured Party: Citibank N.A.\n"
        "   - Collateral: Deposit accounts, investment property"
    )
    response_bad = "I don't know."
    expected = {
        "expected_filings": ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"],
        "expected_entity": "Acme Corporation",
        "key_facts": ["Atlantic Capital Partners", "Citibank N.A.", "accounts receivable"],
    }

    # Test 1: Good response
    result1 = score_with_judge(query, response_good, expected, mock_mode=True)
    print(f"\nTest 1 — Good response (mock mode):")
    print(f"  Score: {result1['score']:.2f}")
    print(f"  Accuracy: {result1['accuracy']}/5")
    print(f"  Completeness: {result1['completeness']}/5")
    print(f"  Clarity: {result1['clarity']}/5")
    print(f"  Reasoning: {result1['reasoning']}")
    assert result1["score"] >= 0.5

    # Test 2: Bad response
    result2 = score_with_judge(query, response_bad, expected, mock_mode=True)
    print(f"\nTest 2 — Bad response (mock mode):")
    print(f"  Score: {result2['score']:.2f}")
    print(f"  Accuracy: {result2['accuracy']}/5")
    print(f"  Completeness: {result2['completeness']}/5")
    print(f"  Clarity: {result2['clarity']}/5")
    assert result2["score"] < result1["score"]

    # Test 3: Live mode
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and HAS_ANTHROPIC:
        print(f"\nTest 3 — Good response (LIVE mode):")
        result3 = score_with_judge(query, response_good, expected, mock_mode=False)
        print(f"  Score: {result3['score']:.2f}")
        print(f"  Accuracy: {result3['accuracy']}/5")
        print(f"  Completeness: {result3['completeness']}/5")
        print(f"  Clarity: {result3['clarity']}/5")
        print(f"  Reasoning: {result3['reasoning']}")

        # Test 4 exists because Test 3 alone proves nothing about a judge. It
        # only ever shows the judge APPROVING a good answer, and a judge that
        # returned 5/5 unconditionally would pass it. The property that makes an
        # evaluator worth having is that it can also REJECT -- so score the bad
        # answer live too, and assert the gap.
        print(f"\nTest 4 — Bad response (LIVE mode):")
        result4 = score_with_judge(query, response_bad, expected, mock_mode=False)
        print(f"  Score: {result4['score']:.2f}")
        print(f"  Accuracy: {result4['accuracy']}/5")
        print(f"  Reasoning: {result4['reasoning']}")
        assert result4["score"] < result3["score"], (
            "the live judge did not rank the bad answer below the good one — "
            "an evaluator that cannot discriminate is worse than none, because "
            "it produces a number you will trust"
        )

    print("\n" + "=" * 50)
    print("All self-tests passed!")
