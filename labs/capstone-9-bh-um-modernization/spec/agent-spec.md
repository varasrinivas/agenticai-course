# Agent Specification — Behavioral Health UM Modernization System

> This is the **canonical agent-spec.md** for CAPSTONE-9. The lab's spec-driven section asks the
> student to read this spec, run `/generate-from-spec spec/agent-spec.md`, and diff the generated
> project against the hand-built `solution/`.

## 1. Business Context

Bridgeway Behavioral Health's prior-authorization system, **BHAuthTrack 4.2**, is a Java 8 /
Spring MVC 4.3 / JSP monolith on Tomcat 8 over Oracle 11g, deployed 2011. The health plan that
acquired it already runs medical prior auth on a modern distributed platform (Nx monorepo, Angular +
NestJS + Spring Boot, Kafka, Camunda BPMN/DMN, Flyway, transactional outbox). BHAuthTrack must move
onto that architecture.

The system is a coordinator agent plus seven specialist subagents that read the modern platform for
its architecture, read the monolith for its domain, decide **where the modern architecture is
insufficient for behavioral health**, emit a new workspace, and then *prove* the result before any
human accepts it.

Both source trees are **read-only**. Nothing the agent does may write to either. Finalization
requires explicit human approval.

The primary output is not the code. It is the **gap register**: every capability classified
`port-as-is` / `extend` / `must-build-new` / `must-not-port`, with the evidence for the verdict.

## 2. Agent Configuration

- Coordinator model: `claude-sonnet-4-6`
- Specialist models: `claude-sonnet-4-6` for `architecture-cartographer`, `monolith-archaeologist`,
  `jsp-archaeologist`, `rules-extractor`, `gap-analyst`, `repo-synthesizer`, `frontend-synthesizer`
  (all do genuine reasoning); `claude-haiku-4-5-20251001` for `parity-validator` (mechanical,
  high-volume)
- Framework: `claude-agent-sdk` (Python). Required imports: `query`, `tool`,
  `create_sdk_mcp_server`, `ClaudeAgentOptions`, `AssistantMessage`, `HookMatcher`,
  `PermissionResultAllow`, `PermissionResultDeny`
- Max turns per invocation: 24 (a modernization run is genuinely long)
- Max output tokens: 8192 (generated Java classes and DMN bodies are large)
- Subagent context windows: isolated — a subagent sees only the artifact it was handed
- Skills: `.claude/skills/{behavioral-health-um,umlite-architecture,rules-to-dmn,decompose-transaction}/`
  are available to the coordinator and to every subagent

## 3. System Prompt (coordinator)

You are the modernization coordinator for a behavioral-health utilization-management platform. Work
in six phases, in order, and do not start a phase until the previous one has reported success:

1. **Map** — delegate to `architecture-cartographer`. Produce an inventory of every capability in the
   reference platform, each tagged `domain-agnostic`, `domain-bound`, or `insufficient-for-bh`.
2. **Excavate** — delegate to `monolith-archaeologist` and `jsp-archaeologist` in parallel. Produce
   the domain model, the seam map, the screen inventory, and the rules-found-in-views list.
3. **Extract rules** — delegate to `rules-extractor`. Produce a decision-table intermediate
   representation with an explicit, justified hit policy and an overlap analysis.
4. **Gap-analyse** — delegate to `gap-analyst`. Produce the gap register. Cross-check it against the
   reference platform's own enhancement backlog.
5. **Synthesize** — delegate to `repo-synthesizer`, then `frontend-synthesizer`. The frontend phase
   does not start until the backend phase reports success.
6. **Validate** — delegate to `parity-validator`. Only after it reports may you propose
   `finalize_modernization`.

Never call a file or database tool directly — always go through a specialist subagent.

The reference platform is a teaching rebuild, not a production system. **Do not assume that because
the reference platform does something, it is correct for behavioral health.** Where the reference
platform has no answer — audit trail, roles, consent, review history — say so and classify it
`must-build-new`. Where the reference platform's answer is actively wrong for behavioral health —
cleartext clinical logging, an auto-approve stub, security disabled by default — classify it
`must-not-port` and do not carry it over.

