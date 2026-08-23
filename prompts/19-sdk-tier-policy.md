# SDK Tier Policy — When to Use Raw API vs Agent SDK vs Spec-Driven

This is the **source of truth** for which tooling/abstraction every module and capstone in the course uses. Apply when generating, regenerating, or reviewing any module brief, lab, capstone, or HTML output.

## The Problem We're Fixing

The course's labs were originally written before `claude-agent-sdk` was the recommended path. As of 2026, ~255 lab files use raw `client.messages.create()` calls (mostly mocked), even in modules that explicitly TEACH the Agent SDK (M26 simulates the SDK with a mock instead of using it). This produces three failure modes:

1. **Cert misalignment.** The Claude Certified Architect exam tests Agent SDK, hooks, subagents, and skills — concepts students never use in the labs.
2. **Anti-pattern muscle memory.** Students leave the course with hand-rolled `while True: client.messages.create(...)` loops as their default agent shape.
3. **Spec-driven development is invisible.** The course is itself spec-driven (prompts → Claude Code → HTML), but the labs don't teach the pattern.

## The Three Tiers

Every lab is classified into exactly one tier. The tier dictates what the primary `solution/` folder contains.

### Tier 1 — Manual (Raw Messages API)

**Modules: M01–M11.**

Labs use `client.messages.create()` directly. Tool definitions are JSON dicts. The tool-use loop is a hand-written `while` loop that checks `stop_reason`. No `claude-agent-sdk` import.

**Why:** These modules teach what the SDK abstracts away. A student who has never written the loop themselves can't reason about latency, retries, or context-window failures when the SDK hides them. Tier 1 builds the mental model.

**What it looks like:**
```python
import anthropic
client = anthropic.Anthropic()
messages = [{"role": "user", "content": "..."}]
while True:
    resp = client.messages.create(model=..., tools=TOOLS, messages=messages)
    if resp.stop_reason == "end_turn":
        break
    # execute tool_use blocks, append tool_result, loop
```

### Tier 2 — Dual-Track (Manual + SDK side-by-side)

**Modules: M12, M13, M14, M16, M17, M19.**

Labs ship **two** solutions: `solution/` (manual, same as Tier 1 style) and `solution-sdk/` (uses `claude-agent-sdk`). The lab walks the student through the manual version first, then shows the SDK version doing the same thing in fewer lines. Side-by-side diff is the lesson.

**Why:** These are pivot-point modules. The student already understands the loop (M12 ReAct is the moment they "get it"); now they learn the SDK as a productivity layer, not a black box. By M19 (tracing) they should be reaching for the SDK by default.

**What ships in `solution-sdk/`:**
- `agent.py` using `from claude_agent_sdk import query, ClaudeAgentOptions, tool, create_sdk_mcp_server`
- Tools as `@tool`-decorated async functions returning `{"content": [{"type": "text", "text": ...}]}`
- An MCP server via `create_sdk_mcp_server`
- `query(prompt=..., options=ClaudeAgentOptions(...))` as the entry point
- Hooks (where applicable) via `hooks={...}` and `can_use_tool=...`

### Tier 3 — SDK-default (rewrite primary solution)

**Modules: M15B, M22B, M25, M26, M27, M27B. All capstones except CAPSTONE-6.**

The `solution/` folder uses the SDK as the primary path. The hand-rolled loop, if shown at all, lives in `appendix/` and is labeled "under the hood — for understanding, not for production."

**Why:** These are flagship/cert-aligned labs. They are what the course is "selling" — a student finishing M15B should walk out with a real SDK-based agent. M26 is the **canonical** SDK module; if its lab simulates the SDK, the entire course's authority on the SDK collapses.

**What ships in `solution/`:**
- Full SDK usage with hooks (`PreToolUse`, `PostToolUse`), `can_use_tool`, sessions
- Subagents declared as `.claude/agents/<name>.md` files (where applicable, M14/M15B)
- Hooks declared in `.claude/settings.json` (M16/M17)
- Slash commands in `.claude/commands/` (M15B/M25)
- A spec file in `spec/agent-spec.md` (capstones, M15B) — see Spec-Driven Pattern below

### Special case — CAPSTONE-6 (Bronze testing / data pipeline)

Stays Tier 1. CAPSTONE-6 is intentionally the "non-agent baseline" — it's a data pipeline using LLMs as evaluators, not an agent. It demonstrates the contrast.

## Spec-Driven Pattern (Tier 3 capstones + M15B)

