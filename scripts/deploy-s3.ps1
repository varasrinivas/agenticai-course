# deploy-s3.ps1 - Replace the contents of s3://agenticai.varasrinivas.com with the local output/ folder
#
# Usage (from the repo root):
#   .\scripts\deploy-s3.ps1                # full deploy (delete stale + upload changed)
#   .\scripts\deploy-s3.ps1 -DryRun        # preview what would change, touch nothing
#   .\scripts\deploy-s3.ps1 -WipeFirst     # delete EVERYTHING in the bucket, then re-upload all
#
# Requires: AWS CLI v2 with credentials configured (aws configure / SSO / env vars)

param(
    [switch]$DryRun,
    [switch]$WipeFirst
)

$Bucket         = "agenticai.varasrinivas.com"
$DistributionId = "E204WFPQTUDQ3Q"   # CloudFront distribution serving https://agenticai.varasrinivas.com
$SourceDir      = Join-Path $PSScriptRoot "..\output"

if (-not (Test-Path (Join-Path $SourceDir "index.html"))) {
    Write-Error "Sanity check failed: $SourceDir\index.html not found. Run from the repo root."
    exit 1
}

# ---------------------------------------------------------------------------
# OPTION 1 (default, recommended): single sync that uploads new/changed files
# and deletes anything in the bucket that no longer exists locally.
# Faster and safer than wipe-then-upload - the site is never empty mid-deploy.
# ---------------------------------------------------------------------------
$syncArgs = @(
    "s3", "sync", $SourceDir, "s3://$Bucket/",
    "--delete",                       # remove S3 objects not present locally
    "--exclude", "*.md",              # don't publish notes/readme files
    "--exclude", "*archive/*",        # local version history - never publish

    "--cache-control", "max-age=300"  # short TTL so updates show up quickly
)
if ($DryRun) { $syncArgs += "--dryrun" }

# ---------------------------------------------------------------------------
# OPTION 2 (-WipeFirst): explicit delete of ALL existing content, then a full
# re-upload. Use when you want a guaranteed clean slate (e.g. renamed folders,
# stale metadata). The site is briefly empty between the two steps.
# ---------------------------------------------------------------------------
if ($WipeFirst) {
    Write-Host "== Step 1: deleting ALL existing content from s3://$Bucket ==" -ForegroundColor Yellow
    if ($DryRun) {
        aws s3 rm "s3://$Bucket/" --recursive --dryrun
    } else {
        aws s3 rm "s3://$Bucket/" --recursive
        if ($LASTEXITCODE -ne 0) { Write-Error "Delete failed; aborting before upload."; exit 1 }
    }
    Write-Host "== Step 2: uploading fresh content from $SourceDir ==" -ForegroundColor Yellow
}

aws @syncArgs
if ($LASTEXITCODE -ne 0) { Write-Error "Sync failed."; exit 1 }

# The site is served through CloudFront - invalidate the cache so visitors
# see the new content immediately instead of waiting for the TTL to expire.
if (-not $DryRun) {
    Write-Host "== Invalidating CloudFront cache ($DistributionId) ==" -ForegroundColor Yellow
    aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*"
    if ($LASTEXITCODE -ne 0) { Write-Error "Invalidation failed - site may serve stale content until cache TTL expires."; exit 1 }
}

Write-Host ""
if ($DryRun) {
    Write-Host "Dry run complete - nothing was changed." -ForegroundColor Cyan
} else {
    Write-Host "Deploy complete: https://agenticai.varasrinivas.com" -ForegroundColor Green
}
