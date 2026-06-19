# Deploying the Course Site to S3 + CloudFront

The course is a static site served at **https://agenticai.varasrinivas.com**.

| Piece | Value |
|---|---|
| S3 bucket | `agenticai.varasrinivas.com` (us-east-1, private — no S3 website hosting) |
| CloudFront distribution | ID in `scripts/deploy-config.ps1` (gitignored) → `*.cloudfront.net` |
| DNS | `agenticai.varasrinivas.com` is a CNAME to the CloudFront domain |
| Default root object | `index.html` (set on the distribution) |
| Source of truth | local `output/` folder (course catalog `index.html` + `courses/<track>/…` + `mobile/…`) |
| Deploy script | `scripts/deploy-s3.ps1` |

**Note on the layout change:** the bucket previously held the old *flat* layout
(module HTML files at the bucket root). The current `output/` folder uses the
*nested* layout (`courses/<track>/...`). The first deploy after this change
deletes ~195 root objects and uploads ~224 new ones — that is expected, not an
error. Old flat-layout URLs (e.g. `/M09-rag-retrieval-augmented-generation.html`,
`/cc/CC5-hooks.html`) are 301-redirected to their new `/courses/...` locations by
the CloudFront Function `agenticai-legacy-redirects` (viewer-request, source in
`scripts/cloudfront-legacy-redirects.js`).

Because CloudFront points at the S3 *REST* endpoint (not a website endpoint),
subfolder URLs like `/courses/cc/` do **not** auto-resolve to `index.html` —
only the site root does. All internal links already point to explicit
`.../index.html` paths, so this is fine; just don't hand out bare folder URLs.

## Prerequisites

- AWS CLI v2 installed (`aws --version`)
- Credentials configured (`aws configure`, SSO, or env vars) with permission for
  `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the
  bucket and `cloudfront:CreateInvalidation` on the distribution
- `scripts/deploy-config.ps1` created (gitignored) with the bucket name and
  distribution ID — template in the header of `scripts/deploy-s3.ps1`.
  Alternatively pass `-Bucket`/`-DistributionId` or set the
  `COURSE_S3_BUCKET`/`COURSE_CF_DISTRIBUTION_ID` environment variables.

## Steps

Run everything from the repo root.

### 1. Preview what would change (dry run — touches nothing)

```powershell
.\scripts\deploy-s3.ps1 -DryRun
```

Review the `(dryrun) delete:` and `(dryrun) upload:` lines. Deletes are objects
in the bucket that no longer exist locally; if a delete surprises you, stop and
investigate before deploying.

### 2. Deploy

```powershell
.\scripts\deploy-s3.ps1
```

This runs one `aws s3 sync output/ s3://… --delete`, which:
- uploads new and changed files (`Cache-Control: max-age=300`); `.md` files and
  `archive/` folders are excluded — archives are local version history of
  regenerated modules and are not linked from any page, so they stay off the
  public site (note: `--exclude *archive/*` also means `--delete` will ignore
  any `archive/` objects already in the bucket)
- deletes bucket objects with no local counterpart
- then invalidates the CloudFront cache (`/*`) so changes are visible immediately

Use `.\scripts\deploy-s3.ps1 -WipeFirst` only when you want a guaranteed clean
slate (deletes **everything** first, then re-uploads all ~260 files / ~89 MB;
the site is briefly empty between the two steps).

### 3. Verify

```powershell
# Homepage serves and shows the new title
Invoke-WebRequest https://agenticai.varasrinivas.com/ -UseBasicParsing |
    Select-Object StatusCode

# Spot-check a nested course page
Invoke-WebRequest https://agenticai.varasrinivas.com/courses/cc/index.html -UseBasicParsing |
    Select-Object StatusCode
```

Then open https://agenticai.varasrinivas.com in a browser and click through one
module per track. If you still see old content, the invalidation may not have
finished yet — check with:

```powershell
aws cloudfront list-invalidations --distribution-id <DISTRIBUTION_ID>
```

## Rollback

There is no versioning safety net unless bucket versioning is enabled. To roll
back, check out the previous git state of `output/` and re-run the deploy:

```powershell
git stash            # or commit current work first
git checkout <good-commit> -- output/
.\scripts\deploy-s3.ps1
```
