---
description: Run the six-phase modernization — map, excavate, extract rules, gap-analyse, synthesize, validate — stopping at the human approval gate.
argument-hint: "[--phase 9a|9b|all] [--resume]"
---

Run the modernization coordinator.

Phases, each starting only after the previous one reports success:

| # | Phase | Agent(s) | Produces |
|---|---|---|---|
| 1 | Map | `architecture-cartographer` | `architecture-manifest.json` |
| 2 | Excavate | `monolith-archaeologist`, `jsp-archaeologist` | `domain-model.json`, `seam-map.json`, `screen-inventory.json` |
| 3 | Extract rules | `rules-extractor` | `rules-ir.json` |
| 4 | Gap-analyse | `gap-analyst` | `gap-register.json` |
| 5A | Synthesize backend | `repo-synthesizer` | `bh-um-lite/apps`, `camunda`, `libs`, `infra` |
| 5B | Synthesize frontend | `frontend-synthesizer` | `bh-um-lite/apps/bh-intake-ui` |
| 6 | Validate | `parity-validator` | `parity-report.json` |

`--phase 9a` stops after phase 6 on the backend. `--phase 9b` requires a green 9A and runs 5B and
the screen-coverage half of 6. Default is `all`.

`--resume` picks up from the last completed phase using the session state.

## What you do as coordinator

**Sequence and report. Do not read source files yourself.** You have no file tools, deliberately —
every read goes through a subagent with its own context, so one phase's reading does not crowd out
the next phase's reasoning.

Between phases, check the previous phase actually produced what it was supposed to. An agent that
reports success having written an empty artifact should stop the run, not advance it.

## Where the run is allowed to stop

- Three consecutive subagent failures in one phase — halt.
- Cumulative output tokens past the ceiling — halt.
- Phase 4 producing a register with no `must-build-new` entries — halt and say so. That result
  means the analysis did not happen, not that the platform is complete.
- Phase 6 reporting a clean result on checks 1–4 — do **not** treat as success. Report it as
  suspicious and name which check to re-examine.

## The end of the run is not the end of the work

The run finishes by calling `finalize_modernization`, which **always denies**, returning the gap
register, the rules divergence table and the protected-content scan for a human to read.

That is the design. The agent cannot approve its own modernization. Report the denial as the
expected outcome, summarise what the human needs to decide, and stop.
