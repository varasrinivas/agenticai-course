# M25: Claude Code Mastery

**Track**: 9 — Certification Prep | **Position**: 25 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M05 (Function Calling), M07 (MCP), M12 (ReAct)
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-capstones) / #D4A843
**Cert Domain**: Domain 3 — Claude Code Configuration & Workflows (~20% of exam)
**SDK Tier**: 3 (SDK-default + spec-driven). Lab uses Claude Code with slash commands, hooks (`.claude/settings.json`), subagents (`.claude/agents/`), and skills. Spec-driven section drives `/generate-from-spec` against an example `agent-spec.md`. See `prompts/19-sdk-tier-policy.md` and `prompts/17-spec-driven-development.md`.

## Why This Module Exists
Domain 3 is 20% of the certification exam and is the biggest gap in the base course. Your course teaches building agents via the API. The cert also tests configuring Claude Code itself — CLAUDE.md, skills, commands, plan mode, CI/CD. This module fills that entire gap.

## Concepts to Cover

### 1. CLAUDE.md Configuration Hierarchy
- Analogy: "CLAUDE.md files work like CSS cascading — user-level is the body tag, project-level is a class, directory-level is an inline style. More specific wins."
- Technical:
  - `~/.claude/CLAUDE.md` — user-level (personal preferences, available everywhere)
  - `.claude/CLAUDE.md` (project root) — project-level (team standards, committed to git)
  - `src/api/CLAUDE.md` — directory-level (path-specific rules)
  - Merge behavior: all levels are combined, more specific overrides more general
  - `@import` syntax for pulling in shared rules
  - `.claude/rules/` directory for topic-specific rule files
- Animation: `PIPELINE_FLOW` — Three CLAUDE.md files stacking/merging, showing which rules win at each level
- 🎓 CERT TIP: Anti-pattern — putting personal editor preferences in project-level CLAUDE.md. Use user-level for personal, project-level for team standards.
- Quiz angle: "A developer adds their preferred code style to .claude/CLAUDE.md in the repo. What's the problem?"

### 2. Custom Slash Commands vs Skills
- Analogy: "Commands are speed-dial buttons you press manually. Skills are things Claude learns and uses automatically when relevant."
- Technical:
  - **Slash commands**: `.claude/commands/deploy.md` → `/deploy`. Markdown files. User invokes explicitly. Support `$ARGUMENTS` placeholders. YAML frontmatter for allowed-tools, argument-hint, model, description.
  - **Skills**: `.claude/skills/explain-code/SKILL.md`. Claude invokes automatically based on description match OR user invokes via `/skill-name`. YAML frontmatter: `name`, `description`, `context: fork` (isolated context), `allowed-tools` (tool restrictions), `disable-model-invocation: true/false`.
  - Key difference: `context: fork` gives skills an isolated context window — exploration noise doesn't pollute the main session.
  - Legacy: `.claude/commands/` and `.claude/skills/` both create slash commands. Skills are the modern approach with extra capabilities.
- Animation: Side-by-side comparison — command runs in main session (context grows), skill with `context: fork` runs in isolated branch (main session stays clean)
- 🎓 CERT TIP: Anti-pattern — using commands for complex tasks that need context isolation. Use skills with `context: fork` and `allowed-tools` restrictions instead.

### 3. Plan Mode vs Direct Execution
- Analogy: "Plan mode is the architect drawing blueprints before construction. Direct execution is the builder who starts hammering immediately. Both have a place — the question is WHEN."
- Technical:
  - Plan mode: Claude generates a plan, shows you, waits for approval before executing. Good for: unfamiliar codebases, risky changes, complex multi-step tasks.
  - Direct execution: Claude acts immediately. Good for: well-understood tasks, small changes, when you have clear context.
  - Decision criteria: complexity of change, familiarity with codebase, risk level, reversibility
  - Iterative refinement patterns:
    - **TDD iteration**: Red (write failing test) → Green (ask Claude to make it pass) → Refactor
    - **Interview pattern**: Ask Claude to ask YOU questions before starting
    - **Concrete examples**: Provide 2-4 examples of desired output, then ask for generalization
- Animation: Decision tree — "New codebase? → Plan mode. Simple rename? → Direct. Complex refactor? → Plan mode."
- 🎓 CERT TIP: The exam tests decision criteria for when to use plan mode. It's not "always plan" — know the tradeoffs.

