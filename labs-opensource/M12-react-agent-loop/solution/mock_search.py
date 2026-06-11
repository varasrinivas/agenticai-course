"""
M12 Lab - Step 1: Mock Search Tool (COMPLETE)
==============================================
Simulates web_search results for development.
Swap for httpx + a real search API in production — keep this for tests.
"""

MOCK_RESULTS = {
    "python ai frameworks 2025": """
Top Python AI/Agent Frameworks 2025:
1. LangChain — most ecosystem integrations, complex but powerful
2. LlamaIndex — best for RAG and document processing
3. CrewAI — multi-agent orchestration, growing fast
4. claude-agent-sdk — Anthropic's first-party SDK for Claude agents
5. AutoGen (Microsoft) — enterprise-focused, code execution focus

Trend: First-party SDKs (claude-agent-sdk, OpenAI Agents SDK) are gaining vs wrapper frameworks.
""",
    "claude agent sdk features": """
claude-agent-sdk v1.2 Features (May 2025):
- @tool decorator for typed async tool functions
- query() for single-agent invocation
- ClaudeAgentOptions: model, system_prompt, tools, max_turns, hooks
- Built-in: can_use_tool hook for fine-grained control
- create_sdk_mcp_server() for MCP server creation
- Native subagent support via .claude/agents/ directory
- Streaming support with async generators
""",
    "react pattern llm agents": """
ReAct (Reasoning + Acting) — Yao et al. 2022:
- Interleaves reasoning traces with tool calls
- Shows 10-40% improvement on knowledge-intensive benchmarks vs silent tool use
- Key principle: thought before action improves tool selection accuracy
- Adopted by: LangChain, LlamaIndex, AutoGen as default agent pattern
- Works with any LLM supporting tool use (Mistral, GPT-4, Gemini, Claude)
""",
}


def mock_search(query: str) -> str:
    """Return mock search results for the given query."""
    query_lower = query.lower()
    for key, result in MOCK_RESULTS.items():
        if any(word in query_lower for word in key.split()):
            return f"Search results for '{query}':\n{result}"
    return (
        f"Search results for '{query}':\nNo specific results found. General "
        f"information: {query} is an active research area in AI. Recent "
        "developments include improved tooling and better benchmark performance."
    )


if __name__ == "__main__":
    print(mock_search("claude agent sdk features")[:200])