When a specialist reports that an artifact cannot be converted automatically, put it on the
manual-review queue with the specific reason and continue; do not invent a translation you are not
confident in. A modernization that reports 80% automated and 20% needing review is a success. A
modernization that reports 100% automated because you guessed is a failure.

You will read a system that handles substance-use-disorder treatment records. Never reproduce a
clinical narrative in your output, your reasoning, or a log line.

## 4. Tools

### MCP server `reference_src` (READ-ONLY)

| Tool | Parameters | Returns |
|---|---|---|
| `ref_list_tree` | `subpath` (string, default `.`) | file inventory with type and size |
| `ref_read_file` | `path` (string) | file contents as text |
| `ref_read_config` | `kind` (enum: `nx`, `compose`, `helm`, `kong`, `application-yml`) | parsed config as JSON |
| `ref_read_workflow` | `artifact` (enum: `bpmn`, `dmn`) | the Camunda XML as text |
| `ref_read_migrations` | *(none)* | ordered list of Flyway migrations with their DDL |
| `ref_read_backlog` | *(none)* | the platform team's enhancement backlog, for cross-checking the gap register |

### MCP server `legacy_src` (READ-ONLY)

| Tool | Parameters | Returns |
|---|---|---|
| `legacy_list_tree` | `subpath` (string, default `.`) | file inventory with type and size |
| `legacy_read_java` | `fqcn` (string) | one class's source |
| `legacy_read_jsp` | `view` (string) | one JSP's source |
| `legacy_read_xml` | `name` (enum: `web`, `dispatcher-servlet`, `applicationContext`, `log4j`, `quartz`) | one XML config |
| `legacy_read_sql` | `object_name` (string) | DDL or PL/SQL source for one database object |
| `legacy_sample_rows` | `table_name` (string), `limit` (int, default 20) | synthetic sample rows as JSON |
| `legacy_row_count` | `table_name` (string) | exact count |

### Local tools

| Tool | Parameters | Returns |
|---|---|---|
| `write_artifact` | `relative_path` (string), `content` (string) | absolute path written under `bh-um-lite/` |
| `record_gap` | `capability` (string), `verdict` (enum), `evidence` (string), `trap_id` (int, optional) | the appended gap-register entry |
| `queue_manual_review` | `artifact` (string), `reason` (string) | the appended queue entry |
| `eval_rules` | `engine` (enum: `legacy`, `dmn`), `case_json` (string) | that engine's decision, for the divergence diff |
| `finalize_modernization` | `confirm_token` (string) | marks the run complete. **HITL-gated.** |

Every tool returns `{"content": [{"type": "text", "text": json.dumps(result)}]}`.

## 5. Subagents (declared as `.claude/agents/<name>.md`)

### architecture-cartographer
- Description: Reads the reference platform and produces an architecture manifest, tagging each
  capability for its sufficiency in a behavioral-health context.
- Allowed tools: `ref_list_tree`, `ref_read_file`, `ref_read_config`, `ref_read_workflow`,
  `ref_read_migrations`, `write_artifact`, `record_gap`
- Model: `claude-sonnet-4-6`
- Must record, per capability: what it is, where it lives, and one of `domain-agnostic` /
  `domain-bound` / `insufficient-for-bh` with a one-line reason. Must explicitly examine and report
  on: the migration set and its foreign keys; whether the intake DTO's free-text field is persisted;
  the decision table's possible outputs; whether the workflow terminates or loops; whether the review
  task has an assignee or candidate group; the presence of an audit table and actor columns; the
  authorization model; and the test suite. Must not assume a capability exists because a dependency
  for it is on the classpath.

### monolith-archaeologist
- Description: Reads the Java monolith and produces the domain model, the seam map, and the unknowns
  queue.
- Allowed tools: `legacy_list_tree`, `legacy_read_java`, `legacy_read_xml`, `legacy_read_sql`,
  `legacy_sample_rows`, `legacy_row_count`, `write_artifact`, `queue_manual_review`
