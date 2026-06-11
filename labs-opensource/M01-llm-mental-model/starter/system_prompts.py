"""
M01 Lab - Step 2: System Prompt Experiment
===========================================
Same user question, three different system prompts. Watch the persona change.
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

# TODO: For each system_prompt in SYSTEM_PROMPTS:
# - Call client.chat.completions.create(model="mistral", messages=[...])
#   IMPORTANT: the messages list must contain BOTH
#     {"role": "system", "content": system_prompt}   ← this is the experiment!
#     {"role": "user",   "content": USER_QUESTION}
# - Print the system prompt and the response, separated by a blank line
# - try/except around each call so one failure doesn't kill the loop

pass  # Remove this line when you add your code
