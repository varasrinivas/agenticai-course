"""
M01 Lab - Step 5 (Stretch): CLI Chat with History — SOLUTION
=============================================================
Run: python chat_cli.py   (type 'quit' to exit)
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

conversation = []

print("Chat with Mistral! (type 'quit' to exit)\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("quit", "exit"):
        break
    if not user_input:
        continue

    conversation.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[
                {"role": "system", "content": "You are a friendly, helpful assistant."}
            ] + conversation,
        )
        assistant_msg = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_msg})
        print(f"\nMistral: {assistant_msg}\n")
    except Exception as e:
        print(f"\nError: {e}\n")
        # Remove the failed user message so conversation stays consistent
        conversation.pop()
