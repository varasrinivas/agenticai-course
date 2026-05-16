---
description: Read an agent-spec.md and generate a complete Tier 3 agent project from it
argument-hint: [PATH_TO_SPEC e.g. labs/M15B-build-complete-agent/spec/agent-spec.md]
---

Read the agent specification at $ARGUMENTS and generate the complete agent project from it. This is the spec-driven workflow described in `prompts/17-spec-driven-development.md`.

Follow these steps in order:

1. Read `prompts/19-sdk-tier-policy.md` to confirm the SDK patterns and required imports
2. Read `prompts/17-spec-driven-development.md` for the canonical spec format and workflow
3. Read the spec file at $ARGUMENTS — it MUST exist; abort with a clear error if not
4. Parse the spec's required sections:
   - **Overview** — agent purpose
   - **Agent Configuration** — model, framework, max_turns, etc. (must be `claude-agent-sdk`)
   - **System Prompt** — the agent's role and instructions
   - **Tools** — each tool's name, description, params, returns, mock data
   - **Hooks** — PreToolUse / PostToolUse hook definitions
   - **Sessions** — multi-turn requirements
   - **API Wrapper** — FastAPI surface (if specified)
   - **Deployment** — Docker / Cloud Run / Lambda targets
   - **Tests** — test files and what each verifies
   - **Evaluation Dataset** — test scenarios
   - **File Structure** — exact tree to generate
5. Determine the output directory: same parent as the spec, in a `generated/` sibling folder. For example, `labs/M15B/spec/agent-spec.md` → `labs/M15B/generated/`. If `generated/` already exists, ask the user before overwriting (this is a regenerate, not destructive — they may want to diff).
6. Generate every file in the spec's File Structure section. Use these mandatory patterns:
   - **Tools**: `@tool`-decorated async functions returning `{"content": [{"type": "text", "text": json.dumps(...)}]}`, exposed via `create_sdk_mcp_server`
   - **Agent entry point**: `async for msg in query(prompt=..., options=ClaudeAgentOptions(...))` — never `client.messages.create()`
   - **Hooks**: `HookMatcher(matcher=..., hooks=[async_fn])` passed to `ClaudeAgentOptions(hooks={...})`
   - **Permission gate**: `can_use_tool=async_callback` returning `PermissionResultAllow()` or `PermissionResultDeny(message=...)`
   - **Subagents** (if multi-agent): `.claude/agents/<name>.md` files with frontmatter `name`, `description`, `tools`, optional `model`
   - **Settings hooks** (if external command hooks): `.claude/settings.json` with PreToolUse/PostToolUse entries pointing to scripts in `hooks/`
   - **Tests**: pytest with `claude-agent-sdk` test patterns from `labs/capstone-4-agent-team/domain-a-healthcare/sdk_tests/` as reference. Tests must exercise hooks, `can_use_tool`, and tool ordering.
   - **Mock data**: realistic, deterministic, in `mock_data.py`. The spec lists count and shape — match exactly.
   - **CLAUDE.md**: include a short CLAUDE.md in the generated project explaining what was built and listing the slash commands that drive it (`/test-agent`, `/eval-agent`, etc.)
7. Generate the slash commands listed in the spec's `.claude/commands/` section. Each command's body must be specific to this project — not generic.
8. After file generation, run a quick sanity check:
   - Every Python file imports from `claude_agent_sdk` (not `anthropic.Agent`)
   - No file mocks `query()` with `client.messages.create()`
   - Every `@tool` returns the `{"content": [{"type": "text", "text": ...}]}` shape
   - `pytest --collect-only` from the generated directory should discover all test files
9. Print a summary:
   - Files generated: count by type (tools, hooks, tests, agents, etc.)
   - Total lines of generated code
   - Lines of spec → ratio (the leverage of spec-driven)
   - Next-step suggestions: "Run `/test-agent` to verify; edit the spec and re-run `/generate-from-spec` to iterate."

## Iteration Mode

If the spec already has a corresponding `generated/` folder, the user is iterating, not generating from scratch. In that case:

1. Read both the spec AND the existing `generated/` files
2. Diff the spec against the previous spec (if one was saved as `generated/.last-spec.md`)
3. Make TARGETED edits — add new tools, modify hooks, update tests for changed behavior
4. Do not regenerate files that haven't been affected by the spec change
5. Save the current spec as `generated/.last-spec.md` for the next iteration

## Anti-patterns to refuse

If you encounter any of these in the spec, refuse to generate and explain:
- Spec says "Framework: anthropic SDK" or "Framework: Messages API" — this command is for Tier 3 SDK projects only. Redirect the user to standard `/generate-module` for Tier 1 labs.
- Spec defines `@agent.tool` or `agent.run()` style API — that's not a real API. Point at the cheat sheet in `prompts/19-sdk-tier-policy.md`.
- Spec has no Tools section — there's nothing to generate.
