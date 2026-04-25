---
description: Generate a complete Git-ready lab repository with starter code, mock data, solutions, and step-by-step instructions for all modules and capstones
argument-hint: [MODULE_ID or ALL or CAPSTONE-N e.g. M09, M15B, ALL, CAPSTONE-3]
---

Generate a Git-ready lab repository for: $ARGUMENTS

If $ARGUMENTS is "ALL", generate the complete course lab repo with all modules and capstones.
If a specific module/capstone, generate just that lab folder.

Read these files first:
- `prompts/07-depth-rules.md` (Rules 13-14 for lab structure and capstone packets)
- `prompts/08-capstone-animations.md` (for capstone architecture context)
- `prompts/03-capstone-domains.md` (for domain-specific mock data)
- The module/capstone brief from `prompts/modules/`

## Repository Structure (for ALL)

Generate this complete directory structure in `labs/`:

```
labs/
├── README.md                           # Course overview, setup guide, how to use this repo
├── SETUP.md                            # Universal setup: Python, Node.js, API keys, Docker
├── .gitignore                          # .env, __pycache__, node_modules, .duckdb, venv/
├── .env.example                        # ANTHROPIC_API_KEY=your-key-here
├── requirements.txt                    # All Python deps across all labs
├── package.json                        # All Node.js deps across all labs
│
├── shared/                             # Shared utilities used across multiple labs
│   ├── mock_ucc_data.py                # UCC filing mock data generator (used by M05+)
│   ├── mock_ucc_data.js                # Same in Node.js
│   ├── test_helpers.py                 # Common test utilities
│   └── README.md                       # What's in shared/ and how to use it
│
├── M01-llm-mental-model/
│   ├── README.md                       # Lab instructions (step-by-step from the module)
│   ├── starter/                        # What the student starts with
│   │   └── first_call.py              # Skeleton with TODOs
│   ├── solution/                       # Complete working code
│   │   ├── first_call.py              # Python solution
│   │   └── first_call.js             # Node.js solution
│   └── expected_output/               # What the student should see
│       └── sample_output.txt
│
├── M02-tokens/
│   ├── README.md
│   ├── starter/
│   │   └── token_counter.py
│   ├── solution/
│   │   ├── token_counter.py
│   │   └── token_counter.js
│   └── expected_output/
│       └── sample_output.txt
│
├── M03-prompts/
│   ├── README.md
│   ├── starter/
│   │   └── conversation_manager.py
│   ├── solution/
│   │   ├── conversation_manager.py
│   │   └── conversation_manager.js
│   └── expected_output/
│       └── multi_turn_output.txt
│
├── M04-structured-output/
│   ├── README.md
│   ├── starter/
│   │   └── data_extractor.py
│   ├── solution/
│   │   ├── data_extractor.py
│   │   └── data_extractor.js
│   └── expected_output/
│       └── extracted_data.json
│
├── M05-function-calling/
│   ├── README.md
│   ├── starter/
│   │   ├── tools.py                    # Tool definitions (complete)
│   │   ├── agent.py                    # Agent skeleton with TODOs
│   │   └── mock_data.py               # Mock weather + calculator data
│   ├── solution/
│   │   ├── tools.py
│   │   ├── agent.py
│   │   ├── agent.js
│   │   └── mock_data.py
│   └── expected_output/
│       ├── single_tool.txt
│       └── multi_tool.txt
│
├── M06-multi-tool/
│   ├── README.md
│   ├── starter/
│   ├── solution/
│   └── expected_output/
│
├── M07-mcp/
│   ├── README.md
│   ├── starter/
│   │   ├── filesystem_server.py        # MCP server skeleton
│   │   └── database_server.py          # MCP server skeleton
│   ├── solution/
│   │   ├── filesystem_server.py        # Complete Python MCP server
│   │   ├── filesystem_server.js        # Complete Node.js MCP server
│   │   ├── database_server.py
│   │   └── mcp_config.json            # Sample .mcp.json configuration
│   ├── test_docs/                      # Sample files for the filesystem server
│   │   ├── filing_guide.md
│   │   ├── glossary.md
│   │   └── state_formats.md
│   └── expected_output/
│
├── M08-conversation-management/
│   ├── README.md
│   ├── starter/
│   │   └── conversation_manager.py     # Skeleton with sliding window TODO
│   ├── solution/
│   │   ├── conversation_manager.py     # Full history, sliding window, summarization
│   │   └── conversation_manager.js
│   └── expected_output/
│
├── M09-rag/
│   ├── README.md
│   ├── starter/
│   │   ├── loader.py                   # Document loader skeleton
│   │   ├── chunker.py                  # Chunking skeleton
│   │   ├── rag_pipeline.py             # RAG pipeline skeleton
│   │   └── requirements.txt            # chromadb, anthropic
│   ├── solution/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── rag_pipeline.py
│   │   └── rag_pipeline.js
│   ├── docs/                           # Sample documents to ingest
│   │   ├── ucc_article9_guide.md       # UCC Article 9 plain-English guide
│   │   ├── filing_procedures.md        # State filing procedures
│   │   ├── collateral_types.md         # Collateral classification guide
│   │   └── faq.md                      # Common UCC questions
│   └── expected_output/
│       └── sample_queries.txt
│
├── M10-advanced-rag/
│   ├── README.md
│   ├── starter/
│   ├── solution/
│   ├── docs/                           # Same docs as M09 (symlink or copy)
│   └── expected_output/
│
├── M11-multi-layer-memory/
│   ├── README.md
│   ├── starter/
│   ├── solution/
│   └── expected_output/
│
├── M12-react/
│   ├── README.md
│   ├── starter/
│   │   ├── tools.py                    # 3 research tools (complete)
│   │   ├── react_agent.py              # ReAct loop skeleton
│   │   └── mock_data.py               # Mock search results
│   ├── solution/
│   │   ├── tools.py
│   │   ├── react_agent.py
│   │   └── react_agent.js
│   └── expected_output/
│       └── reasoning_trace.txt         # Full think→act→observe trace
│
├── M13-planning/
│   ├── README.md
│   ├── starter/
│   ├── solution/
│   └── expected_output/
│
├── M14-multi-agent/
│   ├── README.md
│   ├── starter/
│   │   ├── coordinator.py              # Coordinator skeleton
│   │   ├── researcher.py               # Subagent skeleton
│   │   ├── writer.py                   # Subagent skeleton
│   │   └── editor.py                   # Subagent skeleton
│   ├── solution/
│   │   ├── coordinator.py
│   │   ├── researcher.py
│   │   ├── writer.py
│   │   └── editor.py
│   └── expected_output/
│
├── M15-code-interpreter/
│   ├── README.md
│   ├── starter/
│   ├── solution/
│   └── expected_output/
│
├── M15B-build-complete-agent/
│   ├── README.md                       # Full step-by-step build guide
│   ├── starter/
│   │   ├── config.py                   # Complete — state registry, constants
│   │   ├── mock_data.py                # Complete — 15 realistic UCC filings
│   │   ├── tools.py                    # Tool signatures only, body is TODO
│   │   ├── agent.py                    # Single agent skeleton
│   │   └── coordinator.py              # Coordinator skeleton
│   ├── solution/
│   │   ├── config.py
│   │   ├── mock_data.py
│   │   ├── tools.py                    # 3 complete tools
│   │   ├── agent.py                    # Complete single agent
│   │   ├── coordinator.py              # Complete coordinator + 2 subagents
│   │   ├── agent.js                    # Node.js version
│   │   └── coordinator.js
│   ├── tests/
│   │   ├── test_tools.py               # Tool unit tests
│   │   ├── test_agent.py               # Single agent integration tests
│   │   └── test_coordinator.py         # Multi-agent tests
│   └── expected_output/
│       ├── single_agent_output.txt
│       └── coordinator_output.txt
│
├── M16-input-guardrails/ through M22-cost-optimization/
│   └── (same pattern: README, starter/, solution/, expected_output/)
│
├── M22B-deploy-agent/
│   ├── README.md                       # 3-tier deployment guide
│   ├── starter/
│   │   ├── server.py                   # FastAPI wrapper skeleton
│   │   └── Dockerfile                  # Skeleton with TODOs
│   ├── solution/
│   │   ├── server.py                   # Complete FastAPI wrapper
│   │   ├── Dockerfile                  # Complete multi-stage build
│   │   ├── docker-compose.yml          # Local production stack
│   │   ├── .env.example
│   │   ├── gcp/
│   │   │   ├── deploy.sh               # GCP Cloud Run deploy script
│   │   │   └── cloudbuild.yaml         # Cloud Build config
│   │   └── aws/
│   │       ├── template.yaml           # SAM template
│   │       ├── lambda_handler.py       # Lambda handler
│   │       └── deploy.sh               # SAM deploy script
│   └── expected_output/
│       ├── local_response.json
│       ├── docker_response.json
│       └── health_check.json
│
├── M25-claude-code-mastery/
│   ├── README.md
│   ├── starter/
│   │   ├── .claude/
│   │   │   ├── CLAUDE.md               # Skeleton project config
│   │   │   └── commands/
│   │   │       └── check-filing.md     # Skeleton command
│   │   └── .claude/skills/
│   │       └── entity-resolution/
│   │           └── SKILL.md            # Skeleton skill
│   ├── solution/
│   │   ├── .claude/
│   │   │   ├── CLAUDE.md               # Complete project config
│   │   │   ├── commands/
│   │   │   │   └── check-filing.md     # Complete command
│   │   │   └── skills/
│   │   │       └── entity-resolution/
│   │   │           └── SKILL.md        # Complete skill with context: fork
│   │   └── github-actions/
│   │       └── claude-review.yml       # CI/CD reviewer workflow
│   └── expected_output/
│
├── M26-hooks-sessions-agent-sdk/
│   ├── README.md
│   ├── starter/
│   │   ├── agent_sdk_agent.py          # Agent SDK skeleton
│   │   └── hooks_config.json           # Hook config skeleton
│   ├── solution/
│   │   ├── agent_sdk_agent.py          # Complete Agent SDK agent
│   │   ├── hooks_config.json           # Complete hook definitions
│   │   └── customer_support_agent.py   # Exam Scenario 1 implementation
│   └── expected_output/
│
├── M27-cert-exam-prep/
│   ├── README.md                       # Mock exam instructions
│   ├── mock_exams/
│   │   ├── exam_a.json                 # 10 questions (Scenarios 1+3)
│   │   ├── exam_b.json                 # 10 questions (Scenarios 2+5)
│   │   ├── exam_c.json                 # 10 questions (Scenarios 4+6)
│   │   └── answer_key.json            # All answers with explanations
│   ├── anti_patterns/
│   │   └── anti_patterns_reference.md  # All 18 anti-patterns
│   └── scenario_walkthroughs/
│       ├── scenario_1_support_agent.md
│       ├── scenario_2_claude_code.md
│       ├── scenario_3_multi_agent.md
│       ├── scenario_4_dev_tools.md
│       ├── scenario_5_cicd.md
│       └── scenario_6_data_extraction.md
│
├── capstone-1-first-agent/
│   ├── README.md                       # Project brief + step-by-step guide
│   ├── domain-a-healthcare/
│   │   ├── starter/
│   │   │   ├── tools.py
│   │   │   ├── agent.py
│   │   │   └── mock_data.py            # Mock pre-auth data
│   │   ├── solution/
│   │   └── expected_output/
│   ├── domain-b-ecommerce/
│   │   ├── starter/
│   │   ├── solution/
│   │   └── expected_output/
│   └── domain-c-ucc/
│       ├── starter/
│       ├── solution/
│       └── expected_output/
│
├── capstone-2-knowledge-agent/
│   ├── README.md
│   ├── domain-a-healthcare/
│   │   ├── starter/
│   │   ├── solution/
│   │   ├── docs/                       # Mock clinical policy documents
│   │   └── expected_output/
│   ├── domain-b-ecommerce/
│   ├── domain-c-ucc/
│   │   └── docs/                       # UCC reference documents
│
├── capstone-3-reasoning-agent/
│   ├── README.md
│   ├── domain-a-healthcare/
│   ├── domain-b-ecommerce/
│   └── domain-c-ucc/
│       ├── starter/
│       │   ├── tools.py                # 5 entity resolution tools (signatures only)
│       │   ├── agent.py                # ReAct skeleton
│       │   └── mock_data.py            # Multi-state filing mock data
│       ├── solution/
│       └── expected_output/
│           └── reasoning_trace.txt     # Full think→act→observe chain
│
├── capstone-4-agent-team/
│   ├── README.md
│   ├── domain-a-healthcare/
│   │   ├── starter/
│   │   │   ├── intake_agent.py
│   │   │   ├── criteria_agent.py
│   │   │   ├── decision_agent.py
│   │   │   └── comms_agent.py
│   │   ├── solution/
│   │   └── expected_output/
│   ├── domain-b-ecommerce/
│   └── domain-c-ucc/
│
├── capstone-5-production-agent/
│   ├── README.md
│   ├── domain-c-ucc/                   # One domain deep, not all three
│   │   ├── starter/
│   │   ├── solution/
│   │   ├── docker/
│   │   │   ├── Dockerfile
│   │   │   └── docker-compose.yml
│   │   ├── monitoring/
│   │   │   └── langfuse_setup.py
│   │   ├── tests/
│   │   │   ├── test_suite_100.json     # 100-case evaluation dataset
│   │   │   └── run_eval.py
│   │   └── expected_output/
│
└── capstone-6-bronze-testing/
    ├── README.md                       # Full build guide (15 steps + production)
    ├── starter/
    │   ├── config.py                   # Complete — 50 states registered
    │   ├── coordinator.py              # Skeleton
    │   ├── state_tester.py             # Skeleton
    │   └── tools/
    │       ├── file_parser.py          # Format detection skeleton
    │       ├── bronze_query.py         # Query skeleton
    │       ├── validation_checks.py    # Check signatures only
    │       └── report_generator.py     # Skeleton
    ├── solution/
    │   ├── config.py
    │   ├── coordinator.py              # Complete with parallel execution
    │   ├── state_tester.py             # Complete 12-check agent
    │   ├── tools/
    │   │   ├── file_parser.py          # All 5 format parsers
    │   │   ├── bronze_query.py         # Mock + DuckDB + BigQuery versions
    │   │   ├── bronze_query_local.py   # DuckDB version for Tier 1
    │   │   ├── validation_checks.py    # All 34 checks
    │   │   ├── report_generator.py     # Terminal + JSON + Markdown
    │   │   └── results_db.py           # DuckDB results storage
    │   ├── server.py                   # FastAPI wrapper
    │   ├── file_watcher.py             # Auto-trigger on new files
    │   ├── dashboard_server.py         # Local HTML dashboard
    │   ├── Dockerfile
    │   └── docker-compose.yml          # 3-container local production
    ├── mock_data/
    │   ├── source_files/
    │   │   ├── NY_2024_Q4.xml          # New York — XML
    │   │   ├── CA_2024_Q4.csv          # California — pipe-delimited
    │   │   ├── TX_2024_Q4.dat          # Texas — fixed-width
    │   │   ├── FL_2024_Q4.json         # Florida — JSON
    │   │   ├── IL_2024_Q4.csv          # Illinois — comma CSV
    │   │   ├── GA_2024_Q4.csv          # Georgia — DD/MM/YYYY dates
    │   │   ├── NV_2024_Q4.json         # Nevada — duplicates
    │   │   ├── DE_2024_Q4.csv          # Delaware — small state
    │   │   ├── OH_2024_Q4.xml          # Ohio — different namespace
    │   │   ├── WY_2024_Q4.tsv          # Wyoming — tab-separated
    │   │   ├── TX_BAD_truncated.dat    # Error: truncated
    │   │   ├── FL_BAD_encoding.json    # Error: wrong encoding
    │   │   ├── EMPTY_STATE.csv         # Error: empty file
    │   │   ├── NY_2025_Q1.xml          # Incremental: new quarter
    │   │   └── CA_2025_Q1.csv          # Incremental: new column added
    │   ├── bronze_table_seed.json      # Post-seed Bronze data
    │   ├── bronze_table_incremental.json # Post-incremental Bronze data
    │   ├── state_format_registry.json
    │   ├── load_manifest_2024Q4.json
    │   └── load_manifest_2025Q1.json
    ├── tests/
    │   ├── test_file_parser.py
    │   ├── test_validation_checks.py
    │   ├── test_coordinator.py
    │   └── test_scenarios.json         # All 9 test scenarios with expected results
    └── expected_output/
        ├── full_seed_dashboard.txt
        ├── incremental_dashboard.txt
        ├── change_detection_report.txt
        └── sample_report.json
```

