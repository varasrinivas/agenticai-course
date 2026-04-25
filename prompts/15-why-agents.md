# Why Agents: The Business Case

This section should be added to M00 immediately AFTER the prelude (ML → FastAPI → Agent) and BEFORE "What Is an Agent?". The student has just seen the three approaches — now they need to understand the concrete benefits in business terms.

## Wait — Both End Up in FastAPI. So What's the Difference?

The student just saw three approaches. A sharp student will notice: "In Approach 2, the ML model is wrapped in FastAPI. In production, the agent (Approach 3) will ALSO be wrapped in FastAPI (that's what M22B teaches). So what's actually different?"

This is the CRITICAL distinction the student must understand before moving forward:

### The Architecture Side-by-Side

```
APPROACH 2: ML Model in FastAPI          APPROACH 3: Agent in FastAPI
─────────────────────────────           ─────────────────────────────

Client                                  Client
  │                                       │
  │ POST /predict                         │ POST /query
  │ {"company_name": "Acme"}              │ {"question": "Assess risk for Acme"}
  ▼                                       ▼
┌──────────────────┐                    ┌──────────────────┐
│ FastAPI Server    │                    │ FastAPI Server    │
│                  │                    │                  │
│  1. Parse input  │                    │  1. Parse input  │
│  2. Query DB     │ ← hardcoded SQL    │  2. Call Claude  │ ← sends question
│  3. Load pickle  │                    │  3. Claude THINKS│ ← "what should I search?"
│  4. Predict      │                    │  4. Claude calls │ ← search_filings tool
│  5. Return JSON  │                    │     YOUR tools   │ ← predict_delinquency tool
│                  │                    │  5. Claude loops │ ← decides what's next
│  LOGIC: YOUR     │                    │  6. Claude writes│ ← narrative response
│  CODE decides    │                    │     response     │
│  everything      │                    │                  │
│                  │                    │  LOGIC: CLAUDE   │
│                  │                    │  decides what    │
│                  │                    │  to do           │
└──────────────────┘                    └──────────────────┘
  │                                       │
  ▼                                       ▼
{"prediction": "HIGH RISK",             "Acme Corporation has 8 active
 "probability": 0.823}                   filings across 4 states. The ML
                                         model predicts HIGH RISK (82.3%)
                                         primarily because filing
                                         CA-2024-001 covers all assets
                                         and lapses in 8 months..."
```

### What's the Same
- Both use FastAPI as the HTTP server
- Both have a `/endpoint` that clients call
- Both return a response
- Both can be containerized in Docker and deployed to Cloud Run/Lambda
- Both handle authentication, rate limiting, error handling the same way

### What's Different — The Decision Engine

The ENTIRE difference is **WHERE the decision logic lives**:

| Aspect | ML Model in FastAPI | Agent in FastAPI |
|---|---|---|
| **Who decides what to query?** | YOUR hardcoded SQL | Claude reasons about what to search |
| **Who handles name variations?** | YOUR ILIKE pattern | Claude discovers them |
| **Who picks which data to look at?** | YOUR code, fixed order | Claude, based on what it finds |
| **Who formats the response?** | YOUR template | Claude writes natural language |
| **Who handles a new question type?** | YOU build a new endpoint | Claude figures it out with existing tools |
| **What changes when logic changes?** | YOUR code + redeploy | The system prompt (no redeploy for reasoning changes) |

### The "Intelligence Layer" Concept

Think of it as three layers:

```
┌─────────────────────────────────────────────┐
│ LAYER 3: INTELLIGENCE (Claude)              │ ← NEW with agents
│ Reasoning, planning, synthesis, explanation  │
│ "What should I search? What does this mean?" │
├─────────────────────────────────────────────┤
│ LAYER 2: CAPABILITIES (Tools + ML Model)    │ ← Same in both
│ search_filings(), predict_delinquency()     │
│ get_filing_details(), query database        │
├─────────────────────────────────────────────┤
│ LAYER 1: INFRASTRUCTURE (FastAPI + Docker)  │ ← Same in both
│ HTTP server, auth, rate limits, deployment   │
└─────────────────────────────────────────────┘
```

