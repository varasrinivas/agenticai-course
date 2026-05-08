# CAPSTONE-7: Agent Evolution — Build the Same Agent Three Ways

**Domain**: C — Public Records / UCC Data Engineering
**Difficulty**: ★★★★★ (Comprehensive, ties the entire course together)
**Skills Practiced**: M05, M12, M15B, M16-M17, M19, M21, M22B, M25, M26
**Estimated Time**: 6-8 hours across 3 sessions (one session per iteration)
**Prerequisites**: All modules M01-M27 recommended
**Position**: FINAL capstone — graduation project

---

## The Concept

The student builds ONE agent — the UCC Filing Risk Analyzer — THREE times. Same tools, same mock data, same business problem. Each iteration uses a more advanced approach.

Iteration 1: Raw API Loop (M15B way) — ~3 hours, ~250 lines
Iteration 2: Agent SDK + Claude Code (M25-M26 way) — ~2 hours, ~120 lines
Iteration 3: Spec-Driven (production way) — ~1 hour, ~100 lines of spec

After all three, the student has the SAME working agent built three ways and compares code size, dev time, flexibility, and control.

---

## Choose Your Scenario (same agent, same 3 iterations, different domain)

The student picks ONE scenario. All three use the same iterative structure (raw → SDK → spec) but with different business problems, tools, and mock data.

### Scenario A: Healthcare Pre-Auth Decision Agent
An agent that takes a pre-authorization request (procedure CPT code, diagnosis ICD-10 code, patient info) and reasons through the decision: looks up clinical criteria from payer policies, matches diagnosis against criteria, checks provider network status, verifies benefit coverage, and generates a structured determination (approve/deny/request-info) with clinical justification.

Tools:
- `lookup_clinical_criteria(cpt_code, payer)` — returns approval criteria for the procedure
- `verify_diagnosis_match(icd10_code, criteria)` — checks if diagnosis meets medical necessity
- `check_network_status(provider_npi, payer)` — returns in-network/out-of-network status
- `get_benefit_summary(member_id, cpt_code)` — returns coverage, copay, deductible status
- `generate_determination(case_data)` — produces approve/deny/info-request with rationale

Mock data: 15 mock pre-auth requests across 5 procedures (MRI, knee replacement, specialty drug, cardiac cath, physical therapy), 3 payers (Aetna, UnitedHealth, BlueCross), with realistic CPT/ICD-10 codes.

HIPAA compliance callouts: PII handling in hooks, PHI redaction, audit trail requirements.

### Scenario B: B2B Order Exception Agent
An agent that investigates order exceptions: identifies the exception type (delayed shipment, partial delivery, pricing discrepancy, quality hold), gathers data from ERP and carrier systems, determines root cause, and proposes resolution with customer communication draft.

Tools:
- `get_order_details(po_number)` — returns line items, status, dates
- `track_shipment(tracking_number)` — returns carrier status and location
- `check_contract_pricing(customer_id, sku)` — returns contract vs invoiced price
- `query_inventory(sku, warehouse)` — returns available stock
- `draft_notification(customer_id, exception_type, resolution)` — generates email

Mock data: 10 mock POs with 3 exception types, carrier tracking data, contract pricing for 5 customers.

### Scenario C: UCC Filing Risk Analyzer (default)
The existing scenario — delinquency risk assessment using UCC filing data and ML model.

Tools: search_filings, predict_delinquency, get_filing_details (as already defined).

---

## The Business Problem (varies by scenario, same structure)

Scenario A: "Should this pre-auth for knee replacement (CPT 27447) with diagnosis M17.11 be approved under Aetna?"
Scenario B: "PO-2024-5678 has a pricing discrepancy. Investigate and resolve."
Scenario C: "Assess the delinquency risk for Acme Corporation using UCC filing data."

Each scenario requires: search relevant data, reason through multi-step logic, call a domain model, check specific records, and generate a narrative report. The tools differ but the PATTERN is identical. All three iterations (raw, SDK, spec) work the same regardless of scenario.

---

## ITERATION 1: Raw API Loop (Session 1, ~3 hours)

