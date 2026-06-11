"""
M08 Lab - Steps 1+2: ConversationManager + SlidingWindowManager
================================================================
Run: python conversation_manager.py
"""

from dataclasses import dataclass, field

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ── Step 1: Basic ConversationManager ────────────────────────
@dataclass
class ConversationManager:
    """Full-history conversation manager with token tracking."""

    system_prompt: str = "You are a helpful assistant."
    model: str = "mistral"
    messages: list = field(default_factory=list)

    def __post_init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list:
        """Return messages with system prompt prepended. (COMPLETE)"""
        return [{"role": "system", "content": self.system_prompt}] + list(self.messages)

    def send(self, user_message: str) -> str:
        """Send a message and get the model's response.

        TODO:
        1. self.add_user_message(user_message)
        2. response = client.chat.completions.create(model=self.model,
               messages=self.get_messages())
        3. If response.usage: accumulate prompt_tokens / completion_tokens
           into self.total_input_tokens / self.total_output_tokens
        4. Append + return the assistant text
        5. On exception: self.messages.pop() (remove the failed user message),
           then raise RuntimeError(f"API call failed: {e}")
        """
        pass  # Remove this line when you add your code

    def get_token_usage(self) -> dict:
        return {
            "total_input": self.total_input_tokens,
            "total_output": self.total_output_tokens,
            "messages": len(self.messages),
        }


# ── Step 2: SlidingWindowManager ─────────────────────────────
class SlidingWindowManager(ConversationManager):
    """Stores everything, but only SENDS the most recent N messages."""

    def __init__(self, window_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.window_size = window_size

    def get_messages(self) -> list:
        """Return system prompt + only the most recent N messages.

        TODO:
        1. windowed = the last self.window_size entries of self.messages
           (or all of them if there are fewer)
        2. GOTCHA: if windowed starts with an "assistant" message, drop it —
           history sent to the API should start with a user turn
        3. Return [{"role": "system", ...}] + windowed
        """
        pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Basic ConversationManager (full history)")
    print("=" * 50)
    mgr = ConversationManager(system_prompt="You are a concise coding tutor. Answer in 1-2 sentences.")
    for q in ["What is a list comprehension in Python?", "Show me an example with filtering."]:
        print(f"\nQ: {q}")
        print(f"A: {mgr.send(q)[:150]}")
        print(f"   usage so far: {mgr.get_token_usage()}")

    print("\n" + "=" * 50)
    print("TEST 2: SlidingWindowManager (window_size=6)")
    print("=" * 50)
    win = SlidingWindowManager(window_size=6, system_prompt="You are a concise coding tutor.")
    for q in ["What is Python?", "What are variables?", "Explain loops.",
              "What are functions?", "Explain classes.", "What is inheritance?"]:
        win.send(q)
        print(f"Q: {q}  (stored={len(win.messages)}, sent={len(win.get_messages()) - 1})")

    print(f"\nStored: {len(win.messages)} messages")
    print(f"Sent (excl. system): {len(win.get_messages()) - 1} messages")
