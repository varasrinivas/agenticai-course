"""
M01 Lab - Step 3: Temperature Experiment
=========================================
Same prompt at temperature 0.0 and 1.0, three runs each.
Run: python temperature.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

PROMPT = "Write a one-sentence description of the moon."

# TODO: For temp in [0.0, 1.0]:
#   Print a header like "--- Temperature 0.0 ---"
#   For run i in 1..3:
#     - Call client.chat.completions.create(model="mistral", temperature=temp,
#                                           messages=[{"role": "user", "content": PROMPT}])
#     - Print f"  Run {i}: {response text}"
#     - try/except around each call
#
# What to observe: temp 0.0 → (nearly) identical runs; temp 1.0 → three different ones.

pass  # Remove this line when you add your code