Every Tier 3 capstone ships a `spec/agent-spec.md` that fully describes the agent — tools, hooks, sessions, API surface, deployment, tests, mock data. The student's lab flow is:

1. **Read the spec.** Understand what the system should do.
2. **Run** `claude` and ask: *"Read spec/agent-spec.md and build the entire project."*
3. **Verify** with the included tests.
4. **Iterate** by editing the spec and re-prompting.

The pre-built `solution/` folder exists as a reference only — students can compare what they generate against it. See `prompts/17-spec-driven-development.md` for the full pattern and the canonical `agent-spec.md` template.

The new `/generate-from-spec` slash command implements this workflow.

## Required Imports & Patterns Cheat Sheet

When writing or regenerating SDK-based labs, use these exact patterns. Do not invent alternatives.

### Python — `claude-agent-sdk` (preferred)
```python
from claude_agent_sdk import (
    query,
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    AssistantMessage,
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
)

@tool("tool_name", "description", {"param": str})
async def my_tool(args):
    result = do_work(args["param"])
    return {"content": [{"type": "text", "text": json.dumps(result)}]}

server = create_sdk_mcp_server(name="my_tools", version="1.0.0", tools=[my_tool])

options = ClaudeAgentOptions(
    system_prompt="...",
    mcp_servers={"my": server},
    allowed_tools=["mcp__my__tool_name"],
    max_turns=8,
    model="claude-sonnet-4-6",
    hooks={...},          # optional
    can_use_tool=...,     # optional permission gate
)

async for msg in query(prompt="...", options=options):
    if isinstance(msg, AssistantMessage):
        ...
```

### Python — testing without an API key
Use the SDK's mock-friendly patterns. The pattern from `labs/capstone-4-agent-team/domain-a-healthcare/sdk_tests/` is canonical. For unit tests of hooks/permissions, exercise `HookMatcher`, `can_use_tool`, and `PermissionResultAllow`/`Deny` directly without making real calls.

### Node — `@anthropic-ai/claude-agent-sdk`
```typescript
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";

const myTool = tool("tool_name", "description", { param: z.string() }, async (args) => {
  const result = await doWork(args.param);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
});

const server = createSdkMcpServer({ name: "my_tools", tools: [myTool] });

for await (const msg of query({ prompt: "...", options: { mcpServers: { my: server } } })) {
  // ...
}
```

### Subagent definitions — `.claude/agents/<name>.md`
```markdown
---
name: filing-search
description: Searches UCC filings by debtor name across states. Returns structured filing list.
tools:
  - search_filings
  - get_filing_details
---

You are the filing-search specialist. ...
```

### Skills — `.claude/skills/<name>/SKILL.md`

**New to this corpus as of CAPSTONE-9.** A Skill is knowledge or a runbook, loaded on demand by
description match. It shares the caller's context, so it is the right home for something several
subagents need and the wrong home for anything that has to sequence, isolate, or block.

```markdown
---
name: behavioral-health-um
description: Behavioral-health UM domain knowledge — ASAM levels and the six dimensions,
  concurrent review cadence, 42 CFR Part 2, MHPAEA parity, BH code sets, and the
  reviewer-licensure rule. Load before reading, classifying or generating anything in a
  behavioral-health prior-authorization system.
allowed-tools: Read, Grep        # optional; advisory, not enforced
---

Body. Keep the entry point SHORT and make it route:

| Reference | Load it when |
|---|---|
| `references/asam-levels.md` | Classifying a level of care, or writing a decision table |
| `references/part2-redisclosure.md` | Anything touching consent, disclosure, logging, eventing |
```

**The frontmatter schema — read it from the CLI, never infer it from examples.**
Authority is Claude Code's own schema, not the docs and not a survey of published skills.
Fixed-string greps against the installed binary, so they survive minifier churn:

```bash
CLI=~/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe
grep -aoF '["inline","fork"]' "$CLI"
grep -aoF 'Agent type to spawn when `context: fork`' "$CLI"
# verified against v2.1.241
```

| Field | Notes |
|---|---|
| `name`, `description` | **the only required fields** |
| `context` | `inline` (default) expands the skill into the current conversation; **`fork` spawns a subagent**, giving the skill its own context window so only its result returns |
| `agent` | which agent type to spawn — fork only |
| `background` | fork only; reports as a task notification instead of blocking the turn |
| `when_to_use` | extra trigger guidance beyond `description` |
| `paths` | globs — the skill loads only when matching files are touched |
| `hooks` | hooks scoped to this skill |
| shared with slash commands | `model`, `allowed-tools`, `disallowed-tools`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `effort`, `shell` |
| NOT in the schema | `license`, `tools` — they appear in some marketplace skills and are ignored |

