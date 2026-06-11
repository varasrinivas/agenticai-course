"""
M08 Lab - Step 3: SmartConversationManager — SOLUTION
======================================================
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
        token_threshold: int = 8_000,
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
        return self.last_input_tokens > self.token_threshold

    def _summarize_old_messages(self) -> None:
        """Use Mistral to summarize older messages."""
        keep_count = self.recent_turns_to_keep * 2  # user+assistant pairs
        if len(self.messages) <= keep_count:
            return

        old_messages = self.messages[:-keep_count]
        recent_messages = self.messages[-keep_count:]

        summary_prompt = (
            "Summarize this conversation concisely. "
            "Preserve: key decisions, user preferences, important facts. "
            "Skip: greetings, filler.\n\n"
        )
        for msg in old_messages:
            summary_prompt += f"{msg['role']}: {msg['content']}\n"

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a conversation summarizer. Be concise."},
                    {"role": "user", "content": summary_prompt},
                ],
            )
            new_summary = response.choices[0].message.content

            if self.summary:
                new_summary = f"Previous context: {self.summary}\n\nRecent: {new_summary}"

            self.summary = new_summary
            self.summary_history.append({
                "timestamp": time.time(),
                "messages_summarized": len(old_messages),
            })

            self.messages = [
                {"role": "user", "content": f"[Conversation summary: {self.summary}]"},
                {"role": "assistant", "content": "Understood. I have the conversation context."},
                *recent_messages,
            ]
        except Exception:
            # Graceful fallback: plain truncation. Never crash the conversation.
            self.messages = recent_messages

    def send(self, user_message: str) -> str:
        """Send with automatic summarization when needed."""
        self.messages.append({"role": "user", "content": user_message})

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}] + self.messages,
            )
            if response.usage:
                self.last_input_tokens = response.usage.prompt_tokens
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

            assistant_text = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_text})

            if self._should_summarize():
                self._summarize_old_messages()

            return assistant_text

        except Exception as e:
            self.messages.pop()
            raise RuntimeError(f"API call failed: {e}") from e

    # ── Persistence ──
    def save(self, filepath: str) -> None:
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
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        mgr = cls(system_prompt=data["system_prompt"], model=data["model"])
        mgr.messages = data["messages"]
        mgr.summary = data.get("summary")
        mgr.summary_history = data.get("summary_history", [])
        mgr.total_input_tokens = data.get("total_input_tokens", 0)
        mgr.total_output_tokens = data.get("total_output_tokens", 0)
        return mgr


if __name__ == "__main__":
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
        manager.send(t)
        print(f"Turn {i}: last_input={manager.last_input_tokens} tokens, "
              f"stored={len(manager.messages)} msgs")

    print(f"\nSummaries created: {len(manager.summary_history)}")

    manager.save("conversation_state.json")
    restored = SmartConversationManager.load("conversation_state.json")
    print(f"Restored: {len(restored.messages)} messages, summary={'yes' if restored.summary else 'no'}")
    print(f"\nRestored agent says: {restored.send('Where were we? One sentence.')[:200]}")
