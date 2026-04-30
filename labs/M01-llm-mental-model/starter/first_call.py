"""
M01 Lab - Step 1: Make Your First Claude API Call
==================================================
Complete the TODO below to send a message to Claude and print the response.
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

    # TODO: Use client.messages.create() to send a message to Claude
    # - model: "claude-sonnet-4-6"
    # - max_tokens: 1024
    # - messages: a single user message asking "What is an AI agent? Explain in 2-3 sentences."
    # Then print the response text.
    #
    # Hint: The response text lives at response.content[0].text

    pass  # Remove this line when you add your code


if __name__ == "__main__":
    main()
