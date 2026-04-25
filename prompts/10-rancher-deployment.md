# Rancher Desktop Deployment Guide

This guide provides Rancher Desktop-specific instructions as an alternative to Docker Desktop for all deployment steps in M22B and CAPSTONE-6. Students who prefer Rancher Desktop (free, open-source) or whose organizations restrict Docker Desktop (paid license for enterprises) can follow this guide.

## Why Rancher Desktop?

Docker Desktop requires a paid subscription for companies with 250+ employees or $10M+ revenue. Rancher Desktop is 100% free, open-source, and provides the same container runtime capabilities.

| Feature | Docker Desktop | Rancher Desktop |
|---|---|---|
| License | Free for personal/small business, paid for enterprise | Free for everyone |
| Container runtime | Docker Engine (containerd) | containerd or dockerd (your choice) |
| Kubernetes | Optional, single-node | Built-in K3s (lightweight Kubernetes) |
| CLI | `docker` | `nerdctl` (containerd) or `docker` (dockerd) |
| Compose | `docker compose` | `nerdctl compose` or `docker compose` |
| Image build | `docker build` | `nerdctl build` or `docker build` |
| Platform | Windows, Mac, Linux | Windows, Mac, Linux |

## Setup

### Step 1: Install Rancher Desktop

**Windows:**
Download from https://rancherdesktop.io/ → run installer → restart.

**Mac:**
```bash
brew install --cask rancher
```

**Linux:**
```bash
curl -s https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/Release.key | sudo gpg --dearmor -o /usr/share/keyrings/rancher-desktop.gpg
echo 'deb [signed-by=/usr/share/keyrings/rancher-desktop.gpg] https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/ /' | sudo tee /etc/apt/sources.list.d/rancher-desktop.list
sudo apt update && sudo apt install rancher-desktop
```

### Step 2: Choose your container runtime

When Rancher Desktop starts, it asks you to pick a runtime:

**Option A: dockerd (Docker compatible)** — RECOMMENDED for this course
- All `docker` commands work as-is
- `docker compose` works as-is
- No changes needed to any course commands
- Select this if you want zero friction

**Option B: containerd (nerdctl)** — lighter weight
- Use `nerdctl` instead of `docker`
- Use `nerdctl compose` instead of `docker compose`
- See the command mapping table below

### Step 3: Verify installation

```bash
# If you chose dockerd:
docker --version
docker compose version

# If you chose containerd:
nerdctl --version
nerdctl compose version
```

Expected: version numbers print without errors.

---

## Command Mapping (containerd/nerdctl users only)

If you chose **dockerd**, skip this section — all course commands work as written.

If you chose **containerd**, replace `docker` with `nerdctl` in every command:

| Course Command (Docker) | Rancher Desktop (nerdctl) |
|---|---|
| `docker build -t ucc-agent .` | `nerdctl build -t ucc-agent .` |
| `docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY ucc-agent` | `nerdctl run -p 8000:8000 -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY ucc-agent` |
| `docker compose up -d` | `nerdctl compose up -d` |
| `docker compose down` | `nerdctl compose down` |
| `docker compose logs -f` | `nerdctl compose logs -f` |
| `docker ps` | `nerdctl ps` |
| `docker logs <id>` | `nerdctl logs <id>` |
| `docker stop <id>` | `nerdctl stop <id>` |
| `docker images` | `nerdctl images` |
| `docker tag ucc-agent registry/ucc-agent:v1` | `nerdctl tag ucc-agent registry/ucc-agent:v1` |
| `docker push registry/ucc-agent:v1` | `nerdctl push registry/ucc-agent:v1` |

---

## Module-Specific Changes

### M22B: Deploy Agent — Local Docker (Tier 1)

**No changes needed if you chose dockerd.**

If using nerdctl, replace all `docker` commands in Steps 4-6:

**Step 4: Build the container**
```bash
# Docker Desktop:
docker build -t ucc-agent .

# Rancher Desktop (nerdctl):
nerdctl build -t ucc-agent .
```

**Step 5: Run the container**
```bash
# Docker Desktop:
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ucc-agent

# Rancher Desktop (nerdctl):
nerdctl run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ucc-agent
```

**Step 6: Docker Compose**
```bash
# Docker Desktop:
docker compose up -d

# Rancher Desktop (nerdctl):
nerdctl compose up -d
```

The Dockerfile itself is IDENTICAL — no changes needed. Both Docker Desktop and Rancher Desktop use the same Dockerfile format.

### M22B: Deploy Agent — GCP Cloud Run (Tier 2)

**Change: Push to Artifact Registry**

With Docker Desktop:
```bash
gcloud auth configure-docker us-docker.pkg.dev
docker tag ucc-agent us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1
docker push us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1
```

