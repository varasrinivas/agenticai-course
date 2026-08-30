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

## Results, 2026-08-30

Two runs, kept in two logs on purpose. They answer different questions and
merging them into one number would overstate both.

| run | model | covered | result |
|---|---|---|---|
| `results-live.txt` | `mistral:latest` 7B, local CPU | 23 of 46 | 22 pass, 0 fail |
| `results-cloud-gptoss.txt` | `gpt-oss:20b-cloud` via `cloud_proxy.py` | **46 of 46** | **45 pass, 0 fail** |

Both also record M03B's starter failing by design.

**Every lab in this course runs to completion against a real LLM.** That is the
cloud row, and it is a statement about the code: requests are well-formed, the
tool-call round trips work, replies parse, the loops terminate.

**About half are confirmed on the model the course actually ships.** That is the
mistral row, and it is the stronger claim, because the labs hardcode
`model="mistral"` and a 20B model clears prompts a 7B one may not. The gap is
not a defect; it is CPU inference at ~40s per call versus ~1.3s on cloud. The
remaining 23 finish overnight on the shipped model, or in minutes on a GPU:

```bash
python harness/run_labs.py --live --resume        # picks up where it left off
```

### Two failures that were the harness, not the labs

`M09-rag/solution/rag_pipeline.py` was reported FAIL twice, and was fine both
times. Worth reading before trusting any red result here:

1. It timed out at 900s while ChromaDB downloaded its embedding model on first
   use — a one-time cost that happened to land inside the timed run.
2. It then hung with *no output at all*, because `cloud_proxy.py` was a
   single-threaded server speaking HTTP/1.1. Clients hold keep-alive connections
   open between calls, so the second connection waited behind the first forever.
   `ThreadingHTTPServer` took it from a 900s hang to a 34s pass.

The tell was inconsistency: it completed once, then hung completely. A lab that
is genuinely broken does not alternate. When a red result cannot be reproduced,
suspect the measurement before the lab.

## Live run detail, 2026-08-30

Ollama 0.33.2, `mistral:latest` (7.2B, Q4, 4.4 GB), CPU only. 48 minutes of
model time for 23 scripts — the reason the cloud proxy exists.

Covered: CAPSTONE-C3, M00, M00B (all three frameworks), M01, M02, M03, M04,
M05, M06, M08's `conversation_manager`.

The claim worth singling out: `M04/extractor.py` reports **5/5 extracted**
against real mistral, matching its committed sample name for name, where the
stub reports 0/5. One lab, one line, showing why the modes are not redundant.

Not covered *on mistral*: M09–M22 — the multi-call labs (ReAct, planning
decomposition, multi-agent, guardrails, the LLM judge). All of them pass against
`gpt-oss:20b-cloud`, so their code is sound; what is untested is whether a 7B
model holds up where a 20B one does. Strict JSON, tool-call formatting and loop
termination are where that difference shows, and those are exactly what these
labs exercise — so treat them as code-verified but not shipped-config verified.

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
