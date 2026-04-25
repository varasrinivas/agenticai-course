# M17: Output Guardrails & Human-in-the-Loop — Lab

## What You'll Build
A guardrailed agent with output validation, cost controls, circuit breaker protection, and human-in-the-loop approval for uncertain decisions.

## Prerequisites
- Completed M16 (Input Guardrails)
- Python 3.10+ or Node.js 18+
- Anthropic API key configured

## Setup
```bash
cd labs/M17-output-guardrails-hitl
# Python
pip install -r ../../requirements.txt
# Node.js
npm install --prefix ../..
```

## Lab Steps

### Step 1: Build the Output Validator (15 min)
Open `starter/output_validator.py` (or `starter/output_validator.js` for Node.js).

You'll implement four validation checks for agent outputs:
- JSON structure validation against required fields
- Hallucination marker detection (low-confidence phrases)
- PII leakage detection in outputs
- Composite validation combining all checks

Fill in TODOs 1-6 to complete the validator.

**Test your work:**
```bash
python starter/output_validator.py
# or
node starter/output_validator.js
```

### Step 2: Build the Cost Controller (10 min)
Open `starter/cost_controller.py` (or `starter/cost_controller.js`).

You'll implement a cost tracking system using real Claude Sonnet pricing:
- $3.00 per 1M input tokens
- $15.00 per 1M output tokens
- $0.50 per-request budget cap

Fill in TODOs 1-5 to build the `CostController` class.

**Test your work:**
```bash
python starter/cost_controller.py
# or
node starter/cost_controller.js
```

### Step 3: Build the Circuit Breaker (15 min)
Open `starter/circuit_breaker.py` (or `starter/circuit_breaker.js`).

You'll implement the circuit breaker pattern with three states:
- **CLOSED**: Normal operation, failures are counted
- **OPEN**: Tripped after 3 consecutive failures, all calls rejected
- **HALF_OPEN**: After timeout expires, one test call is allowed

Fill in TODOs 1-7 to build the `CircuitBreaker` class with time-based recovery.

**Test your work:**
```bash
python starter/circuit_breaker.py
# or
node starter/circuit_breaker.js
```

### Step 4: Build the HITL Approval Gate (15 min)
Open `starter/hitl_gate.py` (or `starter/hitl_gate.js`).

You'll implement confidence-based routing for UCC entity matches:
- **Auto-approve**: confidence > 90% (exact matches)
- **HITL review**: confidence 70-90% (partial matches need human check)
- **Auto-deny**: confidence < 70% (too uncertain)

Fill in TODOs 1-6 to build the `HITLGate` class.

**Test your work:**
```bash
python starter/hitl_gate.py
# or
node starter/hitl_gate.js
```

### Step 5: Wire Everything Together (15 min)
Open `starter/guarded_agent.py` (or `starter/guarded_agent.js`).

You'll compose all four guardrails into a single `GuardedAgent` that:
1. Checks circuit breaker state before proceeding
2. Checks remaining budget before the API call
3. Calls the agent (mocked for testing)
4. Validates the output structure and content
5. Routes by confidence through the HITL gate

Fill in TODOs 1-8 to wire the complete guarded agent.

**Test your work:**
```bash
python starter/guarded_agent.py
# or
node starter/guarded_agent.js
```

Compare your output against `expected_output/guarded_agent_output.txt`.

## Final Verification
```bash
# Run the solution to see expected behavior
python solution/guarded_agent.py
# or
node solution/guarded_agent.js
```

## What You Built
- Output validator checking structure and content safety
- Cost controller with per-request budget cap ($0.50)
- Circuit breaker halting after 3 consecutive failures
- HITL gate with confidence-based routing
- Complete guarded agent composing all protections

## Next
-> M18: Evaluation & Testing
