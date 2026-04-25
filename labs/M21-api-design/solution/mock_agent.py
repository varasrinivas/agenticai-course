"""
M21: Mock UCC Agent — Complete (same as starter)
Provides realistic agent responses without requiring an Anthropic API key.
Uses the same mock data patterns from M15B.

Functions:
    mock_query(query) -> dict   — synchronous response
    mock_stream(query) -> generator — yields string chunks
"""

import time
import random
import re

# ---------------------------------------------------------------------------
# Mock filing data (subset of shared/mock_ucc_data.py)
# ---------------------------------------------------------------------------
MOCK_FILINGS = [
    {
        "filing_number": "UCC-2024-NY-0012847",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "Atlantic Capital Partners",
        "state": "New York",
        "status": "Active",
        "collateral": "All accounts receivable, inventory, equipment, and general intangibles",
    },
    {
        "filing_number": "UCC-2024-CA-0098231",
        "debtor": "Pacific Ridge Technologies Inc",
        "secured_party": "Silicon Valley Bank",
        "state": "California",
        "status": "Active",
        "collateral": "All assets including intellectual property, patents, trademarks",
    },
    {
        "filing_number": "UCC-2023-TX-0187634",
        "debtor": "Lone Star Energy Solutions LP",
        "secured_party": "Wells Fargo Equipment Finance",
        "state": "Texas",
        "status": "Active",
        "collateral": "Specific equipment: Caterpillar excavators and Liebherr crane",
    },
    {
        "filing_number": "UCC-2024-FL-0054219",
        "debtor": "Sunshine Medical Group PA",
        "secured_party": "TD Bank N.A.",
        "state": "Florida",
        "status": "Amendment",
        "collateral": "Medical equipment including MRI systems and CT scanner",
    },
    {
        "filing_number": "UCC-2022-DE-0002914",
        "debtor": "Nextera Holdings Corp",
        "secured_party": "JPMorgan Chase Bank N.A.",
        "state": "Delaware",
        "status": "Active",
        "collateral": "All assets, whether now owned or hereafter acquired",
    },
]

# ---------------------------------------------------------------------------
# Canned responses keyed by query pattern
# ---------------------------------------------------------------------------
CANNED_RESPONSES = {
    "acme": {
        "answer": (
            "I found 2 UCC filings potentially related to Acme Corporation in New York.\n\n"
            "1. **UCC-2024-NY-0012847** — Greenfield Logistics LLC (debtor) with "
            "Atlantic Capital Partners (secured party). Filed 2024-03-15, covering all "
            "accounts receivable, inventory, equipment, and general intangibles. Status: Active.\n\n"
            "2. **UCC-2022-DE-0002914** — Nextera Holdings Corp (debtor) with JPMorgan Chase "
            "Bank N.A. (secured party). Filed 2022-04-30, covering all assets. Status: Active.\n\n"
            "Note: No exact match for 'Acme Corporation' was found. The results above are "
            "the closest matches based on entity resolution. You may want to verify the "
            "legal entity name in the state's filing database."
        ),
        "sources": ["UCC-2024-NY-0012847", "UCC-2022-DE-0002914"],
        "tokens_used": 1247,
    },
    "risk": {
        "answer": (
            "**Risk Assessment Summary**\n\n"
            "Based on the UCC filing analysis, here is the risk profile:\n\n"
            "- **Lien Count:** 3 active filings identified\n"
            "- **Collateral Coverage:** Broad — includes 'all assets' clauses in 2 filings\n"
            "- **Risk Level:** MEDIUM-HIGH\n\n"
            "**Key Concerns:**\n"
            "1. Multiple secured parties have claims on overlapping collateral\n"
            "2. One filing covers 'all assets' which creates subordination risk\n"
            "3. No terminated filings found — all liens are currently active\n\n"
            "**Recommendation:** Obtain a full lien search from the state filing office "
            "and request payoff letters from existing secured parties before proceeding."
        ),
        "sources": ["UCC-2024-NY-0012847", "UCC-2024-CA-0098231", "UCC-2022-DE-0002914"],
        "tokens_used": 1583,
    },
    "default": {
        "answer": (
            "I searched the UCC filing database and found the following results:\n\n"
            "1. **UCC-2024-NY-0012847** — Greenfield Logistics LLC → Atlantic Capital Partners. "
            "Active filing in New York covering accounts receivable, inventory, and equipment.\n\n"
            "2. **UCC-2024-CA-0098231** — Pacific Ridge Technologies Inc → Silicon Valley Bank. "
            "Active filing in California covering all assets including IP.\n\n"
            "3. **UCC-2023-TX-0187634** — Lone Star Energy Solutions LP → Wells Fargo Equipment "
            "Finance. Active filing in Texas covering specific heavy equipment.\n\n"
            "The search returned 3 active filings across 3 states. Would you like me to "
            "drill into any specific filing or run a risk assessment?"
        ),
        "sources": ["UCC-2024-NY-0012847", "UCC-2024-CA-0098231", "UCC-2023-TX-0187634"],
        "tokens_used": 1102,
    },
}


def _select_response(query: str) -> dict:
    """Pick the best canned response based on query keywords."""
    query_lower = query.lower()
    if "risk" in query_lower or "assess" in query_lower:
        return CANNED_RESPONSES["risk"]
    if "acme" in query_lower:
        return CANNED_RESPONSES["acme"]
    return CANNED_RESPONSES["default"]


def mock_query(query: str) -> dict:
    """
    Simulate a synchronous UCC agent query.

    Args:
        query: The user's natural-language question about UCC filings.

    Returns:
        dict with keys: answer (str), sources (list[str]), tokens_used (int)

    Simulates realistic latency (0.5-2.0 seconds).
    """
    latency = random.uniform(0.5, 2.0)
    time.sleep(latency)

    response = _select_response(query)
    return {
        "answer": response["answer"],
        "sources": response["sources"],
        "tokens_used": response["tokens_used"],
    }


def mock_stream(query: str):
    """
    Simulate a streaming UCC agent query.

    Args:
        query: The user's natural-language question about UCC filings.

    Yields:
        str — one chunk of the response at a time.

    Simulates realistic chunk-by-chunk delivery with 50-200ms between chunks.
    """
    response = _select_response(query)
    answer = response["answer"]

    words = answer.split()
    pos = 0
    while pos < len(words):
        chunk_size = random.randint(3, 8)
        chunk_words = words[pos : pos + chunk_size]
        chunk = " ".join(chunk_words)

        if pos + chunk_size < len(words):
            chunk += " "

        yield chunk

        time.sleep(random.uniform(0.05, 0.2))
        pos += chunk_size


if __name__ == "__main__":
    print("=== Mock Agent Test ===\n")

    print("1. Synchronous query:")
    result = mock_query("Find all UCC filings for Acme Corporation in New York")
    print(f"   Answer length: {len(result['answer'])} chars")
    print(f"   Sources: {result['sources']}")
    print(f"   Tokens used: {result['tokens_used']}")
    print()

    print("2. Streaming query:")
    print("   ", end="", flush=True)
    for chunk in mock_stream("What is the risk level for Acme Corporation?"):
        print(chunk, end="", flush=True)
    print("\n")

    print("=== Mock Agent Test Complete ===")
