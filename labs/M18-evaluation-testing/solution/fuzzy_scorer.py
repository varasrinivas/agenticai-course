"""
M18 — Fuzzy Entity Match Scorer (Solution)
=============================================
Scores entity resolution accuracy using token-based fuzzy matching.
No external dependencies — uses simple token overlap (Jaccard similarity).
"""

import re


def tokenize(text: str) -> set[str]:
    """
    Break a string into lowercase alphanumeric tokens.

    Examples:
        "Acme Corporation" -> {"acme", "corporation"}
        "A.C.M.E. Corp" -> {"a", "c", "m", "e", "corp"}
    """
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return {t for t in tokens if t}  # filter out empty strings


def score_entity_match(response_entity: str, expected_entity: str) -> float:
    """
    Score how well two entity names match using Jaccard similarity.
    Jaccard = |intersection| / |union|
    """
    tokens_a = tokenize(response_entity)
    tokens_b = tokenize(expected_entity)

    # Edge cases
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


def score_entity_resolution(response: str, expected: dict) -> dict:
    """
    Score entity resolution from the agent response.

    Checks whether the expected entity name appears in the response.
    Uses token overlap to handle abbreviations and variations.
    """
    expected_entity = expected.get("expected_entity")

    # No entity to check
    if expected_entity is None:
        return {
            "score": 1.0,
            "matches": [],
            "details": "No entity check required (expected_entity is None).",
        }

    # Check for exact substring match first
    if expected_entity.lower() in response.lower():
        return {
            "score": 1.0,
            "matches": [
                {
                    "response_entity": expected_entity,
                    "expected_entity": expected_entity,
                    "similarity": 1.0,
                }
            ],
            "details": f"Exact match: '{expected_entity}' found in response.",
        }

    # Fuzzy match: compare expected entity against chunks of the response
    # Try to find the best-matching substring in the response
    response_tokens = tokenize(response)
    expected_tokens = tokenize(expected_entity)

    if not expected_tokens:
        return {
            "score": 1.0,
            "matches": [],
            "details": "Expected entity has no tokens.",
        }

    # Check token overlap between expected entity and full response
    overlap = expected_tokens & response_tokens
    similarity = len(overlap) / len(expected_tokens) if expected_tokens else 0.0

    matches = []
    if similarity > 0:
        matches.append(
            {
                "response_entity": " ".join(sorted(overlap)),
                "expected_entity": expected_entity,
                "similarity": round(similarity, 3),
            }
        )

    # Score: use the token coverage ratio
    score = min(similarity, 1.0)

    if score >= 0.8:
        details = f"Strong match ({score:.0%}): most tokens of '{expected_entity}' found in response."
    elif score >= 0.5:
        details = f"Partial match ({score:.0%}): some tokens of '{expected_entity}' found in response."
    else:
        details = f"Weak match ({score:.0%}): few tokens of '{expected_entity}' found in response."

    return {
        "score": round(score, 3),
        "matches": matches,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Fuzzy Entity Match Scorer — Self-Test")
    print("=" * 50)

    # Test 1: Exact match
    score1 = score_entity_match("Acme Corporation", "Acme Corporation")
    print(f"\nTest 1 — Exact match:")
    print(f"  Score: {score1:.2f} (expected: 1.00)")
    assert score1 == 1.0

    # Test 2: Abbreviation match
    score2 = score_entity_match("Acme Corp", "Acme Corporation")
    print(f"\nTest 2 — Abbreviation:")
    print(f"  Score: {score2:.2f} (expected: ~0.33)")
    assert 0.3 <= score2 <= 0.7

    # Test 3: No match
    score3 = score_entity_match("Totally Different Company", "Acme Corporation")
    print(f"\nTest 3 — No match:")
    print(f"  Score: {score3:.2f} (expected: 0.00)")
    assert score3 == 0.0

    # Test 4: Full name match
    score4 = score_entity_match(
        "Lone Star Energy Solutions LP",
        "Lone Star Energy Solutions LP"
    )
    print(f"\nTest 4 — Full name match:")
    print(f"  Score: {score4:.2f} (expected: 1.00)")
    assert score4 == 1.0

    # Test 5: Entity in response
    response5 = (
        "I found filings for Acme Corporation in New York. "
        "There are 2 active UCC-1 filings."
    )
    expected5 = {"expected_entity": "Acme Corporation"}
    result5 = score_entity_resolution(response5, expected5)
    print(f"\nTest 5 — Entity in response:")
    print(f"  Score: {result5['score']:.2f} (expected: >= 0.5)")
    print(f"  Details: {result5['details']}")
    assert result5["score"] >= 0.5

    # Test 6: No expected entity
    result6 = score_entity_resolution("Some response", {"expected_entity": None})
    print(f"\nTest 6 — No expected entity:")
    print(f"  Score: {result6['score']:.2f} (expected: 1.00)")
    assert result6["score"] == 1.0

    print("\n" + "=" * 50)
    print("All self-tests passed!")
