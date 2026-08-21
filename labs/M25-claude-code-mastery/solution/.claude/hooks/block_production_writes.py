"""PreToolUse hook — refuse any Write that targets data/production/.

Wired in .claude/settings.json under PreToolUse with matcher "Write".

Protocol: Claude Code sends the hook payload as JSON on **stdin** — not as
command-line arguments. A settings entry like
`command: "python hook.py \"$TOOL_INPUT\""` does not work; there is no such
shell variable, and the script would receive an empty string and cheerfully
approve everything.

Blocking has two forms:
  * exit 2, with the reason on stderr — blocks unconditionally
  * exit 0 and print `hookSpecificOutput.permissionDecision` — preferred,
    because the reason reaches the model so it stops instead of retrying

This hook denies. It could instead REDIRECT, by returning `updatedInput`
alongside `permissionDecision: "allow"` to rewrite `file_path` into
`data/staging/`. Denying is the right call here: silently relocating
someone's write is surprising, and the model cannot learn the rule from
an operation that appears to have succeeded somewhere else.

Use `updatedInput` when the rewrite is invisible by design (redacting PII,
sandboxing a path) and `deny` when the caller needs to know.
"""

import json
import sys

PROTECTED_PREFIXES = ("data/production/", "data\\production\\")


def decision(verdict: str, reason: str | None = None) -> dict:
    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict,
        }
    }
    if reason:
        out["hookSpecificOutput"]["permissionDecisionReason"] = reason
    return out


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        # Fail open on an unparseable payload, but say so. Failing closed
        # here would block every Write the moment the payload shape changes.
        print(f"[block_production_writes] unreadable payload: {exc}", file=sys.stderr)
        json.dump({}, sys.stdout)
        return 0

    tool_input = payload.get("tool_input") or {}
    path = str(tool_input.get("file_path", "")).replace("\\", "/").lstrip("./")

    if any(path.startswith(p.replace("\\", "/")) for p in PROTECTED_PREFIXES):
        reason = (
            f"Refused: {path} is under data/production/. Production data is "
            f"read-only from this project. Write to data/staging/ instead, or "
            f"ask a human to promote it."
        )
        print(reason, file=sys.stderr)
        json.dump(decision("deny", reason), sys.stdout)
        return 0

    json.dump(decision("allow"), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
