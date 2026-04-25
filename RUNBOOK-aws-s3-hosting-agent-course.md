# Runbook: Host Claude Agent Course on AWS S3 + CloudFront (HTTPS)

> **Windows users**: All commands use **PowerShell**. Do NOT use Git Bash — it mangles JSON arguments passed to `aws.exe`. Open PowerShell (standalone, not VS Code terminal) and run commands there.

**Domain**: ${DOMAIN}
**Target URL**: https://${SITE_FQDN}
**Architecture**: S3 (static files) → CloudFront (CDN + HTTPS) → ACM (SSL) → DNS

---

## Architecture Overview

```
Browser
  │ HTTPS
  ▼
CloudFront Distribution (${SITE_FQDN})
  │  Origin Access Control (OAC)
  ▼
S3 Bucket: ${SITE_FQDN} (private, no public access)
  └── index.html
  └── M00-course-overview-agent-lifecycle.html
  └── M01-llm-mental-model.html
  └── M02-tokens.html
  └── ... (all module, capstone, and appendix HTML files)
```

**Why CloudFront instead of S3 static website hosting directly?**
- S3 static website endpoint is HTTP only; CloudFront adds HTTPS
- CloudFront caches globally for low latency
- OAC keeps the bucket private (no public S3 URL exposure)
- ACM certificates are free with CloudFront

---

## Step 0: Install and Configure AWS CLI

### Install AWS CLI v2

**Windows (recommended — MSI installer)**
1. Download the installer from:
   https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run the `.msi` installer and follow prompts.
3. Open a new Command Prompt or PowerShell window and verify:
   ```
   aws --version
   # Expected: aws-cli/2.x.x Python/3.x.x Windows/...
   ```

**Windows (alternative — winget)**
```powershell
winget install -e --id Amazon.AWSCLI
```

**macOS**
```powershell
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws --version
```

**Linux (x86_64)**
```powershell
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

---

### Create an IAM User for CLI Access

> Do NOT use your AWS root account credentials. Create a dedicated IAM user.

1. Sign in to AWS Console → **IAM** → **Users** → **Create user**
2. Username: `cli-course-deploy` (or any name)
3. Attach policies directly:
   - `AmazonS3FullAccess`
   - `CloudFrontFullAccess`
   - `AWSCertificateManagerFullAccess`
   - `AmazonRoute53FullAccess` (if using Route 53 for DNS)
4. Click **Create user**
5. Open the user → **Security credentials** tab → **Create access key**
6. Select use case: **Command Line Interface (CLI)**
7. Download the `.csv` file — **you can only view the secret key once**

---

### Configure the AWS CLI

```powershell
aws configure
```

You will be prompted for:

```
AWS Access Key ID [None]:     AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]:   us-east-1
Default output format [None]: json
```

Verify configuration works:
```powershell
aws sts get-caller-identity
# Returns your account ID, user ARN, and user ID
```

---

## Prerequisites

- AWS CLI installed and configured (see Step 0 above)
- AWS account ID handy: `aws sts get-caller-identity --query Account --output text`
- Domain `${DOMAIN}` — access to add DNS records (Route 53 or external registrar)
- Course output files built and present in `d:\work\ai-workspace\tutorials\repo\claude-agent-course-final-adv\output\`

---

## Step 1: Create S3 Bucket

> Bucket name `${SITE_FQDN}` matches the subdomain for clarity.
> Do NOT enable "Static website hosting" — CloudFront handles that.

```powershell
# Create bucket in us-east-1
aws s3api create-bucket --bucket ${SITE_FQDN} --region us-east-1

# Block ALL public access
'{"BlockPublicAcls":true,"IgnorePublicAcls":true,"BlockPublicPolicy":true,"RestrictPublicBuckets":true}' | Out-File block-public.json -Encoding ascii
aws s3api put-public-access-block --bucket ${SITE_FQDN} --public-access-block-configuration file://block-public.json

# Enable versioning
aws s3api put-bucket-versioning --bucket ${SITE_FQDN} --versioning-configuration Status=Enabled

