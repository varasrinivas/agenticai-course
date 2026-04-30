"""
M08 Lab - Step 2: Sliding Window Conversation Manager (Solution)
=================================================================
Complete solution: a SlidingWindowManager that drops the oldest messages
when the conversation exceeds a token budget.

Usage:
    python sliding_window.py
"""

import json
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a UCC filing research assistant. Help users understand "
    "UCC filings, lien risks, and secured transactions. Provide clear, "
    "concise answers."
)


# =============================================================================
# OBSERVATION HELPERS
# =============================================================================

def observe(label: str, message: str) -> None:
    """Print a labeled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tokens(token_count: int, max_tokens: int, message_count: int) -> None:
    """Log token usage against budget."""
    print(f"[TOKENS] ~{token_count} / {max_tokens}")
    print(f"[HISTORY] {message_count} messages in history")


def observe_window(dropped: int, tokens_freed: int) -> None:
    """Log window sliding event."""
    print(f"[WINDOW] Dropped {dropped} oldest messages ({tokens_freed} tokens freed)")


# =============================================================================
# SOLUTION: SlidingWindowManager
# =============================================================================

class SlidingWindowManager:
    """
    Manages conversation history with a sliding window that drops
    oldest messages when the token budget is exceeded.
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT, max_tokens: int = 2048):
        """Initialize the sliding window manager."""
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        # Step 1: Initialize empty messages list
        self.messages = []

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for a list of messages plus system prompt."""
        # Step 2: Estimate tokens
        return (len(self.system_prompt) + len(json.dumps(messages))) // 4

    def _trim_history(self) -> None:
        """Trim oldest messages to stay within token budget."""
        # Step 3: Drop oldest message pairs until under budget
        while self._estimate_tokens(self.messages) > self.max_tokens and len(self.messages) > 2:
            tokens_before = self._estimate_tokens(self.messages)

            # Remove 2 messages at a time (user + assistant pair) for role alternation
            dropped_count = 0
            while (
                self._estimate_tokens(self.messages) > self.max_tokens
                and len(self.messages) > 2
            ):
                self.messages.pop(0)
                dropped_count += 1
                # If we just removed a user message and the next is assistant,
                # remove that too to keep pairs aligned
                if (
                    len(self.messages) > 2
                    and self.messages[0]["role"] == "assistant"
                ):
                    self.messages.pop(0)
                    dropped_count += 1
                break  # One pair per trim cycle for cleaner logging

            tokens_after = self._estimate_tokens(self.messages)
            observe_window(dropped_count, tokens_before - tokens_after)

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        # Step 4: Append user message
        self.messages.append({"role": "user", "content": text})

    def send(self) -> str:
        """Send the conversation to Claude and append the response."""
        # Step 5: Trim history, then call API
        self._trim_history()

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            messages=self.messages,
        )

        # Step 6: Extract text and append to history
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text

        self.messages.append({"role": "assistant", "content": assistant_text})

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the current message history."""
        # Step 7: Return messages
        return self.messages

    def get_token_count(self) -> int:
        """Return estimated token count for current history."""
        return self._estimate_tokens(self.messages) if self.messages else 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M08 Lab - Step 2: Sliding Window Conversation Manager (SOLUTION)")
    print("=" * 60)

    # Use a smaller budget to force window sliding during the test
    manager = SlidingWindowManager(max_tokens=2048)
    print(f"Token budget: {manager.max_tokens} tokens")

    test_questions = [
        "What is a UCC-1 filing?",
        "Who files a UCC-1?",
        "What is the purpose of perfecting a security interest?",
        "What collateral types can be covered by a UCC filing?",
        "What is a continuation statement?",
        "What is a UCC-3 amendment?",
        "How do I search for existing UCC filings?",
        "What are the risks of not filing a UCC-1?",
        "What is a purchase money security interest?",
        "How do UCC filings work in bankruptcy?",
        "What is a blanket lien?",
        "Summarize what we discussed",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Turn {i}/{len(test_questions)} ---")

        observe("USER", question)
        manager.add_user_message(question)

        response = manager.send()

        observe("ASSISTANT", response[:200] + "..." if len(response) > 200 else response)
        observe_tokens(
            manager.get_token_count(),
            manager.max_tokens,
            len(manager.get_history()),
        )

    print(f"\n{'=' * 60}")
    print(f"Final: {len(manager.get_history())} messages visible "
          f"(window dropped older messages to stay under {manager.max_tokens})")
    print(f"{'=' * 60}")
