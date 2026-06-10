# M28: Open Source Models — Running Agents Without an API Key

**Track**: Supplementary / Extensions | **Position**: Appendix (after M27B) | **Level**: Beginner → Intermediate
**Prerequisites**: M01 (required), M12 (recommended)
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-foundations) / #6366F1 (reuse Foundations palette)

## Why This Module Exists

The main curriculum uses Claude via the Anthropic API. That's intentional — this course prepares you for the Claude Certified Architect exam, and Claude-specific features (extended thinking, computer use, prompt caching, hooks) have no open-source equivalent.

But open source matters for three real reasons:
1. **Cost** — Mistral-7B and similar models are free to self-host; for high-volume or batch workloads the math changes dramatically
2. **Data privacy** — some organizations cannot send data to a third-party API (healthcare, finance, government)
3. **Portability** — knowing how to swap providers teaches you which parts of your agent are model-specific vs. model-agnostic

This module teaches the provider-swap skill: same agent, different backbone.

---

## Concepts to Cover

### 1. The LLM Provider Landscape (No API Key Required)
- **Ollama** — local inference on CPU/GPU, zero API cost, runs Mistral, Llama, Gemma, Phi and 100+ models
  - Analogy: "Docker for LLMs — one `ollama pull mistral` and you have a model running locally, same as `docker pull nginx`"
  - Animation: OLLAMA_INSTALL — show `ollama pull mistral` → model download progress bar → local server ready
- **LM Studio** — GUI wrapper around llama.cpp, good for Windows learners who prefer a desktop app
- **Groq / Together AI / Fireworks** — hosted open source inference, fast, cheap, no GPU needed
  - Use these when local hardware is insufficient
- **Hugging Face Inference API** — free tier for smaller models, scales to paid

When to use what (decision matrix visual):
| Situation | Recommended |
|-----------|-------------|
| Laptop dev, data privacy | Ollama |
| No GPU, need speed | Groq |
| Experimenting with many models | Together AI |
| Production, cost control | Claude + prompt caching |

### 2. The OpenAI-Compatible API: The Universal Adapter
- Key insight: Most open source inference servers (Ollama, Together, Groq, LM Studio) implement the **OpenAI Chat Completions API** schema — NOT the Anthropic Messages API
  - Animated: side-by-side JSON diff of Anthropic Messages vs. OpenAI Chat Completions format
