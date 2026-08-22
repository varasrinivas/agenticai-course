# CLAUDE.md — Context for AI-assisted development

This file gives Claude Code (and any other AI dev tool) the context it needs to work in
this repo well. Keep it current — it is the single most valuable lever on AI output quality.

## What this project is

**UM-Lite** is a clean-room learning rebuild of a healthcare **Utilization Management (UM)**
platform. The goal is to learn the full stack — Angular micro-frontends, Spring Boot + NestJS,
Kafka, Camunda (BPM + DMN), Postgres, Kubernetes/Azure — by building one real vertical slice
end to end, then widening it.

This is a teaching codebase. It does **not** use any proprietary implementation. The domain
(Prior Authorization, Concurrent Review, Claims, Appeals) is industry-standard UM; the patterns
(micro-frontends, event-driven services, externalized workflow/rules) are standard architecture.

## The domain (UM journey)

Intake → Basic Validation → **Prior Auth** → Concurrent Review → Discharge Planning →
Post Acute → Care Mgmt → Care@Home → Claims → Appeals.

We are building the **Prior Auth** slice first. A "case" moves: submitted → in review →
decisioned (approved / denied / pended) → letter generated.

## Architecture (target) and where we are

| Layer            | Target tech                                  | Maps to diagram        | Phase |
|------------------|----------------------------------------------|------------------------|-------|
| Micro-frontends  | Angular standalone + Single-SPA + UI library | Root SPA, Intake UI    | 1, 4  |
| API edge         | Kong gateway, NGINX ingress, OIDC auth       | Kong, PingFederate     | 5, 6  |
| Intake/functions | NestJS                                        | UM Intake/EDI Functions| 1, 2  |
| Core services    | Spring Boot                                   | green-leaf services    | 1, 2  |
| Eventing         | Kafka (Redpanda locally)                      | KaaS / EventHub        | 2     |
| Workflow         | Camunda 7 BPMN                                | UM Intake/Case BPM     | 3     |
| Rules            | Camunda 7 DMN                                 | Routing/Guideline DMN  | 3     |
| Data             | Postgres (master + read replica), Redis      | Master Nodes, Redis    | 1, 5  |
| Data-as-service  | GraphQL                                       | "GraphQL Data service" | 5     |
| Infra            | Kubernetes / AKS, Helm, fluentd, App Insights | full Azure deployment  | 6     |

**Current phase: 2 → 3.** `um-intake-svc` (NestJS), `um-case-svc` (Spring Boot), and `intake-ui`
(Angular skeleton) talk over REST. **Phase 2 (Kafka)** is scaffolded (`EVENTS_ENABLED`, see "Eventing"
below). **Phase 3 (Camunda workflow + rules) is now scaffolded too**: a BPMN Prior Auth process + a DMN
decision table in `camunda/`, with the case service acting as an external-task worker
(`WORKFLOW_ENABLED`, default off). See "Workflow & rules (Phase 3)" below.

## Repo layout

```
apps/
  um-intake-svc/   NestJS   — accepts PA requests, forwards to case service
  um-case-svc/     Spring   — owns the PA case, persists to Postgres
  intake-ui/       Angular  — minimal form to submit a PA and see status
libs/
  domain/          shared TS domain types (PriorAuthRequest, CaseStatus, ...)
  events/          shared Kafka topic names + event payload contracts (Phase 2 seed)
infra/
  db/init.sql      per-service Postgres databases
docker-compose.yml local infra (Postgres, Redpanda+Console, Redis, Camunda)
```

## Conventions

- **Language:** TypeScript (strict) for Node/Angular; Java 21 for Spring.
- **NestJS:** controllers thin, logic in services, DTOs validated with `class-validator`.
- **Spring:** constructor injection, DTO ≠ entity, Flyway for schema, no field injection.
- **Shared contracts live in `libs/`** — never duplicate domain/event types across apps.
- **Event names** are past-tense facts: `pa.submitted`, `pa.decisioned` (see `libs/events`).
- **IDs:** UUID. **Money/dates:** never floats; ISO-8601 strings across the wire.
- **Tests:** Jest for TS, JUnit + Testcontainers for Spring integration tests.

## How to run (see README for detail)