# Verify
aws s3api get-bucket-location --bucket ${SITE_FQDN}
```

---

## Step 2: Upload Course Files

```powershell
# Navigate to the course output directory
cd d:\work\ai-workspace\tutorials\repo\claude-agent-course-final-adv\output

# Upload all HTML files with correct content type and cache headers
aws s3 sync . s3://${SITE_FQDN}/ --exclude "*" --include "*.html" --content-type "text/html; charset=utf-8" --cache-control "max-age=3600"

# Verify upload
aws s3 ls s3://${SITE_FQDN}/
```

**Files that will be uploaded (all files in `output/`):**

*Course landing page:*
- `index.html` (home page — must be at root)

*Track 1 — Foundations:*
- `M00-course-overview-agent-lifecycle.html`
- `M01-llm-mental-model.html`
- `M02-tokens.html`
- `M03-prompts.html`
- `M04-structured-output.html`

*Track 2 — Tool Use & Orchestration:*
- `M05-function-calling.html`
- `M06-multi-tool-orchestration.html`
- `M07-mcp-model-context-protocol.html`
- `M08-conversation-management.html`

*Track 3 — Memory & RAG:*
- `M09-rag-retrieval-augmented-generation.html`
- `M10-advanced-rag-patterns.html`
- `M11-multi-layer-memory.html`

*Track 4 — Agent Architecture:*
- `M12-react-agent-loop.html`
- `M13-planning-task-decomposition.html`
- `M14-multi-agent-systems.html`
- `M15-code-interpreter-sandbox.html`
- `M15B-build-agent-subagent-system.html`

*Track 5 — Safety & Evaluation:*
- `M16-input-guardrails.html`
- `M17-output-guardrails-hitl.html`
- `M18-evaluation-testing.html`

*Track 6 — Observability:*
- `M19-tracing-logging.html`
- `M20-monitoring-continuous-improvement.html`

*Track 7 — Production:*
- `M21-api-design-deployment.html`
- `M22-cost-optimization.html`
- `M22B-deploy-local-cloud.html`

*Track 8 — Capstone Projects:*
- `M23-capstone-project-series.html`
- `CAPSTONE-1-DOMAIN-A.html` through `CAPSTONE-5-DOMAIN-C.html`
- `CAPSTONE-6-data-pipeline-testing.html`

*Track 9 — Certification:*
- `M24-whats-next-agent-frontier.html`
- `M25-claude-code-mastery.html`
- `M26-hooks-sessions-agent-sdk.html`
- `M27-cert-exam-prep.html`

*Appendices:*
- `APPENDIX-A-python-essentials.html`
- `APPENDIX-B-fastapi-essentials.html`
- `APPENDIX-C-pyspark-essentials.html`

---

## Step 3: Request ACM SSL Certificate

> **Critical**: ACM certificates for CloudFront MUST be requested in **us-east-1** — CloudFront only reads certs from that region, regardless of where your bucket is.

### Check if You Already Have a Certificate

```powershell
# List all certificates in us-east-1
aws acm list-certificates --region us-east-1 --query "CertificateSummaryList[*].{Domain:DomainName,ARN:CertificateArn,Status:Status}" --output table
```

**Current state (as of setup):**
| Domain | ARN | Status |
|--------|-----|--------|
| `*.${DOMAIN}` | `arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/83015deb-95d2-4fb8-943f-386dcb1eff5c` | **EXPIRED** |
| `${DOMAIN}` | `arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/bfafc7e3-fd0e-4ab7-b772-a3e1ad698869` | ISSUED (SANs: shanaya, blog, www, images, pro, videos, tech — does NOT cover `agenticai.`) |
| `*.${DOMAIN}` | `arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/4d1347ab-1eff-4c85-8838-58bd4a96c500` | Check status — may be valid |

→ If the wildcard cert `4d1347ab-...` is `ISSUED`, **reuse it** (skip to Step 4). A valid `*.${DOMAIN}` cert covers `${SITE_FQDN}`.

→ If no valid wildcard exists, request a new one:

### Request a New Wildcard Certificate

```powershell
aws acm request-certificate --domain-name "*.${DOMAIN}" --subject-alternative-names "${DOMAIN}" --validation-method DNS --region us-east-1
```

**Note the `CertificateArn` from the output** — you'll use it in the next steps and in Step 5.

### Validate the Certificate via Route 53 (DNS Validation)

```powershell
# Step 1: Get the CNAME name and value to add (replace YOUR_NEW_CERT_ID)
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/YOUR_NEW_CERT_ID --region us-east-1 --query "Certificate.DomainValidationOptions[0].{Name:ResourceRecord.Name,Value:ResourceRecord.Value}"
```

Output looks like:
```json
{ "Name": "_abc123def.${DOMAIN}.", "Value": "_xyz789abc.acm-validations.aws." }
```

```powershell
# Step 2: Get your Route 53 hosted zone ID
aws route53 list-hosted-zones --query "HostedZones[?Name=='${DOMAIN}.'].{Id:Id,Name:Name}" --output table
# Use the ID portion only — strip "/hostedzone/" prefix (e.g., Z1ABC123XYZ)

