"""
M03 Lab — Conversation Manager (Solution)
===========================================
Build a multi-turn conversation manager that maintains
full message history across API calls.
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


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

        This method:
        1. Appends the user message to self.messages
        2. Calls client.messages.create with the full message history
        3. Appends the assistant response to self.messages
        4. Returns the response text
        """
        # Step 1: Append the user message
        self.messages.append({"role": "user", "content": user_message})

        # Step 2: Call the API with full history
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            messages=self.messages,
        )

        # Step 3: Extract response text
        response_text = response.content[0].text

        # Step 4: Append assistant response to history
        self.messages.append({"role": "assistant", "content": response_text})

        # Step 5: Return the response
        return response_text

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
