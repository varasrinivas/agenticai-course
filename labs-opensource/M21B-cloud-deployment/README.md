# M21B Lab: Cloud Deployment — Local to Cloud Without Code Changes

> The payoff of the OpenAI-compatible pattern: moving from your laptop to a GPU VM or a managed provider changes **a base_url and a model name — nothing else**. You'll build the provider factory that makes the switch a single environment variable.

## Prerequisites

- M21 complete
- Optional (for the cloud paths): a GCP/AWS account with GPU quota, or a free [Groq](https://console.groq.com) API key — **the Groq path is free and takes 2 minutes; start there**

## Files

| File | Status | What It Is |
|------|--------|------------|
| `local_model_client.py` | **TODOs** | `LocalModelClient.create()` — the provider factory |
| `verify_connection.py` / `.js` | Complete | Smoke test for any endpoint (local, tunneled VM, managed) |

## Part 1: The Provider Factory

`LocalModelClient.create(provider=None)` returns `(client, config)`:
- Provider from the arg, else `LOCAL_MODEL_PROVIDER` env var, else `"ollama"`
- Unknown name → `ValueError` listing supported providers
- `ollama` → `OLLAMA_BASE_URL` env (default `http://localhost:11434/v1`), key `"ollama"`
- `groq` / `together` / `fireworks` → their base URLs + API key from env; **missing key → `EnvironmentError` naming the exact variable** (the most common deploy failure is a missing env var; make the error message do the debugging)
- The returned `ProviderConfig` carries `default_model` and `max_context_tokens` — model names are provider-specific, so callers use `cfg.default_model`, never hardcode

Test the switch:
```bash
python local_model_client.py                              # local Ollama
LOCAL_MODEL_PROVIDER=groq GROQ_API_KEY=gsk_... python local_model_client.py   # Groq cloud
```
Same code, same question, different datacenter.

## Part 2: The Cloud VM Path (guided, optional — costs money)

The course HTML has the full walkthroughs; the short version:

**GCP** (~$0.40/hr for n1-standard-4 + T4):
```bash
gcloud compute instances create ollama-server --zone=us-central1-a \
  --machine-type=n1-standard-4 --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --maintenance-policy=TERMINATE
# SSH in: install NVIDIA drivers + Ollama, ollama pull mistral,
# run Ollama as a systemd service
```

**The key move — SSH tunnel instead of opening port 11434 to the internet:**
```bash
gcloud compute ssh ollama-server --zone=us-central1-a -- -L 11434:localhost:11434 -N -f
python verify_connection.py     # hits localhost:11434 → actually the cloud VM
```
Your agents don't change AT ALL: `localhost:11434` now lands on a datacenter GPU. **Never expose the Ollama port publicly** — it has no authentication.

**Shut the VM down when done** (`gcloud compute instances stop ollama-server`) — a forgotten T4 VM is ~$290/month.

## Verify

```bash
python verify_connection.py                      # whichever endpoint OLLAMA_BASE_URL points at
node verify_connection.js
```

## Stretch Goals

- Add a `bedrock` provider via the bedrock-access-gateway (course HTML has the config)
- Port the cost estimator from the course HTML: tokens/day × provider price vs VM hourly rate — find your break-even volume
- Point the M21 FastAPI service at Groq via the factory: one env var, zero code changes, ~50× faster inference
