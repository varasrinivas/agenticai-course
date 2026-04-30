"""
UCC Entity Resolution Agent — ReAct Agent (Solution)

Complete implementation of the ReAct loop for resolving business entities
across UCC filings in multiple states.
"""

import json
import os
import anthropic
from tools import TOOL_SCHEMAS, execute_tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
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

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
        except Exception as e:
            print(f"\n[ERROR] API call failed: {e}")
            return f"Agent error: {e}"

        tool_use_blocks = []
        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                print(f"\n--- Step {step} ---")
                print(f"[THINK] {block.text}")

            elif block.type == "tool_use":
                tool_use_blocks.append(block)
                print(f"\n--- Step {step} ---")
                print(f"[ACT] Calling tool: {block.name}")
                print(f"      Args: {json.dumps(block.input, indent=2)}")

        if response.stop_reason == "end_turn":
            final_text = "\n".join(text_parts)
            print(f"\n[ANSWER] {final_text[:500]}...")
            return final_text

        if response.stop_reason == "tool_use" and tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_block in tool_use_blocks:
                result = execute_tool(tool_block.name, tool_block.input)
                print(f"[OBSERVE] {tool_block.name} returned: {result[:300]}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

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
