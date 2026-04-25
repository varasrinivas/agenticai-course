/**
 * M07 Lab - Step 2: MCP Server with Resources (Starter)
 * ======================================================
 * Extend your MCP server to expose UCC filing DATA as resources.
 *
 * KEY CONCEPT: Tools are for ACTIONS. Resources are for DATA.
 *   - Tool:     "Search filings by state"  (takes input, returns results)
 *   - Resource: "ucc://filings"            (read-only data, like a GET endpoint)
 *
 * Resources have URIs (like URLs). Clients can:
 *   1. List available resources
 *   2. Read a resource by its URI
 *   3. Use URI templates for parameterized resources
 *
 * Usage (from the labs/ directory):
 *     node M07-mcp/starter/mcp_server_resources.js
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  searchFilings,
  getFilingByNumber,
  ALL_FILINGS,
  getStats,
} from "../../shared/mock_ucc_data.js";

// =============================================================================
// SERVER SETUP (complete -- do not modify)
// =============================================================================

const server = new McpServer({
  name: "UCC Filing Server",
  version: "1.0.0",
});

// =============================================================================
// HELPER (complete -- do not modify)
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
// TOOLS (complete -- carried over from Step 1)
// =============================================================================

server.tool(
  "search_ucc_filings",
  "Search UCC filings by debtor name, state, or status.",
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
  "Retrieve a specific UCC filing by its filing number.",
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
// YOUR CODE: Register resources with server.resource()
// =============================================================================

// --------------------------------------------------------------------------
// TODO 1: Register a static resource at URI "ucc://filings"
//
//   Use server.resource(name, uri, handler).
//   The name is "filings_index" and the URI is "ucc://filings".
//
//   Handler must return:
//     { contents: [{ uri: "ucc://filings", text: "..." }] }
//
//   Implementation:
//     1. Loop through ALL_FILINGS
//     2. For each filing, create a one-line summary:
//        `${filing.filing_number} | ${filing.debtor.name || "(missing)"} | ${filing.state} | ${filing.status}`
//     3. Join all lines with "\n"
//     4. Prepend a header: `UCC Filings Index (${ALL_FILINGS.length} total):\n\n`
// --------------------------------------------------------------------------
// YOUR CODE HERE


// --------------------------------------------------------------------------
// TODO 2: Register a resource template at URI "ucc://filing/{filing_number}"
//
//   Use server.resource(name, template, handler).
//   The name is "filing_detail".
//   The template is: new ResourceTemplate("ucc://filing/{filing_number}", { list: undefined })
//
//   Handler receives (uri, { filing_number }) and must return:
//     { contents: [{ uri: uri.href, text: "..." }] }
//
//   Implementation:
//     1. Call getFilingByNumber(filing_number)
//     2. If null, return text `No filing found: ${filing_number}`
//     3. Otherwise, return JSON.stringify(filing, null, 2)
// --------------------------------------------------------------------------
// YOUR CODE HERE


// --------------------------------------------------------------------------
// TODO 3: Register a static resource at URI "ucc://stats"
//
//   Use server.resource(name, uri, handler).
//   The name is "dataset_stats" and the URI is "ucc://stats".
//
//   Handler must return:
//     { contents: [{ uri: "ucc://stats", text: "..." }] }
//
//   Implementation:
//     1. Call getStats()
//     2. Return JSON.stringify(stats, null, 2)
// --------------------------------------------------------------------------
// YOUR CODE HERE


// =============================================================================
// MAIN (complete -- do not modify)
// =============================================================================

async function main() {
  console.error("Starting UCC Filing MCP Server with Resources (stdio transport)...");
  console.error("Press Ctrl+C to stop.");
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
