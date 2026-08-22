# Tier 1 — local Docker Compose

The lab. No database, no broker, no cloud account: this agent reads a repository and writes a
repository.

```bash
cd labs/capstone-9-bh-um-modernization
cp solution/.env.example solution/.env      # add your ANTHROPIC_API_KEY
docker compose up --build
```

## What you should see

Six phases, then a denial:

```
=== PHASE 1/6  MAP =====================================
...
=== FINALIZE ===========================================
FINALIZATION REQUIRES HUMAN APPROVAL.

GAP REGISTER: port-as-is 2, extend 3, must-build-new 8, must-not-port 3
  MUST-NOT-PORT  cleartext PHI in logs, events and search
                 harm: ...
QUEUED FOR HUMAN DECISION: 5
```

**The denial is the successful outcome.** The agent does not get to decide that its own work is
ready.

## Approving

Read `artifacts/modernization_report.html` first — that is the point of the gate — then:

```bash
docker compose run --rm agent python coordinator.py --phase finalize --approve
```

Note that this is a *separate command a person types*, not a value in `.env`. See the comment at
the bottom of `.env.example`.

## Running without Docker

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd solution && python coordinator.py --phase all
```

## Checking your work without spending a token

Everything under `tests/` runs offline — `rules_ir`, `gap_register`, `seam_map`, `condition`,
`validation` and `screen_inventory` carry no SDK import by design.

```bash
pytest tests/ -v
python solution/evaluation/test_suite.py --self-check
```

## Two failure modes worth recognising

**The run halts after phase 4 saying the register does not meet acceptance.** Working as
intended. A register that is mostly `port-as-is` means the architecture was read and the domain
was not; the coordinator checks that itself rather than believing the phase's report.

**A parity check comes back clean and is flagged suspicious.** Read what it says it *scanned*. A
check that looked at nothing did not run, and that is not a pass.
