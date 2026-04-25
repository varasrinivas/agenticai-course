"""
M16: PII Detector — Solution
Detects and redacts personally identifiable information from user inputs.
"""
import re
import json


# ── PII Patterns ─────────────────────────────────────────────
# Each pattern: (name, regex, replacement)
PII_PATTERNS = [
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    ("credit_card", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CREDIT CARD REDACTED]"),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL REDACTED]"),
    ("phone", r"(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b", "[PHONE REDACTED]"),
    ("dob", r"\b(?:\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b", "[DOB REDACTED]"),
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

    for name, pattern, replacement in PII_PATTERNS:
        # Find all matches for this pattern
        matches = list(re.finditer(pattern, redacted))
        # Process from end to start to preserve positions during replacement
        for match in reversed(matches):
            detections.append({
                "type": name,
                "match": match.group(),
                "position": (match.start(), match.end()),
            })
            redacted = redacted[:match.start()] + replacement + redacted[match.end():]

    # Sort detections by position (start) for consistent output
    detections.sort(key=lambda d: d["position"][0])

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
