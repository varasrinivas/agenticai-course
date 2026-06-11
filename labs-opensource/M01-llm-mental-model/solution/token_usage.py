"""
M01 Lab - Step 4: Observe Token Usage — SOLUTION
=================================================
Run: python token_usage.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

TESTS = [
    ("Short prompt", "Hi!", 50),
    ("Medium prompt", "Explain what a large language model is in detail.", 200),
    ("Long prompt with constraint", "Write a 3-paragraph essay about the history of computing.", 1024),
]

for label, prompt, max_tok in TESTS:
    try:
        response = client.chat.completions.create(
            model="mistral",
            max_tokens=max_tok,
            messages=[{"role": "user", "content": prompt}],
        )
        u = response.usage
        print(f"{label}:")
        print(f"  Input tokens:  {u.prompt_tokens}")
        print(f"  Output tokens: {u.completion_tokens}")
        print(f"  Total tokens:  {u.prompt_tokens + u.completion_tokens}\n")
    except Exception as e:
        print(f"Error: {e}")
