---
name: rules-to-dmn
description: Convert one block of imperative rules — a PL/SQL ladder, a Java if/else chain, or both together — into a DMN decision table with a justified hit policy and a completed overlap analysis. Use once per rules block; run the bundled overlap checker before emitting the table.
---

# Imperative rules → DMN decision table

A runbook. Same steps every time, one rules block per run.

The output is not just a table. It is a table **plus** an overlap analysis **plus** a written
justification for the hit policy. A table without those three is not finished, because the hit
policy is where the meaning of the original code either survives or quietly dies.

---

## Step 1 — Read both layers before you convert either

Rules are commonly split. Some live in a database package; some live in application code that runs
*after* the package has already committed to an outcome. **Neither layer alone is the rule set.**

Establish, in writing, before converting anything:

- Which layer runs first?
- Can the second layer **upgrade** the first layer's decision, or only downgrade and pend? (Almost
  always the latter, because the first layer has already returned.)
- Does the second layer read data the first one did not — accumulators, capacity tables, counts?
  Those are inputs to the merged rule set and they may not be in the same database.

Write this down as the IR's `layers` block. If you convert one layer and call it done, every case
that the other layer touches will diverge, and it will diverge *plausibly*.

## Step 2 — Classify every branch

Walk the source top to bottom. Each branch is one of two kinds, and the distinction is the whole
translation:

| Kind | Shape | Becomes |
|---|---|---|
| **Committing** | Sets an outcome and `RETURN`s / `return`s | A row in the decision table |
| **Accumulating** | Adjusts a running value and falls through | **Not a row.** An input expression |

An accumulating branch is not a rule — it is part of how an input is computed. Emitting one as a
table row is the most common way to produce a table that is subtly, permanently wrong.

Record for each branch: id, kind, condition, effect, and whether it can be reached at all.

### The running score

If the source mutates a score across accumulating branches, that score is a **derived input** to
the table, not an output. Model it as an input expression — a FEEL expression, or a computed field
the caller supplies — and document the arithmetic that produces it.

Do not try to express "score" as a sequence of table rows. It is not a decision; it is a number.

## Step 3 — Run the overlap checker

```bash
python scripts/dmn_overlap.py --ir artifacts/rules_ir.json --report artifacts/overlap.md
```

It enumerates every pair of committing rows and reports pairs that can both match the same input,
with a concrete witness input for each. Do not reason about overlap by inspection — the checker
finds pairs that look disjoint because their conditions are on different variables.

**An overlap is not a bug in the legacy code.** In a first-match ladder, overlapping conditions
plus ordering *is* the rule. The overlap only becomes a problem when you flatten the ordering
away.

## Step 4 — Choose a hit policy, and justify it

For each overlapping pair, work out what each candidate policy would produce:

| Policy | On an overlapping row | Use when |
|---|---|---|
| `FIRST` | First matching row, in table order | The source was a first-match ladder **and** you can guarantee row order survives every downstream tool |
| `UNIQUE` | **Runtime error** — two rules matched | You have eliminated overlaps by tightening conditions, and want to be told loudly if you missed one |
| `PRIORITY` | The match whose *output* ranks highest in a declared priority list | Ordering is a property of the outcome, not of the rows |
| `ANY` | The single output all matches agree on; error if they differ | Overlapping rows exist but always agree |
| `COLLECT` | Every match | The caller decides, and there is a real caller who can |

### The default recommendation, and when to depart from it

Prefer **`UNIQUE` with tightened conditions** over `FIRST`.

Converting a first-match ladder to `FIRST` preserves behaviour only as long as row order survives
— through file edits, through a modeller UI that reorders on save, through a merge. Nothing
enforces it and nothing tests it. It is a correct translation resting on an invariant you cannot
check.

Tightening conditions makes the overlap explicit. In the classic case where one row is
`score >= 10 AND dim1 >= 3 → 3.7` and the next is `score >= 8 → 3.5`, the second row's real
condition — the one that reproduces the ladder — is:

```
score >= 8 AND NOT (score >= 10 AND dim1 >= 3)
```

