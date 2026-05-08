# Agent Framework Comparison

Add this section to M24 (What's Next) so students know the landscape and can make informed decisions about frameworks.

## Section: Agent Frameworks — Do You Need One?

### What This Course Taught You (native approach)
- Raw API: client.messages.create() in a while loop — full control
- Agent SDK: @agent.tool + hooks + sessions — Anthropic's native framework
- Spec-driven: write a spec, Claude Code generates from it

### The Framework Landscape

| Framework | What It Does | Pros | Cons |
|---|---|---|---|
| **Anthropic Agent SDK** | Native Claude agent framework with tools, hooks, sessions | Designed for Claude, maintained by Anthropic, tight integration | Claude-only, newer ecosystem |
| **LangChain** | General-purpose LLM framework with chains, agents, tools | Huge ecosystem, many integrations, lots of examples | Heavy abstraction, frequent breaking changes, vendor-agnostic means optimized for none |
| **LangGraph** | State machine framework for multi-agent workflows | Visual graph editor, explicit state management, good for complex flows | Steep learning curve, tied to LangChain ecosystem |
| **CrewAI** | Multi-agent role-based framework | Easy to define agent "roles", good for team-of-agents patterns | Less flexibility for custom patterns, abstraction hides the loop |
| **AutoGen** | Microsoft's multi-agent conversation framework | Good for agent-to-agent conversations, research-oriented | Complex setup, Microsoft-centric, less production-focused |
| **Haystack** | NLP/RAG-focused pipeline framework | Excellent for RAG pipelines, modular components | Less focused on agents, more on retrieval |
| **No framework (raw SDK)** | Just the Anthropic Python/Node SDK | Maximum control, minimum dependencies, easiest to debug | More code to write, no built-in patterns |

### When to Use What

**Use Anthropic Agent SDK (what this course teaches) when:**
- Building Claude-specific agents
- You want hooks for guardrails and sessions for persistence
- You need production-ready patterns without heavy dependencies
- Your team is standardized on Claude

**Use LangChain/LangGraph when:**
- You need to support multiple LLM providers (Claude + GPT + Gemini)
- You want pre-built integrations (hundreds of tool connectors)
- Your team already uses LangChain

**Use raw SDK (no framework) when:**
- Learning how agents work (this course's approach)
- Building simple single-purpose agents
- You need maximum control over every API call
- Debugging production issues where frameworks hide the problem

**Use CrewAI when:**
- Your use case maps cleanly to "team of specialists" pattern
- You want fast prototyping of multi-agent systems

### The Course's Position

"This course deliberately teaches you without frameworks first (raw SDK in M05-M15B), then with Anthropic's native framework (Agent SDK in M26), then with spec-driven generation (M25). 

If your team uses LangChain, everything you learned transfers — ReAct is ReAct whether you implement it with a while loop or LangChain's AgentExecutor. The patterns are the same. Only the syntax changes.

The student who understands the raw loop can learn ANY framework in a day. The student who learned LangChain first often cannot debug without it."

### Try It Yourself (Optional Exercise)
For students who want to compare, rebuild the M15B agent using LangChain:

```
pip install langchain langchain-anthropic

# The same 3 tools, same mock data, same question
# But using LangChain's AgentExecutor instead of a raw while loop
# Compare: lines of code, output quality, debuggability, dependencies
```

This is NOT required — it's a "Going Further" exercise for students whose teams use LangChain.
