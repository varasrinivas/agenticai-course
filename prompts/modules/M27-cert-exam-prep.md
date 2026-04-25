# M27: Certification Exam Prep — Anti-Patterns, Scenarios & Practice

**Track**: 9 — Certification Prep | **Position**: 27 of 30 | **Level**: Advanced
**Prerequisites**: ALL previous modules (M01-M26). This is the capstone cert prep module.
**Estimated Time**: 90-120 minutes
**Track Color**: var(--track-capstones) / #D4A843
**Cert Domains**: ALL — This module fills remaining gaps across all 5 domains and provides exam practice

## Why This Module Exists
This module has three jobs: (1) teach the remaining cert topics not covered in M25-M26, (2) present all 18 anti-patterns as an animated reference, and (3) provide mock exam scenarios with practice questions. It's the final preparation before sitting the exam.

## Concepts to Cover

### 1. Anti-Patterns Master Reference (All 18)
- Format: Animated "❌ DON'T vs ✅ DO" cards for each anti-pattern, grouped by domain
- Animation: Each card flips — front shows the anti-pattern, back shows the correct approach with WHY
- Interactive: Learner tries to identify the anti-pattern in a code/config snippet before revealing the answer

**Domain 1 — Agentic Architecture (5 anti-patterns)**:
1. ❌ Parsing NL for loop termination → ✅ Check stop_reason
2. ❌ Arbitrary iteration caps as primary stop → ✅ Natural termination via stop_reason
3. ❌ Prompt-based enforcement for critical rules → ✅ Programmatic hooks
4. ❌ Sentiment-based escalation → ✅ Policy gaps, capability limits, thresholds
5. ❌ Self-reported confidence scores → ✅ Structured criteria + programmatic checks

**Domain 2 — Tool Design & MCP (4 anti-patterns)**:
6. ❌ Generic errors ('Operation failed') → ✅ isError, errorCategory, isRetryable, context
7. ❌ Empty results for access failures → ✅ Distinguish access failure from genuinely empty
8. ❌ 18+ tools per agent → ✅ 4-5 per agent, distribute to subagents
9. ❌ Hardcoded API keys in .mcp.json → ✅ ${ENV_VAR} expansion

**Domain 3 — Claude Code Config (3 anti-patterns)**:
10. ❌ Personal prefs in project CLAUDE.md → ✅ User-level for personal, project for team
11. ❌ Commands for complex tasks needing isolation → ✅ Skills with context: fork
12. ❌ Same-session self-review in CI → ✅ Separate sessions for generate vs review

**Domain 4 — Prompt Engineering (3 anti-patterns)**:
13. ❌ Vague instructions ("be thorough") → ✅ Explicit measurable criteria
14. ❌ Assuming tool_use guarantees semantic correctness → ✅ Schema + business rule validation
15. ❌ Generic retry ("try again") → ✅ Append specific errors (which field, expected vs actual)

**Domain 5 — Context & Reliability (3 anti-patterns)**:
16. ❌ Progressive summarization of critical details → ✅ Immutable case facts blocks
17. ❌ Aggregate-only accuracy metrics → ✅ Per-document-type stratified metrics
18. ❌ No provenance tracking in multi-agent → ✅ Source, confidence, timestamp, agent ID

### 2. Remaining Domain 4 Gaps — Validation & Structured Output Details
- **tool_choice options**: `'auto'` (Claude decides), `'any'` (must use a tool, Claude picks which), forced specific tool `{"type": "tool", "name": "extract_filing"}`. When to use each.
- **Schema design patterns**: required vs optional fields, enums with `'other'` + freetext detail field for unexpected categories, nested objects for complex data
- **Validation-retry loop pattern**: Execute tool_use → validate output → if errors, append SPECIFIC error message to conversation (not generic "try again") → re-request → repeat up to 3 times
- **detected_pattern field**: Track patterns the model repeatedly dismisses/ignores across retries. If same field fails 3 times, flag for human review instead of infinite retry.
- **Multi-pass review**: Pass 1 = per-file local analysis (style, bugs, security per file). Pass 2 = cross-file integration (API contracts, data flow consistency). Use SEPARATE sessions for each pass.
- 🎓 CERT TIP: The exam tests tool_choice specifically. Know when 'auto' vs 'any' vs forced is appropriate.

### 3. Remaining Domain 5 Gaps — Provenance & Context
- **Information provenance**: When multiple subagents provide data, track:
  - Source: which agent/tool/API provided this claim
  - Confidence: high/medium/low based on source reliability
  - Timestamp: when the data was retrieved (stale data risk)
  - Agent ID: which subagent in the pipeline
  - Use case: When two subagents return conflicting entity data in UCC filings, provenance lets the coordinator decide which to trust
- **Synthesis output quality**: Categorize claims as:
  - "Well-established" — multiple sources agree
  - "Contested" — sources disagree
  - "Single-source" — only one source, flag for verification
  - Source characterizations: "official state filing" vs "third-party aggregator" vs "user-submitted"
