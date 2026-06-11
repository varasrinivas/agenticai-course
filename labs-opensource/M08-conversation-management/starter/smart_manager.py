"""
M08 Lab - Step 3: SmartConversationManager
===========================================
Auto-summarization when input tokens cross a threshold + JSON persistence.
Run: python smart_manager.py
"""

import json
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


class SmartConversationManager:
    """Full-featured manager with summarization and persistence."""

    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        model: str = "mistral",
        token_threshold: int = 8_000,   # lower for Mistral's 32K context
        recent_turns_to_keep: int = 4,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.messages: list = []
        self.token_threshold = token_threshold
        self.recent_turns_to_keep = recent_turns_to_keep
        self.summary: Optional[str] = None
        self.summary_history: list = []
        self.last_input_tokens = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _should_summarize(self) -> bool:
        """(COMPLETE)"""
        return self.last_input_tokens > self.token_threshold

    def _summarize_old_messages(self) -> None:
        """Use Mistral to summarize older messages.

        TODO:
        1. keep_count = self.recent_turns_to_keep * 2   (user+assistant pairs)
           If len(self.messages) <= keep_count: return (nothing to do)
        2. old_messages = self.messages[:-keep_count]
           recent_messages = self.messages[-keep_count:]
        3. Build a summary prompt:
           "Summarize this conversation concisely. Preserve: key decisions,
            user preferences, important facts. Skip: greetings, filler.\\n\\n"
           + one "role: content" line per old message
        4. Call the model (system: "You are a conversation summarizer. Be concise.")
        5. If self.summary already exists, chain it:
           new_summary = f"Previous context: {self.summary}\\n\\nRecent: {new_summary}"
        6. Set self.summary, append a record to self.summary_history
           ({"timestamp": time.time(), "messages_summarized": len(old_messages)})
        7. Replace self.messages with:
           [{"role": "user", "content": f"[Conversation summary: {self.summary}]"},
            {"role": "assistant", "content": "Understood. I have the conversation context."},
            *recent_messages]
        8. On ANY exception: self.messages = recent_messages  ← graceful fallback,
           never crash the conversation because a summary failed
        """
        pass  # Remove this line when you add your code

    def send(self, user_message: str) -> str:
        """Send with automatic summarization when needed.

        TODO:
        1. Append the user message
        2. Call the API with [system] + self.messages
        3. Record usage: self.last_input_tokens = usage.prompt_tokens, and
           accumulate the running totals
        4. Append + capture the assistant text
        5. AFTER the successful reply: if self._should_summarize():
               self._summarize_old_messages()
        6. Return the assistant text
        7. On exception: pop the user message, raise RuntimeError
        """
        pass  # Remove this line when you add your code

    # ── Persistence (COMPLETE) ──
    def save(self, filepath: str) -> None:
        """Persist conversation state to a JSON file."""
        state = {
            "system_prompt": self.system_prompt,
            "model": self.model,
            "messages": self.messages,
            "summary": self.summary,
            "summary_history": self.summary_history,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "saved_at": time.time(),
        }
        Path(filepath).write_text(json.dumps(state, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, filepath: str) -> "SmartConversationManager":
        """Load conversation state from a JSON file."""
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        mgr = cls(system_prompt=data["system_prompt"], model=data["model"])
        mgr.messages = data["messages"]
        mgr.summary = data.get("summary")
        mgr.summary_history = data.get("summary_history", [])
        mgr.total_input_tokens = data.get("total_input_tokens", 0)
        mgr.total_output_tokens = data.get("total_output_tokens", 0)
        return mgr


# ── Test harness (COMPLETE) ──
if __name__ == "__main__":
    # Low threshold so summarization fires within a few verbose turns
    manager = SmartConversationManager(
        token_threshold=3_000,
        recent_turns_to_keep=4,
        system_prompt="You are a helpful coding assistant.",
    )

    turns = [
        "Help me build a REST API with FastAPI. Explain the project structure in detail.",
        "Now explain how to add a database with SQLAlchemy, including models and migrations.",
        "Add JWT authentication with refresh tokens. Show the full flow.",
        "How do I write tests for all of this with pytest?",
        "What about deployment — Docker, environment variables, the works?",
    ]
    for i, t in enumerate(turns, 1):
        reply = manager.send(t)
        summarized = " [SUMMARIZED]" if manager.summary_history and \
            manager.summary_history[-1].get("messages_summarized") and i > 1 else ""
        print(f"Turn {i}: last_input={manager.last_input_tokens} tokens, "
              f"stored={len(manager.messages)} msgs{summarized}")

    print(f"\nSummaries created: {len(manager.summary_history)}")

    manager.save("conversation_state.json")
    restored = SmartConversationManager.load("conversation_state.json")
    print(f"Restored: {len(restored.messages)} messages, summary={'yes' if restored.summary else 'no'}")
    print(f"\nRestored agent says: {restored.send('Where were we? One sentence.')[:200]}")
