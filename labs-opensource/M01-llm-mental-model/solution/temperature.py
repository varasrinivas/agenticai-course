"""
M01 Lab - Step 3: Temperature Experiment — SOLUTION
====================================================
Run: python temperature.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

PROMPT = "Write a one-sentence description of the moon."

for temp in [0.0, 1.0]:
    print(f"\n--- Temperature {temp} ---")
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model="mistral",
                temperature=temp,
                messages=[{"role": "user", "content": PROMPT}],
            )
            print(f"  Run {i + 1}: {response.choices[0].message.content}")
        except Exception as e:
            print(f"  Error: {e}")
