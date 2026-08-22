---
name: umlite-architecture
description: House style of the reference utilization-management platform — Nx workspace layout, Flyway migration naming, the event envelope and transactional outbox, the feature-flag gating idiom, Camunda BPMN/DMN conventions, and Helm/gateway shapes. Load this before emitting any file into the new workspace, so the output looks like the platform rather than like generic Spring Boot.
---

# Reference platform house style

Everything you emit into `bh-um-lite/` should look like it was written by the team that wrote the
reference platform. This file is how.

**Read the actual files before you copy a convention.** `ref_read_file` and `ref_read_config` are
there for that. What follows is a map of *where* each convention lives and *what it is for* — not
a substitute for looking.

---

## Workspace layout

```
apps/
  <name>-svc/          one deployable service
  <name>-ui/           one deployable client
libs/
  domain/              shared types. No framework imports.
  events/              event envelope + payload types
  ui/                  shared components
camunda/               .bpmn and .dmn, deployed by the Makefile
infra/
  db/                  container init only. Real DDL lives in the service's migrations
  helm/                one chart per service
  k8s/                 raw manifests where Helm is overkill
  gateway/             routes, rate limits, auth plugins
docker-compose.yml     the whole stack, locally
nx.json                project graph
```

One rule that is easy to get wrong: **a service's schema migrations live with the service, not in
`infra/db/`.** `infra/db` holds container bootstrap — creating the database, the user, the
extensions. The tables belong to whoever owns them.

## Migrations

Flyway, named `V{n}__{snake_case_description}.sql`, applied in order, **never edited once
applied**. A correction is a new migration.

Read the reference platform's existing set with `ref_read_migrations` before numbering yours.

Two things to carry across deliberately:

- **The reference platform has zero foreign keys.** That is a database-per-service consequence, not
  a style choice. Where you drop a foreign key that the legacy schema had, you have removed a
  guarantee — say what replaces it (a validating consumer, a reconciliation job, an explicit
  contract test) in the migration's own comment. "Microservices don't do FKs" is not a
  replacement.
- **Composite unique constraints are load-bearing.** The legacy `(auth_id, review_seq)` unique
  constraint is the only thing preventing a corrupt review ladder. Dropping it turns a crash into
  silent duplicate rows.

## The event envelope

Every event goes out in the platform's envelope shape. Read `libs/events` and mirror it exactly —
field names, casing, and the metadata block.

Three things about it that matter more than the shape:

1. **The envelope is hand-mirrored in several places** in the reference platform, with no schema
   registry. Adding a field means finding every copy. If you add a payload type, add it to every
   mirror, and record the absence of a registry in the gap register.
2. **Payload contents are a disclosure decision, not a serialization decision.** Ask what the
   consumer needs, not what the entity has. See the `behavioral-health-um` skill.
3. **The reference platform declares a dead-letter topic with no producer and no consumer.** Do not
   copy that. Either wire it or leave it out.

## The transactional outbox

The pattern the reference platform uses to make "persist and publish" atomic:

1. In one database transaction, write the entity **and** an `outbox_event` row.
2. A separate worker polls unpublished outbox rows, publishes them, and marks them published.
3. Consumers are idempotent, because at-least-once delivery means a duplicate will arrive.

Copy this. It is the platform's best structural idea and it is correct.

**But know its limit before you rely on it.** The outbox makes *one service's* write atomic with
its publication. It does **not** make two services' writes atomic with each other. If the legacy
system wrote five rows in one transaction and your decomposition puts three of them behind an
HTTP call, the outbox does not save you — see the `decompose-transaction` skill.

## Feature-flag gating — copy the idiom, classify each flag

The reference platform gates capabilities behind flags so the stack stays runnable with any
subset enabled: `EVENTS_ENABLED`, `OUTBOX_ENABLED`, `WORKFLOW_ENABLED`, `CACHE_ENABLED`,
`SEARCH_ENABLED`, `REPLICA_ENABLED`, `SECURITY_ENABLED`.

This is genuinely good and worth mirroring.

**Classify every flag you add before you add it:**

| Ask | If the answer is |
|---|---|
| If this were `false` in production for a week, what breaks? | *Slow, degraded, or a feature missing* → a flag is fine |
| | *An unlawful disclosure, an unlicensed determination, a missing audit trail* → **it must not be a flag** |

A regulatory control that can be switched off in configuration is not a control. Consent
enforcement, the disclosure accounting, and reviewer-licensure checks are unconditional.

Note that the reference platform ships `SECURITY_ENABLED=false` by default. That is a defensible
default for a teaching platform and an indefensible one here.

## Camunda

- BPMN and DMN under `camunda/`, deployed by the Makefile target, not by hand.
- Decision tables carry an explicit `hitPolicy`. See the `rules-to-dmn` skill — the reference
  platform's own table is `FIRST` over non-overlapping rows, so its choice tells you nothing.
- **A user task needs an assignee or a candidate group.** The reference platform's manual-review
  task has neither, which means the task exists and nobody is responsible for it. Where a task
  encodes a licensure requirement, the candidate group *is* the requirement.
- **A process that must recur needs a timer**, not a reminder job. A boundary timer on a review
  task with an escalation path is how a regulatory deadline is expressed in a process model.

## Angular

- Standalone components, no NgModules.
- **`provideRouter` with real routes.** The reference platform's `app.config.ts` provides only
  `provideHttpClient()`; `@angular/router` is a declared dependency that was never wired up.
- Service base URLs come from environment configuration, never hardcoded.
- **Consume `libs/ui`.** The reference platform has `TaskListComponent`, `CaseSearchComponent` and
  `CaseCreateComponent` and imports none of them. Orphaned shared components are a smell you
  should not reproduce.
- Route guards for role-gated screens. A guard is a real control; a `*ngIf` around a button is a
  rendering decision.

## Spring Boot service

- Java 21, Spring Boot 3.3.x.
- DTO is not the entity. The reference platform keeps them separate — keep them separate.
  **And check that every DTO field is actually persisted**: the reference platform validates a
  free-text field and then discards it, which is worse than not accepting it, because the caller
  gets a `201` and believes the data landed.
- Constructor injection, not field injection.
- Flyway on startup.

## NestJS service

- DTOs validated with `class-validator`.
- Config through `ConfigService`, never `process.env` inline.

## Gateway and Helm

- One route per service, rate limit and auth plugin declared alongside.
- One chart per service; values files per environment; no secrets in values.

---

## Where the house style and the domain disagree

The reference platform is correct for the domain it was built for. When one of its conventions
cannot express something behavioral health requires, **the convention loses** — and you record why
in the gap register rather than quietly diverging.

Specifically, do not mirror:

| Reference platform does | Because |
|---|---|
| Discards the free-text clinical field | It is the medical-necessity evidence here |
| Ships a decision table with no `DENIED` output | Denials are the regulated event |
| Terminates the process after one decision | Concurrent review is a loop |
| Leaves the review task unassigned | The candidate group is the licensure rule |
| Has no audit table and no actor columns | Part 2 requires an accounting |
| Logs member identifiers in cleartext | Multiplied across services, that is the leak |
| Ships zero tests, with CI that cannot fail on their absence | Nothing catches any of the above |

Each of those is a `must-build-new` or `must-not-port` entry with cited evidence — not a silent
improvement.
