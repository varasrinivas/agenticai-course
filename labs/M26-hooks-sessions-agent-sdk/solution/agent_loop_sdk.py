"""
M26 Lab — Step 1 (canonical): claude-agent-sdk loop

This is the **real** SDK version that replaces the simulated agent_loop.py
sitting next to it. agent_loop.py mocks the SDK with Python dicts so the
lab can run offline; this file shows the actual surface students will use
in production and on the cert exam.

Same scenario as agent_loop.py: a UCC support agent with four tools.

Run:
    pip install claude-agent-sdk
    export ANTHROPIC_API_KEY=...
    python agent_loop_sdk.py
"""
import asyncio
import json

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)


# --- Tools (same four as agent_loop.py, but as @tool functions) ---

@tool(
    "lookup_filing",
    "Look up a UCC filing by filing number (format UCC-YYYY-ST-NNNNNNN). "
    "Returns filing details including status, parties, and collateral.",
    {"filing_number": str},
)
async def lookup_filing(args):
    payload = {
        "filing_number": args.get("filing_number", "UCC-2024-NY-0012847"),
        "status": "Active",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "Atlantic Capital Partners",
        "filing_date": "2024-03-15",
        "expiration_date": "2029-03-15",
        "collateral": "All accounts receivable, inventory, equipment",
    }
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


@tool(
    "check_risk_profile",
    "Get a stored risk profile for a business entity by name.",
    {"entity_name": str},
)
async def check_risk_profile(args):
    payload = {
        "entity": args.get("entity_name", "Greenfield Logistics LLC"),
        "risk_score": 0.35,
        "risk_level": "LOW",
        "factors": ["No prior defaults", "Active 5+ years", "Single active lien"],
        "last_updated": "2024-12-01",
    }
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


@tool(
    "issue_refund",
    "Process a refund. Refunds over $500 must be escalated to a human.",
    {"amount": float, "reason": str},
)
async def issue_refund(args):
    amount = float(args.get("amount", 150.0))
    payload = {
        "refund_id": "REF-2024-0042",
        "amount": amount,
        "status": "processed" if amount <= 500 else "blocked",
        "reason": "Within limit" if amount <= 500 else "Exceeds $500 limit — escalate",
    }
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


@tool(
    "escalate_to_human",
    "Hand off the conversation to a human agent with a priority level.",
    {"priority": str, "reason": str},
)
async def escalate_to_human(args):
    payload = {
        "ticket_id": "ESC-2024-0891",
        "priority": args.get("priority", "medium"),
        "reason": args.get("reason", "Policy gap"),
        "assigned_to": "support-team-lead",
        "eta_minutes": 15,
    }
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


support_server = create_sdk_mcp_server(
    name="support_tools",
    version="1.0.0",
    tools=[lookup_filing, check_risk_profile, issue_refund, escalate_to_human],
)


SYSTEM_PROMPT = (
    "You are a UCC support agent. Use the tools to look up filings, check "
    "risk profiles, and issue refunds. Refunds over $500 MUST be escalated "
    "via escalate_to_human — do not attempt to issue them directly."
)


async def run(prompt: str) -> str:
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"support": support_server},
        allowed_tools=[
            "mcp__support__lookup_filing",
            "mcp__support__check_risk_profile",
            "mcp__support__issue_refund",
            "mcp__support__escalate_to_human",
        ],
        max_turns=6,
        model="claude-sonnet-4-6",
    )
    final = ""
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if hasattr(block, "text") and block.text:
                    final = block.text
    return final


if __name__ == "__main__":
    answer = asyncio.run(run(
        "Look up filing UCC-2024-NY-0012847 and tell me the secured party. "
        "Then check the risk profile of Greenfield Logistics LLC."
    ))
    print(answer)
