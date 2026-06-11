"""
M02 Lab - Step 1: Token Counting with tiktoken
===============================================
Run: python token_counting.py
Requires: pip install tiktoken
"""

import tiktoken

# Load the cl100k_base encoding (GPT-4 tokenizer — close to Mistral's for English)
enc = tiktoken.get_encoding("cl100k_base")

# ── Part A: Basic token counting (COMPLETE — just read and run) ──
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


# ── Part B: Chat message overhead (YOUR JOB) ──
def count_chat_tokens(messages: list[dict]) -> int:
    """Count tokens for a list of chat messages including overhead.

    TODO: Implement this.
    - Start with 3 tokens (the assistant reply primer)
    - For each message add:
        4 tokens                       (role/content field markers + separator)
        + tokens in msg["role"]        (len(enc.encode(...)))
        + tokens in msg["content"]
    - Return the total
    """
    pass  # Remove this line when you add your code


messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Explain what a token is in 2 sentences."},
]
print(f"Chat token estimate: {count_chat_tokens(messages)}")
# Expected: ~31