**Unrecognised keys and invalid enum values are ignored SILENTLY**, so `context: forked` behaves
exactly like no `context` at all — no warning, no error. That is the trap worth teaching.

> **A mistake this corpus already made once.** `context: fork` was written off as not a real
> field because it appears in none of the 58 official marketplace skills and the
> `skill-development` skill does not document it. Neither is evidence of absence. The wrong
> conclusion reached a shipped test, a spec, two CLAUDE.md files and a course page before anyone
> read the schema. Infer a schema from the schema.

A skill directory may bundle files, and bundling is most of the point:

```
.claude/skills/behavioral-health-um/
├── SKILL.md              # the entry point — a router, not the whole body of knowledge
├── references/           # loaded on demand; stays out of context until something needs it
│   ├── asam-levels.md
│   └── part2-redisclosure.md
└── scripts/              # RUN, not recalled
    └── validate_bh_codes.py
```

**Skill vs subagent vs slash command:**

| | Skill | Subagent | Slash command |
|---|---|---|---|
| Loaded | on demand, by description | when delegated to | when a person types it |
| Context | the caller's — **or its own, with `context: fork`** | **its own window** | shares the caller's |
| Bundles files | **yes** | no | no |
| Restricts tools | advisory | **enforced** | no |
| Blocks a tool call | no | no — hooks do that | no |

**The test:** does it decide, branch, parallelize, or block? Subagent. Same steps every time?
Skill. An entry point a human invokes? Slash command.

**Three anti-patterns to reject in review:**
1. The same domain ontology pasted into N subagent prompts. It drifts the moment one is edited and
   costs tokens on every turn. One Skill, loaded on demand.
2. A Skill that "orchestrates". It cannot sequence phases or block a tool call — writing
   "then delegate to the validator" in a Skill produces a suggestion, not a control. But it *can*
   isolate context, via `context: fork`, so "needs isolation" alone does not make something a
   subagent. Reach for a real subagent when you also need a system prompt written for that job
   and its own model routing.
3. A slash command where a Skill belongs. If the agent should reach for it mid-run on its own, it
   is a Skill.

### Hooks — `.claude/settings.json`

**The nesting is three levels deep, and `command` never sits on the matcher.** A matcher entry is
a *group*: it pairs a `matcher` with a `hooks` array of handler objects. Flattening it to
`{"matcher": ..., "command": ...}` parses as JSON, writes to disk without complaint, and silently
never fires — which is the worst failure mode available, because the lab looks correct and the
guardrail is not there.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__ucc__search_filings",
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/validate_query.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/redact_pii.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The three levels are: **event** (`PreToolUse`) → **matcher group** (`{matcher, hooks}`) →
**handlers** (`{type, command, timeout}`).

- **Match-all** is `"*"`, `""`, or omitting `matcher` entirely. A matcher string is matched as a
  regex, so `"mcp__oracle_src__.*"` matches every tool on that MCP server and `"Edit|Write"`
  matches either.
- **`timeout`** is seconds, and belongs on the *handler*, beside `type` and `command` — not on
  the matcher group.
- **Blocking from a `PreToolUse` hook** has two forms. Exit `2` with the reason on stderr blocks
  unconditionally. Or exit `0` and print structured JSON, which is the preferred path because the
  reason reaches the model:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Source database is read-only: DROP rejected"
  }
}
```

`permissionDecision` is one of `"allow"`, `"deny"`, `"ask"`, `"defer"`. Exit `2` wins over the
JSON — a `"permissionDecision": "allow"` cannot override it. When several hooks apply,
`deny` > `defer` > `ask` > `allow`.

- **Rewriting the tool input from a `PreToolUse` hook** uses `updatedInput` in the same block:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": { "file_path": "./sandbox/config.yaml" }
  }
}
```

Return a *new* object rather than mutating `tool_input` — mutating it in place has no effect.
Omitting `permissionDecision` still applies the modified input and lets normal permission
evaluation proceed; with `"defer"`, `updatedInput` is ignored. `PostToolUse` has the mirror
field, `updatedToolOutput`, for replacing a result before the model sees it. Return `{}` to allow
unchanged.

**Settings hooks vs `can_use_tool`.** Two delivery mechanisms, and a Tier 3 lab usually needs
both: `can_use_tool` in `ClaudeAgentOptions` covers the agent running as a Python program, and
`.claude/settings.json` covers a student running plain `claude` in the same directory.

