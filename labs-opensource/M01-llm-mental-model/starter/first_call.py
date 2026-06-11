"""
M01 Lab - Step 1: Your First Chat Completion
=============================================
Run: python first_call.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print("--- First Local Model Call ---\n")

# TODO: Use client.chat.completions.create() to ask Mistral a question.
# - model: "mistral"
# - messages:
#     system: "You are a helpful assistant who explains things clearly."
#     user:   "What is a large language model? Explain in 2 sentences."
# Print the response text (response.choices[0].message.content) and the
# usage line: f"Tokens used: {usage.prompt_tokens} in, {usage.completion_tokens} out"
# Wrap in try/except — on failure, remind the user to run `ollama serve`.

pass  # Remove this line when you add your code
