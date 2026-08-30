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

It does **not** prove a real model answers well. Replies are canned, so a lab
whose point is answer *quality* passes here regardless: M04's extractor
reports 5/5 signatures because the stub hands it well-formed JSON, not because
extraction works. Treat a stub pass as "the plumbing is intact".

**Live** — `ollama pull mistral`, then `--live`. This is what checks the
claims the stub cannot: that the prompts work, that the ReAct loop converges,
that extraction really succeeds. Model text varies between runs, so read it as
"did it complete", not as a diff against the sample.

Between them they still leave the last question open — whether the lab
*teaches* well. No harness reaches that.

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
