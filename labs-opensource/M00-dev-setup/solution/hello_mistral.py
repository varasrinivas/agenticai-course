"""
M00 Lab - Step 2: Your First Local Model Call — SOLUTION
=========================================================
Complete working implementation.
Run: python hello_mistral.py
"""

from openai import OpenAI

# Connect to Ollama running on localhost.
# api_key="ollama" is a placeholder — Ollama doesn't need a real key.
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print("Connecting to local Mistral-7B via Ollama...")
print("-" * 50)

try:
    response = client.chat.completions.create(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": "In exactly one sentence, what is a large language model?"},
        ],
    )
    text = response.choices[0].message.content
    print(f"Mistral says: {text}")
    print("-" * 50)
    print(
        f"Tokens used — input: {response.usage.prompt_tokens}, "
        f"output: {response.usage.completion_tokens}"
    )
    print("\nSetup complete! Your environment is ready for the rest of the course.")

except Exception as e:
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Is Ollama running?    Run: ollama serve")
    print("  2. Is mistral pulled?    Run: ollama pull mistral")
    print("  3. Is openai installed?  Run: pip install openai")
    print("  4. Is venv active?       Check for (venv) in your prompt")
