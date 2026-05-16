"""
PreToolUse hook script — PII redactor.

Wired into .claude/settings.json as a PreToolUse command. The hook
reads the tool input from stdin (JSON), redacts PII patterns, and
writes the modified input back to stdout. Claude Code then dispatches
the tool with the redacted input.

Same regex logic as solution/pii_detector.py — this is the SAME
guardrail expressed as a hook instead of an inline wrapper.
"""
import json
import re
import sys


PII_PATTERNS = [
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    ("credit_card", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CC REDACTED]"),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL REDACTED]"),
    ("phone", r"(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b", "[PHONE REDACTED]"),
    ("dob", r"\b(?:\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b", "[DOB REDACTED]"),
]


def redact(text: str) -> str:
    out = text
    for _name, pattern, replacement in PII_PATTERNS:
        out = re.sub(pattern, replacement, out)
    return out


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})

    redacted = {}
    for k, v in tool_input.items():
        redacted[k] = redact(v) if isinstance(v, str) else v

    payload["tool_input"] = redacted
    json.dump(payload, sys.stdout)


if __name__ == "__main__":
    main()
