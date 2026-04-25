/**
 * M07 Lab - Step 1: Basic MCP Server with Tools (Solution)
 * =========================================================
 * A complete MCP server that exposes two UCC filing tools.
 *
 * Usage (from the labs/ directory):
 *     node M07-mcp/solution/mcp_server_basic.js
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

// =============================================================================
// SERVER SETUP
// =============================================================================

const server = new McpServer({
  name: "UCC Filing Server",
  version: "1.0.0",
});

// =============================================================================
// HELPER
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
// TOOLS
// =============================================================================

server.tool(
  "search_ucc_filings",
  "Search UCC filings by debtor name, state, or status. Supports partial name matching and case-insensitive filters.",
  {
    debtor_name: z.string().optional().describe("Search by debtor name (partial match)"),
    state: z.string().optional().describe("Filter by state, e.g. 'Texas'"),
    status: z.string().optional().describe("Filter by status: Active, Terminated, etc."),
  },
  async ({ debtor_name, state, status }) => {
    const results = searchFilings({ debtorName: debtor_name, state, status });
    if (results.length === 0) {
      return { content: [{ type: "text", text: "No filings found matching your criteria." }] };
    }
    const formatted = results.map(formatFiling).join("\n\n");
    return {
      content: [{ type: "text", text: `Found ${results.length} filing(s):\n\n${formatted}` }],
    };
  }
);

server.tool(
  "get_filing",
  "Retrieve a specific UCC filing by its filing number. Returns the full filing record as JSON.",
  {
    filing_number: z.string().describe("The UCC filing number, e.g. 'UCC-2024-NY-0012847'"),
  },
  async ({ filing_number }) => {
    const filing = getFilingByNumber(filing_number);
    if (!filing) {
      return { content: [{ type: "text", text: `No filing found with number: ${filing_number}` }] };
    }
    return { content: [{ type: "text", text: JSON.stringify(filing, null, 2) }] };
  }
);

// =============================================================================
// MAIN
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
