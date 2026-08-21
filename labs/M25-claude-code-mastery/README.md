# M25 Lab: Claude Code Mastery

> Configuration is the new code. The best agents are shaped before a single prompt is sent.

In this lab you build a complete Claude Code configuration for a **UCC Filing Pipeline** project. Instead of writing application code, your deliverable is the `.claude/` directory structure, project-level and directory-level `CLAUDE.md` files, custom slash commands, hook-based guardrails, and a CI integration workflow. By the end, you will have a production-ready Claude Code configuration that enforces domain rules, blocks dangerous operations, and automates PR review.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Modules M12 (ReAct Agent Loop) and M14 (Multi-Agent Systems) completed
- Familiarity with YAML and JSON syntax
- Basic understanding of GitHub Actions (helpful but not required)

## Exercises

| Step | Time | File(s) | What You Build | Key Concept |
|------|------|---------|---------------|-------------|
| 1 | 10 min | `.claude/CLAUDE.md` | Project-level configuration with identity, standards, domain rules | CLAUDE.md hierarchy, project identity |
| 2 | 5 min | `src/api/CLAUDE.md` | Directory-level overrides for the API layer | Directory-scoped rules, rule inheritance |
| 3 | 10 min | `.claude/commands/check-filing.md` | Custom slash command for filing validation | Slash commands, `$ARGUMENTS`, domain automation |
| 4 | 10 min | `.claude/settings.json` + `.claude/hooks/*.py` | Hook-based guardrails and permission scoping | PreToolUse, PostToolUse, allow/deny lists |
| 5 | 5 min | `.mcp.json` | Project-scoped MCP server config | Config scope: why this is NOT settings.json |
| 6 | 10 min | `.github/workflows/claude-review.yml` | CI pipeline for automated PR review | Claude in CI, `--output-format json`, session isolation |
| 7 | 10 min | `validate_config.py` / `.js` | Run the validator to check your work | Self-assessment, configuration completeness |

**Total time: ~60 minutes**

---

## Step 1: Project-Level CLAUDE.md (10 min)

**File:** `starter/.claude/CLAUDE.md`

Open the starter file and fill in every `TODO` section. Your project-level CLAUDE.md must include:

1. **Project Identity** -- Describe the UCC Filing Pipeline in 2-3 sentences. What does it do? What domain does it serve?
2. **Tech Stack** -- List the full stack (Python/FastAPI, PostgreSQL, Redis, Elasticsearch, React/TS, Docker/GCP).
3. **Coding Standards** -- Define formatting rules (black, ruff for Python; ESLint, Prettier for TS), logging rules (no `print()`), and test file naming conventions.
4. **Domain Rules** -- Define the filing number format (`UCC-YYYY-ST-NNNNNNN`), monetary value storage (cents), debtor name normalization, state code format, and expiration rules.
5. **API Conventions** -- Specify Messages API usage, tool definition requirements, structured output approach, and rate limits.
6. **Testing** -- PR test requirements, integration test approach, async test tooling, and coverage thresholds.

**Checkpoint:** Your CLAUDE.md has all 6 sections with substantive content (not just headings). Each section has at least 2 concrete rules.

---

## Step 2: Directory-Level CLAUDE.md (5 min)

**File:** `starter/src/api/CLAUDE.md`

Create a directory-level CLAUDE.md that adds API-specific rules. These rules apply *only* when Claude is working in the `src/api/` directory and its subdirectories. Fill in:

1. **Endpoint Standards** -- All endpoints return JSON, use proper HTTP status codes (400/401/404/422/500), include request ID in responses.
2. **Rate Limiting** -- Document rate limit headers and throttling behavior.
3. **Authentication** -- Bearer token pattern, where tokens are validated, what to do on 401.

**Checkpoint:** The file exists at `src/api/CLAUDE.md` and contains API-specific rules that would NOT belong in the project-level file.

---

## Step 3: Custom Slash Command (10 min)

**File:** `starter/.claude/commands/check-filing.md`

Build a slash command that Claude Code users can invoke with `/check-filing UCC-2024-NY-0012847`. Fill in the template so the command:

1. Accepts a filing number via `$ARGUMENTS`
2. Validates the filing number format against `UCC-YYYY-ST-NNNNNNN`
3. Searches the codebase for references to the filing
4. Checks `data/filings/` for the record
5. Reports status, debtor, secured party, and expiration date if found
6. Flags compliance issues (expired filings, missing amendments)

**Checkpoint:** The file references `$ARGUMENTS`, includes validation steps, and gives Claude clear instructions for both found and not-found cases.

---

## Step 4: Settings with Hooks (10 min)

**File:** `starter/.claude/settings.json`

Configure Claude Code's behavior with hooks and permissions. The starter gives you the correct
*structure* — you fill in the values marked TODO, and write the two hook scripts.

1. **PreToolUse hook** — block the `Write` tool from creating or modifying files under
   `data/production/`. Write `.claude/hooks/block_production_writes.py`.
2. **PostToolUse hook** — log every `Bash` invocation to `audit.log`. Write
   `.claude/hooks/audit_log.py`.