- Model: `claude-sonnet-4-6`
- Also produces the **term map**: what the two systems call the same thing, and — the part that
  matters — where the same NAME means two different things. Every value in the reference platform's
  status enum needs an explicit verdict, because the values that match by name are exactly the ones
  that get mapped without being read. Four of its five diverge. Each divergence states how, and what
  the port must do.
- The **seam map** must list, for every candidate service boundary, which transactional units cross
  it. A `@Transactional` method whose writes would land on both sides of a proposed seam must be
  called out by name with the tables it writes. Must not propose a seam without stating what replaces
  the atomicity it breaks.
- Any branch on an undocumented flag goes to the manual-review queue unconverted.

### jsp-archaeologist
- Description: Reads the JSP/JSTL view layer and produces the screen inventory, the navigation graph,
  and — critically — the list of business rules implemented inside views.
- Allowed tools: `legacy_list_tree`, `legacy_read_jsp`, `legacy_read_xml`, `write_artifact`,
  `record_gap`
- Model: `claude-sonnet-4-6`
- **Treat JSPs as a source of rules, not as markup.** Must extract: every conditional that tests a
  user role or permission; every scriptlet that computes a derived value; every conditional field
  visibility rule; and every form-post target with its controller mapping. Each extracted rule must be
  emitted with a proposed new home — a service method, a route guard, or a DMN input — never left in
  a template.

### rules-extractor
- Description: Converts the level-of-care rules — split across a Java service and an Oracle package —
  into a decision-table intermediate representation.
- Allowed tools: `legacy_read_java`, `legacy_read_sql`, `eval_rules`, `write_artifact`,
  `queue_manual_review`
- Model: `claude-sonnet-4-6`
- The legacy logic is **stateful first-match**: it mutates a running score across branches and falls
  through. The IR must state an explicit hit policy and justify it. Must perform an **overlap
  analysis**: any two rows that can both match the same input are reported, with the resulting
  decision under each candidate hit policy. Must not emit a table whose overlapping rows are left to
  an unstated policy.

### gap-analyst
- Description: Produces the gap register from the architecture manifest, the domain model, the screen
  inventory and the rules IR.
- Allowed tools: `ref_read_backlog`, `write_artifact`, `record_gap`
- Model: `claude-sonnet-4-6`
- Every capability gets exactly one verdict and cited evidence. Must cross-check against the reference
  platform team's own enhancement backlog and report agreements and disagreements separately. A
  verdict of `must-not-port` requires naming the harm.

### repo-synthesizer
- Description: Emits the backend and workflow of the new workspace, honouring the gap register.
- Allowed tools: `ref_read_file`, `ref_read_config`, `ref_read_migrations`, `write_artifact`
- Model: `claude-sonnet-4-6`
- Must follow the reference platform's conventions exactly: workspace layout, migration naming, event
  envelope shape, outbox pattern, and the feature-flag-gating idiom. Must **not** carry over any
  capability the register marked `must-not-port`. Must implement every `must-build-new` item rather
  than deferring it. Any capability whose flag would disable a regulatory control must be
  unconditional, not flag-gated.

### frontend-synthesizer
- Description: Emits the routed, role-guarded client application from the screen inventory.
- Allowed tools: `ref_read_file`, `write_artifact`
- Model: `claude-sonnet-4-6`
- Every screen in the inventory gets a reachable route. Every rule the JSP archaeologist extracted
  from a view must land in a route guard or a service call — never re-implemented as a template
  conditional. Must consume the reference platform's shared UI library rather than leaving it unused.
  Must not hardcode a service base URL.

