# fix-add-agent-sdk-lab.ps1
# Adds the Agent SDK hands-on build lab to M26
# Run: .\fix-add-agent-sdk-lab.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Agent SDK Build Lab to M26 ===" -ForegroundColor Cyan
Write-Host "1 module updated. Estimated: 10-15 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] M26 - Adding Agent SDK hands-on build lab..." -ForegroundColor Green

$cmd = @"
Read prompts/modules/M26-hooks-sessions-agent-sdk.md for the complete expanded module specification. Open the M26 HTML file in output/. This module needs a major expansion. Add or replace content to include all 6 sections:

Section 1: Raw Loop vs Agent SDK comparison table showing what each approach handles. When to use which.

Section 2: Hands-on lab to rebuild the UCC agent from M15B using the Agent SDK. Step 1 setup. Step 2 define tools as decorated Python functions using agent.tool decorator. Step 3 run the agent in 5 lines and compare to M15B 60-line raw loop. Step 4 side-by-side code comparison.

Section 3: Hooks. Step 5 add PreToolUse hook for logging every tool call with timestamp. Step 6 add PreToolUse hook that blocks broad queries. Step 7 add PostToolUse hook that redacts PII before Claude sees it.

Section 4: Sessions. Step 8 add session for multi-turn follow-ups with session.send and session.fork for what-if branching.

Section 5: Step 9 complete production agent combining SDK plus hooks plus session plus the ML model from prelude as a tool.

Section 6: Decision guide table for raw loop vs SDK.

Every step must follow Rule 13: complete code block and run command and expected output and checkpoint and troubleshooting. Add 4 animations: raw vs SDK comparison and hook lifecycle and session forking tree and production agent stack. Use str_replace to add content. About 1000 words added.
"@

claude --dangerously-skip-permissions -p $cmd
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "M26 now includes a complete hands-on lab building the same UCC agent with the Agent SDK."
Write-Host "Students see: raw loop (M15B) vs Agent SDK (M26) for the same problem."
