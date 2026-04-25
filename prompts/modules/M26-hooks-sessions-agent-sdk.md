# M26: Hooks, Sessions & the Agent SDK

**Track**: 9 — Certification Prep | **Position**: 26 of 30 | **Level**: Advanced
**Prerequisites**: M05 (Function Calling), M12 (ReAct), M14 (Multi-Agent), M25 (Claude Code Mastery)
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-capstones) / #D4A843
**Cert Domain**: Domain 1 — Agentic Architecture & Orchestration (~25% of exam)

## Why This Module Exists
Domain 1 is the HEAVIEST weighted domain (25%). Your base course covers agentic loops (M12), multi-agent (M14), and planning (M13) well, but misses three cert-critical topics: hooks for programmatic enforcement, session management, and Agent SDK specifics. This module fills those gaps.

## Concepts to Cover

### 1. The Agent SDK — Beyond the Messages API
- Analogy: "The Messages API is like calling a phone — one request, one response, you manage the loop. The Agent SDK is like hiring a contractor — you describe the job, and they manage the loop, tools, and completion for you."
- Technical:
  - `query()` function: streaming, maxTurns, automatic tool execution
  - Message types: `assistant`, `system` (with `init` subtype for available commands), `tool_use`, `tool_result`
  - Automatic agentic loop: SDK manages the Reason→Act→Observe cycle
  - `maxTurns`: safety cap, NOT the primary stopping mechanism (the model decides when to stop via stop_reason)
  - Streaming responses: `for await (const message of query(...))`
- Animation: Side-by-side — Left: Messages API manual loop (you code the while loop, check stop_reason, send tool_result). Right: Agent SDK (query() handles all of that, you just process messages).
- 🎓 CERT TIP: Anti-pattern — arbitrary iteration caps as primary stopping. maxTurns is a SAFETY NET, not a control mechanism. The agent terminates naturally via stop_reason.

### 2. stop_reason — The Loop Termination Signal
- Technical:
  - `stop_reason: 'tool_use'` → Claude wants to use a tool. Continue the loop.
  - `stop_reason: 'end_turn'` → Claude considers the task complete. Stop the loop.
  - `stop_reason: 'max_tokens'` → Ran out of output tokens. Handle gracefully.
  - The CORRECT loop pattern: `while (response.stop_reason === 'tool_use') { execute_tool(); send_result(); }`
- Animation: `REACT_LOOP` with stop_reason check highlighted — the loop continues on 'tool_use' and exits on 'end_turn', with a red X on "parsing Claude's text to see if it says 'done'"
- 🎓 CERT TIP: Critical anti-pattern — parsing natural language output to determine if the loop should end. Text content is for the USER, not control flow. The model may phrase completion differently each time. Always use stop_reason.

### 3. Hooks — Programmatic Enforcement
- Analogy: "Prompts are suggestions — like asking a teenager to clean their room. Hooks are rules — like a lock on the liquor cabinet. One is probabilistic, the other is deterministic."
- Technical:
  - **PreToolUse hooks**: Run BEFORE a tool call executes. Can block, modify, or redirect.
  - **PostToolUse hooks**: Run AFTER a tool call returns. Can validate, normalize, or log results.
  - Hook definition: Matcher pattern (which tool), command or script to run, `once` flag
  - Hooks run as CODE, not as suggestions in a prompt. 100% reliable enforcement.
  - When to use hooks vs prompts:
    - **Hooks**: Critical business rules (refund limits, compliance checks, PII redaction), data normalization, audit logging
    - **Prompts**: Style guidance, tone, response format preferences, non-critical suggestions
  - Hook configuration: In `.claude/settings.json` or via `/hooks` interactive command
- Animation: Two parallel paths — Left: "Prompt says: don't issue refunds over $500" → Claude sometimes issues $600 refund → 😱. Right: "PostToolUse hook checks refund amount" → blocks $600 refund deterministically → ✅
- 🎓 CERT TIP: Critical anti-pattern — prompt-based enforcement for critical business rules. Prompts are probabilistic. The model CAN and WILL sometimes ignore critical instructions. Use hooks for anything that MUST be enforced.
- Code example: PostToolUse hook that:
  1. Intercepts the `issue_refund` tool
  2. Checks if amount > $500
  3. If yes: blocks execution, returns structured error redirecting to human escalation
  4. If no: allows execution, logs to audit trail