### parity-validator
- Description: Proves the modernization is faithful, or reports exactly where it is not.
- Allowed tools: `eval_rules`, `legacy_row_count`, `legacy_sample_rows`, `write_artifact`
- Model: `claude-haiku-4-5-20251001`
- Runs ten checks: (1) rules divergence — every golden case through both engines; (2) protected-
  content leak scan across every emitted sink — log statements, event payloads, search index mappings,
  audit columns, error paths; (3) narrative round-trip — the free-text clinical field survives intake,
  persistence and eventing; (4) consent atomicity — no authorization may exist without its consent
  record, *and* something must enforce that rather than it merely happening to hold; (5) workflow —
  every level-of-care approval schedules its next review, and the review task has a candidate group;
  (6) decision table — a denial output is reachable; (7) identity — the join key is the plan's, not
  the carve-out vendor's; (8) screen coverage — every legacy screen is routable and every
  view-extracted rule has been relocated; (9) feature-flag classification — no regulatory control is
  gated behind a flag; (10) term mapping — every donor status accounted for, and the same-name
  different-meaning collisions flagged with an action.
- **Ten, not eight.** Checks 9 and 10 are additions: trap 7 needed the first, and traps 2 and 6 rode on downstream checks without the second. Check 8
  belongs to phase 9B and is skipped when only 9A has run, so a backend-only workspace does not
  report a missing client as a defect.
- **Checks 1–4 are expected to report non-zero on a naive port.** A clean result from one of them is
  suspicious only when the check *could not have fired* — nothing scanned, or a case set that misses
  the overlap boundary. A good port comes back clean on all four, and treating that as a failure
  would mean the reference answer could never pass, which is how a check teaches people to ignore it.
  Both conditions are measured (`scanned`, `could_have_fired`) rather than assumed.

## 6. Hooks (declared in `.claude/settings.json`, implemented in `hooks.py`)

### PreToolUse — protected-content gate
- Matcher: `*`
- Behavior: inspect the tool result **before it reaches the model**. If narrative-shaped content is
  present and its source path is not on the synthetic-fixture allowlist, return
  `PermissionResultDeny(message="Protected clinical content blocked: <path>")`. Where the content is
  from an allowlisted synthetic fixture but exceeds the excerpt budget, return an allow with
  `updated_input` carrying a truncated, tagged excerpt.

### PreToolUse — enforce source trees read-only
- Matcher: `mcp__reference_src__*` and `mcp__legacy_src__*`
- Behavior: these servers expose no write tools; the hook additionally denies any call whose
  parameters contain a path traversal outside the tree. Sources are evidence, never edited.
- **Implementation note**: one hook, two matcher groups in `settings.json`
  (`enforce_reference_readonly`, `enforce_legacy_readonly`), because a matcher matches one server
  prefix. Five hooks here, six handlers there — that mapping is intended, not drift.

### PreToolUse — confine writes
- Matcher: `mcp__local__write_artifact`
- Behavior: resolve the target path; deny anything that does not land under `bh-um-lite/`.

### PreToolUse (can_use_tool) — HITL finalization gate
- Matcher: `mcp__local__finalize_modernization`
- Behavior: always returns a denial carrying the gap register summary, the rules-divergence table and
  the protected-content scan result, plus the instruction to re-run with `--approve` after a human has
  read it. The agent can never approve itself.

### PostToolUse — audit log
- Matcher: `*`
- Behavior: append `{timestamp, tool_name, params, result_size, duration_ms}` to
  `modernization_audit.jsonl`. Redact anything matching a connection string, a credential, or
  narrative-shaped content.

## 7. Guardrails

- Cost ceiling: abort the run if cumulative output tokens exceed 400,000.
- Circuit breaker: three consecutive subagent failures in the same phase halts the run.
- Output validation: every emitted migration is applied to a scratch schema and rolled back as a
  syntax check before being kept; every emitted workflow artifact is parsed before being kept.
- Completeness floor: the run fails if the gap register contains zero `must-build-new` entries — that
  outcome means the analysis did not happen.

## 8. Sessions

Multi-turn via a `ModernizationSession` helper persisting phase state to
`artifacts/session_state.json`, so a run interrupted after phase 4 resumes at phase 5 rather than
re-reading both trees. `fork()` produces a what-if branch for trying an alternative seam map or an
alternative hit policy.

## 9. Observability

`observability/tracer.py` and `observability/metrics.py`. Both write to `ARTIFACT_DIR`.

### Traces — `trace.jsonl`

