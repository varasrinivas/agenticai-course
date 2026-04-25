"""
Healthcare Pre-Auth Status Checker — Agent
=============================================
This is the main agent loop. It takes user input, sends it to Claude
with the tool definition, handles tool calls, and prints Claude's response.

YOUR TASK: Fill in the three TODOs to complete the agent loop.
"""

import json
import anthropic
from tools import TOOLS, get_preauth_status


def run_agent():
    """Run the conversational agent loop."""

    # Initialize the Anthropic client (reads ANTHROPIC_API_KEY from environment)
    client = anthropic.Anthropic()

    # System prompt tells Claude what role it plays
    system_prompt = (
        "You are a healthcare pre-authorization status assistant. "
        "When a user provides a prior authorization reference number "
        "(formatted like PA-YYYY-NNNNN), use the get_preauth_status tool "
        "to look up the status. Then explain the result in clear, "
        "non-technical language and suggest next steps based on the status. "
        "If the user asks a general question, respond helpfully without "
        "calling any tools. Always be professional and empathetic."
    )

    # Conversation history — maintains context across turns
    messages = []

    print("=" * 60)
    print("  Healthcare Pre-Auth Status Checker")
    print("  Type a PA reference number to check status.")
    print("  Type 'quit' to exit.")
    print("=" * 60)
    print()

    while True:
        # Get user input
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # Add the user's message to conversation history
        messages.append({"role": "user", "content": user_input})

        # ──────────────────────────────────────────────────────
        # TODO 1: Send the message to Claude
        # ──────────────────────────────────────────────────────
        # Call client.messages.create() with:
        #   - model="claude-sonnet-4-20250514"
        #   - max_tokens=1024
        #   - system=system_prompt
        #   - tools=TOOLS
        #   - messages=messages
        # Store the response in a variable called `response`
        #
        # response = ...
        # ──────────────────────────────────────────────────────

        # ──────────────────────────────────────────────────────
        # TODO 2: Handle tool use
        # ──────────────────────────────────────────────────────
        # Check if response.stop_reason == "tool_use"
        # If it is:
        #   1. Find the tool_use block in response.content
        #      (loop through response.content, look for block.type == "tool_use")
        #   2. Extract the tool name and input arguments
        #   3. Call get_preauth_status(reference_id=...) with the extracted args
        #   4. Add the assistant's response to messages:
        #      messages.append({"role": "assistant", "content": response.content})
        #   5. Add the tool result to messages:
        #      messages.append({
        #          "role": "user",
        #          "content": [{
        #              "type": "tool_result",
        #              "tool_use_id": <the tool_use block's id>,
        #              "content": json.dumps(tool_result)
        #          }]
        #      })
        #   6. Call client.messages.create() again with the updated messages
        #      to get Claude's final natural language response
        #   7. Store this second response in `response`
        #
        # If stop_reason is NOT "tool_use", do nothing — response already
        # contains Claude's text reply.
        # ──────────────────────────────────────────────────────

        # ──────────────────────────────────────────────────────
        # TODO 3: Extract and print the response text
        # ──────────────────────────────────────────────────────
        # Get the text from response.content[0].text
        # Print it with the prefix "Agent: "
        # Add the assistant's final message to the conversation history:
        #   messages.append({"role": "assistant", "content": response.content})
        #
        # assistant_text = ...
        # print(f"\nAgent: {assistant_text}\n")
        # messages.append({"role": "assistant", "content": response.content})
        # ──────────────────────────────────────────────────────


if __name__ == "__main__":
    run_agent()
