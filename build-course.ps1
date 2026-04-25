param(
    [ValidateSet("setup", "generate", "fix", "capstones", "labs", "mobile", "finalize", "all")]
    [string]$Phase = "all",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
$ProjectDir = Get-Location
$LogDir = Join-Path $ProjectDir "build-logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "build_$Timestamp.log"
$ProgressFile = Join-Path $LogDir "progress.json"
$MaxRetries = 5
$InitialWaitSeconds = 60
$MaxWaitSeconds = 3600
$DailyLimitWaitHours = 4

if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
if (!(Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }

# ============================================================================
# LOGGING
# ============================================================================
function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'HH:mm:ss')] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry
}

# ============================================================================
# PROGRESS TRACKING
# ============================================================================
function Load-Progress {
    if (Test-Path $ProgressFile) {
        $raw = Get-Content $ProgressFile -Raw
        $json = $raw | ConvertFrom-Json
        $ht = @{
            completed     = @($json.completed)
            totalApiCalls = [int]$json.totalApiCalls
            totalRetries  = [int]$json.totalRetries
            lastRun       = [string]$json.lastRun
        }
        return $ht
    }
    return @{
        completed     = @()
        totalApiCalls = 0
        totalRetries  = 0
        lastRun       = ""
    }
}

function Save-Progress {
    param($ProgressHash)
    $ProgressHash.lastRun = (Get-Date).ToString("o")
    $obj = [PSCustomObject]$ProgressHash
    $obj | ConvertTo-Json -Depth 5 | Set-Content $ProgressFile
}

function Test-IsCompleted {
    param([string]$TaskId)
    $p = Load-Progress
    return ($p.completed -contains $TaskId)
}

function Set-Completed {
    param([string]$TaskId)
    $p = Load-Progress
    $list = [System.Collections.ArrayList]@($p.completed)
    if (!$list.Contains($TaskId)) {
        $list.Add($TaskId) | Out-Null
    }
    $p.completed = @($list)
    $p.totalApiCalls = $p.totalApiCalls + 1
    Save-Progress $p
}

function Add-Retry {
    $p = Load-Progress
    $p.totalRetries = $p.totalRetries + 1
    Save-Progress $p
}

# ============================================================================
# RATE LIMIT DETECTION
# ============================================================================
function Test-RateLimit {
    param([string]$Text)
    if ($Text -match "rate.?limit") { return $true }
    if ($Text -match "429") { return $true }
    if ($Text -match "too many requests") { return $true }
    if ($Text -match "quota exceeded") { return $true }
    if ($Text -match "overloaded") { return $true }
    if ($Text -match "usage limit") { return $true }
    if ($Text -match "capacity") { return $true }
    return $false
}

function Test-DailyLimit {
    param([string]$Text)
    if ($Text -match "daily.?limit") { return $true }
    if ($Text -match "daily.?quota") { return $true }
    if ($Text -match "limit.*reset") { return $true }
    if ($Text -match "come back") { return $true }
    if ($Text -match "hours.*remaining") { return $true }
    return $false
}

function Wait-WithCountdown {
    param([int]$Seconds, [string]$Reason)
    $endTime = (Get-Date).AddSeconds($Seconds)
    Write-Host "  $Reason" -ForegroundColor Yellow
    Write-Host "  Waiting $Seconds seconds (until $($endTime.ToString('HH:mm:ss')))..." -ForegroundColor Yellow
    while ((Get-Date) -lt $endTime) {
        $remaining = [math]::Ceiling(($endTime - (Get-Date)).TotalSeconds)
        Write-Host "`r  Resuming in $remaining seconds...   " -NoNewline -ForegroundColor DarkYellow
        Start-Sleep -Seconds 5
    }
    Write-Host "`r  Resuming now.                        " -ForegroundColor Green
}

