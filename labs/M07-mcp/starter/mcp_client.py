"""
M07 Lab - Step 3: MCP Client (Starter)
=======================================
Build an MCP client that connects to your server, discovers its
capabilities, calls tools, and reads resources.

KEY CONCEPT: The MCP client-server handshake:
  1. Client spawns the server as a subprocess (stdio transport)
  2. Client sends "initialize" -> server responds with capabilities
  3. Client sends "initialized" notification
  4. Client can now list tools, call tools, list resources, read resources

Usage (from the labs/ directory):
    python M07-mcp/starter/mcp_client.py
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# =============================================================================
# CONFIGURATION (complete -- do not modify)
# =============================================================================

# Path to the server script (Step 2 solution with both tools AND resources)
SERVER_SCRIPT = os.path.join(
    os.path.dirname(__file__), '..', 'solution', 'mcp_server_resources.py'
)

# StdioServerParameters tells the client HOW to launch the server
server_params = StdioServerParameters(
    command=sys.executable,  # Use the same Python interpreter
    args=[SERVER_SCRIPT],
)


# =============================================================================
# HELPER (complete -- do not modify)
# =============================================================================

def section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# =============================================================================
# YOUR CODE: Implement the client
# =============================================================================

async def run_client():
    """
    Connect to the MCP server, explore its capabilities, and run queries.
    """
    section("MCP Client — Connecting to UCC Filing Server")

    # ------------------------------------------------------------------
    # TODO 1: Connect to the server using stdio_client
    #
    #   Use the async context managers:
    #     async with stdio_client(server_params) as (read_stream, write_stream):
    #         async with ClientSession(read_stream, write_stream) as session:
    #             await session.initialize()
    #             ... your code here ...
    #
    #   The initialize() call performs the MCP handshake.
    # ------------------------------------------------------------------
    pass

    # Inside the context managers, implement the following steps:

    # ------------------------------------------------------------------
    # TODO 2: List available tools
    #
    #   result = await session.list_tools()
    #   Loop through result.tools and print each tool's name and description.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # TODO 3: List available resources
    #
    #   result = await session.list_resources()
    #   Loop through result.resources and print each resource's uri and name.
    #
    #   Also list resource templates:
    #   result = await session.list_resource_templates()
    #   Loop and print each template's uriTemplate and name.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # TODO 4: Call a tool
    #
    #   result = await session.call_tool(
    #       "search_ucc_filings",
    #       {"state": "Texas"}
    #   )
    #   Print result.content (it's a list of content blocks).
    #   Each block has a .text attribute with the tool's response.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # TODO 5: Read a resource
    #
    #   result = await session.read_resource("ucc://stats")
    #   Print result.contents (list of resource contents).
    #   Each item has a .text attribute.
    # ------------------------------------------------------------------

    section("Client session complete!")


# =============================================================================
# MAIN (complete -- do not modify)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M07 Lab - Step 3: MCP Client")
    print("=" * 60)
    asyncio.run(run_client())
