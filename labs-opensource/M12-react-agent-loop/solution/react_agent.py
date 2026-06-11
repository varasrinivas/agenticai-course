"""
M12 Lab - Step 2: The ReAct Research Agent — SOLUTION
======================================================
Run: python react_agent.py
"""

import json

from openai import OpenAI
from mock_search import mock_search

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SYSTEM_PROMPT = """You are a research assistant that compiles accurate, well-sourced reports.

IMPORTANT: Before EVERY tool call, write:
  Thought: [your reasoning — what you know, what's missing, why THIS tool call]

After EVERY tool result, write:
  Thought: [what you learned and whether you need more information]

When you have enough information, produce a structured report with:
- Summary (2-3 sentences)
- Key Findings (bullet points)
- Sources Used (list the searches you ran)"""

TOOLS = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information about AI, technology, or "
            "research topics. Use specific queries for better results."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — be specific (e.g., 'claude agent sdk features 2025' not 'claude')",
                }
            },
            "required": ["query"],
        },
    },
}]


def execute_tool(name: str, inputs: dict) -> str:
    """Dispatch a tool call to its implementation."""
    if name == "web_search":
        return mock_search(inputs.get("query", ""))
    return json.dumps({"error": f"Unknown tool: {name}", "isError": True})


def run_agent(question: str, max_turns: int = 20, verbose: bool = True) -> str:
    """Run the ReAct loop until finish_reason == 'stop'."""
    messages = [{"role": "user", "content": question}]
    turn = 0

    if verbose:
        print(f"\n{'=' * 60}\nQUESTION: {question}\n{'=' * 60}")

    while turn < max_turns:
        turn += 1
        try:
            response = client.chat.completions.create(
                model="mistral",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                tools=TOOLS,
            )
        except Exception as e:
            return f"API error: {e}"

        msg = response.choices[0].message

        # REASON: the thought arrives alongside any tool calls
        if verbose:
            print(f"\n--- Turn {turn} ---")
            if msg.content:
                print(f"Thought: {msg.content[:300]}{'...' if len(msg.content) > 300 else ''}")
            for tc in (msg.tool_calls or []):
                print(f"[tool call] {tc.function.name}({tc.function.arguments[:100]})")

        # STOP: the model has produced its final answer
        if response.choices[0].finish_reason == "stop":
            return msg.content or "Agent completed without final text."

        # ACT: keep msg.content — the thought is part of the history
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": msg.tool_calls,
        })

        # OBSERVE: execute each tool call, append results as tool-role messages
        for tc in (msg.tool_calls or []):
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            if verbose:
                print(f"[observe]   {result[:150]}...")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return f"[Safety cap reached after {max_turns} turns — partial result]"


if __name__ == "__main__":
    question = (
        "What are the main Python frameworks for building AI agents in 2025, "
        "and how does the claude-agent-sdk compare to them?"
    )
    answer = run_agent(question, verbose=True)
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print("=" * 60)
    print(answer)
