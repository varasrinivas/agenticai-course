# Lab harness

Runs every script this course's `expected_output/sample_output.txt` files
declare, and reports which ones still work.

The samples open each block with the command that produced it —
`$ python solution/extractor.py` — so the samples themselves are the list of
things worth running. Nothing here needs to be kept in sync by hand: add a lab
with a sample, and it is covered.

```bash
python harness/run_labs.py            # stub model, deterministic, no download
python harness/run_labs.py --live     # real Ollama on :11434
python harness/run_labs.py --only M04 # substring filter
```

Exit status is non-zero if anything fails, so it drops into CI unchanged.

## Why a stub

Every lab in this course reaches its model through one line:

```python
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
```

That is Ollama on localhost — no key, no cost. `api_key="ollama"` is a
placeholder the OpenAI client insists on. One stub on that port therefore
covers every lab at once.

`fake_ollama.py` answers both dialects Ollama speaks, because the labs use
both:

| endpoint | used by | response shape |
|---|---|---|
| `/v1/chat/completions` | the `openai` client | `choices[].message` |
| `/api/chat` | `langchain-ollama`, the `ollama` package | a single `message`, NDJSON when streaming |

Answering the native path in OpenAI shape produces a pydantic
`ValidationError` *inside the lab*, which reads like a lab bug. It is not; it
is the stub being wrong. If you extend the stub, keep the two dialects apart.

## What each mode proves

**Stub** — the lab imports, builds a well-formed request, survives the
tool-call round trip, parses the reply, and reaches the end of its own demo.
Deterministic and free, so it is worth running on every change.

It does **not** prove a real model answers well, and M04 shows exactly how far
a stub pass is from a correct lab. Run `extractor.py` under the stub and it
exits 0 — so the harness reports `PASS` — while printing:

```
Results: 0/5 extracted successfully
```

against a committed sample that says 5/5. The stub returns the same canned
record for every signature, so the extraction genuinely fails; the script has
no assertion on that count, so it exits 0 anyway. `PASS` here means "ran to
completion", nothing more. Read the output, not just the status, and use
`--live` for anything whose point is answer quality.

**Live** — `ollama pull mistral`, then `--live`. This is what checks the
claims the stub cannot: that the prompts work, that the ReAct loop converges,
that extraction really succeeds. Model text varies between runs, so read it as
"did it complete", not as a diff against the sample.

Between them they still leave the last question open — whether the lab
*teaches* well. No harness reaches that.

## Live run, 2026-08-30

23 of the 46 declared scripts have been run against a real model — Ollama
0.33.2, `mistral:latest` (7.2B, Q4, 4.4 GB), CPU only. **22 passed, 0 failed**,
plus M03B's starter failing by design. 48 minutes of model time.

Covered: CAPSTONE-C3, M00, M00B (all three frameworks), M01, M02, M03, M04,
M05, M06, M08's `conversation_manager`.

The claim worth singling out: `M04/extractor.py` reports **5/5 extracted**
against the real model, matching its committed sample name for name, where the
stub reports 0/5. That is the difference between the two modes in one line.

Not yet covered: M09–M22. Those are the multi-call labs — the ReAct loop,
planning decomposition, the multi-agent pipeline, guardrails, the LLM judge —
so they are both the slowest and the ones most likely to behave differently
against a real model than against canned replies. Treat them as unverified.

### Why it stops there, and what it needs

This machine has no GPU Ollama can use. The server log reads:

```
inference compute id=cpu library=cpu ... total="15.9 GiB"
vram-based default context total_vram="0 B"
```

so every token is CPU-generated: roughly 40s per model call, and
`M06/research_agent.py` alone took 702s. On hardware with a supported GPU the
whole sweep is a single unattended command:

```bash
python harness/run_labs.py --live --resume --timeout 1800
```

`--resume` exists precisely because that is not true on CPU: the sweep has to
be walked forward in batches, and anything already recorded is skipped.

## Reading the output

- `PASS` — ran to completion, exit 0
- `TODO` — a starter that fails until the reader implements its TODOs. Expected.
  Listed in `EXPECTED_FAILURES` in `run_labs.py` so a designed failure never
  reads as a defect; add to it when you add a starter that cannot run as shipped.
- `FAIL` — everything else, with the last line of the error

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Version pins matter here and are commented in `requirements.txt`: LangChain 1.x
removed the agent API M00B teaches, and `ChatOllama` moved out of
`langchain-community` into `langchain-ollama`. Both were caught by this harness.
