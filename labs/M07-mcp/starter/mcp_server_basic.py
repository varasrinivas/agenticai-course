"""
M07 Lab - Step 1: Basic MCP Server with Tools (Starter)
========================================================
Build your first MCP server! You'll register two tools that expose
UCC filing data, then run the server over stdio transport.

KEY CONCEPT: An MCP server exposes TOOLS (actions an AI can take) and
RESOURCES (data an AI can read). This step focuses on tools.

The FastMCP class gives you a decorator-based API:
    @mcp.tool()
    def my_tool(arg: str) -> str:
        ...

FastMCP handles all the JSON-RPC plumbing -- you just write Python functions.

Usage (from the labs/ directory):
    python M07-mcp/starter/mcp_server_basic.py
"""

import sys
import json
import os

# ---------------------------------------------------------------------------
# Import shared mock data
# We insert the parent (labs/) directory into sys.path so we can import
# from shared.mock_ucc_data regardless of where the script is run from.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.mock_ucc_data import search_filings, get_filing_by_number

from mcp.server.fastmcp import FastMCP

# =============================================================================
# SERVER SETUP (complete -- do not modify)
# =============================================================================

mcp = FastMCP("UCC Filing Server")


# =============================================================================
# HELPER: Format a filing as a readable string (complete -- do not modify)
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
# YOUR CODE: Register tools with @mcp.tool()
# =============================================================================

# --------------------------------------------------------------------------
# TODO 1: Register a tool called "search_ucc_filings"
#
#   Use the @mcp.tool() decorator.
#   Parameters:
#     - debtor_name: str = None   (search by debtor name, partial match)
#     - state: str = None         (filter by state, e.g. "Texas")
#     - status: str = None        (filter by status: Active, Terminated, etc.)
#   Returns: str
#
#   Implementation:
#     1. Call search_filings(debtor_name=debtor_name, state=state, status=status)
#     2. If no results, return "No filings found matching your criteria."
#     3. Otherwise, format each filing with format_filing() and join with "\n\n"
#     4. Prepend a count line: f"Found {len(results)} filing(s):\n\n"
#
#   Don't forget a docstring -- MCP uses it as the tool description!
# --------------------------------------------------------------------------
pass


# --------------------------------------------------------------------------
# TODO 2: Register a tool called "get_filing"
#
#   Use the @mcp.tool() decorator.
#   Parameters:
#     - filing_number: str   (e.g. "UCC-2024-NY-0012847")
#   Returns: str
#
#   Implementation:
#     1. Call get_filing_by_number(filing_number)
#     2. If None, return f"No filing found with number: {filing_number}"
#     3. Otherwise, return the full filing as formatted JSON (json.dumps with indent=2)
#
#   Don't forget a docstring!
# --------------------------------------------------------------------------
pass


# =============================================================================
# MAIN (complete -- do not modify)
# =============================================================================

if __name__ == "__main__":
    print("Starting UCC Filing MCP Server (stdio transport)...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    mcp.run()
