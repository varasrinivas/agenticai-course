"""
M08 Lab - Step 3: Auto-Summarizing Conversation Manager (Starter)
==================================================================
Build an AutoSummarizeManager that compresses old messages into a
summary when the conversation hits 80% of its token budget.

KEY CONCEPT: Sliding windows lose information forever. Summarization
preserves the GIST of old messages in fewer tokens, so Claude retains
awareness of earlier topics even after compression.

Usage:
    python auto_summarize.py
"""

import json
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are a UCC filing research assistant. Help users understand "
    "UCC filings, lien risks, and secured transactions. Provide clear, "
    "concise answers. When referencing prior conversation, demonstrate "
    "you remember the context."
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
    pct = (token_count / max_tokens * 100) if max_tokens > 0 else 0
    threshold_marker = " *** ABOVE 80% THRESHOLD ***" if pct >= 80 else ""
    print(f"[TOKENS] ~{token_count} / {max_tokens} ({pct:.0f}%){threshold_marker}")
    print(f"[HISTORY] {message_count} messages in history")


def observe_summarize(num_messages: int, tokens_before: int, tokens_after: int) -> None:
    """Log summarization event."""
    print(f"[SUMMARIZE] Compressed {num_messages} messages into summary "
          f"({tokens_before} tokens -> {tokens_after} tokens)")


# =============================================================================
# YOUR CODE: Implement AutoSummarizeManager
# =============================================================================

class AutoSummarizeManager:
    """
    Manages conversation history with automatic summarization.

    When the conversation reaches 80% of the token budget, the oldest
    messages are sent to Claude for summarization. The summary replaces
    those messages, dramatically reducing token usage while preserving
    context.
    """

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 2048,
        threshold: float = 0.8,
    ):
        """Initialize the auto-summarize manager.

        Args:
            system_prompt: The system prompt for Claude.
            max_tokens: Maximum token budget for conversation history.
            threshold: Fraction of budget that triggers summarization (default 0.8).
        """
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.threshold = threshold
        self.summarize_count = 0  # Track how many times we've summarized
        # ------------------------------------------------------------------
        # TODO 1: Initialize an empty messages list.
        # ------------------------------------------------------------------
        self.messages = None  # Replace with correct initialization

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for a list of messages plus system prompt."""
        # ------------------------------------------------------------------
        # TODO 2: Estimate tokens using:
        #   (len(self.system_prompt) + len(json.dumps(messages))) // 4
        # ------------------------------------------------------------------
        return 0

    def _should_summarize(self) -> bool:
        """Check if current token usage exceeds the threshold.

        Returns:
            True if tokens >= max_tokens * threshold.
        """
        # ------------------------------------------------------------------
        # TODO 3: Return True if _estimate_tokens(self.messages) >= max_tokens * threshold
        # ------------------------------------------------------------------
        return False

    def _summarize_old_messages(self) -> None:
        """Compress old messages into a summary.

        Steps:
        1. Split messages into "old" (first 2/3) and "recent" (last 1/3).
        2. Send old messages to Claude asking for a 2-3 sentence summary.
        3. Create a summary message: {"role": "assistant", "content": "[Summary of earlier conversation]: <summary>"}
        4. Replace self.messages with [summary_message] + recent_messages.
        5. Log the compression with observe_summarize.
        """
        # ------------------------------------------------------------------
        # TODO 4: Calculate the split point.
        #   split_at = max(2, (len(self.messages) * 2) // 3)
        #   old_messages = self.messages[:split_at]
        #   recent_messages = self.messages[split_at:]
        # ------------------------------------------------------------------
        pass

        # ------------------------------------------------------------------
        # TODO 5: Record tokens BEFORE summarization.
        #   tokens_before = self._estimate_tokens(self.messages)
        # ------------------------------------------------------------------
        pass

        # ------------------------------------------------------------------
        # TODO 6: Build a summarization prompt.
        #   Format old messages as a readable text block, then ask Claude:
        #   "Summarize this conversation so far in 2-3 sentences. Focus on
        #    the key topics discussed and any important facts established."
        #
        #   Call client.messages.create with:
        #     - model=MODEL
        #     - max_tokens=256
        #     - messages=[{"role": "user", "content": summarize_prompt}]
        # ------------------------------------------------------------------
        pass

        # ------------------------------------------------------------------
        # TODO 7: Extract the summary text from the response.
        # ------------------------------------------------------------------
        summary_text = ""
        pass

        # ------------------------------------------------------------------
        # TODO 8: Build new messages list:
        #   summary_message = {
        #       "role": "assistant",
        #       "content": f"[Summary of earlier conversation]: {summary_text}"
        #   }
        #   self.messages = [summary_message] + recent_messages
        #
        #   BUT: ensure role alternation! If the first recent message is also
        #   "assistant", we need to add a bridging user message.
        #   Insert {"role": "user", "content": "(continuing conversation)"} if needed.
        # ------------------------------------------------------------------
        pass

        # ------------------------------------------------------------------
        # TODO 9: Record tokens AFTER summarization and log.
        #   tokens_after = self._estimate_tokens(self.messages)
        #   self.summarize_count += 1
        #   observe_summarize(len(old_messages), tokens_before, tokens_after)
        #   print(f'[SUMMARIZE] Summary: "{summary_text[:100]}..."')
        # ------------------------------------------------------------------
        pass

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        # ------------------------------------------------------------------
        # TODO 10: Append a user message dict to self.messages.
        # ------------------------------------------------------------------
        pass

    def send(self) -> str:
        """Send the conversation to Claude and append the response.

        Before sending, check if summarization is needed.

        Returns:
            Claude's response text.
        """
        # ------------------------------------------------------------------
        # TODO 11: Check _should_summarize() and call _summarize_old_messages()
        # if needed. Then call client.messages.create with:
        #   - model=MODEL
        #   - max_tokens=1024
        #   - system=self.system_prompt
        #   - messages=self.messages
        # ------------------------------------------------------------------
        response = None  # Replace with your API call
        pass

        # ------------------------------------------------------------------
        # TODO 12: Extract text from response.content and append as assistant
        # message to self.messages.
        # ------------------------------------------------------------------
        assistant_text = ""
        pass

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the current message history."""
        # ------------------------------------------------------------------
        # TODO 13: Return self.messages.
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
    print("M08 Lab - Step 3: Auto-Summarizing Conversation Manager")
    print("=" * 60)

    manager = AutoSummarizeManager(max_tokens=2048)
    threshold_tokens = int(manager.max_tokens * manager.threshold)
    print(f"Token budget: {manager.max_tokens} tokens "
          f"(summarize at 80% = {threshold_tokens} tokens)")

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
        "How do fixture filings work?",
        "What is a debtor-in-possession?",
        "What is the difference between attachment and perfection?",
        "Give me a final summary of everything we covered",
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
    print(f"Final: {len(manager.get_history())} messages, "
          f"{manager.summarize_count} summarization events triggered")
    print(f"{'=' * 60}")
