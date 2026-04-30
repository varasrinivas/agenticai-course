"""
M14 Lab -- Multi-Agent Systems: Analyst Subagent (Starter)
==========================================================
The Analyst receives raw findings from the Researcher and
identifies patterns: multi-state exposure, blanket liens,
secured party concentration. Uses calculate_risk tool for
quantitative scoring.

Usage (standalone test):
    python analyst.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from tools import ANALYSIS_TOOLS, execute_tool

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# SYSTEM PROMPT — tells the Analyst what it is and how to work
# =============================================================================

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


# =============================================================================
# ANALYST AGENT — YOUR CODE HERE
# =============================================================================

def run_analyst(findings_json: str, max_turns: int = 5) -> str:
    """
    Run the Analyst subagent on the Researcher's findings.

    The Analyst receives the raw findings JSON, uses calculate_risk
    to get a quantitative score, and identifies patterns.

    Args:
        findings_json: JSON string from the Researcher agent
        max_turns: Safety cap on loop iterations

    Returns:
        JSON string with analysis summary
    """
    # Parse findings to extract entity name for risk calculation
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

    # ------------------------------------------------------------------
    # TODO 1: Initialize messages list with the task
    # ------------------------------------------------------------------
    messages = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO 2: Implement the ReAct loop (same pattern as researcher)
    #   - Loop up to max_turns
    #   - Call client.messages.create() with:
    #       model=MODEL, max_tokens=4096,
    #       system=ANALYST_SYSTEM_PROMPT,
    #       tools=ANALYSIS_TOOLS,
    #       messages=messages
    #   - If stop_reason != "tool_use": extract text and return it
    #   - If stop_reason == "tool_use": execute tools, append results
    # ------------------------------------------------------------------

    # Placeholder: return empty analysis so coordinator doesn't crash
    return json.dumps({
        "entity": entity,
        "risk_score": 0,
        "risk_level": "UNKNOWN",
        "patterns": [],
        "summary": "TODO: Implement the ReAct loop in run_analyst()",
        "recommendation": "N/A",
    })


# =============================================================================
# MAIN — standalone test with sample findings
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M14 Analyst — Standalone Test")
    print("=" * 60)

    # Sample findings (as if the Researcher had run)
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
