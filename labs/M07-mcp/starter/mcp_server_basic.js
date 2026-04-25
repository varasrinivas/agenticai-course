/**
 * M07 Lab - Step 1: Basic MCP Server with Tools (Starter)
 * ========================================================
 * Build your first MCP server! You'll register two tools that expose
 * UCC filing data, then run the server over stdio transport.
 *
 * KEY CONCEPT: An MCP server exposes TOOLS (actions an AI can take) and
 * RESOURCES (data an AI can read). This step focuses on tools.
 *
 * The McpServer class gives you a method-based API:
 *     server.tool("my_tool", { schema }, async (args) => { ... })
 *
 * McpServer handles all the JSON-RPC plumbing -- you just write handler functions.
 *
 * Usage (from the labs/ directory):
 *     node M07-mcp/starter/mcp_server_basic.js
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

// =============================================================================
// SERVER SETUP (complete -- do not modify)
// =============================================================================

const server = new McpServer({
  name: "UCC Filing Server",
  version: "1.0.0",
});

// =============================================================================
// HELPER: Format a filing as a readable string (complete -- do not modify)
// =============================================================================

function formatFiling(filing) {
  return [
    `Filing: ${filing.filing_number}`,
    `  Type:           ${filing.type}`,
    `  State:          ${filing.state}`,
    `  Status:         ${filing.status}`,
    `  Filed:          ${filing.filing_date}`,
    `  Expires:        ${filing.expiration_date ?? "N/A"}`,
    `  Debtor:         ${filing.debtor.name || "(missing)"}`,
    `  Secured Party:  ${filing.secured_party.name}`,
    `  Collateral:     ${filing.collateral_description.slice(0, 80)}...`,
  ].join("\n");
}

// =============================================================================
// YOUR CODE: Register tools with server.tool()
// =============================================================================

// --------------------------------------------------------------------------
// TODO 1: Register a tool called "search_ucc_filings"
//
//   Use server.tool(name, schema, handler).
//
//   Schema (Zod):
//     {
//       debtor_name: z.string().optional().describe("Search by debtor name (partial match)"),
//       state: z.string().optional().describe("Filter by state, e.g. 'Texas'"),
//       status: z.string().optional().describe("Filter by status: Active, Terminated, etc."),
//     }
//
//   Handler receives { debtor_name, state, status } and must return:
//     { content: [{ type: "text", text: "..." }] }
//
//   Implementation:
//     1. Call searchFilings({ debtorName: debtor_name, state, status })
//     2. If no results, return text "No filings found matching your criteria."
//     3. Otherwise, format each filing with formatFiling() and join with "\n\n"
//     4. Prepend a count line: `Found ${results.length} filing(s):\n\n`
//
//   Don't forget a description string as the second argument!
// --------------------------------------------------------------------------
// YOUR CODE HERE


// --------------------------------------------------------------------------
// TODO 2: Register a tool called "get_filing"
//
//   Use server.tool(name, schema, handler).
//
//   Schema (Zod):
//     {
//       filing_number: z.string().describe("The UCC filing number, e.g. 'UCC-2024-NY-0012847'"),
//     }
//
//   Handler receives { filing_number } and must return:
//     { content: [{ type: "text", text: "..." }] }
//
//   Implementation:
//     1. Call getFilingByNumber(filing_number)
//     2. If null, return text `No filing found with number: ${filing_number}`
//     3. Otherwise, return JSON.stringify(filing, null, 2)
//
//   Don't forget a description string!
// --------------------------------------------------------------------------
// YOUR CODE HERE


// =============================================================================
// MAIN (complete -- do not modify)
// =============================================================================

async function main() {
  console.error("Starting UCC Filing MCP Server (stdio transport)...");
  console.error("Press Ctrl+C to stop.");
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
