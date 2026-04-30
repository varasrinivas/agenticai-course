# Environment Setup Guide

## Prerequisites

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| pip | 22+ | `pip --version` |
| Git | 2.30+ | `git --version` |
| Docker | 24+ (M22B only) | `docker --version` |

You need **either** Python or Node.js — both are optional if you only work in one language.

## 1. Python Setup

```bash
# Verify Python version (3.10+ required)
python --version

# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows (cmd):
venv\Scripts\activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print(f'anthropic SDK v{anthropic.__version__}')"
```

### Python Dependencies Explained

| Package | Purpose | Used In |
|---------|---------|---------|
| `anthropic` | Claude API client | All modules |
| `python-dotenv` | Load `.env` files | All modules |
| `pydantic` | Data validation & structured output | M04+, capstones |
| `tiktoken` | Token counting (OpenAI-compatible tokenizer) | M02 |
| `numpy` | Numerical operations, cosine similarity | M09-M11 (RAG) |
| `chromadb` | Vector database for embeddings | M09-M11 (RAG) |
| `pyspark` | Data pipeline processing | Capstone 5-6 (Domain C) |
| `pytest` | Test framework | M18, capstones |
| `httpx` | Async HTTP client | M21-M22 |
| `fastapi` | API framework | M21-M22B |
| `uvicorn` | ASGI server for FastAPI | M21-M22B |
| `structlog` | Structured logging | M19-M20 |
| `opentelemetry-api` | Distributed tracing | M19-M20 |

## 2. Node.js Setup

```bash
# Verify Node.js version (18+ required)
node --version

# Install dependencies
npm install

# Verify installation
node -e "import('@anthropic-ai/sdk').then(m => console.log('SDK loaded'))"
```

### Node.js Dependencies Explained

| Package | Purpose | Used In |
|---------|---------|---------|
| `@anthropic-ai/sdk` | Claude API client | All modules |
| `dotenv` | Load `.env` files | All modules |
| `zod` | Schema validation & structured output | M04+, capstones |

## 3. API Key Configuration

1. Get your API key from [console.anthropic.com](https://console.anthropic.com/)
2. Copy the example env file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and replace the placeholder:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   ```

**Never commit your `.env` file.** It's already in `.gitignore`.

### Using Environment Variables Directly

If you prefer not to use a `.env` file:

```bash
# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Windows (cmd)
set ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-api03-your-actual-key-here"
```

## 4. Verify Everything Works

```bash
# Python
cd M01-llm-mental-model
python solution/first_call.py

# Node.js
node solution/first_call.js
```

You should see Claude respond to "What is an AI agent?" If you get an authentication error, double-check your API key.

## 5. Docker Setup (M22B Only)

Module M22B (Deploy an Agent) requires Docker for local containerized deployment:

```bash
# Verify Docker is running
docker --version
docker ps

# If using Docker Desktop, make sure it's started
# Test with a quick pull
docker run --rm hello-world
```

## 6. Editor Setup (Recommended)

### VS Code

Install these extensions for the best experience:

- **Python** (ms-python.python) — Python language support
- **Pylance** (ms-python.vscode-pylance) — Python type checking
- **ESLint** (dbaeumer.vscode-eslint) — JS/TS linting
- **REST Client** (humao.rest-client) — Test API endpoints (M21+)

### Workspace Settings

Create `.vscode/settings.json` in the labs root:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true
  }
}
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: anthropic` | Run `pip install -r requirements.txt` |
| `AuthenticationError` | Check your API key in `.env` |
| `RateLimitError` | Wait 60 seconds and retry |
| `python: command not found` | Use `python3` instead, or check your PATH |
| `Permission denied` on venv | Use `python -m venv venv --clear` |
| `npm ERR! ERESOLVE` | Delete `node_modules/` and run `npm install` again |
| `ImportError: cannot import name` | Make sure you're in the correct lab directory |
| Shared imports fail | Run from the `labs/` root: `python -m M05-function-calling.starter.agent` |
| Docker permission denied | Add your user to the docker group: `sudo usermod -aG docker $USER` |
| `ECONNREFUSED` on API calls | Check if you're behind a proxy; set `HTTPS_PROXY` if needed |

### Import Path for Shared Utilities

Labs import from `shared/` using relative paths. If imports fail, make sure you run scripts from the `labs/` root directory:

```bash
# From labs/ root (correct)
python -m M05-function-calling.starter.agent

# Or add labs/ to your Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
cd M05-function-calling/starter
python agent.py
```

### API Cost Awareness

All labs use `claude-sonnet-4-6` by default. Estimated costs per lab:

| Track | Estimated Cost per Lab |
|-------|----------------------|
| M00-M03 (Foundations) | $0.01-0.05 |
| M04-M07 (Core Skills) | $0.05-0.15 |
| M08-M14 (Memory/Reasoning) | $0.10-0.30 |
| M15-M22 (Advanced/Production) | $0.15-0.50 |
| Capstones 1-3 | $0.10-0.50 |
| Capstones 4-5 | $0.50-2.00 |

Total course cost estimate: **$5-15** at Sonnet pricing.
