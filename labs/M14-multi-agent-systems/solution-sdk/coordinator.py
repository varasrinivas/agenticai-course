"""
M14 — SDK Coordinator
======================

claude-agent-sdk version of the manual multi_agent.py orchestration.

The four specialists (researcher, analyst, writer, reviewer) live in
.claude/agents/ as declarative subagent files. The SDK invokes each one
in an isolated context window when the coordinator names it.

Compare this file (~80 lines) with solution/multi_agent.py (~250 lines)
to see what the SDK absorbs.

Run:
    pip install claude-agent-sdk
    export ANTHROPIC_API_KEY=...
    python coordinator.py "Acme Corporation"
"""
import asyncio
import json
import os
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)

# Reuse the shared mock data already present in this lab.
HERE = os.path.dirname(os.path.abspath(__file__))
LAB_ROOT = os.path.normpath(os.path.join(HERE, ".."))
if LAB_ROOT not in sys.path:
    sys.path.insert(0, LAB_ROOT)
SHARED = os.path.normpath(os.path.join(HERE, "..", "..", "shared"))
if SHARED not in sys.path:
    sys.path.insert(0, SHARED)

from mock_ucc_data import search_filings as _search, get_filing_by_number  # noqa: E402


@tool(
    "search_filings",
    "Search UCC filings by debtor name and/or state.",
    {"debtor_name": str, "state": str},
)
async def t_search(args):
    rows = _search(debtor_name=args.get("debtor_name"), state=args.get("state"))
    return {"content": [{"type": "text", "text": json.dumps(rows, default=str)[:8000]}]}


@tool(
    "get_filing_details",
    "Get full details for a specific filing by filing number.",
    {"filing_number": str},
)
async def t_details(args):
    row = get_filing_by_number(args["filing_number"])
    return {"content": [{"type": "text", "text": json.dumps(row, default=str)}]}


server = create_sdk_mcp_server(name="ucc", version="1.0.0", tools=[t_search, t_details])


COORDINATOR_PROMPT = (
    "You are the coordinator of a UCC research pipeline. Four specialists are "
    "available as named subagents in .claude/agents/: researcher, analyst, "
    "writer, reviewer.\n\n"
    "Pipeline (in order):\n"
    "1. Delegate to `researcher` to gather filings for the target debtor.\n"
    "2. Delegate to `analyst` with the researcher's filing list — get patterns.\n"
    "3. Delegate to `writer` with the analyst's findings — get a draft report.\n"
    "4. Delegate to `reviewer` with the draft AND the raw filings — get fact-check.\n"
    "5. If the reviewer returned corrections, send them and the draft back to the writer; otherwise return the approved report.\n\n"
    "Each subagent has an isolated context window. Pass them everything they "
    "need explicitly — they do not see your conversation."
)


async def run(target: str) -> str:
    options = ClaudeAgentOptions(
        system_prompt=COORDINATOR_PROMPT,
        mcp_servers={"ucc": server},
        allowed_tools=[
            "mcp__ucc__search_filings",
            "mcp__ucc__get_filing_details",
        ],
        max_turns=12,
        model="claude-sonnet-4-6",
    )
    final = ""
    async for msg in query(prompt=f"Produce a credit-risk report for: {target}", options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if hasattr(block, "text") and block.text:
                    final = block.text
    return final


if __name__ == "__main__":
    target = " ".join(sys.argv[1:]) or "Acme Corporation"
    print(asyncio.run(run(target)))
