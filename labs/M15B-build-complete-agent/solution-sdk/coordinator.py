"""
M15B — Coordinator (SDK Solution)
==================================

The same UCC research system as solution/coordinator.py, but built on
claude-agent-sdk's `query()` and ClaudeAgentOptions. The two specialists
are declared as .claude/agents/<name>.md files — the SDK gives each
subagent an isolated context window when it's invoked by name.

Run:
    python coordinator.py "What is the lien exposure for Acme Corporation?"
"""
import asyncio
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    query,
)

from tools import ucc_server, ALLOWED_TOOLS
from hooks import HOOKS, gate


COORDINATOR_PROMPT = (
    "You are the coordinator for a UCC filing research system.\n\n"
    "For each user question:\n"
    "1. Decide which specialist subagent(s) you need: filing-search, "
    "risk-analysis, or both. Subagents are declared in .claude/agents/.\n"
    "2. Delegate by invoking each specialist with a focused, explicit "
    "instruction. Subagents do NOT see your conversation; pass them "
    "everything they need.\n"
    "3. Synthesize results into a single narrative answer that cites filing "
    "numbers, states, and contributing risk factors.\n\n"
    "If a specialist returns no results, surface that fact instead of "
    "guessing. If you must call tools directly (because the question is "
    "narrow enough), prefer search_filings before calculate_risk_score."
)


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=COORDINATOR_PROMPT,
        mcp_servers={"ucc": ucc_server},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=8,
        model="claude-sonnet-4-6",
        hooks=HOOKS,
        can_use_tool=gate,
    )


async def ask(question: str) -> str:
    options = build_options()
    final_text = ""
    async for msg in query(prompt=question, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if hasattr(block, "text") and block.text:
                    final_text = block.text
    return final_text


def main():
    question = " ".join(sys.argv[1:]) or "What is the lien exposure for Acme Corporation?"
    print(f"\n>>> {question}\n")
    answer = asyncio.run(ask(question))
    print(answer)


if __name__ == "__main__":
    main()
