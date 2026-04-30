"""
M08 Lab - Step 1: Full Conversation History (Solution)
======================================================
Complete solution: a ConversationManager that stores the entire message
history and sends it to Claude on every API call.

Usage:
    python full_history.py
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


def observe_tokens(token_count: int, message_count: int) -> None:
    """Log token and message count."""
    print(f"[TOKENS] Estimated tokens in conversation: ~{token_count}")
    print(f"[HISTORY] {message_count} messages in history")


# =============================================================================
# SOLUTION: ConversationManager
# =============================================================================

class ConversationManager:
    """
    Manages a multi-turn conversation with Claude by maintaining full history.

    The messages list grows with every turn. Every API call sends the
    complete history so Claude has full context.
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        """Initialize the conversation manager."""
        self.system_prompt = system_prompt
        # Step 1: Initialize empty messages list
        self.messages = []

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        # Step 2: Append user message
        self.messages.append({"role": "user", "content": text})

    def send(self) -> str:
        """Send the current conversation to Claude and append the response."""
        # Step 3: Call the API with full history
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            messages=self.messages,
        )

        # Step 4: Extract text from response
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text

        # Step 5: Append assistant response to history
        self.messages.append({"role": "assistant", "content": assistant_text})

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the full message history."""
        # Step 6: Return messages
        return self.messages

    def get_token_count(self) -> int:
        """Estimate the token count for the current conversation."""
        # Step 7: Estimate tokens (system prompt + messages)
        total_chars = len(self.system_prompt) + len(json.dumps(self.messages))
        return total_chars // 4


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M08 Lab - Step 1: Full Conversation History (SOLUTION)")
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
