# Capstone 3: Reasoning Agent — ReAct Multi-Step Problem Solver

## What You'll Build

In this capstone, you will build a **ReAct (Reasoning + Acting) agent** that solves complex, multi-step problems by thinking through each step, selecting the right tool, observing the result, and iterating until it reaches a well-justified conclusion.

Unlike simple single-tool agents, your ReAct agent will:
- **Plan** its approach before acting
- **Chain** multiple tool calls together, where each call depends on previous results
- **Reason** about intermediate observations to decide what to do next
- **Terminate** gracefully with a structured recommendation
- **Log** a full reasoning trace so you can inspect every decision

You will pick **one** of three industry domains:

| Domain | Scenario | Tools |
|--------|----------|-------|
| **A — Healthcare** | Pre-Authorization Decision Support Agent | `lookup_clinical_criteria`, `verify_diagnosis_match`, `check_network_status`, `get_benefit_summary`, `generate_auth_recommendation` |
| **B — Ecommerce** | Order Exception Resolution Agent | `get_order_details`, `query_warehouse_inventory`, `track_shipment`, `get_contract_pricing`, `check_quality_hold_status`, `draft_customer_notification` |
| **C — UCC Data** | Entity Resolution Agent | `search_filings_by_name`, `fuzzy_match_score`, `get_filing_details`, `get_business_registry_data`, `merge_entity_profile` |

Each domain gives you 5-6 tools and a realistic mock dataset. The agent must reason through 5-8 steps to reach its final answer.

---

## Prerequisites

- Modules M01 through M13 completed (especially M06: Tool Use, M12: ReAct Pattern, M13: Planning)
- Python 3.10+ installed
- Node.js 18+ installed (for the JS solution)
- Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- `pip install anthropic` (Python SDK)
- `npm install @anthropic-ai/sdk` (Node.js SDK)

---

## Setup

```bash
# Clone or navigate to this directory
cd labs/capstone-3-reasoning-agent

# Pick your domain
cd domain-a-healthcare   # or domain-b-ecommerce or domain-c-ucc

# Install dependencies
pip install anthropic

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start with the starter code
cd starter
```

---

## Step-by-Step Lab Instructions

Pick ONE domain, then follow these steps:

### Step 1: Define 5-6 Tools with Anthropic Tool Schemas

Open `starter/tools.py`. You will see tool definitions already written in Anthropic's tool schema format. Each tool has:
- A `name` (snake_case)
- A `description` (tells Claude when and why to use this tool)
- An `input_schema` (JSON Schema defining required parameters)

**Your task:** Review each tool schema. Understand what each tool does and what parameters it expects. The schemas are complete — you do not need to modify them.

### Step 2: Implement Mock Tool Functions with Realistic Data

Open `starter/mock_data.py` to see the mock dataset. Then complete the TODO sections in `starter/tools.py`:
- Each tool function should look up data from `mock_data.py`
- Return realistic results matching what a real API would return
- Handle missing or invalid inputs gracefully (return error messages, not exceptions)

### Step 3: Build the ReAct Loop (Think, Act, Observe, Repeat)

Open `starter/agent.py`. The skeleton has the structure of a ReAct agent. Complete the TODOs:

1. **Send the user query + tools to Claude** using the Messages API
2. **Parse the response** — check for `tool_use` content blocks
3. **Execute the requested tool** by dispatching to your tool functions
4. **Append a `tool_result`** message back to the conversation
5. **Loop** until Claude responds with `end_turn` (no more tool calls)

The key insight: each iteration, Claude sees ALL previous reasoning + tool results, so it can plan its next move based on accumulated evidence.

### Step 4: Add Reasoning Trace Logging

Add logging so you can see the agent's full reasoning chain:
- `[THINK]` — Claude's text reasoning before a tool call
- `[ACT]` — Which tool was called with what arguments
- `[OBSERVE]` — What the tool returned
- `[ANSWER]` — The final recommendation

Print each step with a step number so you can follow the chain.

### Step 5: Handle Multi-Step Tool Chains

Test your agent with queries that require multiple tools. For example:
- Domain A: "Process pre-auth for CPT 27447 with diagnosis M17.11"
- Domain B: "Investigate exception on order ORD-2024-1847"
- Domain C: "Resolve entity: Acme Corp across all state filings"

Verify that your agent:
- Calls tools in a logical order (not random)
- Uses results from earlier tools to inform later tool calls
- Does not call the same tool twice with identical arguments

### Step 6: Add Termination Conditions and Error Recovery

Add safeguards:
- **Max iterations:** Stop after 15 tool calls to prevent infinite loops
- **Error recovery:** If a tool returns an error, the agent should note it and try an alternative approach
- **Graceful termination:** If the agent cannot reach a conclusion, it should say so with what it found so far

---

## Final Verification

Run your completed agent:

```bash
# From the starter/ directory (after completing TODOs)
python agent.py

# Or run the solution to see expected behavior
cd ../solution
python agent.py
```

Compare your output against `expected_output/reasoning_trace.txt`. Your agent should:
- [ ] Call at least 3 different tools
- [ ] Show a logical reasoning chain (each step builds on the last)
- [ ] Produce a final recommendation with justification
- [ ] Complete in under 15 iterations
- [ ] Handle edge cases without crashing

---

## What You Built

By completing this capstone, you have built:

1. **A ReAct agent** that interleaves reasoning and action in a loop
2. **Multi-tool orchestration** where tool selection depends on prior results
3. **Reasoning trace logging** for debugging and auditing agent decisions
4. **Termination logic** that prevents runaway loops and handles errors
5. **Domain-specific problem solving** with realistic industry data

These are the same patterns used in production agent systems for decision support, exception handling, and data reconciliation.

---

## Next Steps

Continue to **Capstone 4: Deployment Agent** where you will take an agent like this one and deploy it to Docker, GCP Cloud Run, and AWS Lambda.
