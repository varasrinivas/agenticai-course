# fix-add-final-polish.ps1
# Adds 6 remaining production topics to existing modules
# Run: .\fix-add-final-polish.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Final Production Topics ===" -ForegroundColor Cyan
Write-Host "6 modules will be updated. Estimated: 15-20 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/6] M16 - Prompt injection deep-dive..." -ForegroundColor Green
$cmd1 = @"
Open the M16 HTML file in output/. Expand the prompt injection section with a deep-dive titled Prompt Injection Attack Patterns and Defenses. Include 4 attack examples: (1) Direct injection where user says Ignore previous instructions. (2) Indirect injection where a tool result contains hidden instructions. (3) Payload smuggling with base64 or unicode. (4) Context manipulation across turns. For each show the defense: input sanitization and system prompt hardening and output validation and multi-turn detection. Add an animated diagram showing attack flow. About 300 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

Write-Host "[2/6] M08 - Context window management..." -ForegroundColor Green
$cmd2 = @"
Open the M08 HTML file in output/. Add a subsection titled Practical Context Window Management. Include: (1) How to count tokens before sending with pseudocode. (2) Token budget allocation: 20 percent system prompt and 50 percent history and 20 percent user message and 10 percent response headroom as an animated stacked bar. (3) What happens when you exceed the limit with the specific API error. (4) Dynamic sliding window based on token count not message count. About 250 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

Write-Host "[3/6] M22 - Tool result caching..." -ForegroundColor Green
$cmd3 = @"
Open the M22 HTML file in output/. Add a subsection titled Caching Tool Results Across Conversations. Include: (1) The problem: same filing searched 100 times per day. (2) Three caching layers: in-memory and Redis/DuckDB and CDN. (3) Cache invalidation: TTL based versus event based. (4) Pseudocode for cached tool wrapper. (5) Cost math: 100 searches at 0.01 each versus 1 search plus 99 cache hits. About 200 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd3
Write-Host ""

Write-Host "[4/6] M18 - CI/CD agent testing..." -ForegroundColor Green
$cmd4 = @"
Open the M18 HTML file in output/. Add a subsection titled Agent Testing in CI CD. Include: (1) The challenge: non-deterministic and slow and costs money. (2) Three-tier strategy: Tier 1 unit tests on every commit with zero API calls. Tier 2 integration tests on PR merge with 10 scenarios. Tier 3 full eval nightly with 100 scenarios. (3) GitHub Actions workflow pseudocode. (4) Handling flaky tests with retries. (5) Monthly CI/CD API budget with alerts. About 250 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd4
Write-Host ""

Write-Host "[5/6] M19 - OpenTelemetry..." -ForegroundColor Green
$cmd5 = @"
Open the M19 HTML file in output/. Add a subsection titled OpenTelemetry for Agent Observability. Include: (1) Why OTel: vendor-neutral standard for Datadog and Grafana and New Relic. (2) Key concepts mapped to agents: one trace per request and one span per tool call. (3) Pseudocode for OTel instrumentation. (4) When to use Langfuse vs OTel: Langfuse for agent-specific and OTel for enterprise APM. About 200 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd5
Write-Host ""

Write-Host "[6/6] M21 - Long-running agents..." -ForegroundColor Green
$cmd6 = @"
Open the M21 HTML file in output/. Add a subsection titled Handling Long-Running Agents. Include: (1) The problem: agents take 2-5 minutes but HTTP timeouts at 30-60 seconds. (2) Three patterns: Pattern A async job queue with POST returning job_id and polling. Pattern B Server-Sent Events streaming progress updates. Pattern C WebSocket for full duplex with cancel support. (3) Pseudocode for Pattern B with FastAPI SSE. (4) Timeout handling: max 5 minutes then return partial results. About 250 words. Use str_replace.
"@
claude --dangerously-skip-permissions -p $cmd6
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "6 modules updated: M16 M08 M22 M18 M19 M21"
