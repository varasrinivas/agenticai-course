"""
CAPSTONE C3: Mock Entity Resolution Tools (COMPLETE)
=====================================================
Five tools with structured error returns — tools never raise.
Smoke test: python e2e_test.py
"""

import re

# --- Tool 1: Search filings by name ---
MOCK_CANDIDATES = {
    "acme logistics llc": [
        {"name": "ACME LOGISTICS, L.L.C.", "state": "DE", "filing_count": 3, "most_recent": "2024-01-15"},
        {"name": "Acme Logistics Company", "state": "DE", "filing_count": 1, "most_recent": "2023-08-20"},
        {"name": "Acme Logistics Inc.", "state": "NY", "filing_count": 2, "most_recent": "2023-12-01"},
    ],
    "buildright construction": [
        {"name": "BuildRight Construction LLC", "state": "NY", "filing_count": 1, "most_recent": "2024-01-10"},
        {"name": "Build Right Construction", "state": "NY", "filing_count": 1, "most_recent": "2022-03-15"},
    ],
}


def search_filings_by_name(business_name: str, state: str | None = None,
                           match_type: str = "fuzzy") -> dict:
    try:
        key = business_name.lower().strip()
        candidates = MOCK_CANDIDATES.get(key, [])
        if state:
            candidates = [c for c in candidates if c["state"] == state.upper()]
        if not candidates:
            return {"is_error": True, "error_category": "NO_RESULTS", "is_retryable": False,
                    "context": f"No filings found for '{business_name}'"}
        return {"is_error": False, "candidates": candidates, "total": len(candidates)}
    except Exception as e:
        return {"is_error": True, "error_category": "INTERNAL_ERROR", "is_retryable": True, "context": str(e)}


# --- Tool 2: Fuzzy match score ---
_SUFFIX_RE = re.compile(r"\b(llc|l l c|inc|incorporated|corp|corporation|company|co|ltd)\b")


def _normalize(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[,.\-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    name = _SUFFIX_RE.sub("", name)
    return re.sub(r"\s+", " ", name).strip()


def fuzzy_match_score(entity_a: str, entity_b: str) -> dict:
    try:
        if not entity_a or not entity_b:
            return {"is_error": True, "error_category": "EMPTY_INPUT", "is_retryable": False,
                    "context": "Both entities required"}
        norm_a, norm_b = _normalize(entity_a), _normalize(entity_b)
        exact = 1.0 if entity_a.lower() == entity_b.lower() else round(
            len(set(entity_a.lower()) & set(entity_b.lower())) / max(len(set(entity_a.lower())), 1), 2)
        normalized = 1.0 if norm_a == norm_b else round(
            len(set(norm_a.split()) & set(norm_b.split())) / max(len(set(norm_a.split()) | set(norm_b.split())), 1), 2)
        token_sort = min(round(normalized * 1.03, 2) if normalized > 0.8 else normalized, 1.0)
        avg = round((exact + normalized + token_sort) / 3, 2)
        rec = "likely_match" if avg >= 0.85 else ("possible_match" if avg >= 0.65 else "unlikely_match")
        return {"is_error": False, "entity_a": entity_a, "entity_b": entity_b,
                "scores": {"exact": exact, "normalized": normalized, "token_sort_ratio": token_sort},
                "recommendation": rec}
    except Exception as e:
        return {"is_error": True, "error_category": "INTERNAL_ERROR", "is_retryable": True, "context": str(e)}


# --- Tool 3: Get filing details ---
MOCK_FILINGS = {
    ("acme logistics, l.l.c.", "DE"): {"filings": [
        {"filing_number": "2023-1234567", "secured_party": "First National Bank",
         "collateral": "All inventory and equipment", "status": "active", "estimated_amount": 750_000},
        {"filing_number": "2022-9876543", "secured_party": "Delaware Capital Partners",
         "collateral": "All vehicles", "status": "active", "estimated_amount": 350_000},
        {"filing_number": "2024-0011223", "secured_party": "First National Bank",
         "collateral": "Accounts receivable", "status": "active", "estimated_amount": 1_200_000},
    ]},
}


def get_filing_details(business_name: str, state: str) -> dict:
    try:
        key = (business_name.lower().strip(), state.upper())
        result = MOCK_FILINGS.get(key)
        return {"is_error": False, **result} if result else {"is_error": False, "filings": []}
    except Exception as e:
        return {"is_error": True, "error_category": "INTERNAL_ERROR", "is_retryable": True, "context": str(e)}


# --- Tool 4: Business registry ---
MOCK_REGISTRY = {
    ("acme logistics llc", "DE"): {
        "entity_name": "Acme Logistics LLC", "state": "DE", "entity_type": "LLC",
        "file_number": "DE-LLC-2019-4567890", "formation_date": "2019-03-15",
        "status": "active", "principal_address": "456 Commerce Blvd, Dover, DE 19901",
    },
    ("acme logistics inc.", "NY"): {
        "entity_name": "Acme Logistics Inc.", "state": "NY", "entity_type": "Corporation",
        "file_number": "NY-CORP-2020-1234567", "formation_date": "2020-07-01",
        "status": "active", "principal_address": "100 Broadway, New York, NY 10001",
    },
}


def get_business_registry_data(business_name: str, state: str) -> dict:
    try:
        key = (business_name.lower().strip(), state.upper())
        result = MOCK_REGISTRY.get(key)
        if result:
            return {"is_error": False, **result}
        # NOT_FOUND is a SIGNAL (lower your confidence), not a crash
        return {"is_error": True, "error_category": "NOT_FOUND", "is_retryable": False,
                "context": f"No registry entry for '{business_name}' in {state}"}
    except Exception as e:
        return {"is_error": True, "error_category": "INTERNAL_ERROR", "is_retryable": True, "context": str(e)}


# --- Tool 5: Merge entity profile ---
def merge_entity_profile(primary_entity: dict, merge_candidates: list, confidence: float) -> dict:
    try:
        if confidence < 0.5:
            return {"is_error": True, "error_category": "INSUFFICIENT_EVIDENCE", "is_retryable": False,
                    "context": f"Confidence {confidence} below 0.5 threshold"}
        total_filings = sum(c.get("filing_count", 0) for c in merge_candidates) + primary_entity.get("filing_count", 0)
        total_lien = sum(c.get("estimated_amount", 0) for c in merge_candidates) + primary_entity.get("estimated_amount", 0)
        return {"is_error": False,
                "merged_profile_id": f"MP-{primary_entity.get('name', 'unknown')[:10]}-{confidence:.0%}",
                "canonical_name": primary_entity.get("name", "Unknown"),
                "total_filings": total_filings,
                "total_lien_exposure": total_lien,
                "states": list(set([primary_entity.get("state", "")] + [c.get("state", "") for c in merge_candidates])),
                "confidence": confidence,
                "merge_log": [f"Merged '{c.get('name', '')}' (score: {c.get('match_score', 'N/A')})"
                              for c in merge_candidates]}
    except Exception as e:
        return {"is_error": True, "error_category": "INTERNAL_ERROR", "is_retryable": True, "context": str(e)}
