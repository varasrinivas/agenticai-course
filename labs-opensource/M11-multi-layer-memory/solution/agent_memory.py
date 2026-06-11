"""
M11 Lab - Step 3: AgentMemory — SOLUTION
=========================================
Run: python agent_memory.py     (uses ./chroma_memory_lab for persistence)
"""

from __future__ import annotations

from buffer_memory import BufferMemory
from vector_memory import VectorMemory
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


class AgentMemory:
    """Orchestrates BufferMemory + VectorMemory behind a single interface."""

    def __init__(
        self,
        buffer_max_messages: int = 20,
        buffer_max_tokens: int = 4000,
        vector_persist_dir: str = "./chroma_memory_lab",
        vector_recall_k: int = 5,
    ) -> None:
        self.buffer = BufferMemory(max_messages=buffer_max_messages, max_tokens=buffer_max_tokens)
        self.vector = VectorMemory(persist_directory=vector_persist_dir)
        self.vector_recall_k = vector_recall_k

    def build_context(self, query: str) -> list[dict]:
        """Assemble the full message list for a query.

        Order: vector facts first (as a system message), buffer LAST —
        the most recent conversation always wins over older context.
        """
        messages = []

        vector_hits = self.vector.recall(query, k=self.vector_recall_k)
        if vector_hits:
            mem_lines = ["[RELEVANT PAST FACTS]"]
            for hit in vector_hits:
                if hit["score"] >= 0.5:  # filter low-confidence noise
                    mem_lines.append(f"- [{hit['score']:.2f}] {hit['text']}")
            if len(mem_lines) > 1:
                # SYSTEM message — a fake user/assistant turn confuses the model
                messages.append({"role": "system", "content": "\n".join(mem_lines)})

        messages.extend(self.buffer.get())
        return messages

    def save_turn(self, user_msg: str, assistant_msg: str) -> None:
        """Record a completed exchange in both layers."""
        self.buffer.add("user", user_msg)
        self.buffer.add("assistant", assistant_msg)

        # Heuristic: long messages probably contain facts worth keeping
        if len(user_msg) > 80 or len(assistant_msg) > 80:
            self.vector.save(
                f"User asked: {user_msg[:120]} -> Agent: {assistant_msg[:200]}"
            )


def chat(memory: AgentMemory, user_msg: str) -> str:
    """One agent turn using the assembled context."""
    messages = [{"role": "system", "content": "You are a helpful order-support assistant. Be concise."}]
    messages += memory.build_context(user_msg)
    messages.append({"role": "user", "content": user_msg})
    try:
        response = client.chat.completions.create(model="mistral", messages=messages)
        reply = response.choices[0].message.content or ""
    except Exception as e:
        return f"[error: {e}]"
    memory.save_turn(user_msg, reply)
    return reply


if __name__ == "__main__":
    print("=== SESSION 1 ===")
    mem1 = AgentMemory()
    print(chat(mem1, "Order TRK-001 shipped via FedEx on Monday. The customer prefers "
                     "email notifications over SMS. Please remember all of this.")[:200])

    print("\n=== SESSION 2 (fresh buffer, persistent vector store) ===")
    mem2 = AgentMemory()
    answer = chat(mem2, "How should I notify the customer about their TRK-001 delivery?")
    print(answer[:300])
    print("\nPass criteria: the answer mentions EMAIL (not SMS) and ideally FedEx —")
    print("facts recalled from the vector store, not from the (empty) buffer.")
