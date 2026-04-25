"""
M18 — Task Completion Scorer (Solution)
=========================================
Scores whether the agent found the correct UCC filings.
Uses partial credit: finding 3 of 5 expected filings = 0.6.
"""

import re


def extract_filing_numbers(text: str) -> list[str]:
    """
    Extract UCC filing numbers from response text.
    Pattern: UCC-YYYY-XX-NNNNNNN (e.g., UCC-2024-NY-0012847)
    """
    pattern = r"UCC-\d{4}-[A-Z]{2}-\d{7}"
    matches = re.findall(pattern, text)
    return list(set(matches))  # deduplicate


def score_task_completion(response: str, expected: dict) -> dict:
    """
    Score whether the agent found the correct filings.

    Returns:
        {"score": 0.0-1.0, "found": [...], "missed": [...], "extra": [...], "details": str}
    """
    expected_filings = set(expected.get("expected_filings", []))
    found_filings = set(extract_filing_numbers(response))

    # Edge case: no filings expected
    if not expected_filings:
        if not found_filings:
            return {
                "score": 1.0,
                "found": [],
                "missed": [],
                "extra": [],
                "details": "Correctly returned no filings (none expected).",
            }
        else:
            return {
                "score": 0.0,
                "found": [],
                "missed": [],
                "extra": sorted(found_filings),
                "details": f"Expected no filings but found {len(found_filings)}.",
            }

    # Calculate matches
    correctly_found = expected_filings & found_filings
    missed = expected_filings - found_filings
    extra = found_filings - expected_filings

    # Partial credit: proportion of expected filings that were found
    score = len(correctly_found) / len(expected_filings)

    details_parts = []
    if correctly_found:
        details_parts.append(f"Found {len(correctly_found)}/{len(expected_filings)} expected filings.")
    if missed:
        details_parts.append(f"Missed: {', '.join(sorted(missed))}.")
    if extra:
        details_parts.append(f"Extra (not expected): {', '.join(sorted(extra))}.")
    if score == 1.0:
        details_parts.append("Perfect match!")

    return {
        "score": score,
        "found": sorted(correctly_found),
        "missed": sorted(missed),
        "extra": sorted(extra),
        "details": " ".join(details_parts),
    }


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

    # Test 4: Empty expected
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
