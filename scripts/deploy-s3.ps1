# deploy-s3.ps1 - Deploy THIS repo's courses to the shared course-site bucket.
#
# DECOUPLED DEPLOY: the site (agenticai.varasrinivas.com) is one bucket fed by
# several repos. This repo owns only its own course folders and the mobile
# guide; the site's root index.html (the master catalog) is owned by the
# separate `agenticai-landing` repo. To avoid clobbering the catalog or other
# repos' courses, this script:
#   * syncs each courses/<slug>/ prefix INDIVIDUALLY (scoped --delete), plus mobile/
#   * NEVER touches the bucket root (no root index.html, no bucket-wide --delete)
#   * invalidates only /courses/* and /mobile/*
# The course slugs are discovered from output/courses/ - whatever this repo has
# locally is exactly what it deploys, and nothing else can be deleted.
#
# Usage (from the repo root):
#   .\scripts\deploy-s3.ps1                # deploy this repo's courses + mobile
#   .\scripts\deploy-s3.ps1 -DryRun        # preview what would change, touch nothing
#
# Bucket and CloudFront distribution ID are resolved in this order:
#   1. -Bucket / -DistributionId parameters
#   2. COURSE_S3_BUCKET / COURSE_CF_DISTRIBUTION_ID environment variables
#   3. scripts/deploy-config.ps1 (gitignored)
#
# scripts/deploy-config.ps1 template:
#   @{
#       Bucket         = "agenticai.varasrinivas.com"
#       DistributionId = "YOUR_DISTRIBUTION_ID"
#   }
#
# Requires: AWS CLI v2 with credentials configured (aws configure / SSO / env vars)

param(
    [switch]$DryRun,
    [string]$Bucket = $env:COURSE_S3_BUCKET,
    [string]$DistributionId = $env:COURSE_CF_DISTRIBUTION_ID
)

$SourceDir  = Join-Path $PSScriptRoot "..\output"
$CoursesDir = Join-Path $SourceDir "courses"
$MobileDir  = Join-Path $SourceDir "mobile"

$configFile = Join-Path $PSScriptRoot "deploy-config.ps1"
if ((-not $Bucket -or -not $DistributionId) -and (Test-Path $configFile)) {
    $cfg = & $configFile
    if (-not $Bucket)         { $Bucket = $cfg.Bucket }
    if (-not $DistributionId) { $DistributionId = $cfg.DistributionId }
}
if (-not $Bucket -or -not $DistributionId) {
    Write-Error "Bucket/DistributionId not set. Pass -Bucket/-DistributionId, set COURSE_S3_BUCKET/COURSE_CF_DISTRIBUTION_ID, or create scripts/deploy-config.ps1 (see template in this script's header)."
    exit 1
}
if (-not (Test-Path $CoursesDir)) {
    Write-Error "Sanity check failed: $CoursesDir not found. Run from the repo root."
    exit 1
}

# ---------------------------------------------------------------------------
# Common sync options. --delete is SCOPED to a single courses/<slug>/ (or
# mobile/) prefix on each call, so it can only ever remove objects under that
# one prefix - never the catalog, never another repo's course.
# ---------------------------------------------------------------------------
$commonExcludes = @(
    "--exclude", "*.md",              # don't publish notes/readme files
    "--exclude", "*archive/*",        # local version history - never publish
    "--cache-control", "max-age=300"  # short TTL so updates show up quickly
)

function Sync-Prefix($localPath, $s3Prefix) {
    $cmd = @("s3", "sync", $localPath, "s3://$Bucket/$s3Prefix", "--delete") + $commonExcludes
    if ($DryRun) { $cmd += "--dryrun" }
    Write-Host "== sync $s3Prefix ==" -ForegroundColor Yellow
    aws @cmd
    if ($LASTEXITCODE -ne 0) { Write-Error "Sync of $s3Prefix failed."; exit 1 }
}

# Each course folder this repo owns -> its own scoped prefix.
$slugs = Get-ChildItem $CoursesDir -Directory | Select-Object -ExpandProperty Name | Sort-Object
Write-Host "Deploying $($slugs.Count) course(s) owned by this repo: $($slugs -join ', ')" -ForegroundColor Cyan
foreach ($slug in $slugs) {
    Sync-Prefix (Join-Path $CoursesDir $slug) "courses/$slug/"
}

# The mobile study guide (also owned by this repo).
if (Test-Path $MobileDir) {
    Sync-Prefix $MobileDir "mobile/"
}

# ---------------------------------------------------------------------------
# NOTE: the site root index.html (master catalog) is deliberately NOT deployed
# here. It is owned by the `agenticai-landing` repo. This repo keeps a local
# copy at output/index.html for reference/preview only; it is never uploaded.
# ---------------------------------------------------------------------------

# Invalidate only the paths this repo touched - never the root index.
if (-not $DryRun) {
    Write-Host "== Invalidating CloudFront cache ($DistributionId): /courses/* and /mobile/* ==" -ForegroundColor Yellow
    aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/courses/*" "/mobile/*"
    if ($LASTEXITCODE -ne 0) { Write-Error "Invalidation failed - site may serve stale content until cache TTL expires."; exit 1 }
}

Write-Host ""
if ($DryRun) {
    Write-Host "Dry run complete - nothing was changed." -ForegroundColor Cyan
} else {
    Write-Host "Deploy complete: https://$Bucket" -ForegroundColor Green
}