**Approach 2** has Layers 1 and 2. YOUR CODE is the intelligence — you write every if/else, every query pattern, every response template.

**Approach 3** has all three layers. Claude IS the intelligence — it decides what capabilities to use, in what order, and synthesizes the results. Your code provides the infrastructure and capabilities. Claude provides the reasoning.

**The ML model lives in Layer 2 in BOTH approaches.** It doesn't move. It doesn't change. The difference is what's ABOVE it — hardcoded logic vs Claude's reasoning.

### Why This Matters for Your Career

"In 5 years, most APIs will still be FastAPI (or equivalent). Most ML models will still be pickle/ONNX/TensorFlow. The change is Layer 3 — the intelligence layer that decides how to use the tools and models. That's what this course teaches you to build."

### The Cost-Benefit Reality

| Metric | ML in FastAPI | Agent in FastAPI |
|---|---|---|
| Response time | 50-200ms | 3-15 seconds |
| Cost per request | ~$0 | $0.003-0.075 |
| Development time for v1 | 2-3 days | 4-6 hours |
| Time to add new question type | 1-2 days (new endpoint) | 0 (Claude handles it) |
| Time to handle new edge case | Hours (find, code, test, deploy) | 0 (Claude reasons about it) |
| Maintenance burden | High (every change = code) | Low (tools rarely change) |
| Explainability | Manual feature importance | Built-in narrative |
| User training needed | API documentation | None (natural language) |

"The agent costs $0.015 per request and takes 10 seconds longer. But it eliminates days of development per new question type and produces output that non-technical users can actually read."

## The 7 Benefits of AI Agents Over Traditional Approaches

### 1. Reasoning Replaces Hardcoded Logic
**Traditional**: Every decision path is an if/else chain YOU write. 50 edge cases = 50 code branches.
**Agent**: Claude reasons about what to do. New edge cases are handled by reasoning — no code change.

**Concrete example from the prelude**: The script searched 5 hardcoded name variants. The agent discovered "ACME CORP DBA ROADRUNNER SUPPLIES" by reasoning: "Let me also check for DBAs." That reasoning was NOT programmed — Claude figured it out.

**Business impact**: A credit risk team at a mid-size bank manually maintained 200+ name variation rules. After switching to an agent, they eliminated the rules file entirely. Name match rate improved from 78% to 94%.

### 2. Natural Language In, Structured Action Out
**Traditional**: Users must learn your API format, fill forms, or use specific query syntax.
**Agent**: Users ask in plain English. The agent figures out what tools to call.

**Concrete example**: 
- Traditional: `POST /predict {"company_name": "ACME CORPORATION", "state": "NY"}`
- Agent: "What's the lien exposure for Acme across the northeast?"

**Business impact**: Non-technical analysts (credit officers, compliance reviewers, loan underwriters) can directly use the system without training on API syntax. Adoption goes from "5 engineers who know the API" to "50 analysts who can ask questions."

### 3. Explainability Built In
**Traditional**: ML model returns 0.823. Why? Check feature importance plots. Still unclear to a business user.
**Agent**: "The risk is HIGH (82.3%) primarily because filing CA-2024-001 covers all assets and lapses in 8 months. If this filing lapses without renewal, the $2.4M collateral exposure becomes unsecured."

**Business impact**: Regulatory compliance (OCC, FDIC) increasingly requires explainable AI decisions. An agent's narrative output satisfies examiners in a way that "probability: 0.823" never will.

### 4. Follow-Up Questions Without New Code
**Traditional**: Every new question type = new endpoint, new query, new code, new deployment.
**Agent**: "What about their Texas filings?" — works immediately using the same tools.

**Concrete example**:
- Traditional: Build `/predict`, then `/predict-by-state`, then `/compare-entities`, then `/what-if-continuation` — four separate endpoints.
- Agent: One agent handles all four naturally in conversation.

