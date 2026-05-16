# Agent Framework Comparison

For M24 (What's Next) — so students know the landscape.

| Framework | Pros | Cons |
| Anthropic Agent SDK | Designed for Claude, native, tight integration | Claude-only |
| LangChain | Huge ecosystem, many integrations | Heavy abstraction, breaking changes |
| LangGraph | Visual graph editor, explicit state | Steep learning curve, LangChain-tied |
| CrewAI | Easy role-based multi-agent | Less flexible, hides the loop |
| AutoGen | Good agent-to-agent conversations | Complex, Microsoft-centric |
| Haystack | Excellent RAG pipelines | Less agent-focused |
| Raw SDK (no framework) | Max control, min dependencies | More code to write |

When to use what:
- Agent SDK: Claude-specific, production, hooks/sessions needed
- LangChain: multi-provider support, pre-built integrations
- Raw SDK: learning, simple agents, max control
- CrewAI: team-of-specialists pattern

Course position: learn raw first (M15B), then SDK (M26), then spec-driven (M25). Student who understands the raw loop can learn ANY framework in a day.
