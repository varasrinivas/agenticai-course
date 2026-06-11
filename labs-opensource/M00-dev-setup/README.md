# M00 Lab: Dev Setup Verification

> Before any agent code, prove your environment works: Python/Node + the `openai` SDK + Ollama serving Mistral-7B locally.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Ollama installed and running (`ollama serve`)
- Mistral pulled (`ollama pull mistral`)
- Dependencies installed:
  ```bash
  pip install openai python-dotenv     # Python
  npm install                          # Node.js (from labs-opensource/ root)
  ```

## Exercises

| Step | File | What You Do | Key Concept |
|------|------|------------|-------------|
| 1 | `check_setup.py` / `check_setup.js` | Run the provided diagnostic (no TODOs) | What a healthy environment looks like |
| 2 | `hello_mistral.py` / `hello_mistral.js` | Make your first local model call | `base_url`, placeholder API key, `chat.completions.create` |

## Step 1: Run the Environment Check

**File:** `starter/check_setup.py` (or `.js`) — this file is **complete**; just run it.

```bash
python starter/check_setup.py
# or
node starter/check_setup.js
```

It verifies, in order:
1. The `openai` package is importable
2. The Ollama server answers on `http://localhost:11434`
3. The `mistral` model is pulled and listed

Every line should print `OK`. If one fails, the script tells you the exact command to fix it. Do not move to Step 2 until all checks pass.

## Step 2: Your First Local Model Call

**File:** `starter/hello_mistral.py` (or `.js`)

You will:
1. Create an `OpenAI` client pointed at Ollama (`base_url="http://localhost:11434/v1"`, `api_key="ollama"`)
2. Call `client.chat.completions.create()` with model `"mistral"`, a system message, and a user message
3. Print the response text and the token usage (`usage.prompt_tokens` / `usage.completion_tokens`)

**Run it:**
```bash
python starter/hello_mistral.py
# or
node starter/hello_mistral.js
```

**Success looks like:** a one-sentence answer from Mistral plus a token count line. Compare with `expected_output/sample_output.txt` (your wording will differ — the *shape* of the output should match).

## Gotchas

- **First call is slow** (10–30s): Ollama loads the 4 GB model into RAM on first use. Subsequent calls are much faster.
- **`api_key="ollama"` is a placeholder** — the SDK requires *some* string, Ollama ignores it. Never put a real key here.
- **Windows**: if `ollama serve` says the port is busy, Ollama is already running as a service — that's fine.
