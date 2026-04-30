"""
M14 Lab -- Multi-Agent Systems: Researcher Subagent (Starter)
=============================================================
The Researcher searches UCC filings for a given entity using
search_filings and get_filing_details tools. It returns
structured JSON findings that the Analyst will consume next.

Usage (standalone test):
    python researcher.py "Greenfield Logistics"
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from tools import RESEARCH_TOOLS, execute_tool

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# SYSTEM PROMPT — tells the Researcher what it is and how to work
# =============================================================================

RESEARCHER_SYSTEM_PROMPT = """You are a UCC filing researcher. Your ONLY job is to search for
and gather raw filing data for a given entity.

## How to Work
1. Use search_filings to find all filings for the entity (search by debtor name).
2. For each filing found, use get_filing_details to get the complete record.
3. Compile your findings into a structured JSON summary.

## Output Format
Return a JSON object with this structure:
{
  "entity": "<name searched>",
  "total_found": <count>,
  "filings": [
    {
      "filing_number": "...",
      "type": "...",
      "state": "...",
      "status": "...",
      "filing_date": "...",
      "secured_party": "...",
      "collateral_summary": "..."
    }
  ]
}

## Rules
- ALWAYS use tools. Never guess or make up filing data.
- Search broadly first, then get details for each match.
- If no filings are found, return {"entity": "...", "total_found": 0, "filings": []}.
- Include ALL filings found, not just the first few.
"""


# =============================================================================
# RESEARCHER AGENT — YOUR CODE HERE
# =============================================================================

def run_researcher(entity_name: str, max_turns: int = 10) -> str:
    """
    Run the Researcher subagent to find all UCC filings for an entity.

    This is a ReAct loop: send a task to Claude with research tools,
    execute any tool calls, feed results back, repeat until Claude
    produces a final text response.

    Args:
        entity_name: The company/entity name to research
        max_turns: Safety cap on loop iterations

    Returns:
        JSON string with structured findings
    """
    task = f"Find all UCC filings for '{entity_name}'. Search across all states."

    print(f"\n[RESEARCHER] Starting research for: {entity_name}")

    # ------------------------------------------------------------------
    # TODO 1: Initialize messages list with the task
    #   messages = [{"role": "user", "content": task}]
    # ------------------------------------------------------------------
    messages = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO 2: Implement the ReAct loop
    #   - Loop up to max_turns times
    #   - Call client.messages.create() with:
    #       model=MODEL, max_tokens=4096,
    #       system=RESEARCHER_SYSTEM_PROMPT,
    #       tools=RESEARCH_TOOLS,
    #       messages=messages
    #   - If response.stop_reason != "tool_use":
    #       Extract text from response.content blocks
    #       Return the text (this is the researcher's findings)
    #   - If response.stop_reason == "tool_use":
    #       For each block in response.content where block.type == "tool_use":
    #           result = execute_tool(block.name, block.input)
    #           Collect: {"type": "tool_result", "tool_use_id": block.id, "content": result}
    #       Append assistant message and tool results to messages
    #   - After the loop, return a fallback error message
    # ------------------------------------------------------------------

    # Placeholder: return empty findings so coordinator doesn't crash
    return json.dumps({
        "entity": entity_name,
        "total_found": 0,
        "filings": [],
        "note": "TODO: Implement the ReAct loop in run_researcher()",
    })


# =============================================================================
# MAIN — standalone test
# =============================================================================

if __name__ == "__main__":
    entity = sys.argv[1] if len(sys.argv) > 1 else "Greenfield Logistics"
    print("=" * 60)
    print(f"M14 Researcher — Standalone Test")
    print("=" * 60)
    result = run_researcher(entity)
    print(f"\n[RESEARCHER] Findings:\n{result}")
