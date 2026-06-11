"""
M01 Lab - Step 1: Your First Chat Completion — SOLUTION
========================================================
Run: python first_call.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print("--- First Local Model Call ---\n")

try:
    response = client.chat.completions.create(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who explains things clearly."},
            {"role": "user", "content": "What is a large language model? Explain in 2 sentences."},
        ],
    )
    print(response.choices[0].message.content)
    print(
        f"\nTokens used: {response.usage.prompt_tokens} in, "
        f"{response.usage.completion_tokens} out"
    )
except Exception as e:
    print(f"API error: {e}")
    print("Is Ollama running? Try: ollama serve")
