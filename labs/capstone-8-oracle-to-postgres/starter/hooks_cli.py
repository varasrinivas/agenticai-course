"""Command-line adapter so `.claude/settings.json` can reach hooks.py.

There are two ways the guardrails get applied, and they need the same code
behind them:

  1. `python coordinator.py` wires `hooks.can_use_tool` and
     `hooks.audit_log` straight into `ClaudeAgentOptions`. In-process,
     no subprocess.
  2. A student running plain `claude` in this directory gets the hooks
     from `.claude/settings.json`, which can only invoke *commands*. This
     module is that command.

Both paths call the same functions in hooks.py, so a guardrail cannot be
correct in one mode and missing in the other.

Protocol: the hook payload arrives on stdin; the decision goes out on stdout
as `hookSpecificOutput.permissionDecision` with exit 0. That is the structured
path Claude Code documents for PreToolUse.

The alternative -- exit 2 with the reason on stderr -- also blocks, and blocks
unconditionally: exit 2 wins even over a JSON `"permissionDecision": "allow"`.
This module uses the JSON path because the denial message is the useful part.
A guard that blocks without saying why just gets retried with a synonym.

Usage (from settings.json, not by hand):
    python -m hooks_cli enforce_oracle_readonly
"""

from __future__ import annotations

import asyncio
import json
import sys
from types import SimpleNamespace

from claude_agent_sdk import PermissionResultDeny

import hooks

DISPATCH = {
    "enforce_oracle_readonly": hooks.enforce_oracle_readonly,
    "protect_pg_target": hooks.protect_pg_target,
    "hitl_cutover_gate": hooks.hitl_cutover_gate,
    "can_use_tool": hooks.can_use_tool,
}


def _decision(verdict: str, reason: str | None = None) -> str:
    """The documented PreToolUse output shape."""
    payload: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict,
        }
    }
    if reason:
        payload["hookSpecificOutput"]["permissionDecisionReason"] = reason
    return json.dumps(payload)


async def _run_guard(name: str, payload: dict) -> int:
    guard = DISPATCH[name]
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    context = SimpleNamespace(**{k: v for k, v in payload.items()
                                if k not in {"tool_name", "tool_input"}})

    result = await guard(tool_name, tool_input, context)

    if isinstance(result, PermissionResultDeny):
        # stderr for the human tailing the terminal, JSON for Claude Code.
        print(result.message, file=sys.stderr)
        print(_decision("deny", result.message))
        return 0

    print(_decision("allow"))
    return 0


async def _run_audit(payload: dict) -> int:
    """PostToolUse. It observes and never blocks, so it emits no decision --
    an empty object is the documented 'nothing to say' response."""
    context = SimpleNamespace(duration_ms=payload.get("duration_ms"))
    await hooks.audit_log(
        payload.get("tool_name", ""),
        payload.get("tool_input", {}) or {},
        payload.get("tool_response", {}) or {},
        context,
    )
    print(json.dumps({}))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m hooks_cli <hook_name>", file=sys.stderr)
        return 64

    name = sys.argv[1]
    raw = sys.stdin.read().strip()

    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        # Fail OPEN on a malformed payload we cannot parse, but say so
        # loudly. Failing closed here would brick every tool call the
        # moment the hook protocol changes shape -- and the in-process
        # guards in coordinator.py are still active either way.
        print(f"[hooks_cli] could not parse hook payload: {exc}", file=sys.stderr)
        print(json.dumps({}))
        return 0

    if name == "audit_log":
        return asyncio.run(_run_audit(payload))
    if name not in DISPATCH:
        print(f"[hooks_cli] unknown hook: {name}", file=sys.stderr)
        return 64
    return asyncio.run(_run_guard(name, payload))


if __name__ == "__main__":
    sys.exit(main())
