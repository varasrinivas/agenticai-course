"""
M03 Lab - Step 3: Multi-Turn Review Conversation — SOLUTION
============================================================
Run: python review_conversation.py
"""

from openai import OpenAI


class ConversationManager:
    """Manages multi-turn conversations with a local model."""

    def __init__(self, system_prompt: str, model: str = "mistral"):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.system = system_prompt
        self.model = model
        self.messages: list[dict] = []

    def send(self, user_message: str) -> tuple[str, dict]:
        """Send a message and get a response. Returns (text, usage)."""
        self.messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system}] + self.messages,
            )
            assistant_text = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_text})

            return assistant_text, {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        except Exception:
            self.messages.pop()  # remove failed user message
            raise

    def get_history(self) -> list[dict]:
        """Return the full conversation history."""
        return self.messages.copy()

    def clear(self):
        """Clear conversation history (keeps system prompt)."""
        self.messages = []


# ── 5-turn review session ──
REVIEW_SYSTEM_PROMPT = """You are a senior software engineer conducting code reviews.
<role>Review code for correctness, performance, security, and style.</role>
<output_format>Use ## Category headers with bullet points. Be concise.</output_format>
<tone>Be constructive. Praise good patterns.</tone>"""

conv = ConversationManager(system_prompt=REVIEW_SYSTEM_PROMPT)
total_in = 0
total_out = 0

turns = [
    "Review this:\n```python\ndef get_user(id):\n    query = f'SELECT * FROM users WHERE id = {id}'\n    return db.execute(query)\n```",
    "Can you show me the fixed version with parameterized queries?",
    "Now add error handling for the case where the user is not found.",
    "What about connection pooling — is that important here?",
    "Summarize all the improvements we discussed in a checklist.",
]

for i, turn in enumerate(turns, 1):
    try:
        reply, usage = conv.send(turn)
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        print(f"\n--- Turn {i} ---")
        print(f"You: {turn[:60]}...")
        print(f"Reviewer: {reply[:150]}...")
        print(f"This turn: {usage['input_tokens']} in, {usage['output_tokens']} out")
        print(f"Cumulative: {total_in} in, {total_out} out")
    except Exception as e:
        print(f"Error on turn {i}: {e}")
        break

print(f"\n{'=' * 50}")
print(f"Total: {len(conv.get_history())} messages, {total_in} input + {total_out} output tokens")