# ============================================================================
# CORE: Run Claude with retry + rate limit handling
# ============================================================================
function Invoke-Claude {
    param(
        [string]$Description,
        [string]$Command,
        [string]$TaskId = ""
    )

    # Skip if already completed (resume support)
    if ($TaskId -ne "" -and (Test-IsCompleted $TaskId)) {
        Write-Log "SKIP (done): $Description"
        return
    }

    Write-Log ">> $Description"

    $retryCount = 0
    $waitSec = $InitialWaitSeconds

    while ($retryCount -le $MaxRetries) {
        $output = ""
        $failed = $false

        try {
            $output = & claude --dangerously-skip-permissions -p $Command 2>&1 | Out-String
        }
        catch {
            $output = $_.ToString()
            $failed = $true
        }

        # Check daily limit
        if (Test-DailyLimit $output) {
            Write-Host "DAILY LIMIT HIT" -ForegroundColor Red
            Write-Host "Pausing $DailyLimitWaitHours hours. Ctrl+C then: .\build-course.ps1 -Phase $Phase -Resume" -ForegroundColor Yellow
            Add-Retry
            $waitHoursSec = $DailyLimitWaitHours * 3600
            Wait-WithCountdown -Seconds $waitHoursSec -Reason "Daily limit reached"
            $retryCount++
            continue
        }

        # Check rate limit
        if (Test-RateLimit $output) {
            $retryCount++
            Add-Retry
            if ($retryCount -gt $MaxRetries) {
                Write-Log "FAILED after $MaxRetries retries: $Description"
                Write-Host "Run: .\build-course.ps1 -Phase $Phase -Resume" -ForegroundColor Yellow
                exit 1
            }
            Wait-WithCountdown -Seconds $waitSec -Reason "Rate limited (attempt $retryCount of $MaxRetries)"
            $waitSec = [math]::Min($waitSec * 2, $MaxWaitSeconds)
            continue
        }

        # Check for other failures
        if ($failed) {
            Write-Log "ERROR: $Description - $output"
            Write-Host "Run: .\build-course.ps1 -Phase $Phase -Resume" -ForegroundColor Yellow
            exit 1
        }

        # Success — log and mark complete
        Add-Content -Path $LogFile -Value $output
        $lines = $output -split "`n"
        $preview = ($lines | Select-Object -First 15) -join "`n"
        Write-Host $preview
        if ($lines.Count -gt 15) {
            Write-Host "  ...($($lines.Count - 15) more lines in log)" -ForegroundColor DarkGray
        }
        Write-Log "OK: $Description"
        if ($TaskId -ne "") { Set-Completed $TaskId }
        return
    }
}

# ============================================================================
# PHASE: SETUP
# ============================================================================
function Phase-Setup {
    Write-Log "=== SETUP ==="

    $required = @(
        "CLAUDE.md",
        ".claude\commands\generate-module.md",
        ".claude\commands\fix-explanations.md",
        ".claude\commands\generate-capstone.md",
        ".claude\commands\validate-capstone.md",
        ".claude\commands\generate-lab-repo.md",
        ".claude\commands\generate-mobile.md",
        ".claude\commands\build-index.md",
        ".claude\commands\consistency-check.md",
        "prompts\00-course-philosophy.md",
        "prompts\07-depth-rules.md",
        "prompts\08-capstone-animations.md",
        "prompts\09-mobile-design.md",
        "prompts\10-rancher-deployment.md",
        "prompts\11-gap-coverage.md"
    )

    $miss = 0
    foreach ($f in $required) {
        if (!(Test-Path $f)) {
            Write-Host "  MISSING: $f" -ForegroundColor Red
            $miss++
        }
    }
    if ($miss -gt 0) {
        Write-Host "ERROR: $miss required files missing. Unzip scaffold first." -ForegroundColor Red
        exit 1
    }

    if ($Resume) {
        $p = Load-Progress
        $doneCount = $p.completed.Count
        Write-Log "Resuming: $doneCount tasks done, $($p.totalApiCalls) API calls, $($p.totalRetries) retries"
    }

    $existing = (Get-ChildItem "output\*.html" -ErrorAction SilentlyContinue).Count
    Write-Log "OK: $existing HTML files in output/"
}

