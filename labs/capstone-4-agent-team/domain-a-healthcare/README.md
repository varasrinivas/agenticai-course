# Capstone 4-A: Multi-Agent Pre-Auth Pipeline (Healthcare)

## What You'll Build

A 4-agent pre-authorization pipeline that takes a raw clinical request, runs it through Intake → Clinical Criteria → Decision (with HITL routing) → Communication (with a HIPAA output guardrail), and emits an approve / deny / request_info determination.

All four agents run through the **same `run_agent` Claude tool-use loop**, so the circuit breaker is enforced at every hand-off. The Communication Agent must call `check_hipaa_compliance` before sending — and the orchestrator re-checks it as a belt-and-suspenders defense.

| Component | What it does |
|---|---|
| **Agent 1 — Intake** | Validates the raw request, verifies member eligibility, verifies provider NPI |
| **Agent 2 — Clinical Criteria** | Fetches the policy for the procedure, evaluates each criterion against the clinical notes |
| **Agent 3 — Decision** | LLM-driven routing: `>0.90` → auto-approve, `0.70-0.90` → HITL, `<0.70` → deny |
| **Agent 4 — Communication** | Drafts the determination letter, runs the HIPAA guardrail, then sends |
| **Circuit breaker** | 3 consecutive `run_agent` failures → halt the pipeline |
| **HITL** | Borderline decisions pause for a CLI reviewer before finalizing |
| **HIPAA guardrail** | `check_hipaa_compliance` flags PII leakage, missing keywords, format issues |

## Time Estimate

**2–3 hours** for the full build, ~30 minutes if you copy from `solution/` and just want to run + experiment.

## Prerequisites

- **M14** (Multi-agent systems) — pipeline architecture, state passing, hand-offs
- **M16** (Input guardrails) — schema validation, duplicate detection
- **M17** (HITL & guardrails) — the HITL flow and circuit breaker pattern
- **M18** (Evaluation) — the pytest suite
- Python **3.10+**
- An Anthropic API key

## Files You'll Create

```
domain-a-healthcare/
├── starter/                  # Where you start (skeletons + TODOs)
│   ├── mock_tools.py         # 11 tools across 4 agents
│   ├── pipeline.py           # PipelineState, circuit breaker, HITL, run_agent, run_pipeline
│   ├── test_pipeline.py      # 6 pytest cases (provided complete — your gate)
│   ├── requirements.txt
│   └── .env.example
├── solution/                 # Reference if stuck
│   ├── mock_tools.py
│   ├── pipeline.py
│   ├── mock_tools.ts         # Node.js version
│   ├── pipeline.ts
│   ├── test_pipeline.py
│   ├── requirements.txt
│   └── .env.example
└── expected_output/
    ├── happy_path_run.txt    # Sample TKA approval run
    ├── pytest_output.txt     # Expected `pytest -v` output
    ├── circuit_breaker.txt   # CB-tripped trace
    └── hipaa_block.txt       # Guardrail blocking an SSN-leaking letter
```

## Setup

```bash
cd starter
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add your real ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=$(cat .env | cut -d= -f2)  # or `set` on Windows
```

✅ Checkpoint: `python -c "import anthropic; print(anthropic.__version__)"` should print a version number ≥ 0.40.0.

## Lab Steps

### Step 1: Complete the mock tools (`mock_tools.py`)

The mock tools are the deterministic surface that the four agents call. Open `starter/mock_tools.py` and complete every `TODO` (six functions). Each docstring tells you the exact return shape.

```bash
# Verify partial progress as you go — these two tests don't need pipeline.py:
pytest test_pipeline.py::test_invalid_input_handling -v
pytest test_pipeline.py::test_hipaa_guardrail_blocks_ssn_leak -v
```

✅ Checkpoint: both tests should pass once `validate_auth_request`, `verify_member_eligibility`, and `check_hipaa_compliance` are correct.

⚠️ Troubleshooting:
- `MISSING_KEYWORD: approval letter must say 'approved'` failing — make sure your check_hipaa_compliance lowercases the body before checking.
- `[redacted-ssn]` not appearing — your SSN regex must use `\b` word boundaries.

### Step 2: Build the agent runner (`pipeline.py` — `run_agent`)

