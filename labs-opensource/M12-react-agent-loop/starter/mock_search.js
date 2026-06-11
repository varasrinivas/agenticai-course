/**
 * M12 Lab - Step 1: Mock Search Tool (COMPLETE)
 * ==============================================
 * Simulates web_search results for development.
 */

const MOCK_RESULTS = {
  "python ai frameworks 2025": `
Top Python AI/Agent Frameworks 2025:
1. LangChain — most ecosystem integrations, complex but powerful
2. LlamaIndex — best for RAG and document processing
3. CrewAI — multi-agent orchestration, growing fast
4. claude-agent-sdk — Anthropic's first-party SDK for Claude agents
5. AutoGen (Microsoft) — enterprise-focused, code execution focus

Trend: First-party SDKs are gaining vs wrapper frameworks.
`,
  "claude agent sdk features": `
claude-agent-sdk v1.2 Features (May 2025):
- @tool decorator for typed async tool functions
- query() for single-agent invocation
- ClaudeAgentOptions: model, system_prompt, tools, max_turns, hooks
- create_sdk_mcp_server() for MCP server creation
- Native subagent support via .claude/agents/ directory
`,
  "react pattern llm agents": `
ReAct (Reasoning + Acting) — Yao et al. 2022:
- Interleaves reasoning traces with tool calls
- 10-40% improvement on knowledge-intensive benchmarks vs silent tool use
- Thought before action improves tool selection accuracy
`,
};

export function mockSearch(query) {
  const queryLower = query.toLowerCase();
  for (const [key, result] of Object.entries(MOCK_RESULTS)) {
    if (key.split(" ").some((word) => queryLower.includes(word))) {
      return `Search results for '${query}':\n${result}`;
    }
  }
  return (
    `Search results for '${query}':\nNo specific results found. General ` +
    `information: ${query} is an active research area in AI.`
  );
}
