"""
M07 Lab - Step 3: MCP Client (Solution)
========================================
MCP client that connects to the UCC Filing Server, lists capabilities,
calls tools, and reads resources.

Usage (from the labs/ directory):
    python M07-mcp/solution/mcp_client.py
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_SCRIPT = os.path.join(
    os.path.dirname(__file__), 'mcp_server_resources.py'
)

server_params = StdioServerParameters(
    command=sys.executable,
    args=[SERVER_SCRIPT],
)


# =============================================================================
# HELPER
# =============================================================================

def section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# =============================================================================
# CLIENT
# =============================================================================

async def run_client():
    """Connect to the MCP server, explore its capabilities, and run queries."""
    section("MCP Client -- Connecting to UCC Filing Server")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # ----------------------------------------------------------
            # Handshake: initialize the session
            # ----------------------------------------------------------
            await session.initialize()
            print("Connected! Session initialized.\n")

            # ----------------------------------------------------------
            # List available tools
            # ----------------------------------------------------------
            section("Available Tools")
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # ----------------------------------------------------------
            # List available resources
            # ----------------------------------------------------------
            section("Available Resources")
            resources_result = await session.list_resources()
            for resource in resources_result.resources:
                print(f"  - {resource.uri}  ({resource.name})")

            section("Available Resource Templates")
            templates_result = await session.list_resource_templates()
            for template in templates_result.resourceTemplates:
                print(f"  - {template.uriTemplate}  ({template.name})")

            # ----------------------------------------------------------
            # Call a tool: search by state
            # ----------------------------------------------------------
            section("Tool Call: search_ucc_filings(state='Texas')")
            result = await session.call_tool(
                "search_ucc_filings",
                {"state": "Texas"}
            )
            for block in result.content:
                print(block.text)

            # ----------------------------------------------------------
            # Call a tool: get a specific filing
            # ----------------------------------------------------------
            section("Tool Call: get_filing('UCC-2024-CA-0098231')")
            result = await session.call_tool(
                "get_filing",
                {"filing_number": "UCC-2024-CA-0098231"}
            )
            for block in result.content:
                print(block.text)

            # ----------------------------------------------------------
            # Call a tool: search with no results
            # ----------------------------------------------------------
            section("Tool Call: search_ucc_filings(debtor_name='Nonexistent Corp')")
            result = await session.call_tool(
                "search_ucc_filings",
                {"debtor_name": "Nonexistent Corp"}
            )
            for block in result.content:
                print(block.text)

            # ----------------------------------------------------------
            # Read a resource: stats
            # ----------------------------------------------------------
            section("Resource Read: ucc://stats")
            result = await session.read_resource("ucc://stats")
            for item in result.contents:
                print(item.text)

            # ----------------------------------------------------------
            # Read a resource: filings index
            # ----------------------------------------------------------
            section("Resource Read: ucc://filings")
            result = await session.read_resource("ucc://filings")
            for item in result.contents:
                print(item.text)

    section("Client session complete!")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M07 Lab - Step 3: MCP Client")
    print("=" * 60)
    asyncio.run(run_client())
