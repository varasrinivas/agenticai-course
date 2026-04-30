"""
M03 Lab — Conversation Manager
================================
Build a multi-turn conversation manager that maintains
full message history across API calls.
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


class ConversationManager:
    """Manages a multi-turn conversation with Claude, maintaining full history."""

    def __init__(self, system_prompt: str):
        """
        Initialize the conversation manager.

        Args:
            system_prompt: The system prompt that defines Claude's role.
        """
        self.system_prompt = system_prompt
        self.messages: list[dict] = []

    def send(self, user_message: str) -> str:
        """
        Send a user message and get Claude's response.

        This method must:
        1. Append the user message to self.messages
        2. Call client.messages.create with the full message history
        3. Append the assistant response to self.messages
        4. Return the response text

        Args:
            user_message: The user's message text.

        Returns:
            Claude's response text.
        """
        # TODO: Implement the send method.
        #
        # Step 1: Append {"role": "user", "content": user_message} to self.messages
        #
        # Step 2: Call client.messages.create with:
        #   - model=MODEL
        #   - max_tokens=1024
        #   - system=self.system_prompt
        #   - messages=self.messages  (the FULL history)
        #
        # Step 3: Extract the response text from the API response
        #
        # Step 4: Append {"role": "assistant", "content": response_text} to self.messages
        #
        # Step 5: Return the response text
        pass

    def get_history(self) -> list[dict]:
        """Return the full conversation history."""
        return self.messages

    def reset(self):
        """Clear the conversation history."""
        self.messages = []


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    system = (
        "You are a UCC filing research assistant. You help users understand "
        "UCC filings, search for filings, and explain legal terminology in "
        "plain English. Be concise and accurate."
    )

    manager = ConversationManager(system)

    turns = [
        "What is a UCC-1 filing?",
        "How long do they last?",
        "What happens when one expires?",
    ]

    print("=" * 60)
    print("Multi-Turn Conversation")
    print("=" * 60)

    for i, user_msg in enumerate(turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"USER: {user_msg}")
        try:
            response = manager.send(user_msg)
            print(f"CLAUDE: {response}")
        except Exception as e:
            print(f"[ERROR] {e}")

    # Show history summary
    print("\n" + "=" * 60)
    print("Conversation History Summary")
    print("=" * 60)
    history = manager.get_history()
    print(f"Total messages: {len(history)}")
    for msg in history:
        role = msg["role"].upper()
        preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        print(f"  [{role}] {preview}")
