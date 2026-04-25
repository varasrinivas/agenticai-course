"""
M14 Lab -- Multi-Agent Systems: Researcher Subagent (Solution)
==============================================================
The Researcher searches UCC filings for a given entity using
search_filings and get_filing_details tools via a ReAct loop.

Usage (standalone test):
    python researcher.py "Greenfield Logistics"
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Allow imports from starter/ (tools.py) and labs/ (shared/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from tools import RESEARCH_TOOLS, execute_tool

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


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


def run_researcher(entity_name: str, max_turns: int = 10) -> str:
    """
    Run the Researcher subagent to find all UCC filings for an entity.

    Uses a ReAct loop with search_filings and get_filing_details tools.

    Args:
        entity_name: The company/entity name to research
        max_turns: Safety cap on loop iterations

    Returns:
        JSON string with structured findings
    """
    task = f"Find all UCC filings for '{entity_name}'. Search across all states."

    print(f"\n[RESEARCHER] Starting research for: {entity_name}")

    messages = [{"role": "user", "content": task}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=RESEARCHER_SYSTEM_PROMPT,
            tools=RESEARCH_TOOLS,
            messages=messages,
        )

        # Done — Claude has produced a final text response
        if response.stop_reason != "tool_use":
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            print(f"[RESEARCHER] Complete ({len(text)} chars, {turn + 1} turn(s))")
            return text

        # Tool use — execute each requested tool and feed results back
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[RESEARCHER] Calling tool: {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Safety fallback
    print("[RESEARCHER] Hit max turns without completing")
    return json.dumps({
        "entity": entity_name,
        "total_found": 0,
        "filings": [],
        "error": f"Researcher did not complete within {max_turns} turns",
    })


if __name__ == "__main__":
    entity = sys.argv[1] if len(sys.argv) > 1 else "Greenfield Logistics"
    print("=" * 60)
    print("M14 Researcher — Standalone Test (SOLUTION)")
    print("=" * 60)
    result = run_researcher(entity)
    print(f"\n[RESEARCHER] Findings:\n{result}")
