# M16 — SDK Solution (hook-based guardrails)

The dual-track companion to `solution/`. Same SSN/PII/injection guardrails, two ways to wire them in.

## What's here

```
solution-sdk/
├── .claude/settings.json     # PreToolUse hooks fire on EVERY tool call
├── hooks/
│   ├── injection_blocker.py  # permissionDecision: deny  → blocks the call
│   └── pii_redactor.py       # updatedInput             → rewrites the input
└── sdk_agent.py              # in-process equivalent using can_use_tool
```

## Two delivery modes for the same guardrails

| | External hook command | In-process callback |
|---|---|---|
| Wired via | `.claude/settings.json` | `ClaudeAgentOptions(can_use_tool=...)` |
| Runs as | a subprocess, per tool call | inside `query()` |
| Sees | the JSON payload on stdin | Python objects directly |
| Block | `permissionDecision: "deny"` (or exit 2) | `PermissionResultDeny(message=...)` |
| Rewrite | `hookSpecificOutput.updatedInput` | `PermissionResultAllow(updated_input=...)` |

**Equal in power.** Both can block and both can rewrite. What differs is where the code runs and how you express the result. Pick the hook when the guardrail must apply to anyone running `claude` in this directory; pick `can_use_tool` when the agent runs as a Python program. Real systems usually want both, pointed at the same implementation.

### The one thing that silently fails either way

Mutating the `tool_input` you were handed does nothing. In both modes the result is read from what you *return*, not from the dict you were given:

```python
# does nothing
for k, v in tool_input.items():
    tool_input[k] = redact(v)
return PermissionResultAllow()

# works
redacted = {k: redact(v) if isinstance(v, str) else v for k, v in tool_input.items()}
return PermissionResultAllow(updated_input=redacted)
```

Same trap in the hook: printing a modified payload to stdout does not sanitize anything. stdout is parsed as a *decision object*, so the redaction has to travel inside `hookSpecificOutput.updatedInput`.

Nothing errors in either failure case. The tool just receives the raw SSN.

The point of M16: **a guardrail belongs at the agent boundary, not inside caller code.** Both wirings here put it at the SDK's tool-dispatch boundary — adding a new agent or a new tool requires zero changes to the guardrail.

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
