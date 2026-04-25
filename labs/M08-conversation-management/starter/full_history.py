"""
M08 Lab - Step 1: Full Conversation History (Starter)
=====================================================
Build a ConversationManager that stores the entire message history
and sends it to Claude on every API call.

KEY CONCEPT: Claude is stateless. Every messages.create() call starts
from scratch. YOUR code must maintain the conversation history and send
it every time. The messages array IS the memory.

Usage:
    python full_history.py
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


def observe_tokens(token_count: int, message_count: int) -> None:
    """Log token and message count."""
    print(f"[TOKENS] Estimated tokens in conversation: ~{token_count}")
    print(f"[HISTORY] {message_count} messages in history")


# =============================================================================
# YOUR CODE: Implement ConversationManager
# =============================================================================

class ConversationManager:
    """
    Manages a multi-turn conversation with Claude by maintaining full history.

    The messages list grows with every turn. Every API call sends the
    complete history so Claude has full context.
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        """Initialize the conversation manager.

        Args:
            system_prompt: The system prompt for Claude.
        """
        self.system_prompt = system_prompt
        # ------------------------------------------------------------------
        # TODO 1: Initialize an empty list to store messages.
        # Each message is a dict: {"role": "user"|"assistant", "content": "..."}
        # ------------------------------------------------------------------
        self.messages = None  # Replace with correct initialization
        pass

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history.

        Args:
            text: The user's message text.
        """
        # ------------------------------------------------------------------
        # TODO 2: Append a user message dict to self.messages.
        # Format: {"role": "user", "content": text}
        # ------------------------------------------------------------------
        pass

    def send(self) -> str:
        """Send the current conversation to Claude and append the response.

        Returns:
            Claude's response text.
        """
        # ------------------------------------------------------------------
        # TODO 3: Call client.messages.create with:
        #   - model=MODEL
        #   - max_tokens=1024
        #   - system=self.system_prompt
        #   - messages=self.messages
        # ------------------------------------------------------------------
        response = None  # Replace with your API call
        pass

        # ------------------------------------------------------------------
        # TODO 4: Extract the text from response.content.
        # Loop through response.content blocks, collect text from blocks
        # that have a .text attribute.
        # ------------------------------------------------------------------
        assistant_text = ""
        pass

        # ------------------------------------------------------------------
        # TODO 5: Append the assistant's response to self.messages.
        # Format: {"role": "assistant", "content": assistant_text}
        # ------------------------------------------------------------------
        pass

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the full message history."""
        # ------------------------------------------------------------------
        # TODO 6: Return the messages list.
        # ------------------------------------------------------------------
        return []

    def get_token_count(self) -> int:
        """Estimate the token count for the current conversation.

        Uses a simple heuristic: len(str(messages)) // 4
        (approximately 4 characters per token).

        Returns:
            Estimated token count.
        """
        # ------------------------------------------------------------------
        # TODO 7: Estimate tokens using len(json.dumps(self.messages)) // 4
        # Include the system prompt in the estimate.
        # ------------------------------------------------------------------
        return 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M08 Lab - Step 1: Full Conversation History")
    print("=" * 60)

    manager = ConversationManager()

    test_questions = [
        "What is a UCC-1 filing?",
        "How long does a UCC-1 last before it lapses?",
        "What happens when a filing lapses?",
        "Can a filing be renewed?",
        "Summarize everything we discussed",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Turn {i}/{len(test_questions)} ---")

        observe("USER", question)
        manager.add_user_message(question)
        observe_tokens(manager.get_token_count(), len(manager.get_history()))

        response = manager.send()

        observe("ASSISTANT", response)
        observe_tokens(manager.get_token_count(), len(manager.get_history()))

    print(f"\n{'=' * 60}")
    print(f"Final conversation: {len(manager.get_history())} messages, "
          f"~{manager.get_token_count()} estimated tokens")
    print(f"{'=' * 60}")
