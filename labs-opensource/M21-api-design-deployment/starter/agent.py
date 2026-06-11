"""
M21 Lab: The Agent Being Wrapped (COMPLETE)
============================================
A minimal M05-style agent. The lab is about the API around it,
not the agent itself.
"""

import json
import time

from openai import OpenAI

TOOLS = [
    {"type": "function", "function": {
        "name": "calculate",
        "description": "Evaluate a math expression. Use for any computation.",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string"}}, "required": ["expression"]},
    }},
]


def _run_tool(name: str, args: dict) -> str:
    if name == "calculate":
        expr = args.get("expression", "")
        if not all(c in "0123456789+-*/.()% " for c in expr):
            return json.dumps({"error": "invalid characters"})
        try:
            return json.dumps({"result": eval(expr)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return json.dumps({"error": f"unknown tool {name}"})


async def run_agent(query: str, session_id: str | None, max_iterations: int,
                    ollama_host: str = "http://localhost:11434") -> dict:
    """Run the loop; return the fields AgentResponse needs (minus latency)."""
    client = OpenAI(base_url=f"{ollama_host}/v1", api_key="ollama")
    messages = [{"role": "user", "content": query}]
    tool_records = []

    for iteration in range(1, max_iterations + 1):
        response = client.chat.completions.create(
            model="mistral", tools=TOOLS, messages=messages
        )
        choice = response.choices[0]
        tool_calls = choice.message.tool_calls or []

        if choice.finish_reason == "stop" or not tool_calls:
            return {
                "result": choice.message.content or "",
                **({"session_id": session_id} if session_id else {}),
                "iterations": iteration,
                "tool_calls": tool_records,
                "model": "mistral",
            }

        messages.append({"role": "assistant", "content": choice.message.content,
                         "tool_calls": tool_calls})
        for tc in tool_calls:
            args = json.loads(tc.function.arguments)
            t0 = time.perf_counter()
            result = _run_tool(tc.function.name, args)
            tool_records.append({
                "tool_name": tc.function.name,
                "input_summary": json.dumps(args)[:120],
                "output_summary": result[:120],
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return {
        "result": "Max iterations reached.",
        **({"session_id": session_id} if session_id else {}),
        "iterations": max_iterations,
        "tool_calls": tool_records,
        "model": "mistral",
    }
