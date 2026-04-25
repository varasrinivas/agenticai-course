/**
 * M07 Lab - Step 3: MCP Client (Solution)
 * ========================================
 * MCP client that connects to the UCC Filing Server, lists capabilities,
 * calls tools, and reads resources.
 *
 * Usage (from the labs/ directory):
 *     node M07-mcp/solution/mcp_client.js
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "path";
import { fileURLToPath } from "url";

// =============================================================================
// CONFIGURATION
// =============================================================================

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SERVER_SCRIPT = path.join(__dirname, "mcp_server_resources.js");

// =============================================================================
// HELPER
// =============================================================================

function section(title) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`  ${title}`);
  console.log(`${"=".repeat(60)}`);
}

// =============================================================================
// CLIENT
// =============================================================================

async function runClient() {
  section("MCP Client -- Connecting to UCC Filing Server");

  // Connect to the server via stdio
  const transport = new StdioClientTransport({
    command: "node",
    args: [SERVER_SCRIPT],
  });

  const client = new Client({
    name: "ucc-filing-client",
    version: "1.0.0",
  });

  await client.connect(transport);
  console.log("Connected! Session initialized.\n");

  // ----------------------------------------------------------
  // List available tools
  // ----------------------------------------------------------
  section("Available Tools");
  const toolsResult = await client.listTools();
  for (const tool of toolsResult.tools) {
    console.log(`  - ${tool.name}: ${tool.description}`);
  }

  // ----------------------------------------------------------
  // List available resources
  // ----------------------------------------------------------
  section("Available Resources");
  const resourcesResult = await client.listResources();
  for (const resource of resourcesResult.resources) {
    console.log(`  - ${resource.uri}  (${resource.name})`);
  }

  section("Available Resource Templates");
  const templatesResult = await client.listResourceTemplates();
  for (const template of templatesResult.resourceTemplates) {
    console.log(`  - ${template.uriTemplate}  (${template.name})`);
  }

  // ----------------------------------------------------------
  // Call a tool: search by state
  // ----------------------------------------------------------
  section("Tool Call: search_ucc_filings(state='Texas')");
  const searchResult = await client.callTool({
    name: "search_ucc_filings",
    arguments: { state: "Texas" },
  });
  for (const block of searchResult.content) {
    console.log(block.text);
  }

  // ----------------------------------------------------------
  // Call a tool: get a specific filing
  // ----------------------------------------------------------
  section("Tool Call: get_filing('UCC-2024-CA-0098231')");
  const filingResult = await client.callTool({
    name: "get_filing",
    arguments: { filing_number: "UCC-2024-CA-0098231" },
  });
  for (const block of filingResult.content) {
    console.log(block.text);
  }

  // ----------------------------------------------------------
  // Call a tool: search with no results
  // ----------------------------------------------------------
  section("Tool Call: search_ucc_filings(debtor_name='Nonexistent Corp')");
  const noResult = await client.callTool({
    name: "search_ucc_filings",
    arguments: { debtor_name: "Nonexistent Corp" },
  });
  for (const block of noResult.content) {
    console.log(block.text);
  }

  // ----------------------------------------------------------
  // Read a resource: stats
  // ----------------------------------------------------------
  section("Resource Read: ucc://stats");
  const statsResource = await client.readResource({ uri: "ucc://stats" });
  for (const item of statsResource.contents) {
    console.log(item.text);
  }

  // ----------------------------------------------------------
  // Read a resource: filings index
  // ----------------------------------------------------------
  section("Resource Read: ucc://filings");
  const filingsResource = await client.readResource({ uri: "ucc://filings" });
  for (const item of filingsResource.contents) {
    console.log(item.text);
  }

  // ----------------------------------------------------------
  // Clean up
  // ----------------------------------------------------------
  await client.close();
  console.log("\nDisconnected from server.");

  section("Client session complete!");
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M07 Lab - Step 3: MCP Client");
console.log("=".repeat(60));

runClient().catch((error) => {
  console.error("Client error:", error);
  process.exit(1);
});
