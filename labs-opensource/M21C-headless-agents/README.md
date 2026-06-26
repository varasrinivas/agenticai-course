# M21C Lab: Headless Agents

> An agent no one watches. A clock or an event triggers it, it runs to
> completion alone, and it hands a **machine-readable** result to another
> program. With no human in the loop, the contract — JSON on stdout, logs on
> stderr, a meaningful **exit code** — *is* the API. This lab builds a nightly
> log-triage agent end to end against local Mistral.

Companion module: `output/courses/opensource/M21C-headless-agents.html`

## Prerequisites

- M05 (function calling) and M21 (API design & deployment) recommended
- `pip install openai` and Ollama running with `ollama pull mistral`
- `jq` for slicing the JSON output in pipelines (optional but used below)

## Files

| File | Status | What It Is |
|------|--------|------------|
| `starter/triage_agent.py` | **TODOs** | The headless agent: stdin → JSON → exit code, with guardrails |
| `starter/run_triage.sh` | **1 TODO** | Cron wrapper; you wire the exit-code routing |
| `starter/sample.log` | Complete | 10 log lines (mix of INFO/WARN/ERROR) to triage |
| `solution/triage_agent.py` | Complete | Reference Python implementation |
| `solution/triage_agent.js` | Complete | Node.js mirror (same contract) |
| `solution/run_triage.sh` | Complete | Reference cron wrapper with full routing |
| `solution/test_contract.py` | Complete | **No-Ollama** self-test of the contract + exit codes |

> Python is the full lab. `solution/triage_agent.js` is a complete Node mirror
> for the JS track — same stdin→stdout→exit-code contract, `AbortController`
> instead of `signal.alarm`.

## What You Build

A headless agent with four things an interactive agent never needs:

1. **Clean I/O separation** — the JSON result on stdout, *every* log line on
   stderr. The #1 headless bug is mixing them, which breaks the consumer's
   `json.loads()`.
2. **A stable envelope** — every run prints exactly one
   `{"ok", "data", "error", "meta"}` object, so callers parse one shape forever.
3. **An exit-code contract** — the one-integer status channel every scheduler
   already understands:

   | Code | Meaning | Caller should… |
   |------|---------|----------------|
   | `0` | success | consume the JSON, continue |
   | `1` | transient (model down, timeout) | retry later |
   | `2` | bad output (non-JSON / schema fail) | escalate, **do not** retry |
   | `3` | needs review (critical anomaly) | route to a human |

4. **Guardrails that replace the human** — a wall-clock timeout and a token
   budget. Interactively *you* hit Ctrl-C on a runaway; at 02:00 on a cron job,
   nobody is there, so the limits must be code.

## The TODOs (`starter/triage_agent.py`)

1. `log()` writes to **stderr** (keeps stdout pure JSON).
2. Token-budget guard: raise `GuardTripped` when `total_tokens` exceeds the cap.
3. Parse + validate the model's text: bad JSON or a missing key → `BadOutput`.
4. Business rule: any `severity == "critical"` anomaly → `NeedsReview`.
5. `main()`: map each outcome (success / `NeedsReview` / `BadOutput` /
   `GuardTripped` / other) to the envelope + the right exit code.

Plus one TODO in `starter/run_triage.sh`: fill the `case "$CODE"` routing.

## Verify Without Ollama (do this first)

The contract is deterministic, so you can grade it with no model running.
Copy the self-test next to your starter and run it:

```bash
cp solution/test_contract.py starter/
cd starter && python test_contract.py     # exit 0 = all green
```

It stubs the model call and asserts: clean → 0, critical → 3, junk → 2, and
that stdout is always exactly one JSON object.

## Then Run It For Real

```bash
# Pure JSON on stdout (logs suppressed with 2>/dev/null), sliced by jq
cat starter/sample.log | python starter/triage_agent.py 2>/dev/null | jq .

# See the stderr logs AND the result together
cat starter/sample.log | python starter/triage_agent.py

# Drive it the way cron will, and watch the routing + exit code
cd starter && bash run_triage.sh sample.log ; echo "wrapper exit=$?"

# Node mirror (same output shape)
cat starter/sample.log | node solution/triage_agent.js 2>/dev/null | jq .severity
```

The `sample.log` contains a pool-exhaustion + HTTP 500 pair and a burst of
failed admin logins — whether Mistral rates any of them `critical` (exit 3) vs
`high` (exit 0) is a judgment the model makes; both are valid. Drop in a log
with a clear outage to force the exit-3 path.

## Stretch Goals

- **Trip the timeout deliberately.** Set `--max-seconds 1` on a large log and
  confirm the agent exits non-zero *without hanging* — then confirm the outer
  `timeout --signal=KILL` in the wrapper catches a fully wedged process.
- **Chain two agents.** Pipe the high-severity summaries into a second headless
  agent that drafts an incident note: `... | python draft_agent.py | jq -r .draft`.
- **Put it in CI.** Add a GitHub Actions job that installs Ollama, pulls
  mistral, runs the agent on `git log -1`, and gates the build with
  `jq -e '.data.clean == true'` (see the module's CI section).
- **Idempotency.** Hash the input log; if the same content was already triaged
  today, return the cached envelope and exit 0 without calling the model.
