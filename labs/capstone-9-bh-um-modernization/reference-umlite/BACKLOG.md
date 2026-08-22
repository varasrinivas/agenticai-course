<!--
  Vendored from the reference platform team's own governance folder:
    um-course-kit/leadership/backlog-um-enhancements.md

  Checked in so the lab is portable. The gap-analyst cross-checks its
  register against this file: AGREEMENT IS SIGNAL -- the team that built
  the platform independently reached the same conclusion about what is
  missing -- and DISAGREEMENT is something to investigate in either
  direction.
-->

# Pre-Filled Backlog — UM Enhancement Candidates (2 Sprints)

Grounded in the real `um-lite` codebase (services, file paths, and current gaps as of this planning).
Each item is a **thin vertical slice**. Sequenced so Sprint 1 builds trust on lower-clinical-risk work
and Sprint 2 takes on the decisioning/clinical changes once the review loop is proven.

**Legend**
- **Est:** S (≤1 day) · M (2–3 days) · L (3–5 days)
- **Risk:** clinical = affects a utilization decision; compliance = affects audit/regulatory; data = integrity only; low = none of these
- **AI-suit:** High = well-scoped, grounded in existing files · Med = needs concurrency/integration reasoning · **Low = needs human/clinical SME judgment** (still done with AI, but budget extra review)

---

## Current-state recap (what exists today)

| Layer | Service | State |
|---|---|---|
| Intake | `apps/um-intake-svc` (NestJS) | Validates length only; forwards over REST or publishes `pa.submitted` |
| Case | `apps/um-case-svc` (Spring/Postgres) | Owns `PriorAuthCase`; `transitionTo()` unguarded; rationale not persisted; outbox table exists |
| UI | `apps/intake-ui` (Angular) | Minimal submit form; no list/search |
| Events | `libs/events`, `apps/.../events` | `pa.submitted` / `pa.decisioned` / `pa.dead-letter`; `EventEnvelope` v1 |
| Workflow | `camunda/prior-auth.bpmn`, `camunda/pa-decision.dmn` | Base process + decision table; no appeals, no SLA timers |
| Statuses | `CaseStatus` | `SUBMITTED, IN_REVIEW, APPROVED, DENIED, PENDED` — **no APPEALED** |

---

## Sprint 1 — establish rhythm & trust (lower clinical risk, high AI-suitability)

Target: commit 3, keep 2 as stretch/backfill. Get an early credible win.

| # | Enhancement (vertical slice) | Files touched | Est | Risk | AI-suit | Owner | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Guard case status transitions** — replace unguarded `transitionTo()` with a validated state machine (e.g. block `APPROVED→SUBMITTED`, allow `SUBMITTED→IN_REVIEW→APPROVED/DENIED/PENDED`). | `um-case-svc/.../domain/PriorAuthCase.java`, `domain/CaseStatus.java` | S | data | High | | Commit |
| 2 | **Persist decision rationale + decidedBy** on the case so the *why* of every decision is auditable, not just on the Kafka event. New columns + Flyway migration + response field. | `um-case-svc/.../domain/PriorAuthCase.java`, `api/CaseResponse.java`, new `db/migration/V3__decision_audit.sql`, consumer of `pa.decisioned` | M | **compliance** | High | | Commit |
| 3 | **CPT/ICD format validation at intake** — reject malformed `procedureCode` (CPT/HCPCS) and `diagnosisCode` (ICD-10) with a clear 400, instead of only length-checking. | `um-intake-svc/.../dto/create-prior-auth.dto.ts`, mirror in `libs/domain/.../prior-auth.types.ts` | S | low | High | | Commit |
| 4 | **Case list + filter endpoint & UI** — `GET /api/cases?status=&memberId=` plus a simple Angular list view. Gives reviewers operational visibility. | `um-case-svc/.../api/CaseController.java`, `repo/PriorAuthCaseRepository.java`, `intake-ui/.../app` | M | low | High | | Stretch |
| 5 | ~~**Idempotent `pa.submitted` consumer**~~ — **already implemented** (`PaSubmittedConsumer` dedupes via `existsById`, and an outbox exists). *Replace with:* **harden idempotency tests** + dedupe by `eventId` (not just `caseId`) so a replayed event with a new caseId edge case is covered. | `um-case-svc/.../events/PaSubmittedConsumer.java`, `src/test` | S | data | High | | Stretch |

**Sprint 1 guardrail:** ≤1 "Med" AI-suitability item committed; everything else High. No clinical-risk
items this sprint — that's deliberate, to prove the review loop first.

---

## Sprint 2 — scale into decisioning & clinical (higher risk, more human review)

Target: commit 2–3. These need a clinical/business SME in review (see `definition-of-done.md`).

| # | Enhancement (vertical slice) | Files touched | Est | Risk | AI-suit | Owner | Status |
|---|---|---|---|---|---|---|---|
| 6 | **Extend DMN medical-necessity criteria** — add criteria rows (e.g. for procedure `27447` total knee) so the decision table reflects real necessity rules instead of a stub. **Clinical SME signs off the table.** | `camunda/pa-decision.dmn` | M | **clinical** | **Low** | | Commit |
| 7 | **Appeals path** — add `APPEALED` to `CaseStatus`, an appeal-intake endpoint, and a BPMN appeal sub-process. Completes the Utilization Journey (Intake → … → Appeals). | `CaseStatus.java`, `PriorAuthCase.java`, `CaseController.java`, `camunda/prior-auth.bpmn`, intake DTO | L | **clinical/compliance** | Low–Med | | Commit |
| 8 | **SLA turnaround timer + auto-escalation** — Camunda boundary timer that pends/escalates a case nearing its decision deadline (regulatory turnaround). Ties to Camunda appendix C6 (timers). | `camunda/prior-auth.bpmn`, case-svc worker | M | compliance | Med | | Commit / Stretch |
| 9 | **Pend workflow with reason codes** — `PENDED` carries a reason + a "request additional clinical info" loop back to the provider, rather than a dead-end status. | `CaseStatus`/case-svc, `camunda/prior-auth.bpmn`, intake-ui | M | clinical/compliance | Med | | Stretch |
| 10 | **Dead-letter retry + alerting** — consume `pa.dead-letter`, apply bounded retry, and surface a metric/alert so poisoned messages aren't silently lost. | `um-case-svc/.../events`, `um-intake-svc/.../events`, `infra` | M | data | Med | | Stretch |

**Sprint 2 guardrail:** every clinical-risk item gets a clinical/business reviewer who understands the
*intent*, not just the code. Reserve the last 2–3 days as the hardening buffer.

---

## How to run planning with this

1. **Sprint 0:** confirm current-state recap still holds, assign owners, set the Sprint 0 DORA baseline
   in `sprint-planning-template.md`.
2. **Pick Sprint 1 commits (3):** recommend **#1, #2, #3** — small, high-value, high AI-suitability,
   and #2 lands an early *compliance* win that plays well upward.
3. **Sprint 1 retro** answers *"where did AI help / cost rework?"* → use it to decide how aggressively to
   take the **Low AI-suitability** Sprint 2 items (#6, #7).
4. **Sprint 2:** lead with **#6** (highest clinical value) but pair it with the clinical SME from day one.

> **Backlog sizing check (from the template):** if >60% of a sprint is "L" or "Low AI-suit", you're
> overcommitting. Sprint 1 is all S/M & High — healthy. Sprint 2 is heavier by design — commit fewer.
