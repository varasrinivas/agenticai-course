# fix-gaps-and-patterns.ps1
# Adds design patterns to M12 and gap coverage to M04, M12, M19, M20, M21, M22
# Run: .\fix-gaps-and-patterns.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Design Patterns + Gap Coverage ===" -ForegroundColor Cyan
Write-Host "7 steps updating 6 modules. Estimated: 15-20 minutes." -ForegroundColor Yellow
Write-Host ""

# --- Step 1: M12 Design Patterns ---
Write-Host "[1/7] M12 - Adding 8 Agent Design Patterns..." -ForegroundColor Green

$cmd1 = @"
Read prompts/modules/M12-react.md which contains Part A Agent Design Patterns Overview. Open the M12 HTML file in output/. Add Part A BEFORE the existing ReAct deep dive section. Part A must include: the 8 patterns table covering Single-Turn and ReAct and Plan-Execute and Router and Parallel Fan-Out and Pipeline and Supervisor-Workers and Autonomous-HITL. Add the decision tree flowchart as an animated SVG. Add the Combining Patterns section showing how CAPSTONE-4 and CAPSTONE-6 combine patterns. Add the pattern comparison matrix. Add the 5 anti-patterns. Use str_replace to insert. Do NOT remove existing ReAct content.
"@

claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

# --- Step 2: M04 Multi-modal ---
Write-Host "[2/7] M04 - Adding multi-modal agents section..." -ForegroundColor Green

$cmd2 = @"
Read prompts/11-gap-coverage.md and find GAP 6 Multi-Modal Agents. Open the M04 HTML file in output/. Add a new section after the existing structured output content titled Multi-Modal Input Vision and PDF. Cover sending images to Claude via base64 and vision use cases for agents like reading scanned documents and extracting data from photos. Cover PDF processing and a pseudocode example of an analyze_document tool. About 200 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

# --- Step 3: M12 Error Handling + Extended Thinking ---
Write-Host "[3/7] M12 - Adding error handling and extended thinking..." -ForegroundColor Green

$cmd3 = @"
Read prompts/11-gap-coverage.md and find GAP 1 Error Handling and GAP 5 Extended Thinking. Open the M12 HTML file in output/. Add two new sections AFTER the ReAct deep dive. First section: Error Handling and Retry Patterns covering retry with exponential backoff and fallback chains and graceful degradation with pseudocode example about 300 words. Second section: Extended Thinking covering what it is and when to use it and the API parameter and reading thinking blocks and when NOT to use it about 200 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd3
Write-Host ""

# --- Step 4: M19 Compliance + Prompt Versioning ---
Write-Host "[4/7] M19 - Adding compliance logging and prompt versioning..." -ForegroundColor Green

$cmd4 = @"
Read prompts/11-gap-coverage.md and find GAP 9 Compliance and GAP 8 Prompt Management. Open the M19 HTML file in output/. Add two new sections. First: Compliance and Audit Logging covering what to log for HIPAA and SOC2 and GDPR and PII redaction in logs and audit trail requirements and data retention about 200 words. Second: Prompt Management and Versioning covering prompts as code in version control and A/B testing prompts and prompt regression testing about 200 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd4
Write-Host ""

# --- Step 5: M20 Agent Versioning ---
Write-Host "[5/7] M20 - Adding agent versioning and rollback..." -ForegroundColor Green

$cmd5 = @"
Read prompts/11-gap-coverage.md and find GAP 10 Agent Versioning. Open the M20 HTML file in output/. Add a new section called Agent Versioning and Rollback covering canary deployments for agents and feature flags for agent behavior and rollback strategy and version tagging tied to eval results about 200 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd5
Write-Host ""

# --- Step 6: M21 Streaming + Auth ---
Write-Host "[6/7] M21 - Adding streaming and authentication..." -ForegroundColor Green

$cmd6 = @"
Read prompts/11-gap-coverage.md and find GAP 2 Streaming and GAP 3 Authentication. Open the M21 HTML file in output/. Add two new sections. First: Streaming Responses covering SSE vs WebSocket and Claude streaming API with stream equals True and implementing streaming in FastAPI with pseudocode and client-side consumption and progress indicators about 300 words. Second: Authentication and Authorization covering API key auth and OAuth JWT and role-based access and tool-level permissions and rate limiting per user with pseudocode about 300 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd6
Write-Host ""

# --- Step 7: M22 Prompt Caching + Batch API ---
Write-Host "[7/7] M22 - Adding prompt caching and batch API..." -ForegroundColor Green

$cmd7 = @"
Read prompts/11-gap-coverage.md and find GAP 4 Prompt Caching and GAP 7 Batch API. Open the M22 HTML file in output/. Add two new sections. First: Prompt Caching covering how Anthropic prompt caching works and cache TTL and what to cache vs not cache and cost math example showing 90 percent savings about 200 words. Second: Batch API covering what it is and 50 percent discount and use cases like nightly eval runs and bulk processing and implementation pattern about 200 words. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd7
Write-Host ""

# --- Done ---
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "6 modules updated:" -ForegroundColor Cyan
Write-Host "  M04  + Multi-modal (vision + PDF)"
Write-Host "  M12  + 8 Design Patterns + Error Handling + Extended Thinking"
Write-Host "  M19  + Compliance Logging + Prompt Versioning"
Write-Host "  M20  + Agent Versioning + Rollback"
Write-Host "  M21  + Streaming + Authentication"
Write-Host "  M22  + Prompt Caching + Batch API"
