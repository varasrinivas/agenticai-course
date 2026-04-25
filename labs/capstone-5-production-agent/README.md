# Capstone 5: Production Agent — Autonomous System with Full Observability

## What You'll Build

In this capstone, you will build a **production-grade autonomous agent system** that processes UCC filing queries with multi-layer memory, model routing, full observability, and containerized deployment. This is Domain C (Public Records / UCC Data Engineering) only — you go deep into one domain rather than spanning all three.

Your system will include:
- **4 specialized agents** (Router, Filing, Entity, Risk) with model routing
- **Multi-layer memory** (Working, Episodic, Procedural) for context awareness
- **Model routing** that selects Claude Haiku / Sonnet / Opus based on query complexity
- **Full observability** with tracing (LangFuse-style) and metrics collection
- **Evaluation harness** with 100 test cases including adversarial inputs
- **Containerized deployment** via Docker + docker-compose

## Difficulty: ★★★★★ (4-6 hours across 2-3 sessions)

## Prerequisites

- Modules M01 through M22 completed (especially M11: Multi-Layer Memory, M18: Evaluation, M19: Tracing, M20: Monitoring, M22: Cost Optimization)
- Capstones 1-4 completed
- Python 3.10+ installed
- Node.js 18+ installed
- Docker Desktop installed
- Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- `pip install anthropic pydantic` (Python dependencies)
- `npm install @anthropic-ai/sdk` (Node.js SDK)

---

## Setup

```bash
# Navigate to this directory
cd labs/capstone-5-production-agent

# Enter the domain directory
cd domain-c-ucc

# Install dependencies
pip install -r starter/requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start with the starter code
cd starter
```

---

## Step-by-Step Lab Instructions

### Step 1: Understand the Configuration

Open `starter/config.py`. Read the model tiers (`fast`, `balanced`, `powerful`), routing rules, complexity weights, system prompts, and observability settings. This file is complete — do not modify it.

**Key things to notice:**
- Three model tiers map to different Claude models with different cost/capability trade-offs
- Routing rules define which task types default to which tier, and when to upgrade
- System prompts define each agent's persona and available tools
- Observability config controls tracing sample rate and log level

### Step 2: Implement Working Memory

Open `starter/memory/working_memory.py`. Complete the TODOs to build a working memory layer that stores:

1. **Current query** — the user's question being processed right now
2. **Tool call history** — every tool invoked during this request
3. **Intermediate results** — partial answers from each agent
4. **Agent handoff log** — records of which agent handed off to which

Working memory clears at the end of every request. It is the "scratchpad" for the current operation.

### Step 3: Implement Episodic Memory

Open `starter/memory/episodic_memory.py`. Complete the TODOs to build an episodic memory layer that:

1. **Stores episodes** — past query/response pairs with metadata (agent used, tools called, task type, success flag)
2. **Recalls similar episodes** — given a new query, finds past episodes with high keyword overlap
3. **Respects capacity limits** — evicts oldest episodes when `max_episodes` is exceeded

This lets the agent learn from past interactions. If a user asks the same question twice, the agent can recall what worked before.

### Step 4: Implement Procedural Memory

Open `starter/memory/procedural_memory.py`. Complete the TODOs to build a procedural memory layer that:

1. **Stores rules** — learned heuristics like "when query mentions 'blanket lien', use the powerful model tier"
2. **Finds applicable rules** — given keywords from the current query, returns rules whose triggers match
3. **Tracks confidence** — rules have confidence scores that can be updated as the system learns

### Step 5: Implement the Router Agent

Open `starter/agents/router_agent.py`. Complete the TODOs to build a router that:

1. **Analyzes the query** — determines what kind of task this is (filing_lookup, entity_resolution, risk_assessment, etc.)
2. **Selects target agents** — decides which specialist agent(s) should handle the query
3. **Assesses complexity** — determines if this is simple, medium, or complex
4. **Returns a routing decision** — a dict with `task_type`, `agents`, `complexity`, and `reasoning`

The router uses Claude to make intelligent routing decisions based on the system prompt in `config.py`.

### Step 6: Implement the Filing Agent

Open `starter/agents/filing_agent.py`. Complete the TODOs to build a filing specialist that:

1. **Defines 4 tools** — `search_filings`, `get_filing_details`, `check_filing_status`, `get_amendments`
2. **Runs a ReAct loop** — sends messages to Claude, parses tool_use blocks, executes tools against mock data, appends results
3. **Returns structured results** — answer text plus a list of tool calls made

### Step 7: Implement the Entity Agent

Open `starter/agents/entity_agent.py`. Complete the TODOs to build an entity resolution specialist that:

1. **Defines 4 tools** — `search_filings`, `fuzzy_match`, `get_business_registry`, `merge_entity_profile`
2. **Handles name matching** — compares entity names using keyword overlap and fuzzy matching
3. **Resolves entities** — determines whether two names refer to the same business using EIN matching, address comparison, and name similarity

