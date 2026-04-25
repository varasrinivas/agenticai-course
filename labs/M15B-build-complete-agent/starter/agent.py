"""
M15B — Single ReAct Agent (Starter)
=====================================
A single agent that uses all 3 tools to research UCC filings.
This is the stepping stone before upgrading to coordinator + subagents.

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


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

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


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a UCC (Uniform Commercial Code) filing research agent.

You help users research UCC filings — public records documenting secured
commercial transactions (liens). You have three tools:

1. search_filings — find filings by debtor name and/or state
2. get_filing_details — get complete details for a specific filing
3. calculate_risk_score — assess lien risk for a debtor

## How to Work
- ALWAYS use tools to find information. Never guess or fabricate data.
- Start by searching for filings, then get details or calculate risk as needed.
- Cite specific filing numbers, dates, and parties in your answers.
- If no results found, say so clearly — don't make up filings.

## Response Format
- Lead with the key finding
- Include filing numbers and specific data
- End with an assessment or recommendation if relevant
"""


# =============================================================================
# REACT AGENT — YOUR CODE HERE
# =============================================================================

def run_agent(user_query: str, max_turns: int = None) -> str:
    """
    Run a ReAct agent for the given user query.

    Args:
        user_query: The user's question about UCC filings
        max_turns: Max loop iterations (default from config)

    Returns:
        Claude's final text response
    """
    if max_turns is None:
        max_turns = MAX_AGENT_TURNS

    observe("QUERY", user_query)

    # ------------------------------------------------------------------
    # TODO: Implement the ReAct loop
    #   1. Initialize messages with user query
    #   2. Loop up to max_turns:
    #      a) Call client.messages.create(model, max_tokens, system, tools, messages)
    #      b) If stop_reason != "tool_use": extract text, return it
    #      c) If "tool_use": execute tools, append results, continue
    #   3. Return fallback if max_turns exhausted
    #
    # This is the same pattern from M12 — now with 3 tools.
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Single Agent")
    print("=" * 60)

    # Test 1: Simple search
    print("\n\n>>> Test 1: Find Acme filings in New York")
    r1 = run_agent("Find all UCC filings for Acme Corporation in New York")
    print(f"\nANSWER:\n{r1}")

    # Test 2: Risk assessment
    print("\n\n>>> Test 2: Risk level for Acme Corporation")
    r2 = run_agent("What's the risk level for Acme Corporation?")
    print(f"\nANSWER:\n{r2}")

    # Test 3: State-specific follow-up style query
    print("\n\n>>> Test 3: Texas filings for Acme")
    r3 = run_agent("What about Acme Corporation's filings in Texas?")
    print(f"\nANSWER:\n{r3}")