This is the single most important function in the whole pipeline. It wraps Claude's tool-use loop and records success/failure on the circuit breaker. All four agents flow through it.

The `run_agent` skeleton tells you exactly what shape the loop has — implement it line by line. Use `solution/pipeline.py` as a reference if you get stuck on the tool_use → tool_result message format.

```bash
# Verify the circuit breaker logic
pytest test_pipeline.py::test_circuit_breaker_trips -v
```

✅ Checkpoint: circuit-breaker test should pass — proves `check_circuit_breaker`, `record_failure`, `record_success` are correct.

### Step 3: Build the pipeline orchestrator (`run_pipeline`)

Wire all four agents together. This is the largest function in the file (~250 lines in the solution). Build it agent-by-agent:

1. Agent 1 (Intake) — wire intake_tools + handlers, call `run_agent`, populate `state.intake_output`
2. Agent 2 (Clinical) — wire clinical_tools + handlers, call `run_agent`, then directly evaluate each policy criterion
3. Agent 3 (Decision) — wire `compute_decision_confidence` as a tool with a scratchpad-capturing handler. The system prompt instructs the LLM to compute confidence and reply with a JSON object. Parse the reply, fall back to scratchpad
4. If `human_review_required`, call `human_review()` (offline step, OUTSIDE `run_agent`)
5. `finalize_determination(...)`
6. Agent 4 (Communication) — wire `draft_determination_letter` + `check_hipaa_compliance` + `send_notification` as tools with scratchpad handlers
7. After `run_agent` returns, the orchestrator re-checks the HIPAA guardrail. If `compliant=False`, set `state.stage = "error"` and record the issues

### Step 4: Run the full demo

```bash
echo demo | python pipeline.py
```

Expected (compare to `expected_output/happy_path_run.txt`):
```
[INTAKE] Starting...
[INTAKE] Complete.
[CLINICAL] Starting...
[CLINICAL] Complete.
[DECISION] Starting...
[DECISION] Complete.
[COMMUNICATION] Starting...
[COMMUNICATION] Complete.
[PIPELINE] Complete! Determination: APPROVE
```

### Step 5: Run the full test suite

```bash
pytest test_pipeline.py -v
```

Expected: all **6 tests** pass.

## Final Verification

```bash
pytest test_pipeline.py -v && echo "---" && echo demo | python pipeline.py
```

Expected: 6 tests pass, then a clean APPROVE run on the sample TKA case.

## What You Built

A production-shaped multi-agent pipeline with:
- 11 deterministic mock tools split across 4 agents
- A unified `run_agent` Claude tool-use runner
- Circuit breaker enforced at every transition (3 failures → halt)
- HITL routing for borderline confidence (70–90%)
- A HIPAA output guardrail that blocks PII leaks before sending
- 6 pytest cases covering the happy path, denial, HITL, circuit breaker, invalid input, and the SSN-redaction guardrail

## Going Further (Optional)

- Replace the deterministic clinical-evidence keywords with embeddings + similarity threshold
- Add Pydantic models for `PipelineState` for typed access
- Replace the in-process circuit breaker with Redis so it works across pods
- Add OpenTelemetry tracing around `run_agent` so you can see per-agent latencies
- Wire a real HITL queue (Slack approvals, web dashboard) instead of CLI `input()`

## Optional Sub-Lab: Agent SDK Behavior Tests

Once your manual `run_agent` loop and 6 pytest cases pass, see [`sdk_tests/`](./sdk_tests/) for a hands-on demo of how the **Claude Agent SDK** can be used to verify agent behavior:

- `test_tool_order.py` — `PreToolUse` hooks assert the Communication agent calls `check_hipaa_compliance` BEFORE `send_notification`
- `test_safety_gate.py` — `can_use_tool` callback denies production channels in dev and demonstrates input rewriting

The sub-lab ports the Communication agent from `solution/pipeline.py` to the SDK and exercises it with realistic test scenarios. Total cost: < $0.01 per full run on Haiku.

## Next

Continue to [Capstone 4-B: B2B Order Lifecycle Pipeline →](../domain-b-ecommerce/) or jump to [Capstone 5-A: Production Pre-Auth System →](../../capstone-5-production-agent/domain-a-healthcare/).
