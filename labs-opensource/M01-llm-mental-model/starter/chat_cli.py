"""
M01 Lab - Step 5 (Stretch): CLI Chat with History
==================================================
A terminal chat loop that resends the FULL conversation every turn.
Run: python chat_cli.py   (type 'quit' to exit)
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

conversation = []

print("Chat with Mistral! (type 'quit' to exit)\n")

# TODO: Build the chat loop:
# while True:
#   1. user_input = input("You: ").strip()
#   2. Exit on "quit"/"exit"; skip empty input
#   3. conversation.append({"role": "user", "content": user_input})
#   4. Call the model with [system message] + conversation
#      (system: "You are a friendly, helpful assistant.")
#   5. Append the assistant reply to conversation and print it
#   6. On API error: print the error AND conversation.pop() — remove the
#      failed user message so the history stays consistent

pass  # Remove this line when you add your code
