"""
PreToolUse hook — PII redactor.

Wired into .claude/settings.json as a PreToolUse command, and also
imported by sdk_agent.py for the in-process path.

A PreToolUse hook CAN rewrite the tool input. It does so by returning
`updatedInput` inside `hookSpecificOutput` — not by echoing the payload
to stdout, which is ignored:

    {"hookSpecificOutput": {
       "hookEventName": "PreToolUse",
       "permissionDecision": "allow",
       "updatedInput": {...}}}

Two rules that decide whether this actually works:

  * Return a NEW object. Mutating the `tool_input` you were handed has
    no effect, in either delivery mode.
  * Pair `updatedInput` with `permissionDecision: "allow"` to
    auto-approve the rewrite, or omit the decision to let normal
    permission evaluation run on the modified input. With `"defer"`,
    `updatedInput` is ignored.

Same regex logic as solution/pii_detector.py — the SAME guardrail
expressed as a hook instead of an inline wrapper.

Run directly to self-test the patterns:
    python hooks/pii_redactor.py --self-test
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


def self_test():
    cases = [
        ("SSN 123-45-6789 on file", "[SSN REDACTED]"),
        ("card 4111-1111-1111-1111", "[CC REDACTED]"),
        ("write to ada@example.com", "[EMAIL REDACTED]"),
        ("account ACC-1001, no PII", None),
    ]
    failures = 0
    for text, expected in cases:
        got = redact(text)
        ok = (expected in got) if expected else (got == text)
        print(("  PASS  " if ok else "  FAIL  ") + repr(text) + " -> " + repr(got))
        failures += 0 if ok else 1
    print()
    print("%d/%d passed" % (len(cases) - failures, len(cases)))
    return 1 if failures else 0


def main():
    if "--self-test" in sys.argv:
        sys.exit(self_test())

    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {}) or {}

    # Build a NEW dict. Mutating tool_input in place does nothing.
    redacted = {
        k: (redact(v) if isinstance(v, str) else v)
        for k, v in tool_input.items()
    }

    if redacted == tool_input:
        json.dump({}, sys.stdout)          # nothing to change
        return

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": redacted,
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
