"""
M18 — Fuzzy Entity Match Scorer
=================================
Scores entity resolution accuracy using token-based fuzzy matching.
No external dependencies — uses simple token overlap (Jaccard similarity).

TODO: Implement the three functions below.
"""


def tokenize(text: str) -> set[str]:
    """
    Break a string into lowercase alphanumeric tokens.

    Examples:
        "Acme Corporation" -> {"acme", "corporation"}
        "Lone Star Energy Solutions LP" -> {"lone", "star", "energy", "solutions", "lp"}
        "A.C.M.E. Corp" -> {"a", "c", "m", "e", "corp"}

    TODO:
    1. Convert to lowercase
    2. Split on non-alphanumeric characters
    3. Filter out empty strings
    4. Return as a set (for set operations)
    """
    # TODO: Implement tokenization
    pass


def score_entity_match(response_entity: str, expected_entity: str) -> float:
    """
    Score how well two entity names match using Jaccard similarity.

    Jaccard similarity = |intersection| / |union| of token sets.

    Args:
        response_entity: The entity name found by the agent
        expected_entity: The expected entity name from the test case

    Returns:
        float between 0.0 and 1.0

    TODO:
    1. Tokenize both strings
    2. Handle edge case: both empty -> 1.0, one empty -> 0.0
    3. Calculate Jaccard similarity: len(intersection) / len(union)
    4. Return the score

    Examples:
        ("Acme Corp", "Acme Corporation") -> ~0.67 (shared: acme; union: acme, corp, corporation)
        ("Acme Corporation", "Acme Corporation") -> 1.0
        ("Totally Different", "Acme Corporation") -> 0.0
    """
    # TODO: Implement Jaccard similarity
    pass


def score_entity_resolution(response: str, expected: dict) -> dict:
    """
    Score entity resolution from the agent response.

    This extracts the entity name from the response and compares it
    against the expected entity name.

    Args:
        response: The agent's text response
        expected: Dict with 'expected_entity' (str or None)

    Returns:
        {
            "score": float (0.0-1.0),
            "matches": list of {"response_entity": str, "expected_entity": str, "similarity": float},
            "details": str description of the result
        }

    TODO:
    1. If expected_entity is None, return score 1.0 (no entity check needed)
    2. Check if the expected entity name appears in the response (exact or close)
    3. Also check common abbreviations / variations:
       - Try matching against the full response text using token overlap
       - Use score_entity_match to get similarity
    4. A score >= 0.5 from token overlap counts as a match
    5. Build the result dict
    """
    # TODO: Implement entity resolution scoring
    pass


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
    assert score1 == 1.0, f"Expected 1.0, got {score1}"

    # Test 2: Abbreviation match
    score2 = score_entity_match("Acme Corp", "Acme Corporation")
    print(f"\nTest 2 — Abbreviation:")
    print(f"  Score: {score2:.2f} (expected: ~0.33-0.67)")
    assert 0.3 <= score2 <= 0.7, f"Expected ~0.33-0.67, got {score2}"

    # Test 3: No match
    score3 = score_entity_match("Totally Different Company", "Acme Corporation")
    print(f"\nTest 3 — No match:")
    print(f"  Score: {score3:.2f} (expected: 0.00)")
    assert score3 == 0.0, f"Expected 0.0, got {score3}"

    # Test 4: Variant name ("Lonestar" vs "Lone Star")
    score4 = score_entity_match(
        "Lone Star Energy Solutions LP",
        "Lone Star Energy Solutions LP"
    )
    print(f"\nTest 4 — Full name match:")
    print(f"  Score: {score4:.2f} (expected: 1.00)")
    assert score4 == 1.0, f"Expected 1.0, got {score4}"

    # Test 5: Entity resolution from response text
    response5 = (
        "I found filings for Acme Corporation in New York. "
        "There are 2 active UCC-1 filings."
    )
    expected5 = {"expected_entity": "Acme Corporation"}
    result5 = score_entity_resolution(response5, expected5)
    print(f"\nTest 5 — Entity in response:")
    print(f"  Score: {result5['score']:.2f} (expected: >= 0.5)")
    print(f"  Details: {result5['details']}")
    assert result5["score"] >= 0.5, f"Expected >= 0.5, got {result5['score']}"

    # Test 6: No expected entity
    result6 = score_entity_resolution("Some response", {"expected_entity": None})
    print(f"\nTest 6 — No expected entity:")
    print(f"  Score: {result6['score']:.2f} (expected: 1.00)")
    assert result6["score"] == 1.0

    print("\n" + "=" * 50)
    print("All self-tests passed!")
