# UM-Lite

A clean-room learning rebuild of a healthcare **Utilization Management** platform, used to
learn the full stack end to end: **Angular micro-frontends · Spring Boot · NestJS · Kafka ·
Camunda (BPM + DMN) · Postgres · Kubernetes / Azure** — with AI in the loop throughout.

You build **one vertical slice** (Prior Authorization) that pierces every layer, then widen and
deepen it. Every phase produces something runnable.

---

## Quickstart

Prerequisites: Docker, Node 20+, JDK 21, and Maven (the Spring app ships a Maven wrapper).

```bash
# 1. Start local infrastructure (Postgres, Kafka/Redpanda, Redis, Camunda)
docker compose up -d
docker compose ps                 # wait for healthy

# 2. Run the Spring Boot case service  ->  http://localhost:8081
cd apps/um-case-svc
./mvnw spring-boot:run

# 3. Run the NestJS intake service     ->  http://localhost:3000
cd apps/um-intake-svc
npm install
npm run start

# 4. Run the Angular intake UI         ->  http://localhost:4200
cd apps/intake-ui
npm install
npm start
```

Useful local URLs:

| URL                              | What                                  |
|----------------------------------|---------------------------------------|
| http://localhost:4200            | Intake UI (submit a PA)               |
| http://localhost:3000/health     | NestJS intake service health          |
| http://localhost:8081/actuator/health | Spring case service health       |
| http://localhost:8085            | Redpanda Console (watch Kafka topics) |
| http://localhost:8088/camunda    | Camunda cockpit (demo / demo)         |

### Smoke test the slice

```bash
curl -X POST http://localhost:3000/prior-auth \
  -H 'content-type: application/json' \
  -d '{
        "memberId": "M1001",
        "providerId": "P2002",
        "procedureCode": "27447",
        "diagnosisCode": "M17.11",
        "requestedUnits": 1
      }'
```

The intake service validates the request and forwards it to the case service, which creates a
case in Postgres and returns a case id + status. Fetch it back:

```bash
curl http://localhost:8081/api/cases/<caseId>
```

### Run it event-driven (Phase 2, optional)

By default the slice runs over REST. To run it over Kafka instead — intake publishes `pa.submitted`,
the case service consumes it and publishes `pa.decisioned`:

```bash
docker compose up -d        # Redpanda is part of local infra
make topics                 # create pa.submitted / pa.decisioned / pa.dead-letter
make case-events            # case service, EVENTS_ENABLED=true (Kafka consumer on)
make intake-events          # intake service, EVENTS_ENABLED=true (publishes instead of REST)
make smoke                  # submit a PA → returns a caseId immediately
make watch-decisioned       # see the auto-decision land on pa.decisioned
```

Watch the messages flow in the Redpanda Console at http://localhost:8085. With `EVENTS_ENABLED` unset
(the default) everything runs over REST exactly as above.

---

## Repository layout

```
apps/
  um-intake-svc/    NestJS  — intake endpoint, validation, forwards to case service
  um-case-svc/      Spring  — owns the Prior Auth case, persists to Postgres (Flyway)
  intake-ui/        Angular — minimal standalone form to submit a PA and view status
libs/
  domain/           shared TypeScript domain types
  events/           shared Kafka topic names + event payload contracts (Phase 2 seed)
infra/
  db/init.sql       creates per-service Postgres databases
docker-compose.yml  local infrastructure
CLAUDE.md           context for AI-assisted development — read this
```

The TypeScript apps and libs are set up as an **Nx** workspace (`npm install` at the root wires
it). The Spring Boot service is a sibling Maven module in the same monorepo — build it with the
Maven wrapper. Each app is independently runnable; Nx is the orchestration convenience layer.

---

## The 12-week plan

| Phase | Weeks | Build                                                              | Learn |
|------:|------:|-------------------------------------------------------------------|-------|
| 0 | 1     | Monorepo + docker-compose + CLAUDE.md (**this scaffold**)          | workspace, local infra, AI setup |
| 1 | 2–3   | PA slice over REST: Intake (Nest) → Case (Spring) → Postgres → UI  | TS/Nest, Spring/JPA, Angular basics |
| 2 | 4–5   | Make it event-driven with Kafka; dead-letter handling             | topics, consumer groups, schemas, idempotency |
| 3 | 6–7   | Camunda BPMN process + DMN decision tables; external task workers | BPMN, DMN, workflow orchestration |
| 4 | 8–9   | Single-SPA shell + micro-frontends + shared UI library            | micro-frontends, Angular signals/RxJS, design system |
| 5 | 10    | GraphQL data-as-a-service, Redis cache, search, read replica, OIDC| cross-cutting services, auth |
| 6 | 11–12 | Containerize, Helm, deploy to AKS; ingress, Kong, observability    | Kubernetes, AKS, Helm, monitoring |

Throughout: drive each service from a contract (OpenAPI), use AI to scaffold/test/review, and
track progress on DORA/SPACE rather than lines of code.

---

## Notes

- The Angular app here is an intentionally minimal skeleton — real UI/design work is Phase 4.
- Camunda runs on its embedded DB for now; it moves onto Postgres in Phase 3.
- Nothing in this repo depends on any proprietary system; the value is in the patterns.