That is uglier and it is honest: the exclusion was always there, encoded as position. Now it is
encoded as a condition, `UNIQUE` will error if you ever break it, and the table means the same
thing on the day someone drags a row.

**Choose `FIRST` instead when** the ladder has many rows whose negations would compound into
unreadable conditions, or when the ordering genuinely reflects clinical priority that a reviewer
should be able to read off the table. If you do, add a test that asserts row order.

**Never leave the policy unstated.** DMN defaults to `UNIQUE`, so an unstated policy on an
overlapping table is a production error waiting for the first case that matches two rows.

## Step 5 — Check the outputs are complete

Two failures recur:

- **A missing outcome.** If the target platform's example table has no `DENIED` output and you
  mirror its shape, you have built an engine that cannot deny. Enumerate the outcomes the *source*
  can produce and make sure each is reachable.
- **A missing reason.** An outcome without a criterion-traceable reason code cannot be explained
  to the person it was applied to. Carry the reason code, and carry the rule path if the source
  produces one.

Also check what the source deliberately **does not** output. If the legacy engine pends rather
than denying when clinical criteria are not met, that is a separation-of-duties rule, not a
missing feature — reproducing it as a denial removes a control. Distinguish "the engine cannot
deny" from "the engine must not deny here".

## Step 6 — Emit and verify

Emit the table with `write_artifact`, then verify with the golden set:

```bash
python scripts/dmn_overlap.py --verify artifacts/rules_ir.json --golden ../bhauthtrack/db/02_seed.sql
```

**A non-zero divergence on first run is the expected result**, not a failure. Read each divergence
and classify it:

| Divergence is | Then |
|---|---|
| A hit-policy artefact | Fix the policy or the conditions |
| A layer you did not convert | Go back to step 1 |
| A branch you classified as committing that accumulates (or vice versa) | Fix step 2 |
| A deliberate correction of legacy behaviour | **Record it in the gap register.** Do not silently "fix" a rule |

A zero divergence on the first run usually means the golden set does not exercise the overlap, not
that the conversion is perfect.

## Step 7 — Queue what you could not convert

A branch on an undocumented flag, a threshold with no provenance that you would have to guess at,
a rule flagged by compliance and never actioned — these go to `queue_manual_review` with the
source quoted and the specific question stated.

**A refusal with a reason is a useful output. A confident wrong translation is not.** A conversion
reporting 100% automated coverage over a system with undocumented branches has guessed at them.

---

## IR shape

```json
{
  "block": "PKG_LOC_RULES.EVAL_LOC + LocRulesService.evaluate",
  "layers": [
    {"name": "plsql_ladder", "order": 1, "can_upgrade": true,
     "source": "db/03_PKG_LOC_RULES.sql"},
    {"name": "java_adjustments", "order": 2, "can_upgrade": false,
     "source": "service/LocRulesService.java",
     "extra_inputs": ["benefit_accumulator", "rolling_denial_count", "bed_capacity"]}
  ],
  "inputs": [
    {"name": "score", "type": "number", "derived": true,
     "expression": "sum of accumulating branches B1,B2,B3,B4,B5,B6"},
    {"name": "dim1", "type": "number", "source": "assessment dimension 1"}
  ],
  "branches": [
    {"id": "B2", "kind": "accumulating", "condition": "cssrs >= 4", "effect": "score += 6"},
    {"id": "B7a", "kind": "committing", "condition": "score >= 10 and dim1 >= 3",
     "outputs": {"outcome": "APPROVED", "loc": "3.7", "units": "min(requested, 10)"}}
  ],
  "hit_policy": "UNIQUE",
  "hit_policy_justification": "…",
  "overlaps": [
    {"rows": ["B7a", "B7b"], "witness": {"score": 10, "dim1": 3},
     "under_first": "3.7", "under_unique": "ERROR", "under_collect": ["3.7", "3.5"],
     "resolution": "B7b tightened with NOT(B7a)"}
  ],
  "unconverted": [
    {"id": "B0", "reason": "branches on an undocumented flag", "queued": true}
  ]
}
```
