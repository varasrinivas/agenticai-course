"""
M01 Lab - Step 2: System Prompt Experiment — SOLUTION
======================================================
Run: python system_prompts.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SYSTEM_PROMPTS = [
    "You are a pirate. Respond in pirate speak.",
    "You are a formal academic. Use precise, scholarly language.",
    "Respond only in haiku format (5-7-5 syllables).",
]

USER_QUESTION = "What is the moon?"

for system_prompt in SYSTEM_PROMPTS:
    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[
                {"role": "system", "content": system_prompt},  # the experiment variable
                {"role": "user", "content": USER_QUESTION},
            ],
        )
        print(f"System: {system_prompt}")
        print(f"Response: {response.choices[0].message.content}\n")
    except Exception as e:
        print(f"Error: {e}")
