# M15B: Build a Complete Agent & Subagent System — From Zero to Running

**Track**: 4B — Applied Agent Building | **Position**: After M15, before M16
**Prerequisites**: M05 (Function Calling), M07 (MCP), M12 (ReAct), M14 (Multi-Agent)
**Estimated Time**: 2-3 hours (this is a BUILD module, not a concept module)
**Level**: Intermediate → Advanced
**Track Color**: var(--track-architecture) / #F97316
**SDK Tier**: 3 (SDK-default + spec-driven). See `prompts/19-sdk-tier-policy.md`. The primary `solution/` uses `claude-agent-sdk` with `query`, `@tool`, `create_sdk_mcp_server`, and `ClaudeAgentOptions`. Subagents are declared as `.claude/agents/<name>.md` files. The lab is **spec-driven**: the student writes `spec/agent-spec.md`, runs `claude` with `/generate-from-spec`, and verifies the result. The hand-rolled `while` loop lives in `appendix/manual-loop.py` for understanding, not as the deliverable.

## Why This Module Must Exist
By M15, the student has learned tools (M05), MCP (M07), agentic loops (M12), planning (M13), multi-agent (M14), and code execution (M15). But they've never built a COMPLETE agent from scratch in one sitting. Each module built a piece — this module assembles ALL the pieces into a working system.

This is NOT a lecture module. It's 80% hands-on lab, 20% architecture explanation. The student walks out with a running multi-agent system on their laptop.

## What the Student Builds
A **UCC Filing Research System** with:
- A **coordinator agent** that receives user questions and delegates to specialists
- A **filing search subagent** that searches UCC filings by debtor name across states
- A **risk analysis subagent** that calculates lien exposure and risk scores
- **3 tools**: search_filings, get_filing_details, calculate_risk_score (all using mock data)
- A **conversation loop** that handles multi-turn interactions
- **Error handling** throughout — tools fail gracefully, subagents report partial results

By the end, the student types "What's the lien exposure for Acme Corporation?" and gets a complete answer assembled from multiple subagent calls.

## Module Structure

### Section 1: Architecture Overview (15 min — concept)
- Animated diagram showing the system they're about to build:
  - User → Coordinator Agent → [Filing Search Subagent, Risk Analysis Subagent] → Tools → Mock Data → Response
- Explain the three architectural decisions they'll make:
  1. Single agent with many tools vs coordinator + subagents (and why coordinator wins here)
  2. How the coordinator passes context to subagents (explicit, not inherited)
  3. How results flow back and get synthesized
- This is the "show the blueprint before building the house" section from M00

### Section 2: Build the Tools (30 min — lab)

**Step 1: Create the project structure**
```
ucc-agent/
├── tools.py           # Tool definitions with mock data
├── agent.py           # Single ReAct agent
├── coordinator.py     # Coordinator + subagent system
├── mock_data.py       # Realistic UCC filing mock data
├── requirements.txt   # Dependencies
└── test_agent.py      # Test scenarios
```
- Complete environment setup block
- Mock data file with 15 realistic UCC filings across NY, CA, TX, FL, IL

**Step 2: Build mock_data.py**
- 15 filings with realistic debtor names, secured parties, collateral descriptions, filing dates, lapse dates, state codes
- A function to search by debtor name (fuzzy matching)
- A function to calculate risk score based on filing count, collateral types, lapse dates

**Step 3: Build tools.py — Three tool definitions**
- `search_filings(debtor_name, state=None)` — searches mock data, returns matching filings
- `get_filing_details(filing_number)` — returns full details for one filing
- `calculate_risk_score(entity_id)` — returns risk profile with score, factors, recommendation
- Each tool has: complete JSON Schema definition, error handling, structured response format
- Checkpoint: run each tool standalone and verify output

### Section 3: Build a Single Agent (30 min — lab)

**Step 4: Build agent.py — Using claude-agent-sdk**
- Use `claude-agent-sdk`'s `query()` and `ClaudeAgentOptions` as the primary path
- Tools are declared with `@tool` and exposed via `create_sdk_mcp_server`
- The SDK manages stop_reason, message appending, and the agentic loop
- Error handling: tool wrappers catch exceptions and return `{"isError": True, "content": [...]}`
- A 30-line **`appendix/manual-loop.py`** is included to show what the SDK abstracts away — students read it once, do not maintain it

