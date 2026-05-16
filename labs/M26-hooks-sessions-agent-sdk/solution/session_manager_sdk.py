"""
M26 Lab — Step 3 (canonical): claude-agent-sdk sessions

The SDK does not ship a Session class — multi-turn flows are implemented
by managing the transcript yourself and re-passing it on each query().
This thin wrapper does exactly that, plus a fork() for what-if branching.

Run:
    python session_manager_sdk.py
"""
import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, query

from agent_loop_sdk import support_server
from hooks_sdk import HOOKS, gate


def _options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="You are a UCC support agent. Help the customer across multiple turns.",
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


class SessionManager:
    def __init__(self):
        self.options = _options()
        self.transcript: list[str] = []

    async def send(self, user_input: str) -> str:
        full = "\n\n".join(self.transcript + [f"USER: {user_input}"])
        final = ""
        async for msg in query(prompt=full, options=self.options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        final = block.text
        self.transcript.append(f"USER: {user_input}")
        self.transcript.append(f"ASSISTANT: {final}")
        return final

    def fork(self) -> "SessionManager":
        clone = SessionManager()
        clone.transcript = list(self.transcript)
        return clone


async def _demo():
    s = SessionManager()
    print("Turn 1:", await s.send("Look up filing UCC-2024-NY-0012847."))
    print("\nTurn 2 (follow-up):", await s.send("What's the risk profile for that debtor?"))
    branch = s.fork()
    print("\nFork (what-if):", await branch.send("If they file a continuation, how does that change the risk?"))
    print("\nOriginal session, Turn 3:", await s.send("Issue a $200 goodwill credit on this account."))


if __name__ == "__main__":
    asyncio.run(_demo())