**Business impact**: Development velocity. A team that spent 2 weeks per new query type now deploys 0 new code for new question types. The tools stay the same — Claude combines them differently per question.

### 5. Multi-Source Synthesis
**Traditional**: Each data source is a separate query, separate code path, separate response. YOU write the join logic.
**Agent**: Claude searches multiple sources, correlates results, and synthesizes a unified answer.

**Concrete example from the prelude**: The agent searched UCC filings (Tool 1), ran the ML model (Tool 2), then fetched specific filing details (Tool 3), and SYNTHESIZED all three into a coherent risk report. Writing that synthesis logic as a script would take 200+ lines and would break every time a new data source is added.

**Business impact**: Data teams spend 40-60% of their time on integration and synthesis. An agent automates the synthesis layer — the tools stay decoupled, Claude handles the joining.

### 6. Graceful Handling of Incomplete Data
**Traditional**: Missing data = error, null, or hardcoded default. The script either crashes or silently returns wrong results.
**Agent**: Claude reasons about what's missing and adapts. "I found filings in NY and CA but no results in TX. This may mean no filings exist in TX, or the data may not be current. I'll note this uncertainty in the report."

**Concrete example**: An entity search returns 0 results for one state. A script returns `"states": ["NY", "CA"]` — no mention that TX was searched and found empty. The agent explicitly notes: "Searched TX — no active filings found. Last filing TX-2021-005 was terminated in 2022."

**Business impact**: Reduces false negatives. Analysts stop asking "did you check Texas?" because the agent tells them what it checked and what it found (or didn't find).

### 7. The ML Model Gets Smarter Context (Not Replaced)
**Traditional**: ML model sees 6 numbers. That's all it has.
**Agent**: ML model sees 6 numbers. But the agent wraps those numbers with: which specific filings contributed to each number, what the collateral descriptions say, whether any filings are under unusual circumstances, and what a continuation or termination would change.

**The key point**: Agents don't replace ML models. They make ML models MORE USEFUL by providing context that the model can't see. The model gives the probability. The agent gives the story.

## When NOT to Use Agents

Agents are not always the answer. Use traditional approaches when:

| Situation | Why Not an Agent |
|---|---|
| Batch processing 1M records | Agent cost: $10K+. Script cost: $0. |
| Sub-100ms response required | Agent latency: 3-15 seconds. Script: milliseconds. |
| Deterministic compliance check | Must be reproducible. Agents are non-deterministic. |
| Simple CRUD operations | No reasoning needed. Over-engineering. |
| No human will read the output | If the output feeds another system, structured API is better. |

**The decision rule**: If a human needs to UNDERSTAND the output, consider an agent. If a machine needs to CONSUME the output, use an API.

## The Cost Question

Students always ask: "But agents cost money per request."

| Approach | Cost Per Query | What You Get |
|---|---|---|
| ML Script | ~$0 | A number |
| FastAPI | ~$0 | A number + some data |
| Claude Agent (Haiku) | ~$0.003 | Narrative report with reasoning |
| Claude Agent (Sonnet) | ~$0.015 | Detailed analysis with evidence |
| Claude Agent (Opus) | ~$0.075 | Expert-level assessment |

"Is a $0.015 comprehensive risk report with specific filing citations worth more than a free 0.823? For a $2.4M collateral decision, yes."

The cost comparison should include: what does it cost to have a human analyst do the same work? ($50-100/hour × 30 minutes = $25-50 per report). The agent costs $0.015 and takes 15 seconds.

## Animated Diagram: The Benefits Stack

Visual showing the three approaches as stacked layers:
- Bottom (gray): ML Model — prediction only
- Middle (blue): FastAPI — prediction + auto-fetch
- Top (gradient): Agent — prediction + auto-fetch + reasoning + name discovery + explanation + follow-ups + synthesis

Each layer ADDS capability without removing the one below. The agent INCLUDES the model. It doesn't replace it.
