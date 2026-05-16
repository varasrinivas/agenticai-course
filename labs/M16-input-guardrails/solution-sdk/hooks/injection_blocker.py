"""
PreToolUse hook script — prompt-injection blocker.

Mirrors solution/injection_filter.py but expressed as a hook command.
Returns a non-zero exit code when an injection pattern is detected;
Claude Code blocks the tool call when the hook fails.
"""
import json
import re
import sys


# Same pattern set as solution/injection_filter.py.
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"disregard\s+(?:the\s+)?system\s+prompt",
    r"you\s+are\s+now\s+",
    r"</?\s*system\s*>",
    r"\[INST\]",
    r"act\s+as\s+(?:a\s+)?different\s+",
]


def is_injection(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in INJECTION_PATTERNS)


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})

    for v in tool_input.values():
        if isinstance(v, str) and is_injection(v):
            sys.stderr.write(f"BLOCKED: prompt injection detected in tool input\n")
            sys.exit(2)  # non-zero → Claude Code blocks the tool call

    json.dump(payload, sys.stdout)


if __name__ == "__main__":
    main()
