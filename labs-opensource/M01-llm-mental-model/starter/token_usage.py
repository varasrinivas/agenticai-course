"""
M01 Lab - Step 4: Observe Token Usage
======================================
Three prompts of increasing size — watch prompt_tokens and completion_tokens grow.
Run: python token_usage.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

TESTS = [
    ("Short prompt", "Hi!", 50),
    ("Medium prompt", "Explain what a large language model is in detail.", 200),
    ("Long prompt with constraint", "Write a 3-paragraph essay about the history of computing.", 1024),
]

# TODO: For (label, prompt, max_tok) in TESTS:
# - Call client.chat.completions.create(model="mistral", max_tokens=max_tok,
#                                       messages=[{"role": "user", "content": prompt}])
# - u = response.usage  → print, per test:
#     Input tokens:  u.prompt_tokens
#     Output tokens: u.completion_tokens
#     Total tokens:  u.prompt_tokens + u.completion_tokens
# - try/except around each call
#
# NOTE: the OpenAI-compatible usage fields are prompt_tokens / completion_tokens
# (NOT input_tokens / output_tokens — that's the Anthropic SDK naming).

pass  # Remove this line when you add your code
