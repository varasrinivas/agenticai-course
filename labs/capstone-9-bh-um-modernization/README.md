# CAPSTONE-9 — Behavioral Health UM Modernization

**Difficulty: 5/5 · 14–18 hours · SDK Tier 3 (`claude-agent-sdk`, spec-driven)**

Build an agent that modernizes a legacy behavioral-health utilization-management monolith onto a
modern distributed platform — and that reports where the modern platform is **not good enough**
for the new domain.

---

## The one-sentence version

You have a clinical prior-auth platform that works, and a behavioral-health system that does not
run on it. Porting one onto the other is not a translation exercise, because behavioral health
asks questions the clinical platform has never had to answer.

The deliverable is a working repository **and a gap register**.

---

## Two source trees, both read-only

| Tree | What it is | Role |
|---|---|---|
| `reference-umlite/` | The clinical utilization-management platform: Nx monorepo, NestJS + Spring Boot + Angular, Kafka, Camunda BPMN/DMN, Flyway, transactional outbox | **Architecture donor.** Copy its conventions |
| `bhauthtrack/` | BHAuthTrack 4.2 — Java 8 / Spring MVC 4.3 / JSP on Tomcat 8 over Oracle 11g. One WAR, deployed 2011, last schema change 2016 | **Domain donor.** Recover the rules from it |

Both are **read-only, enforced in code** — a `PreToolUse` hook returns `PermissionResultDeny` on
any write. They are evidence. If the agent could edit them, the parity validator would be
comparing the port against a moving target.

Everything the agent produces goes to `bh-um-lite/`, and nowhere else.

---

## Why this is not a transpiler exercise

The reference platform describes itself as a *"clean-room learning rebuild."* It is deliberately
thin, and the thinness is invisible until you point a new domain at it:

| Reference platform | Fine for medical prior auth | Fatal for behavioral health |
|---|---|---|
| Two tables, zero foreign keys | One case, one decision | Concurrent review has nowhere to live |
| `notes` validated, then discarded | Nobody reads it | It is the medical-necessity evidence **and** the Part 2-protected content |
| A decision table that cannot output `DENIED` | Denials are rare and manual | Denials are the regulated event, and parity requires each to trace to a published criterion |
| A one-shot process, review task with no assignee | Correct | No continued-stay loop; the "only a physician may deny" rule vanishes |
| No audit table, no actor, no transition history | Deferred | 42 CFR Part 2 requires an accounting of disclosures |
| Authentication-only security, off by default | Deferred | No way to scope a consent-limited disclosure |
| Zero tests; CI runs `npm test --if-present` | — | Nothing catches any of the above |

None of that is a defect *for the slice it teaches*. Every one is fatal here. **Detecting that is
the capstone.**

The reference platform's own backlog independently lists guarded transitions, decision audit,
extended criteria, an appeals path and SLA timers as planned-and-unbuilt. The `gap-analyst`
subagent cross-checks its register against that backlog: agreement is signal, disagreement is
something to investigate.

---

## Skills or agents? Both, with a hard split

This is a real design decision and one of the lab's learning objectives.

| Layer | Mechanism | Why |
|---|---|---|
| BH domain knowledge — ASAM, LOCUS, code sets, 42 CFR Part 2, parity | **Skill** `.claude/skills/behavioral-health-um/` | Coordinator *and* every subagent load the same knowledge on demand. One source of truth; bundled references stay out of context until needed |
| Target house style — Nx layout, Flyway naming, event envelope, the flag idiom | **Skill** `.claude/skills/umlite-architecture/` | This is what makes the output look like the donor rather than like generic Spring Boot |
| Mechanical recipes — rules→DMN, decompose a transaction | **Skills** + bundled `scripts/` | Same steps every time, run N times. Runbooks, not decisions |
| Orchestration — phase sequencing, fan-out, per-file context isolation, read-only enforcement, the PHI gate, the HITL gate, cost ceiling, traces | **Agent SDK** | Skills cannot orchestrate, isolate context, or block a tool call |

**The rule of thumb: Skills carry knowledge and recipes; agents carry control flow and safety.**
Runbook → Skill. Decides, branches, parallelizes, or blocks → agent.

---

## No PHI in prompts, ever

The agent reads a system whose most valuable content is substance-use-disorder clinical
narrative. That constraint is first-class here, not a footnote:

- Every fixture in `bhauthtrack/` is **synthetic**, generated from documented seed `20260822`.
  Codes are real and correctly formatted; the people are not.
- A `PreToolUse` hook scans every tool result **before it reaches the model** and denies or
  redacts narrative-shaped content from files not on the synthetic allowlist.
- `tests/test_no_phi_in_prompt.py` plants a realistic-looking narrative and asserts the hook
  fires.

The question the lab is really teaching: *how do you point an agent at a regulated codebase
without feeding it regulated data?*

---

## Two phases

Both share one `spec/agent-spec.md`, one gap register, one lab folder.

- **9A — Backend and workflow** (10–12 h). Rules extraction, the decomposition, the process
  model, the Part 2 controls. Ends green at the HITL gate.