They are equal in *power* — both can allow, deny, and rewrite. What differs is where they run and
how the rewrite is expressed:

| | settings.json hook | `can_use_tool` |
|---|---|---|
| Runs as | a subprocess, per tool call | in-process |
| Deny | `permissionDecision: "deny"`, or exit 2 | `PermissionResultDeny(message=...)` |
| Rewrite | `hookSpecificOutput.updatedInput` | `PermissionResultAllow(updated_input=...)` |
| Sees | the JSON payload on stdin | the Python objects directly |

SDK callback hooks (`HookMatcher`) use the **same JSON output format** as shell command hooks, so
one implementation can serve both. Point them at the same code — a guardrail enforced in one mode
and missing in the other is worse than one consistently absent, because nobody knows which mode
they are in. `labs/capstone-8-oracle-to-postgres/solution/hooks_cli.py` is the canonical adapter:
settings.json can only invoke *commands*, so that module reads the payload on stdin and
dispatches to the same functions `can_use_tool` calls.

### Model IDs — read them from the provider, never pattern-match them

A wrong model ID is the cheapest error to make and one of the most expensive to catch: it looks
plausible in review, passes every offline test, and fails at runtime with a 400 or a
model-not-found. Two things make it easy to get wrong — the naming convention changed, and
each cloud provider has its own namespace.

**Direct API.** Same authority as the Skills schema — the CLI binary:

```bash
CLI=~/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe
grep -aoE 'claude-(opus|sonnet|haiku|fable)-[0-9][a-z0-9-]*' "$CLI" | sort -u
```

Note the convention flip. Current IDs are **tier-first** — `claude-sonnet-4-6`,
`claude-haiku-4-5-20251001`. Models from the 3.x era are **tier-last** — `claude-3-5-haiku-20241022`.
Writing an old model in the new shape (`claude-haiku-3-5`) produces a string that reads correctly
to a human and does not exist.

**Bedrock and Vertex are a different namespace.** The CLI binary is not authoritative for them;
the provider’s model card is. Look up the literal string per model:

| Provider | Where | Sonnet 4.6 |
|---|---|---|
| Direct | CLI binary, grep above | `claude-sonnet-4-6` |
| Bedrock | `docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-<model>.html` — "Programmatic Access" table | `anthropic.claude-sonnet-4-6`, geo `us.anthropic.claude-sonnet-4-6`, global `global.anthropic.claude-sonnet-4-6` |
| Vertex | Google Cloud partner-model page for that model | `claude-sonnet-4-6` |

**The suffixes are generational, not universal.** The `-v1:0` and the embedded date belong to the
older Bedrock IDs — `anthropic.claude-3-5-sonnet-20241022-v2:0` still carries both. Sonnet 4.6
and Opus 4.7 carry neither. Vertex `@date` pinning is the same story: real for
`claude-sonnet-4-5@20250929`, absent for 4.6. So the shape of a sibling model’s ID tells you
nothing about this one.

> **This corpus got it wrong twice.** `claude-haiku-3-5` shipped in a copy-pasteable
> `claude --model` command. `us.anthropic.claude-sonnet-4-6-20250514-v1:0` shipped as the
> *correct answer* to a Knowledge Check asking which Bedrock ID is right — a 4.6 name welded
> to Sonnet 4’s date and a suffix 4.6 does not use. Both were produced by reasoning from a
> neighbouring ID instead of looking one up. Looking it up takes one fetch.

## Per-Module Tier Index

