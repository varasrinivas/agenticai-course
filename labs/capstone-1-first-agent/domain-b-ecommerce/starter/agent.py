"""
B2B Ecommerce Order Status Bot — Agent
=========================================
This is the main agent loop for the order status bot.

YOUR TASK: Fill in the three TODOs to complete the agent loop.
"""

import json
import anthropic
from tools import TOOLS, get_order_status


def run_agent():
    """Run the conversational agent loop."""

    client = anthropic.Anthropic()

    system_prompt = (
        "You are a B2B ecommerce order status assistant. "
        "When a user provides a purchase order number (formatted like PO-YYYY-NNNN), "
        "use the get_order_status tool to look up the order. Then explain the result "
        "clearly, including the current status, any tracking information, expected "
        "delivery dates, and relevant notes. If there are issues (backorder, hold, "
        "cancellation), explain what happened and suggest next steps. "
        "If the user asks a general question, respond helpfully without calling tools. "
        "Always be professional and solution-oriented."
    )

    messages = []

    print("=" * 60)
    print("  B2B Order Status Bot")
    print("  Enter a PO number to check order status.")
    print("  Type 'quit' to exit.")
    print("=" * 60)
    print()

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # ──────────────────────────────────────────────────────
        # TODO 1: Send the message to Claude
        # ──────────────────────────────────────────────────────
        # Call client.messages.create() with:
        #   - model="claude-sonnet-4-6"
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
        #   2. Extract the tool name and input arguments
        #   3. Call get_order_status(po_number=...) with the extracted args
        #   4. Add the assistant's response to messages
        #   5. Add the tool result to messages
        #   6. Call client.messages.create() again to get the final response
        #   7. Store the second response in `response`
        # ──────────────────────────────────────────────────────

        # ──────────────────────────────────────────────────────
        # TODO 3: Extract and print the response text
        # ──────────────────────────────────────────────────────
        # assistant_text = response.content[0].text
        # print(f"\nAgent: {assistant_text}\n")
        # messages.append({"role": "assistant", "content": response.content})
        # ──────────────────────────────────────────────────────


if __name__ == "__main__":
    run_agent()
