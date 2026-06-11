"""
M08 Lab - Steps 1+2: ConversationManager + SlidingWindowManager — SOLUTION
===========================================================================
Run: python conversation_manager.py
"""

from dataclasses import dataclass, field

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


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
        return [{"role": "system", "content": self.system_prompt}] + list(self.messages)

    def send(self, user_message: str) -> str:
        self.add_user_message(user_message)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.get_messages(),
            )
            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
            assistant_text = response.choices[0].message.content
            self.add_assistant_message(assistant_text)
            return assistant_text
        except Exception as e:
            self.messages.pop()  # remove failed user message
            raise RuntimeError(f"API call failed: {e}") from e

    def get_token_usage(self) -> dict:
        return {
            "total_input": self.total_input_tokens,
            "total_output": self.total_output_tokens,
            "messages": len(self.messages),
        }


class SlidingWindowManager(ConversationManager):
    """Stores everything, but only SENDS the most recent N messages."""

    def __init__(self, window_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.window_size = window_size

    def get_messages(self) -> list:
        if len(self.messages) <= self.window_size:
            windowed = list(self.messages)
        else:
            windowed = self.messages[-self.window_size:]

        # History sent to the API should start with a user turn
        if windowed and windowed[0]["role"] == "assistant":
            windowed = windowed[1:]

        return [{"role": "system", "content": self.system_prompt}] + windowed


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
