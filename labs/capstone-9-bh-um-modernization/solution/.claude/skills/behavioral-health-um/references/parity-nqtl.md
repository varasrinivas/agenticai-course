# MHPAEA parity and non-quantitative treatment limitations

**Educational model, not legal advice.**

## The rule in one sentence

A limitation a plan applies to behavioral-health benefits may be **no more restrictive** than the
comparable limitation it applies to medical/surgical benefits — both as written and **as applied**.

## Quantitative vs non-quantitative

**Quantitative** limitations are numeric and easy to compare: visit caps, day limits, copays,
deductibles. A 20-visit cap on BH therapy where medical has none is a parity problem visible from
the benefit document.

**Non-quantitative treatment limitations (NQTLs)** are the hard ones, because they live in
*process* rather than in numbers:

| NQTL | What to look for in code |
|---|---|
| Prior-authorization requirements | Which services require review at all |
| **Concurrent review frequency** | How often continued stay is re-reviewed |
| Medical-necessity criteria strictness | Threshold values in the rules engine |
| **Step-therapy / fail-first** | "Try outpatient before residential" logic |
| Provider network admission standards | Credentialing and network-adequacy rules |
| Reimbursement methodology | Fee schedules and rate-setting |
| **Frequency-based triggers** | "Three prior denials pends the case" |
| Geographic or facility-type limits | Network-adequacy step-downs |

The comparative analysis a plan must be able to produce asks, for each NQTL: what is the
med/surg analogue, and is this one more restrictive in writing or in practice?

## Where this bites during a modernization

Legacy BH systems accumulate rules that were reasonable when written and that have **no
med/surg counterpart**. Three shapes recur:

1. **A frequency trigger.** "Three or more adverse determinations in a rolling year pends the
   case for a medical director." Nobody applies that to a member with three denied MRIs.
2. **A network-adequacy step-down.** "If no in-network facility at this level has capacity, step
   down one level rather than authorise out-of-network." The med/surg side would authorise
   out-of-network.
3. **A tighter review cadence than clinical guidelines require**, applied because BH is
   perceived as higher-utilization.

Each looks like ordinary business logic in the file you find it in. Each is potentially an NQTL
applied to behavioral health alone.

## What to do when you find one

**Neither port it silently nor drop it silently.** Both are wrong, and in opposite directions:

| Action | Consequence |
|---|---|
| Port it forward | The exposure moves to the new system, now with better logging |
| Drop it | Outcomes change for real members, with no clinical review of that change |
| **Escalate it** | Correct |

Use `queue_manual_review` and include, concretely:

- the rule, quoted from source, with its file and line
- what triggers it and what it does
- whether any med/surg analogue exists in the material you can see
- **any comment in the source suggesting it was already flagged** — a compliance note that was
  never actioned is the single most valuable thing you can surface, because it means someone
  already reached this conclusion and the organisation lost track of it

## An unactioned compliance note is evidence

You will sometimes find something like:

```java
// PARITY NOTE (added by compliance, 2016, never actioned):
// "The medical side does not apply an equivalent frequency-based
//  pend to med/surg requests. If we keep this we need a
//  comparative analysis on file."
```

Do not treat that as a stale comment. Treat it as a finding that was raised, understood, and
dropped — which is a much stronger signal than one you inferred yourself, and it belongs in the
gap register with the comment quoted verbatim and its date.

## Parity and the denial path

Parity also constrains **how** a denial is issued, not just whether. Each adverse determination
should trace to a **published, applied criterion** — which is why a decision engine that cannot
produce a denial with a reason code is a parity problem and not merely a feature gap.

A modernized decision table that:

- has no `DENIED` output at all, or
- can deny but produces no criterion-traceable reason, or
- discards the rule path that shows which criteria were applied

leaves the organisation unable to answer the comparative question for any individual case. Record
that as `must-build-new`, not as a nice-to-have.
