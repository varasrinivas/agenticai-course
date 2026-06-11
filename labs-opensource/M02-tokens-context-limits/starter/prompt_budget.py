"""
M02 Lab - Step 2: The PromptBudget Class
=========================================
Track token usage across a conversation and auto-truncate when it won't fit.
Run: python prompt_budget.py
Requires: pip install tiktoken openai
"""

from __future__ import annotations

import json
import tiktoken
from openai import OpenAI


class PromptBudget:
    """Track and manage token usage across a conversation."""

    # Per-message overhead in cl100k_base terms
    TOKENS_PER_MESSAGE = 4    # role + content markers + sep
    TOKENS_REPLY_PRIMER = 3   # assistant reply primer tokens

    def __init__(self, model: str = "mistral", max_context: int = 32_000):
        self.model = model
        self.max_context = max_context
        # cl100k_base is a close approximation for Mistral
        self._enc = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(self, text: str) -> int:
        """Count tokens in a plain string. (COMPLETE)"""
        return len(self._enc.encode(text))

    def _count_messages(self, messages: list[dict]) -> int:
        """Count tokens for a messages list including overhead. (COMPLETE)"""
        total = self.TOKENS_REPLY_PRIMER
        for msg in messages:
            total += self.TOKENS_PER_MESSAGE
            total += len(self._enc.encode(msg.get("role", "")))
            total += len(self._enc.encode(msg.get("content", "")))
        return total

    def _count_tools(self, tools: list[dict] | None) -> int:
        """Rough estimate: serialize tools to JSON and count. (COMPLETE)"""
        if not tools:
            return 0
        return len(self._enc.encode(json.dumps(tools)))

    def remaining(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        reserve_output: int = 512,
    ) -> int:
        """Return how many tokens are left for new messages + output.

        TODO: used = self._count_messages(messages) + self._count_tools(tools)
              return self.max_context - used - reserve_output
        """
        pass  # Remove this line when you add your code

    def fits(
        self,
        text: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        reserve_output: int = 512,
    ) -> bool:
        """True if adding `text` as a new message still fits in budget.

        TODO: the new message costs estimate_tokens(text) + TOKENS_PER_MESSAGE.
              Compare against self.remaining(...).
        """
        pass  # Remove this line when you add your code

    def truncate_history(
        self,
        messages: list[dict],
        reserve_output: int = 512,
    ) -> list[dict]:
        """Drop oldest non-system messages until the conversation fits.

        TODO:
        - Work on a COPY of messages (don't mutate the input)
        - If the first message is the system prompt, never drop it
          (start dropping from index 1, else index 0)
        - While _count_messages(result) + reserve_output > max_context:
            - stop if only the system prompt + one message remain
            - otherwise pop the oldest non-system message
        - Return the new list
        """
        pass  # Remove this line when you add your code


# ── Demo: 4-turn conversation with budget checks (COMPLETE) ──
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
            history.pop()  # keep state consistent


if __name__ == "__main__":
    main()
