"""
CAPSTONE C3: Tool Smoke Tests (COMPLETE — run BEFORE building the agent)
=========================================================================
Run: python e2e_test.py
"""

from entity_tools import (fuzzy_match_score, get_business_registry_data,
                          get_filing_details, merge_entity_profile,
                          search_filings_by_name)

print("1. search_filings_by_name")
result = search_filings_by_name("Acme Logistics LLC")
assert not result["is_error"], "search failed"
assert result["total"] == 3, f"expected 3 candidates, got {result['total']}"
print(f"   OK — {result['total']} candidates")

print("2. search with state filter")
result = search_filings_by_name("Acme Logistics LLC", state="DE")
assert result["total"] == 2
print("   OK — 2 DE candidates")

print("3. search miss returns structured error (not an exception)")
result = search_filings_by_name("Nonexistent Corp")
assert result["is_error"] and result["error_category"] == "NO_RESULTS"
print("   OK — NO_RESULTS")

print("4. fuzzy_match_score on near-identical names")
result = fuzzy_match_score("Acme Logistics LLC", "ACME LOGISTICS, L.L.C.")
assert not result["is_error"]
assert result["scores"]["normalized"] >= 0.9, result["scores"]
print(f"   OK — {result['recommendation']} {result['scores']}")

print("5. registry hit and NOT_FOUND signal")
hit = get_business_registry_data("Acme Logistics LLC", "DE")
assert not hit["is_error"] and hit["entity_type"] == "LLC"
miss = get_business_registry_data("Acme Logistics Company", "DE")
assert miss["is_error"] and miss["error_category"] == "NOT_FOUND"
print("   OK — hit + NOT_FOUND")

print("6. filing details")
details = get_filing_details("ACME LOGISTICS, L.L.C.", "DE")
assert len(details["filings"]) == 3
total = sum(f["estimated_amount"] for f in details["filings"])
assert total == 2_300_000
print(f"   OK — 3 filings, ${total:,} exposure")

print("7. merge rejects low confidence")
rejected = merge_entity_profile({"name": "X"}, [], confidence=0.3)
assert rejected["is_error"] and rejected["error_category"] == "INSUFFICIENT_EVIDENCE"
print("   OK — INSUFFICIENT_EVIDENCE below 0.5")

print("8. merge succeeds with evidence")
merged = merge_entity_profile(
    {"name": "ACME LOGISTICS, L.L.C.", "state": "DE", "filing_count": 3},
    [{"name": "Acme Logistics Company", "state": "DE", "filing_count": 1, "match_score": 0.91}],
    confidence=0.88,
)
assert not merged["is_error"] and merged["total_filings"] == 4
print(f"   OK — {merged['merged_profile_id']}")

print("\nAll 8 tool checks passed. Build the agent.")
