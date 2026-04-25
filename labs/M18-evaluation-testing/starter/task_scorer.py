"""
M18 — Task Completion Scorer
==============================
Scores whether the agent found the correct UCC filings.
Uses partial credit: finding 3 of 5 expected filings = 0.6.

TODO: Implement the two functions below.
"""

import re


def extract_filing_numbers(text: str) -> list[str]:
    """
    Extract UCC filing numbers from response text.

    Filing numbers follow the pattern: UCC-YYYY-XX-NNNNNNN
    Examples: UCC-2024-NY-0012847, UCC-2023-TX-0187634

    TODO:
    1. Use a regex pattern to find all filing numbers in the text
    2. Return a list of unique filing numbers found
    3. Handle edge cases: no filings, duplicates

    Hint: The pattern is UCC-DDDD-LL-DDDDDDD where D=digit, L=letter
    """
    # TODO: Implement regex extraction
    # Pattern: UCC- followed by 4 digits, dash, 2 uppercase letters, dash, 7 digits
    pass


def score_task_completion(response: str, expected: dict) -> dict:
    """
    Score whether the agent found the correct filings.

    Args:
        response: The agent's text response
        expected: Dict with 'expected_filings' (list of filing number strings)

    Returns:
        {
            "score": float (0.0-1.0),
            "found": list of filing numbers correctly identified,
            "missed": list of expected filings not found in response,
            "extra": list of filing numbers in response but not expected,
            "details": str description of the result
        }

    TODO:
    1. Extract filing numbers from the response using extract_filing_numbers()
    2. Compare against expected["expected_filings"]
    3. Calculate partial credit: found / expected count
    4. Handle edge case: if expected list is empty, score 1.0 if response
       has no filings, 0.0 if response has filings
    5. Build the result dict with found, missed, and extra lists
    """
    # TODO: Implement scoring logic
    pass


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Task Completion Scorer — Self-Test")
    print("=" * 50)

    # Test 1: Perfect match
    response1 = (
        "Found 2 filings:\n"
        "- UCC-2024-NY-0012847 (Active)\n"
        "- UCC-2024-NY-0015921 (Active)"
    )
    expected1 = {
        "expected_filings": ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"]
    }
    result1 = score_task_completion(response1, expected1)
    print(f"\nTest 1 — Perfect match:")
    print(f"  Score: {result1['score']} (expected: 1.0)")
    print(f"  Found: {result1['found']}")
    print(f"  Missed: {result1['missed']}")
    assert result1["score"] == 1.0, f"Expected 1.0, got {result1['score']}"

    # Test 2: Partial match (1 of 2)
    response2 = "I found filing UCC-2024-NY-0012847 for Acme Corporation."
    expected2 = {
        "expected_filings": ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"]
    }
    result2 = score_task_completion(response2, expected2)
    print(f"\nTest 2 — Partial match (1/2):")
    print(f"  Score: {result2['score']} (expected: 0.5)")
    print(f"  Found: {result2['found']}")
    print(f"  Missed: {result2['missed']}")
    assert result2["score"] == 0.5, f"Expected 0.5, got {result2['score']}"

    # Test 3: No match
    response3 = "I could not find any filings for that entity."
    expected3 = {
        "expected_filings": ["UCC-2024-NY-0012847"]
    }
    result3 = score_task_completion(response3, expected3)
    print(f"\nTest 3 — No match:")
    print(f"  Score: {result3['score']} (expected: 0.0)")
    assert result3["score"] == 0.0, f"Expected 0.0, got {result3['score']}"

    # Test 4: Empty expected (edge case — no filings expected)
    response4 = "No filings were found for XYZ Corp."
    expected4 = {"expected_filings": []}
    result4 = score_task_completion(response4, expected4)
    print(f"\nTest 4 — Empty expected, no filings in response:")
    print(f"  Score: {result4['score']} (expected: 1.0)")
    assert result4["score"] == 1.0, f"Expected 1.0, got {result4['score']}"

    # Test 5: Extra filings found
    response5 = (
        "Found 3 filings:\n"
        "- UCC-2024-NY-0012847\n"
        "- UCC-2024-NY-0015921\n"
        "- UCC-2024-CA-0101457"
    )
    expected5 = {
        "expected_filings": ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"]
    }
    result5 = score_task_completion(response5, expected5)
    print(f"\nTest 5 — All expected found + extra:")
    print(f"  Score: {result5['score']} (expected: 1.0)")
    print(f"  Extra: {result5['extra']}")
    assert result5["score"] == 1.0, f"Expected 1.0, got {result5['score']}"

    print("\n" + "=" * 50)
    print("All self-tests passed!")
