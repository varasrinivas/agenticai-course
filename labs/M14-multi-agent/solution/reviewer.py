"""
M14 Lab -- Multi-Agent Systems: Reviewer Subagent (Solution)
============================================================
The Reviewer cross-references the Writer's report against the
Researcher's original findings for accuracy verification.

Usage (standalone test):
    python reviewer.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


REVIEWER_SYSTEM_PROMPT = """You are a quality reviewer for UCC filing reports. Your job is to
verify accuracy and completeness by cross-referencing the report against the
original research data.

## Checks to Perform
1. **Filing numbers**: Every filing number cited in the report must exist in the research data.
2. **Data accuracy**: Dates, parties, states, and collateral descriptions must match the source.
3. **Risk consistency**: The risk level and score in the report must match the analyst's calculation.
4. **No fabrication**: The report must not contain any filing numbers, entities, or facts that
   are not in the original research data.
5. **Completeness**: All filings from the research should be mentioned in the report.

## Output Format
Return EXACTLY one of:

### If approved:
VERDICT: APPROVED
CONFIDENCE: [HIGH/MEDIUM/LOW]
NOTES: [brief note on report quality]

### If revision needed:
VERDICT: NEEDS_REVISION
ISSUES:
- [issue 1]
- [issue 2]
SUGGESTED_FIXES:
- [fix 1]
- [fix 2]

## Rules
- Be strict. If ANY filing number is fabricated, mark as NEEDS_REVISION.
- If the report is good but could be improved, still mark APPROVED with notes.
- Do not rewrite the report — only evaluate it.
"""


def run_reviewer(report: str, findings_json: str) -> str:
    """
    Run the Reviewer subagent to verify the report against source data.

    No tools — single API call for verification.

    Args:
        report: The formatted report from the Writer agent
        findings_json: The original JSON findings from the Researcher

    Returns:
        Review verdict string (APPROVED or NEEDS_REVISION with details)
    """
    task = f"""Review this UCC filing report for accuracy and completeness.
Cross-reference every claim in the report against the original research data.

## Report to Review
{report}

## Original Research Data (ground truth)
{findings_json}

Perform your checks and return your verdict."""

    print(f"\n[REVIEWER] Reviewing report...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=REVIEWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": task}],
    )

    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    print(f"[REVIEWER] Complete ({len(text)} chars)")
    return text


if __name__ == "__main__":
    print("=" * 60)
    print("M14 Reviewer — Standalone Test (SOLUTION)")
    print("=" * 60)

    sample_report = """# UCC Lien Risk Report: Greenfield Logistics LLC

## Executive Summary
Greenfield Logistics LLC has 1 active UCC filing in New York with broad collateral coverage.

## Filing Details
- **UCC-2024-NY-0012847** (UCC-1, Active): Filed 2024-03-15 in New York.
  Secured Party: Atlantic Capital Partners.
  Collateral: All accounts receivable, inventory, equipment, and general intangibles.

## Risk Assessment
- **Risk Score**: 0.55 / 1.00
- **Risk Level**: MEDIUM

## Recommendation
Review collateral descriptions before extending credit.
"""

    sample_findings = json.dumps({
        "entity": "Greenfield Logistics LLC",
        "total_found": 1,
        "filings": [
            {
                "filing_number": "UCC-2024-NY-0012847",
                "type": "UCC-1",
                "state": "New York",
                "status": "Active",
                "filing_date": "2024-03-15",
                "secured_party": "Atlantic Capital Partners",
                "collateral_summary": "All accounts receivable, inventory, equipment...",
            }
        ],
    })

    result = run_reviewer(sample_report, sample_findings)
    print(f"\n[REVIEWER] Verdict:\n{result}")
