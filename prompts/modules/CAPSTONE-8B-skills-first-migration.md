# CAPSTONE-8B: Legacy Migration Agent — Skills-First

**Track:** Bonus / Legacy Modernization · **Difficulty:** 5/5 · **Time:** 8–10 hours
**SDK Tier:** 3 (`claude-agent-sdk`, spec-driven)
**Lab:** `labs/capstone-8b-skills-first/`
**Output:** `output/courses/claude-agents/CAPSTONE-8B-skills-first-migration.html`
**Prerequisite:** CAPSTONE-8. This capstone is a comparison and needs a baseline.

---

## What makes this a capstone and not a refactor

Capstone 8 solves the Oracle → PostgreSQL migration with a coordinator plus five subagents.
Three of those five are not delegation — they are rulebooks with a context window attached.

8B rebuilds the identical problem with **Agent Skills** and then **measures** which architecture
did better. The measurement is the deliverable. The page must never claim skills are simply
better; it must teach the reader to tell when each shape is right.

**The thesis, stated once so the page can keep returning to it:**

> Skills are knowledge loaded *into* the current context. Subagents are work delegated *to* a
> separate one. Collapsing five subagents into one context buys shared knowledge and costs
> independence — and the phase that needs independence most is validation.

---

## Business Context

Reuse Capstone 8's verbatim: Meridian Public Records, 11-state UCC filing system, Oracle since
2003, 6 TB, $1.4M/yr licence, both PL/SQL authors retired in 2021. Systems integrator quoted
14 months and $2.1M.

Do **not** re-teach the domain at Capstone 8 length. The reader has done Capstone 8. One tight
recap paragraph, then get to the architecture question.

---

## What the Student Builds

Five skills under `.claude/skills/`, each with `SKILL.md` + `references/` + `scripts/`:

| Skill | Replaces | Bundled script | Loaded by |
|---|---|---|---|
| `oracle-pg-typing` | `schema-translator` + `type_mapping.py` | `check_mapping.py` | schema |
| `plsql-conversion` | `plsql-converter` | *(borrows the scanner)* | code |
| `appsql-rewriting` | `appsql-rewriter` + `oracle_constructs.py` + the `scan_app_sql` MCP tool | `find_oracleisms.py` | code |
| `nullability-preservation` | knowledge duplicated in **two** subagent prompts | `compare_nulls.py` | **data + validate** |
| `migration-validation` | `migration-validator` + `validation.py` | `compare_checksums.py` | validate |

Plus a single-context `coordinator.py` carrying `PHASE_SKILLS`, and
`evaluation/architecture_comparison.md`.

### The three things the page must land

1. **`nullability-preservation` is loaded by two phases.** In Capstone 8 that rule was
   copy-pasted into `data-migrator.md` and `migration-validator.md`, free to drift. One shared
   file is the concrete reuse argument. `tests/test_skills_wellformed.py` asserts the sharing.

2. **`scan_app_sql` moved from MCP tool to skill script.** An MCP tool sits in every request's
   tool list whether the phase needs it or not, and its rationale lives somewhere unlinked. A
   skill script loads with its skill, beside the file explaining when to run it.
   `write_artifact` *stays* a tool — it is a capability, not knowledge, and its confinement
   boundary must hold in phases where no skill is loaded.

3. **Hooks and guardrails are byte-identical.** They sit between the agent and the tools, so
   reorganising knowledge does not touch them. Show this as a *result*.

---

## SKILL.md accuracy — non-negotiable

Frontmatter fields Claude Code actually reads: **`name` and `description` required**;
`version`, `allowed-tools`, `tools`, `user-invocable`, `license`, `argument-hint`,
`disable-model-invocation` optional. `name` must match the directory.

> **`context: fork` is NOT a Claude Code skill field.** Zero of the 58 skills shipped in the
> official Anthropic plugin marketplace use it, and
> `plugin-dev/skills/skill-development/SKILL.md` lists only `name` and `description` as
> required. M25 currently teaches it — that is a separate bug. **This page must not repeat it.**

