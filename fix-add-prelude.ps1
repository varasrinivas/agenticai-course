# fix-add-prelude.ps1
# Adds the ML Model -> FastAPI -> Agent prelude with hands-on lab to M00
# Run: .\fix-add-prelude.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Prelude: From ML Model to AI Agent ===" -ForegroundColor Cyan
Write-Host "1 module updated. Estimated: 5-10 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] M00 - Adding prelude with hands-on lab..." -ForegroundColor Green

$cmd = @"
Read prompts/14-prelude-ml-to-agent.md for the complete prelude specification including the hands-on lab. Open the M00 HTML file in output/. Add a new section as the VERY FIRST content section before What Is an Agent titled Prelude: From ML Model to AI Agent. This section must include:

PART 1 CONCEPT: Show the same business problem (UCC delinquency prediction for Acme Corporation) solved three ways. Approach 1 is a Python script with pickle model where YOU prepare features and get back a number. Approach 2 is a FastAPI wrapper that auto-fetches but still returns rigid JSON and misses name variations. Approach 3 is a Claude agent that uses the ML model as ONE tool among several and discovers name variations and writes a narrative report. Include the three-way comparison table. Include the key insight that the ML model does not go away and the agent uses it.

PART 2 HANDS-ON LAB with 5 steps following Rule 13 (every step has complete code and run command and expected output and checkpoint and troubleshooting). Step 1: Create mock_data.py with 9 UCC filings for 3 companies and train a RandomForest model saved as pickle. Step 2: Run Approach 1 script that loads pickle and predicts from manual features. Step 3: Run Approach 2 FastAPI server and curl it showing it finds only 3 filings. Step 4: Run Approach 3 Claude agent showing it searches name variations and finds 9 filings and runs the ML model and writes a narrative report. Step 5: Ask a follow-up question showing only the agent can handle it. End with summary table comparing lines of code and filings found and output type across all three.

PART 3 ANIMATED DIAGRAM: Three-lane SVG showing ML script as gray rigid flow ending at a number and FastAPI adding database query ending at JSON and Agent as colorful dynamic flow with think bubbles ending at narrative report. Same data flows through all three but agent path is richer.

Complete code for all four Python files must be included inline in the module (mock_data.py and approach1_script.py and approach2_api.py and approach3_agent.py). Each file must be copy-paste runnable.

Use str_replace to insert before existing content. About 1200 words total including code blocks.
"@

claude --dangerously-skip-permissions -p $cmd
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "M00 now starts with the ML-to-Agent prelude including hands-on lab."
Write-Host "Students run all 3 approaches themselves and see the difference."
