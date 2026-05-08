# Spec-Driven Agent Development

This content should be added to M25 (Claude Code) as an advanced section showing how to build agents by writing a specification document and letting Claude Code generate everything from it.

## The Idea

Instead of building agents piece by piece, the student writes a SPEC document that describes:
- What the agent does
- What tools it has
- What guardrails it needs
- How it should be deployed
- What tests to run

Then one Claude Code command generates the ENTIRE agent project from the spec.

This mirrors real production workflows where architects write design docs and engineers implement. With Claude Code, the architect writes the spec and Claude Code IS the engineer.

## The Pattern

```
Step 1: Write agent-spec.md (the blueprint)
Step 2: claude "Read agent-spec.md and build everything"
Step 3: Review generated code
Step 4: Iterate on the spec → regenerate
```

## Hands-On: Build an Agent from a Spec (30 min)

### Step 1: Write the Spec (10 min)

The student creates `agent-spec.md` — a single document that describes the entire agent:

```markdown
# Agent Specification: UCC Filing Risk Analyzer

## Overview
An AI agent that assesses delinquency risk for business entities by 
searching UCC filing records, running an ML prediction model, and 
generating narrative risk reports.

## Agent Configuration
- Model: claude-sonnet-4-20250514
- Framework: Anthropic Agent SDK
- Max tool calls per request: 10
- Max tokens per response: 4096

## System Prompt
You are a credit risk analyst agent specializing in UCC filings. When 
assessing risk: search for name variations including abbreviations and 
DBAs, gather filing statistics, run the ML model, examine the riskiest 
filings, and write a narrative report citing specific evidence.

## Tools

### search_filings
- Description: Search UCC filings by debtor name with partial matching
- Parameters: debtor_name (string, required), state (string, optional)
- Returns: List of filing objects with filing_number, debtor_name, state, 
  filing_type, status, filing_date, lapse_date, collateral, secured_party
- Mock data: 9 filings for Acme Corporation across NY, CA, TX, FL 
  including one DBA variant. 2 filings for Pinnacle Industries. 
  1 filing for Sunrise Holdings.

### get_filing_details
- Description: Get full details for a specific filing by filing number
- Parameters: filing_number (string, required)
- Returns: Complete filing record

### predict_delinquency
- Description: Run ML delinquency prediction model
- Parameters: active_filing_count (int), state_count (int), 
  collateral_types (int), filing_age_years (float), 
  amendment_frequency (float), months_to_lapse (float)
- Returns: probability (float), prediction (HIGH/MEDIUM/LOW RISK)
- Implementation: Load scikit-learn RandomForest from pickle file

## Hooks

### PreToolUse: Logging
- Log every tool call with timestamp, tool name, input parameters
- Format: [ISO timestamp] TOOL_CALL: tool_name(params)

### PreToolUse: Input Validation
- Block search_filings calls where debtor_name is less than 3 characters
- Return error message: "Query too broad"

### PostToolUse: PII Redaction
- Scan all tool results for SSN patterns (NNN-NN-NNNN)
- Replace with [SSN REDACTED]
- Scan for phone numbers (NNN-NNN-NNNN)
- Replace with [PHONE REDACTED]

### PostToolUse: Audit Log
- Write every tool call and result to audit_log.jsonl
- Include: timestamp, tool_name, input, output_summary, token_count

## Sessions
- Support multi-turn conversations with session persistence
- Support session.fork() for what-if analysis
- Store session history in memory (no external database needed)

## API Wrapper
- Framework: FastAPI
- Endpoints:
  - POST /query — send question, get response (synchronous)
  - POST /query/stream — send question, get SSE streaming response
  - POST /chat — multi-turn with session_id
  - GET /health — health check
- Authentication: API key in X-API-Key header
- Rate limit: 10 requests per minute per API key

## Deployment
- Tier 1 (Local): Docker + DuckDB
  - Dockerfile with multi-stage build
  - docker-compose.yml with agent + dashboard containers
  - DuckDB for audit log storage
- Tier 2 (GCP): Cloud Run (document only, do not implement)
- Tier 3 (AWS): Lambda (document only, do not implement)

## Tests
- test_tools.py: Each tool returns valid data for known inputs
- test_agent.py: Agent finds all 9 Acme filings including DBA
- test_hooks.py: PreToolUse blocks short queries, PostToolUse redacts PII
- test_sessions.py: Follow-up questions maintain context across 3 turns
- test_api.py: Health check returns 200, /query returns valid JSON

## Evaluation Dataset
10 test questions in test_scenarios.json:
1. "What is the lien exposure for Acme Corporation?" — should find 9 filings
2. "Find filings for ACME CORP in California" — should find 2 CA filings
3. "What is the risk level for Pinnacle Industries?" — should return LOW/MEDIUM
4. "Compare Acme and Pinnacle risk profiles" — should compare both
5. "Find all filings in New York" — should find 4 NY filings
6. "What happens if Acme files a continuation on CA-2024-001?" — what-if analysis
7. "Are there any filings about to lapse?" — should identify imminent lapses
8. "Who is the secured party for the Florida filing?" — detail lookup
9. "Find filings for a company that does not exist" — should handle gracefully
10. "Summarize all filings across all states" — broad synthesis

## File Structure
ucc-risk-agent/
├── CLAUDE.md
├── .claude/commands/
│   ├── run-agent.md
│   ├── test-agent.md
│   └── eval-agent.md
├── agent.py
├── tools.py
├── hooks.py
├── mock_data.py
├── delinquency_model.pkl
├── server.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── tests/
│   ├── test_tools.py
│   ├── test_agent.py
│   ├── test_hooks.py
│   ├── test_sessions.py
│   └── test_api.py
└── test_scenarios.json
```

