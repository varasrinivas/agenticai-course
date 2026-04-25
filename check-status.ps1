# check-status.ps1
# Scans your project and reports what's done vs pending
# Run: .\check-status.ps1

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "=== COURSE BUILD STATUS ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Existing Modules ---
Write-Host "1. MODULES (output/*.html)" -ForegroundColor Yellow
$allModules = @("M00","M01","M02","M03","M04","M05","M06","M07","M08","M09","M10","M11","M12","M13","M14","M15","M15B","M16","M17","M18","M19","M20","M21","M22","M22B","M23","M24","M25","M26","M27")
$found = 0
$missing = @()
foreach ($m in $allModules) {
    $file = Get-ChildItem "output\$m*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($file) {
        $found++
    } else {
        $missing += $m
    }
}
Write-Host "   Found: $found / $($allModules.Count)" -ForegroundColor $(if ($found -eq $allModules.Count) {"Green"} else {"White"})
if ($missing.Count -gt 0) {
    Write-Host "   Missing: $($missing -join ', ')" -ForegroundColor Red
}

# --- 2. Capstones ---
Write-Host ""
Write-Host "2. CAPSTONES (output/CAPSTONE*.html)" -ForegroundColor Yellow
$capstones = @("CAPSTONE-1","CAPSTONE-2","CAPSTONE-3","CAPSTONE-4","CAPSTONE-5","CAPSTONE-6")
$capFound = 0
$capMissing = @()
foreach ($c in $capstones) {
    $file = Get-ChildItem "output\$c*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($file) {
        $capFound++
    } else {
        $capMissing += $c
    }
}
Write-Host "   Found: $capFound / $($capstones.Count)" -ForegroundColor $(if ($capFound -eq $capstones.Count) {"Green"} else {"White"})
if ($capMissing.Count -gt 0) {
    Write-Host "   Missing: $($capMissing -join ', ')" -ForegroundColor Red
}

# --- 3. Labs ---
Write-Host ""
Write-Host "3. LABS (labs/ folder)" -ForegroundColor Yellow
if (Test-Path "labs") {
    $labReadmes = (Get-ChildItem "labs" -Recurse -Filter "README.md" -ErrorAction SilentlyContinue).Count
    $labStarters = (Get-ChildItem "labs" -Recurse -Filter "*.py" -Path "*starter*" -ErrorAction SilentlyContinue).Count
    $labSolutions = (Get-ChildItem "labs" -Recurse -Filter "*.py" -Path "*solution*" -ErrorAction SilentlyContinue).Count
    Write-Host "   Lab READMEs: $labReadmes" -ForegroundColor Green
    Write-Host "   Starter files: $labStarters"
    Write-Host "   Solution files: $labSolutions"
} else {
    Write-Host "   NOT GENERATED" -ForegroundColor Red
}

# --- 4. Mobile ---
Write-Host ""
Write-Host "4. MOBILE (output/mobile/*-mobile.html)" -ForegroundColor Yellow
if (Test-Path "output\mobile") {
    $mobileCount = (Get-ChildItem "output\mobile\*-mobile.html" -ErrorAction SilentlyContinue).Count
    Write-Host "   Mobile modules: $mobileCount / 30" -ForegroundColor $(if ($mobileCount -ge 28) {"Green"} else {"White"})
} else {
    Write-Host "   NOT GENERATED" -ForegroundColor Red
}

# --- 5. Index Page ---
Write-Host ""
Write-Host "5. INDEX PAGE" -ForegroundColor Yellow
if (Test-Path "output\index.html") {
    Write-Host "   output\index.html EXISTS" -ForegroundColor Green
} else {
    Write-Host "   NOT GENERATED" -ForegroundColor Red
}

# --- 6. Check if gaps and patterns were applied ---
Write-Host ""
Write-Host "6. DESIGN PATTERNS + GAPS (content checks)" -ForegroundColor Yellow

# Check M12 for design patterns
$m12File = Get-ChildItem "output\M12*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m12File) {
    $m12Content = Get-Content $m12File.FullName -Raw
    if ($m12Content -match "Design Pattern|design pattern|8 pattern|Pattern Catalog|decision tree") {
        Write-Host "   M12 Design Patterns: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M12 Design Patterns: NOT FOUND" -ForegroundColor Red
    }
    if ($m12Content -match "Error Handling|Retry Pattern|exponential backoff") {
        Write-Host "   M12 Error Handling: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M12 Error Handling: NOT FOUND" -ForegroundColor Red
    }
    if ($m12Content -match "Extended Thinking|extended thinking|budget_tokens") {
        Write-Host "   M12 Extended Thinking: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M12 Extended Thinking: NOT FOUND" -ForegroundColor Red
    }
    if ($m12Content -match "Script vs Agent|script approach|hardcoded") {
        Write-Host "   M12 Script vs Agent: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M12 Script vs Agent: NOT FOUND" -ForegroundColor Red
    }
} else {
    Write-Host "   M12 not found in output/" -ForegroundColor Red
}

