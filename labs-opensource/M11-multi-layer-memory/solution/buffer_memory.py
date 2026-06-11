"""
M11 Lab - Step 1: BufferMemory — SOLUTION
==========================================
Run: python buffer_memory.py
"""

from __future__ import annotations

from typing import Optional


class BufferMemory:
    """In-process message buffer with sliding window eviction."""

    def __init__(self, max_messages: int = 20, max_tokens: Optional[int] = 4000) -> None:
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """4-chars-per-token heuristic — good enough for eviction."""
        total_chars = sum(
            len(str(m.get("content", ""))) + len(m.get("role", ""))
            for m in messages
        )
        return total_chars // 4

    def token_count(self) -> int:
        return self._estimate_tokens(self.messages)

    def add(self, role: str, content: str) -> None:
        """Add a message and evict oldest messages if over limits."""
        self.messages.append({"role": role, "content": content})

        # Evict by count — always in user+assistant PAIRS
        while len(self.messages) > self.max_messages:
            self.messages.pop(0)
            if self.messages:
                self.messages.pop(0)

        # Evict by tokens — pairs again
        if self.max_tokens is not None:
            while (
                len(self.messages) >= 2
                and self._estimate_tokens(self.messages) > self.max_tokens
            ):
                self.messages.pop(0)
                self.messages.pop(0)

    def get(self) -> list[dict]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages = []

    def __repr__(self) -> str:
        return f"BufferMemory(messages={len(self.messages)}, ~{self.token_count()} tokens)"


if __name__ == "__main__":
    buf = BufferMemory(max_messages=6, max_tokens=200)

    for i in range(5):
        buf.add("user", f"Query number {i}: what is the status of order {i}?")
        buf.add("assistant", f"Order {i} is shipped. Tracking: TRK{i:04d}.")

    print(buf)
    print(f"Messages kept: {len(buf.get())}")
    for m in buf.get():
        print(f"  [{m['role']}] {m['content'][:60]}")
    assert len(buf.get()) <= 6, "max_messages eviction failed"
    assert buf.token_count() <= 200, "token eviction failed"
    assert buf.get()[0]["role"] == "user", "buffer must start with a user turn (evict in pairs!)"
    print("\nAll eviction checks passed.")
