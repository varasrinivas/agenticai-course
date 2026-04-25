# M07: MCP — Model Context Protocol

**Track**: 2 — Tool Use | **Position**: 7 of 30 | **Level**: Intermediate
**Prerequisites**: M05, M06
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-tooluse) / #8B5CF6

## Concepts
- What is MCP? The "USB-C for AI" analogy (animated: before MCP = N×M, after = N+M)
- MCP architecture: Client ↔ Server ↔ Resources/Tools/Prompts
- JSON-RPC 2.0 over stdio or HTTP+SSE transports — why each, when each
- Visual: Animated protocol handshake sequence
- Building MCP servers (Python with FastMCP + Node.js with SDK)
- Resources vs Tools vs Prompts — when to expose each
- Connecting Claude Desktop / Claude Code to your MCP server

## Hands-On Lab
Build two MCP servers: (1) filesystem server that reads UCC document files, (2) database server that queries mock UCC filing data. Connect both to Claude Desktop.

## Quiz Focus (5 questions)
1. What problem does MCP solve? (N×M integration problem → N+M)
2. What protocol does MCP use? (JSON-RPC 2.0)
3. When use stdio vs HTTP+SSE transport? (stdio for local, HTTP for remote)
4. What's the difference between MCP Resources and Tools? (resources are data, tools are actions)
5. MCP servers run as ___? (subprocesses managed by the client)
