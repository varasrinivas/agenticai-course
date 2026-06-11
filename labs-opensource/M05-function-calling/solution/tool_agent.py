"""
M05 Lab - Step 2: The Agent Loop — SOLUTION
============================================
Run: python tool_agent.py
"""

import json

from openai import OpenAI
from tools import TOOLS, run_tool

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def agent_chat(user_message: str) -> str:
    """Run the full agent loop: send message, handle tool calls, return final answer."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        try:
            response = client.chat.completions.create(
                model="mistral",
                tools=TOOLS,
                messages=messages,
            )
        except Exception as e:
            return f"API error: {e} (is Ollama running? ollama serve)"

        finish_reason = response.choices[0].finish_reason

        # The model is done — return the text
        if finish_reason == "stop":
            return response.choices[0].message.content or "(no text response)"

        # The model wants to use tools — execute them and report back
        if finish_reason == "tool_calls":
            # The assistant message MUST be appended before the tool results,
            # with matching tool_call_ids, or the API rejects the history
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": response.choices[0].message.tool_calls,
            })

            for tool_call in response.choices[0].message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)  # JSON string!
                print(f"  [tool call] {name}({json.dumps(args)})")
                result = run_tool(name, args)
                print(f"  [result]    {result[:80]}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            # loop back — the model reads the results and continues
        else:
            return f"(unexpected finish_reason: {finish_reason})"


if __name__ == "__main__":
    test_questions = [
        "What's the weather like in Tokyo?",
        "What is (15 * 7) + 23?",
        "What time is it in London?",
        "What's the capital of France?",  # No tool needed!
    ]

    for q in test_questions:
        print(f"\n{'=' * 50}")
        print(f"User: {q}")
        answer = agent_chat(q)
        print(f"Agent: {answer[:150]}")
