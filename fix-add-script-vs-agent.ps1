# fix-add-script-vs-agent.ps1
# Adds script vs agent comparison to M00 and M12
# Run: .\fix-add-script-vs-agent.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Script vs Agent Comparison ===" -ForegroundColor Cyan
Write-Host "2 modules will be updated. Estimated: 10 minutes." -ForegroundColor Yellow
Write-Host ""

# Step 1: M00 — High-level preview
Write-Host "[1/2] M00 - Adding comparison preview..." -ForegroundColor Green

$cmd1 = @"
Read prompts/13-script-vs-agent.md for the full script vs agent comparison. Open the M00 HTML file in output/. Add a new section titled Script vs Agent - Why This Course Exists between the What Is an Agent section and the See an Agent in Action section. Include: the condensed comparison table showing hardcoded vs reasoning for name variations and states and decision logic and edge cases and follow-ups. Include the key insight paragraph about replacing hardcoded decision logic with an LLM. Add a side-by-side animated SVG diagram showing the script approach as rigid gray arrows through fixed boxes on the left and the agent approach as colorful dynamic think bubbles on the right. Also include the When Scripts Are Better section so students know agents are not always the answer. About 400 words total. Use str_replace to insert.
"@

claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

# Step 2: M12 — Full implementation comparison
Write-Host "[2/2] M12 - Adding full implementation comparison..." -ForegroundColor Green

$cmd2 = @"
Read prompts/13-script-vs-agent.md for the full script vs agent comparison. Open the M12 HTML file in output/. Add a new section titled From Script to Agent - The Problem Agents Solve as the FIRST section before the existing design patterns or ReAct content. Include: both complete code listings side by side - the traditional Python script with hardcoded name variants and fixed state loop and rigid filtering (about 40 lines) and the agent approach with the tool use loop where Claude decides what to search (about 30 lines). Below the code show the annotated trace of what the agent DOES across 5 turns with its reasoning. Include the full comparison table. Include the When Scripts Are Better section with 5 examples. Include the key insight paragraph. Add the animated SVG showing script as gray rigid flow vs agent as colored dynamic reasoning. About 600 words total. Use str_replace to insert before existing content.
"@

claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "2 modules updated:" -ForegroundColor Cyan
Write-Host "  M00  + Script vs Agent preview (comparison table + key insight)"
Write-Host "  M12  + Full implementation comparison (both code listings + trace + when scripts win)"
