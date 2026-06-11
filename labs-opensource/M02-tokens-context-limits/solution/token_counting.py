"""
M02 Lab - Step 1: Token Counting with tiktoken — SOLUTION
==========================================================
Run: python token_counting.py
"""

import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

# ── Part A: Basic token counting ──
samples = [
    "Hello, world!",
    "tokenization",
    "don't use pseudocode",
    "ChatGPT is one token",
    "from openai import OpenAI",
]

print("── Token breakdown ──")
for text in samples:
    ids = enc.encode(text)
    tokens = [enc.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids]
    print(f"{len(ids):3d} tokens | {tokens!r}")
    print(f"           text: {text!r}\n")


# ── Part B: Chat message overhead ──
def count_chat_tokens(messages: list[dict]) -> int:
    """Count tokens for a list of chat messages including overhead."""
    total = 3  # primer for assistant reply
    for msg in messages:
        total += 4  # role, content field markers, sep
        total += len(enc.encode(msg.get("role", "")))
        total += len(enc.encode(msg.get("content", "")))
    return total


messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Explain what a token is in 2 sentences."},
]
print(f"Chat token estimate: {count_chat_tokens(messages)}")
# Output: Chat token estimate: ~31
