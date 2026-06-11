"""
M03B Lab: The ContextBudget Class
==================================
Accounts for and curates the six layers of a local-model context.
You implement: account(), strategy(), crop(), build_messages().
Provided complete: count_tokens, MODEL_LIMITS, summarize_history, checkpoint().
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import tiktoken
from openai import OpenAI

# cl100k_base is OpenAI's tokenizer — a good approximation for Mistral/Llama
_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text) -> int:
    """Count tokens in a string or JSON-serializable object. (COMPLETE)"""
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
    """Summarize older turns; keep the last `keep_recent` turns verbatim. (COMPLETE)

    GOTCHA: this is a SEPARATE model call — never ask the main model to
    summarize the context it is currently reading.
    """
    if len(history) <= keep_recent:
        return history  # nothing to do

    older = history[:-keep_recent]
    recent = history[-keep_recent:]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in older)

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    try:
        result = client.chat.completions.create(
            model="mistral",  # use a fast/cheap local model for summarization
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(transcript=transcript)}],
            max_tokens=250,
        )
        summary_text = result.choices[0].message.content or ""
    except Exception as e:
        print(f"Summarization failed: {e}; falling back to truncation.")
        return recent  # safe fallback: just keep recent turns

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
    retrieved_docs: list[str] = field(default_factory=list)   # semi-static
    history: list[dict] = field(default_factory=list)          # [{"role","content"}]
    tool_results: list[str] = field(default_factory=list)
    current_user_message: str = ""
    model: str = "mistral"
    reserve_output: int = 2048   # tokens reserved for the model's response

    @property
    def max_tokens(self) -> int:
        return MODEL_LIMITS.get(self.model, 32_768) - self.reserve_output

    def account(self) -> dict[str, int]:
        """Per-layer token breakdown.

        TODO: return a dict with these keys (use count_tokens):
          "system"       — tokens in self.system_prompt
          "tools"        — count_tokens(self.tool_definitions) if any, else 0
          "retrieved"    — sum over self.retrieved_docs
          "history"      — sum of count_tokens(m["content"]) over self.history
          "tool_results" — sum over self.tool_results
          "current"      — tokens in self.current_user_message
        """
        pass  # Remove this line when you add your code

    def total(self) -> int:
        """(COMPLETE once account() works)"""
        return sum(self.account().values())

    def remaining(self) -> int:
        return self.max_tokens - self.total()

    def fits(self) -> bool:
        return self.total() <= self.max_tokens

    def strategy(self) -> str:
        """Return recommended strategy based on budget utilization.

        TODO: utilization = self.total() / self.max_tokens
          < 0.60 → "ok"          (plenty of room)
          < 0.75 → "compress"    (crop tool defs, compress tool results)
          < 0.90 → "summarize"   (summarize old history turns)
          else   → "critical"    (keep only system + last 2 turns + current)
        """
        pass  # Remove this line when you add your code

    def crop(self) -> "ContextBudget":
        """Apply the recommended strategy in place. Returns self for chaining.

        TODO:
        - strat = self.strategy(); if "ok", return self unchanged
        - For "compress", "summarize", "critical": self.tool_definitions = []
          (saves ~900 tokens for 4 tools)
        - For "summarize", "critical": keep only the last 4 history turns
          (2 if critical) and the last 2 tool_results
        - For "critical" only: also drop all retrieved_docs
        - Return self
        """
        pass  # Remove this line when you add your code

    def checkpoint(self, keep_recent: int = 4) -> "ContextBudget":
        """Summarize old history turns. Call when strategy() == 'summarize'. (COMPLETE)"""
        self.history = summarize_history(self.history, keep_recent=keep_recent)
        return self

    def build_messages(self) -> tuple[str, list[dict]]:
        """Assemble (system, messages) for client.chat.completions.create().

        Order: system (start, high recall) → history → retrieved docs +
        current message (end, high recall). Never bury key facts in the middle.

        TODO:
        - If self.retrieved_docs is non-empty, build:
            "\\n\\n<reference_docs>\\n" + "\\n---\\n".join(docs) + "\\n</reference_docs>\\n\\n"
          (appended to the CURRENT user message — end position = max recall on Mistral-7B)
        - messages = list(self.history) + [{"role": "user",
            "content": retrieved_block + self.current_user_message}]
        - Return (self.system_prompt, messages)
        """
        pass  # Remove this line when you add your code


if __name__ == "__main__":
    # Quick self-test (no API call needed for account/strategy/build_messages)
    budget = ContextBudget(
        model="mistral",
        system_prompt="You are an order-tracking assistant. Always cite order IDs.",
        current_user_message="Where is my order ORD-88421?",
        retrieved_docs=["ORD-88421: in transit, estimated delivery Nov 8 via FedEx."],
    )
    print(f"Tokens: {budget.total()} / {budget.max_tokens} ({budget.strategy()})")
    system, messages = budget.build_messages()
    print(f"Messages: {len(messages)}, last content: {messages[-1]['content'][:80]}")
