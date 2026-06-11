"""
M05 Lab - Step 2: The Agent Loop
=================================
The tools are provided (tools.py). You build the loop that lets the model
use them: call → check finish_reason → execute tools → report back → repeat.
Run: python tool_agent.py
"""

import json

from openai import OpenAI
from tools import TOOLS, run_tool

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def agent_chat(user_message: str) -> str:
    """Run the full agent loop: send message, handle tool calls, return final answer.

    TODO:
    messages = [{"role": "user", "content": user_message}]
    Loop forever:
      1. response = client.chat.completions.create(model="mistral",
             tools=TOOLS, messages=messages)
         — wrap in try/except, return f"API error: {e}" on failure
      2. finish_reason = response.choices[0].finish_reason
      3. If finish_reason == "stop":
           return response.choices[0].message.content or "(no text response)"
      4. If finish_reason == "tool_calls":
           a. FIRST append the assistant message to history:
              messages.append({"role": "assistant", "content": None,
                               "tool_calls": response.choices[0].message.tool_calls})
           b. For each tool_call in response.choices[0].message.tool_calls:
              - name = tool_call.function.name
              - args = json.loads(tool_call.function.arguments)   # JSON STRING!
              - print(f"  [tool call] {name}({json.dumps(args)})")
              - result = run_tool(name, args)
              - print(f"  [result]    {result[:80]}")
              - messages.append({"role": "tool",
                                 "tool_call_id": tool_call.id,
                                 "content": result})
           c. Loop back to 1 — the model reads the results and continues
      5. Anything else: return f"(unexpected finish_reason: {finish_reason})"

    GOTCHA: the assistant message (4a) MUST come before the tool results (4b),
    with matching tool_call_ids — otherwise the API rejects the history.
    """
    pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──
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