# ============================================================================
# PHASE: GENERATE — New modules (M00, M15B, M22B)
# ============================================================================
function Phase-Generate {
    Write-Log "=== GENERATE: New modules ==="

    # M00
    if (!(Get-ChildItem "output\M00*.html" -ErrorAction SilentlyContinue)) {
        Invoke-Claude -Description "Generate M00" -TaskId "gen-M00" `
            -Command "Read all prompt files as specified in /generate-module, then generate module M00. Follow prompts/modules/M00-course-overview-agent-lifecycle.md exactly. Include all 8 sections and 7 animations. Save to output/. Run quality checklist."
        Invoke-Claude -Description "Review M00" -TaskId "review-M00" `
            -Command "Review output/M00*.html against quality standards. Auto-fix critical issues."
        Invoke-Claude -Description "Compact" -Command "/compact"
    }
    else { Write-Log "SKIP: M00 exists" }

    # M15B
    if (!(Get-ChildItem "output\M15B*.html" -ErrorAction SilentlyContinue)) {
        Invoke-Claude -Description "Generate M15B" -TaskId "gen-M15B" `
            -Command "Read all prompt files then generate module M15B. Follow prompts/modules/M15B-build-complete-agent-system.md. 80 percent lab. Every step: complete code, run command, expected output, checkpoint, troubleshooting. Save to output/."
        Invoke-Claude -Description "Review M15B" -TaskId "review-M15B" `
            -Command "Review output/M15B*.html against quality standards. Auto-fix critical issues."
        Invoke-Claude -Description "Compact" -Command "/compact"
    }
    else { Write-Log "SKIP: M15B exists" }

    # M22B
    if (!(Get-ChildItem "output\M22B*.html" -ErrorAction SilentlyContinue)) {
        Invoke-Claude -Description "Generate M22B" -TaskId "gen-M22B" `
            -Command "Read all prompt files then generate module M22B. Follow prompts/modules/M22B-deploy-agent-gcp-aws-local.md. Include 3 tiers: Docker, GCP Cloud Run, AWS Lambda. Include Rancher Desktop callout from prompts/10-rancher-deployment.md. Save to output/."
        Invoke-Claude -Description "Review M22B" -TaskId "review-M22B" `
            -Command "Review output/M22B*.html against quality standards. Auto-fix critical issues."
        Invoke-Claude -Description "Compact" -Command "/compact"
    }
    else { Write-Log "SKIP: M22B exists" }

    Write-Log "GENERATE phase complete"
}

