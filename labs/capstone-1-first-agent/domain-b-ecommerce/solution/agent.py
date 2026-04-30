"""
B2B Ecommerce Order Status Bot — Agent (SOLUTION)
====================================================
Complete implementation of the conversational agent loop.
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

        try:
            # Step 1: Send the message to Claude
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            # Step 2: Handle tool use
            if response.stop_reason == "tool_use":
                tool_use_block = None
                for block in response.content:
                    if block.type == "tool_use":
                        tool_use_block = block
                        break

                if tool_use_block:
                    tool_name = tool_use_block.name
                    tool_input = tool_use_block.input

                    if tool_name == "get_order_status":
                        tool_result = get_order_status(
                            po_number=tool_input["po_number"]
                        )
                    else:
                        tool_result = {"error": f"Unknown tool: {tool_name}"}

                    messages.append(
                        {"role": "assistant", "content": response.content}
                    )

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_block.id,
                                    "content": json.dumps(tool_result),
                                }
                            ],
                        }
                    )

                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        system=system_prompt,
                        tools=TOOLS,
                        messages=messages,
                    )

            # Step 3: Extract and print the response
            assistant_text = response.content[0].text
            print(f"\nAgent: {assistant_text}\n")
            messages.append({"role": "assistant", "content": response.content})

        except anthropic.AuthenticationError:
            print(
                "\nError: Invalid API key. Please set the ANTHROPIC_API_KEY "
                "environment variable.\n"
            )
            messages.pop()
        except anthropic.RateLimitError:
            print(
                "\nError: Rate limit exceeded. Please wait a moment and try again.\n"
            )
            messages.pop()
        except anthropic.APIError as e:
            print(f"\nError: API error — {e}\n")
            messages.pop()
        except Exception as e:
            print(f"\nError: {e}\n")
            messages.pop()


if __name__ == "__main__":
    run_agent()
