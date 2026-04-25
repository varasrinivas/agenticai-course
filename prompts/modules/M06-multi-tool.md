# M06: Multi-Tool Orchestration

**Track**: 2 — Tool Use | **Position**: 6 of 30 | **Level**: Intermediate
**Prerequisites**: M05
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-tooluse) / #8B5CF6

## Concepts
- Parallel tool calls — when Claude requests multiple tools at once
- Sequential tool chains — output of tool A feeds tool B
- Tool selection strategies: how Claude picks the right tool from many
- The degradation problem: tool selection accuracy drops above 5-8 tools
- Dynamic tool registration — adding/removing tools at runtime based on context
- Interactive: "What tool would YOU pick?" quiz matching Claude's reasoning
- Visual: Animated DAG showing tool execution order

## Hands-On Lab
Build a research assistant with 5 tools: web_search, fetch_page, summarize, save_note, generate_report. Test with UCC research queries that require chaining multiple tools.

## Quiz Focus (5 questions)
1. When does Claude use parallel vs sequential tool calls? (parallel when independent, sequential when dependent)
2. What happens with 20+ tools? (selection accuracy degrades)
3. How do you handle tool A's output feeding tool B? (send tool_result back, Claude decides next)
4. What is dynamic tool registration? (changing available tools based on conversation state)
5. How do you test multi-tool interactions? (scenario-based tests with expected tool sequences)
