"""
M03B Lab: The ContextBudget Class — SOLUTION
=============================================
Run the self-test: python context_budget.py
Run the full lab:  copy this over starter/context_budget.py, then python diagnose.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import tiktoken
from openai import OpenAI

# cl100k_base is OpenAI's tokenizer — a good approximation for Mistral/Llama
_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text) -> int:
    """Count tokens in a string or JSON-serializable object."""
    if not isinstance(text, str):
        text = json.dumps(text, separators=(",", ":"))
    return max(1, len(_enc.encode(text)))


MODEL_LIMITS = {
    "mistral": 32_768,
    "mixtral": 32_768,
    "llama3": 131_072,
    "gemma2": 8_192,
}

SUMMARY_PROMPT = """Summarize this conversation in 3-5 sentences.
CRITICAL: preserve every order ID, customer ID, tracking number, exact dollar amount,
and explicit user decision. Drop only retry errors, duplicate results, and resolved detours.

Conversation:
{transcript}

Summary:"""


def summarize_history(history: list[dict], keep_recent: int = 4) -> list[dict]:
    """Summarize older turns; keep the last `keep_recent` turns verbatim.

    GOTCHA: this is a SEPARATE model call — never ask the main model to
    summarize the context it is currently reading.
    """
    if len(history) <= keep_recent:
        return history

    older = history[:-keep_recent]
    recent = history[-keep_recent:]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in older)

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    try:
        result = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(transcript=transcript)}],
            max_tokens=250,
        )
        summary_text = result.choices[0].message.content or ""
    except Exception as e:
        print(f"Summarization failed: {e}; falling back to truncation.")
        return recent

    summary_msg = {
        "role": "user",
        "content": f"[Summary of {len(older)} earlier turns] {summary_text}",
    }
    return [summary_msg] + recent


@dataclass
class ContextBudget:
    """Accounts for and curates the six layers of a local model context."""

    system_prompt: str = ""
    tool_definitions: list = field(default_factory=list)
    retrieved_docs: list[str] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)
    current_user_message: str = ""
    model: str = "mistral"
    reserve_output: int = 2048

    @property
    def max_tokens(self) -> int:
        return MODEL_LIMITS.get(self.model, 32_768) - self.reserve_output

    def account(self) -> dict[str, int]:
        """Per-layer token breakdown."""
        return {
            "system": count_tokens(self.system_prompt),
            "tools": count_tokens(self.tool_definitions) if self.tool_definitions else 0,
            "retrieved": sum(count_tokens(d) for d in self.retrieved_docs),
            "history": sum(count_tokens(m["content"]) for m in self.history),
            "tool_results": sum(count_tokens(r) for r in self.tool_results),
            "current": count_tokens(self.current_user_message),
        }

    def total(self) -> int:
        return sum(self.account().values())

    def remaining(self) -> int:
        return self.max_tokens - self.total()

    def fits(self) -> bool:
        return self.total() <= self.max_tokens

    def strategy(self) -> str:
        """Return recommended strategy based on budget utilization."""
        utilization = self.total() / self.max_tokens
        if utilization < 0.60:
            return "ok"           # plenty of room — no action needed
        elif utilization < 0.75:
            return "compress"     # crop tool definitions, compress tool results
        elif utilization < 0.90:
            return "summarize"    # summarize old history turns
        else:
            return "critical"     # emergency: system + last 2 turns + current only

    def crop(self) -> "ContextBudget":
        """Apply the recommended strategy in place. Returns self for chaining."""
        strat = self.strategy()
        if strat == "ok":
            return self

        if strat in ("compress", "summarize", "critical"):
            # Crop tool definitions when in trouble (saves ~900 tok for 4 tools)
            self.tool_definitions = []

        if strat in ("summarize", "critical"):
            keep = 2 if strat == "critical" else 4
            self.history = self.history[-keep:]
            self.tool_results = self.tool_results[-2:]

        if strat == "critical":
            # Nuclear option: drop all retrieved docs too
            self.retrieved_docs = []

        return self

    def checkpoint(self, keep_recent: int = 4) -> "ContextBudget":
        """Summarize old history turns. Call when strategy() == 'summarize'."""
        self.history = summarize_history(self.history, keep_recent=keep_recent)
        return self

    def build_messages(self) -> tuple[str, list[dict]]:
        """Assemble (system, messages) for client.chat.completions.create().

        Retrieved docs are appended to the CURRENT message, not the system
        prompt — end position = maximum recall on Mistral-7B.
        """
        retrieved_block = ""
        if self.retrieved_docs:
            retrieved_block = (
                "\n\n<reference_docs>\n"
                + "\n---\n".join(self.retrieved_docs)
                + "\n</reference_docs>\n\n"
            )

        messages = list(self.history)
        messages.append({
            "role": "user",
            "content": retrieved_block + self.current_user_message,
        })
        return self.system_prompt, messages


if __name__ == "__main__":
    budget = ContextBudget(
        model="mistral",
        system_prompt="You are an order-tracking assistant. Always cite order IDs.",
        current_user_message="Where is my order ORD-88421?",
        retrieved_docs=["ORD-88421: in transit, estimated delivery Nov 8 via FedEx."],
    )
    print(f"Tokens: {budget.total()} / {budget.max_tokens} ({budget.strategy()})")
    system, messages = budget.build_messages()
    print(f"Messages: {len(messages)}, last content: {messages[-1]['content'][:80]}")
