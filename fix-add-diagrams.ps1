# fix-add-diagrams.ps1
# Adds SVG diagrams to all modules based on prompts/12-module-diagrams.md
# Run: .\fix-add-diagrams.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Diagrams to All Modules ===" -ForegroundColor Cyan
Write-Host "10 batches of 3 modules each. Estimated: 30-40 minutes." -ForegroundColor Yellow
Write-Host ""

# Batch 1: M00-M02
Write-Host "[1/10] M00 M01 M02 - Foundation diagrams..." -ForegroundColor Green
$cmd1 = @"
Read prompts/12-module-diagrams.md for the required diagrams for M01 and M02. Read prompts/02-visual-design-system.md for colors and CSS variables. For M01: add two SVG diagrams inline - (1) How an LLM generates text showing tokens flowing through transformer layers to probability distribution to output token and (2) Context window visualization showing system prompt and conversation history and user message with token counts. For M02: add two SVGs - (1) Tokenization example showing a sentence splitting into colored token blocks and (2) Token cost calculator visual. All SVGs must use dark theme with transparent background and CSS variables for colors. Max 600px wide. Include aria-label. Use str_replace to insert after each concepts main explanation paragraph. Do NOT remove existing content.
"@
claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

# Batch 2: M03-M05
Write-Host "[2/10] M03 M04 M05 - Prompts and tools diagrams..." -ForegroundColor Green
$cmd2 = @"
Read prompts/12-module-diagrams.md for M03 M04 M05 diagrams. For M03: add message role flow diagram and prompting patterns comparison (zero-shot vs few-shot vs chain-of-thought as three columns). For M04: add tool use flow diagram showing the full cycle from user message through Claude through tool_use through your code back to Claude and schema validation pipeline. For M05: add the tool use loop circular flow and tool definition anatomy with annotated JSON Schema. All inline SVG with dark theme and CSS variables. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

# Batch 3: M06-M08
Write-Host "[3/10] M06 M07 M08 - Multi-tool and MCP diagrams..." -ForegroundColor Green
$cmd3 = @"
Read prompts/12-module-diagrams.md for M06 M07 M08 diagrams. For M06: add parallel vs sequential tools side-by-side and tool selection degradation chart. For M07: add MCP architecture diagram and N-times-M vs N-plus-M comparison and transport comparison. For M08: add stateless reality diagram and three memory strategies comparison and token budget allocation stacked bar. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd3
Write-Host ""

# Compact
claude --dangerously-skip-permissions -p "/compact"

# Batch 4: M09-M11
Write-Host "[4/10] M09 M10 M11 - RAG and memory diagrams..." -ForegroundColor Green
$cmd4 = @"
Read prompts/12-module-diagrams.md for M09 M10 M11 diagrams. For M09: add RAG pipeline end-to-end flow and embedding space 2D scatter and chunking comparison. For M10: add naive vs advanced RAG parallel pipelines and HyDE flow. For M11: add three-tier brain diagram with concentric layers and memory activation timeline. All inline SVG dark theme CSS variables. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd4
Write-Host ""

# Batch 5: M12-M14
Write-Host "[5/10] M12 M13 M14 - Agent architecture diagrams..." -ForegroundColor Green
$cmd5 = @"
Read prompts/12-module-diagrams.md for M12 M13 M14 diagrams. For M12: add 8 design patterns catalog grid and pattern decision tree flowchart and ReAct loop circular diagram and combining patterns block diagram. For M13: add task decomposition tree and DAG execution graph. For M14: add three architecture patterns comparison and context isolation diagram showing separate context windows. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd5
Write-Host ""

# Batch 6: M15-M16
Write-Host "[6/10] M15 M15B M16 - Sandbox and guardrails diagrams..." -ForegroundColor Green
$cmd6 = @"
Read prompts/12-module-diagrams.md for M15 M15B M16 diagrams. For M15: add sandbox architecture diagram and security boundary diagram. For M15B: add system architecture with coordinator and subagents and single agent vs coordinator comparison. For M16: add guardrail pipeline with gates and prompt injection anatomy. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd6
Write-Host ""

# Compact
claude --dangerously-skip-permissions -p "/compact"

# Batch 7: M17-M19
Write-Host "[7/10] M17 M18 M19 - HITL and eval diagrams..." -ForegroundColor Green
$cmd7 = @"
Read prompts/12-module-diagrams.md for M17 M18 M19 diagrams. For M17: add confidence routing diagram with three branches and circuit breaker state machine. For M18: add eval pipeline flow and aggregate vs per-type accuracy comparison. For M19: add trace waterfall with nested bars and what to log vs not log two-column diagram. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd7
Write-Host ""

# Batch 8: M20-M22
Write-Host "[8/10] M20 M21 M22 - Monitoring and deployment diagrams..." -ForegroundColor Green
$cmd8 = @"
Read prompts/12-module-diagrams.md for M20 M21 M22 diagrams. For M20: add dashboard layout mockup 4-panel and drift detection line chart. For M21: add streaming SSE flow and deployment pipeline from code to user. For M22: add cost breakdown waterfall with cache savings and model routing decision tree. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd8
Write-Host ""

# Compact
claude --dangerously-skip-permissions -p "/compact"

# Batch 9: M22B-M24
Write-Host "[9/10] M22B M23 M24 - Deploy and capstone diagrams..." -ForegroundColor Green
$cmd9 = @"
Read prompts/12-module-diagrams.md for M22B diagrams. For M22B: add 3-tier deployment comparison columns and Docker multi-stage build diagram. For M23 and M24 these are overview modules so check if they already have adequate visuals and add if missing. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd9
Write-Host ""

# Batch 10: M25-M27
Write-Host "[10/10] M25 M26 M27 - Cert prep diagrams..." -ForegroundColor Green
$cmd10 = @"
Read prompts/12-module-diagrams.md for M25 M26 M27 diagrams. For M25: add CLAUDE.md hierarchy tree and slash command execution flow. For M26: add hook lifecycle PreToolUse to PostToolUse and Agent SDK loop diagram. For M27: add exam domain coverage pie chart and anti-pattern identification flow. All inline SVG dark theme. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd10
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "All 30 modules now have concept diagrams." -ForegroundColor Cyan
Write-Host "Total diagrams added: ~55 SVGs across 30 modules." -ForegroundColor White
