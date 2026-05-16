"""
M15B — SessionManager (SDK Solution)
=====================================

claude-agent-sdk's `query()` does not ship a Session class — sessions are
implemented by re-passing the running transcript on each call. This thin
wrapper handles that, plus a fork() for what-if branching.
"""
import asyncio

from claude_agent_sdk import AssistantMessage, query

from coordinator import build_options


class SessionManager:
    def __init__(self):
        self.options = build_options()
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
    print("Turn 1:", await s.send("What is the lien exposure for Acme Corporation?"))
    print("\nTurn 2:", await s.send("What about their Texas filings specifically?"))
    branch = s.fork()
    print("\nFork:", await branch.send("If Acme files a continuation in CA, how does that change the risk?"))
    print("\nTurn 3 (original session is untouched):", await s.send("Summarize what we know."))


if __name__ == "__main__":
    asyncio.run(_demo())