```
docker compose up -d                          # infra
cd apps/um-case-svc && ./mvnw spring-boot:run  # :8081
cd apps/um-intake-svc && npm i && npm run start # :3000
cd apps/intake-ui && npm i && npm start         # :4200
```

## Eventing (Phase 2)

The event-driven path is **opt-in** via `EVENTS_ENABLED=true` (set on both services). With it off, the
slice runs over REST exactly as before.

- **Contracts:** `libs/events` (`@um-lite/events`) is the source of truth — `Topics`
  (`pa.submitted`, `pa.decisioned`, `pa.dead-letter`), the `EventEnvelope<T>` (with `correlationId =
  caseId`), and the payloads. The Java side mirrors these in `um-case-svc/.../events/` (Java can't
  import the TS lib); the intake app mirrors them in `src/app/events/pa-events.ts` (kept inline so the
  service stays runnable, same pattern as the DTO). Keep the three copies in sync.
- **Producer (intake, NestJS):** `KafkaProducerService` (kafkajs). `PriorAuthService.submit()`
  generates a `caseId`, publishes `pa.submitted` keyed by `caseId`, and returns immediately.
- **Consumer (case, Spring):** `PaSubmittedConsumer` (`@KafkaListener`, group `um-case-svc`,
  `autoStartup=${um.events.enabled}`) persists the case with the upstream `caseId` (idempotent —
  at-least-once safe), then `PaEventsProducer` publishes `pa.decisioned` (auto-approval stub; real
  rules are Track 3 / Camunda DMN).
- **Partition key is the `caseId`** so a case's events stay ordered. Broker = `KAFKA_BROKERS`
  (Redpanda locally). Create topics with `make topics`; run the slice with `make case-events` +
  `make intake-events`; watch decisions with `make watch-decisioned`.
- **Idempotency:** the consumer skips a `caseId` it has already persisted (at-least-once safe).
- **Transactional outbox (`OUTBOX_ENABLED=true`, M14):** with it on, the consumer writes
  `pa.decisioned` to the `outbox_event` table in the same DB tx as the case change, and
  `OutboxPublisher` (a `@Scheduled` poller) sends outbox rows to Kafka and stamps `published_at` —
  no dual-write. With it off, the consumer publishes directly (M12). Run via `make case-outbox`.

## Workflow & rules (Phase 3)

Opt-in via `WORKFLOW_ENABLED=true` (case service) + Camunda from docker-compose (`:8088`, demo/demo).

- **Process & rules as files:** `camunda/prior-auth.bpmn` (Start → DMN business-rule task → Pended?
  gateway → optional Manual review user task → external "notify-decision" service task → End) and
  `camunda/pa-decision.dmn` (a decision table: requestedUnits > 10 → PENDED, 27447 → APPROVED, else
  APPROVED). Deploy with `make deploy-bpmn`; start an instance with `make start-pa`.
- **Worker, not engine:** the engine is the standalone Camunda container; the case service is an
  **external-task worker** — `workflow/NotifyDecisionWorker` (`@ExternalTaskSubscription("notify-decision")`,
  gated by `um.workflow.enabled`) fetches-and-locks the task, publishes `pa.decisioned`, completes it.
  Client base URL = `camunda.bpm.client.base-url` (`CAMUNDA_BASE_URL`). Run with `make case-workflow`.
- **Orchestration vs choreography:** Phase 3 (Camunda) orchestrates the steps centrally; Phase 2
  (Kafka events) choreographs them. Both real in the repo, toggled by flags — that contrast is M18.

## Frontend at scale (Phase 4)

The `intake-ui` is a single Angular 18 **standalone** app using the esbuild `application` builder
(signals, `inject()`, `@for`). Phase 4 widens it:

- **Shared UI library `@um-lite/ui` (`libs/ui`, scaffolded):** reusable standalone components —
  `TaskListComponent`, `CaseSearchComponent`, `CaseCreateComponent` — plus design tokens
  (`libs/ui/src/styles/tokens.css`). Components reference tokens (`var(--um-...)`), have visible focus
  rings, and honor reduced motion. Path `@um-lite/ui` in `tsconfig.base.json`.
