"""
Healthcare Pre-Auth Status Checker — Agent (SOLUTION)
=======================================================
Complete implementation of the conversational agent loop.
"""

import json
import anthropic
from tools import TOOLS, get_preauth_status


def run_agent():
    """Run the conversational agent loop."""

    # Initialize the Anthropic client (reads ANTHROPIC_API_KEY from environment)
    client = anthropic.Anthropic()

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

        try:
            # ── Step 1: Send the message to Claude ──────────────
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            # ── Step 2: Handle tool use ─────────────────────────
            if response.stop_reason == "tool_use":
                # Find the tool_use block in the response
                tool_use_block = None
                for block in response.content:
                    if block.type == "tool_use":
                        tool_use_block = block
                        break

                if tool_use_block:
                    # Execute the tool
                    tool_name = tool_use_block.name
                    tool_input = tool_use_block.input

                    if tool_name == "get_preauth_status":
                        tool_result = get_preauth_status(
                            reference_id=tool_input["reference_id"]
                        )
                    else:
                        tool_result = {"error": f"Unknown tool: {tool_name}"}

                    # Add the assistant's response (with tool_use) to messages
                    messages.append(
                        {"role": "assistant", "content": response.content}
                    )

                    # Add the tool result to messages
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

                    # Get Claude's final response with the tool result
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system=system_prompt,
                        tools=TOOLS,
                        messages=messages,
                    )

            # ── Step 3: Extract and print the response ──────────
            assistant_text = response.content[0].text
            print(f"\nAgent: {assistant_text}\n")

            # Add the final assistant response to conversation history
            messages.append({"role": "assistant", "content": response.content})

        except anthropic.AuthenticationError:
            print(
                "\nError: Invalid API key. Please set the ANTHROPIC_API_KEY "
                "environment variable.\n"
            )
            # Remove the failed message from history
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
