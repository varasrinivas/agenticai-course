"""
M01 Lab - Step 3: Model Comparison
====================================
Compare Claude Haiku and Sonnet on the same prompt.
"""
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def call_model(model_name: str, prompt: str) -> tuple[str, float]:
    """Call a specific Claude model and return (response_text, elapsed_seconds)."""
    # TODO:
    # 1. Record start time with time.time()
    # 2. Call client.messages.create() with:
    #    - model=model_name
    #    - max_tokens=1024
    #    - messages: a single user message with the prompt
    # 3. Record end time
    # 4. Return (response_text, elapsed_time)
    pass


if __name__ == "__main__":
    prompt = "Explain what a UCC filing is in 2-3 sentences."
    models = [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
    ]

    print("--- Model Comparison ---\n")
    for model in models:
        print(f"Model: {model}")
        try:
            text, elapsed = call_model(model, prompt)
            print(f"Time: {elapsed:.2f}s")
            print(f"Response:\n  {text}\n")
        except Exception as e:
            print(f"  [ERROR] {e}\n")
