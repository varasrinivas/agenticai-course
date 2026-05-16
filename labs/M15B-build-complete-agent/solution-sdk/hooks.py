"""
M15B — Hooks (SDK Solution)
============================

PreToolUse / PostToolUse / can_use_tool implementations referenced from
agent-spec.md. Imported by coordinator.py and the tests.
"""
import json
import os
import sys
from datetime import datetime, timezone

from claude_agent_sdk import (
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
)


AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_log.jsonl")


# --- PreToolUse: log every call to stderr ---

async def log_tool_call(input_data, tool_use_id, context):
    name = input_data.get("tool_name")
    params = input_data.get("tool_input")
    sys.stderr.write(f"[{datetime.now(timezone.utc).isoformat()}] PRE  {name}({params})\n")
    return {}


# --- PostToolUse: append to audit_log.jsonl ---

async def audit_log(input_data, tool_use_id, context):
    name = input_data.get("tool_name")
    params = input_data.get("tool_input")
    response = input_data.get("tool_response", "")
    summary = response if isinstance(response, str) else json.dumps(response, default=str)
    summary = summary[:200]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": name,
        "tool_input": params,
        "output_summary": summary,
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return {}


# --- can_use_tool: deny too-broad search queries ---

async def gate(tool_name, tool_input, context):
    if tool_name == "mcp__ucc__search_filings":
        name = tool_input.get("debtor_name") or ""
        if len(name.strip()) < 3:
            return PermissionResultDeny(message="Query too broad — minimum 3 characters")
    return PermissionResultAllow()


HOOKS = {
    "PreToolUse": [HookMatcher(matcher="*", hooks=[log_tool_call])],
    "PostToolUse": [HookMatcher(matcher="*", hooks=[audit_log])],
}