### Step 8: Implement the Risk Agent

Open `starter/agents/risk_agent.py`. Complete the TODOs to build a risk assessment specialist that:

1. **Defines 4 tools** — `search_filings`, `classify_collateral`, `calculate_exposure`, `generate_risk_report`
2. **Classifies collateral** — categorizes descriptions as blanket lien, equipment, inventory, accounts receivable, etc.
3. **Calculates exposure** — computes total lien exposure across filings
4. **Generates risk reports** — produces structured risk assessments with severity levels

### Step 9: Implement Model Routing

Open `starter/model_router.py`. Complete the TODOs to build a model router that:

1. **Computes complexity score** — based on token count, entity count, state count, and ambiguity
2. **Selects model tier** — maps the complexity score to fast/balanced/powerful using thresholds
3. **Applies routing rules** — checks if the task type has an upgrade condition that applies
4. **Estimates cost** — calculates expected cost based on the selected model's pricing

### Step 10: Implement Observability

Open `starter/observability/tracer.py` and `starter/observability/metrics.py`. Complete the TODOs to build:

**Tracer:**
1. **Start/end traces** — a trace represents one full request lifecycle
2. **Start/end spans** — spans are nested operations within a trace (routing, agent calls, tool calls)
3. **Format trace output** — produce a human-readable trace tree showing timing and status

**MetricsCollector:**
1. **Record request metrics** — cost, latency, tokens, tool calls, status
2. **Compute aggregates** — cost by tier, latency percentiles (p50/p95/p99), token usage
3. **Format dashboard** — produce a text dashboard showing system health

### Step 11: Wire the Main Entry Point

Open `starter/main.py`. Complete the TODOs in the `ProductionAgent` class:

1. **`process_query()`** — the main pipeline: start trace, set working memory, check episodic/procedural memory, route query, select model, execute agents, record metrics, store episode, end trace
2. **`_select_agent()`** — map agent name strings to agent instances
3. **`get_dashboard()`** — return the metrics dashboard
4. **`get_trace()`** — return a formatted trace

The CLI interface (interactive mode, eval mode, single query mode) is already complete.

### Step 12: Run the Evaluation Suite

Once all TODOs are complete, run the evaluation harness against the solution:

```bash
cd solution
python main.py --eval --max-tests 10
```

This runs the first 10 of 100 test cases and produces a report showing:
- Pass/fail for each test
- Accuracy by category (filing_lookup, entity_resolution, risk_assessment, edge_case)
- Accuracy by difficulty (simple, medium, complex, edge)
- Latency percentiles and token usage

Compare your output against `expected_output/eval_report.txt`.

### Step 13: Deploy with Docker

Build and run the containerized system:

```bash
cd solution
docker compose up --build
```

The container exposes the interactive agent on port 8080. Run queries against it:

```bash
docker exec -it ucc-production-agent python main.py --query "Find all filings for Acme Corporation in California"
```

---

## Final Verification

Compare your output against the files in `expected_output/`. Your system should:

- [ ] Process queries through the full pipeline (route -> agent -> response)
- [ ] Router correctly identifies task type (filing_lookup, entity_resolution, risk_assessment)
- [ ] Filing agent searches, retrieves details, checks status, and lists amendments
- [ ] Entity agent resolves name variations using fuzzy matching and EIN lookup
- [ ] Risk agent classifies collateral, calculates exposure, and generates risk reports
- [ ] Model router selects appropriate tier (fast for simple lookups, powerful for risk analysis)
- [ ] Working memory stores and clears per-request context
- [ ] Episodic memory stores past episodes and recalls similar queries
- [ ] Procedural memory stores and retrieves learned rules
- [ ] Tracer produces nested span trees for every request
- [ ] Metrics dashboard shows cost, latency, tokens, and request stats
- [ ] Evaluation harness passes 9/10 tests on the first 10 test cases
- [ ] Docker container builds and runs successfully

---

## What You Built

By completing this capstone, you have built:

1. **A production-grade multi-agent system** with 4 specialized agents collaborating through an intelligent router
2. **Multi-layer memory** (working, episodic, procedural) that gives the agent short-term context, long-term recall, and learned heuristics
3. **Model routing** that optimizes cost by selecting the cheapest model capable of handling each query's complexity
4. **Full observability** with distributed tracing and a metrics dashboard tracking cost, latency, tokens, and error rates
5. **An evaluation harness** with 100 test cases spanning filing lookups, entity resolution, risk assessment, and adversarial edge cases
6. **Containerized deployment** with Docker and docker-compose, ready for production hosting

These are the exact patterns used in production AI agent systems: memory for context, routing for cost, observability for debugging, evaluation for quality, and containers for deployment.

---

## Next Steps

Continue to **Capstone 6: Data Pipeline Testing** where you will build a bronze-layer data testing pipeline with schema validation, data quality checks, and automated regression tests.
