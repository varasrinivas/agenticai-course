"""
UCC Entity Resolution Agent — ReAct Agent (Starter)

This agent uses the ReAct pattern to resolve business entities across
UCC filings in multiple states, identifying name variations and merging
into a unified entity profile.

YOUR TASK: Complete the TODO sections to build a working ReAct agent.
"""

import json
import os
import anthropic
from tools import TOOL_SCHEMAS, execute_tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 15

SYSTEM_PROMPT = """You are a UCC Entity Resolution Agent. Your job is to take a business name and
resolve it across UCC filings in multiple states, identifying all name variations,
confirming entity identity, and building a unified entity profile.

You MUST follow this reasoning process:
1. FIRST, search for filings by the given business name across all states
2. THEN, examine the results for name variations (abbreviations, DBA names, misspellings)
3. NEXT, use fuzzy matching to score how closely name variations match
4. THEN, look up the business registry data to confirm identity (using EIN or name)
5. CHECK for entities that have similar names but are DIFFERENT businesses (different EINs)
6. FINALLY, merge all confirmed filings into a unified entity profile

Think step-by-step. Pay careful attention to:
- Same EIN across different name spellings = same entity
- Similar names but different EINs = different entities (flag this)
- DBA names and former names listed in registry data
- Name changes documented in filing amendments

When you find name variations, always verify with fuzzy_match_score before assuming
they are the same entity. Use the EIN as the definitive identifier."""

# ---------------------------------------------------------------------------
# ReAct Agent Loop
# ---------------------------------------------------------------------------

def run_agent(user_query: str) -> str:
    """
    Run the ReAct agent loop.

    Args:
        user_query: The entity resolution query.

    Returns:
        The agent's final response text.
    """
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": user_query}]

    step = 0
    print("\n" + "=" * 70)
    print("REASONING TRACE")
    print("=" * 70)

    while step < MAX_ITERATIONS:
        step += 1

        # TODO 1: Send the message to Claude with tools
        response = None  # Replace with API call

        # TODO 2: Process the response content blocks
        # TextBlock → [THINK], ToolUseBlock → [ACT] + execute + [OBSERVE]

        # TODO 3: Check stop reason
        # "end_turn" → return final text
        # "tool_use" → continue loop

        # TODO 4: Build tool_result messages and append to conversation

        pass  # Remove once TODOs are implemented

    return "Agent reached maximum iterations without completing."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    query = (
        "Resolve entity: Acme Corp. Find all UCC filings across all states, "
        "identify all name variations, and build a unified entity profile. "
        "Be sure to distinguish this entity from any similarly-named but "
        "separate businesses."
    )

    result = run_agent(query)
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(result)


if __name__ == "__main__":
    main()
