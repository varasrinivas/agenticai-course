"""
M06 Lab - Step 2: The Orchestrating Loop
=========================================
The M05 loop + tool filtering + max-iterations guard + PARALLEL execution.
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
    """Run the multi-tool agent. Optionally filter tools by tag.

    TODO:
    1. active_tools = registry.get_tools_for_context(tags=tool_tags) if tool_tags
       else registry.get_tools_for_context()
    2. messages = [{"role": "system", "content": SYSTEM},
                   {"role": "user", "content": question}]
    3. for iteration in range(10):          ← max-iterations guard, NOT while True
       a. response = client.chat.completions.create(model="mistral",
              tools=active_tools, messages=messages)
          (try/except → return f"API error: {e}")
       b. choice = response.choices[0]; tool_calls = choice.message.tool_calls or []
       c. If choice.finish_reason == "stop" or not tool_calls:
            return choice.message.content or ""
       d. Append the assistant message (content + tool_calls) to messages
       e. If verbose: print "PARALLEL" if len(tool_calls) > 1 else "SEQUENTIAL"
          and each requested call
       f. EXECUTE:
          - If len(tool_calls) > 1: use ThreadPoolExecutor + as_completed —
            submit execute_tool(name, json.loads(arguments)) per call, map each
            future back to its tool_call.id, build the {"role": "tool", ...} list
          - Else: run the single call directly
          REMEMBER: every tool_call_id needs a result message, including errors
       g. messages.extend(tool_results) and loop back
    4. After the loop: return "Max iterations reached."
    """
    pass  # Remove this line when you add your code


# ── Test Scenarios (COMPLETE) ──
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
