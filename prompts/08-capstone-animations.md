# Capstone Architecture Diagrams & Animations

This file defines the visual requirements for ALL capstone projects. The `/generate-capstone` command MUST read this file and include every specified diagram and animation.

---

## CAPSTONE-1: "First Agent" — Single-Tool Conversational Assistant (★☆☆☆☆)

### ARCHITECTURE DIAGRAM (static, shown at the top)
```
User Question
    │
    ▼
┌────────────────────────────────┐
│  SINGLE AGENT                  │
│  System Prompt + 1 Tool        │
│                                │
│  ┌────────────────────┐        │
│  │ Claude (LLM Brain) │        │
│  └────────┬───────────┘        │
│           │ tool_use            │
│  ┌────────▼───────────┐        │
│  │ get_status(id)     │ ← 1 tool│
│  └────────┬───────────┘        │
│           │ result              │
│  ┌────────▼───────────┐        │
│  │ Natural Language   │        │
│  │ Response           │        │
│  └────────────────────┘        │
└────────────────────────────────┘
    │
    ▼
User sees answer
```

### ANIMATION 1: The Tool Use Loop (hero animation)
**Purpose**: Show the complete request→tool_use→tool_result→response cycle
**Behavior**:
- Step 1: User message bubble appears ("What's the status of filing NY-2024-001?")
- Step 2: Message flows into the agent box
- Step 3: Claude "thinks" (thought bubble: "I need to look up this filing")
- Step 4: Claude returns tool_use block (highlighted JSON: `{name: "get_status", input: {id: "NY-2024-001"}}`)
- Step 5: Tool executes (gear spinning animation)
- Step 6: Tool returns result (highlighted JSON: `{status: "ACTIVE", lapse_date: "2029-10-15"}`)
- Step 7: Result flows back to Claude
- Step 8: Claude generates natural language response
- Step 9: Response bubble appears to user
**Key teaching**: The student sees that Claude doesn't call the tool — it ASKS to call the tool. The code executes it.

### ANIMATION 2: Conversation Memory (multi-turn)
**Purpose**: Show how follow-up questions work
**Behavior**:
- Turn 1: User asks → Agent responds with filing status
- Turn 2: User asks "What about the secured party?" → Agent remembers the filing from turn 1 → calls tool with same ID → responds with secured party details
- Show the conversation history growing (message stack visualization)
**Key teaching**: The agent is stateless — conversation history is sent every time

---

## CAPSTONE-2: "Knowledge Agent" — RAG-Powered Domain Expert (★★☆☆☆)

### ARCHITECTURE DIAGRAM
```
┌──────────────────────────────────────────────────────┐
│                 RAG AGENT                             │
│                                                       │
│  ┌─────────────┐    ┌──────────────┐                 │
│  │ Documents    │───▶│ Chunk + Embed│───▶ Vector DB   │
│  │ (policies/  │    │              │    (ChromaDB)    │
│  │  contracts/ │    └──────────────┘    ┌──────────┐ │
│  │  UCC guides)│                        │ 🔍 Search│ │
│  └─────────────┘                        └────┬─────┘ │
│                                               │       │
│  User Question ───▶ Embed Query ───▶ Find Top 3 ───▶ │
│                                               │       │
│  ┌─────────────────────────────────────┐      │       │
│  │ Claude + Retrieved Context          │◀─────┘       │
│  │ "Answer using ONLY these sources"   │              │
│  │ Generates response with citations   │              │
│  └─────────────────────────────────────┘              │
└──────────────────────────────────────────────────────┘
```

### ANIMATION 1: The RAG Pipeline (hero animation)
**Purpose**: Show the complete Document→Chunk→Embed→Store→Retrieve→Generate flow
**Behavior**:
- Step 1: Documents appear on the left (3-4 document icons with titles)
- Step 2: Documents split into colored chunks (animated splitting)
- Step 3: Each chunk transforms into a number array (embedding visualization — chunk shrinks into a dot)
- Step 4: Dots land in a 2D scatter plot (vector database)
- Step 5: User question appears → transforms into a query dot
- Step 6: Query dot finds nearest 3 dots in the scatter plot (lines connect, distances shown)
- Step 7: 3 dots expand back into text chunks
- Step 8: Chunks flow into Claude's prompt alongside the user question
- Step 9: Claude generates response with "[Source: filing_guide.md]" citations

