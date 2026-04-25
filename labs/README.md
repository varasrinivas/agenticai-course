# Building AI Agents with Claude — Lab Repository

Hands-on labs for the **Building AI Agents with Claude: From Hello World to Autonomous Production Systems** course. Each lab folder contains starter code with TODOs, complete solutions in Python and Node.js, and expected output for verification.

## Quick Start

```bash
# 1. Clone and enter
git clone <repo-url>
cd claude-agent-course-labs

# 2. Set up environment
cp .env.example .env
# Edit .env and add your Anthropic API key

# 3. Install dependencies (pick your language)
pip install -r requirements.txt   # Python
npm install                       # Node.js

# 4. Start with M00
cd M00-agent-lifecycle
cat README.md
```

See [SETUP.md](SETUP.md) for detailed installation instructions and troubleshooting.

## Lab Structure

Every lab folder follows this pattern:

```
M05-function-calling/
├── README.md              # Step-by-step instructions
├── starter/               # Skeleton code with TODOs (start here)
│   ├── agent.py           # Your working file
│   ├── agent.js           # Parallel Node.js implementation
│   ├── tools.py           # Pre-built tools (complete)
│   └── mock_data.py       # Test data (complete)
├── solution/              # Complete working code (peek if stuck)
│   ├── agent.py           # Python solution
│   └── agent.js           # Node.js solution
└── expected_output/       # What success looks like
    └── sample_output.txt
```

**Rule**: Config, mock data, and helper files are complete. You only build the agent logic.

## Course Tracks & Module Labs

### Track 1: Foundations (M00-M03)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M00 | The Agent Lifecycle | Beginner | 1 (explore) | Trace a working agent's loop and components |
| M01 | The LLM Mental Model | Beginner | 3 | First API call, temperature, model comparison |
| M02 | Tokens | Beginner | 3 | Token counting, cost estimation, budget management |
| M03 | Prompts | Beginner | 3 | Message roles, few-shot prompting, conversation manager |

### Track 2: Core Agent Skills (M04-M07)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M04 | Structured Output | Beginner+ | 3 | JSON extraction, tool_use structure, Pydantic/Zod validation |
| M05 | Function Calling | Beginner+ | 3 | Single tool call, multi-tool agent loop, error handling |
| M06 | Multi-Tool Orchestration | Intermediate | 3 | Tool chaining, parallel calls, orchestrator pattern |
| M07 | Model Context Protocol (MCP) | Intermediate | 3 | MCP server setup, tool registration, client integration |

### Track 3: Memory & Knowledge (M08-M11)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M08 | Conversation Management | Intermediate | 3 | Context windows, message pruning, sliding window |
| M09 | RAG (Retrieval-Augmented Generation) | Intermediate | 3 | Embeddings, vector search, grounded answers |
| M10 | Advanced RAG | Intermediate+ | 3 | Hybrid search, reranking, query decomposition |
| M11 | Multi-Layer Memory | Intermediate+ | 3 | Short/long-term memory, memory retrieval strategies |

### Track 4: Reasoning & Planning (M12-M14)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M12 | ReAct Agent Loop | Intermediate+ | 3 | Thought-action-observation cycle, loop control |
| M13 | Planning & Task Decomposition | Advanced | 3 | Plan generation, subtask execution, replanning |
| M14 | Multi-Agent Systems | Advanced | 3 | Agent handoffs, shared state, supervisor pattern |

### Track 5: Advanced Capabilities (M15, M15B)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M15 | Code Interpreter Sandbox | Advanced | 3 | Sandboxed code execution, output parsing |
| M15B | Build a Complete Agent | Advanced | 1 (full build) | End-to-end agent + subagent system (80% lab) |

### Track 6: Safety & Quality (M16-M18)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M16 | Input Guardrails | Intermediate | 3 | Input validation, injection detection, content filtering |
| M17 | Output Guardrails & HITL | Intermediate+ | 3 | Output validation, human approval workflows |
| M18 | Evaluation & Testing | Intermediate+ | 3 | Eval datasets, automated scoring, regression testing |

### Track 7: Production (M19-M22, M22B)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M19 | Tracing & Logging | Intermediate | 3 | Structured logging, trace context, span trees |
| M20 | Monitoring | Intermediate+ | 3 | Metrics, alerts, dashboards, anomaly detection |
| M21 | API Design | Advanced | 3 | REST/streaming endpoints, auth, rate limiting |
| M22 | Cost Optimization | Advanced | 3 | Prompt caching, model routing, budget controls |
| M22B | Deploy an Agent | Advanced | 1 (full deploy) | Docker, Cloud Run, Lambda deployment (80% lab) |

### Track 9: Certification Prep (M25-M27)

| Lab | Title | Difficulty | Exercises | Key Skill |
|-----|-------|-----------|-----------|-----------|
| M25 | Claude Code Mastery | Intermediate | 3 | CLAUDE.md, hooks, slash commands, permission modes |
| M26 | Hooks, Sessions & Agent SDK | Advanced | 3 | Event hooks, session management, SDK patterns |
| M27 | Cert Exam Prep | All levels | 3 | Practice questions, domain review, exam strategies |

### Capstone Projects (Track 8)

Each capstone has three domain variants (Healthcare, B2B Ecommerce, UCC Data Engineering):

| Lab | Title | Difficulty | What You Build |
|-----|-------|-----------|----------------|
| Capstone 1 | First Agent | ★☆☆☆☆ | Single-tool conversational assistant |
| Capstone 2 | Knowledge Agent | ★★☆☆☆ | RAG-powered domain expert |
| Capstone 3 | Reasoning Agent | ★★★☆☆ | ReAct multi-step problem solver |
| Capstone 4 | Agent Team | ★★★★☆ | Multi-agent pipeline with HITL |
| Capstone 5 | Production Agent | ★★★★★ | Autonomous system with full observability |
| Capstone 6 | Bronze Layer Testing | ★★★☆☆ | Data pipeline quality testing |

## Domain Anchors

All capstones apply the same agent pattern across three industries:

- **Domain A — Healthcare Pre-Authorization**: Clinical criteria matching, CPT/ICD codes, HIPAA compliance
- **Domain B — B2B Ecommerce Order Tracking**: PO lifecycle, carrier APIs, SLA management
- **Domain C — UCC Data Engineering**: Lien risk assessment, entity resolution, Medallion Architecture

## Shared Utilities

The `shared/` directory contains reusable files used across multiple labs:

| File | Purpose | Used By |
|------|---------|---------|
| `mock_ucc_data.py` | 11 realistic UCC filings with search functions | M04+ (Python) |
| `mock_ucc_data.js` | Same data and functions for Node.js | M04+ (Node.js) |
| `test_helpers.py` | Response validation, mock objects, output formatting | All labs |

These files are **complete** — do not modify them.

## Prerequisites

- Python 3.10+ or Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)
- A code editor (VS Code recommended)
- Docker (for M22B deployment lab)
- Git

## Recommended Learning Path

1. **Complete M00-M05 first** — these build the foundation every later lab assumes
2. **Do labs in order within each track** — later modules build on earlier ones
3. **Attempt the starter code before looking at solutions** — struggle is where learning happens
4. **Run expected output comparisons** to verify your solutions
5. **Try at least one capstone per difficulty tier** to consolidate skills
6. **Pick one domain and go deep** or try all three to see pattern transfer

## Getting Help

- Each lab's `README.md` has hints and common pitfalls
- Solutions include inline comments explaining key decisions
- If you hit an API error, check the [troubleshooting section in SETUP.md](SETUP.md#troubleshooting)