Bundled-resource layout is `scripts/` (executables), `references/` (loaded on demand),
`assets/` (used in output).

The page should teach *why* an invented key is dangerous: unknown keys are ignored silently, so
the skill behaves nothing like intended and nothing errors.

---

## Animations

Six. Reuse Capstone 8's guardrail animations unchanged — the visual point being that they did
not need to change.

1. **Two architectures, same problem** (hero). Split screen. Left: coordinator fanning to five
   isolated context boxes. Right: one context box with skills sliding in and out as phases
   advance. Same five phases run underneath both.

2. **Progressive disclosure, measured.** `SKILL.md` loads (small block); the agent hits a
   `NUMBER` with no precision; `references/number-precision.md` slides in only then. Running
   token counter beside it. Contrast with the subagent prompt, which loads whole, every time.

3. **The phase → skill map.** Five phases across; five skills down; cells light as each phase
   loads its set. `nullability-preservation` visibly lights **twice** — hold on that frame.

4. **Context growth.** Two lines over the six tables of phase 2–3. Subagent: sawtooth, resetting
   each table. Skills: monotonic climb. Do not editorialise in the animation; let the shapes
   differ and put the reading underneath.

5. **The validator problem.** Phase 5 begins. In the subagent version a fresh empty context box
   receives only the numbers. In the skills version the context already contains phases 2–4,
   shown greyed but present. Then the question on screen: *which one do you believe?*

6. **Guardrails unchanged** — reuse Capstone 8's "three guards that run before the tool does"
   verbatim, with a caption noting nothing about it changed.

---

## Sections

Follow Capstone 8's section shape. These are the ones that differ:

- **Skill or Subagent?** — the decision rule and the comparison table. Early, right after the
  brief.
- **Anatomy of a Skill** — frontmatter (with the `context:` warning), `references/`, `scripts/`,
  and the three-part structure. Show a real `SKILL.md` from the lab.
- **Progressive Disclosure, Measured** — actual token counts of `SKILL.md` vs its `references/`.
- **One File, Two Phases** — `nullability-preservation`, and the drift it prevents.
- **The Validator Problem** — the honest cost, with the comparison harness.
- **When a Skill Silently Does Not Load** — `setting_sources` + `skills`, the missing-both
  failure, and how to prove from `migration_audit.jsonl` that a script ran.
- **Measuring It Yourself** — walk through `architecture_comparison.md`, including the
  instruction to publish an unfavourable result.

Baseline numbers for the comparison section, from Capstone 8's
`expected_output/migration_report.json` (a clean second run): 118,940 output tokens, 279.4 s,
$1.78, 19 spans, 6 tables, 36 checks passed, 3 manual-review items, 19,065 rows.

**Leave 8B's column empty on the page.** Publishing invented numbers for the new architecture
would destroy the one thing this capstone teaches.

---

## Test Outline

Same 20 evaluation cases as Capstone 8 — that is what makes the scores comparable. Plus
`test_skills_wellformed.py` (45 assertions): frontmatter validity, no invented keys, description
quality, `allowed-tools` resolvable, scripts import / self-test / run standalone, references
exist, `PHASE_SKILLS` consistency, and the two-phase sharing.

Note for the page: the solution suite is 199 tests green; a fresh starter gives 39 passes and
160 failures, and those failures are the work list.

---

## Going Further (all OPTIONAL)

- Add a sixth skill (`index-strategy`) to the **spec**, regenerate, and compare the cost of that
  change against adding a sixth subagent to Capstone 8's spec.
- Run phase 5 in a fresh process (`--phase validate` alone) so it has the session file but not
  the conversation. Does independence come back? Record it.
- Hybrid: keep the four knowledge skills, restore `migration-validator` as a subagent. Measure
  whether it recovers Capstone 8's validator reliability at 8B's knowledge-sharing cost. **If
  the measurements support the hybrid, that is the right answer** — the course should not
  pretend otherwise.
