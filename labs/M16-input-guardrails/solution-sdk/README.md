# M16 — SDK Solution (hook-based guardrails)

The dual-track companion to `solution/`. Same SSN/PII/injection guardrails, two ways to wire them in.

## What's here

```
solution-sdk/
├── .claude/settings.json     # PreToolUse hooks fire on EVERY tool call
├── hooks/
│   ├── injection_blocker.py  # exits non-zero on injection patterns → blocks the call
│   └── pii_redactor.py       # rewrites tool_input with PII redacted
└── sdk_agent.py              # in-process equivalent using can_use_tool
```

## Two delivery modes for the same guardrails

| Mode | Wired via | When it fires | Used in |
|---|---|---|---|
| **External hook command** | `.claude/settings.json` PreToolUse `command` | Claude Code subprocess execution before each tool call | Any agent run via Claude Code, regardless of caller |
| **In-process callback** | `ClaudeAgentOptions(can_use_tool=...)` | Synchronously inside `query()` | Programs running `query()` directly without Claude Code |

The point of M16: **a guardrail belongs at the agent boundary, not inside caller code.** Both wirings here put the guardrail at the SDK's tool-dispatch boundary — adding a new agent or a new tool requires zero changes to the guardrail.

## Run

```powershell
pip install claude-agent-sdk
$env:ANTHROPIC_API_KEY = "sk-..."
python sdk_agent.py
```

Three test cases run automatically:
1. Clean input → tool succeeds
2. Input containing an SSN → PII is redacted before the tool sees it
3. Prompt injection attempt → `PermissionResultDeny` returned, tool not called