- **Context degradation mitigation**:
  - `/compact` — summarize conversation, trim old context (lossy — critical details may be lost)
  - Scratchpad files — write persistent state to disk, read back when needed (lossless)
  - Crash recovery manifests — structured file tracking: current task, completed steps, pending steps, context references
  - Subagent delegation — offload subtasks to fresh subagents with clean context
- 🎓 CERT TIP: The exam tests provenance tracking in multi-agent research scenarios (Scenario 3). Know the claim-source mapping pattern.

### 4. Exam Scenario Walkthroughs (All 6)
Walk through each of the 6 possible exam scenarios with architectural reasoning:

**Scenario 1: Customer Support Resolution Agent**
- Architecture: Single agent with hooks + escalation
- Key decisions: Hook-based refund limits, escalation on policy gaps (not sentiment), structured error responses from tools
- Maps to: M12 (ReAct), M26 (Hooks)

**Scenario 2: Code Generation with Claude Code**
- Architecture: Claude Code with CLAUDE.md, plan mode, iterative refinement
- Key decisions: Plan mode for complex tasks, TDD iteration pattern, directory-level CLAUDE.md for API vs frontend
- Maps to: M25 (Claude Code Mastery)

**Scenario 3: Multi-Agent Research System**
- Architecture: Coordinator + subagents via Task tool, parallel execution
- Key decisions: Context isolation, provenance tracking, fork_session for exploration, structured result aggregation
- Maps to: M14 (Multi-Agent), M26 (Sessions/Subagents)

**Scenario 4: Developer Productivity with Claude**
- Architecture: Agent SDK with built-in tools + MCP servers
- Key decisions: Tool selection (Read/Write/Bash/Grep/Glob), MCP server integration, codebase exploration strategy
- Maps to: M25 (Built-in tools), M07 (MCP)

**Scenario 5: Claude Code for CI/CD**
- Architecture: Non-interactive Claude Code in GitHub Actions
- Key decisions: -p flag, --output-format json, session isolation (generate ≠ review), batch API for non-urgent analysis
- Maps to: M25 (CI/CD), M21 (Deployment)

**Scenario 6: Structured Data Extraction**
- Architecture: tool_use with JSON schemas + validation-retry
- Key decisions: Schema design (required/optional/enum+other), validation-retry with specific errors, few-shot for format consistency, field-level confidence for human review
- Maps to: M04 (Structured Output), M03 (Prompts)

For each scenario: animated architecture diagram, decision points highlighted, which anti-patterns apply, which correct patterns to use.

### 5. Mock Exam Practice
Three mock exam sessions, each with 10 questions across multiple scenarios:

**Mock Exam A** (Scenarios 1 + 3 focus):
- 4 questions on agentic loops and hooks (Domain 1)
- 3 questions on multi-agent provenance (Domain 5)
- 3 questions on tool design (Domain 2)

**Mock Exam B** (Scenarios 2 + 5 focus):
- 4 questions on Claude Code configuration (Domain 3)
- 3 questions on CI/CD integration (Domain 3)
- 3 questions on prompt engineering (Domain 4)

**Mock Exam C** (Scenarios 4 + 6 focus):
- 3 questions on built-in tool selection (Domain 2/3)
- 4 questions on structured output and validation (Domain 4)
- 3 questions on context management (Domain 5)

Each question: scenario context → question → 4 options (1 correct, 3 distractors including anti-patterns) → detailed explanation for ALL 4 options (why right is right, why wrong is wrong).

## Code Walkthrough
- Validation-retry loop: tool_use → validate → append specific error → retry (complete Python implementation)
- Provenance tracker: Subagent result with source, confidence, timestamp, agent_id metadata
- Crash recovery manifest: JSON file tracking task state for session recovery

## Hands-On Exercise
**Mini Exam Simulation**: Learner picks 2 of 6 scenarios and answers 10 questions for each, timed at 30 minutes. Course provides:
1. Scenario context (2-3 paragraphs describing the system to build)
2. 10 questions with 4 options each
3. After submission: detailed explanations for every answer
4. Score breakdown by domain
5. Weak areas identified with links back to relevant modules

- Stretch: Build one of the 6 scenarios end-to-end as a working prototype using the patterns from this module

## Quiz Focus (30 questions total — 10 per mock exam)
Mock Exam A: Agentic loops, hooks, multi-agent, provenance, tool errors
Mock Exam B: CLAUDE.md, skills, CI/CD, plan mode, prompt criteria, batch API
Mock Exam C: Built-in tools, structured output, validation-retry, context degradation, stratified metrics

Each question follows the cert format:
- Scenario preamble (2-3 sentences)
- Question stem
- 4 options (A-D)
- Correct answer with explanation
- Why each wrong answer is wrong (anti-pattern identification)
