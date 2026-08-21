"""PostToolUse hook — append every Bash invocation to audit.log.

Wired in .claude/settings.json under PostToolUse with matcher "Bash".

PostToolUse runs *after* the tool has executed, so it observes and never
blocks. That makes it a **detective** control, not a preventive one: it
tells you what happened, it cannot stop it. If you need something not to
happen, that is PreToolUse — see block_production_writes.py.

Like every hook, this reads its payload as JSON on stdin. PostToolUse
payloads carry `tool_response` alongside `tool_name` and `tool_input`.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.environ.get("AUDIT_LOG", "audit.log")

# An audit log is a file people commit, paste into tickets, and ship to a
# log aggregator. Anything credential-shaped has to come out first.
SECRET_PATTERNS = [
    re.compile(r"(--password[= ])(\S+)", re.I),
    re.compile(r"(://[^:/\s]+:)([^@/\s]+)(@)"),
    re.compile(r"((?:API_KEY|TOKEN|SECRET)\s*=\s*)(\S+)", re.I),
    re.compile(r"(sk-ant-[A-Za-z0-9_-]{6})([A-Za-z0-9_-]+)"),
]


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(r"\1***\3" if pattern.groups >= 3 else r"\1***", text)
    return text


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[audit_log] unreadable payload: {exc}", file=sys.stderr)
        json.dump({}, sys.stdout)
        return 0

    tool_input = payload.get("tool_input") or {}
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": payload.get("tool_name", "?"),
        "command": redact(str(tool_input.get("command", ""))),
        "cwd": payload.get("cwd"),
    }

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        # A failed audit write must not break the session, but it must be
        # visible — a silently missing audit trail is worse than none.
        print(f"[audit_log] WARNING: could not write {LOG_PATH}: {exc}", file=sys.stderr)

    # PostToolUse has nothing to decide.
    json.dump({}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