### Step 2: Generate Everything from the Spec (5 min)

```bash
claude
```

One command:
```
Read agent-spec.md and build the entire project. Create every file listed 
in the File Structure section. Implement every tool, hook, test, and endpoint 
exactly as specified. Use the Agent SDK. Create realistic mock data. Train and 
save the pickle model. Make every file runnable.
```

Claude Code reads the spec and generates 15+ files in one pass.

### Step 3: Verify (5 min)

```
/test-agent
```

All tests should pass. If any fail:

```
Fix the failing tests. Read agent-spec.md to understand the expected behavior.
```

Claude Code reads the spec, understands the intent, and fixes the code.

### Step 4: Iterate on the Spec (10 min)

The student modifies the spec and regenerates:

```markdown
# Add to agent-spec.md under Tools:

### check_lapse_dates
- Description: Find all filings approaching lapse within N months
- Parameters: months_ahead (int, default 12)
- Returns: List of filings with days_until_lapse for each
```

Then:
```
I added a new tool to agent-spec.md. Read the updated spec and add the 
check_lapse_dates tool to the project. Update tools.py, mock_data.py, 
add a test, and add an eval scenario for it.
```

Claude Code reads the diff and makes targeted changes — not a full regeneration.

## Why Spec-Driven Matters

### For Individual Developers
- Write WHAT you want, not HOW to build it
- Iterate at the design level, not the code level
- The spec is documentation AND source of truth
- Review and revise the spec → Claude Code handles the implementation

### For Teams
- Architects write specs, Claude Code implements
- Code reviews become spec reviews
- Onboarding: read the spec, not the code
- Spec changes are tracked in git alongside code changes

### For Production
- The spec is your living architecture document
- When you need to rebuild (new framework, new patterns), the spec transfers
- Compliance auditors can read the spec instead of the code

## The Spec-Driven Workflow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                 SPEC-DRIVEN DEVELOPMENT                   │
│                                                           │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │ agent-   │────▶│ Claude Code  │────▶│ Complete     │ │
│  │ spec.md  │     │ reads spec   │     │ Project      │ │
│  │          │     │ generates    │     │ (15+ files)  │ │
│  │ WHAT     │     │ everything   │     │              │ │
│  └──────────┘     └──────────────┘     └──────┬───────┘ │
│       ▲                                        │         │
│       │           ┌──────────────┐             │         │
│       └───────────│ Review +     │◀────────────┘         │
│    Update spec    │ Iterate      │  Run tests            │
│                   └──────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

"You just saw this pattern in action — this entire COURSE was built spec-driven. The prompt files (00-philosophy.md through 15-why-agents.md) are the spec. Claude Code generated the modules. The /fix-explanations command iterates. You're learning the pattern by experiencing it."
