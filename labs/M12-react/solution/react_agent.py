"""
M12 -- ReAct Agent (Complete Solution)
=======================================
A ReAct research agent with 3 UCC filing tools, query router, and trace logging.

Usage:
    python react_agent.py                  # Run test queries with ReAct loop
    python react_agent.py --router         # Run with query router
    python react_agent.py --trace          # Run with formatted trace output
    python react_agent.py --router --trace # Both router and trace
"""

import json
import re
import sys
import os
from dotenv import load_dotenv
from anthropic import Anthropic

from tools import TOOL_DEFINITIONS, execute_tool

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()

client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a UCC (Uniform Commercial Code) filing research agent.
You help users investigate UCC filings, assess debtor risk, and answer questions
about commercial liens and secured transactions.

When answering questions:
1. Think step-by-step about what information you need.
2. Use the available tools to gather data before answering.
3. Always cite specific filing numbers and data points in your answers.
4. If a search returns no results, say so clearly -- do not make up data.

You have access to these tools:
- search_filings: Search by debtor name and/or state
- get_filing_details: Get full details for a specific filing number
- calculate_risk: Compute risk score for a debtor
"""


# ---------------------------------------------------------------------------
# Trace logging helpers
# ---------------------------------------------------------------------------
class TraceLog:
    """Collects Think/Act/Observe/Response entries for later formatting."""

    def __init__(self):
        self.entries = []
        self.current_turn = 0

    def new_turn(self):
        self.current_turn += 1

    def think(self, text: str):
        self.entries.append({
            "turn": self.current_turn,
            "type": "THINK",
            "content": text,
        })

    def act(self, tool_name: str, tool_input: dict):
        input_str = ", ".join(f'{k}="{v}"' for k, v in tool_input.items())
        self.entries.append({
            "turn": self.current_turn,
            "type": "ACT",
            "content": f"{tool_name}({input_str})",
        })

    def observe(self, result: dict):
        if isinstance(result, dict):
            if "count" in result:
                summary = f"[{result['count']} result(s) found]"
            elif "risk_score" in result and result.get("success"):
                summary = (
                    f"{{risk_score: {result['risk_score']}, "
                    f"risk_level: \"{result['risk_level']}\"}}"
                )
            elif "filing" in result and result.get("success"):
                f = result["filing"]
                summary = f"[Filing {f['filing_number']} -- {f['debtor']['name']}]"
            elif "error" in result:
                summary = f"[ERROR: {result['error']}]"
            else:
                summary = json.dumps(result)[:120]
        else:
            summary = str(result)[:120]
        self.entries.append({
            "turn": self.current_turn,
            "type": "OBSERVE",
            "content": summary,
        })

    def response(self, text: str):
        self.entries.append({
            "turn": self.current_turn,
            "type": "RESPONSE",
            "content": text[:200] + ("..." if len(text) > 200 else ""),
        })


# ---------------------------------------------------------------------------
# ReAct loop (COMPLETE SOLUTION)
# ---------------------------------------------------------------------------
def run_react_agent(query: str, max_turns: int = 10) -> tuple[str, TraceLog]:
    """
    Run a ReAct agent loop for the given query.

    The loop:
      1. Send messages (with tools) to Claude
      2. If stop_reason == "tool_use": extract tool calls, execute them,
         append results, and loop back to step 1
      3. If stop_reason == "end_turn": extract final text and return
      4. Stop after max_turns to prevent infinite loops

    Args:
        query: The user's question
        max_turns: Maximum number of Think-->Act-->Observe cycles

    Returns:
        Tuple of (final_response_text, trace_log)
    """
    trace = TraceLog()
    messages = [{"role": "user", "content": query}]

    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    for turn in range(1, max_turns + 1):
        trace.new_turn()

        # Step 1: Call Claude with the current conversation + tools
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except Exception as e:
            error_msg = f"API error: {e}"
            print(f"\n[ERROR] {error_msg}")
            trace.response(error_msg)
            return (error_msg, trace)

        # Step 2: Extract any text blocks as the "think" step
        for block in response.content:
            if block.type == "text":
                trace.think(block.text)
                # Print a truncated version for readability
                preview = block.text[:150] + ("..." if len(block.text) > 150 else "")
                print(f"\n[THINK] Turn {turn}: {preview}")

        # Step 3: Check stop_reason
        if response.stop_reason == "end_turn":
            # Extract final text from the response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            if not final_text:
                final_text = "[No text in final response]"

            trace.response(final_text)
            print(f"\n[RESPONSE] {final_text[:300]}{'...' if len(final_text) > 300 else ''}")
            return (final_text, trace)

        # Step 4: Process tool calls (stop_reason == "tool_use")
        # Append assistant message to conversation
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool call and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                # Log the action
                trace.act(tool_name, tool_input)
                input_str = ", ".join(f'{k}="{v}"' for k, v in tool_input.items())
                print(f"[ACT]     Turn {turn}: {tool_name}({input_str})")

                # Execute the tool
                result = execute_tool(tool_name, tool_input)

                # Log the observation
                trace.observe(result)
                if isinstance(result, dict) and "count" in result:
                    print(f"[OBSERVE] Turn {turn}: {result['count']} result(s)")
                elif isinstance(result, dict) and result.get("success") and "risk_score" in result:
                    print(f"[OBSERVE] Turn {turn}: risk_score={result['risk_score']}, level={result['risk_level']}")
                elif isinstance(result, dict) and result.get("success") and "filing" in result:
                    print(f"[OBSERVE] Turn {turn}: Filing found -- {result['filing']['debtor']['name']}")
                elif isinstance(result, dict) and "error" in result:
                    print(f"[OBSERVE] Turn {turn}: ERROR -- {result['error']}")
                else:
                    print(f"[OBSERVE] Turn {turn}: {json.dumps(result)[:100]}")

                # Build tool result for the next message
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        # Append tool results as a user message
        messages.append({"role": "user", "content": tool_results})

    # Max turns reached
    print(f"\n[MAX TURNS REACHED ({max_turns})]")
    trace.response(f"[Max turns reached after {max_turns} cycles]")
    return (f"I wasn't able to complete the research within {max_turns} turns.", trace)


# ---------------------------------------------------------------------------
# Query Router (COMPLETE SOLUTION)
# ---------------------------------------------------------------------------
def classify_query(query: str) -> str:
    """
    Classify a query as "lookup" or "research".

    - "lookup": Direct filing number references, simple name searches
    - "research": Risk assessments, comparisons, multi-step analysis
    """
    query_lower = query.lower()

    # Pattern 1: Contains a filing number --> lookup
    if re.search(r"ucc-\d{4}-[a-z]{2}-\d+", query_lower):
        return "lookup"

    # Pattern 2: Simple search keywords without analysis --> lookup
    lookup_keywords = ["find", "search", "look up", "list", "show me"]
    research_keywords = [
        "risk", "assess", "compare", "analyze", "analysis",
        "why", "explain", "evaluate", "recommend", "should",
        "how many", "which is", "what is the risk",
    ]

    has_research = any(kw in query_lower for kw in research_keywords)
    has_lookup = any(kw in query_lower for kw in lookup_keywords)

    if has_research:
        return "research"
    if has_lookup:
        return "lookup"

    # Default to research (safer -- uses full ReAct loop)
    return "research"


def run_with_router(query: str) -> tuple[str, TraceLog]:
    """
    Route query to the appropriate handler.
    "lookup" queries get fewer turns; "research" queries get the full loop.
    """
    category = classify_query(query)
    print(f"\n[ROUTER] Classified as: {category.upper()}")

    if category == "lookup":
        return run_react_agent(query, max_turns=3)
    else:
        return run_react_agent(query, max_turns=10)


# ---------------------------------------------------------------------------
# Trace formatter (COMPLETE SOLUTION)
# ---------------------------------------------------------------------------
def format_trace(trace: TraceLog) -> str:
    """
    Format a TraceLog into a clean, human-readable string.
    """
    lines = []
    for entry in trace.entries:
        turn = entry["turn"]
        entry_type = entry["type"]
        content = entry["content"]
        padded_type = entry_type.ljust(8)
        lines.append(f'Turn {turn}: {padded_type} --> "{content}"')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    "Find all UCC filings for Greenfield Logistics",
    "What is the risk level for Greenfield Logistics and why?",
    "Get the full details of filing UCC-2024-CA-0098231",
]

if __name__ == "__main__":
    use_router = "--router" in sys.argv
    show_trace = "--trace" in sys.argv

    for query in TEST_QUERIES:
        if use_router:
            result_text, trace = run_with_router(query)
        else:
            result_text, trace = run_react_agent(query)

        if show_trace:
            print(f"\n--- Reasoning Trace ---")
            print(format_trace(trace))
            print(f"--- End Trace ---\n")
        else:
            print(f"\nFINAL ANSWER:\n{result_text}\n")
