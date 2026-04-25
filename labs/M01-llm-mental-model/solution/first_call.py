"""
M01 Lab - Step 1: Make Your First Claude API Call — SOLUTION
=============================================================
Complete working implementation.
"""

import os
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file (if present)
load_dotenv()

# Create the Anthropic client (reads ANTHROPIC_API_KEY automatically)
client = anthropic.Anthropic()


def main():
    print("--- First Claude API Call ---\n")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "What is an AI agent? Explain in 2-3 sentences.",
                }
            ],
        )

        print("Response from Claude:")
        print(response.content[0].text)

    except anthropic.AuthenticationError:
        print("[ERROR] Invalid API key. Check your ANTHROPIC_API_KEY environment variable.")
    except anthropic.APIError as e:
        print(f"[ERROR] API call failed: {e}")


if __name__ == "__main__":
    main()
