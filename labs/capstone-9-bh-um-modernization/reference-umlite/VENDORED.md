# Vendored reference platform

This directory is a **trimmed copy** of the clinical utilization-management platform that serves as
this capstone's **architecture donor**. It is checked in so the lab is portable — the original lives
outside this repository and the lab must not depend on an absolute path on one machine.

**Excluded from the copy**: `node_modules/`, `.git/`, `dist/`, `target/`, `package-lock.json`,
Maven wrapper files. 93 files, ~308 KB.

## This tree is read-only

The agent's `PreToolUse` hook denies every write against this path, enforced in code rather than by
convention. This tree is *evidence*. If the agent could edit it, the parity validator would be
comparing the port against a moving target.

## Do not mistake this for a production system

The platform describes itself as a *"clean-room learning rebuild."* It is a teaching codebase, and
it is deliberately thin. Before using it as a template, know what it does **not** have:

| Area | Actual state |
|---|---|
| Schema | Two tables, **zero foreign keys**. No member, provider, or reference tables |
| Free-text clinical field | The intake DTO validates `notes`, then **discards it** — not a column, not an entity field, not in either event payload |
| Decision table | Three rules, first-hit. **No rule can output `DENIED`.** No diagnosis input. One row is dead code (identical output to the default) |
| Workflow | One-shot: start → decide → gateway → notify → end. No loop, no timer. The manual-review task has **no assignee and no candidate group** |
| Audit | **None.** No audit table, no `createdBy`/`updatedBy`, no status-transition history. `transitionTo()` is unguarded |
| Authorization | Off by default; even enabled it is authentication-only — no roles, no scopes, no method security |
| PHI handling | Member identifiers logged in cleartext; event payloads carry member and diagnosis as plain JSON on an unauthenticated broker; no TLS anywhere |
| Tests | **Zero.** CI runs `npm test --if-present`, so their absence never fails the build |
| Event contracts | Hand-mirrored in three copies, no schema registry. One declared topic has no producer and no consumer. One status enum value is never assigned |

None of this is a defect *for the medical prior-auth slice it teaches*. Every one of it is fatal for
behavioral health. **Detecting that is the capstone.**

The platform team knows: their own `leadership/backlog-um-enhancements.md` (not vendored here — the
agent reads it through `ref_read_backlog`) lists guarded status transitions, decision audit, extended
decision criteria, an appeals path, and turnaround-time timers as *planned and unbuilt*. The
`gap-analyst` subagent cross-checks its register against that backlog. Agreement is signal;
disagreement is something to investigate.

## Build state

The upstream checkout had **Angular dependencies uninstalled** — `node_modules` held only the NestJS
side, with no `@angular` packages and no `ng` binary, so `ng build` and `ng serve` did not run there.
Nothing is broken; the standalone bootstrap is correct. But it means:

- The lab's setup step must run `npm install` at this directory's root before anything is built.
- No `expected_output/` fixture may claim a UI screenshot, because none has ever been produced.

**Verified for this vendored copy** (2026-08-22, npm 11.2.0 / node 22.14.0): `npm install --dry-run`
at this root resolves the full workspace — **1345 packages**, including the Angular 18 app and its
`@angular/cli` toolchain. The manifests are coherent and installable. `node_modules/` is
`.gitignore`d here and is deliberately not committed; the setup step installs it.

### One detail worth carrying into the gap register

`apps/intake-ui/package.json` declares **`@angular/router` as a dependency** — and
`app.config.ts` provides only `provideHttpClient()`, with no `provideRouter`. The router was
installed and never wired up. That is not a bug to fix in the donor; it is evidence about how far
the reference frontend actually got, and it belongs in the register next to the three orphaned
`libs/ui` components.

## The one trait worth copying wholesale

Capability layering behind feature flags — `EVENTS_ENABLED`, `OUTBOX_ENABLED`, `WORKFLOW_ENABLED`,
`CACHE_ENABLED`, `SEARCH_ENABLED`, `REPLICA_ENABLED`, `SECURITY_ENABLED`. It is what lets the
platform teach one capability at a time and stay runnable at every step.

Mirror the idiom. But classify each flag before you do: a cache flag and a consent-enforcement flag
are not the same kind of thing, and a regulatory control that can be switched off in configuration is
not a control.