- **Micro-frontends:** the target is **Native Federation** (`@angular-architects/native-federation`),
  which fits the esbuild builder (classic Single-SPA/webpack Module Federation does not). A root shell
  app loads each MFE from a federation manifest. This wiring is taught in M20/M21 as the target pattern;
  it is **not yet stood up** in the repo (only the shared lib + tokens are scaffolded so far) — build it
  in the lab. The README already flags "real UI/design work is Phase 4."

## Data & cross-cutting (Phase 5)

Read-side + cross-cutting services, all gated so the case service still runs standalone:

- **GraphQL data-as-a-service (M24, real):** `spring-boot-starter-graphql` + `resources/graphql/schema.graphqls`
  (Query: `cases`, `case(id)`, `casesByMember`) + `query/CaseGraphQlController` over `CaseQueryService`.
  Served at `/graphql`, explorer at `/graphiql`.
- **Redis cache-aside (M25, real):** `CaseQueryService.getById` is `@Cacheable("case")`; `config/CacheConfig`
  enables caching only when `CACHE_ENABLED=true` (Redis from docker-compose). Off ⇒ `@Cacheable` is a no-op.
- **OIDC resource server (M28, real):** `config/SecurityConfig` — secured chain (validate Keycloak JWTs,
  `issuer-uri`) when `SECURITY_ENABLED=true`, else an open chain. Keycloak added to docker-compose (`:8087`,
  admin/admin; create the `um-lite` realm in the lab).
- **Search (M26, real):** `spring-boot-starter-data-elasticsearch` + `search/CaseDocument` (`@Document`),
  `CaseSearchRepository` (`ElasticsearchRepository`, gated `spring.data.elasticsearch.repositories.enabled`),
  `CaseSearchService` (reindex/index/search, `@ConditionalOnProperty SEARCH_ENABLED`). Elasticsearch added to
  docker-compose (`:9200`, security off). Off by default.
- **Read replicas (M27, real):** `config/RoutingDataSourceConfig` — an `AbstractRoutingDataSource` sending
  read-only transactions to the replica, writes to the primary, gated `REPLICA_ENABLED` (`um.replica.url`).
  A second Postgres (`postgres-replica`, `:5433`) added to docker-compose (stand-in read node; true streaming
  replication is the lab extension). Off by default → normal single-DataSource auto-config.
- **API gateway/ingress (M29, real-config):** Kong (DB-less) added to docker-compose (`:8000` proxy / `:8001`
  admin) reading `infra/kong/kong.yml` (routes + rate-limit + correlation-id). `infra/k8s/ingress.yaml` is the
  NGINX-ingress target pattern for AKS (Track 6). Kong is runnable locally; the k8s Ingress needs a cluster.

## Platform & delivery (Phase 6)

Real config artifacts (not deployed this session — no cluster/registry/Azure here; build/deploy in the lab):

- **Containers (M30):** multi-stage `Dockerfile` in each app (`um-case-svc` = Maven→JRE, `um-intake-svc`
  = node build→node, `intake-ui` = ng build→nginx, with `nginx.conf` SPA fallback). Non-root, small runtime.
- **Kubernetes (M31):** `infra/k8s/um-case-svc.yaml` — ConfigMap + Secret + Deployment (probes, resources)
  + Service + HPA. The other services follow the same shape.
- **Helm (M32):** `infra/helm/um-case-svc/` — `Chart.yaml`, `values.yaml`, `templates/deployment.yaml`
  (templated Deployment+Service). One chart per service; an umbrella chart composes them.
- **CI/CD (M35):** `.github/workflows/ci.yml` — build+test all apps; on `main`, build/push images tagged
  by commit SHA and `helm upgrade` to AKS (image promotion = same SHA dev→stage→prod).
- **AKS (M33) + observability (M34):** taught with az-CLI + the manifests/charts above + App Insights /
  Azure Monitor / fluentd config patterns (target pattern; no Azure here).

## Working agreements for AI

- Prefer editing shared `libs/` types over inlining a type in one app.
- When adding an endpoint, update the matching DTO/contract and a test in the same change.
- Generate BPMN/DMN/Helm/Avro as files in the repo, then explain what you produced — do not
  leave generated XML/YAML unexplained.
- Keep services independently runnable; do not introduce a shared runtime coupling that breaks
  "run one app on its own."
- Ask before adding a new top-level dependency or a new infra service to docker-compose.
