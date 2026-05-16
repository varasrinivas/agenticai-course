# M12: The ReAct Pattern & Agent Design Patterns

**Track**: 4 — Agent Architectures | **Position**: 12 of 30 | **Level**: Intermediate
**Prerequisites**: M05, M06
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-architecture) / #F97316
**SDK Tier**: 2 (dual-track) — this is the **pivot module**. The lab ships `solution/` (the manual ReAct loop, ~50 lines, written by hand) AND `solution-sdk/` (the same flow via `claude-agent-sdk`'s `query()` in ~15 lines). The HTML must include a side-by-side comparison: "you just built this loop — here is the SDK doing the same thing." See `prompts/19-sdk-tier-policy.md`.

## Concepts

### Part A: Agent Design Patterns Overview (teach BEFORE ReAct)
This section gives students the COMPLETE landscape of agent patterns before diving deep into any single one. They need the map before the territory.

**The 8 Agent Design Patterns** (animated pattern catalog):

| Pattern | When to Use | Complexity | Example |
|---|---|---|---|
| 1. Single-Turn Tool Use | One question, one tool call, done | ★☆☆☆☆ | "Look up filing NY-2024-001" |
| 2. ReAct (Reason + Act) | Multi-step reasoning, dynamic tool selection | ★★☆☆☆ | "Find all filings for Acme across states" |
| 3. Plan-then-Execute | Known complex task, decompose first, then run steps | ★★★☆☆ | "Generate a full risk report for Acme Corp" |
| 4. Router / Classifier | Route to different handlers based on input type | ★★☆☆☆ | "Is this a lookup, research, or report request?" |
| 5. Parallel Fan-Out | Same task across many inputs simultaneously | ★★★☆☆ | "Validate 50 state files in parallel" |
| 6. Pipeline / Chain | Sequential specialist stages, output feeds next | ★★★☆☆ | "Parse → validate → transform → load" |
| 7. Supervisor + Workers | Coordinator delegates to specialist subagents | ★★★★☆ | "Coordinator assigns filing search, risk analysis, report writing to 3 specialists" |
| 8. Autonomous Loop with HITL | Agent runs autonomously but pauses for human approval at key decisions | ★★★★★ | "Process pre-auth: auto-approve high confidence, escalate medium to reviewer" |

**The Decision Tree** (animated flowchart — the HERO visual of this section):
```
Does the task need tools?
├── NO → Simple prompt (not an agent)
└── YES
    ├── One tool call enough?
    │   └── YES → Pattern 1: Single-Turn Tool Use
    │   └── NO
    │       ├── Do you know the steps upfront?
    │       │   └── YES → Pattern 3: Plan-then-Execute
    │       │   └── NO → Pattern 2: ReAct (discover steps as you go)
    │       │
    │       ├── Does input type determine the handler?
    │       │   └── YES → Pattern 4: Router / Classifier
    │       │
    │       ├── Same task × many inputs?
    │       │   └── YES → Pattern 5: Parallel Fan-Out
    │       │
    │       ├── Sequential specialist stages?
    │       │   └── YES → Pattern 6: Pipeline / Chain
    │       │
    │       ├── Need multiple specialist agents?
    │       │   └── YES → Pattern 7: Supervisor + Workers
    │       │
    │       └── Needs human approval at decision points?
    │           └── YES → Pattern 8: Autonomous + HITL
```

**Combining Patterns** (this is the advanced insight):
Real production agents almost always COMBINE patterns. Examples:
- CAPSTONE-4 uses Router (classify input) → Pipeline (4 agent stages) → HITL (human approval)
- CAPSTONE-6 uses Supervisor (coordinator) → Parallel Fan-Out (50 state testers) → Pipeline (12 checks per state)
- A typical production agent uses Router → ReAct → HITL

"Think of patterns like LEGO blocks — you snap them together. M12-M14 teach you each block. M15B teaches you to assemble them."

**Anti-Patterns to Avoid**:
- ❌ Using multi-agent when single agent + 3 tools would suffice (over-engineering)
- ❌ ReAct without max iterations (infinite loop)
- ❌ Plan-then-execute for exploratory tasks (you don't know the steps yet)
- ❌ Parallel fan-out without error handling (one failure kills everything)
- ❌ Pipeline without intermediate validation (garbage propagates through all stages)

### Part B: Deep Dive — The ReAct Pattern
- What is an agent? (animated comparison: chatbot = one turn, agent = loop with tools)
- The ReAct loop: Think → Act → Observe → Repeat
- Implementing ReAct with Claude's tool use and stop_reason checking
- Thought traces: making Claude "think out loud" improves results
- Stop conditions: max iterations, stop_reason 'end_turn', confidence threshold
- Visual: Animated ReAct loop with thought bubbles and action arrows

### Pattern Comparison Table (shown after ReAct deep dive)
| Aspect | Single-Turn | ReAct | Plan-Execute | Router | Fan-Out | Pipeline | Supervisor | Autonomous+HITL |
|---|---|---|---|---|---|---|---|---|
| Turns | 1 | 2-10 | Known upfront | 1 (routing) + N | N parallel | N sequential | 1 + N delegated | N + human pause |
| Context growth | Minimal | Grows per turn | Fixed plan | Split per route | Isolated per task | Passes forward | Isolated per worker | Grows + checkpoints |
| Error handling | Simple | Retry in loop | Re-plan | Route to fallback | Partial results OK | Stop pipeline | Worker reports to supervisor | Escalate to human |
| Cost | $ | $$ | $$ | $$ | $$$ (parallel API calls) | $$ | $$$ | $$$$ |
| When learned | M05 | M12 (this module) | M13 | M13 | M14, CAPSTONE-6 | M14 | M14, M15B | M17, CAPSTONE-4 |

## Hands-On Lab
Build a ReAct research agent with 3 tools (search_filings, get_details, calculate_risk) that reasons through multi-step UCC questions. Log the full think→act→observe trace. Then add a simple router that classifies the user's question into "lookup" (Pattern 1) or "research" (Pattern 2) and dispatches accordingly.

## Quiz Focus (7 questions)
1. What makes an agent different from a chatbot? (tools + loop + decisions)
2. What does stop_reason 'tool_use' mean? (Claude wants to call a tool — continue the loop)
3. Which pattern for: "Validate 50 state files simultaneously"? (Pattern 5: Parallel Fan-Out)
4. Which pattern for: "I don't know how many steps this will take"? (Pattern 2: ReAct)
5. Can you combine patterns? (yes — most production agents combine 2-3 patterns)
6. Why is ReAct + no max iterations dangerous? (infinite loop, unbounded cost)
7. When is multi-agent overkill? (when single agent + 3-4 tools would work fine)

## Animation Requirements
1. **Agent Design Patterns Catalog** — 8 cards showing each pattern with a simple animated icon
2. **Decision Tree** — interactive animated flowchart, tap a question to see the recommended pattern
3. **Pattern Combinator** — shows how CAPSTONE-4 and CAPSTONE-6 combine multiple patterns
4. **ReAct Loop** — the detailed think→act→observe animation with UCC example
5. **Pattern Comparison Matrix** — interactive table, click any cell to see explanation
