"""
M08 Lab - Step 3: Auto-Summarizing Conversation Manager (Solution)
===================================================================
Complete solution: an AutoSummarizeManager that compresses old messages
into a summary when the conversation hits 80% of its token budget.

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
# OBSERVATION HELPERS
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
# SOLUTION: AutoSummarizeManager
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
        """Initialize the auto-summarize manager."""
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.threshold = threshold
        self.summarize_count = 0
        # Step 1: Initialize empty messages list
        self.messages = []

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for a list of messages plus system prompt."""
        # Step 2: Estimate tokens
        return (len(self.system_prompt) + len(json.dumps(messages))) // 4

    def _should_summarize(self) -> bool:
        """Check if current token usage exceeds the threshold."""
        # Step 3: Check threshold
        return self._estimate_tokens(self.messages) >= self.max_tokens * self.threshold

    def _summarize_old_messages(self) -> None:
        """Compress old messages into a summary."""
        # Step 4: Calculate split point -- keep the last 1/3 of messages intact
        split_at = max(2, (len(self.messages) * 2) // 3)
        old_messages = self.messages[:split_at]
        recent_messages = self.messages[split_at:]

        # Step 5: Record tokens before summarization
        tokens_before = self._estimate_tokens(self.messages)

        # Step 6: Build summarization prompt from old messages
        conversation_text = ""
        for msg in old_messages:
            role = msg["role"].upper()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n\n"

        summarize_prompt = (
            "Summarize this conversation so far in 2-3 sentences. Focus on "
            "the key topics discussed and any important facts established.\n\n"
            f"Conversation:\n{conversation_text}"
        )

        summary_response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": summarize_prompt}],
        )

        # Step 7: Extract summary text
        summary_text = ""
        for block in summary_response.content:
            if hasattr(block, "text"):
                summary_text += block.text

        # Step 8: Build new messages list with summary + recent messages
        summary_message = {
            "role": "assistant",
            "content": f"[Summary of earlier conversation]: {summary_text}",
        }

        # Ensure role alternation: if first recent message is also "assistant",
        # insert a bridging user message
        new_messages = [summary_message]
        if recent_messages and recent_messages[0]["role"] == "assistant":
            new_messages.append({"role": "user", "content": "(continuing conversation)"})
        new_messages.extend(recent_messages)

        self.messages = new_messages

        # Step 9: Record tokens after and log
        tokens_after = self._estimate_tokens(self.messages)
        self.summarize_count += 1
        observe_summarize(len(old_messages), tokens_before, tokens_after)
        print(f'[SUMMARIZE] Summary: "{summary_text[:100]}..."')

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        # Step 10: Append user message
        self.messages.append({"role": "user", "content": text})

    def send(self) -> str:
        """Send the conversation to Claude and append the response."""
        # Step 11: Check if summarization is needed, then call API
        if self._should_summarize():
            self._summarize_old_messages()

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            messages=self.messages,
        )

        # Step 12: Extract text and append to history
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text

        self.messages.append({"role": "assistant", "content": assistant_text})

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the current message history."""
        # Step 13: Return messages
        return self.messages

    def get_token_count(self) -> int:
        """Return estimated token count for current history."""
        return self._estimate_tokens(self.messages) if self.messages else 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M08 Lab - Step 3: Auto-Summarizing Conversation Manager (SOLUTION)")
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
