"""
M07 Lab - Step 2: MCP Server with Resources (Solution)
=======================================================
MCP server with both tools AND resources for UCC filing data.

Usage (from the labs/ directory):
    python M07-mcp/solution/mcp_server_resources.py
"""

import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.mock_ucc_data import (
    search_filings, get_filing_by_number, ALL_FILINGS, get_stats
)

from mcp.server.fastmcp import FastMCP

# =============================================================================
# SERVER SETUP
# =============================================================================

mcp = FastMCP("UCC Filing Server")


# =============================================================================
# HELPER
# =============================================================================

def format_filing(filing: dict) -> str:
    """Format a single filing dict into a human-readable string."""
    lines = [
        f"Filing: {filing['filing_number']}",
        f"  Type:           {filing['type']}",
        f"  State:          {filing['state']}",
        f"  Status:         {filing['status']}",
        f"  Filed:          {filing['filing_date']}",
        f"  Expires:        {filing.get('expiration_date', 'N/A')}",
        f"  Debtor:         {filing['debtor']['name'] or '(missing)'}",
        f"  Secured Party:  {filing['secured_party']['name']}",
        f"  Collateral:     {filing['collateral_description'][:80]}...",
    ]
    return "\n".join(lines)


# =============================================================================
# TOOLS
# =============================================================================

@mcp.tool()
def search_ucc_filings(debtor_name: str = None, state: str = None, status: str = None) -> str:
    """Search UCC filings by debtor name, state, or status. Supports partial name matching and case-insensitive filters."""
    results = search_filings(debtor_name=debtor_name, state=state, status=status)
    if not results:
        return "No filings found matching your criteria."
    formatted = "\n\n".join(format_filing(f) for f in results)
    return f"Found {len(results)} filing(s):\n\n{formatted}"


@mcp.tool()
def get_filing(filing_number: str) -> str:
    """Retrieve a specific UCC filing by its filing number. Returns the full filing record as JSON."""
    filing = get_filing_by_number(filing_number)
    if not filing:
        return f"No filing found with number: {filing_number}"
    return json.dumps(filing, indent=2, default=str)


# =============================================================================
# RESOURCES
# =============================================================================

@mcp.resource("ucc://filings")
def list_all_filings() -> str:
    """Index of all UCC filings in the dataset. Returns a summary line for each filing."""
    lines = []
    for filing in ALL_FILINGS:
        debtor = filing['debtor']['name'] or '(missing)'
        lines.append(
            f"{filing['filing_number']} | {debtor} | {filing['state']} | {filing['status']}"
        )
    header = f"UCC Filings Index ({len(ALL_FILINGS)} total):\n\n"
    return header + "\n".join(lines)


@mcp.resource("ucc://filing/{filing_number}")
def get_filing_resource(filing_number: str) -> str:
    """Retrieve the full details of a specific UCC filing by its filing number."""
    filing = get_filing_by_number(filing_number)
    if not filing:
        return f"No filing found: {filing_number}"
    return json.dumps(filing, indent=2, default=str)


@mcp.resource("ucc://stats")
def get_dataset_stats() -> str:
    """Summary statistics about the UCC filings dataset: counts by status, states covered, edge cases."""
    stats = get_stats()
    return json.dumps(stats, indent=2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Starting UCC Filing MCP Server with Resources (stdio transport)...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    mcp.run()
