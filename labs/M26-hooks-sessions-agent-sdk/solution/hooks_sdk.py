"""
M26 Lab — Step 2 (canonical): claude-agent-sdk hooks

Replaces the simulated HookEngine in hooks.py with the SDK's real
HookMatcher / can_use_tool primitives. This is the surface the cert exam
tests.

Run:
    python hooks_sdk.py
"""
import asyncio
import json
import sys
from datetime import datetime, timezone

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    query,
)

from agent_loop_sdk import support_server


# --- PreToolUse hook: log every tool call ---

async def log_pre(input_data, tool_use_id, context):
    name = input_data.get("tool_name")
    params = input_data.get("tool_input")
    sys.stderr.write(
        f"[{datetime.now(timezone.utc).isoformat()}] PRE  {name}({params})\n"
    )
    return {}


# --- PostToolUse hook: log result + redact PII ---

async def post_redact(input_data, tool_use_id, context):
    name = input_data.get("tool_name")
    response = input_data.get("tool_response")
    summary = response if isinstance(response, str) else json.dumps(response, default=str)
    sys.stderr.write(
        f"[{datetime.now(timezone.utc).isoformat()}] POST {name} → {summary[:120]}...\n"
    )
    # Hooks may return a modified response; here we just observe.
    return {}


# --- can_use_tool: gate refunds over $500 ---

async def gate(tool_name, tool_input, context):
    if tool_name == "mcp__support__issue_refund":
        amount = float(tool_input.get("amount", 0))
        if amount > 500:
            return PermissionResultDeny(
                message=f"Refund amount ${amount:.2f} exceeds the $500 auto-approval "
                        "limit. Use escalate_to_human instead."
            )
    return PermissionResultAllow()


HOOKS = {
    "PreToolUse": [HookMatcher(matcher="*", hooks=[log_pre])],
    "PostToolUse": [HookMatcher(matcher="*", hooks=[post_redact])],
}


async def run(prompt: str) -> str:
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a UCC support agent. You may attempt any tool — the "
            "permission gate will deny ones that violate policy."
        ),
        mcp_servers={"support": support_server},
        allowed_tools=[
            "mcp__support__lookup_filing",
            "mcp__support__check_risk_profile",
            "mcp__support__issue_refund",
            "mcp__support__escalate_to_human",
        ],
        max_turns=6,
        model="claude-sonnet-4-6",
        hooks=HOOKS,
        can_use_tool=gate,
    )
    final = ""
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if hasattr(block, "text") and block.text:
                    final = block.text
    return final


if __name__ == "__main__":
    print("\n--- Refund within limit ($150) ---")
    print(asyncio.run(run("Issue a $150 refund for order ORD-555. Reason: shipping delay.")))

    print("\n--- Refund over limit ($800) — gate should deny and force escalation ---")
    print(asyncio.run(run("Issue an $800 refund for order ORD-777. Reason: missing item.")))
