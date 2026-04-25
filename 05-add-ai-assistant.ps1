# 05-add-ai-assistant.ps1
# Embeds an offline AI tutor (fuzzy-search knowledge base) into each course
# No API key needed. Works offline. Instant responses.
#
# Run: .\05-add-ai-assistant.ps1
# Run: .\05-add-ai-assistant.ps1 -Resume
# Run: .\05-add-ai-assistant.ps1 -CourseSlug ai-sdlc-data-engineering

param(
    [string]$CourseSlug = "",
    [switch]$Resume
)
$ErrorActionPreference = "Stop"
$script:Resume = $Resume
. .\_shared-progress.ps1

Write-Host "=== ADD AI ASSISTANT ===" -ForegroundColor Cyan
Write-Host "Embedding offline tutor (no API key needed)." -ForegroundColor Yellow
if ($Resume) { Write-Host "Resuming -- skipping completed courses." -ForegroundColor Yellow }

if ($CourseSlug -ne "") {
    $courses = @(Get-ChildItem "output\$CourseSlug.html" -EA SilentlyContinue)
    if ($courses.Count -eq 0) { Write-Host "Not found: output\$CourseSlug.html" -ForegroundColor Red; exit 1 }
} else {
    $courses = Get-ChildItem "output\*.html" -EA SilentlyContinue | Where-Object { $_.Name -ne "index.html" -and $_.Name -ne "ai-course-assistant.html" }
}

Write-Host "Processing $($courses.Count) course(s)." -ForegroundColor White
Write-Host ""

$n = 0
foreach ($course in $courses) {
    $n++
    $slug = $course.BaseName
    Write-Host "[$n/$($courses.Count)] $slug" -ForegroundColor Green

    $cmd = @"
Open output/${slug}.html. Check if it already contains the string ai-tutor-fab. If yes report SKIP and do nothing.

If NOT present add an offline AI tutor widget. This is a floating button that opens a searchable knowledge base panel. No API calls. No API key. Everything runs in the browser.

Step 1: Identify the course from the page title and content. Determine which track it belongs to: Data Engineering or Spring Boot API or React Frontend or Gemini Code Assist or MCP Servers or OpenSpec or AI Agents or Atlassian AI or Prompt Engineering.

Step 2: Build a knowledge base array of 15-20 QA entries specific to THIS course. Each entry has: q (question string) and c (category: concept or code or mistake or domain) and t (array of 2 tags: course name and phase) and a (answer HTML with strong tags for bold and code tags for inline code and pre tags for code blocks and div class co tip or co warn or co prod for callouts).

The QA entries must cover: 3-4 key concepts with analogy-first explanations. 3-4 code examples with annotated walkthroughs. 2-3 common mistakes with corrections. 2-3 UCC domain connections. 2-3 production consequences. Use real UCC table names and field names and canonical entities from prompts/03-content-guidelines.md.

Step 3: Add CSS just before the closing </style> tag. Use the ai-tutor- prefix on all classes. Include: a fixed-position floating action button bottom-right with gradient background. A panel that slides open with: search input with fuzzy matching. Category filter tabs. Expandable QA cards with icons per category. Mobile responsive at 500px breakpoint. Dark theme matching the course.

Step 4: Add the HTML elements just before </body>: the floating button and the panel with search and tabs and QA list.

Step 5: Add JavaScript just before </body> in a script tag: the KB array with the 15-20 entries. Fuzzy search function that matches query terms against q and a and t fields. Render functions for tabs and QA list. Toggle function for expanding cards. Search input handler with 150ms debounce. All variable and function names prefixed with aiTutor to avoid conflicts.

CRITICAL: The knowledge base content must be specific to THIS course. A Data Engineering course gets PySpark and BigQuery and Medallion Architecture QAs. A Spring Boot API course gets REST endpoint and OAuth2 and Testcontainers QAs. Do NOT use generic content.

CRITICAL: Do NOT use any external API calls. Everything is self-contained in the HTML file.

Report: ADDED with count of QA entries or SKIP if already present.
"@

    Invoke-Claude -TaskId "assistant-$slug" -Command $cmd

    if ($n % 2 -eq 0) {
        Write-Host "  [compacting]" -ForegroundColor DarkGray
        claude --dangerously-skip-permissions -p "/compact" | Out-Null
    }
    Write-Host ""
}

Write-Host "=== AI ASSISTANT ADDED ===" -ForegroundColor Green
Write-Host "Each course has a floating tutor button. No API key needed." -ForegroundColor Yellow
Write-Host "Learners search questions and get instant answers with code examples." -ForegroundColor White