### ANIMATION 2: Chunking Strategy Comparison
**Purpose**: Show why chunk size matters
**Behavior**: Same document chunked 3 ways side-by-side. User query highlights which chunk gets retrieved in each strategy. Small chunks = precise but may miss context. Large chunks = more context but diluted relevance.

### ANIMATION 3: Embedding Space
**Purpose**: Interactive 2D scatter plot where the student can type a query and see which document chunks are nearest
**Behavior**: Pre-populated dots (chunks), student types → query dot appears → nearest neighbors highlighted

---

## CAPSTONE-3: "Reasoning Agent" — ReAct Multi-Step Problem Solver (★★★☆☆)

### ARCHITECTURE DIAGRAM
```
User Question
    │
    ▼
┌────────────────────────────────────────────────────┐
│  ReAct AGENT                                        │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │              REASONING LOOP                    │ │
│  │                                                │ │
│  │   THINK ──▶ ACT ──▶ OBSERVE ──▶ THINK ──▶ ...│ │
│  │     │         │         │                      │ │
│  │  "I need  "Call tool" "Got result,             │ │
│  │   to find   with       now I need              │ │
│  │   filings"  these      to check                │ │
│  │             params"    variations"              │ │
│  └───────────────────────────────────────────────┘ │
│           │                                         │
│  ┌────────▼────────────────────────────────┐       │
│  │ TOOLS (5)                                │       │
│  │ search_filings │ fuzzy_match │ get_details│      │
│  │ registry_check │ merge_profile            │      │
│  └───────────────────────────────────────────┘     │
│           │                                         │
│  stop_reason: 'end_turn' ──▶ FINAL RESPONSE        │
└────────────────────────────────────────────────────┘
```

### ANIMATION 1: The ReAct Loop in Action (hero animation)
**Purpose**: Walk through a COMPLETE multi-step reasoning chain
**Behavior** (using Domain C entity resolution as the example):
- Step 1: User asks "Find all filings for Acme Corporation across all states"
- Step 2: THINK bubble: "I'll search for the exact name first"
- Step 3: ACT: calls search_filings("Acme Corporation") → 4 filings found in NY
- Step 4: OBSERVE: "Found 4 in NY, but there might be name variations"
- Step 5: THINK bubble: "Let me try abbreviations"
- Step 6: ACT: calls search_filings("ACME CORP") → 3 more filings in CA, TX
- Step 7: OBSERVE: "7 total, let me check for DBAs"
- Step 8: ACT: calls fuzzy_match("Acme") → finds "ACME CORP DBA ROADRUNNER SUPPLIES" in FL
- Step 9: OBSERVE: "8 filings total across 4 states"
- Step 10: ACT: calls merge_profile() → unified entity profile
- Step 11: stop_reason: 'end_turn' → FINAL RESPONSE with full report
**Key teaching**: The agent made DECISIONS at each step. It wasn't following a script — it reasoned about what to do next based on what it found.

### ANIMATION 2: Thought Trace Visualization
**Purpose**: Show the internal reasoning chain as an expandable trace
**Behavior**: Collapsible tree showing each Think→Act→Observe step with timing. Click any step to see the full tool call + result.

### ANIMATION 3: stop_reason Decision Point
**Purpose**: Show how the agent decides to continue vs stop
**Behavior**: At each loop iteration, highlight the stop_reason check: 'tool_use' = continue (green arrow loops back), 'end_turn' = exit (blue arrow to response)

---

## CAPSTONE-4: "Agent Team" — Multi-Agent Pipeline with HITL (★★★★☆)

