# fix-add-approach-references.ps1
# Adds forward/backward references connecting raw -> SDK -> spec across modules
# Run: .\fix-add-approach-references.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Approach References Across Modules ===" -ForegroundColor Cyan
Write-Host "5 modules will be updated. Estimated: 15 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/5] M05 - Adding forward reference..." -ForegroundColor Green
$cmd1 = @"
Open the M05 HTML file in output/. Add a gold accent callout box (border-color D4A843) before the quiz titled Where This Leads Three Ways to Build Agents. Content: You just wrote your first tool call using client.messages.create. This is the RAW approach. As the course progresses this pattern evolves: In M12 you wrap it in a ReAct loop. In M15B you build a complete multi-agent system. In M26 you rebuild it using the Agent SDK in 15 lines instead of 60. In M25 you write a spec and Claude Code generates everything. In CAPSTONE-7 you build the SAME agent all three ways and compare. Every approach uses the tool pattern you just learned. About 100 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

Write-Host "[2/5] M12 - Adding approach reference..." -ForegroundColor Green
$cmd2 = @"
Open the M12 HTML file in output/. Add a gold accent callout box (D4A843) after the ReAct loop implementation titled The Evolution of This Loop. Content: In M05 you made a single tool call. Now you have wrapped it in a while loop. What comes next: M15B adds a coordinator with subagents each running its own loop. M26 replaces this entire while loop with the Agent SDK where hooks intercept each tool call. M25 generates everything from a spec. You are learning the engine before using the car. Understanding this raw loop is what lets you debug the SDK when something goes wrong. About 120 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

Write-Host "[3/5] M15B - Adding forward reference to SDK..." -ForegroundColor Green
$cmd3 = @"
Open the M15B HTML file in output/. Add a gold accent callout box (D4A843) at the end before the quiz titled What You Just Built And What Comes Next. Content: You just built a complete multi-agent system from scratch. About 250 lines of code. Now the question: what if you could get the SAME output in 15 lines? In M26 you rebuild this exact agent using the Agent SDK. The agent.tool decorator replaces JSON Schema. Hooks replace inline guardrails. Sessions replace manual history. Same output one fifth the code. But you needed M15B first. When the SDK does something unexpected you know what it abstracts because you wrote it yourself. In CAPSTONE-7 you build this same agent a third time by writing a spec. About 150 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd3
Write-Host ""

Write-Host "[4/5] M26 - Adding backward reference..." -ForegroundColor Green
$cmd4 = @"
Open the M26 HTML file in output/. Add a gold accent callout box (D4A843) at the top of the module content titled Remember M15B You Are About to Rebuild It. Content: In M15B you built a UCC agent from scratch. Coordinator plus subagents plus tools plus guardrails. About 250 lines. This module rebuilds that SAME agent using the Agent SDK. Your 250 lines shrink to about 40. The output is identical. Keep M15B open in another tab as you work through this module. At each step compare what the SDK does versus what you coded manually. That comparison IS the lesson. After M26 there is one more level in M25 spec-driven development. CAPSTONE-7 ties all three together. About 120 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd4
Write-Host ""

Write-Host "[5/5] M25 - Adding journey reference..." -ForegroundColor Green
$cmd5 = @"
Open the M25 HTML file in output/. Add a gold accent callout box (D4A843) titled The Three Approaches Your Complete Toolkit. Content: You now have three ways to build agents. Approach 1 Raw API Loop from M15B: 250 lines and full control. Approach 2 Agent SDK from M26: 40 lines with hooks and sessions. Approach 3 Spec-Driven from this module: 100 lines of spec and Claude Code generates everything. Each builds on the one before. You cannot debug Approach 3 without understanding Approach 1. CAPSTONE-7 is where you prove this by building the SAME agent all three ways and comparing code size and development time and flexibility. About 150 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd5
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "5 modules updated: M05 M12 M15B M26 M25"