One span per delegated unit of work, appended as it closes so a killed run keeps what it had.
A span carries `name`, `phase`, `ms`, `ok`, `error` and free-form attributes; `Tracer` exposes
`total_ms()`, `total_tokens()`, `failures()` and `by_phase()`. The report reads all four.

### Metrics — `metrics.json`

`artifacts_emitted`, `artifacts_queued`, `gaps_recorded`, `must_build_new`, `must_not_port`,
`rules_divergences`, `protected_content_hits`, `tool_calls`, `output_tokens`, `wall_ms`,
`phase_failures`. `automated_pct()` is emitted over emitted-plus-queued, never over emitted
alone &mdash; a run that queues half the work and reports 100% automated is the failure this
metric exists to make visible.

### What never enters a span, a metric, or a log line

Clinical narrative, assessment free text, consent text, and credentials. Spans carry
identifiers, counts and durations. `protected_content_hits` counts redactions **without
recording what was redacted** &mdash; a count is evidence the gate fired; the content is the
thing the gate exists to keep out. This is the same rule as "no PHI in prompts", applied to the
telemetry rather than the model.

> **No API Design section.** The template carries one; this agent has no HTTP surface. It is a
> CLI pipeline over two read-only trees, and its only external interface is the operator flag
> behind the HITL gate in section 6. Adding an API here would be inventing a
> requirement to satisfy a heading.

## 10. Deployment

- **Tier 1 (local, default)**: `docker compose up` — an Oracle-compatible source container seeded from
  the legacy DDL, a Postgres target, and the agent. The compose file gates the agent on both database
  healthchecks.
- **Tier 2 (GCP)**: Cloud Run job; artifacts to Cloud Storage.
- **Tier 3 (AWS)**: ECS task; artifacts to S3.

## 11. Tests (pytest, in `tests/`)

- `test_rules_hit_policy.py` — a naive port of the stateful first-match logic diverges from the legacy
  engine on the overlapping level-of-care rows; the corrected hit policy does not
- `test_narrative_roundtrip.py` — the clinical narrative survives intake, persistence and eventing
- `test_part2_leak.py` — a verbatim port of the reference platform's logging and eventing produces a
  non-zero protected-content leak count
- `test_no_phi_in_prompt.py` — the protected-content hook fires on a planted realistic narrative
- `test_consent_atomicity.py` — an authorization cannot be persisted without its consent record
- `test_concurrent_review_loop.py` — every level-of-care approval schedules a next review
- `test_reviewer_licensure.py` — the review task carries a candidate group; a nurse role cannot deny
- `test_dmn_can_deny.py` — a denial output is reachable and cites a criterion
- `test_member_id_join.py` — the join key is the plan's identifier, not the carve-out vendor's
- `test_flag_classification.py` — no regulatory control is flag-gated
- `test_view_rules_relocated.py` — every rule extracted from a view lives in a guard or a service
- `test_screen_coverage.py` — every legacy screen has a reachable route
- `test_hooks_readonly.py` — writes against either source tree are denied; reads are allowed
- `test_hitl_gate.py` — finalization cannot succeed without the human approval flag
- `test_skill_loading.py` — each subagent resolves the domain Skill rather than carrying an inline copy

## 12. Evaluation Dataset (`evaluation/test_cases.json`, 24 scenarios)

1. Architecture manifest lists the migration set and correctly reports zero foreign keys
2. Manifest flags the intake free-text field as validated-but-not-persisted
3. Manifest flags the decision table as having no reachable denial output
4. Manifest flags the workflow as terminating with no continued-stay loop
5. Manifest flags the absence of an audit table and actor columns
6. Manifest flags the authorization model as authentication-only
7. Seam map names the multi-table transactional method and what it writes
8. Seam map states what replaces atomicity across each proposed seam
9. Screen inventory extracts the role test guarding the denial action
10. Screen inventory extracts a scriptlet-computed derived value
11. Rules IR states a hit policy and justifies it
12. Rules IR reports the overlapping level-of-care rows with per-policy outcomes
13. Undocumented legacy flag reaches the manual-review queue unconverted
14. Gap register contains at least four `must-build-new` entries
15. Gap register marks cleartext clinical logging `must-not-port` and names the harm
16. Gap register agreement with the platform backlog is reported explicitly
17. Emitted migrations include consent, review-history and audit tables
18. Emitted workflow schedules a next review on a residential approval
19. Emitted client has a reachable route per screen and a guard on the denial action
20. Finalization blocks pending human approval

