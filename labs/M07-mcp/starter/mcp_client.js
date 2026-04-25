/**
 * M07 Lab - Step 3: MCP Client (Starter)
 * =======================================
 * Build an MCP client that connects to your server, discovers its
 * capabilities, calls tools, and reads resources.
 *
 * KEY CONCEPT: The MCP client-server handshake:
 *   1. Client spawns the server as a subprocess (stdio transport)
 *   2. Client sends "initialize" -> server responds with capabilities
 *   3. Client sends "initialized" notification
 *   4. Client can now list tools, call tools, list resources, read resources
 *
 * Usage (from the labs/ directory):
 *     node M07-mcp/starter/mcp_client.js
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "path";
import { fileURLToPath } from "url";

// =============================================================================
// CONFIGURATION (complete -- do not modify)
// =============================================================================

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Path to the server script (Step 2 solution with both tools AND resources)
const SERVER_SCRIPT = path.join(__dirname, "..", "solution", "mcp_server_resources.js");

// =============================================================================
// HELPER (complete -- do not modify)
// =============================================================================

function section(title) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`  ${title}`);
  console.log(`${"=".repeat(60)}`);
}

// =============================================================================
// YOUR CODE: Implement the client
// =============================================================================

async function runClient() {
  section("MCP Client — Connecting to UCC Filing Server");

  // ------------------------------------------------------------------
  // TODO 1: Create a StdioClientTransport and Client, then connect
  //
  //   const transport = new StdioClientTransport({
  //     command: "node",
  //     args: [SERVER_SCRIPT],
  //   });
  //
  //   const client = new Client({
  //     name: "ucc-filing-client",
  //     version: "1.0.0",
  //   });
  //
  //   await client.connect(transport);
  //   console.log("Connected to server!");
  //
  //   The connect() call performs the MCP handshake (initialize/initialized).
  // ------------------------------------------------------------------
  // YOUR CODE HERE


  // ------------------------------------------------------------------
  // TODO 2: List available tools
  //
  //   const toolsResult = await client.listTools();
  //   Loop through toolsResult.tools and print each tool's name and description.
  // ------------------------------------------------------------------
  // YOUR CODE HERE


  // ------------------------------------------------------------------
  // TODO 3: List available resources
  //
  //   const resourcesResult = await client.listResources();
  //   Loop through resourcesResult.resources and print uri + name.
  //
  //   Also list resource templates:
  //   const templatesResult = await client.listResourceTemplates();
  //   Loop and print each template's uriTemplate and name.
  // ------------------------------------------------------------------
  // YOUR CODE HERE


  // ------------------------------------------------------------------
  // TODO 4: Call a tool
  //
  //   const result = await client.callTool({
  //     name: "search_ucc_filings",
  //     arguments: { state: "Texas" },
  //   });
  //   Print result.content -- it's an array of content blocks.
  //   Each block has a .text property with the tool's response.
  // ------------------------------------------------------------------
  // YOUR CODE HERE


  // ------------------------------------------------------------------
  // TODO 5: Read a resource
  //
  //   const resource = await client.readResource({ uri: "ucc://stats" });
  //   Print resource.contents -- array of resource contents.
  //   Each item has a .text property.
  // ------------------------------------------------------------------
  // YOUR CODE HERE


  // ------------------------------------------------------------------
  // TODO 6: Clean up
  //
  //   await client.close();
  //   console.log("Disconnected from server.");
  // ------------------------------------------------------------------
  // YOUR CODE HERE

  section("Client session complete!");
}

// =============================================================================
// MAIN (complete -- do not modify)
// =============================================================================

console.log("=".repeat(60));
console.log("M07 Lab - Step 3: MCP Client");
console.log("=".repeat(60));

runClient().catch((error) => {
  console.error("Client error:", error);
  process.exit(1);
});