### ARCHITECTURE DIAGRAM
```
Incoming Request
    │
    ▼
┌────────────────────────────────────────────────────────────┐
│  COORDINATOR                                                │
│  Receives request, delegates to specialist agents           │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent 4  │  │
│  │ INTAKE   │─▶│ ANALYSIS │─▶│ DECISION │─▶│ COMMS    │  │
│  │          │  │          │  │          │  │          │  │
│  │ Parse &  │  │ RAG +    │  │ Route:   │  │ Generate │  │
│  │ validate │  │ criteria │  │ auto/    │  │ output   │  │
│  │ input    │  │ match    │  │ HITL/    │  │ letter   │  │
│  │          │  │          │  │ deny     │  │          │  │
│  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘  │
│                                    │                        │
│  ┌─────────────────────┐          │ confidence < 90%       │
│  │ INPUT GUARDRAILS    │          ▼                        │
│  │ PII detection       │  ┌──────────────┐                │
│  │ Schema validation   │  │ HUMAN-IN-    │                │
│  │ Injection filter    │  │ THE-LOOP     │                │
│  └─────────────────────┘  │ Review queue │                │
│                            └──────────────┘                │
│  ┌─────────────────────┐                                   │
│  │ OUTPUT GUARDRAILS   │  ┌──────────────┐                │
│  │ Compliance check    │  │ CIRCUIT      │                │
│  │ Format validation   │  │ BREAKER      │                │
│  │ Tone check          │  │ 3 failures   │                │
│  └─────────────────────┘  │ → halt + alert│               │
│                            └──────────────┘                │
└────────────────────────────────────────────────────────────┘
```

### ANIMATION 1: Multi-Agent Pipeline Flow (hero animation)
**Purpose**: Show a request flowing through all 4 agents with data transformation at each stage
**Behavior**:
- Step 1: Raw request arrives (JSON or freetext)
- Step 2: Agent 1 (Intake) lights up → parses → outputs structured data → input guardrails flash green
- Step 3: Agent 2 (Analysis) lights up → RAG search → criteria matching → outputs determination with confidence
- Step 4: Agent 3 (Decision) lights up → checks confidence:
  - If > 90%: green arrow to Agent 4 (auto-approve)
  - If 70-90%: yellow arrow to HITL queue (pause, human reviews)
  - If < 70%: red arrow to Agent 4 (auto-deny with rationale)
- Step 5: HITL panel lights up for medium-confidence case → human clicks approve/deny/modify
- Step 6: Agent 4 (Comms) lights up → generates notification → output guardrails flash green
- Step 7: Final output delivered

### ANIMATION 2: Guardrail Checkpoint Flow
**Purpose**: Show input and output guardrails as gates that data passes through
**Behavior**: Data blob approaches a gate → gate runs checks → green = pass through, red = blocked with error details. Show both input guardrails (before Agent 1) and output guardrails (after Agent 4).

### ANIMATION 3: Circuit Breaker Activation
**Purpose**: Show the circuit breaker pattern — counting failures and tripping
**Behavior**: Counter at 0 → failure 1 (count: 1) → failure 2 (count: 2) → failure 3 (count: 3, THRESHOLD) → circuit TRIPS → all traffic redirected to fallback → alert fires → after cooldown, circuit half-opens → test request → success → circuit closes

### ANIMATION 4: HITL Decision Dashboard
**Purpose**: Show what the human reviewer sees
**Behavior**: Mock dashboard with: case summary, Agent 2's determination, confidence score, relevant evidence, and three buttons: Approve / Deny / Modify. Human clicks → decision flows to Agent 4.

---

## CAPSTONE-5: "Production Agent" — Autonomous System with Full Observability (★★★★★)

