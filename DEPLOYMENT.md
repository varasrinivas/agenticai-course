# Deploying to S3 + CloudFront

The course site is a static site served at **https://agenticai.varasrinivas.com**.

> **Decoupled deploys.** The site is one bucket fed by **several repos**. This
> repo deploys only **its own course folders** (`courses/<slug>/`) and the
> **mobile** guide. The site's root **`index.html` (the master catalog) is owned
> by `learnings-hub/agenticai/index.html`**, and three courses
> (`courses/llmops/`, `courses/context-engineering/`,
> `courses/ai-platform-engineering/`) are owned by their own repos
> (`llmops-kit`, `context-eng-kit`, `ai-platform-kit`). No repo's deploy may
> ever `--delete` outside the prefixes it owns.

| Piece | Value |
|---|---|
| S3 bucket | `agenticai.varasrinivas.com` (us-east-1, private — no S3 website hosting) |
| CloudFront distribution | ID in `scripts/deploy-config.ps1` (gitignored) → `*.cloudfront.net` |
| DNS | `agenticai.varasrinivas.com` is a CNAME to the CloudFront domain |
| Default root object | `index.html` (set on the distribution; **deployed from `learnings-hub/agenticai/`, not here**) |
| This repo deploys | `output/courses/<slug>/` (8 courses) + `output/mobile/` |
| This repo does NOT deploy | the root `index.html` (owned by `learnings-hub/agenticai/`) |
| Deploy script | `scripts/deploy-s3.ps1` |

The course slugs this repo owns are discovered automatically from
`output/courses/` — currently `ai-cli-comparison`, `cc`, `claude-agents`,
`gemini-cli`, `gemini-code-assist`, `mcp`, `multi-sdk-agents`, `opensource`.
Each is synced to its own `courses/<slug>/` prefix with a **scoped** `--delete`,
so a deploy from this repo can never remove the catalog or another repo's course.

`output/index.html` is kept as a **local preview only** and is not uploaded —
the authoritative catalog is `learnings-hub/agenticai/index.html`.

> **Note.** The `agenticai-landing` repo previously owned the catalog and still
> contains a stale 11-course copy. It was **retired on 2026-08-28** and its
> deploy script now refuses to run. Do not deploy the catalog from there.

## Legacy redirects & subfolder behavior

Old flat-layout URLs (e.g. `/M09-rag-retrieval-augmented-generation.html`,
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

You'll see one scoped sync per course slug (`== sync courses/<slug>/ ==`) plus
`== sync mobile/ ==`. Review the `(dryrun) delete:` / `(dryrun) upload:` lines.
Deletes are objects under **that one prefix** with no local counterpart; if a
delete surprises you, stop and investigate before deploying.

### 2. Deploy

```powershell
.\scripts\deploy-s3.ps1
```

This runs `aws s3 sync` once **per course prefix** (and once for `mobile/`), each
with a `--delete` scoped to that prefix (`Cache-Control: max-age=300`; `.md`
files and `archive/` folders excluded), then invalidates
`/courses/*` and `/mobile/*` so changes are visible immediately. It never touches
the bucket root or the catalog.

### 3. Deploy the catalog (separately, only when it changes)

The root `index.html` catalog is deployed from **`learnings-hub/agenticai/`**:

```bash
# from the learnings-hub repo
aws s3 cp agenticai/index.html s3://agenticai.varasrinivas.com/index.html   --content-type "text/html; charset=utf-8" --cache-control "public, max-age=300"
MSYS_NO_PATHCONV=1 aws cloudfront create-invalidation   --distribution-id E204WFPQTUDQ3Q --paths "/" "/index.html"
```

Update the catalog there whenever a course is added/renamed/removed — editing a
card doesn't touch the course itself.

### 4. Verify

```powershell
# Homepage serves (deployed from learnings-hub/agenticai/)
Invoke-WebRequest https://agenticai.varasrinivas.com/ -UseBasicParsing | Select-Object StatusCode

# A course page owned by this repo
Invoke-WebRequest https://agenticai.varasrinivas.com/courses/multi-sdk-agents/index.html -UseBasicParsing | Select-Object StatusCode
```

If you still see old content, the invalidation may not have finished — check with:

```powershell
aws cloudfront list-invalidations --distribution-id <DISTRIBUTION_ID>
```

## Rollback

There is no versioning safety net unless bucket versioning is enabled. To roll
back a course, check out the previous git state of that course folder and re-run
the deploy:

```powershell
git checkout <good-commit> -- output/courses/<slug>/
.\scripts\deploy-s3.ps1
```
