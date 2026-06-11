"""
M00 Lab - Step 2: Your First Local Model Call
==============================================
Complete the TODO below to send a message to Mistral-7B running in Ollama.
Run: python hello_mistral.py
"""

from openai import OpenAI

# Connect to Ollama running on localhost.
# api_key="ollama" is a placeholder — Ollama doesn't need a real key.
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print("Connecting to local Mistral-7B via Ollama...")
print("-" * 50)

# TODO: Use client.chat.completions.create() to send a message to Mistral
# - model: "mistral"
# - messages: a system message ("You are a helpful assistant. Be concise.")
#             and a user message ("In exactly one sentence, what is a large language model?")
# Then print:
#   1. The response text       — response.choices[0].message.content
#   2. The token usage         — response.usage.prompt_tokens and response.usage.completion_tokens
# Wrap the call in try/except and print troubleshooting hints on failure
# (is Ollama running? is mistral pulled?).

pass  # Remove this line when you add your code