# Check M04 for multi-modal
$m04File = Get-ChildItem "output\M04*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m04File) {
    $m04Content = Get-Content $m04File.FullName -Raw
    if ($m04Content -match "Multi-Modal|multi-modal|Vision|vision|PDF input") {
        Write-Host "   M04 Multi-Modal: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M04 Multi-Modal: NOT FOUND" -ForegroundColor Red
    }
}

# Check M21 for streaming + auth
$m21File = Get-ChildItem "output\M21*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m21File) {
    $m21Content = Get-Content $m21File.FullName -Raw
    if ($m21Content -match "Streaming|streaming|SSE|Server-Sent") {
        Write-Host "   M21 Streaming Deep-Dive: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M21 Streaming Deep-Dive: NOT FOUND" -ForegroundColor Red
    }
    if ($m21Content -match "Authentication|authorization|OAuth|JWT|API key auth") {
        Write-Host "   M21 Authentication: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M21 Authentication: NOT FOUND" -ForegroundColor Red
    }
}

# Check M22 for prompt caching + batch
$m22File = Get-ChildItem "output\M22*.html" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch "M22B" } | Select-Object -First 1
if ($m22File) {
    $m22Content = Get-Content $m22File.FullName -Raw
    if ($m22Content -match "Prompt Caching|prompt caching|cache TTL") {
        Write-Host "   M22 Prompt Caching: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M22 Prompt Caching: NOT FOUND" -ForegroundColor Red
    }
    if ($m22Content -match "Batch API|batch API|50 percent discount") {
        Write-Host "   M22 Batch API: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M22 Batch API: NOT FOUND" -ForegroundColor Red
    }
}

# Check M19 for compliance + prompt versioning
$m19File = Get-ChildItem "output\M19*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m19File) {
    $m19Content = Get-Content $m19File.FullName -Raw
    if ($m19Content -match "Compliance|compliance|audit log|HIPAA|SOC2|GDPR") {
        Write-Host "   M19 Compliance Logging: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M19 Compliance Logging: NOT FOUND" -ForegroundColor Red
    }
    if ($m19Content -match "Prompt Versioning|prompt versioning|prompt.*version control") {
        Write-Host "   M19 Prompt Versioning: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M19 Prompt Versioning: NOT FOUND" -ForegroundColor Red
    }
}

# Check M20 for agent versioning
$m20File = Get-ChildItem "output\M20*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m20File) {
    $m20Content = Get-Content $m20File.FullName -Raw
    if ($m20Content -match "Agent Versioning|canary deploy|rollback") {
        Write-Host "   M20 Agent Versioning: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M20 Agent Versioning: NOT FOUND" -ForegroundColor Red
    }
}

# Check M00 for script vs agent
$m00File = Get-ChildItem "output\M00*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($m00File) {
    $m00Content = Get-Content $m00File.FullName -Raw
    if ($m00Content -match "Script vs Agent|script approach|hardcoded") {
        Write-Host "   M00 Script vs Agent: ADDED" -ForegroundColor Green
    } else {
        Write-Host "   M00 Script vs Agent: NOT FOUND" -ForegroundColor Red
    }
}

# --- 7. Diagrams check (sample) ---
Write-Host ""
Write-Host "7. DIAGRAMS (SVG check on sample modules)" -ForegroundColor Yellow
$diagramModules = @("M01","M05","M09","M12","M16","M21")
foreach ($dm in $diagramModules) {
    $dmFile = Get-ChildItem "output\$dm*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($dmFile) {
        $dmContent = Get-Content $dmFile.FullName -Raw
        $svgCount = ([regex]::Matches($dmContent, "<svg")).Count
        if ($svgCount -gt 0) {
            Write-Host "   $dm : $svgCount SVG diagrams" -ForegroundColor Green
        } else {
            Write-Host "   $dm : NO SVG diagrams found" -ForegroundColor Red
        }
    }
}

# --- Summary ---
Write-Host ""
Write-Host "=== WHAT TO RUN NEXT ===" -ForegroundColor Cyan
if ($missing.Count -gt 0) {
    Write-Host "  .\build-course.ps1 -Phase generate   # Create $($missing -join ', ')" -ForegroundColor White
}
if ($capMissing.Count -gt 0) {
    Write-Host "  .\build-course.ps1 -Phase capstones   # Create $($capMissing.Count) capstones" -ForegroundColor White
}
if (!(Test-Path "labs")) {
    Write-Host "  .\build-course.ps1 -Phase labs        # Generate lab repository" -ForegroundColor White
}
if (!(Test-Path "output\mobile")) {
    Write-Host "  .\build-course.ps1 -Phase mobile      # Generate mobile versions" -ForegroundColor White
}
if (!(Test-Path "output\index.html")) {
    Write-Host "  .\build-course.ps1 -Phase finalize    # Build index + consistency check" -ForegroundColor White
}
Write-Host ""