- Two swap strategies:
  - **Strategy A: LiteLLM** — wraps any provider behind a single unified API; one config change swaps providers
  - **Strategy B: OpenAI SDK** — use the `openai` Python/JS package pointed at `http://localhost:11434/v1` (Ollama's endpoint)
- Both Python and Node.js examples for each strategy

### 3. Running Mistral-7B Locally with Ollama
- Installation: `brew install ollama` / Windows installer / `curl` script
- Pull and run: `ollama pull mistral` → `ollama run mistral` (interactive) → `ollama serve` (API mode)
- Hardware reality check: Mistral-7B needs ~5GB RAM in 4-bit quantization; mention 13B and 70B requirements too
- Animation: HARDWARE_METER — show RAM/VRAM gauge as model size increases; green zone / yellow zone / red zone
- Making your first call to Ollama via HTTP (curl), then Python, then Node.js

### 4. Provider Swap: Claude → Mistral-7B (Side-by-Side Code)
Show the SAME agent (the CLI chat from M01 Step 5) running against both providers with a one-line swap.

Both Python AND Node.js, side by side:
- **Claude version**: `anthropic.Anthropic()` + `client.messages.create(model="claude-sonnet-4-6", ...)`
- **Ollama version**: `openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")` + `client.chat.completions.create(model="mistral", ...)`
- **LiteLLM version**: `litellm.completion(model="ollama/mistral", messages=...)` — same call, any provider

Key gotchas to annotate:
- `content[0].text` (Anthropic) vs `choices[0].message.content` (OpenAI schema)
- Anthropic has `system` as a top-level param; OpenAI uses a `{"role": "system", ...}` message
- `max_tokens` is required by Anthropic; optional in OpenAI schema (defaults to model max)

### 5. What Doesn't Port Over
Be honest about the gaps — this sets correct expectations:
- **Prompt caching** — Anthropic-only; no equivalent in Ollama
- **Extended thinking** — Claude-specific reasoning mode
- **Computer use** — Claude-specific tool
- **Claude Code / hooks** — Anthropic Agent SDK is Claude-specific
- **Quality gap** — Mistral-7B is 7B parameters; Claude Sonnet is a frontier model. For agentic tasks requiring multi-step reasoning, tool chaining, or complex instruction following, the quality difference is significant.
- **Context window** — Mistral-7B default context is 32K; Claude Sonnet is 200K

Use this as a teaching moment: most of this course's techniques (RAG, ReAct, guardrails, tracing) ARE model-agnostic. The Claude-specific modules are M25-M27 (cert prep) and the Agent SDK modules.

### 6. When to Use Open Source in Production
- Use Claude for: agentic tasks, complex reasoning, cert prep, hooks/sessions, production reliability
- Use open source for: batch/offline processing, privacy-sensitive data, cost reduction on simple classification/extraction tasks, fine-tuning on proprietary data
- Hybrid routing pattern: cheap open source model for intent classification → Claude for complex reasoning (preview M22's model routing section)

---

## Code Walkthrough
Three working examples, all complete and runnable:

1. **`ollama_hello.py` / `ollama_hello.mjs`** — Basic call to Mistral-7B via Ollama using the OpenAI SDK
2. **`litellm_swap.py`** — Same prompt sent to Claude AND Mistral-7B using LiteLLM, outputs compared side by side
3. **`provider_agnostic_chat.py` / `provider_agnostic_chat.mjs`** — The M01 CLI chat refactored to accept `--provider claude|mistral|groq` flag

All three include:
- Error handling (model not running, API key missing, connection refused)
- Environment variable setup (`ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `OLLAMA_HOST`)
- `requirements.txt` / `package.json` snippets

---

## Hands-On Exercise

### Step 1: Install Ollama and Pull Mistral-7B
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral

# Windows: download installer from https://ollama.ai
# Then in PowerShell:
ollama pull mistral
```

### Step 2: Your First Ollama API Call
Run `ollama_hello.py` — sends "Explain what a language model is in one sentence" to local Mistral-7B

### Step 3: Side-by-Side Comparison
Run `litellm_swap.py` — sends the same prompt to both Claude and Mistral-7B, prints both responses and token counts side by side

### Step 4: Provider-Agnostic CLI Chat
Run `provider_agnostic_chat.py --provider mistral` — same multi-turn chat from M01 Step 5, now powered by a local model

### Stretch Goal: Try Groq (Cloud Speed)
Sign up for free Groq API key → set `GROQ_API_KEY` → run `litellm_swap.py --provider groq/mistral-saba-v1` and compare latency vs. Ollama local

---

## Animations Required
1. **OLLAMA_INSTALL** — animated terminal showing pull progress + server startup (CSS-animated progress bar + status dots)
2. **API_DIFF** — side-by-side animated diff of Anthropic Messages API vs. OpenAI Chat Completions JSON format
3. **HARDWARE_METER** — RAM/VRAM gauge showing model size requirements (7B / 13B / 70B)

---

## Quiz Focus (5 questions)
1. Which open source inference server implements the OpenAI Chat Completions API format? (Ollama — and also LM Studio, Together, Groq)
2. What is the main code difference between calling Claude and calling Ollama? (SDK/client init + response path: `content[0].text` vs `choices[0].message.content`)
3. Name two reasons to prefer open source models over Claude in production. (cost, data privacy, fine-tuning control, offline operation)
4. What Claude feature has NO open-source equivalent? (any of: extended thinking, computer use, hooks/sessions, prompt caching)
5. What does LiteLLM do? (provides a unified API wrapper that routes to any LLM provider with a single function call)

---

## Sidebar Nav Sections
- Why Open Source?
- The Provider Landscape
- OpenAI-Compatible API
- Ollama Setup
- Provider Swap: Code
- What Doesn't Port
- When to Use Each
- Hands-On Lab
- Quiz

---

## Notes for Generator
- This is **NOT** a cert prep module — no cert tip callouts needed
- SDK Tier: **Tier 1** for Claude examples (raw Messages API); OpenAI SDK for Ollama examples (that's the correct tool for the job, not a workaround)
- Do NOT simulate the Anthropic Agent SDK with raw API calls
- Progress bar should show "Appendix Module" not a numbered position
- Add a note at the top: "This module is optional supplementary content. It is not required for the Claude Certified Architect exam."
- Previous module: M27B | Next module: (none — end of curriculum)
