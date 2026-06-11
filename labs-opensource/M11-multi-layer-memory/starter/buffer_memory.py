"""
M11 Lab - Step 1: BufferMemory (Layer 1 — this session)
========================================================
Sliding window buffer with token-aware eviction.
Run: python buffer_memory.py
"""

from __future__ import annotations

from typing import Optional


class BufferMemory:
    """In-process message buffer with sliding window eviction.

    Eviction policy (applied in order when both limits set):
    1. If len(messages) > max_messages: drop oldest pairs
    2. If token_count() > max_tokens: drop oldest pairs until under budget
    """

    def __init__(self, max_messages: int = 20, max_tokens: Optional[int] = 4000) -> None:
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """(COMPLETE) 4-chars-per-token heuristic — good enough for eviction.
        GOTCHA: JSON-heavy content tokenizes denser; lower max_tokens ~15% if
        you store tool outputs here."""
        total_chars = sum(
            len(str(m.get("content", ""))) + len(m.get("role", ""))
            for m in messages
        )
        return total_chars // 4

    def token_count(self) -> int:
        return self._estimate_tokens(self.messages)

    def add(self, role: str, content: str) -> None:
        """Add a message and evict oldest messages if over limits.

        TODO:
        1. Append {"role": role, "content": content}
        2. While len(self.messages) > self.max_messages:
             pop TWO messages from the front (index 0, twice) — always evict
             in user+assistant PAIRS; an orphaned turn confuses the model
        3. If self.max_tokens is not None:
             while len(self.messages) >= 2 and
                   self._estimate_tokens(self.messages) > self.max_tokens:
               pop two from the front (pairs again)
        """
        pass  # Remove this line when you add your code

    def get(self) -> list[dict]:
        """(COMPLETE) Safe to pass directly to the API."""
        return list(self.messages)

    def clear(self) -> None:
        self.messages = []

    def __repr__(self) -> str:
        return f"BufferMemory(messages={len(self.messages)}, ~{self.token_count()} tokens)"


# ── Smoke test (COMPLETE) ──
if __name__ == "__main__":
    buf = BufferMemory(max_messages=6, max_tokens=200)

    for i in range(5):
        buf.add("user", f"Query number {i}: what is the status of order {i}?")
        buf.add("assistant", f"Order {i} is shipped. Tracking: TRK{i:04d}.")

    print(buf)  # should show ~3 pairs or fewer (oldest evicted)
    print(f"Messages kept: {len(buf.get())}")
    for m in buf.get():
        print(f"  [{m['role']}] {m['content'][:60]}")
    assert len(buf.get()) <= 6, "max_messages eviction failed"
    assert buf.token_count() <= 200, "token eviction failed"
    assert buf.get()[0]["role"] == "user", "buffer must start with a user turn (evict in pairs!)"
    print("\nAll eviction checks passed.")