3. **Permissions** — fill in `allow` and `deny`. Allow read tools freely, allow writes only to
   `src/` and `tests/`, deny writes to production data and destructive shell commands.

Three things about hooks that are easy to get wrong, and all fail *silently*:

**The shape is three levels deep.** Event → `{matcher, hooks: [...]}` → `{type, command, timeout}`.
Putting `command` directly on the matcher is valid JSON, saves without complaint, and never fires.
Nothing errors — the guardrail simply is not there.

```json
"PreToolUse": [
  {
    "matcher": "Write",
    "hooks": [
      { "type": "command", "command": "python .claude/hooks/block_production_writes.py", "timeout": 5 }
    ]
  }
]
```

**Hooks read stdin, not argv.** The payload arrives as JSON on standard input. There is no
`$TOOL_INPUT` shell variable; a command that passes one hands your script an empty string, and it
approves everything.

**Blocking and rewriting live in the same output block.** A PreToolUse hook returns
`hookSpecificOutput.permissionDecision` — `allow`, `deny`, `ask`, or `defer` — and can *also*
return `updatedInput` to rewrite the tool's arguments before it runs. Exit 2 blocks
unconditionally and beats any JSON. When several hooks apply, `deny` > `defer` > `ask` > `allow`.

The trap: to rewrite, you must **return a new object**. Mutating the `tool_input` you were handed
does nothing, and printing a modified payload to stdout does nothing either — stdout is parsed as
a decision object. See M16 for a redactor that gets this right.

**Checkpoint:** The file is valid JSON with `hooks.PreToolUse`, `hooks.PostToolUse`,
`permissions.allow` and `permissions.deny`, both hook scripts exist, and no `mcpServers` key —
see Step 5.

---

## Step 5: MCP Server Configuration (5 min)

**File:** `starter/.mcp.json`

Configure a PostgreSQL MCP server so Claude Code can query the filing database directly.

This is a separate file on purpose. **`settings.json` has no `mcpServers` key** — a server
declared there is silently ignored, the same class of bug as a flattened hook. Config lives in
different files by scope:

| Scope | File | Shared with |
|---|---|---|
| Project | `.mcp.json` (committed) | everyone on the repo |
| User | `~/.claude.json` | just you, across all projects |

Read the connection string from the environment (`${DATABASE_URL}`) rather than hardcoding it —
`.mcp.json` is committed.

**Checkpoint:** `.mcp.json` is valid JSON with a non-empty `mcpServers` object, and no database
password appears in it.

---

## Step 6: GitHub Actions CI Integration (10 min)

**File:** `starter/.github/workflows/claude-review.yml`

Create a GitHub Actions workflow that uses Claude Code to review PRs automatically. Fill in:

1. **Trigger** -- On `pull_request` events (opened, synchronize) for `src/` and `tests/` paths.
2. **Permissions** -- `contents: read`, `pull-requests: write`.
3. **Review step** -- Use `claude -p` with a prompt that checks for UCC domain violations, missing error handling, security issues, and test coverage. Use `--output-format json` for structured output.
4. **Session isolation** -- Use `--session "pr-review-${{ github.event.pull_request.number }}"` so each PR gets its own session.
5. **Comment step** -- Post the review results as a PR comment using `gh pr comment`.

**Checkpoint:** The YAML is syntactically valid. It contains `claude -p`, `--output-format json`, `--session`, and `gh pr comment`.

---

## Step 7: Validation (10 min)

Run the provided validation script to check that all your files are correct:

```bash
# From the starter/ directory
python validate_config.py

# Or Node.js
node validate_config.js
```

The validator checks:
- All required files exist
- CLAUDE.md files have required sections
- settings.json has correctly NESTED hooks, and the scripts they name exist
- MCP servers are in .mcp.json, not settings.json
- Slash command references `$ARGUMENTS`
- GitHub Actions workflow contains required elements

**Checkpoint:** All checks pass (exit code 0). The report shows a checkmark for every item.

---

## Verification

After completing all exercises, compare your work against the solution:

```bash
# Run validation against the solution to see a perfect report
cd solution/
python validate_config.py

# Or Node.js
node validate_config.js
```

Compare your files against those in `solution/` and review `expected_output/validation_report.txt` for the expected validator output.

## What You Built

By completing this lab, you have created:

1. **Project-level CLAUDE.md** -- the single most important file for shaping Claude's behavior in your codebase
2. **Directory-level CLAUDE.md** -- scoped rules that override or extend project-level settings
3. **Custom slash command** -- a reusable domain workflow accessible via `/check-filing`
4. **Hook-based guardrails** -- PreToolUse and PostToolUse hooks that enforce safety and audit policies
5. **CI integration** -- automated PR review using Claude Code in GitHub Actions

This is the configuration foundation for every production Claude Code deployment. In M26, you will build on this with the Agent SDK for programmatic agent orchestration.

## Next

- **M26**: Agent SDK Deep Dive -- programmatic agent creation with the Claude Agent SDK
- **M27**: Anti-Patterns & Exam Prep -- common mistakes and certification practice questions
