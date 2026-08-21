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
            reason = "Prompt injection detected in tool input"
            sys.stderr.write("BLOCKED: " + reason + "\n")
            # Two ways to block. Exit 2 blocks unconditionally -- it wins even
            # over a JSON "allow". The structured form below is preferred
            # because the reason reaches the model, so it stops rather than
            # rephrasing and retrying.
            json.dump(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                sys.stdout,
            )
            sys.exit(0)

    # Nothing to say. `{}` means "allow, unchanged".
    #
    # Echoing the payload back would NOT work as a pass-through: stdout is
    # parsed as a decision object, not as a replacement payload. To rewrite
    # the input you set hookSpecificOutput.updatedInput -- see
    # pii_redactor.py, which does exactly that.
    json.dump({}, sys.stdout)


if __name__ == "__main__":
    main()
