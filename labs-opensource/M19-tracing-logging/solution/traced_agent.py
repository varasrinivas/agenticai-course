"""
M19 Lab - Step 2: Instrument the M05 Agent — SOLUTION
======================================================
Run: python traced_agent.py     (writes traces/trace_<runid>.jsonl)
"""

import json
import os
import time
import uuid

from openai import OpenAI
from tracer import TraceRecorder

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

TOOLS = [
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string"}}, "required": ["city"]},
    }},
    {"type": "function", "function": {
        "name": "calculate",
        "description": "Evaluate a math expression. Use for any computation.",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string"}}, "required": ["expression"]},
    }},
]

MOCK_WEATHER = {"tokyo": {"temp": 22, "condition": "sunny"},
                "london": {"temp": 14, "condition": "cloudy"}}


def run_tool(name: str, args: dict) -> str:
    if name == "get_weather":
        data = MOCK_WEATHER.get(args.get("city", "").lower())
        return json.dumps(data or {"error": "city not found"})
    if name == "calculate":
        expr = args.get("expression", "")
        if not all(c in "0123456789+-*/.()% " for c in expr):
            return json.dumps({"error": "invalid characters"})
        try:
            return json.dumps({"result": eval(expr)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return json.dumps({"error": f"unknown tool {name}"})


def _safe(fn, *args, **kwargs):
    """Tracing must never break the agent — swallow emit failures."""
    try:
        fn(*args, **kwargs)
    except Exception:
        pass


def agent_chat(user_message: str, recorder: TraceRecorder) -> str:
    """The M05 loop with all four instrumentation points."""
    messages = [{"role": "user", "content": user_message}]
    turn = 0

    while turn < 10:
        turn += 1
        iter_start = time.perf_counter()

        try:
            llm_start = time.perf_counter()
            response = client.chat.completions.create(
                model="mistral", tools=TOOLS, messages=messages
            )
            llm_ms = (time.perf_counter() - llm_start) * 1000

            # Emit point 1: the LLM turn
            _safe(recorder.llm_turn, "mistral",
                  response.usage.prompt_tokens,
                  response.usage.completion_tokens,
                  response.choices[0].finish_reason, llm_ms, turn)

        except Exception as e:
            # Emit point 4: the error
            _safe(recorder.error, e)
            return f"API error: {e}"

        choice = response.choices[0]
        tool_calls = choice.message.tool_calls or []
        invoked = []

        if choice.finish_reason == "stop" or not tool_calls:
            # Emit point 3: final iteration
            _safe(recorder.loop_iter, turn, invoked, "goal_achieved",
                  (time.perf_counter() - iter_start) * 1000)
            return choice.message.content or ""

        messages.append({"role": "assistant", "content": choice.message.content,
                         "tool_calls": tool_calls})

        for tc in tool_calls:
            args = json.loads(tc.function.arguments)
            tool_start = time.perf_counter()
            result = run_tool(tc.function.name, args)
            tool_ms = (time.perf_counter() - tool_start) * 1000
            is_error = '"error"' in result
            invoked.append(tc.function.name)

            # Emit point 2: the tool call
            _safe(recorder.tool_call, tc.function.name, args, result, tool_ms,
                  not is_error, result if is_error else None)

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        # Emit point 3: continuing iteration
        _safe(recorder.loop_iter, turn, invoked, "continuing",
              (time.perf_counter() - iter_start) * 1000)

    return "Max turns reached."


if __name__ == "__main__":
    os.makedirs("traces", exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    recorder = TraceRecorder(run_id=run_id, filepath=f"traces/trace_{run_id}.jsonl")

    questions = [
        "What's the weather in Tokyo?",
        "What is (15 * 7) + 23?",
        "What's the weather in Atlantis?",  # tool error path
    ]
    for q in questions:
        print(f"\nUser: {q}")
        print(f"Agent: {agent_chat(q, recorder)[:120]}")

    print(f"\nTrace written: traces/trace_{run_id}.jsonl")
    print(f"View it:       python trace_viewer.py traces/trace_{run_id}.jsonl")
