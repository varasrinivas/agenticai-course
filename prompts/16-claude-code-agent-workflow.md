# Building Agents with Claude Code + Agent SDK

This content should be added to M25 (Claude Code) and M26 (Agent SDK) to show students how to use Claude Code as their development environment for building agents, AND how to combine Claude Code's project features with the Agent SDK.

## The Gap
M25 teaches Claude Code features (CLAUDE.md, commands, skills). M26 teaches Agent SDK (agent.tool, hooks, sessions). But neither shows:
1. How to use Claude Code to BUILD an agent project from scratch
2. How CLAUDE.md configures an agent project
3. How slash commands automate agent development tasks
4. How to test and iterate on agents using Claude Code
5. How Claude Code + Agent SDK work together in a real workflow

## Add to M25: Use Claude Code to Build an Agent Project

### Section: Hands-On — Build an Agent Project with Claude Code (30 min)

The student uses Claude Code itself to scaffold, build, test, and iterate on a UCC agent.

**Step 1: Create the project with Claude Code (5 min)**

```bash
mkdir ucc-agent && cd ucc-agent
claude
```

Inside Claude Code:
```
Create a CLAUDE.md for a UCC filing research agent project. The agent searches 
filings by debtor name across states and calculates risk scores. Tech stack: 
Python, anthropic SDK, FastAPI for the API wrapper, DuckDB for local data, 
pytest for tests. Include: project description, file structure, coding 
standards (type hints, docstrings, error handling), and the 3 tool definitions 
(search_filings, get_filing_details, calculate_risk_score).
```

Claude Code creates `CLAUDE.md` — the student sees how project configuration works by DOING it, not just reading about it.

**Step 2: Create slash commands for agent development (10 min)**

```
Create these slash commands in .claude/commands/:

1. /run-agent.md — Run the agent with a test question, show the full 
   tool call trace, report token usage and cost

2. /test-agent.md — Run the pytest test suite, report pass/fail, 
   suggest fixes for failures

3. /add-tool.md — Add a new tool to the agent. Takes tool name and 
   description as arguments. Creates the tool function, adds it to the 
   agent config, creates a test for it

4. /eval-agent.md — Run the agent against 10 test questions from 
   test_scenarios.json, score each response, generate an eval report
```

Now the student has reusable commands:
```
/run-agent "What is the lien exposure for Acme Corporation?"
/test-agent
/add-tool check_lapse_dates "Check which filings are approaching lapse date"
/eval-agent
```

**Step 3: Build the agent using slash commands (10 min)**

```
/run-agent "Find all filings for Acme Corporation"
```

Claude Code runs the agent, shows the trace, reports: "5 tool calls, 2,340 tokens, $0.007 cost, 4.2 seconds."

Student sees an issue — agent didn't find DBA variations. They iterate:

```
The agent missed ACME CORP DBA ROADRUNNER SUPPLIES. Update the system prompt 
to instruct the agent to always try name abbreviations and DBA variations.
```

Claude Code edits the system prompt. Student runs again:

```
/run-agent "Find all filings for Acme Corporation"
```

Now finds 9 filings. That's the Claude Code workflow — iterate on the agent using natural language.

**Step 4: Create a skill for entity resolution (5 min)**

```
Create a skill in .claude/skills/entity-resolution/ that teaches Claude Code 
how to handle entity name matching in the UCC domain. Include: common 
abbreviations (Corp/Corporation/Inc), DBA patterns, state-specific naming 
conventions, and fuzzy matching thresholds.
```

Now when the student asks Claude Code about entity resolution in this project, it has domain-specific knowledge.

### Key Insight for Students
"Claude Code is not just a code editor. It's an agent development environment. Your CLAUDE.md is the project brain. Your slash commands are reusable workflows. Your skills are domain knowledge. You're using an agent (Claude Code) to build agents (your UCC agent)."

## Add to M26: Agent SDK Inside a Claude Code Project

### Section: Agent SDK + Claude Code Together (20 min)

