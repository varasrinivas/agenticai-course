# fix-add-why-agents.ps1
# Adds the business case for agents to M00 including the FastAPI architecture comparison
# Run: .\fix-add-why-agents.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding: Why Agents - The Business Case ===" -ForegroundColor Cyan
Write-Host "1 module updated. Estimated: 5-10 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] M00 - Adding business case with FastAPI comparison..." -ForegroundColor Green

$cmd = @"
Read prompts/15-why-agents.md for the complete Why Agents specification. Open the M00 HTML file in output/. Add a new section AFTER the Prelude and BEFORE What Is an Agent. Title: Why Agents: The Business Case.

CRITICAL: Start with the Both End Up in FastAPI comparison. Show two architecture diagrams side by side: ML model in FastAPI (hardcoded SQL and fixed logic and JSON response) vs Agent in FastAPI (Claude reasons about what to search and discovers variations and writes narrative). Show the three-layer model: Layer 1 Infrastructure (FastAPI and Docker - same in both) and Layer 2 Capabilities (tools and ML model - same in both) and Layer 3 Intelligence (Claude reasoning - NEW with agents). Make clear the ML model stays in Layer 2 in BOTH approaches. The difference is what is ABOVE it. Include the decision engine comparison table showing who decides what to query and who handles name variations and what changes when logic changes. Include the cost-benefit reality table with response time and cost per request and development time comparisons.

THEN include the 7 benefits: reasoning replaces hardcoded logic and natural language input and explainability and follow-ups without new code and multi-source synthesis and graceful incomplete data and ML model gets smarter context. Each with concrete examples from the UCC domain.

THEN include When NOT to Use Agents table with 5 situations. Include the decision rule about human reads output vs machine consumes output.

Add an animated SVG showing the three-layer stack with Layer 1 at bottom in gray and Layer 2 in blue and Layer 3 at top in gradient. Animate Layer 3 appearing to show what agents ADD. About 800 words total. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "M00 now explains WHY agents matter with the FastAPI architecture comparison."
Write-Host "Students understand: same FastAPI and same ML model but different intelligence layer."