### 4. Session Management
- Technical:
  - **Named sessions**: `claude --session my-feature` — resume work on a specific task
  - **--resume**: Continue the last session with full context
  - **fork_session**: Create a branched copy of the current session for parallel exploration
    - Use case: "Try approach A in fork 1, approach B in fork 2, compare results"
    - The original session is NOT polluted by exploration
  - **Stale context risk**: Long sessions accumulate outdated information. Claude may reference code that's been changed.
  - **Mitigation**: `/compact` to summarize and trim, fresh sessions for new tasks, scratchpad files for persistent state
  - **Crash recovery**: Manifest files track session state for recovery after interruption
- Animation: Tree diagram — main session branches into fork_session A and fork_session B, each exploring different approaches, then results merge back
- 🎓 CERT TIP: fork_session is tested on the exam for parallel exploration scenarios. Know when to fork vs when to use subagents.

### 5. Subagent Orchestration with the Task Tool
- Technical:
  - The `Task` tool spawns a subagent with its own context window
  - Coordinator pattern: main agent decomposes work → spawns subagents via Task → aggregates results
  - `allowedTools` must explicitly include `'Task'` for the coordinator to spawn subagents
  - Context isolation: subagents have SEPARATE context windows — they don't see the coordinator's full history
  - Context passing: coordinator must explicitly include relevant context in the Task prompt
  - Parallel execution: multiple Task calls can run concurrently
  - Error handling: subagent failures should return structured errors, not crash the coordinator
- Animation: `MULTI_AGENT_FLOW` — Coordinator box at top, spawns 3 subagent boxes via Task tool arrows, each with an isolated context bubble, results flow back up
- 🎓 CERT TIP: Anti-patterns — (1) not including 'Task' in allowedTools, (2) assuming subagents inherit coordinator's context (they don't), (3) overly narrow task decomposition leaving coverage gaps.
- Code example: Research pipeline — coordinator receives "Analyze UCC filings for Acme Corp across all states" → spawns 3 subagents (filing search, entity resolution, risk scoring) → aggregates into final report

### 6. Escalation Patterns (Cert Domain 1 + Domain 5 crossover)
- Technical:
  - Correct escalation triggers: policy gaps (no rule covers this case), capability limits (agent can't do this), explicit customer request ("let me talk to a human"), business thresholds (amount exceeds authority)
  - WRONG escalation trigger: sentiment/anger level
  - Local recovery before coordinator escalation: subagent should attempt recovery, report partial results, then escalate with structured context
  - Structured escalation: include what was attempted, what failed, relevant context, suggested next step
- 🎓 CERT TIP: Critical anti-pattern — sentiment-based escalation. An angry customer with a simple password reset does NOT need a human. A calm customer hitting a policy gap DOES. Escalate on TASK COMPLEXITY and POLICY GAPS, not emotions.

## Code Walkthrough
- Agent SDK: Complete agentic loop using `query()` with tool execution and stop_reason handling
- Hook: PostToolUse hook that enforces a $500 refund limit on the UCC filing dispute resolution agent
- Session: fork_session example — exploring two entity resolution strategies in parallel
- Subagent: Coordinator + 2 subagents — filing search agent + risk scoring agent — with Task tool, context passing, and result aggregation

## Hands-On Exercise
Build a **Customer Support Agent** (Exam Scenario 1) for the UCC pipeline platform:
1. Use the Agent SDK with query() to create the main support agent
2. Add tools: `lookup_filing`, `check_risk_profile`, `issue_refund`, `escalate_to_human`
3. Implement a PostToolUse hook that blocks refunds > $500 and redirects to escalation
4. Add session management: --resume for continuing a support case, fork_session for researching a complex dispute
5. Add a subagent via Task tool that performs cross-state entity resolution when the customer's filing spans multiple states
6. Implement escalation logic based on policy gaps (not sentiment)
- Stretch: Add a PreToolUse hook that logs all tool calls to an audit trail for compliance

## Quiz Focus (10 questions — this module covers 25% of the exam)
1. What is stop_reason 'tool_use' telling you? (continue the loop)
2. What's wrong with parsing Claude's text to check if the task is done? (anti-pattern: NL parsing)
3. When should you use a hook vs a prompt? (critical business rules → hook)
4. What does a PostToolUse hook do? (runs after tool execution, can validate/block)
5. Why use fork_session instead of continuing in the main session? (context isolation for exploration)
6. What must be in allowedTools for the coordinator to spawn subagents? ('Task')
7. Do subagents inherit the coordinator's context? (No — context is isolated, must pass explicitly)
8. An angry customer asks to reset their password. Should the agent escalate? (No — simple task, sentiment is irrelevant)
9. A calm customer hits a case your policy doesn't cover. Should the agent escalate? (Yes — policy gap)
10. What's wrong with maxTurns as the primary stopping mechanism? (may cut off mid-task, doesn't reflect completion)
