"""
M16: PII Detector — Starter
Detects and redacts personally identifiable information from user inputs.
"""
import re
import json


# ── PII Patterns ─────────────────────────────────────────────
# Each pattern: (name, regex, replacement)
PII_PATTERNS = [
    # TODO 1: Add regex pattern for SSN (XXX-XX-XXXX format)
    # Hint: \d{3}-\d{2}-\d{4}
    # ("ssn", r"...", "[SSN REDACTED]"),

    # TODO 2: Add regex pattern for credit card numbers (XXXX-XXXX-XXXX-XXXX or 16 digits)
    # Hint: \d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
    # ("credit_card", r"...", "[CREDIT CARD REDACTED]"),

    # TODO 3: Add regex pattern for email addresses
    # ("email", r"...", "[EMAIL REDACTED]"),

    # TODO 4: Add regex pattern for phone numbers (XXX-XXX-XXXX, (XXX) XXX-XXXX, etc.)
    # ("phone", r"...", "[PHONE REDACTED]"),

    # TODO 5: Add regex pattern for dates of birth (MM/DD/YYYY, YYYY-MM-DD)
    # ("dob", r"...", "[DOB REDACTED]"),
]


def detect_pii(text: str) -> dict:
    """
    Scan text for PII patterns.

    Returns:
        {
            "has_pii": bool,
            "detections": [{"type": str, "match": str, "position": (start, end)}],
            "redacted_text": str
        }
    """
    detections = []
    redacted = text

    # TODO 6: Loop through PII_PATTERNS
    # For each pattern, use re.finditer to find all matches
    # Append each match to detections list with type, match text, and position
    # Replace matches in redacted text with the replacement string
    # IMPORTANT: Process patterns from end of string to start to preserve positions

    return {
        "has_pii": len(detections) > 0,
        "detections": detections,
        "redacted_text": redacted,
    }


# ── Self-Test ────────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "Look up filings for John Smith, SSN 123-45-6789",
        "Contact me at john@example.com or 555-123-4567",
        "Credit card 4111-1111-1111-1111 for payment",
        "Born on 03/15/1990, needs UCC search",
        "Search filings for Acme Corporation in New York",  # Clean — no PII
    ]

    for text in test_inputs:
        result = detect_pii(text)
        status = "PII FOUND" if result["has_pii"] else "Clean"
        print(f"\n{status}: {text}")
        if result["has_pii"]:
            for d in result["detections"]:
                print(f"   -> {d['type']}: {d['match']}")
            print(f"   Redacted: {result['redacted_text']}")