### ARCHITECTURE DIAGRAM
```
┌──────────────────────────────────────────────────────────────────┐
│                    PRODUCTION SYSTEM                              │
│                                                                   │
│  ┌──────────────────┐   ┌──────────────────────────────────┐    │
│  │ API Gateway       │   │ MULTI-AGENT CORE                  │    │
│  │ REST + Streaming  │──▶│                                    │    │
│  │ Auth + Rate Limit │   │  Coordinator                      │    │
│  └──────────────────┘   │    ├── Agent 1 (Intake)            │    │
│                          │    ├── Agent 2 (Analysis + RAG)    │    │
│  ┌──────────────────┐   │    ├── Agent 3 (Decision + HITL)   │    │
│  │ MEMORY SYSTEM     │   │    └── Agent 4 (Communication)    │    │
│  │ Tier 1: Working   │◀─┤                                    │    │
│  │ Tier 2: Episodic  │   │  Guardrails: Input + Output       │    │
│  │ Tier 3: Procedural│   │  Circuit Breaker                  │    │
│  └──────────────────┘   └──────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────┐   ┌──────────────────────────────────┐    │
│  │ COST OPTIMIZER    │   │ OBSERVABILITY STACK               │    │
│  │ Haiku: simple     │   │ Trace every LLM + tool call       │    │
│  │ Sonnet: moderate  │   │ Langfuse / Arize dashboards       │    │
│  │ Opus: complex     │   │ Latency, cost, success rate       │    │
│  │ Cache: frequent   │   │ Drift detection                   │    │
│  └──────────────────┘   └──────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────┐   ┌──────────────────────────────────┐    │
│  │ DEPLOYMENT        │   │ EVALUATION                        │    │
│  │ Docker + Cloud Run│   │ 100-case test suite                │    │
│  │ Queue processing  │   │ Per-type accuracy                  │    │
│  │ Webhooks          │   │ Regression detection               │    │
│  └──────────────────┘   └──────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### ANIMATION 1: Full System Request Flow (hero animation — the most complex in the course)
**Purpose**: Show a single request flowing through the ENTIRE production system
**Behavior**: 
- Request enters via API Gateway → auth check → rate limit check
- Flows into coordinator → delegates to agents 1-4 sequentially
- Memory system is accessed at Agent 2 (episodic: "similar past cases") and Agent 3 (procedural: "learned quirks")
- Model router selects Haiku for Agent 1 (simple parsing), Sonnet for Agent 2 (RAG analysis), Opus for Agent 3 (complex decision)
- Guardrails check at input and output
- HITL gate for medium-confidence
- Every step generates a trace span (shown as nested bars on the right side)
- Response streams back to user
- Cost counter ticks up at each LLM call
**Duration**: 15-20 seconds, step-through-able

### ANIMATION 2: Three-Tier Memory Activation
**Purpose**: Show when each memory tier activates during a request
**Behavior**: Brain diagram with 3 layers. As the request flows:
- Working memory lights up (current case state)
- Episodic memory searches and returns similar past cases
- Procedural memory activates for learned patterns ("Aetna always requires ICD-10 specificity level 4")

### ANIMATION 3: Model Router Decision Tree
**Purpose**: Show how requests get routed to different Claude models based on complexity
**Behavior**: Request enters → complexity assessment → Haiku (simple, fast, cheap) / Sonnet (moderate) / Opus (complex, slow, expensive). Show cost per call next to each route.

### ANIMATION 4: Trace Waterfall
**Purpose**: Show a real observability trace with nested spans
**Behavior**: Horizontal waterfall chart showing:
- Total request: 4.2 seconds
  - Coordinator: 0.1s
  - Agent 1 (Haiku): 0.3s
    - Tool: parse_request: 0.05s
  - Agent 2 (Sonnet): 1.8s
    - Tool: search_rag: 0.4s
    - Tool: match_criteria: 0.2s
    - LLM reasoning: 1.2s
  - Agent 3 (Opus): 1.5s
    - Memory lookup: 0.3s
    - LLM decision: 1.2s
  - Agent 4 (Haiku): 0.5s
    - Output guardrails: 0.1s

### ANIMATION 5: Evaluation Dashboard
**Purpose**: Show the 100-case test suite results
**Behavior**: Animated dashboard building up: overall accuracy → per-type breakdown (some types at 98%, one at 72% — masked by aggregate) → regression detection (comparison to previous version)

---

## CAPSTONE-9: "Behavioral Health UM Modernization" — Legacy Monolith → Distributed Platform (★★★★★)

Bonus capstone. Standalone (no domain letter); uses DOMAIN A-BH from `03-capstone-domains.md`.
Six animations, and the ordering matters — 1 and 2 establish what is being produced, 3 through 6
each carry one trap.

### ARCHITECTURE DIAGRAM (static, shown at the top)

Two source trees on the left, both marked READ-ONLY with a padlock; the agent in the middle; one
emitted workspace on the right.

```
  reference-umlite/  ─┐                                  ┌─→ bh-um-lite/
  (architecture donor) │   coordinator (NO file tools)   │   apps/ camunda/ libs/ infra/
                       ├──→  8 subagents, isolated ctx ──┤
  bhauthtrack/        ─┘     5 hooks, 10 parity checks   └─→ THE GAP REGISTER
  (domain donor)                                              + manual-review queue