With Rancher Desktop (nerdctl):
```bash
# nerdctl needs explicit login for GCR/Artifact Registry
nerdctl login us-docker.pkg.dev -u _json_key --password-stdin < key.json
nerdctl tag ucc-agent us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1
nerdctl push us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1
```

Alternative: Use `gcloud builds submit` to build in the cloud (skips local push entirely):
```bash
gcloud builds submit --tag us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1
```
This works regardless of which local container runtime you use.

### M22B: Deploy Agent — AWS Lambda (Tier 3)

**No changes.** AWS SAM builds containers using its own Docker-compatible builder. If Rancher Desktop is running with dockerd, SAM works as-is. With containerd, set the environment variable:
```bash
# Tell SAM to use nerdctl
export SAM_CLI_CONTAINER_CONNECTION_TIMEOUT=30
```

### CAPSTONE-6: Bronze Testing — Local Production (Tier 1)

**docker-compose.yml works identically** with both Docker Desktop and Rancher Desktop (dockerd mode).

For nerdctl users, the compose file is the same — just use `nerdctl compose`:
```bash
# Docker Desktop:
docker compose up -d

# Rancher Desktop (nerdctl):
nerdctl compose up -d
```

All three containers (test-agent, file-watcher, dashboard) start the same way.

---

## Rancher Desktop Bonus: Built-in Kubernetes

Rancher Desktop includes K3s (lightweight Kubernetes). For students who want to try Kubernetes deployment instead of Docker Compose:

### Deploy the agent to local Kubernetes (optional advanced exercise)

**Step 1: Create a Kubernetes deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ucc-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ucc-agent
  template:
    metadata:
      labels:
        app: ucc-agent
    spec:
      containers:
      - name: ucc-agent
        image: ucc-agent:latest
        imagePullPolicy: Never  # Use local image
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: anthropic-api-key
        - name: DEPLOYMENT_TIER
          value: "local"
        - name: DB_PATH
          value: "/data/bronze.duckdb"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: agent-data
---
apiVersion: v1
kind: Service
metadata:
  name: ucc-agent
spec:
  type: NodePort
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30080
  selector:
    app: ucc-agent
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**Step 2: Create the secret**
```bash
kubectl create secret generic agent-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY
```

**Step 3: Deploy**
```bash
# Build the image so K3s can find it
nerdctl build -t ucc-agent:latest .

# Apply the deployment
kubectl apply -f k8s/deployment.yaml

# Verify
kubectl get pods
kubectl get svc
```

**Step 4: Test**
```bash
curl http://localhost:30080/health
curl -X POST http://localhost:30080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Find filings for Acme Corporation"}'
```

This gives students exposure to Kubernetes deployment without needing a cloud cluster — Rancher Desktop's built-in K3s handles everything locally.

---

## Troubleshooting

### "nerdctl: command not found"
Rancher Desktop may not add nerdctl to PATH automatically on Windows. Fix:
```powershell
# Add to PATH (Windows)
$env:PATH += ";$env:LOCALAPPDATA\Programs\Rancher Desktop\resources\resources\win32\bin"
```

### "Cannot connect to the Docker daemon"
Rancher Desktop needs to be running. Start it from the Start menu / Applications.

### "Port already in use"
Another container or process is using port 8000. Either stop it or change the port:
```bash
nerdctl run -p 8001:8000 ucc-agent
# Then test with: curl http://localhost:8001/health
```

### "Image not found" when deploying to K3s
K3s uses containerd images, not Docker images. Build with nerdctl (not docker) or import:
```bash
docker save ucc-agent:latest | nerdctl load
```

### Compose file version warning
If you see "version is obsolete", remove the `version: '3.8'` line from docker-compose.yml. Both Docker Compose V2 and nerdctl compose ignore it.

---

## 4-Tier Deployment Comparison (Updated)

| Component | Tier 1A: Docker Desktop | Tier 1B: Rancher Desktop | Tier 1C: Rancher + K8s | Tier 2: GCP | Tier 3: AWS |
|---|---|---|---|---|---|
| Container runtime | Docker Engine | containerd or dockerd | K3s (Kubernetes) | Cloud Run | Lambda |
| CLI | `docker` | `nerdctl` or `docker` | `kubectl` | `gcloud` | `sam` |
| Compose | `docker compose` | `nerdctl compose` | K8s manifests | N/A | N/A |
| License cost | Free/Paid | Free | Free | Pay-per-use | Pay-per-use |
| Kubernetes | Optional | Built-in K3s | Yes | GKE (optional) | EKS (optional) |
| Best for | Most students | Enterprise/no Docker license | K8s learning | Production | Serverless |
| Dockerfile changes | None | None | None | None | None |