Step 1: Setup + mock data + train pickle model (15 min)
Step 2: Define tools as JSON Schema + execution functions (15 min)
Step 3: Build the while loop — check stop_reason, execute tools, append messages (45 min)
Step 4: Add guardrails manually — input validation, PII redaction, cost cap, circuit breaker (30 min)
Step 5: Add logging manually — timestamped tool calls, audit_log.jsonl (15 min)
Step 6: Add multi-turn — conversation history, sliding window (15 min)
Step 7: Deploy as FastAPI + Docker (20 min)

Iteration 1 Metrics:
- Files: 7 | Lines: ~250 | Time: ~3 hours
- Everything hand-coded, full understanding, full control

### Debugging in Iteration 1: Print Statements + Manual Inspection
When the agent gives wrong output, the student debugs by:
- Adding print() statements in the while loop to see each tool call and result
- Inspecting the messages list to see what Claude received vs what it returned
- Checking stop_reason at each turn — is it looping forever? stopping too early?
- Reading the raw API response JSON to see tool_use blocks
- Common bugs: wrong tool_result format, missing tool_use_id, message order wrong

Debug exercise: Introduce a bug (wrong tool_use_id in tool_result) and watch the agent fail. Fix it by reading the error message and tracing the message flow.

```python
# Debug helper — add to agent.py
def debug_turn(turn_num, response, messages):
    print(f"\n=== TURN {turn_num} ===")
    print(f"stop_reason: {response.stop_reason}")
    for block in response.content:
        if block.type == "tool_use":
            print(f"  TOOL: {block.name}({block.input})")
        elif block.type == "text":
            print(f"  TEXT: {block.text[:100]}...")
    print(f"  Messages in history: {len(messages)}")
    print(f"  Total tokens: {response.usage.input_tokens + response.usage.output_tokens}")
```

---

## ITERATION 2: Agent SDK + Claude Code (Session 2, ~2 hours)

Step 8: Create CLAUDE.md via Claude Code (10 min)
Step 9: Build agent with @agent.tool decorators via Claude Code (15 min)
Step 10: Add hooks via Claude Code — logging, blocking, PII redaction, audit (20 min)
Step 11: Add sessions via Claude Code — multi-turn + fork (15 min)
Step 12: Create slash commands — /run-agent, /test-agent, /eval-agent (15 min)
Step 13: Deploy via Claude Code — FastAPI + Docker (15 min)

Iteration 2 Metrics:
- Files: 8 | Lines: ~120 | Time: ~2 hours
- Same output as Iteration 1, half the code, Claude Code did the work

### Debugging in Iteration 2: Hooks + Anthropic Console Web UI
The SDK abstracts the loop — you cannot print inside it. Instead you debug through:

**A. Hooks as Debug Probes**
Hooks fire at every tool call. Add a verbose debug hook:
```python
@agent.hook("pre_tool_use")
def debug_pre(tool_name, tool_input):
    print(f"[DEBUG PRE] {tool_name}: {tool_input}")
    return True

@agent.hook("post_tool_use")  
def debug_post(tool_name, tool_input, tool_result):
    result_preview = str(tool_result)[:200]
    print(f"[DEBUG POST] {tool_name} -> {result_preview}")
    return tool_result
```

This is BETTER than Iteration 1 print statements because hooks are modular — remove them when done, the agent code stays clean.

**B. Anthropic Console Web UI (console.anthropic.com)**
The Anthropic Console shows every API call your agent makes:
- Go to console.anthropic.com > Logs
- Filter by your API key
- See every messages.create() call with full request/response
- Click any call to inspect: input messages, tool definitions, Claude's response, token usage, latency
- Compare successful vs failed calls side-by-side

Debug exercise: The agent calls search_filings but gets 0 results when it should find 5. Steps:
1. Check Console > Logs — find the failed call
2. Inspect the tool_use block — what did Claude pass as debtor_name?
3. Found: Claude sent "acme" (lowercase) but mock data has "ACME CORPORATION" (uppercase)
4. Fix: update search_filings to do case-insensitive matching
5. Re-run — Console shows the fix working

**C. Langfuse Traces (if instrumented in M19)**
If the student added Langfuse tracing in M19:
- langfuse.com dashboard shows the full agent trace as a waterfall
- Each tool call is a span with timing, input, output
- Can compare traces across runs — "why did today's run take 12 seconds vs yesterday's 4?"

**D. Claude Code /run-agent with Verbose Mode**
The /run-agent slash command can include a --verbose flag:
```
/run-agent --verbose "What is the risk for Acme Corporation?"
```
Shows: every tool call, every hook fire, every token count, total cost, total time.

