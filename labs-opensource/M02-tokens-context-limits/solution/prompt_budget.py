"""
M02 Lab - Step 2: The PromptBudget Class — SOLUTION
====================================================
Run: python prompt_budget.py
"""

from __future__ import annotations

import json
import tiktoken
from openai import OpenAI


class PromptBudget:
    """Track and manage token usage across a conversation."""

    TOKENS_PER_MESSAGE = 4    # role + content markers + sep
    TOKENS_REPLY_PRIMER = 3   # assistant reply primer tokens

    def __init__(self, model: str = "mistral", max_context: int = 32_000):
        self.model = model
        self.max_context = max_context
        self._enc = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(self, text: str) -> int:
        """Count tokens in a plain string."""
        return len(self._enc.encode(text))

    def _count_messages(self, messages: list[dict]) -> int:
        """Count tokens for a messages list including overhead."""
        total = self.TOKENS_REPLY_PRIMER
        for msg in messages:
            total += self.TOKENS_PER_MESSAGE
            total += len(self._enc.encode(msg.get("role", "")))
            total += len(self._enc.encode(msg.get("content", "")))
        return total

    def _count_tools(self, tools: list[dict] | None) -> int:
        """Rough estimate: serialize tools to JSON and count tokens."""
        if not tools:
            return 0
        return len(self._enc.encode(json.dumps(tools)))

    def remaining(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        reserve_output: int = 512,
    ) -> int:
        """Return how many tokens are left for new messages + output."""
        used = self._count_messages(messages) + self._count_tools(tools)
        return self.max_context - used - reserve_output

    def fits(
        self,
        text: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        reserve_output: int = 512,
    ) -> bool:
        """True if adding `text` as a new message still fits in budget."""
        new_msg_tokens = self.estimate_tokens(text) + self.TOKENS_PER_MESSAGE
        return self.remaining(messages, tools, reserve_output) >= new_msg_tokens

    def truncate_history(
        self,
        messages: list[dict],
        reserve_output: int = 512,
    ) -> list[dict]:
        """Drop oldest non-system messages until the conversation fits.

        Always preserves the first message if it's the system prompt.
        Returns a new list — does not mutate the input.
        """
        result = list(messages)
        start = 1 if result and result[0].get("role") == "system" else 0

        while True:
            tokens_used = self._count_messages(result)
            headroom = self.max_context - tokens_used - reserve_output
            if headroom >= 0:
                break
            if len(result) <= start + 1:
                break  # can't drop any more
            result.pop(start)  # remove oldest non-system message

        return result


# ── Demo: 4-turn conversation with budget checks ──
def main():
    budget = PromptBudget(model="mistral", max_context=32_000)
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    system = {"role": "system", "content": "You are a concise coding assistant."}
    history: list[dict] = [system]

    turns = [
        "What is a Python list comprehension?",
        "Show me an example that squares even numbers from 1 to 20.",
        "How does that compare to a regular for-loop?",
        "What's the memory usage difference?",
    ]

    for user_text in turns:
        print(f"\nUser: {user_text}")
        print(f"  Tokens remaining: {budget.remaining(history)}")

        if not budget.fits(user_text, history):
            print("  [truncating history to fit]")
            history = budget.truncate_history(history)

        history.append({"role": "user", "content": user_text})

        try:
            response = client.chat.completions.create(
                model="mistral",
                messages=history,
                max_tokens=256,
            )
            reply = response.choices[0].message.content
            history.append({"role": "assistant", "content": reply})
            print(f"Assistant: {reply[:120]}...")
        except Exception as e:
            print(f"  Error: {e}")
            history.pop()


if __name__ == "__main__":
    main()
