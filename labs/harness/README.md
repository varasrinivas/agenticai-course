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

## Results, 2026-08-31 (live, real API)

One full pass against the real Anthropic API before the account's $5 balance
ran out. **33 passed, 1 WARN, 5 failed, 8 skipped.**

It found four defects no stub could have, all since fixed:

* **M03's prefill lesson had never worked.** The prefill literal ends in a
  newline and the API rejects a final assistant message ending in whitespace.
  Fixing that exposed the real problem: `claude-sonnet-4-6` does not support
  assistant prefill at all. Call 3 now uses a model that does.
* **M01's multimodal image URL was dead**, and URLs were the wrong mechanism:
  the API fetches the image itself, so the lab depended on a third party
  serving that path to Anthropic's fetcher. Now base64 from a PNG shipped with
  the lab.
* **`claude-3-5-haiku-20241022` is retired** and 404s; it appeared in five M22
  files.
* A solution too broken to parse was **silently dropped from discovery** rather
  than failing.

Still unresolved: `M08/auto_summarize`, `M13/planning_agent`,
`M14/multi_agent` and `capstone-9/coordinator` exceeded a 300s timeout. Real
inference is far slower than canned replies, so these are *probably* the
timeout being too tight rather than defects — but that has not been confirmed,
and should not be assumed. Re-run those four with `--timeout 900` on a funded
account.

### On budget, and why a green run can be worthless

The second full sweep reported 22 failures and 13 WARNs. **None of them were
lab defects.** The balance had run out, and every script was returning
"Your credit balance is too low". The run said nothing about the labs at all.

Pre-flight cannot prevent this: a four-token probe still fits in the last few
cents. So the harness now aborts the whole sweep the moment it sees that error,
rather than converting one budget problem into a page of red that reads like
forty.

That is the same principle as the WARN check, in the other direction. Both
exist because the expensive failure here is not a lab that breaks — it is a run
that *looks* like it measured something.

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

## The JavaScript labs

The course ships a `.js` beside almost every `.py`, and until 2026-08-31 none of
it had ever been run. The JS SDK reads `ANTHROPIC_BASE_URL` exactly like the
Python one, so the same stub covers both languages; the harness discovers
`solution/*.js` alongside `solution/*.py`.

**Stub run: 91 of 93 pass** (47 Python + 46 JavaScript). The two failures are
`capstone-9` and `M26` — see below.

Four defect classes were found the first time these ran, none of which reading
would have caught:

1. **ESM cannot import a Windows path.** `await import(join(__dirname, ...))`
   hands the loader a filesystem path. Posix paths happen to work; a Windows one
   is read as protocol `d:` and rejected with `ERR_UNSUPPORTED_ESM_URL_SCHEME`.
   M12–M15 were dead on arrival for every Windows reader — solutions *and*
   starters. Fixed with `pathToFileURL(...).href`.
2. **CommonJS under `"type": "module"`.** M18 and M22 used `require` /
   `module.exports`, which node refuses outright when the governing manifest
   declares `"type": "module"`. Converted to ESM, which is what the rest of the
   course already uses.

   **M21 and M22B are NOT affected, and must not be "fixed".** Both ship their
   own `solution/package.json` with no `type` field, so those directories
   default to CommonJS and their `require` is correct. A nested manifest
   overrides the parent — which is easy to miss, because the files look
   identical to the broken ones. I converted them before noticing and had to
   revert. If a JS lab uses `require`, check for a nearer `package.json` before
   concluding anything.
3. **`readline` used after close.** capstone-1's agents recurse `askQuestion()`
   after each turn; when stdin ends mid-request the recursive call throws
   `ERR_USE_AFTER_CLOSE`. Interactive typing never hits it, redirected input
   always does.
4. **Undeclared npm dependencies** — 8 in `labs/`, 4 in `labs-opensource/`
   (`chromadb`, `chromadb-default-embed`, `express`, `cors`, `uuid`,
   `gpt-tokenizer`, `serverless-http`, `@modelcontextprotocol/sdk`). Imported by
   labs, declared by neither manifest, so `npm install` produced a tree that
   could not run the RAG, MCP, API or deployment labs at all.

### The JS RAG labs need a Chroma server

Python's `chromadb.Client()` is in-memory. The JavaScript `ChromaClient()` is an
HTTP client with no embedded mode, so M10, M11 and capstone-2's JS variants need
a server before they will run at all:

```bash
chroma run --path ./chroma-data --port 8000    # labs/.venv/Scripts/chroma.exe
```

This is a real asymmetry between the two languages, not a bug, and it was
previously undocumented — the labs failed with a bare `ChromaConnectionError`.

## Setup

```bash
python -m venv labs/.venv
labs/.venv/Scripts/activate      # macOS/Linux: source labs/.venv/bin/activate
pip install -r labs/requirements.txt
```

The pins in `labs/requirements.txt` carry comments explaining why the ceilings
are there. They are not incidental — two of the three defects above were an
unbounded `>=` quietly installing a new major version.
