# Claude-course lab harness

Runs the lab solutions that call the Anthropic API, against a local stub by
default so a full pass is free and repeatable.

```bash
python labs/harness/run_labs.py            # stub — free, deterministic
python labs/harness/run_labs.py --live     # real API — SPENDS MONEY
python labs/harness/run_labs.py --only M05
```

Exit status is non-zero if anything fails, so it drops into CI unchanged.

## Why this is separate from labs-opensource/harness

That harness discovers its work from the `$ python solution/x.py` lines the
Ollama course puts at the top of each `expected_output` block. **This course's
samples are not that shape** — they are transcripts of an interactive agent
session — so that discovery finds nothing here, and the Ollama harness never
covered these labs at all. Its "45 of 46 pass" was always a statement about the
Ollama course only.

Work is discovered by scanning instead: `solution/*.py` that import `anthropic`
and have a `__main__` block.

## Why a stub, and what it is worth

The Ollama course could be verified for free because its model runs locally.
This one cannot: the labs call a paid API, so every run costs money and returns
something different. That is a poor fit for a check you want to run on every
change, and it is why these scripts stayed unverified while the Ollama ones did
not.

Every lab builds its client as a bare `anthropic.Anthropic()`, which reads
`ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from the environment — so pointing
the whole course at a local stub needs **no proxy and no edits to any lab**.
Without `--live`, the key is also replaced with a dummy, so a real key sitting
in the environment cannot be spent by a run that never meant to spend it.

A stub pass means: valid requests, a working tool-use round trip, correct
reading of content blocks and `stop_reason`, and completion. It means nothing
about answer quality. Labs whose subject *is* the answer — evals, judges,
guardrail decisions — are only truly checked under `--live`.

### The stub reads each prompt's requested shape

Canned replies are not enough on their own. M10 asks for "ONLY a JSON array of
3 strings" and then does `[query, hyde] + parsed`; M13 asks for "a JSON array of
step objects" and calls `step.get(...)`. Hand either one the other's shape and
it fails one line after a clean `json.loads` — which reads exactly like a lab
bug and is not one. So the stub parses the field list out of the prompt
(`- "step_id": string like "step_1"`) and answers in the shape that was asked
for. Tool arguments are likewise synthesised from each tool's `input_schema`,
honouring enums and types, so tools take their real branch instead of their
error branch.

That heuristic has limits. If you add a lab that parses a new structure, expect
to teach the stub about it — or run that lab under `--live`.

## Results, 2026-08-31 (stub)

**37 passed, 2 failed, 8 skipped, 47 total.**

- **8 skipped** read stdin and cannot run unattended. They are reported, never
  silently dropped, so the count never overstates what was exercised.
- **2 failed** are `capstone-9` and `M26`, which drive `claude-agent-sdk`. The
  stub does not implement streaming and says so rather than returning a body the
  SDK would mis-parse. Both also need a native Claude Code binary — the SDK
  refuses the npm `.CMD` shim on Windows — so they are not stub-verifiable at
  all and need `--live` plus a native install.

Three real defects were fixed on the way to that number; all three were version
drift that no amount of reading would have caught:

1. **`anthropic>=0.39.0` installs 1.x today**, which removed `temperature` from
   `messages.create()`. That breaks `M01/temperature_lab.py` outright — a lab
   whose entire subject is temperature. Pinned `<1.0`; migrating is a content
   change, not a pin change.
2. **`claude-agent-sdk` was imported by six labs and declared by none**, so
   students installed whatever pip resolved that day. Now pinned.
3. **`hooks=[HookMatcher(...)]` no longer works** — the SDK takes a dict keyed
   by event. The course already used the dict form in M15B, M26 and capstone-4;
   the capstone-8, 8b and 9 coordinators had been left behind. Migrated to
   `{"PostToolUse": [...]}`, the event those labs' own docstrings name.

## Setup

```bash
python -m venv labs/.venv
labs/.venv/Scripts/activate      # macOS/Linux: source labs/.venv/bin/activate
pip install -r labs/requirements.txt
```

The pins in `labs/requirements.txt` carry comments explaining why the ceilings
are there. They are not incidental — two of the three defects above were an
unbounded `>=` quietly installing a new major version.
