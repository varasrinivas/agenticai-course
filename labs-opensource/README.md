# Building AI Agents with Open Source Models — Lab Repository

Hands-on labs for the **Open Source Track (Mistral/Ollama)** of the agent course. Every lab runs against a **local Mistral-7B model served by Ollama** through the standard `openai` SDK — no API key, no per-token cost, everything on your machine.

Each lab folder contains starter code with TODOs, complete solutions in Python and Node.js, and expected output for verification.

## Quick Start

```bash
# 1. Install Ollama and pull Mistral (one-time, ~4.1 GB download)
ollama pull mistral
ollama serve        # leave running in a separate terminal

# 2. Clone and enter
cd labs-opensource

# 3. Install dependencies (pick your language)
pip install -r requirements.txt   # Python
npm install                       # Node.js

# 4. Verify your environment
cd M00-dev-setup
python starter/check_setup.py     # or: node starter/check_setup.js

# 5. Start learning
cat README.md
```

See [SETUP.md](SETUP.md) for detailed installation instructions and troubleshooting.

## How These Labs Differ from the Claude Track (`../labs/`)

| | Claude Track | Open Source Track (this repo) |
|---|---|---|
| Model | Claude (hosted) | Mistral-7B via Ollama (local) |
| SDK | `anthropic` / `@anthropic-ai/sdk` | `openai` (pointed at `http://localhost:11434/v1`) |
| API key | Required | None (`api_key="ollama"` placeholder) |
| Cost | Per token | Free (your hardware) |
| Tool calling | `tool_use` / `tool_result` content blocks | `tool_calls` array + `role: "tool"` messages |
| Stop signal | `stop_reason == "end_turn"` | `finish_reason == "stop"` |

## Lab Structure

Every lab folder follows this pattern:

```
M05-function-calling/
├── README.md              # Step-by-step instructions
├── starter/               # Skeleton code with TODOs (start here)
│   ├── tool_agent.py      # Your working file
│   ├── tool_agent.js      # Parallel Node.js implementation
│   └── tools.py / .js     # Pre-built tools (complete)
├── solution/              # Complete working code (peek if stuck)
│   ├── tool_agent.py
│   └── tool_agent.js
└── expected_output/       # What success looks like
    └── sample_output.txt
```

**Rule**: Config, mock data, and helper files are complete. You only build the agent logic.

## Module Labs

### Track 1: Foundations (M00–M03B)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M00 | Dev Setup | Beginner | 2 | Verify Ollama + Mistral + SDK environment |
| M00B | Hello World, Three Approaches | Beginner | 3 | Raw SDK loop vs CrewAI vs LangChain |
| M01 | The LLM Mental Model | Beginner | 4 + stretch | First API call, system prompts, temperature, token usage |
| M02 | Tokens & Context Limits | Beginner | 3 | Token counting, prompt budgeting, throughput benchmark |
| M03 | Prompts | Beginner | 3 | System prompts, zero/few-shot/CoT, multi-turn conversations |
| M03B | Context Engineering | Beginner+ | 1 (multi-part) | ContextBudget class, the poisoned-transcript fix |

### Track 2: Core Agent Skills (M04–M06)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M04 | Structured Output | Beginner+ | 3 | Forced tool calls, Pydantic/Zod validation, retry with feedback |
| M05 | Function Calling | Beginner+ | 2 + stretch | Tool definitions, the agent loop, `finish_reason` handling |
| M06 | Multi-Tool Orchestration | Intermediate | 2 | Parallel vs sequential execution, ToolRegistry, error recovery |

### Track 3: Memory & Knowledge (M08–M11)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M08 | Conversation Management | Intermediate | 3 | Sliding window, auto-summarization, save/restore |
| M09 | RAG | Intermediate | 3 | Chunking, ChromaDB, grounded answers with citations |
| M10 | Advanced RAG | Intermediate+ | 3 | BM25 + dense hybrid search, RRF, LLM re-ranking |
| M11 | Multi-Layer Memory | Intermediate+ | 3 | Token-aware buffer + persistent vector memory + facade |

### Track 4: Reasoning & Planning (M12–M15)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M12 | ReAct Agent Loop | Intermediate | 2 | Thought traces, stop conditions |
| M13 | Planning & Decomposition | Intermediate+ | 3 | Intent routing, DAG validation (topo sort), wave execution |
| M14 | Multi-Agent Systems | Intermediate+ | 1 (big) | 4-specialist pipeline, handoff messages, review/retry loop |
| M15 | Code Execution Sandbox | Intermediate+ | 2 | Subprocess sandboxing, self-debugging agent |

### Track 5: Safety & Quality (M16–M18)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M16 | Input Guardrails | Advanced | 4 | PII redaction, token-bucket rate limiting, injection classifier (fails CLOSED) |
| M17 | Output Guardrails & HITL | Advanced | 3 | Hallucination judge, cost budget, circuit breaker, approval gate |
| M18 | Evaluation & Testing | Advanced | 2 | LLM-as-judge with bias mitigations, golden dataset |

### Track 6: Production (M19–M22)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M19 | Tracing & Logging | Advanced | 2 + viewer | JSONL tracer (4 event categories), trace viewer CLI |
| M20 | Monitoring | Advanced | 2 | Z-score drift detection, feedback→eval loop |
| M21 | API Design & Deployment | Advanced | 1 (big) | FastAPI/Express wrapper: auth, health, error envelope |
| M21B | Cloud Deployment | Advanced | 1 + guided | Provider factory; local→GPU VM→managed with zero code change |
| M22 | Cost Optimization | Advanced | 2 | Two-layer response cache, model benchmark harness |

### Wrap-Up

| Lab | Title | What It Is |
|-----|-------|-----------|
| M24 | What's Next | Reading checklist + consolidation exercises (no code) |
| CAPSTONE-C3 | Entity Resolution Agent | The integration exam: 5 tools, ReAct, calibrated merges |

## The One Pattern Used Everywhere

Every lab connects to the local model the same way:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(model="mistral", messages=[...])
```

```javascript
import OpenAI from "openai";
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const response = await client.chat.completions.create({ model: "mistral", messages: [...] });
```

If a lab fails, check the three usual suspects first: **Ollama running?** (`ollama serve`) — **model pulled?** (`ollama list`) — **dependencies installed?** (`pip list` / `npm ls`).
