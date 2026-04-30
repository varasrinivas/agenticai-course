"""
M08 Lab - Step 2: Sliding Window Conversation Manager (Starter)
================================================================
Build a SlidingWindowManager that drops the oldest messages when the
conversation exceeds a token budget.

KEY CONCEPT: Full history works for short conversations, but tokens cost
money and context windows have limits. A sliding window keeps only the
most recent messages, trading long-term memory for cost control.

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
# OBSERVATION HELPERS (complete -- do not modify)
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
# YOUR CODE: Implement SlidingWindowManager
# =============================================================================

class SlidingWindowManager:
    """
    Manages conversation history with a sliding window that drops
    oldest messages when the token budget is exceeded.
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT, max_tokens: int = 2048):
        """Initialize the sliding window manager.

        Args:
            system_prompt: The system prompt for Claude.
            max_tokens: Maximum token budget for conversation history.
        """
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        # ------------------------------------------------------------------
        # TODO 1: Initialize an empty messages list.
        # ------------------------------------------------------------------
        self.messages = None  # Replace with correct initialization

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for a list of messages.

        Uses len(json.dumps(messages)) // 4 as a simple heuristic.
        Include the system prompt in the estimate.

        Args:
            messages: List of message dicts.

        Returns:
            Estimated token count.
        """
        # ------------------------------------------------------------------
        # TODO 2: Estimate tokens for the given messages plus system prompt.
        # Use: (len(self.system_prompt) + len(json.dumps(messages))) // 4
        # ------------------------------------------------------------------
        return 0

    def _trim_history(self) -> None:
        """Trim oldest messages to stay within token budget.

        Keep removing the oldest message (index 0) until the estimated
        token count is under self.max_tokens. Log each trim event.

        IMPORTANT: Never drop all messages -- always keep at least the
        last 2 messages (the most recent user + assistant pair).
        """
        # ------------------------------------------------------------------
        # TODO 3: While _estimate_tokens(self.messages) > self.max_tokens
        #   and len(self.messages) > 2:
        #
        #   a) Record the token count BEFORE trimming.
        #   b) Remove messages from the front of the list, 2 at a time
        #      (user + assistant pairs) to maintain role alternation.
        #   c) Record the token count AFTER trimming.
        #   d) Call observe_window(dropped_count, tokens_before - tokens_after)
        # ------------------------------------------------------------------
        pass

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        # ------------------------------------------------------------------
        # TODO 4: Append a user message dict to self.messages.
        # ------------------------------------------------------------------
        pass

    def send(self) -> str:
        """Send the conversation to Claude and append the response.

        Before sending, trim the history to stay within budget.

        Returns:
            Claude's response text.
        """
        # ------------------------------------------------------------------
        # TODO 5: Call self._trim_history() first.
        # Then call client.messages.create with:
        #   - model=MODEL
        #   - max_tokens=1024
        #   - system=self.system_prompt
        #   - messages=self.messages
        # ------------------------------------------------------------------
        response = None  # Replace with your API call
        pass

        # ------------------------------------------------------------------
        # TODO 6: Extract text from response.content and append as assistant
        # message to self.messages.
        # ------------------------------------------------------------------
        assistant_text = ""
        pass

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the current message history."""
        # ------------------------------------------------------------------
        # TODO 7: Return self.messages.
        # ------------------------------------------------------------------
        return []

    def get_token_count(self) -> int:
        """Return estimated token count for current history."""
        return self._estimate_tokens(self.messages) if self.messages else 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M08 Lab - Step 2: Sliding Window Conversation Manager")
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