# Step 3: Create the validation DNS record
@'
{"Comment":"ACM cert validation for *.${DOMAIN}","Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"CNAME_NAME","Type":"CNAME","TTL":300,"ResourceRecords":[{"Value":"CNAME_VALUE"}]}}]}
'@ | Out-File acm-validation.json -Encoding ascii

# Edit to fill in CNAME_NAME and CNAME_VALUE from Step 1 output
notepad acm-validation.json

aws route53 change-resource-record-sets --hosted-zone-id YOUR_ZONE_ID --change-batch file://acm-validation.json
```

**Check certificate status** (wait for `"ISSUED"` — typically 5–30 minutes):
```powershell
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/YOUR_NEW_CERT_ID --region us-east-1 --query "Certificate.Status"
```

---

## Step 4: Create CloudFront Origin Access Control (OAC)

OAC is the modern replacement for OAI — it signs S3 requests with SigV4 so only your CloudFront distribution can read the bucket.

```powershell
'{"Name":"${OAC_NAME}","Description":"OAC for ${SITE_FQDN} S3 bucket","SigningProtocol":"sigv4","SigningBehavior":"always","OriginAccessControlOriginType":"s3"}' | Out-File oac-config.json -Encoding ascii
aws cloudfront create-origin-access-control --origin-access-control-config file://oac-config.json
```

**Note the `Id` from the output** — looks like `E1ABCDEFGHIJKL`. You need this in Step 5.

> **Skip this step** if you already have an OAC from a previous distribution. You can reuse an existing OAC ID.

---

## Step 5: Create CloudFront Distribution

Save the following as `cloudfront-config-agenticai.json` in your working directory. Replace all `YOUR_*` placeholders.

```json
{
  "CallerReference": "agenticai-varasrinivas-course-2026",
  "Aliases": {
    "Quantity": 1,
    "Items": ["${SITE_FQDN}"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${SITE_FQDN}",
        "DomainName": "${SITE_FQDN}.s3.us-east-1.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        },
        "OriginAccessControlId": "E24MP9F5KBMU9D"
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${SITE_FQDN}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "Compress": true,
    "FunctionAssociations": {
      "Quantity": 0
    }
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 10
      }
    ]
  },
  "Comment": "${SITE_FQDN} Claude Agent Course hosting",
  "Enabled": true,
  "HttpVersion": "http2and3",
  "IsIPV6Enabled": true,
  "PriceClass": "PriceClass_100",
  "ViewerCertificate": {
    "ACMCertificateArn": "arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/4d1347ab-1eff-4c85-8838-58bd4a96c500",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
```

> `CachePolicyId` `658327ea-...` is the AWS-managed **CachingOptimized** policy — correct for static files.

```powershell
aws cloudfront create-distribution --distribution-config file://cloudfront-config-agenticai.json
```

From the output, record:
- **`DomainName`** — looks like `d1a2b3c4xyz.cloudfront.net` (used in DNS step)
- **`Id`** — the distribution ID (used in bucket policy and cache invalidations)

CloudFront deployment takes 5–15 minutes. Poll status:
```powershell
aws cloudfront get-distribution --id ${CLOUDFRONT_DISTRIBUTION_ID} --query "Distribution.Status"
# "InProgress" → still deploying; "Deployed" → ready
```

---

## Step 6: Update S3 Bucket Policy (Allow CloudFront OAC)

Replace `YOUR_DISTRIBUTION_ID` with the actual value from Step 5.

```powershell
# Create the policy file (edit placeholders first)
@'
{"Version":"2012-10-17","Statement":[{"Sid":"AllowCloudFrontOAC","Effect":"Allow","Principal":{"Service":"cloudfront.amazonaws.com"},"Action":"s3:GetObject","Resource":"arn:aws:s3:::${SITE_FQDN}/*","Condition":{"StringEquals":{"AWS:SourceArn":"arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${CLOUDFRONT_DISTRIBUTION_ID}"}}}]}
'@ | Out-File bucket-policy-agenticai.json -Encoding ascii

# Edit the file to replace YOUR_DISTRIBUTION_ID, then apply
notepad bucket-policy-agenticai.json

aws s3api put-bucket-policy --bucket ${SITE_FQDN} --policy file://bucket-policy-agenticai.json
```

Verify the policy was applied:
```powershell
aws s3api get-bucket-policy --bucket ${SITE_FQDN}
```

---

## Step 7: Configure DNS (Point ${SITE_FQDN} → CloudFront)

Since this is a **subdomain** (not the root domain), you add a single **CNAME** record.

### Option A: Route 53 (if ${DOMAIN} is hosted in Route 53)

```powershell
# Get your hosted zone ID
aws route53 list-hosted-zones --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text

# Create DNS change file — replace d1a2b3c4xyz with your actual CloudFront domain
@'
{"Comment":"Point agenticai subdomain to CloudFront","Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"${SITE_FQDN}","Type":"CNAME","TTL":300,"ResourceRecords":[{"Value":"d1a2b3c4xyz.cloudfront.net"}]}}]}
'@ | Out-File dns-change-agenticai.json -Encoding ascii

# Edit to replace d1a2b3c4xyz, then apply
notepad dns-change-agenticai.json

aws route53 change-resource-record-sets --hosted-zone-id Z2PNVSMNCULG7G --change-batch file://dns-change-agenticai.json

# Verify
aws route53 list-resource-record-sets --hosted-zone-id Z2PNVSMNCULG7G --query "ResourceRecordSets[?Name=='${SITE_FQDN}.']"
```

### Option B: External DNS Registrar (GoDaddy, Namecheap, Cloudflare, etc.)

Log in to your registrar's DNS management panel and add:

| Type  | Host / Name | Value / Points to               | TTL  |
|-------|-------------|---------------------------------|------|
| CNAME | agenticai   | d1a2b3c4xyz.cloudfront.net      | 3600 |

- **GoDaddy**: DNS → Add Record → Type: CNAME, Name: `agenticai`, Value: `d1a2b3c4xyz.cloudfront.net`
- **Namecheap**: Advanced DNS → Add New Record → CNAME, Host: `agenticai`, Value: `d1a2b3c4xyz.cloudfront.net`
- **Cloudflare**: DNS → Add record → CNAME, Name: `agenticai`, Target: `d1a2b3c4xyz.cloudfront.net`, Proxy status: **DNS only** (grey cloud — do NOT proxy through Cloudflare)

DNS propagation typically takes 5–30 minutes. Check with:
```powershell
nslookup ${SITE_FQDN}
```

---

## Step 8: Verify the Deployment

```powershell
# Test HTTPS response
curl.exe -I https://${SITE_FQDN}

# Expected response headers:
# HTTP/2 200
# content-type: text/html; charset=utf-8
# x-cache: Miss from cloudfront   (first request)
# x-cache: Hit from cloudfront    (subsequent requests)
# server: AmazonS3
```

Open in browser and verify key pages load:
- `https://${SITE_FQDN}` → course landing page (index.html)
- `https://${SITE_FQDN}/M00-course-overview-agent-lifecycle.html` → gateway module
- `https://${SITE_FQDN}/M01-llm-mental-model.html` → Module 1
- `https://${SITE_FQDN}/M15B-build-agent-subagent-system.html` → Build lab
- `https://${SITE_FQDN}/CAPSTONE-1-DOMAIN-A.html` → Capstone 1

---

## Step 9: No Link Changes Needed

All course files use relative paths (e.g., `href="M01-llm-mental-model.html"`). These work correctly on S3/CloudFront as-is — no changes to the HTML files are required.

---

## Ongoing: Deploy Updates

When you generate or update module files:

```powershell
# From the course output directory
cd d:\work\ai-workspace\tutorials\repo\claude-agent-course-final-adv\output

# Sync all updated HTML files to S3
aws s3 sync . s3://${SITE_FQDN}/ --exclude "*" --include "*.html" --content-type "text/html; charset=utf-8" --cache-control "max-age=3600"

# Invalidate CloudFront cache so visitors see updates immediately
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

> The first 1,000 invalidation paths per month are free. `/*` counts as one path.

### Deploy a Single Updated Module (faster)

```powershell
# Upload just one file
aws s3 cp M12-react-agent-loop.html s3://${SITE_FQDN}/M12-react-agent-loop.html --content-type "text/html; charset=utf-8" --cache-control "max-age=3600"

# Invalidate only that file's cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/M12-react-agent-loop.html"
```

---

## Cost Estimate (monthly, low traffic)

| Service         | Usage                                      | Est. Cost       |
|-----------------|--------------------------------------------|-----------------|
| S3 storage      | ~50 HTML files (~5–10 MB total)            | ~$0.00          |
| S3 GET requests | Served via CloudFront (few direct hits)    | ~$0.01          |
| CloudFront      | First 1 TB transfer free tier              | ~$0.00–$1       |
| ACM Certificate | Free with CloudFront (reuse wildcard)      | $0.00           |
| Route 53        | $0.50/hosted zone/month                    | $0.50 (if used) |
| **Total**       |                                            | **~$0.50–$2/month** |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 403 Forbidden | Bucket policy missing or wrong distribution ID | Re-check Step 6; make sure `YOUR_DISTRIBUTION_ID` in the policy matches the actual distribution ID |
| SSL cert error in browser | Certificate not `ISSUED` yet, or in wrong region | Wait for `ISSUED` status; verify cert is in us-east-1 |
| Old content showing | CloudFront cache not invalidated | Run `create-invalidation --paths "/*"` (see Ongoing: Deploy Updates) |
| `index.html` not loading on root | `DefaultRootObject` not set in distribution | In CloudFront console → Distribution → Edit → Default root object: `index.html` |
| DNS not resolving | Propagation delay or wrong CNAME value | Wait 30 min; verify CNAME points to `*.cloudfront.net` domain |
| Certificate pending validation | DNS validation CNAME not added | Add the ACM-provided CNAME to your DNS provider (Step 3) |
| Cloudflare orange-cloud issue | Cloudflare proxying conflicts with CloudFront | Set Cloudflare DNS record to "DNS only" (grey cloud) |
| Module page 404 | File not uploaded or wrong filename | Run `aws s3 ls s3://${SITE_FQDN}/` and verify filename matches exactly |

---

## Quick Reference: Record These After Setup

```
S3 Bucket Name:         ${SITE_FQDN}
S3 Region:              us-east-1
Source Directory:       d:\work\ai-workspace\tutorials\repo\claude-agent-course-final-adv\output\
Target URL:             https://${SITE_FQDN}

ACM Certificate ARN:    arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/YOUR_CERT_ID
OAC ID:                 E_______________________
CloudFront Dist ID:     E_______________________
CloudFront Domain:      _________________.cloudfront.net
Route 53 Hosted Zone:   Z_______________________  (if applicable)
```
