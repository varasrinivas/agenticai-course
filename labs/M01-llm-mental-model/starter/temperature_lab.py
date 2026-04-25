"""
M01 Lab - Step 2: Temperature Experiment
==========================================
Send the same prompt at three different temperatures and compare.
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def call_with_temperature(prompt: str, temp: float) -> str:
    """Call Claude with a specific temperature and return the response text."""
    # TODO: Call client.messages.create() with:
    #   - model=MODEL
    #   - max_tokens=256
    #   - temperature=temp
    #   - messages: a single user message with the prompt
    # Return response.content[0].text
    pass


if __name__ == "__main__":
    prompt = "Write a one-sentence tagline for an AI coding assistant."
    temperatures = [0.0, 0.5, 1.0]

    print("--- Temperature Experiment ---\n")
    for temp in temperatures:
        print(f"Temperature {temp}:")
        try:
            result = call_with_temperature(prompt, temp)
            print(f'  "{result}"\n')
        except Exception as e:
            print(f"  [ERROR] {e}\n")
