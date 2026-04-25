"""
M17: Output Validator — Starter
Validates agent outputs for structure, hallucination markers, and PII leakage.
"""
import re
import json


# ── Hallucination Markers ───────────────────────────────────
# Phrases that signal the agent is guessing rather than answering from data
HALLUCINATION_MARKERS = [
    # TODO 1: Add at least 6 low-confidence phrases that indicate hallucination.
    # Examples: "I think", "probably", "I'm not sure", "it seems like",
    #           "I believe", "might be", "not entirely certain"
    # Format: list of lowercase strings
]


# ── PII Patterns for Output Scanning ───────────────────────
PII_PATTERNS = [
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    ("credit_card", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CC REDACTED]"),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL REDACTED]"),
    ("phone", r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE REDACTED]"),
]


def check_json_structure(output: dict, required_fields: list[str]) -> dict:
    """
    Validate that the output dict contains all required fields.

    Returns:
        {
            "valid": bool,
            "missing_fields": list[str],
            "extra_fields": list[str]
        }
    """
    # TODO 2: Check which required_fields are missing from output keys.
    # Also identify any unexpected fields not in the required list.
    # Return the result dict with valid=True only if no fields are missing.
    missing = []
    extra = []

    return {
        "valid": len(missing) == 0,
        "missing_fields": missing,
        "extra_fields": extra,
    }


def check_hallucination_markers(text: str) -> dict:
    """
    Scan text for low-confidence phrases indicating potential hallucination.

    Returns:
        {
            "has_markers": bool,
            "markers_found": list[str],
            "confidence_penalty": float  # 0.1 per marker found, max 0.5
        }
    """
    # TODO 3: Check text (lowercased) for each marker in HALLUCINATION_MARKERS.
    # Collect all found markers.
    # Calculate confidence_penalty: 0.1 per marker, capped at 0.5.
    markers_found = []
    penalty = 0.0

    return {
        "has_markers": len(markers_found) > 0,
        "markers_found": markers_found,
        "confidence_penalty": penalty,
    }


def check_pii_in_output(text: str) -> dict:
    """
    Ensure agent outputs don't leak PII data.

    Returns:
        {
            "has_pii": bool,
            "pii_types": list[str],
            "redacted_text": str
        }
    """
    # TODO 4: Loop through PII_PATTERNS. Use re.findall to detect matches.
    # Collect the PII type names found.
    # Replace all PII matches in text with the redaction string.
    pii_types = []
    redacted = text

    return {
        "has_pii": len(pii_types) > 0,
        "pii_types": pii_types,
        "redacted_text": redacted,
    }


def validate_output(output: dict, expected_fields: list[str]) -> dict:
    """
    Run all output validation checks.

    Returns:
        {
            "valid": bool,
            "checks": {
                "structure": {...},
                "hallucination": {...},
                "pii": {...}
            },
            "output": dict  # original or redacted output
        }
    """
    # TODO 5: Run check_json_structure with output and expected_fields.
    # TODO 6: If output has a "response" key (string), run check_hallucination_markers
    #         and check_pii_in_output on it. If PII found, replace the response with
    #         the redacted version.
    # Combine all check results. valid=True only if structure is valid AND no PII found.

    structure_check = {"valid": True, "missing_fields": [], "extra_fields": []}
    hallucination_check = {"has_markers": False, "markers_found": [], "confidence_penalty": 0.0}
    pii_check = {"has_pii": False, "pii_types": [], "redacted_text": ""}

    is_valid = structure_check["valid"] and not pii_check["has_pii"]

    return {
        "valid": is_valid,
        "checks": {
            "structure": structure_check,
            "hallucination": hallucination_check,
            "pii": pii_check,
        },
        "output": output,
    }


# ── Self-Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("M17 Output Validator — Self-Test")
    print("=" * 60)

    # Test 1: Valid output
    good_output = {
        "entity": "Acme Corp",
        "filing_number": "UCC-2024-CA-0001234",
        "response": "Acme Corp has 3 active UCC filings in California.",
        "confidence": 0.95,
    }
    result = validate_output(good_output, ["entity", "filing_number", "response", "confidence"])
    print(f"\nTest 1 — Valid output: {'PASS' if result['valid'] else 'FAIL'}")
    print(f"  Structure valid: {result['checks']['structure']['valid']}")
    print(f"  Hallucination markers: {result['checks']['hallucination']['has_markers']}")
    print(f"  PII detected: {result['checks']['pii']['has_pii']}")

    # Test 2: Missing fields
    bad_structure = {"entity": "Acme Corp"}
    result = validate_output(bad_structure, ["entity", "filing_number", "response", "confidence"])
    print(f"\nTest 2 — Missing fields: {'PASS' if not result['valid'] else 'FAIL'}")
    print(f"  Missing: {result['checks']['structure']['missing_fields']}")

    # Test 3: Hallucination markers
    hedging_output = {
        "entity": "Acme Corp",
        "filing_number": "UCC-2024-CA-0001234",
        "response": "I think Acme Corp probably has some filings, but I'm not sure about the details.",
        "confidence": 0.75,
    }
    result = validate_output(hedging_output, ["entity", "filing_number", "response", "confidence"])
    print(f"\nTest 3 — Hallucination markers:")
    print(f"  Markers found: {result['checks']['hallucination']['markers_found']}")
    print(f"  Confidence penalty: {result['checks']['hallucination']['confidence_penalty']}")

    # Test 4: PII in output
    pii_output = {
        "entity": "John Smith",
        "filing_number": "UCC-2024-NY-0005678",
        "response": "Contact John Smith at 555-123-4567 or john@example.com. SSN: 123-45-6789.",
        "confidence": 0.85,
    }
    result = validate_output(pii_output, ["entity", "filing_number", "response", "confidence"])
    print(f"\nTest 4 — PII in output: {'PASS' if not result['valid'] else 'FAIL'}")
    print(f"  PII types: {result['checks']['pii']['pii_types']}")
    print(f"  Redacted: {result['output'].get('response', 'N/A')}")

    print("\n" + "=" * 60)
    print("Self-test complete. Fill in TODOs to make all tests pass.")
    print("=" * 60)
