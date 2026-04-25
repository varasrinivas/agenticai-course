"""
M01 Lab - Step 2: Temperature Experiment — SOLUTION
=====================================================
Complete working implementation.
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def call_with_temperature(prompt: str, temp: float) -> str:
    """Call Claude with a specific temperature and return the response text."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        temperature=temp,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.content[0].text


if __name__ == "__main__":
    prompt = "Write a one-sentence tagline for an AI coding assistant."
    temperatures = [0.0, 0.5, 1.0]

    print("--- Temperature Experiment ---\n")
    for temp in temperatures:
        print(f"Temperature {temp}:")
        try:
            result = call_with_temperature(prompt, temp)
            print(f'  "{result}"\n')
        except anthropic.APIError as e:
            print(f"  [ERROR] {e}\n")