# ============================================================================
# PHASE: FIX — All existing modules (9 passes each)
# ============================================================================
function Phase-Fix {
    Write-Log "=== FIX: 30 modules x 9 passes ==="

    $batches = @(
        @("M00", "M01", "M02"),
        @("M03", "M04", "M05"),
        @("M06", "M07", "M08"),
        @("M09", "M10", "M11"),
        @("M12", "M13", "M14"),
        @("M15", "M15B", "M16"),
        @("M17", "M18", "M19"),
        @("M20", "M21", "M22"),
        @("M22B", "M23", "M24"),
        @("M25", "M26", "M27")
    )

    $batchNum = 0
    foreach ($batch in $batches) {
        $batchNum++
        $batchStr = $batch -join ", "
        Write-Log "--- Batch $batchNum/10: $batchStr ---"

        foreach ($mod in $batch) {
            $htmlFile = Get-ChildItem "output\$mod*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
            if (!$htmlFile) {
                Write-Log "SKIP: $mod (no HTML)"
                continue
            }

            $fixCmd = "Apply all 9 fix-explanations passes to module $mod in output/. " +
                "Read prompts/07-depth-rules.md for all 14 rules. " +
                "Read prompts/06-cert-tip-callouts.md for cert tips. " +
                "Read prompts/11-gap-coverage.md for gap sections to add. " +
                "Pass 1: break dense sentences. " +
                "Pass 2: land analogies with concrete artifacts. " +
                "Pass 3: expand thin sections to 3+ paragraphs. " +
                "Pass 4: conversational code annotations. " +
                "Pass 5: add common misconceptions callout. " +
                "Pass 6: insert cert tips where applicable. " +
                "Pass 7: fix lab instructions (every step needs run command, expected output, checkpoint, troubleshooting). " +
                "Pass 8: add gap coverage sections per 11-gap-coverage.md (only for M04, M12, M19, M20, M21, M22). " +
                "Pass 9: update progress bar to of 30. " +
                "Use str_replace only, do NOT regenerate. Report word count before and after."

            Invoke-Claude -Description "Fix $mod" -TaskId "fix-$mod" -Command $fixCmd
        }

        Invoke-Claude -Description "Compact after batch $batchNum" -Command "/compact"
    }

    Invoke-Claude -Description "Post-fix consistency check" -TaskId "fix-consistency" `
        -Command "Scan all HTML files in output/. Check CSS, fonts, nav, quizzes, progress bars, animations, cert tips, lab steps, gap sections. Report inconsistencies. Auto-fix critical issues."

    Write-Log "FIX phase complete"
}

# ============================================================================
# PHASE: CAPSTONES
# ============================================================================
function Phase-Capstones {
    Write-Log "=== CAPSTONES ==="

    $capstones = @(
        @{ Id = "cap-1"; Args = "CAPSTONE-1 DOMAIN-C"; File = "CAPSTONE-1" },
        @{ Id = "cap-2"; Args = "CAPSTONE-2 DOMAIN-C"; File = "CAPSTONE-2" },
        @{ Id = "cap-3"; Args = "CAPSTONE-3 DOMAIN-C"; File = "CAPSTONE-3" },
        @{ Id = "cap-4"; Args = "CAPSTONE-4 DOMAIN-C"; File = "CAPSTONE-4" },
        @{ Id = "cap-5"; Args = "CAPSTONE-5 DOMAIN-C"; File = "CAPSTONE-5" },
        @{ Id = "cap-6"; Args = "CAPSTONE-6"; File = "CAPSTONE-6" }
    )

    foreach ($cap in $capstones) {
        $exists = Get-ChildItem "output\$($cap.File)*.html" -ErrorAction SilentlyContinue
        if ($exists) {
            Write-Log "SKIP: $($cap.File) exists"
            continue
        }

        $genCmd = "Read prompts/00-course-philosophy.md, prompts/07-depth-rules.md, " +
            "prompts/08-capstone-animations.md, prompts/03-capstone-domains.md, " +
            "prompts/10-rancher-deployment.md. " +
            "Read capstone brief from prompts/modules/ if it exists. " +
            "Generate capstone HTML for $($cap.Args). " +
            "Include architecture diagram, all specified animations, " +
            "lab steps with Rule 13 format (code, run command, expected output, checkpoint, troubleshooting), " +
            "mock data, test scenarios, " +
            "Tier 1 local deployment (Docker or Rancher Desktop + DuckDB). " +
            "Save to output/."

        Invoke-Claude -Description "Generate $($cap.Args)" -TaskId $cap.Id -Command $genCmd

        $valCmd = "Validate output/$($cap.File)*.html. " +
            "Run 10 validation passes: prerequisites, environment setup, code completeness, " +
            "mock data, step sequence, API accuracy, conceptual accuracy, quiz accuracy, " +
            "student experience, domain-specific. Auto-fix critical issues."

        Invoke-Claude -Description "Validate $($cap.File)" -TaskId "val-$($cap.File)" -Command $valCmd

        Invoke-Claude -Description "Compact" -Command "/compact"
    }

    Write-Log "CAPSTONES phase complete"
}

# ============================================================================
# PHASE: LABS
# ============================================================================
function Phase-Labs {
    Write-Log "=== LABS ==="

    $labBatches = @(
        @{ Id = "labs-1"; Cmd = "Generate lab repo for M00, M01, M02, M03, M04, M05 in labs/ folder. Each lab needs README.md, starter/ with skeleton code and TODOs, solution/ with complete Python and Node.js code, expected_output/. Mock data complete in starter/." },
        @{ Id = "labs-2"; Cmd = "Generate lab repo for M06, M07, M08, M09, M10, M11 in labs/ folder. Include docs/ for M09 with UCC reference documents." },
        @{ Id = "labs-3"; Cmd = "Generate lab repo for M12, M13, M14, M15, M15B in labs/ folder. M15B needs mock_data.py with 15 UCC filings, all tools, agents, tests." },
        @{ Id = "labs-4"; Cmd = "Generate lab repo for M16, M17, M18, M19, M20, M21, M22, M22B in labs/ folder. M22B needs Dockerfile, docker-compose.yml, GCP and AWS deploy scripts." },
        @{ Id = "labs-5"; Cmd = "Generate lab repo for M25, M26, M27 in labs/ folder. M25 needs .claude/ directory structure. M27 needs mock exam JSON with answer keys." },
        @{ Id = "labs-6"; Cmd = "Generate lab repo for capstone-1, capstone-2, capstone-3 in labs/ folder with domain-a, domain-b, domain-c subdirectories." },
        @{ Id = "labs-7"; Cmd = "Generate lab repo for capstone-4, capstone-5, capstone-6 in labs/ folder. Capstone-6 needs 15 mock source files, bronze_table mock, 3-tier deployment." },
        @{ Id = "labs-8"; Cmd = "Generate labs/README.md, labs/SETUP.md, labs/requirements.txt, labs/package.json, labs/.gitignore, labs/.env.example, and labs/shared/ with mock_ucc_data.py and test_helpers.py." }
    )

    foreach ($batch in $labBatches) {
        Invoke-Claude -Description "Lab $($batch.Id)" -TaskId $batch.Id -Command $batch.Cmd
        Invoke-Claude -Description "Compact" -Command "/compact"
    }

    Write-Log "LABS phase complete"
}

# ============================================================================
# PHASE: MOBILE
# ============================================================================
function Phase-Mobile {
    Write-Log "=== MOBILE: Condensed mobile versions ==="

    if (!(Test-Path "output\mobile")) { New-Item -ItemType Directory -Path "output\mobile" | Out-Null }

    $mobileBatches = @(
        @{ Id = "mobile-1"; Mods = "M00, M01, M02, M03, M04, M05" },
        @{ Id = "mobile-2"; Mods = "M06, M07, M08, M09, M10, M11" },
        @{ Id = "mobile-3"; Mods = "M12, M13, M14, M15, M15B, M16" },
        @{ Id = "mobile-4"; Mods = "M17, M18, M19, M20, M21, M22" },
        @{ Id = "mobile-5"; Mods = "M22B, M23, M24, M25, M26, M27" }
    )

    foreach ($batch in $mobileBatches) {
        $mobileCmd = "Read prompts/09-mobile-design.md for mobile design spec. " +
            "For each module in $($batch.Mods): " +
            "read the desktop HTML from output/, " +
            "extract core concept, best analogy, " +
            "convert code to pseudocode (10-15 lines max, language-agnostic), " +
            "take 2-3 misconceptions and 3 quiz questions. " +
            "Generate 9-card mobile HTML with swipe navigation. " +
            "Save each to output/mobile/MODULE-mobile.html. " +
            "Total 800-1200 words per module. No real code. " +
            "16px minimum font. 44px tap targets. Dark theme."

        Invoke-Claude -Description "Mobile $($batch.Id): $($batch.Mods)" -TaskId $batch.Id -Command $mobileCmd
        Invoke-Claude -Description "Compact" -Command "/compact"
    }

    Invoke-Claude -Description "Mobile index" -TaskId "mobile-index" `
        -Command "Generate output/mobile/index.html as mobile course landing page. List all modules as tap-friendly cards with track colors. Link each to its mobile HTML. Same dark theme as desktop."

    $mobileCount = (Get-ChildItem "output\mobile\*-mobile.html" -ErrorAction SilentlyContinue).Count
    Write-Log "MOBILE phase complete: $mobileCount mobile modules"
}

