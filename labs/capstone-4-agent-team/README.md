# Capstone 4: Agent Team — Multi-Agent Pipeline with Human-in-the-Loop

## What You'll Build

In this capstone, you will build a **4-agent pipeline** where specialized agents collaborate to process complex workflows end-to-end. Each agent has its own system prompt, tools, and ReAct loop. A typed `PipelineState` object flows between agents, accumulating data at each stage.

Your pipeline will include:
- **4 specialized agents**, each with 3 domain-specific tools
- **Typed pipeline state** (Pydantic model) that flows between agents
- **Human-in-the-loop (HITL) gate** that pauses for human review when confidence is low
- **Circuit breaker** that halts the pipeline when error rates exceed a threshold
- **Structured logging** at every agent transition
- **A coordinator** that orchestrates the full pipeline

You will pick **one** of three industry domains:

| Domain | Scenario | Agents | HITL Gate | Circuit Breaker |
|--------|----------|--------|-----------|-----------------|
| **A — Healthcare** | Pre-Auth Pipeline | Intake -> Clinical Criteria -> Decision -> Communication | Decision confidence < 80% | > 10% intake validation failures |
| **B — Ecommerce** | Order Pipeline | Order Intake -> Fulfillment Planning -> Exception Monitor -> Communication | Split-shipment needed | > 3 consecutive SLA violations |
| **C — UCC Data** | Data Pipeline | Ingestion -> Transformation -> Quality -> Reporting | Entity resolution confidence < 80% | Parse error rate > 10% |

Each domain gives you 4 agents with 3 tools each (12 tools total) and a realistic mock dataset with 15+ records including edge cases.

---

## Prerequisites

- Modules M01 through M14 completed (especially M12: ReAct Pattern, M14: Multi-Agent Systems)
- Capstone 3 completed (ReAct agent fundamentals)
- Python 3.10+ installed
- Node.js 18+ installed (for the JS coordinator)
- Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- `pip install anthropic pydantic` (Python dependencies)
- `npm install @anthropic-ai/sdk` (Node.js SDK)

---

## Setup

```bash
# Navigate to this directory
cd labs/capstone-4-agent-team

# Pick your domain
cd domain-a-healthcare   # or domain-b-ecommerce or domain-c-ucc

# Install dependencies
pip install -r starter/requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start with the starter code
cd starter
```

---

## Step-by-Step Lab Instructions

Pick ONE domain, then follow these steps:

### Step 1: Understand the Pipeline State Model

Open `starter/agents/__init__.py`. You will find a Pydantic `PipelineState` model that defines the typed state flowing between all 4 agents. Each agent reads from and writes to specific fields.

**Your task:** Read the state model. Understand which fields each agent produces and consumes. The model is complete — do not modify it.

### Step 2: Implement Agent 1 (Intake/Ingestion)

Open `starter/agents/agent1.py`. You will see:
- Tool schemas already defined in Anthropic format
- A system prompt tailored to the agent's role
- An agent class skeleton with TODOs for the ReAct loop

**Your task:** Complete the TODOs:
1. Implement the 3 tool handler functions using mock data
2. Build the ReAct loop: send messages to Claude, parse tool_use blocks, execute tools, append results
3. Update the `PipelineState` with this agent's outputs

### Step 3: Implement Agent 2 (Analysis/Planning)

Open `starter/agents/agent2.py`. Same structure as Agent 1 but with different tools and responsibilities.

**Your task:** Complete the TODOs. This agent reads the state produced by Agent 1 and adds its own analysis.

### Step 4: Implement Agent 3 (Decision/Quality)

Open `starter/agents/agent3.py`. This agent contains the **HITL gate**.

**Your task:** Complete the TODOs:
1. Implement the 3 tool handlers
2. Build the ReAct loop
3. Implement the HITL check: if the agent's confidence score is below the threshold, pause execution and prompt for human review using `input()`

### Step 5: Implement Agent 4 (Communication/Reporting)

Open `starter/agents/agent4.py`. The final agent in the pipeline.

**Your task:** Complete the TODOs. This agent reads the accumulated state and produces the final output artifacts.

### Step 6: Implement the Circuit Breaker

Open `starter/quality_gate.py`. The circuit breaker skeleton tracks error rates and trips when a threshold is exceeded.

**Your task:** Complete the TODOs:
1. Implement `record_success()` and `record_failure()`
2. Implement `is_tripped()` — returns True when the error rate exceeds the configured threshold
3. Implement `reset()` — resets the circuit breaker after a cooldown period

### Step 7: Wire the Coordinator

Open `starter/coordinator.py`. The coordinator orchestrates the 4 agents in sequence.

**Your task:** Complete the TODOs:
1. Initialize all 4 agents and the circuit breaker
2. Run each agent in sequence, passing the `PipelineState` between them
3. Check the circuit breaker before each agent transition
4. Log structured output at every stage transition
5. Handle HITL pauses from Agent 3

### Step 8: Test the Full Pipeline

Run the coordinator with the provided test cases:

```bash
# From the starter/ directory (after completing TODOs)
python coordinator.py

# Or run the solution to see expected behavior
cd ../solution
python coordinator.py
```

Test these scenarios:
1. **Happy path** — all agents process normally, no HITL pause, no circuit breaker
2. **HITL trigger** — a case that triggers human review (confidence below threshold)
3. **Circuit breaker trip** — feed multiple failing records to trip the breaker

---

## Final Verification

Compare your output against the files in `expected_output/`. Your pipeline should:

- [ ] Process a record through all 4 agents in sequence
- [ ] Show typed PipelineState growing at each stage
- [ ] Log every agent transition with timestamps
- [ ] Pause for HITL review when confidence is below threshold
- [ ] Resume after human approval or rejection
- [ ] Trip the circuit breaker after enough failures
- [ ] Halt gracefully when circuit breaker trips
- [ ] Each agent calls at least 2 tools per invocation
- [ ] Complete happy-path processing in under 20 iterations total

---

## What You Built

By completing this capstone, you have built:

1. **A multi-agent pipeline** with 4 specialized agents collaborating in sequence
2. **Typed state passing** using Pydantic models that grow as they flow through the pipeline
3. **Human-in-the-loop gates** that pause for review on low-confidence decisions
4. **Circuit breaker pattern** that halts processing when error rates spike
5. **Structured logging** for full pipeline observability
6. **An orchestrator/coordinator** that wires agents together with error handling

These are production patterns used in healthcare claims processing, supply chain orchestration, and data engineering pipelines.

---

## Next Steps

Continue to **Capstone 5: Deployment Agent** where you will take a multi-agent system like this one and deploy it to Docker, GCP Cloud Run, and AWS Lambda with monitoring and observability.