**Step 5: Test the single agent**
- Run: `python agent.py "Find all UCC filings for Acme Corporation in New York"`
- Expected output: agent calls search_filings → gets results → formats response
- Run: `python agent.py "What's the risk level for Acme Corporation?"`
- Expected output: agent calls search_filings → then calculate_risk_score → synthesizes
- Multi-turn: ask follow-up "What about their filings in Texas?"
- Checkpoint: all three queries produce correct, sourced responses

### Section 4: Upgrade to Coordinator + Subagents (45 min — lab)

**Step 6: Understand why we need subagents**
- Conceptual bridge: "Your single agent works, but it has all 3 tools. As you add more tools (20+), tool selection accuracy degrades. Also, each tool call adds to the context window. Let's split into specialists."
- Architecture comparison animation: single agent (3 tools, growing context) vs coordinator + 2 subagents (each with 1-2 focused tools, isolated context)

**Step 7: Build the filing search subagent**
- Declared as `.claude/agents/filing-search.md` with frontmatter (`name`, `description`, `tools: [search_filings, get_filing_details]`) and a focused system prompt
- Coordinator delegates by invoking the subagent by name; the SDK gives it an isolated context window
- Returns structured result: {filings: [...], count: N, states_searched: [...]}

**Step 8: Build the risk analysis subagent**
- Declared as `.claude/agents/risk-analysis.md` with its own tools (calculate_risk_score, search_filings)
- Receives explicit context from the coordinator (NOT the full conversation)
- Returns: {risk_score: 0.73, risk_level: "HIGH", factors: [...], recommendation: "..."}

**Step 9: Build the coordinator**
- Receives user question
- Decides which subagent(s) to invoke (can be parallel)
- Passes EXPLICIT context to each subagent (not the full conversation)
- Aggregates results into a coherent response
- Handles subagent failures gracefully (partial results)

**Step 10: Test the complete system**
- Same queries as Step 5, but now routed through coordinator
- Verify: coordinator calls filing subagent → calls risk subagent → synthesizes
- Test error case: "Find filings for NonExistent Corp" → subagent returns empty → coordinator handles gracefully
- Checkpoint: system produces same quality answers as single agent, but with cleaner architecture

### Section 5: Add Conversation Memory (20 min — lab)

**Step 11: Add conversation history to the coordinator**
- Track previous questions and answers
- Handle follow-ups: "What about Texas?" understands context from previous turn
- Simple sliding window (last 5 turns)

### Section 5B: Spec-Driven Build (Bonus, 25 min — lab)

By now the student has assembled the system file by file. Now they replay the same build using the spec-driven workflow:

**Step 12: Write the spec**
- Open `spec/agent-spec.md` (template provided in `prompts/17-spec-driven-development.md`)
- Fill in tools, hooks, sessions, deployment, tests, mock data — all already understood from Steps 1–11

**Step 13: Generate from spec**
- Run `claude` and use `/generate-from-spec spec/agent-spec.md`
- Claude Code reads the spec and regenerates the entire project into `generated/`
- Compare `generated/` to the hand-built `solution/` — they should be functionally equivalent

**Step 14: Iterate at the spec level**
- Add a new tool (`check_lapse_dates`) to the spec
- Re-run `/generate-from-spec` — Claude Code makes targeted edits, not a full rewrite
- Run tests, see the new tool work

This section is the student's first taste of the pattern that powers the cert-track modules and capstones.

### Section 6: Architecture Reflection (10 min — concept)
- What we built vs production architecture (animated comparison)
- What's missing: guardrails (M16-M17), observability (M19-M20), deployment (M21)
- "You now have a working multi-agent system on your laptop. You also know two ways to build one: file-by-file using `claude-agent-sdk`, and spec-driven via `/generate-from-spec`. The next modules add the production layers."

## Quiz Focus (5 questions)
1. Why split from single agent to coordinator + subagents? (tool count, context isolation)
2. How does the coordinator pass context to subagents? (explicitly, not inherited)
3. What happens when a subagent fails? (return structured error, coordinator handles gracefully)
4. What does stop_reason 'tool_use' mean? (continue the loop)
5. The coordinator has 15 subagents. What's wrong? (too many — same problem as too many tools)