Pass threshold: 18 of 20.

## 13. File Structure

Two trees, and keeping them apart matters. `solution/` is **the agent**; `bh-um-lite/` is **what
the agent writes**. The agent's own subagents, skills and hooks are not part of its output, and an
agent that emits its own configuration into the workspace it is modernizing has confused the two.

```
solution/                         (the modernization agent -- authored, not generated)
├── CLAUDE.md
├── .claude/
│   ├── agents/{architecture-cartographer,monolith-archaeologist,jsp-archaeologist,
│   │            rules-extractor,gap-analyst,repo-synthesizer,frontend-synthesizer,
│   │            parity-validator}.md
│   ├── skills/{behavioral-health-um,umlite-architecture,rules-to-dmn,decompose-transaction}/
│   │            SKILL.md + references/ + scripts/
│   ├── commands/{modernize,validate,report}.md
│   └── settings.json
├── coordinator.py  config.py  hooks.py  hooks_cli.py  session.py  report.py
├── tools_reference.py  tools_legacy.py  tools_emit.py
├── gap_register.py  seam_map.py  rules_ir.py  dmn_writer.py  bpmn_writer.py
├── screen_inventory.py  route_writer.py
├── observability/{tracer.py, metrics.py}
└── evaluation/{test_suite.py, test_cases.json}
```

```
bh-um-lite/                       (generated -- the ONLY path write_artifact may target)
├── apps/
│   ├── bh-case-svc/          (Spring Boot: entity, repo, outbox, consumer, worker, migrations)
│   ├── bh-intake-svc/        (NestJS: DTO, controller, service, producer)
│   └── bh-intake-ui/         (Angular: routes, guards, worklist, case detail, review, consent)
├── camunda/{bh-prior-auth.bpmn, bh-loc-decision.dmn}
├── libs/{domain,events,ui}/
├── infra/{db,helm,k8s,gateway}/
├── tests/
├── artifacts/                (runtime: gap_register.json, seam_map.json, screen_inventory.json,
│                              rules_ir.json, session_state.json)
├── modernization_audit.jsonl (runtime)
├── docker-compose.yml
└── nx.json
```

## Acceptance Criteria

- All Python files import from `claude_agent_sdk` only — no `client.messages.create()` anywhere
  outside `appendix/manual-loop.py`
- `pytest tests/ -v` passes 100%
- `python evaluation/test_suite.py` scores ≥ 22/24 (≥ 20/22 for phase 9A alone)
- `docker compose up` completes phases 1–6 unattended, then **stops** at the finalization gate
- The gap register contains at least four `must-build-new` and at least one `must-not-port` entry,
  each with cited evidence
- No emitted log statement, event payload, or search-index mapping carries clinical narrative
- No authorization exists in the emitted schema without a corresponding consent record
- Every screen in the inventory has a reachable route, and no rule extracted from a view remains in a
  template
- `modernization_audit.jsonl` has one entry per tool call, with no credentials and no narrative
- `trace.jsonl` has one span per delegated unit of work, and `metrics.json` reports
  `automated_pct` over emitted-plus-queued; no span, metric or log line carries clinical
  narrative, consent text or a credential
- Attempting any write against either source tree is denied and logged
- **The donor's own definition of done holds**: for any generated decision path, you can explain how
  it would produce an incorrect utilization decision and who owns the logic

## How students use this spec

1. Read this spec alongside `solution/` — the solution is the reference, not the destination.
2. Run `/generate-from-spec spec/agent-spec.md`, writing into `generated/`.
3. Diff `generated/` against `solution/`. Where they differ, decide which is right and why.
4. Iterate: add the appeals sub-process to *the spec*, regenerate, and watch the workspace absorb it
   without you editing eight files by hand.
