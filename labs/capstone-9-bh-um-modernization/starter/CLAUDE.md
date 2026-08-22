# Behavioral Health UM Modernization Agent

An agent that modernizes a legacy behavioral-health utilization-management monolith onto a modern
distributed platform — and reports where the modern platform is **not good enough** for the new
domain.

The deliverable is a working repository **and a gap register**. A run that produces the first
without the second has done a translation, not a modernization.

---

## The two planes

The split between them is the design decision this project exists to demonstrate, and it is not
arbitrary.

**Skills carry knowledge and recipes. Agents carry control flow and safety.**

| `.claude/skills/` — knowledge plane | What it holds |
|---|---|
| `behavioral-health-um` | ASAM and the six dimensions, concurrent review, 42 CFR Part 2, parity, code sets, the reviewer-licensure rule. Loaded by the coordinator **and every subagent** |
| `umlite-architecture` | The target platform's house style — layout, migration naming, event envelope, outbox, the flag idiom |
| `rules-to-dmn` | Runbook: one imperative rules block → one DMN table with a justified hit policy |
| `decompose-transaction` | Runbook: one `@Transactional` method → services + events, with a stated replacement for the atomicity broken |

One source of truth for the domain, loaded on demand, with bundled references that stay out of
context until needed. The alternative — pasting the ontology into eight subagent prompts — drifts
the moment one is edited and costs tokens on every turn.

| `.claude/agents/` — control plane | Phase |
|---|---|
| `architecture-cartographer` | 1 Map |
| `monolith-archaeologist`, `jsp-archaeologist` | 2 Excavate |
| `rules-extractor` | 3 Extract rules |
| `gap-analyst` | 4 Gap-analyse |
| `repo-synthesizer`, `frontend-synthesizer` | 5A / 5B Synthesize |
| `parity-validator` | 6 Validate |

Skills cannot sequence phases, isolate context per file, or block a tool call. That is what the
agents and the hooks are for.

**The test: does it decide, branch, parallelize, or block?** Then it is an agent. Is it the same
steps every time? Then it is a Skill.

## The coordinator has no file tools

Deliberately. Every read goes through a subagent with its own context window, so one phase's
reading does not crowd out the next phase's reasoning. The coordinator sequences, checks that each
phase produced what it claimed, and reports.

## Two source trees, both read-only, enforced in code

| Tree | Role |
|---|---|
| `reference-umlite/` | Architecture donor. Copy its conventions |
| `bhauthtrack/` | Domain donor. Recover the rules from it |

A `PreToolUse` hook denies every write. **They are evidence** — if the agent could edit them, the
parity validator would be diffing the port against a moving target.

Everything the agent produces goes under `bh-um-lite/`, and nowhere else. That is a hook too, not
a convention.

## No PHI in prompts, ever

The agent reads a system whose most valuable content is substance-use-disorder clinical narrative.

A `PreToolUse` hook inspects every tool result **before it reaches the model** and denies
narrative-shaped content whose source is not on the synthetic-fixture allowlist. Content from an
allowlisted fixture that exceeds the excerpt budget comes back truncated and tagged.

Every fixture in `bhauthtrack/` is synthetic, generated from a documented seed. Codes are real and
correctly formatted; the people are not. That is what makes it possible to point an agent at this
codebase at all.

## The agent cannot approve itself

`finalize_modernization` is gated and **always denies**, returning the gap register, the rules
divergence table and the protected-content scan for a human to read. A person re-runs with
`--approve`.

Borrowed from the reference platform's own definition of done, and it is the standard every
generated artifact is held to:

> *If this caused an incorrect utilization decision in production, could we explain how it
> happened and who owned the logic?*

## Four results that are supposed to be non-zero

Checks 1–4 of the parity validator — rules divergence, protected-content leak, narrative
round-trip, consent atomicity — exist to detect the four ways a faithful-looking port is wrong. A
naive port trips all four.

**If any comes back clean, suspect the validator before the port.** A false pass is worse than no
check, because it is the thing everyone downstream trusts.

## A high automation percentage is bad news

The legacy system contains branches nobody can explain — a flag whose ticket body is four words,
handled in two places, set on hundreds of live rows. The correct handling is the manual-review
queue.

**A run reporting 100% automated has guessed at something.** Coverage is reported as a pair —
automated and queued for human decision — with the queue first.

## Commands

| Command | Does |
|---|---|
| `/modernize [--phase 9a\|9b\|all] [--resume]` | Run the six phases, stop at the gate |
| `/validate [--check N] [--strict]` | Run the eight parity checks, change nothing |
| `/report [--format html\|json\|both]` | Render the modernization report |

## Layout

```
solution/               this agent
  .claude/{agents,skills,commands}/, settings.json
  coordinator.py  config.py  hooks.py  hooks_cli.py  session.py  report.py
  tools_reference.py  tools_legacy.py  tools_emit.py
  gap_register.py  seam_map.py  rules_ir.py  dmn_writer.py  bpmn_writer.py
  screen_inventory.py  route_writer.py
  observability/  evaluation/
bh-um-lite/             what the agent writes -- the only writable path
artifacts/              gap-register.json, seam-map.json, rules-ir.json, ...
modernization_audit.jsonl
```

## SDK

Tier 3. Everything imports from `claude_agent_sdk`. The only `client.messages.create()` in this
lab is in `appendix/manual-loop.py`, which exists to show what the SDK is doing and is explicitly
not for production.