## Generation Rules

### README.md for each lab
Every lab README follows this exact format:
```markdown
# M09: RAG — Retrieval-Augmented Generation — Lab

## What You'll Build
A RAG pipeline that answers questions about UCC filing documents using ChromaDB and Claude.

## Prerequisites
- Completed M01-M08 course modules
- Python 3.10+ installed
- Anthropic API key set as environment variable

## Setup
\`\`\`bash
cd labs/M09-rag
pip install -r requirements.txt   # or: pip install chromadb anthropic
export ANTHROPIC_API_KEY=your-key-here
\`\`\`

## Lab Steps

### Step 1: [title]
[what & why — 2-3 sentences]

**Starter code**: `starter/loader.py` — open this file and complete the TODOs
**Solution**: If stuck, check `solution/loader.py`

\`\`\`bash
# Run:
python starter/loader.py
# Expected output:
# Loaded 4 documents from docs/
\`\`\`
✅ Checkpoint: [what success looks like]
⚠️ Troubleshooting: [common errors]

### Step 2: [title]
...

## Final Verification
\`\`\`bash
python solution/rag_pipeline.py "What is a UCC-1 filing?"
\`\`\`
Expected: [full expected output]

## What You Built
[summary of the complete artifact]

## Next
Continue to [M10: Advanced RAG →](../M10-advanced-rag/)
```