- **9B — Frontend** (4–6 h). JSP screens → Angular routes. Gated on 9A being green, because the
  screen inventory and the rules-found-in-views list are its inputs.

---

## Where to start reading

Read `bhauthtrack/` before you write any agent code. Its own `README.md` names the five files
that matter and the order to read them in. Then:

1. `spec/agent-spec.md` — the twelve-section contract the whole lab implements
2. `bhauthtrack/db/02_seed.sql` — the golden set. Each authorization exercises one branch of the
   ladder and states its expected outcome
3. `reference-umlite/VENDORED.md` — what the donor does and does not have

---

## Setup

```bash
cd labs/capstone-9-bh-um-modernization
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# The vendored donor ships without node_modules. Angular was never installed in the
# upstream checkout either -- no @angular packages, no `ng` binary -- so this step is
# required before anything in 9B will build.
cd reference-umlite && npm install && cd ..
```

`bhauthtrack/` needs no build. It is read, never run — there is no Oracle instance in this lab
and no Tomcat. The SQL is a specification, not a database.

---

## Verification

```bash
pytest tests/ -v                                        # 219 tests
python solution/evaluation/test_suite.py --phase 9a     # >= 18 / 20
python solution/evaluation/test_suite.py                # >= 20 / 22 (both phases)
```

**Four parity checks are the ones a naive port trips**: rules divergence, protected-content leak,
narrative round-trip, consent atomicity.

A clean result from one of them is **not** a problem by itself — a good port comes back clean on
all four, and a check that could never pass is a check people learn to ignore.

What matters is whether the check **could have fired**. Every check reports what it *scanned*, and
a clean result is flagged suspicious only when it scanned nothing, or when its inputs cannot
exercise what it is for:

| Check | When a clean result proves nothing |
|---|---|
| rules divergence | The case set has no case at the ASAM 3.5/3.7 overlap boundary — the one input that separates a hit-policy decision from a lucky guess |
| protected-content leak | Nothing was emitted, so nothing was scanned |
| narrative round-trip | It asserted on the DTO rather than the persisted column |
| consent atomicity | It checked current state and not whether anything *enforces* the invariant |

And one that must always report **zero**: `test_no_phi_in_prompt.py`.

---

## The deliberate dead end

`BH_AUTH.LEGACY_OVERRIDE`, added under BHA-2291 in 2013. The ticket body reads, in full, *"per DM
request"*. It is handled in two places and set on roughly 400 live rows. Nobody at Bridgeway can
say what it means.

It belongs in the manual-review queue. **A modernization that reports 100% automated coverage has
guessed at it, and that is a failing run.**

---

## Regulatory note

The 42 CFR Part 2 and MHPAEA parity behaviour modelled in this lab is an **educational
simplification** — enough to make the architectural point, not enough to build a compliance
programme on. It is not legal advice.

---

## Working through it

`starter/` mirrors `solution/` with **31 numbered TODOs**. List them in order:

```bash
grep -rn "TODO [0-9]" starter/ | sort -t' ' -k3 -n
```

They are ordered deliberately. TODOs 1–6 are the two rule engines, because the divergence check is
what makes every later phase measurable — until both engines run you cannot tell a correct
conversion from a lucky one.

| TODOs | What |
|---|---|
| 1–6 | The legacy ladder, the second rules layer, and the decision-table engine |
| 7–12 | The gap register's constraints and the seam map's refusals |
| 13–18 | The five guardrails |
| 19–21 | The tools that produce output |
| 22–24 | The DMN and BPMN writers, and what they refuse to emit |
| 25–27 | The parity checks |
| 28–31 | Phase 9B: screen inventory, route writer, screen coverage |

`.claude/` — the four skills, eight subagents, three commands and `settings.json` — is **given
whole**. Writing a skill from a blank file teaches nothing; reading four good ones and then
writing a fifth teaches a lot. `condition.py`, `session.py` and `observability/` are given too:
they are plumbing, not the lesson.

Check your work without spending a token:

```bash
pytest tests/ -v
python solution/evaluation/test_suite.py --self-check
```

`starter/` is generated from `solution/`, so it cannot drift:

```bash
python solution/make_starter.py --check    # fails if stale
```

## Deploying

`deploy/` has three tiers; tier 1 is the lab and needs only Docker.

```bash
cp solution/.env.example solution/.env      # add your ANTHROPIC_API_KEY
docker compose up --build
```

Read `deploy/README.md` before either cloud tier. The constraint that shapes every deployment
decision is **"no PHI in prompts, ever"**, and it gets *harder* in the cloud — a redacted log line
that reaches Cloud Logging or CloudWatch has been copied into a system with its own retention and
its own export sinks.

## The appendix

`appendix/manual-loop.py` is the only file in this capstone that calls `client.messages.create()`.
It exists so you can see the loop the SDK runs on your behalf — and, more usefully, see where the
guardrails have to go when there is no `can_use_tool` to put them in. Read it once. Then use the
SDK.
