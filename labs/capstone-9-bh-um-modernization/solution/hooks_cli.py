"""Command-line entry point for the hooks declared in .claude/settings.json.

Claude Code invokes a hook as a shell command, hands it the tool call on stdin
as JSON, and reads a decision from stdout. `hooks.py` holds the logic as async
Python for the SDK path; this module is the shell adapter, so there is exactly
one implementation of each rule and two ways to reach it.

    python -m hooks_cli protected_content_gate < payload.json

Exit code 0 with `{"permissionDecision": "deny"}` blocks the call. A crash here
must NOT silently allow the tool -- an exception in the guard is reported as a
denial, because a guard that fails open is not a guard.
"""

from __future__ import annotations

import asyncio
import json
import sys

from claude_agent_sdk import PermissionResultDeny

import hooks

GUARDS = {
    "protected_content_gate": hooks.protected_content_gate,
    "enforce_reference_readonly": hooks.enforce_source_readonly,
    "enforce_legacy_readonly": hooks.enforce_source_readonly,
    "confine_writes": hooks.confine_writes,
    "hitl_finalization_gate": hooks.hitl_finalization_gate,
}


def _emit(decision: str, reason: str = "") -> int:
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m hooks_cli <guard-name>", file=sys.stderr)
        print(f"guards: {', '.join(sorted(GUARDS))}, audit_log", file=sys.stderr)
        return 2

    name = argv[0]

    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except json.JSONDecodeError as exc:
        # Unreadable input is not permission to proceed.
        return _emit("deny", f"hook received unreadable input: {exc}")

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if name == "audit_log":
        try:
            asyncio.run(hooks.audit_log(tool_name, tool_input,
                                        payload.get("tool_response"), None))
        except Exception as exc:                     # noqa: BLE001
            # A failed audit write must not block work, but it must be visible.
            print(f"[audit] WARNING: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0

    guard = GUARDS.get(name)
    if guard is None:
        return _emit("deny", f"unknown guard {name!r}")

    try:
        result = asyncio.run(guard(tool_name, tool_input, None))
    except Exception as exc:                         # noqa: BLE001
        # FAIL CLOSED. A guard that errors is a guard whose answer is unknown,
        # and "unknown" is not "allowed" when the question is whether this call
        # discloses protected health information.
        return _emit("deny",
                     f"{name} failed ({type(exc).__name__}: {exc}). Denying, "
                     f"because a guard that cannot answer has not said yes.")

    if isinstance(result, PermissionResultDeny):
        return _emit("deny", getattr(result, "message", "denied"))
    return _emit("allow")


if __name__ == "__main__":
    sys.exit(main())
