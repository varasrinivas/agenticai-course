# SDK Behavior Tests — Capstone 4-A Communication Agent

This sub-lab uses the **Claude Agent SDK** to verify that the Communication
agent (built in `solution/pipeline.py`) behaves correctly under realistic
test scenarios. It is the practical companion to the *Agent SDK Port*
stretch goal in the Capstone 5-A HTML.

## What's the Point?

The capstone teaches you to build the tool-use loop manually so you
understand `tool_use`/`tool_result`, `stop_reason`, circuit breakers, and
HITL routing. Once that's clear, the SDK becomes useful as a **testing
and safety layer**: hooks let you assert on tool ordering, the
`can_use_tool` callback lets you block or rewrite tool calls, and the
event stream is easy to capture for replay tests.

This lab demonstrates two patterns:

| File | Pattern | What it proves |
|---|---|---|
| `test_tool_order.py` | `PreToolUse` hooks | The agent calls `check_hipaa_compliance` BEFORE `send_notification` (and `draft_determination_letter` before HIPAA check) |
| `test_safety_gate.py` | `can_use_tool` callback | Sending to a production channel is denied in dev; the gate can also transparently rewrite tool inputs |

## Files

```
sdk_tests/
├── README.md                      # This file
├── requirements.txt               # SDK + pytest deps
├── pytest.ini                     # asyncio_mode=auto so async tests just work
├── sdk_communication_agent.py     # SDK port of the Communication agent
├── test_tool_order.py             # 2 tests — hook-based ordering assertions
├── test_safety_gate.py            # 3 tests — can_use_tool callback gates
└── expected_output/
    └── test_run.txt               # Reference pytest output
```

## Setup

You need the capstone solution in place. From the capstone-4-A folder:

```bash
# 1. Activate your venv (created in the main capstone setup)
# Linux/macOS:    source venv/bin/activate
# Windows PS:     venv\Scripts\Activate.ps1

# 2. Install the SDK + pytest extras
pip install -r sdk_tests/requirements.txt

# 3. Make sure the API key is set
# Linux/macOS:    export ANTHROPIC_API_KEY=...
# Windows PS:     $env:ANTHROPIC_API_KEY = "..."
```

## Running the Tests

From the `domain-a-healthcare/` folder (so `sdk_tests/` and `solution/`
are siblings):

```bash
cd sdk_tests
pytest -v
```

Expected output (compare to `expected_output/test_run.txt`):

```
test_safety_gate.py::test_production_channel_blocked PASSED
test_safety_gate.py::test_test_channel_allowed PASSED
test_safety_gate.py::test_input_mutation_via_gate PASSED
test_tool_order.py::test_hipaa_check_runs_before_send PASSED
test_tool_order.py::test_draft_runs_before_hipaa_check PASSED

5 passed in ~30s
```

> Each test makes a real API call (~$0.001 per test on Haiku). Total
> cost for the suite: less than $0.01 per run.

## How the Tests Work

### `test_tool_order.py` — Hook-based assertions

The `PreToolUse` hook fires *before* every tool call. We use it to:

1. **Record** every tool name in a `calls` list (turning the run into something we can assert on).
2. **Block** `send_notification` if `check_hipaa_compliance` hasn't been called yet — preventing the bug we're testing for.

```python
async def hook(input_data, tool_use_id, context):
    name = input_data.get("tool_name", "")
    calls.append(name)
    if name == "mcp__comms__send_notification":
        if "mcp__comms__check_hipaa_compliance" not in calls:
            return {"decision": "block", "reason": "..."}
    return {}
```

The hook is attached via `ClaudeAgentOptions.hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[hook])]}`.

### `test_safety_gate.py` — `can_use_tool` callback

This is a separate API from hooks: it's a per-tool-call permission check
that returns either `PermissionResultAllow(updated_input=...)` or
`PermissionResultDeny(message=...)`. Three tests:

- `test_production_channel_blocked` — gate denies `channel="portal"` (production)
- `test_test_channel_allowed` — gate allows `channel="portal_test"`
- `test_input_mutation_via_gate` — gate transparently rewrites `portal` → `portal_test` (the agent never sees the deny)

The third test is the most useful pattern in production: a single safety
layer that mutates tool inputs to enforce environment-specific rules
without changing the agent's prompt.

## When You Would Add These Patterns to a Real System

| Pattern | Use case |
|---|---|
| `PreToolUse` ordering hook | Compliance-critical tool sequences (HIPAA check, PCI tokenization, audit log writes) |
| `PreToolUse` blocking hook | Tool-call frequency caps, cost ceilings, rate limits |
| `can_use_tool` deny | Environment gates (no prod sends from staging), high-value action confirmation |
| `can_use_tool` rewrite | Force test channels, redact PII from arguments before logging, route to mocks in CI |

Both patterns are runtime — they don't change the agent's prompt — so
they're additive to the manual loop you already built.

## Troubleshooting

- **`ModuleNotFoundError: claude_agent_sdk`** — install the SDK: `pip install claude-agent-sdk`
- **`ModuleNotFoundError: mock_tools`** — run pytest from `sdk_tests/` (the agent file adds `../solution/` to `sys.path`)
- **`pytest: error: unrecognized arguments: --asyncio-mode`** — old pytest-asyncio; upgrade with `pip install -U pytest-asyncio`
- **Tests pass but spend more than $0.10** — model is wrong; ensure `model="claude-haiku-4-5-20251001"` in `sdk_communication_agent.py`
- **`test_hipaa_check_runs_before_send` fails on first run** — Haiku occasionally skips the explicit HIPAA check despite the system prompt. Re-run; if it fails consistently, tighten the system prompt or upgrade to Sonnet for this test.

## Going Further

- Add a **golden trace test**: capture the event stream once, save it as JSON, then write a regression test that asserts subsequent runs produce the same shape (modulo timestamps and IDs).
- Add a **cost ceiling hook** that tallies token usage from `ResultMessage` events and aborts if estimated cost exceeds a threshold.
- Port the **Decision agent** to the SDK and write tests asserting that low-confidence cases trigger HITL routing.
