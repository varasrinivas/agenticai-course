"""
UCC Filing Lookup Agent — Agent (SOLUTION)
=============================================
Complete implementation of the conversational agent loop.
"""

import json
import anthropic
from tools import TOOLS, search_ucc_filings


def run_agent():
    """Run the conversational agent loop."""

    client = anthropic.Anthropic()

    system_prompt = (
        "You are a UCC (Uniform Commercial Code) filing research assistant. "
        "When a user asks about UCC filings, liens, or security interests for a "
        "business, use the search_ucc_filings tool with the business name and "
        "state to look up filings. Then explain the results clearly, including: "
        "filing status, secured party (lender), collateral description, filing "
        "and lapse dates, and any amendments or continuations. "
        "Explain what the filing means in practical terms — e.g., whether there "
        "are active liens, what assets are encumbered, and whether any filings "
        "have lapsed or been terminated. "
        "If the user asks a general question about UCC filings, explain the "
        "concept without calling tools. Always be professional and precise."
    )

    messages = []

    print("=" * 60)
    print("  UCC Filing Lookup Agent")
    print("  Search for UCC filings by business name and state.")
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

                    if tool_name == "search_ucc_filings":
                        tool_result = search_ucc_filings(
                            business_name=tool_input["business_name"],
                            state=tool_input["state"],
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
