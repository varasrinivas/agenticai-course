"""
M07 Lab - Step 2: MCP Server with Resources (Starter)
======================================================
Extend your MCP server to expose UCC filing DATA as resources.

KEY CONCEPT: Tools are for ACTIONS. Resources are for DATA.
  - Tool:     "Search filings by state"  (takes input, returns results)
  - Resource: "ucc://filings"            (read-only data, like a GET endpoint)

Resources have URIs (like URLs). Clients can:
  1. List available resources
  2. Read a resource by its URI
  3. Use URI templates for parameterized resources (like ucc://filing/{number})

Usage (from the labs/ directory):
    python M07-mcp/starter/mcp_server_resources.py
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
# SERVER SETUP (complete -- do not modify)
# =============================================================================

mcp = FastMCP("UCC Filing Server")


# =============================================================================
# HELPER (complete -- do not modify)
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
# TOOLS (complete -- carried over from Step 1)
# =============================================================================

@mcp.tool()
def search_ucc_filings(debtor_name: str = None, state: str = None, status: str = None) -> str:
    """Search UCC filings by debtor name, state, or status."""
    results = search_filings(debtor_name=debtor_name, state=state, status=status)
    if not results:
        return "No filings found matching your criteria."
    formatted = "\n\n".join(format_filing(f) for f in results)
    return f"Found {len(results)} filing(s):\n\n{formatted}"


@mcp.tool()
def get_filing(filing_number: str) -> str:
    """Retrieve a specific UCC filing by its filing number."""
    filing = get_filing_by_number(filing_number)
    if not filing:
        return f"No filing found with number: {filing_number}"
    return json.dumps(filing, indent=2, default=str)


# =============================================================================
# YOUR CODE: Register resources with @mcp.resource()
# =============================================================================

# --------------------------------------------------------------------------
# TODO 1: Register a resource at URI "ucc://filings"
#
#   Use the @mcp.resource("ucc://filings") decorator.
#   The function should return a string listing ALL filings in summary form.
#
#   Implementation:
#     1. Loop through ALL_FILINGS
#     2. For each filing, create a one-line summary:
#        f"{filing['filing_number']} | {filing['debtor']['name'] or '(missing)'} | {filing['state']} | {filing['status']}"
#     3. Join all lines with "\n"
#     4. Prepend a header: f"UCC Filings Index ({len(ALL_FILINGS)} total):\n\n"
#
#   Don't forget a docstring -- it becomes the resource description!
# --------------------------------------------------------------------------
pass


# --------------------------------------------------------------------------
# TODO 2: Register a resource template at URI "ucc://filing/{filing_number}"
#
#   Use the @mcp.resource("ucc://filing/{filing_number}") decorator.
#   The function takes filing_number: str as a parameter.
#
#   Implementation:
#     1. Call get_filing_by_number(filing_number)
#     2. If None, return f"No filing found: {filing_number}"
#     3. Otherwise, return json.dumps(filing, indent=2, default=str)
#
#   This is a URI TEMPLATE -- the {filing_number} part is filled in by the client.
# --------------------------------------------------------------------------
pass


# --------------------------------------------------------------------------
# TODO 3: Register a resource at URI "ucc://stats"
#
#   Use the @mcp.resource("ucc://stats") decorator.
#   The function should return dataset statistics as a JSON string.
#
#   Implementation:
#     1. Call get_stats()
#     2. Return json.dumps(stats, indent=2)
# --------------------------------------------------------------------------
pass


# =============================================================================
# MAIN (complete -- do not modify)
# =============================================================================

if __name__ == "__main__":
    print("Starting UCC Filing MCP Server with Resources (stdio transport)...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    mcp.run()
