"""
M06 Lab - Step 2: The Orchestrating Loop — SOLUTION
====================================================
Run: python research_agent.py
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from tools_registry import build_registry, execute_tool

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
registry = build_registry()

SYSTEM = (
    "You are a research assistant. When asked to compare or research multiple "
    "topics, search for each one in parallel. When asked to fetch and summarize "
    "a page, do it sequentially."
)


def run_agent(question: str, tool_tags: list[str] = None, verbose: bool = True) -> str:
    """Run the multi-tool agent. Optionally filter tools by tag."""
    if tool_tags:
        active_tools = registry.get_tools_for_context(tags=tool_tags)
    else:
        active_tools = registry.get_tools_for_context()

    if verbose:
        print(f"  Active tools: {[t['function']['name'] for t in active_tools]}")

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

    for iteration in range(10):  # safety limit
        try:
            response = client.chat.completions.create(
                model="mistral",
                tools=active_tools,
                messages=messages,
            )
        except Exception as e:
            return f"API error: {e}"

        choice = response.choices[0]
        tool_calls = choice.message.tool_calls or []

        if choice.finish_reason == "stop" or not tool_calls:
            if verbose:
                print(f"  Agent finished in {iteration + 1} iteration(s)")
            return choice.message.content or ""

        # Append assistant message (must precede the tool results)
        messages.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ],
        })

        if verbose:
            mode = "PARALLEL" if len(tool_calls) > 1 else "SEQUENTIAL"
            print(f"\n  Iteration {iteration + 1} [{mode}]:")
            for tc in tool_calls:
                print(f"    -> {tc.function.name}({tc.function.arguments[:80]})")

        # Execute tools — parallel when multiple requested
        if len(tool_calls) > 1:
            tool_results = []
            with ThreadPoolExecutor(max_workers=len(tool_calls)) as pool:
                futures = {
                    pool.submit(execute_tool, tc.function.name, json.loads(tc.function.arguments)): tc.id
                    for tc in tool_calls
                }
                # as_completed yields in FINISH order; matching is by tool_call_id
                for future in as_completed(futures):
                    tid = futures[future]
                    result_json, is_err = future.result()
                    if verbose and is_err:
                        print(f"    [error] {result_json[:60]}")
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tid,
                        "content": result_json,
                    })
        else:
            tc = tool_calls[0]
            result_json, is_err = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            if verbose and is_err:
                print(f"    [error] {result_json[:60]}")
            tool_results = [{
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_json,
            }]

        messages.extend(tool_results)

    return "Max iterations reached."


if __name__ == "__main__":
    print("\n" + "> TEST 1: PARALLEL SEARCH ".ljust(60, "-"))
    r1 = run_agent(
        "Search for information about these 3 topics: AI agents, "
        "prompt engineering, and tool use patterns.",
        tool_tags=["research"],
    )
    print(f"\nResult preview: {(r1 or '')[:200]}...")

    print("\n" + "> TEST 2: SEQUENTIAL CHAIN ".ljust(60, "-"))
    r2 = run_agent(
        "Search for 'Mistral AI tool use', then fetch the first "
        "result page and summarize its content.",
        tool_tags=["research"],
    )
    print(f"\nResult preview: {(r2 or '')[:200]}...")

    print("\n" + "> TEST 3: ERROR RECOVERY ".ljust(60, "-"))
    r3 = run_agent(
        "Fetch and summarize this page: https://broken.example.com/404",
        tool_tags=["research"],
    )
    print(f"\nResult preview: {(r3 or '')[:200]}...")

    print("\n" + "> TEST 4: DYNAMIC TOOL FILTERING ".ljust(60, "-"))
    r4 = run_agent(
        "Format a citation for an article titled 'Multi-Tool AI Agents' "
        "from https://example.com/agents, accessed today.",
        tool_tags=["citation"],
    )
    print(f"\nResult preview: {(r4 or '')[:200]}...")
