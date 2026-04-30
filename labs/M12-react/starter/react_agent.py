"""
M12 -- ReAct Agent Skeleton
============================
Build the Think --> Act --> Observe loop that powers AI agents.

YOUR TASK: Complete the functions marked with TODO.

Usage:
    python react_agent.py                  # Run test queries with ReAct loop
    python react_agent.py --router         # Run with query router
    python react_agent.py --trace          # Run with formatted trace output
    python react_agent.py --router --trace # Both router and trace
"""

import json
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
# Trace logging helpers (complete -- use these in your ReAct loop)
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
        # Compact summary of tool result
        if isinstance(result, dict):
            if "count" in result:
                summary = f"[{result['count']} result(s) found]"
            elif "risk_score" in result and result.get("success"):
                summary = f"{{risk_score: {result['risk_score']}, risk_level: \"{result['risk_level']}\"}}"
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
# ReAct loop
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

        # -----------------------------------------------------------------
        # TODO 1: Call the Anthropic API with messages, tools, and system prompt
        # -----------------------------------------------------------------
        # HINT: Use client.messages.create() with:
        #   - model=MODEL
        #   - max_tokens=4096
        #   - system=SYSTEM_PROMPT
        #   - tools=TOOL_DEFINITIONS
        #   - messages=messages
        #
        # response = client.messages.create(...)
        response = None  # <-- Replace this line

        # -----------------------------------------------------------------
        # TODO 2: Extract any text blocks from the response as the "think" step
        # -----------------------------------------------------------------
        # HINT: Loop through response.content and check for blocks where
        #       block.type == "text". Log each one with trace.think()
        #       and print it as [THINK].
        #
        # for block in response.content:
        #     if block.type == "text":
        #         ...
        pass  # <-- Replace this

        # -----------------------------------------------------------------
        # TODO 3: Check the stop_reason to decide what to do next
        # -----------------------------------------------------------------
        # HINT: response.stop_reason will be either "tool_use" or "end_turn"
        #
        # If stop_reason == "end_turn":
        #   - Extract the final text from response.content
        #   - Log it with trace.response()
        #   - Print [RESPONSE] and return (final_text, trace)
        #
        # If stop_reason == "tool_use":
        #   - Continue to TODO 4 below
        #
        # if response.stop_reason == "end_turn":
        #     ...
        #     return (final_text, trace)
        pass  # <-- Replace this

        # -----------------------------------------------------------------
        # TODO 4: Process tool calls (only reached if stop_reason == "tool_use")
        # -----------------------------------------------------------------
        # HINT:
        #   a) Append the assistant's response to messages:
        #      messages.append({"role": "assistant", "content": response.content})
        #
        #   b) For each block in response.content where block.type == "tool_use":
        #      - Log with trace.act(block.name, block.input)
        #      - Print [ACT]
        #      - Call execute_tool(block.name, block.input)
        #      - Log with trace.observe(result)
        #      - Print [OBSERVE]
        #      - Build a tool_result content block:
        #        {"type": "tool_result", "tool_use_id": block.id,
        #         "content": json.dumps(result)}
        #
        #   c) Append all tool results as a "user" message:
        #      messages.append({"role": "user", "content": tool_results})
        pass  # <-- Replace this

    # If we exit the loop, we hit max_turns
    print(f"\n[MAX TURNS REACHED ({max_turns})]")
    trace.response(f"[Max turns reached after {max_turns} cycles]")
    return (f"I wasn't able to complete the research within {max_turns} turns.", trace)


# ---------------------------------------------------------------------------
# Query Router
# ---------------------------------------------------------------------------
def classify_query(query: str) -> str:
    """
    Classify a query as "lookup" or "research".

    - "lookup": Direct filing number references, simple name searches
    - "research": Risk assessments, comparisons, multi-step analysis

    Args:
        query: The user's question

    Returns:
        "lookup" or "research"
    """
    # -----------------------------------------------------------------
    # TODO 5: Implement query classification
    # -----------------------------------------------------------------
    # HINT: Use keyword heuristics:
    #   - If query contains a filing number pattern (UCC-20XX-XX-XXXXXXX)
    #     or words like "find", "search", "look up", "details" --> "lookup"
    #   - If query contains "risk", "assess", "compare", "analyze",
    #     "why", "explain" --> "research"
    #   - Default to "research" (safer -- uses full ReAct loop)
    #
    # import re
    # if re.search(r"UCC-\d{4}-[A-Z]{2}-\d+", query):
    #     return "lookup"
    # ...
    return "research"  # <-- Replace with real classification


def run_with_router(query: str) -> tuple[str, TraceLog]:
    """
    Route query to the appropriate handler.

    "lookup" queries get a simpler single-turn call.
    "research" queries go through the full ReAct loop.

    Args:
        query: The user's question

    Returns:
        Tuple of (final_response_text, trace_log)
    """
    # -----------------------------------------------------------------
    # TODO 6: Implement the router
    # -----------------------------------------------------------------
    # HINT:
    #   category = classify_query(query)
    #   print(f"[ROUTER] Classified as: {category}")
    #
    #   if category == "lookup":
    #       # Use run_react_agent with max_turns=3 (simple queries need fewer turns)
    #       return run_react_agent(query, max_turns=3)
    #   else:
    #       # Use run_react_agent with full max_turns=10
    #       return run_react_agent(query, max_turns=10)
    return run_react_agent(query)  # <-- Replace with routed version


# ---------------------------------------------------------------------------
# Trace formatter
# ---------------------------------------------------------------------------
def format_trace(trace: TraceLog) -> str:
    """
    Format a TraceLog into a clean, human-readable string.

    Output format:
        Turn 1: THINK    --> "I need to search for ..."
        Turn 1: ACT      --> search_filings(debtor_name="...")
        Turn 1: OBSERVE  --> [2 results found]
        Turn 2: RESPONSE --> "Based on my research..."

    Args:
        trace: A TraceLog instance

    Returns:
        Formatted string
    """
    # -----------------------------------------------------------------
    # TODO 7: Format the trace entries
    # -----------------------------------------------------------------
    # HINT: Loop through trace.entries and format each one:
    #
    # lines = []
    # for entry in trace.entries:
    #     turn = entry["turn"]
    #     entry_type = entry["type"]
    #     content = entry["content"]
    #     # Pad the type for alignment: "THINK   ", "ACT     ", etc.
    #     padded_type = entry_type.ljust(8)
    #     lines.append(f'Turn {turn}: {padded_type} --> "{content}"')
    # return "\n".join(lines)
    return "[Trace formatting not implemented yet]"  # <-- Replace


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