---

## ITERATION 3: Spec-Driven (Session 3, ~1 hour)

Step 14: Write agent-spec.md — 12-section template covering tools, hooks, guardrails, sessions, API, deployment, tests, eval (30 min)
Step 15: One Claude Code command generates everything — 15-20 files (10 min)
Step 16: Review + iterate — update spec, targeted regeneration (15 min)
Step 17: Deploy + compare — same curl, same output (15 min)

Iteration 3 Metrics:
- Files: ~18 (generated) | Lines you wrote: ~100 (spec only) | Time: ~1 hour
- Same output, spec IS the documentation

### Debugging in Iteration 3: Spec Review + Regeneration
When generated code has bugs, the student debugs differently:

**A. Spec vs Code Comparison**
```
Read agent-spec.md and compare it to the generated agent.py. 
Report any deviations where the code does not match the spec.
```
Claude Code reads both and tells you exactly what diverged. The spec is the truth — if the code deviates, the code is wrong.

**B. Test-Driven Debugging**
The spec includes test definitions. When tests fail:
```
Test test_name_variations failed: expected 9 filings, got 5.
Read agent-spec.md section 3 (Tools) for the search_filings spec.
Read the generated search_filings function. Find why it misses 
4 filings and fix it.
```
Claude Code reads the spec, reads the code, identifies the mismatch, and fixes it.

**C. Eval-Driven Debugging**
Run the eval suite:
```
/eval-agent
```
Output shows: scenario 6 scored 2/5 — "agent did not try DBA variations."
Fix: update the spec system prompt to be more explicit about DBAs, then:
```
I updated the system prompt in agent-spec.md to explicitly mention 
DBA variations. Regenerate only agent.py with the updated prompt.
```

**D. Console + Langfuse (same as Iteration 2)**
All the same debugging tools from Iteration 2 work here because the generated code uses the same SDK and hooks.

**The Debugging Evolution:**
| Iteration | Primary Debug Method | Secondary | Speed |
|---|---|---|---|
| 1 Raw | print() in the loop | Manual message inspection | Slow (find the line) |
| 2 SDK | Hooks + Console Web UI | Langfuse traces | Medium (modular probes) |
| 3 Spec | Spec vs code comparison | Tests + evals + Console | Fast (Claude Code finds it) |

---

## The Comparison Table

| Metric | Iteration 1: Raw | Iteration 2: SDK | Iteration 3: Spec |
|---|---|---|---|
| Lines YOU wrote | ~250 | ~120 | ~100 (spec only) |
| Time to build | ~3 hours | ~2 hours | ~1 hour |
| Agent output | Baseline | Same | Same |
| Guardrails | Inline code | Hooks (modular) | Hooks (generated) |
| Multi-turn | Manual history | SDK sessions | SDK sessions (generated) |
| New tool | Edit 3 files | One command | Update spec |
| Tests | Manual | Claude Code generated | Spec generated |
| Documentation | Separate | CLAUDE.md | Spec IS docs |
| Control | Full | SDK-managed | Least (reviewable) |
| Understanding needed | Every line | SDK abstractions | Architecture-level |
| Debugging | print() in loop | Hooks + Console Web UI + Langfuse | Spec comparison + tests + evals |

---

## Key Takeaway

All three produce the SAME agent. The difference:
- Iteration 1 teaches WHAT an agent is (deep understanding)
- Iteration 2 teaches HOW to build efficiently (SDK + tools)
- Iteration 3 teaches HOW production teams work (spec-driven)

You need all three. Skip Iteration 1 and you cannot debug Iteration 3. Skip Iteration 3 and you are 10x slower.

---

## Animations
1. Three-lane evolution — code shrinking, capabilities staying same
2. Code size waterfall — 250 to 120 to 100+300 generated
3. Time comparison — 3 hours to 2 hours to 1 hour
4. Architecture diagrams per iteration
5. Spec-to-code flow

## Grading
- Iteration 1: 25% (loop works, guardrails, deployed)
- Iteration 2: 25% (hooks, sessions, slash commands, deployed)
- Iteration 3: 25% (spec complete, generated code runs, deployed)
- Comparison table: 15% (honest metrics)
- Reflection: 10% (what they learned)
