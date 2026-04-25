"""
M14 Lab -- Multi-Agent Systems: Analyst Subagent (Solution)
===========================================================
The Analyst receives raw findings from the Researcher, uses
calculate_risk for quantitative scoring, and identifies patterns.

Usage (standalone test):
    python analyst.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from tools import ANALYSIS_TOOLS, execute_tool

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


ANALYST_SYSTEM_PROMPT = """You are a UCC filing analyst. You receive raw research data from a
researcher agent and your job is to identify patterns, assess risk, and produce a structured
analysis.

## How to Work
1. Review the research data provided.
2. Use calculate_risk to get a quantitative risk score for the debtor.
3. Identify patterns in the filings.

## Patterns to Look For
- **Multi-state exposure**: Filings in more than one state
- **Blanket liens**: Collateral descriptions covering "all assets" or very broad scope
- **Secured party concentration**: Multiple liens held by the same lender
- **Filing freshness**: Recent filings vs old/lapsed ones
- **Amendment history**: UCC-3 amendments or terminations

## Output Format
Return a JSON object with this structure:
{
  "entity": "<name>",
  "risk_score": <0.0-1.0>,
  "risk_level": "LOW|MEDIUM|HIGH|UNKNOWN",
  "patterns": [
    {"pattern": "<name>", "detail": "<explanation>", "severity": "low|medium|high"}
  ],
  "summary": "<2-3 sentence summary of key findings>",
  "recommendation": "<actionable recommendation>"
}

## Rules
- Base ALL analysis on the provided research data. Do not fabricate filings.
- Use calculate_risk tool to get the official risk score.
- Be specific: cite filing numbers, dates, and parties in your analysis.
"""


def run_analyst(findings_json: str, max_turns: int = 5) -> str:
    """
    Run the Analyst subagent on the Researcher's findings.

    Args:
        findings_json: JSON string from the Researcher agent
        max_turns: Safety cap on loop iterations

    Returns:
        JSON string with analysis summary
    """
    try:
        findings = json.loads(findings_json)
        entity = findings.get("entity", "Unknown")
    except (json.JSONDecodeError, TypeError):
        entity = "Unknown"

    task = f"""Analyze the following UCC filing research data for '{entity}'.
Use the calculate_risk tool to get a quantitative risk score, then identify
patterns and produce your analysis.

## Research Data (from Researcher agent)
{findings_json}"""

    print(f"\n[ANALYST] Starting analysis for: {entity}")

    messages = [{"role": "user", "content": task}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=ANALYST_SYSTEM_PROMPT,
            tools=ANALYSIS_TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            print(f"[ANALYST] Complete ({len(text)} chars, {turn + 1} turn(s))")
            return text

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[ANALYST] Calling tool: {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    print("[ANALYST] Hit max turns without completing")
    return json.dumps({
        "entity": entity,
        "risk_score": 0,
        "risk_level": "UNKNOWN",
        "patterns": [],
        "summary": f"Analyst did not complete within {max_turns} turns",
        "recommendation": "N/A",
    })


if __name__ == "__main__":
    print("=" * 60)
    print("M14 Analyst — Standalone Test (SOLUTION)")
    print("=" * 60)

    sample_findings = json.dumps({
        "entity": "Greenfield Logistics LLC",
        "total_found": 2,
        "filings": [
            {
                "filing_number": "UCC-2024-NY-0012847",
                "type": "UCC-1",
                "state": "New York",
                "status": "Active",
                "filing_date": "2024-03-15",
                "secured_party": "Atlantic Capital Partners",
                "collateral_summary": "All accounts receivable, inventory, equipment...",
            },
            {
                "filing_number": "UCC-2024-NY-0012847",
                "type": "UCC-1",
                "state": "New York",
                "status": "Active",
                "filing_date": "2024-07-10",
                "secured_party": "Second National Bank",
                "collateral_summary": "All inventory and equipment.",
            },
        ],
    })

    result = run_analyst(sample_findings)
    print(f"\n[ANALYST] Analysis:\n{result}")
