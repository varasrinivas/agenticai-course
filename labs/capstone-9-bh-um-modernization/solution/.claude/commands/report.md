---
description: Render the modernization report — gap register, seam map, rules divergence, manual-review queue, coverage and cost — as HTML and JSON.
argument-hint: "[--format html|json|both] [--open]"
---

Render `modernization_report.html` and `modernization_report.json` from the run's artifacts and
the audit log. Read-only.

## Sections, in this order

1. **The gap register.** First, because it is the deliverable. Grouped by verdict, with
   `must-build-new` and `must-not-port` at the top and every entry showing its cited evidence.
   Each `must-not-port` entry shows its named harm.
2. **Backlog cross-check.** The three lists: agreements, we-found-they-did-not,
   they-list-we-missed. Agreements are the strongest findings in the report — the platform team
   independently reached the same conclusion.
3. **Rules divergence.** Every case where the emitted engine disagrees with the legacy one, with
   both answers and the legacy branch taken. Each divergence classified: hit-policy artefact,
   unconverted layer, misclassified branch, or deliberate correction.
4. **The seam map**, with what replaces the atomicity at every seam crossed. A seam with no stated
   replacement is rendered as an error, not omitted.
5. **Protected-content scan.** Every sink, with the count going in and coming out. If the emitted
   system has more sinks than the legacy one and the same content reaches them, say so in those
   words.
6. **The manual-review queue.** Everything the agents refused to convert, with the specific
   question each needs answered.
7. **Screen coverage.** Every legacy screen, its route, and every rule extracted from a view with
   where it landed.
8. **Coverage and cost.** Percentage automated, items queued, tokens, wall time.

## The number that matters most

**Percentage automated is not the headline, and a high one is not good news.**

This system contains branches nobody can explain — a flag whose ticket body is four words, set on
hundreds of live rows. The correct handling is the manual-review queue.

So render coverage as a pair: *automated* and *queued for human decision*, side by side, with the
queue first. **A run reporting 100% automated has guessed at something, and the report should say
so in place of the number.**

## Tone

This report is read by someone deciding whether to approve a modernization that changes how
medical necessity determinations are made. Write for that reader.

State findings plainly. Do not soften a `must-not-port`. Do not describe an unresolved divergence
as a note. If the run is not ready, the report's first line says it is not ready and why.