```

Label the coordinator "no file tools" explicitly — that is a design decision, not an omission.
Label the gap register as the deliverable, visually equal to the workspace and not subordinate.

### ANIMATION 1: Monolith → Distributed, and the Transaction That Is Severed (hero animation)

**Purpose**: Show that decomposition is a decision about GUARANTEES, not about files.
**Behavior**: `submitAndDecide()`'s five writes appear as one block, then move one at a time to the
service that will own them. Write 3 (the Part 2 consent) turns red and stays attached to write 1.
Final state: four of five in `bh-case-svc`, one crossing a seam with an outbox.
**Key beat**: the closing note says the authorization/consent seam was **rejected** — recording a
rejection is a result, not an omission.

### ANIMATION 2: Fifteen Capabilities Resolve Into Four Verdicts

**Purpose**: The deliverable, and the discomfort of its distribution.
**Behavior**: Capability rows resolve one at a time into colour-coded verdict chips. ORDER THEM so
`port-as-is` lands first and `must-not-port` last — the comfortable verdicts arrive early and the
uncomfortable shape emerges.
**Key beat**: on the first `must-not-port`, the note states that the tool REJECTS the entry without
a named harm. Closing note gives the distribution and says a mostly-`port-as-is` register means the
architecture was read and the domain was not.

### ANIMATION 3: One Case, Two Engines, Two Answers

**Purpose**: Trap 1 — a stateful first-match ladder becoming a decision table.
**Behavior**: Split view. Left, the ladder accumulates: C-SSRS 4 (+6), dim1 = 3 (+4), score 10 —
then branch 7a commits to 3.7 and 7b is marked "true as well, never reached". Right, the flattened
table lights BOTH rows red. Final step tightens the lower row with a named derived input and it
turns green.
**Key beat**: `FIRST` gives the right answer **only while the row order survives**. Reduced-motion
static must show both rows matching simultaneously — that is the whole point.

### ANIMATION 4: The Narrative Clears HIPAA, Then Fans Out

**Purpose**: Trap 5 — 42 CFR Part 2 reaching sinks with no consent scope.
**Behavior**: Three stages (submit → HIPAA passes → consent scope is AUTH_DECISION_ONLY), then four
sinks light in sequence: application log, event payload, search index, audit table.
**Key beat**: the closing note says the monolith had ONE sink and nobody made it worse — fan-out is
what a distributed architecture does with a field, so the count going UP is the expected shape.

### ANIMATION 5: Knowledge Plane and Control Plane

**Purpose**: The Skill-vs-agent decision, which is a learning objective in its own right.
**Behavior**: Two columns. Left fills with the four Skills; right fills with the coordinator, the
eight subagents, the hooks, the gate, the budget.
**Key beat**: closing note is the rule of thumb — "decides, branches, parallelizes or blocks →
agent; same steps every time → Skill."

### ANIMATION 6: A Role Guard Lifts Out of a Template

**Purpose**: Trap 9 — business rules living in JSP scriptlets and JSTL guards.
**Behavior**: Five rules found in `decision.jsp`, each moving from "still in the template" to a
named new home: a BPMN candidate group, an API omission, computed fields.
**Key beat**: closing note gives the count — 20 rules across 7 screens, **11 with no server-side
enforcement at all** — and states that moving one to `*ngIf` has moved nothing.

### Notes for this capstone specifically

- **No architecture animation of the agent topology.** Capstone 8 covers subagent fan-out and this
  module links to it rather than repeating it. Six animations is already the ceiling.
- **Every animation's closing step is a written finding**, not a "done" state. The animations here
  carry argument, not just mechanism.
- Reduced-motion static frames must show the FINAL state of each, because in every one of these the
  final state is the finding.

---

## Animation Rules for ALL Capstones

1. **Architecture diagram appears FIRST** — before any build steps. The student sees the blueprint before building.
2. **Hero animation** plays when the student first opens the capstone page (auto-play once, then controls available).
3. **All animations have**: play/pause/restart/step-through controls.
4. **`prefers-reduced-motion`**: Shows static version of each diagram with all labels visible.
5. **Interactive elements**: Where marked "interactive", the student can click/type to explore (e.g., embedding space in CAPSTONE-2, HITL dashboard in CAPSTONE-4).
6. **Consistent styling**: All capstone animations use the same visual language as module animations (same colors, fonts, node styles from the design system).
7. **Progressive complexity**: CAPSTONE-1 has 2 simple animations. CAPSTONE-5 has 5 complex ones. The visual complexity matches the project complexity.
8. **Domain variants**: Architecture diagrams show the GENERIC structure. Domain-specific details (tool names, data fields) are labeled but the STRUCTURE is the same across domains A/B/C.