### Starter code rules
- NEVER empty files — always have structure, imports, docstrings, and TODO comments
- TODOs must be specific: `# TODO: Add the tool_use loop here — check stop_reason for 'tool_use' vs 'end_turn'`
- Config files, mock data, and test helpers are COMPLETE (not skeleton) — the student builds the agent code, not the infrastructure
- Every starter file runs without errors (it just doesn't do anything useful yet)

### Solution code rules
- COMPLETE and RUNNABLE — copy from solution/ and it works immediately
- Both Python AND Node.js for every agent/tool file
- Extensive inline comments explaining WHY, not just WHAT
- Error handling present
- No hardcoded API keys

### Mock data rules
- REALISTIC — real-looking filing numbers, debtor names, addresses, amounts
- SUFFICIENT — enough records to demonstrate the concept (not 2 records, not 10,000)
- INCLUDES EDGE CASES — the mock data has deliberate issues for the student to discover
- CONSISTENT — the same mock filings appear across labs where they reference each other

### Expected output rules
- EXACT terminal output the student should see
- Includes both success cases and expected error cases
- Matches the checkpoint descriptions in the README

## After Generation

Copy the entire `labs/` folder to a separate Git repo:

```bash
cd labs
git init
git add .
git commit -m "Initial lab repository — AI Agent Development Course"
git remote add origin git@github.com:yourusername/claude-agent-course-labs.git
git push -u origin main
```

Students clone this repo and follow the README in each lab folder.

Report: total files created, total lines of code (starter vs solution), total mock data records, total expected output files
