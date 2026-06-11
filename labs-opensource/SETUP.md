# Environment Setup Guide — Open Source Track

## Prerequisites

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Ollama | 0.3+ | `ollama --version` |
| RAM | 8 GB (16 GB recommended) | — |
| Disk | ~5 GB free for Mistral-7B | — |

You need **either** Python or Node.js — both are optional if you only work in one language. Ollama is required for everything.

## 1. Install Ollama

### Windows
Download and run the installer from [ollama.com/download](https://ollama.com/download). Ollama starts automatically as a background service.

### macOS
```bash
brew install ollama
ollama serve &        # or use the macOS app, which runs it for you
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
```

### Pull Mistral-7B (all platforms)

```bash
# ~4.1 GB download — do this on a good connection
ollama pull mistral

# Verify
ollama list                              # should show mistral:latest
ollama run mistral "Say hello in one sentence."
curl http://localhost:11434/api/tags     # should return JSON with model info
```

**Performance note**: On a machine without a GPU, Mistral-7B generates roughly 5–15 tokens/second on CPU. Responses take longer than a hosted API — that's normal. With an NVIDIA GPU (CUDA) or Apple Silicon, expect 30–80 tokens/second.

## 2. Python Setup

```bash
# Verify Python version (3.10+ required)
python --version

# Create and activate a virtual environment
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify
python -c "import openai; print(f'openai SDK v{openai.__version__}')"
```

### Python Dependencies Explained

| Package | Purpose | Used In |
|---------|---------|---------|
| `openai` | OpenAI-compatible client (points at Ollama) | All modules |
| `python-dotenv` | Load `.env` files | All modules |
| `pydantic` | Schema validation for structured output | M04+ |
| `tiktoken` | Token counting (cl100k_base ≈ Mistral) | M02, M03B |
| `crewai` | Agent framework (Approach 2) | M00B only |
| `langchain` + `langchain-community` | Agent framework (Approach 3) | M00B only |
| `transformers` | Exact Mistral tokenizer comparison (optional) | M02 stretch |

> **Tip**: `crewai`, `langchain`, and `transformers` are only needed for M00B and the M02 stretch goal. If installation is slow, comment them out of `requirements.txt` and install later.

## 3. Node.js Setup

```bash
# Verify Node version (18+ required)
node --version

# Install dependencies (from the labs-opensource/ root)
npm install

# Verify
npm run verify
```

### Node Dependencies Explained

| Package | Purpose | Used In |
|---------|---------|---------|
| `openai` | OpenAI-compatible client (points at Ollama) | All modules |
| `dotenv` | Load `.env` files | All modules |
| `zod` | Schema validation for structured output | M04+ |
| `js-tiktoken` | Token counting | M02, M03B |
| `langchain`, `@langchain/ollama`, `@langchain/core` | Agent framework | M00B only |

> CrewAI has no official JavaScript package — the M00B CrewAI exercise is Python-only (the lab README shows the equivalent hand-rolled JS pattern).

## 4. No API Key Needed (Mostly)

Ollama ignores the API key — the SDK just requires *something*, so all labs use the placeholder `api_key="ollama"`. The `.env.example` file only contains **optional** keys:

- `GROQ_API_KEY` — if your machine is too slow for local inference, [Groq's free tier](https://console.groq.com) serves open models at high speed. Point the client at `https://api.groq.com/openai/v1` and use model `mixtral-8x7b-32768` or similar.
- `TOGETHER_API_KEY` — same idea via [Together AI](https://together.ai).

Every lab works unchanged with these hosted alternatives: only `base_url`, `api_key`, and `model` change.

## 5. Smoke Test

From the repo root:

```bash
cd M00-dev-setup
python starter/check_setup.py    # or: node starter/check_setup.js
```

All checks should print `OK`. If not, the script tells you exactly what to fix.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` / `ECONNREFUSED` on port 11434 | Ollama not running | `ollama serve` (or start the Ollama app) |
| `model "mistral" not found` | Model not pulled | `ollama pull mistral` |
| Very slow first response | Model loading into RAM (cold start) | Normal — first call after `ollama serve` takes 10–30s |
| Out-of-memory / system freeze | Not enough RAM for 7B model | Close apps, or use `ollama pull mistral:7b-instruct-q4_0` (smaller quantization) |
| `ModuleNotFoundError: openai` | venv not activated | Activate venv, re-run `pip install -r requirements.txt` |
| Tool calls never happen (M04/M05) | Older Ollama without tool support | Update Ollama to 0.3.0+ (`ollama --version`) |