Show how the Agent SDK agent lives inside a Claude Code project with CLAUDE.md governing the development workflow.

**Step 5: Convert raw agent to Agent SDK using Claude Code**

```
Read agent.py which uses the raw client.messages.create loop. Convert it to 
use the Agent SDK with @agent.tool decorators. Keep the same tools and mock 
data. The Agent SDK version should produce identical output.
```

Claude Code does the conversion. Student compares:

```
/run-agent "What is the lien exposure for Acme Corporation?"
```

Same output, less code.

**Step 6: Add hooks using Claude Code**

```
Add a PreToolUse hook that logs every tool call with timestamp and a 
PostToolUse hook that redacts any SSN patterns from tool results. Use the 
patterns from the compliance logging section.
```

Claude Code adds the hooks. Student verifies:

```
/run-agent "Find filings for Acme Corporation"
```

Sees timestamped logs and PII redaction in action.

**Step 7: Add session support using Claude Code**

```
Add session support so the agent handles follow-up questions. Use 
agent.create_session and session.send. Add a /chat-agent.md slash command 
that starts an interactive multi-turn conversation with the agent.
```

Now the student has:
```
/chat-agent
> What is the lien exposure for Acme Corporation?
[agent responds]
> What about their Texas filings?
[agent remembers context and responds]
> exit
```

**Step 8: Create a test suite using Claude Code**

```
Create a pytest test suite in tests/ that covers:
- Each tool returns valid data for known inputs
- Agent finds all 9 Acme filings including DBA
- Hooks block queries shorter than 3 characters
- Session maintains context across 3 turns
- Agent handles company with zero filings gracefully
Run the tests.
```

Student runs:
```
/test-agent
```

Sees: 5 passed, 0 failed.

**Step 9: Deploy using Claude Code**

```
Create a Dockerfile and docker-compose.yml for the agent. Wrap it in 
FastAPI with /query and /health endpoints. Use the DuckDB local 
production setup from M22B.
```

Then:
```
docker compose up -d
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "Find filings for Acme"}'
```

### The Complete Claude Code Agent Development Workflow

```
1. claude                              # Start Claude Code
2. "Create CLAUDE.md for UCC agent"    # Project setup
3. "Create slash commands"             # Development tools
4. /run-agent "test question"          # Build and iterate
5. "Convert to Agent SDK"             # Upgrade to SDK
6. "Add hooks for logging and PII"    # Add guardrails
7. "Add session support"              # Add persistence
8. /test-agent                         # Verify
9. /eval-agent                         # Evaluate quality
10. "Create Dockerfile and deploy"     # Ship it
```

"You just built a production agent — from project setup to deployment — entirely inside Claude Code. Every step was a natural language instruction. That's the future of agent development."

## File Structure Created by This Workflow

```
ucc-agent/
├── CLAUDE.md                          # Project brain (created in Step 1)
├── .claude/
│   ├── commands/
│   │   ├── run-agent.md               # Run + trace (Step 2)
│   │   ├── test-agent.md              # Pytest runner (Step 2)
│   │   ├── add-tool.md                # Add new tool (Step 2)
│   │   ├── eval-agent.md              # Evaluation runner (Step 2)
│   │   └── chat-agent.md              # Interactive chat (Step 7)
│   └── skills/
│       └── entity-resolution/
│           └── SKILL.md               # Domain knowledge (Step 4)
├── agent.py                           # Agent SDK agent (Step 5)
├── tools.py                           # @agent.tool functions (Step 5)
├── hooks.py                           # PreToolUse + PostToolUse (Step 6)
├── mock_data.py                       # Mock UCC filings
├── server.py                          # FastAPI wrapper (Step 9)
├── Dockerfile                         # Container (Step 9)
├── docker-compose.yml                 # Local production (Step 9)
├── tests/
│   ├── test_tools.py                  # Tool unit tests (Step 8)
│   ├── test_agent.py                  # Agent integration tests (Step 8)
│   └── test_scenarios.json            # Eval dataset (Step 2)
└── requirements.txt
```