### 4. Built-in Tools: Read, Write, Edit, Bash, Grep, Glob
- Technical: Claude Code comes with built-in tools that don't require MCP setup:
  - **Read**: Read file contents. Use for: examining code, understanding context.
  - **Write**: Create new files or overwrite existing. Use for: generating new code, config files.
  - **Edit**: Modify specific parts of existing files (str_replace pattern). Use for: targeted changes.
  - **Bash**: Execute shell commands. Use for: running tests, installing deps, git operations.
  - **Grep**: Search file contents with regex. Use for: finding patterns, references, usage.
  - **Glob**: Find files by name pattern. Use for: discovering file structure, finding specific file types.
  - When to use each: Glob to find → Read to understand → Edit to change → Bash to test
- Animation: Flowchart showing a typical Claude Code session — "Find the auth module" (Glob) → "Read the login function" (Read) → "Fix the bug" (Edit) → "Run tests" (Bash)
- 🎓 CERT TIP: The exam tests tool selection — given a task, which built-in tool is correct?

### 5. CI/CD Integration
- Technical:
  - **Non-interactive mode**: `claude -p "Review this PR for security issues"` — the `-p` flag runs without interactive prompts
  - **Structured output**: `--output-format json` returns machine-parseable results. `--json-schema` enforces a specific output structure.
  - **Session isolation**: In CI, use SEPARATE sessions for code generation and code review. Same session = confirmation bias (reviewer retains generator's reasoning context).
  - **GitHub Actions integration**: Run Claude Code as a PR reviewer step
- Animation: CI/CD pipeline flow — Commit → Build → Claude Code Review (Session A: generate) → Claude Code Review (Session B: review) → Deploy
- 🎓 CERT TIP: Critical anti-pattern — same-session self-review in CI/CD. The exam tests this directly. Always use separate sessions for generate vs review.

### 6. Batch Processing (Message Batches API)
- Technical:
  - Message Batches API: Send up to 10,000 requests in a batch
  - 50% cost reduction vs synchronous API calls
  - 24-hour processing window
  - Use for: latency-tolerant tasks (bulk data extraction, batch reviews, nightly analysis)
  - NOT for: real-time user-facing responses, interactive chat
  - Decision criteria: synchronous for blocking workflows, batch for latency-tolerant
- 🎓 CERT TIP: The exam tests when to use batch vs synchronous. Batch = non-urgent, high-volume, cost-sensitive. Synchronous = user-facing, real-time.

## Code Walkthrough
- Complete `.claude/CLAUDE.md` for the UCC pipeline project with: project conventions, API patterns, database schema reference, @import for shared rules
- A slash command: `.claude/commands/review-filing.md` that reviews a UCC filing parser implementation
- A skill: `.claude/skills/entity-resolution/SKILL.md` with `context: fork` for isolated entity matching analysis
- GitHub Actions workflow using `claude -p` for automated PR review with `--output-format json`

## Hands-On Exercise
Build a complete Claude Code configuration for the UCC pipeline project:
1. Create user-level CLAUDE.md with personal preferences
2. Create project-level CLAUDE.md with team standards, UCC schema reference, @import for coding conventions
3. Create a directory-level CLAUDE.md in `src/api/` with Spring Boot API-specific rules
4. Build a slash command `/check-filing` that validates a UCC filing parser against test data
5. Build a skill `entity-resolution` with `context: fork` and `allowed-tools: [Read, Grep, Glob]`
6. Configure a GitHub Actions workflow that uses Claude Code for PR review with session isolation
- Stretch: Add a batch processing script that extracts structured data from 100 UCC filing PDFs using the Message Batches API

## Quiz Focus (8 questions — this module covers 20% of the exam)
1. Where should personal code style preferences go? (user-level CLAUDE.md, not project)
2. What does `context: fork` do in a skill? (isolated context window)
3. When should you use plan mode? (scenario-based decision)
4. Given a task, which built-in tool is correct? (Grep vs Glob vs Read)
5. What's wrong with same-session self-review in CI? (confirmation bias)
6. When to use Message Batches API vs synchronous? (latency-tolerant vs real-time)
7. What's the anti-pattern with using commands for complex exploration? (use skills with fork)
8. How does CLAUDE.md hierarchy merge? (more specific overrides general)
