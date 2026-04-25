"""
M18 — Claude-as-Judge Scorer
===============================
Uses a SEPARATE Claude call to evaluate response quality on a rubric.
Supports mock mode for testing without API calls.

TODO: Implement the two functions below.
"""

import json
import os

# Try to import anthropic — not required for mock mode
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# The rubric prompt sent to the judge model.
# IMPORTANT: This is a SEPARATE call — the judge should NOT see the agent's system prompt.
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

    Args:
        query: The original user question
        response: The agent's response text
        expected: Dict with expected_filings, expected_entity, key_facts, etc.
        mock_mode: If True, return predetermined scores without API call

    Returns:
        {
            "score": float (0.0-1.0, normalized from the three 0-5 scores),
            "accuracy": int (0-5),
            "completeness": int (0-5),
            "clarity": int (0-5),
            "reasoning": str
        }

    TODO:
    1. If mock_mode is True, call _mock_judge_score() and return its result
    2. If mock_mode is False:
       a. Check that anthropic is installed and API key is set
       b. Build the judge prompt with the query, response, and expected data
       c. Call Claude (claude-sonnet-4-20250514) with JUDGE_SYSTEM_PROMPT
       d. Parse the JSON response
       e. Normalize: score = (accuracy + completeness + clarity) / 15.0
       f. Return the structured result
    3. Handle errors gracefully: if the API call fails, return a score of 0.0
       with error details in the reasoning field
    """
    # TODO: Implement judge scoring
    pass


def _mock_judge_score(query: str, response: str, expected: dict) -> dict:
    """
    Return a mock judge score for testing without API calls.

    TODO:
    1. Use simple heuristics to generate plausible scores:
       - Check if expected filing numbers appear in the response -> accuracy
       - Check if key_facts strings appear in the response -> completeness
       - Check response length and structure -> clarity
    2. Build and return the result dict with normalized score

    This doesn't need to be perfect — it just needs to produce reasonable
    scores so students can test the pipeline end-to-end.
    """
    # TODO: Implement mock scoring heuristics
    pass


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

    # Test 1: Good response in mock mode
    result1 = score_with_judge(query, response_good, expected, mock_mode=True)
    print(f"\nTest 1 — Good response (mock mode):")
    print(f"  Score: {result1['score']:.2f}")
    print(f"  Accuracy: {result1['accuracy']}/5")
    print(f"  Completeness: {result1['completeness']}/5")
    print(f"  Clarity: {result1['clarity']}/5")
    print(f"  Reasoning: {result1['reasoning']}")
    assert result1["score"] >= 0.5, f"Good response should score >= 0.5, got {result1['score']}"

    # Test 2: Bad response in mock mode
    result2 = score_with_judge(query, response_bad, expected, mock_mode=True)
    print(f"\nTest 2 — Bad response (mock mode):")
    print(f"  Score: {result2['score']:.2f}")
    print(f"  Accuracy: {result2['accuracy']}/5")
    print(f"  Completeness: {result2['completeness']}/5")
    print(f"  Clarity: {result2['clarity']}/5")
    assert result2["score"] < result1["score"], "Bad response should score lower"

    # Test 3: Live mode (only if API key is available)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and HAS_ANTHROPIC:
        print(f"\nTest 3 — Good response (LIVE mode):")
        result3 = score_with_judge(query, response_good, expected, mock_mode=False)
        print(f"  Score: {result3['score']:.2f}")
        print(f"  Accuracy: {result3['accuracy']}/5")
        print(f"  Completeness: {result3['completeness']}/5")
        print(f"  Clarity: {result3['clarity']}/5")
        print(f"  Reasoning: {result3['reasoning']}")
    else:
        print(f"\nTest 3 — Skipped (no API key or anthropic not installed)")

    print("\n" + "=" * 50)
    print("All self-tests passed!")
