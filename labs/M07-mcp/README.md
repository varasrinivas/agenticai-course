# M07 Lab: MCP -- Model Context Protocol

> **"USB-C for AI"** -- one protocol, every tool provider.
> Instead of building custom integrations for each AI host, you build ONE MCP server
> and every MCP-compatible client (Claude Desktop, Claude Code, Cursor, etc.) can use it.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Install dependencies:
  ```bash
  # Python
  pip install mcp

  # Node.js
  npm install @modelcontextprotocol/sdk zod
  ```
- Verify the shared mock data works:
  ```bash
  # From the labs/ directory
  python -c "from shared.mock_ucc_data import ALL_FILINGS; print(f'{len(ALL_FILINGS)} filings loaded')"
  # or
  node -e "import { ALL_FILINGS } from './shared/mock_ucc_data.js'; console.log(ALL_FILINGS.length + ' filings loaded')"
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `mcp_server_basic.py` / `mcp_server_basic.js` | Basic MCP server with 2 tools using FastMCP (Python) / MCP SDK (JS) | MCP server setup, tool registration, JSON-RPC |
| 2 | `mcp_server_resources.py` / `mcp_server_resources.js` | MCP server with resources + tools -- expose UCC docs as resources | Resources vs Tools, URI templates |
| 3 | `mcp_client.py` / `mcp_client.js` | MCP client that connects to a server over stdio | Client-server handshake, transport layer |

## Step 1: Basic MCP Server with Tools

**File:** `starter/mcp_server_basic.py` (or `.js`)

You will:
1. Create a FastMCP server instance named "UCC Filing Server"
2. Register a `search_ucc_filings` tool that accepts optional `debtor_name`, `state`, and `status` parameters
3. Register a `get_filing` tool that accepts a `filing_number` parameter
4. Each tool handler calls the corresponding function from `shared/mock_ucc_data`
5. Format results as human-readable strings

**Test it:**
```bash
# Python -- test in isolation (the server validates tool handlers on startup)
cd labs
python M07-mcp/starter/mcp_server_basic.py

# Node.js
node M07-mcp/starter/mcp_server_basic.js
```

The server will start and wait for JSON-RPC messages on stdin. Press Ctrl+C to exit.
You can also test it with the MCP client in Step 3.

## Step 2: MCP Server with Resources

**File:** `starter/mcp_server_resources.py` (or `.js`)

You will:
1. Start from your Step 1 server (tools are pre-included)
2. Add a `ucc://filings` resource -- returns a summary list of all filings
3. Add a `ucc://filing/{filing_number}` resource template -- returns full detail for one filing
4. Add a `ucc://stats` resource -- returns dataset statistics

**Key distinction:** Tools are for ACTIONS (search, compute, mutate). Resources are for DATA (read-only content the model can pull into context).

**Test it:**
```bash
cd labs
python M07-mcp/starter/mcp_server_resources.py
# or
node M07-mcp/starter/mcp_server_resources.js
```

## Step 3: MCP Client

**File:** `starter/mcp_client.py` (or `.js`)

You will:
1. Create an MCP client session that connects to the Step 2 server via stdio transport
2. List all available tools and print their names + descriptions
3. List all available resources and print their URIs
4. Call the `search_ucc_filings` tool with `state="Texas"`
5. Read the `ucc://stats` resource
6. Clean up and disconnect

**Test it:**
```bash
cd labs
python M07-mcp/starter/mcp_client.py
# or
node M07-mcp/starter/mcp_client.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
cd labs

# Python
python M07-mcp/solution/mcp_server_basic.py    # Starts server (Ctrl+C to stop)
python M07-mcp/solution/mcp_client.py           # Connects to solution server, runs queries

# Node.js
node M07-mcp/solution/mcp_server_basic.js       # Starts server (Ctrl+C to stop)
node M07-mcp/solution/mcp_client.js              # Connects to solution server, runs queries
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **MCP Server with Tools** -- registered tool handlers that expose UCC filing search and lookup via the Model Context Protocol
2. **MCP Resources** -- exposed read-only data (filing lists, individual filings, statistics) as addressable resources with URI templates
3. **MCP Client** -- connected to an MCP server over stdio, discovered its capabilities, called tools, and read resources
4. **The MCP Handshake** -- understood how client and server negotiate capabilities via the initialize/initialized flow

This is the foundation for connecting any data source to any AI host -- one protocol to rule them all.

## Next

- **M08**: Multi-Turn Conversation Management
- **M09**: RAG -- Retrieval-Augmented Generation
