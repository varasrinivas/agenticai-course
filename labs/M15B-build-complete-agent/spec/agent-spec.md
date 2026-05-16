# Agent Specification — UCC Filing Research System

> This is the **canonical agent-spec.md** for M15B. The lab's spec-driven section asks the student to read this spec, run `/generate-from-spec`, and verify the result matches the hand-built `solution/`.

## Overview
A multi-agent system that helps credit analysts assess lien exposure for business entities. The coordinator agent receives a natural-language question (e.g., *"What is the lien exposure for Acme Corporation?"*) and delegates to two specialist subagents: a **filing-search** subagent that searches UCC filings across states, and a **risk-analysis** subagent that calculates a risk profile from those filings. The coordinator synthesizes their results into a narrative answer with citations.

## Agent Configuration
- Model: `claude-sonnet-4-6`
- Framework: `claude-agent-sdk` (Python). Required imports: `query`, `tool`, `create_sdk_mcp_server`, `ClaudeAgentOptions`, `AssistantMessage`, `HookMatcher`.
- Max turns per invocation: 8
- Max output tokens: 4096
- Subagent context windows: isolated (subagents do not see the coordinator's transcript)

## System Prompt (coordinator)
You are the coordinator for a UCC filing research system. For each user question:
1. Decide which specialist(s) you need: filing-search, risk-analysis, or both.
2. Delegate by invoking the specialist subagent with explicit, focused context.
3. Synthesize results into a single narrative response that cites filing numbers, states, and risk factors.
Never call tools directly — always go through a specialist subagent. If a specialist returns no results, surface that fact rather than hallucinating an answer.

## Tools (exposed via the `ucc_tools` MCP server)

### search_filings
- Description: Search UCC filings by debtor name with optional state filter. Supports partial matching.
- Parameters: `debtor_name` (string, optional), `state` (string, optional — full state name)
- Returns: list of filing summaries with `filing_number`, `debtor`, `secured_party`, `state`, `status`, `type`, `filing_date`, `collateral` (truncated)
- Mock data source: `mock_data.MOCK_FILINGS` (15 filings across NY, CA, TX, FL, IL)

### get_filing_details
- Description: Get the full record for a specific filing by number.
- Parameters: `filing_number` (string, required)
- Returns: complete filing object including debtor, secured party, collateral, amendments

### calculate_risk_score
- Description: Compute a lien risk profile for a debtor across all their filings.
- Parameters: `debtor_name` (string, required)
- Returns: `{debtor, risk_score (0–1), risk_level (LOW|MEDIUM|HIGH), total_filings, active_filings, blanket_liens, amendments, states, secured_parties, factors[], recommendation}`

## Subagents (declared as `.claude/agents/<name>.md`)

### filing-search
- Description: Searches UCC filings by debtor name across states; returns structured filing lists.
- Allowed tools: `search_filings`, `get_filing_details`
- Model: `claude-haiku-4-5-20251001` (fast specialist)

### risk-analysis
- Description: Calculates lien exposure and risk scores given a debtor name.
- Allowed tools: `calculate_risk_score`, `search_filings`
- Model: `claude-haiku-4-5-20251001`

## Hooks

### PreToolUse — log every tool call
- Matcher: `*`
- Behavior: Print `[ISO timestamp] PRE  tool_name(params)` to stderr.

### PreToolUse — block overly broad queries
- Matcher: `mcp__ucc__search_filings`
- Behavior: Reject calls where `debtor_name` is shorter than 3 characters with message `"Query too broad — minimum 3 characters"`. Implemented via `can_use_tool` returning `PermissionResultDeny`.

### PostToolUse — audit log
- Matcher: `*`
- Behavior: Append `{timestamp, tool_name, tool_input, output_summary}` to `audit_log.jsonl`.

## Sessions
- Multi-turn supported via a `SessionManager` helper that maintains the running transcript and re-passes it to `query()` on each `send()` call.
- `SessionManager.fork()` returns a deep-copied session for what-if analysis.
- No external persistence — sessions live in memory only for this lab.

## Tests (pytest, in `tests/`)
- `test_tools.py` — each `@tool` returns valid `{"content": [{"type": "text", ...}]}` shape for known inputs
- `test_agent.py` — full-flow test: coordinator answers "What is the lien exposure for Acme Corporation?" with all 9 Acme filings cited
- `test_subagents.py` — filing-search returns filings; risk-analysis returns a score
- `test_hooks.py` — `PreToolUse` blocks short queries; `PostToolUse` writes to audit_log.jsonl
- `test_sessions.py` — follow-up "What about their Texas filings?" maintains context across 3 turns; `fork()` produces an independent branch

## Evaluation Dataset (`test_scenarios.json`)
1. "What is the lien exposure for Acme Corporation?" → finds all 9 Acme filings, HIGH risk
2. "Find filings for ACME CORP in California" → 2 CA filings
3. "What is the risk level for Pinnacle Industries?" → MEDIUM
4. "Compare Acme and Pinnacle risk profiles" → both, side by side
5. "Find all filings in New York" → 4 NY filings
6. "Are there any filings about to lapse?" → identifies imminent lapses
7. "Who is the secured party for the Florida filing?" → detail lookup
8. "Find filings for a company that does not exist" → graceful empty result
9. "Summarize all filings across all states" → broad synthesis
10. "What's the risk if Acme files a continuation on the CA filing?" → what-if (uses `fork()`)

## File Structure
```
generated/
├── CLAUDE.md
├── .claude/
│   ├── agents/
│   │   ├── filing-search.md
│   │   └── risk-analysis.md
│   ├── commands/
│   │   ├── run-agent.md
│   │   ├── test-agent.md
│   │   └── eval-agent.md
│   └── settings.json
├── coordinator.py
├── tools.py
├── mock_data.py
├── session_manager.py
├── hooks.py
├── audit_log.jsonl   (created at runtime)
├── requirements.txt
├── tests/
│   ├── test_tools.py
│   ├── test_agent.py
│   ├── test_subagents.py
│   ├── test_hooks.py
│   └── test_sessions.py
└── test_scenarios.json
```

## Acceptance Criteria
- All Python files import from `claude_agent_sdk` only — no `client.messages.create()` calls
- `python coordinator.py "What is the lien exposure for Acme Corporation?"` produces a narrative answer citing 9 filings
- `pytest tests/` passes 100%
- `python eval.py` runs all 10 scenarios with ≥9 passing
- Asking "find filings for AB" hits the `can_use_tool` deny path and returns an explanatory message instead of executing the tool