| Module | Tier | Notes |
|---|---|---|
| M00 | n/a | Code-free overview |
| M01–M04 | 1 | Foundations — raw API only |
| M05 Function Calling | 1 | Foundational tool-use loop |
| M06 Multi-tool | 1 | Same |
| M07 MCP | 1 | MCP via raw protocol |
| M08–M11 | 1 | Conversation, RAG, memory — raw API |
| M12 ReAct | 2 | Pivot point. Manual loop + SDK side-by-side |
| M13 Planning | 2 | |
| M14 Multi-agent | 2 | Manual coordinator + `.claude/agents/` SDK version |
| M15 Code Interpreter | 1 | Sandbox is a separate concern from SDK choice |
| **M15B Build Complete Agent** | **3** | Flagship. Spec-driven, SDK primary |
| M16 Input Guardrails | 2 | Manual wrappers + hooks |
| M17 Output Guardrails / HITL | 2 | Manual + hooks + `can_use_tool` |
| M18 Evaluation | 1 | Eval framework is independent of SDK choice |
| M19 Tracing | 2 | Manual logging + SDK event stream |
| M20 Monitoring | 1 | Independent |
| M21 API Design | 1 | FastAPI wrapper is independent |
| M22 Cost Optimization | 1 | Independent |
| **M22B Deploy** | **3** | Deploy an SDK agent, not a hand-rolled loop |
| **M25 Claude Code Mastery** | **3** | SDK + slash commands + skills |
| **M26 Hooks/Sessions/SDK** | **3** | MUST use real `claude-agent-sdk` |
| **M27 Cert Prep** | **3** | Cert-aligned, SDK-only |
| **M27B Cert Domain 5–6** | **3** | Same |
| CAPSTONE-1 | 1 | All domains. Raw `anthropic` only |
| CAPSTONE-2 | 1 | All domains. Raw `anthropic` only |
| CAPSTONE-3 | 1 | All domains. Raw `anthropic` only |
| CAPSTONE-4 | 1 | Solutions are raw `anthropic`. The only SDK code is the offline test harness in `domain-a-healthcare/sdk_tests/`, which is the canonical `HookMatcher` / `can_use_tool` pattern this document cites elsewhere |
| CAPSTONE-5 | 1 | Solutions are raw `anthropic`. `domain-c-ucc/spec/agent-spec.md` exists and describes an SDK build, but no code implements it; domains A and B have no spec |
| CAPSTONE-6 | 1 | Non-agent baseline (intentional) |
| CAPSTONE-7 | n/a | "Agent Evolution" → three module pages, **no lab in this repo**. Nothing to score until one exists |
| CAPSTONE-8 | 3 | Standalone (no domain letter). Spec-driven. Legacy Oracle → PostgreSQL migration; five subagents, three `PreToolUse` guards, HITL cutover gate |
| CAPSTONE-8B | 3 | Skills-first rebuild of Capstone 8. Spec-driven. |
| **CAPSTONE-9** | **3** | Standalone (no domain letter); uses DOMAIN A-BH. Spec-driven. Legacy Spring MVC/JSP monolith → distributed platform. Coordinator + 8 subagents, **4 Skills**, 5 hooks, 10 parity checks, HITL finalization gate. Two gated phases: 9A backend, 9B frontend. FIRST module in the corpus to use `.claude/skills/` |

> **These rows describe what the labs contain, not what they should become.** Capstones 1–5 were previously listed as Tier 3 spec-driven; none of them were. That gap made `/validate-capstone` report five critical findings that were really one stale table, which is the fastest way to teach people to ignore a validator. Capstone 6 is Tier 1 **by design** — it is the non-agent baseline and must stay that way. Capstones 1–5 are Tier 1 **by circumstance** and are the real upgrade backlog, in roughly that order: 5 already has a spec to build against, and 4 already has the test harness. Moving one means writing `spec/agent-spec.md` and porting `solution/` to `claude-agent-sdk` — see Capstones 8 and 9 for the shape.


## Generator Rules

When `/generate-module`, `/generate-capstone`, or `/generate-lab-repo` runs:

1. **Look up the module's tier** from the table above. If absent, default to Tier 1 with a warning.
2. **Tier 1**: Generate raw-API labs. Do NOT import `claude-agent-sdk`.
3. **Tier 2**: Generate `solution/` (raw) AND `solution-sdk/` (SDK). The brief and HTML must walk through both, with a side-by-side comparison section.
4. **Tier 3**: Generate `solution/` using the SDK. If the module is in the spec-driven set (M15B + capstones 1–5, 7, 8, 8B, 9), also generate `spec/agent-spec.md` and an `appendix/manual-loop.py` showing the under-the-hood version.
5. **Always** include the SDK pattern cheat sheet imports verbatim — do not invent alternative APIs.
6. **Never** mock the SDK by reimplementing `query()` with `client.messages.create()`. If an offline test is needed, use the `claude-agent-sdk` test patterns (see `capstone-4-agent-team/domain-a-healthcare/sdk_tests/`).

## Reviewer Rules

When `/review-module` or `/consistency-check` runs, fail the review if:
- A Tier 2 module ships only one solution folder.
- A Tier 3 module's primary `solution/` does not import `claude-agent-sdk`.
- M26's lab simulates the SDK.
- Any capstone in 1–5/7/8 is missing `spec/agent-spec.md`.
- A lab uses `claude_agent_sdk` but reimplements `query()` as a wrapper around `client.messages.create()`.
