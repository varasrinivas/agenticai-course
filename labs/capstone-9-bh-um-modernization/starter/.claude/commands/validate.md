---
description: Run the parity validator against the emitted workspace and report the nine checks without changing anything.
argument-hint: "[--check 1-9] [--phase 9a|9b|all] [--strict]"
---

Run `parity-validator` over `bh-um-lite/` and the legacy source. Read-only: this command reports,
it does not fix.

`--check N` runs one check. `--phase 9a` skips check 8, which belongs to the frontend phase.
`--strict` treats a suspicious clean result as a failure rather than a warning.

## The nine checks

1. Rules divergence against the golden set
2. Protected-content leak scan across every emitted sink
3. Narrative round-trip — intake to column to response
4. Consent atomicity — state **and** enforcing mechanism
5. Workflow — loop, timer, escalation, candidate group
6. Decision table — denial reachable, diagnosis input, hit policy stated, rationale persisted
7. Identity — the right join key, both identifiers carried
8. Screen coverage — routes reachable, view rules relocated, components consumed *(phase 9B)*
9. Feature-flag classification — no regulatory control behind a flag

## Reading the result

**Checks 1–4 are the four a naive port trips.** A clean result from one of them is not a problem by
itself — a good port comes back clean on all four.

What matters is whether the check **could have fired**. Each reports what it scanned; a clean check
that scanned nothing did not run. When one is clean and suspicious, this is what to suspect:

| Clean check | First thing to suspect |
|---|---|
| 1 rules divergence | The golden set does not include a case at the overlap boundary |
| 2 leak scan | The scan looked at one event payload, not all of them, or missed structured-logging fields |
| 3 narrative round-trip | It asserted on the DTO rather than the persisted column |
| 4 consent atomicity | It checked current state and not whether anything enforces the invariant |

Report each check's count and evidence. Do not summarise a finding into a note — the point of the
number is that someone has to decide about it.
