# CAPSTONE-9: Modernization Agent — Behavioral Health UM (Spring MVC monolith → distributed)

**Domain**: A-BH — Behavioral Health Utilization Management (a payer's carve-out prior-auth system)
**Difficulty**: ★★★★★
**Skills Practiced**: MCP servers (M07), multi-tool orchestration (M06), planning & task
decomposition (M13), multi-agent systems (M14), input guardrails (M16), output guardrails + HITL
(M17), evaluation & testing (M18), tracing & logging (M19), deployment (M22B), spec-driven
development (M15B, M26), **Claude Code Skills** (new to this corpus)
**Estimated Time**: 14–18 hours across two gated phases (9A backend 10–12h, 9B frontend 4–6h)
**Prerequisites**: M07, M13, M14, M15B, M16, M17, M18, M22B. Docker Desktop with ~8 GB free disk.
Java 21 + Node 20 to build the generated output.
**SDK Tier**: **Tier 3** per `prompts/19-sdk-tier-policy.md`. The primary solution uses
`claude-agent-sdk`; subagents are declared as `.claude/agents/<name>.md`; hooks live in
`.claude/settings.json`; domain knowledge lives in `.claude/skills/<name>/SKILL.md`;
`spec/agent-spec.md` is mandatory and drives `/generate-from-spec`. The hand-rolled loop is confined
to `appendix/manual-loop.py`, labeled "under the hood — for understanding, not for production."

---

## Business Context

Bridgeway Behavioral Health was the **carve-out vendor**. For thirty years, payers carved behavioral
health out to a separate company with its own separate system, its own network, and its own member
IDs. That is the reason this capstone exists: the health plan's medical prior-auth runs on a modern
distributed platform, while behavioral health still runs on **BHAuthTrack 4.2** — a single Java 8 /
Spring MVC 4.3 / JSP WAR on Tomcat 8, backed by Oracle 11g, deployed in 2011 and last meaningfully
touched in 2013.

The plan has in-sourced behavioral health. Two systems answering the same question — *is this
medically necessary?* — cannot be maintained by one team. BHAuthTrack has to move onto the medical
platform's architecture.

The obvious framing is "rewrite the monolith as microservices," and that framing is a trap. The
modern platform is a **clean-room learning rebuild**: it is deliberately thin. It has two tables and
no foreign keys. It validates a `notes` field and then throws it away. Its decision table has three
rules and cannot produce a denial. It has no audit trail, no roles, and no tests at all. None of that
is a defect *for medical prior auth as taught* — and every one of them is fatal for behavioral health.

So the agent's job is not translation. It is: **port the architecture, and detect where the
architecture you are porting to is insufficient for the domain you are porting in.** The deliverable
is a working repository *plus a gap register*.

---

## What the Student Builds

A coordinator agent plus seven specialist subagents, reading two source trees and emitting a third.

```
modernization-coordinator  (claude-sonnet-4-6)
  |- architecture-cartographer  reference platform -> architecture manifest (+ insufficiency tags)
  |- monolith-archaeologist     Java monolith      -> domain model + seam map + unknowns queue
  |- jsp-archaeologist          JSP/JSTL views     -> screen inventory + RULES FOUND IN VIEWS
  |- rules-extractor            PL/SQL + Java rules-> decision-table IR with a justified hit policy
  |- gap-analyst                all of the above   -> THE GAP REGISTER
  |- repo-synthesizer           gap register       -> bh-um-lite/ backend + workflow
  |- frontend-synthesizer       screen inventory   -> bh-um-lite/ routed, role-guarded Angular app
  |- parity-validator           everything         -> proof, or exactly where the proof fails
```

Two source trees, both **read-only, enforced in code**:

| Tree | What it is | Role |
|---|---|---|
| `reference-umlite/` | The modern clinical platform: Nx monorepo, Angular + NestJS + Spring Boot, Kafka, Camunda BPMN/DMN, Flyway, outbox | **Architecture donor** |
| `bhauthtrack/` | The Java 8 / Spring MVC / JSP / Oracle monolith | **Domain donor** |

Output: `bh-um-lite/`, an Nx workspace that looks like the donor and behaves like behavioral health.

---

## The Gap Register — the distinctive deliverable

Every capability gets one of four verdicts. This artifact, not the code, is what the student is
really building; the code is what proves the register was right.

| Verdict | Meaning | Example |
|---|---|---|
| `port-as-is` | Donor pattern transfers unchanged | Transactional outbox; Flyway naming; the event envelope |
| `extend` | Donor pattern is right but incomplete | DMN exists but needs DENIED outputs and a diagnosis input |
| `must-build-new` | Donor has nothing; BH cannot ship without it | Audit trail, consent model, roles, review history |
| `must-not-port` | Donor pattern is actively wrong for BH | Cleartext PHI logging; the auto-approve stub; security-off-by-default |

The register is cross-checked against the donor's own `leadership/backlog-um-enhancements.md`, which
independently lists guarded status transitions, decision audit, extended DMN criteria, an appeals
path, and SLA timers as *planned and unbuilt*. When the agent's register and the donor team's backlog
agree, that is signal. When they disagree, the student investigates which is wrong.

---

## The Legacy Monolith — `bhauthtrack/`

Java 8 · Spring MVC 4.3 · JSP/JSTL · single WAR on Tomcat 8 · Oracle 11g · Quartz · Log4j 1.x.
Classic four-layer package structure. XML config. Rules split between a Java God-class and an Oracle
package. Every artifact below maps to exactly one capability in the reference platform, and every
mapping hides a decomposition question.

| Legacy artifact | Maps to | The question it forces |
|---|---|---|
| One WAR, one Tomcat | Three deployables | Where are the service boundaries? |
| `@Controller` + JSP + JSTL | Angular SPA + REST/GraphQL | Which "markup" is actually business logic? |
| `AuthCaseService` (God-class) | Case service + intake service | What belongs to which side of the seam? |
| `dao/` `JdbcTemplate` + hand SQL | JPA entity + Flyway migration | DTO ≠ entity |
| One Oracle schema, **FKs everywhere** | Database-per-service, **zero FKs** | Referential integrity is a *cost* you are choosing to pay — with what? |
| `@Transactional` over the whole request | Outbox + idempotent consumer | Where did atomicity go? |
| `LocRulesService` + `PKG_LOC_RULES` | Camunda DMN | Stateful first-match vs. a declarative hit policy |
| `AuthStatusService.advance()` switch | Camunda BPMN | One-shot vs. continued stay |
| Quartz nightly X12 278 batch | Real-time REST intake | Batch idempotency |
| `AuthFilter` + LDAP + role bitmasks | OIDC + gateway | Map onto *what*? The donor has no roles |
| Log4j narrative concatenation | (donor logs PHI too) | The port amplifies one leak into three |
| `BH_AUDIT` + Hibernate interceptor | (donor has nothing) | `must-build-new` |

**Data model**: `BH_MEMBER`, `BH_AUTH`, `BH_LOC_REVIEW`, `BH_ASSESSMENT`, `BH_CONSENT`,
`BH_AUTH_QUEUE`, `BH_AUDIT_LOG`, `BH_USER_ROLE`, `BH_PROVIDER` — with real foreign keys, which is
precisely what makes losing them visible.

**Codes** (real, correctly formatted; all patient data fictional): CPT 90791/90792/90832/90834/90837/
90853; ABA 97151–97158; HCPCS H0015/H0018/H0019/H2036, S9480; ICD-10 F10.20, F11.20, F32.2, F33.2,
F41.1, F84.0; ASAM 1.0/2.1/2.5/3.1/3.5/3.7/4.0; PHQ-9, GAD-7, C-SSRS instrument scores.

---

## Why Behavioral Health Is Not A Reskin

| Axis | Medical (the donor) | Behavioral health |
|---|---|---|
| Criteria | Procedure-based yes/no on a CPT | **ASAM** 0.5→4.0 over six dimensions; **LOCUS/CALOCUS** — a level-of-care *ladder* |
| Cadence | One-shot: submit → decide → notify → end | **Concurrent review**: initial auth plus a recurring continued-stay review (residential ~7d, PHP ~14d) |
| Privacy | HIPAA | HIPAA **plus 42 CFR Part 2** — SUD records carry a redisclosure prohibition and consent must name the recipient |
| Regulatory | Medical necessity | **plus MHPAEA parity** — a BH treatment limitation stricter than its med/surg analogue is an exposure |

Two rules from the donor course's own domain modules anchor the design:

- **The role rule**: *a nurse may approve but may never deny; only a medical director may issue an
  adverse determination.* This is why the status enum has `PENDED` at all — a separation of duties
  encoded as an enum value. In behavioral health it is stronger still: adverse determinations for SUD
  and psychiatric level-of-care generally require a same-specialty peer reviewer.
- **The regulator's clock**: a timer on a workflow task is not a technical nicety, it is a
  regulator's turnaround deadline. Continued-stay cadence *is* that timer, and the donor has none.

---

## The Trap Registry (this list is the curriculum)

Conceptual, not syntactic. A verbatim port passes everything the donor ships — because the donor
ships no tests — and is still wrong.

### Backend traps (phase 9A)

1. **Stateful first-match → declarative hit policy** *(primary)*. `PKG_LOC_RULES.EVAL_LOC` mutates a
   running score across branches and falls through; `LocRulesService` layers Java `if/else` on top.
   DMN is declarative with a hit policy. The donor's table is first-hit over trivial non-overlapping
   rows, so the distinction never bites there — it bites hard at the ASAM 3.5 / 3.7 boundary.
   **The validator runs both engines over a golden set and diffs. Non-zero divergence is the expected
   first result.**
2. **The validated-then-dropped narrative** *(primary)*. The donor's `notes` field passes DTO
   validation and is then discarded — not a column, not an entity field, not in either event payload.
   Ported verbatim, the BH clinical narrative — which is simultaneously the medical-necessity evidence
   *and* the Part 2-protected content — is validated and thrown away, behind a `201 Created`.
3. **No continued-stay loop, no reviewer licensure.** A verbatim BPMN port terminates after the first
   decision, and the donor's review task has no assignee and no candidate group, so the "only a
   medical director may deny" rule vanishes.
4. **A decision table that cannot deny.** The donor table has no `DENIED` output and no diagnosis
   input, and one of its three rows is dead code. Mirroring its shape yields a level-of-care engine
   that approves everything, with no criterion-traceable denial reason.
5. **Part 2 leaks through logging and eventing** *(primary)*. The legacy already concatenates the
   narrative into Log4j lines; the donor logs member IDs, ships plain JSON to an unauthenticated
   broker, and indexes into Elasticsearch. Ported verbatim, SUD narrative fans out to **three** sinks
   with no consent scope. HIPAA-clean and Part 2-illegal.
6. **Carve-out identity.** The legacy member ID is the *carve-out vendor's*, not the plan's. The donor
   keys on an opaque 32-char string with no foreign key and no member table, so nothing objects. A 1:1
   map joins on the wrong key and matches by luck for the subset whose formats coincide.
7. **Not everything may be a feature flag.** The donor's flag-gated capability layering is its best
   trait and should be mirrored — but a consent-enforcement flag is not the same kind of thing as a
   cache flag. Part 2 enforcement can never default off.
8. **The lost transaction boundary** *(deepest)*. `AuthCaseService.submitAndDecide()` writes the auth,
   the level-of-care review **and the consent record** in one Oracle transaction. Decomposed, those
   become an HTTP hop, an event, a persist, an outbox row, another event — atomicity is gone. A naive
   port yields a system where an auth can exist without its consent record, with no compensation.

### Frontend traps (phase 9B)

9. **Business logic hiding in JSP scriptlets** *(primary)*. A JSTL role test wrapped around the deny
   button *is* the role rule, implemented in a view. Scriptlets also compute derived values that exist
   nowhere else. An agent porting screens as markup emits a component that renders the deny button for
   everyone. **JSPs are a source of rules, not markup.**
10. **Role-gated screens have nothing to map onto.** The donor ships security off by default and, even
    enabled, authentication-only — no roles, no scopes, no method security, no login flow, no
    interceptor. Verdict `must-build-new`, on both sides of the wire.

### The deliberate dead end

`AuthStatusService.advance()` branches on a `LEGACY_OVERRIDE` flag with no surviving documentation.
It goes to the manual-review queue. It is not invented. **A port that reports 100% automated is a
failure; 80% automated with a documented 20% is a success.**

---

## Hard Constraint: No PHI In Prompts

The donor organisation's own AI ground rules state *"no PHI in prompts, ever."* This agent reads a
system whose most valuable content is SUD clinical narrative, so the constraint is first-class:

- All `bhauthtrack/` fixtures are **synthetic**, generated from a documented seed, clearly fictional.
- A `PreToolUse` hook scans every tool result *before it reaches the model* and blocks or redacts
  narrative-shaped content originating outside the synthetic allowlist.
- `test_no_phi_in_prompt.py` asserts the hook fires on a planted realistic-looking narrative.
- The lab teaches the pattern by name: *how do you point an agent at a regulated codebase without
  feeding it regulated data?*

No prior capstone in this course addresses this.

---

## Skills vs Subagents vs Slash Commands

This capstone introduces `.claude/skills/` to the lab corpus, and the split is a learning objective.

| Layer | Mechanism | Why |
|---|---|---|
| BH domain knowledge — ASAM, LOCUS, code sets, Part 2, parity, the role rule | **Skill** `behavioral-health-um/` | Coordinator *and* every subagent load the same knowledge on demand. One source of truth; bundled references stay out of context until needed |
| Target house style — Nx layout, Flyway naming, envelope shape, the flag idiom, chart shapes | **Skill** `umlite-architecture/` | Makes the synthesizer emit code that looks like *this* platform, not generic Spring Boot |
| Mechanical recipes — rules→DMN; decompose one `@Transactional` method | **Skills** `rules-to-dmn/`, `decompose-transaction/` | Same steps every time, run N times. Runbooks, not decisions |
| Orchestration, isolation, hooks, HITL, cost ceiling, traces, evals | **Agent SDK** | Skills cannot orchestrate, isolate context, block a tool call, or emit spans |

**The rule of thumb**: *Skills carry knowledge and recipes; agents carry control flow and safety.*
If you would write it in a runbook, it is a Skill. If it decides, branches, parallelizes, or blocks,
it is the agent.

**Anti-patterns named in the module**: pasting the BH ontology into seven subagent system prompts
(drift plus token cost on every turn); making a Skill do orchestration; reaching for a slash command
where a Skill belongs.

---

## Guardrails (the load-bearing safety design)

1. `PreToolUse` **PHI gate** on every read result — see above. Returns `PermissionResultDeny` or a
   redacted `updatedInput`.
2. `PreToolUse` on both source trees — **read-only enforced in code, not by convention**. Evidence is
   never edited.
3. `PreToolUse` on `write_file` — deny any path outside `bh-um-lite/`.
4. `can_use_tool` **HITL gate** on `finalize_modernization` — always returns the gap register, the
   rules-divergence table and the Part 2 summary, and requires a human `--approve`. The agent can
   never approve itself.
5. `PostToolUse` — append one entry per tool call to `modernization_audit.jsonl`, narrative and
   credentials redacted.
6. Cost ceiling: abort above 400,000 cumulative output tokens. Circuit breaker: three consecutive
   subagent failures in one phase halts the run.

## Observability

`observability/tracer.py` emits one span per ported artifact (name, phase, subagent, model, tokens,
duration, verdict). `report.py` renders a console dashboard plus `modernization_report.html` /
`.json`: percentage auto-ported, the manual-review queue, the gap register, the seam map, the
rules-divergence table, screen coverage, and total token cost.

**Acceptance criterion, borrowed verbatim from the donor's definition of done**: *"If this caused an
incorrect utilization decision in production, could we explain how it happened and who owned the
logic?"* Every generated artifact must trace to a legacy source or a flagged gap.

---

## Two Tracks: Port vs Generate

The student runs both and diffs them.

| Track | How | Inherits | Misses |
|---|---|---|---|
| **1 — Modernize** | Agent reads both trees → `bh-um-lite/` | Architecture fidelity, conventions, the flag idiom | The donor's *holes* — traps 2, 3, 4, 5, 7, 10 |
| **2 — Generate** | Student writes the spec → `/generate-from-spec` → `bh-um-lite-spec/` | Clean intent, no clinical bias | Institutional knowledge — traps 1, 6, 8, 9 |

**The lesson**: *porting carries architecture and its blind spots; generating carries intent but not
institutional knowledge.* The production answer is port-then-spec-review, which is exactly what the
student performs by diffing the two trees.

---

## Test Outline

**Happy path (3)** — the full seam map is produced and every legacy screen has a route; the rules IR
round-trips to a DMN table Camunda accepts; 500 synthetic auths migrate with matching counts.

**Edge (4)** — a residential approval carries `next_review_due`; the ASAM 3.5/3.7 overlap resolves
identically under both engines once the hit policy is corrected; the clinical narrative survives
intake → persist → event; `LEGACY_OVERRIDE` reaches the manual-review queue unconverted.

**Error / adversarial (7)** — a write against either source tree is denied; a write outside
`bh-um-lite/` is denied; `finalize_modernization` blocks on HITL; **the Part 2 leak is detected and
reported non-zero**; **the consent-atomicity violation is detected**; **the deny button renders
without a role guard and the screen test fails**; the PHI hook fires on a planted narrative.

*A clean report on any of the bolded three means the validator is broken, not that the port is good.*

---

## Going Further (all OPTIONAL)

1. Add an appeals sub-process — an `APPEALED` status plus a BPMN appeal sub-process with the
   no-self-review constraint. This completes the utilization journey and is item #7 on the donor's
   own backlog.
2. Stand up Native Federation for real and split the worklist into its own micro-frontend.
3. Replace hand-mirrored event contracts with a schema registry and prove compatibility on evolution.
4. Add a `parity-auditor` subagent that compares every BH treatment limitation against its med/surg
   analogue and produces an MHPAEA comparative-analysis draft.
5. Run the same spec against the *medical* monolith and diff what the agent produces — does the gap
   register shrink?