# ============================================================================
# PHASE: FINALIZE
# ============================================================================
function Phase-Finalize {
    Write-Log "=== FINALIZE ==="

    Invoke-Claude -Description "Build index" -TaskId "fin-index" `
        -Command "Scan output/ for all HTML files. Generate output/index.html as course landing page with 9 tracks, module cards, 3 learning paths (Weekend Builder, Deep Diver, Cert Prep), progress tracker, mobile version link."

    Invoke-Claude -Description "Final consistency check" -TaskId "fin-check" `
        -Command "Scan ALL HTML in output/ including mobile/. Verify: all progress bars say of 30. Previous and Next links correct. CSS consistent. Quiz formats match. Cert tips present where required. Lab steps complete. Gap sections present in M04 M12 M19 M20 M21 M22. Report every inconsistency."

    # Summary stats
    $mc = (Get-ChildItem "output\M*.html" -ErrorAction SilentlyContinue).Count
    $cc = (Get-ChildItem "output\CAPSTONE*.html" -ErrorAction SilentlyContinue).Count
    $mob = (Get-ChildItem "output\mobile\*-mobile.html" -ErrorAction SilentlyContinue).Count
    $lc = (Get-ChildItem "labs" -Recurse -Filter "README.md" -ErrorAction SilentlyContinue).Count
    $p = Load-Progress

    Write-Log "=========================================="
    Write-Host "BUILD COMPLETE" -ForegroundColor Green
    Write-Log "=========================================="
    Write-Log "  Modules:      $mc"
    Write-Log "  Capstones:    $cc"
    Write-Log "  Mobile:       $mob"
    Write-Log "  Lab READMEs:  $lc"
    Write-Log "  API calls:    $($p.totalApiCalls)"
    Write-Log "  Retries:      $($p.totalRetries)"
    Write-Log "  Log:          $LogFile"
    Write-Log "=========================================="
    Write-Host "  Desktop: npx serve output -p 3000" -ForegroundColor Green
    Write-Host "  Mobile:  npx serve output/mobile -p 3001" -ForegroundColor Green
    Write-Host "  Labs:    cd labs; git init; git add .; git push" -ForegroundColor Green
    Write-Log "=========================================="
}

# ============================================================================
# MAIN
# ============================================================================

Write-Log "=========================================="
Write-Log "CLAUDE AGENT COURSE BUILD"
Write-Log "Phase: $Phase | Resume: $Resume"
Write-Log "Started: $(Get-Date)"
Write-Log "=========================================="

switch ($Phase) {
    "setup"     { Phase-Setup }
    "generate"  { Phase-Setup; Phase-Generate }
    "fix"       { Phase-Setup; Phase-Fix }
    "capstones" { Phase-Setup; Phase-Capstones }
    "labs"      { Phase-Setup; Phase-Labs }
    "mobile"    { Phase-Setup; Phase-Mobile }
    "finalize"  { Phase-Setup; Phase-Finalize }
    "all"       { Phase-Setup; Phase-Generate; Phase-Fix; Phase-Capstones; Phase-Labs; Phase-Mobile; Phase-Finalize }
}

Write-Log "Finished: $(Get-Date)"
