# fix-add-agent-boundary.ps1
# Adds clear definition of LLM Call vs Workflow vs Agent with hands-on to M00
# Run: .\fix-add-agent-boundary.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding: What Is and Isn't an Agent ===" -ForegroundColor Cyan
Write-Host "1 module updated. Estimated: 10 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] M00 - Adding agent boundary definition..." -ForegroundColor Green

$cmd = @"
Read prompts/20-what-is-an-agent.md for the complete specification. Open the M00 HTML file in output/. Add a new section AFTER the Why Agents business case and BEFORE or REPLACING the existing What Is an Agent section. Title: What Is and Is Not an Agent — The Clear Boundary.

Include all three levels with complete code examples: Level 1 LLM Call (single client.messages.create and one response and done). Level 2 LLM Workflow (3 fixed LLM calls in sequence where YOUR code decides every step). Level 3 Agent (while loop with tools where CLAUDE decides what tool to call and when to stop).

Include the decision matrix table comparing all three levels across 7 dimensions: number of calls and who decides sequence and tools and loop and adaptation and path known upfront and stop_reason.

Include the litmus test: if you replace the LLM with hardcoded responses and the program works the same it is NOT an agent.

Include the 20-minute hands-on with 4 steps: Step 1 build Level 1 single call (3 min). Step 2 build Level 2 three-step pipeline (5 min). Step 3 build Level 3 agent with tools and loop (7 min). Step 4 prove the difference by running agent with two different questions showing different tool sequences from same code (5 min).

Include the common gray areas section with 4 scenarios and answers.

Include an animated diagram showing three columns: Level 1 as single arrow down. Level 2 as three arrows in fixed sequence. Level 3 as a loop with branching paths that Claude chooses at runtime.

About 800 words total. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "M00 now clearly defines the boundary between LLM Call vs Workflow vs Agent."
Write-Host "Students build all three in 20 minutes and see the difference hands-on."
