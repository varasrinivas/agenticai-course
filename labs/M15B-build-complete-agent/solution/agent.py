"""
M15B — Single ReAct Agent (Solution)
======================================
Complete single agent using all 3 tools.

Usage:
    python agent.py
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

import anthropic
from config import MODEL, MAX_AGENT_TURNS
from tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic()


def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    print(f"\n{'─' * 60}")
    print(f"[ACT]   Tool: {tool_name}")
    print(f"[INPUT] {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[OBSERVE]")
    if len(result) > 400:
        print(result[:400] + "\n... (truncated)")
    else:
        print(result)
    print(f"{'─' * 60}")


SYSTEM_PROMPT = """You are a UCC (Uniform Commercial Code) filing research agent.

You help users research UCC filings — public records documenting secured
commercial transactions (liens). You have three tools:

1. search_filings — find filings by debtor name and/or state
2. get_filing_details — get complete details for a specific filing
3. calculate_risk_score — assess lien risk for a debtor

## How to Work
- ALWAYS use tools. Never guess or fabricate data.
- Start by searching, then get details or calculate risk as needed.
- Cite specific filing numbers, dates, and parties.
- If no results found, say so clearly.
"""


def run_agent(user_query: str, max_turns: int = None) -> str:
    """Run a ReAct agent for the given user query."""
    if max_turns is None:
        max_turns = MAX_AGENT_TURNS

    observe("QUERY", user_query)
    messages = [{"role": "user", "content": user_query}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            observe("RESPONSE", final_text[:200] + "..." if len(final_text) > 200 else final_text)
            return final_text

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                observe_tool_call(block.name, block.input)
                result = execute_tool(block.name, block.input)
                observe_tool_result(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Agent did not complete within max turns."


if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Single Agent (SOLUTION)")
    print("=" * 60)

    print("\n\n>>> Test 1: Find Acme filings in New York")
    r1 = run_agent("Find all UCC filings for Acme Corporation in New York")
    print(f"\nANSWER:\n{r1}")

    print("\n\n>>> Test 2: Risk level for Acme Corporation")
    r2 = run_agent("What's the risk level for Acme Corporation?")
    print(f"\nANSWER:\n{r2}")

    print("\n\n>>> Test 3: Texas filings for Acme")
    r3 = run_agent("What about Acme Corporation's filings in Texas?")
    print(f"\nANSWER:\n{r3}")
