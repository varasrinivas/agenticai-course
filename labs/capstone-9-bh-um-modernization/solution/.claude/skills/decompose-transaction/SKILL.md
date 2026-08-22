---
name: decompose-transaction
description: Decompose one @Transactional service method that spans a proposed service boundary into services, events and an outbox — while stating explicitly what replaces the atomicity being broken. Use once per transactional method the seam map flags as crossing a seam.
---

# Decomposing a transaction across a service boundary

A runbook. One `@Transactional` method per run.

**The output is not the decomposition. The output is the decomposition plus a written answer to
one question:**

> The old code guaranteed these writes all happened or none did. What guarantees that now?

If you cannot answer it, you have not finished, and "we'll write the second row right after" is
not an answer.

---

## Why this is the hardest step

A monolith gets atomicity free. One database, one transaction manager, one annotation. It costs
nothing to write and it is easy to stop noticing.

Decomposed, those same writes become an HTTP call, a message, a persist in another schema, an
outbox row, another message. **Every arrow is a place the sequence can stop.** Nothing is rolled
back; there is nothing to roll back to.

The distributed system is not wrong for lacking atomicity. It is wrong if nobody noticed it was
there.

## Step 1 — Enumerate the writes, in order, with their reasons

For the method in hand, list every write: the table, what it means, and — critically — **why it is
in this transaction**.

That last column is the one that matters and the one most likely to be undocumented. Look for it
in class comments, in the commit that merged the method, in a ticket reference. When you find a
comment saying three services were merged into one in 2013 because transaction boundaries kept
producing orphaned rows, **that is the requirement**, stated by someone who hit the failure.

Example shape:

| # | Write | Meaning | Why atomic |
|---|---|---|---|
| 1 | authorization | the request itself | anchor |
| 2 | assessments | the rules engine's inputs | a decision computed from missing inputs is not reproducible |
| 3 | **consent** | the disclosure permission | **an authorization from a protected program with no consent record is content we cannot lawfully act on** |
| 4 | initial review | schedules the next review | an approval with no next review is one nobody looks at again |
| 5 | outbound queue row | the notification | a notification for a rolled-back decision, or a decision nobody is told about |

## Step 2 — Classify each pair, don't treat them all alike

Not every pair in one transaction needs the same guarantee. Sort them:

| Class | Meaning | Mechanism |
|---|---|---|
| **Must be atomic** | One existing without the other is unsafe or unlawful | **Keep in one service, one transaction.** Do not split |
| **Must be eventually consistent, guaranteed** | Order matters, the gap is tolerable, but it must close | Transactional outbox + idempotent consumer |
| **Must be eventually consistent, best effort** | A delay or a loss is an operational problem, not a correctness one | Ordinary publish |
| **Independent** | No relationship | Anywhere |

**The first class is the point of this step.** The usual failure is deciding in advance that
everything decomposes and then finding a mechanism for each pair. Sometimes the correct answer is
that two writes stay together, and the seam moves.

In the example above, writes 1 and 3 are class one. The authorization and its consent must commit
together, because the intermediate state — protected content held with no record of who the
member agreed it could be shared with — is a state the organisation cannot be in, even briefly,
even if a compensation would eventually clean it up. **So `bh-case-svc` owns both, and the seam
goes somewhere else.**

Writes 4 and 5 are class two: the outbox handles them.

## Step 3 — Draw the seam where the classification allows

Only now choose the boundary. It goes where no class-one pair crosses it.

If every candidate seam splits a class-one pair, **say so and stop**. That is a finding — the
domain does not decompose the way the reference architecture assumes — and it belongs in the gap
register, not in a workaround.

## Step 4 — Apply the outbox to what crosses

For each class-two pair:

1. Owning service writes the entity **and** an outbox row in one local transaction.
2. A relay publishes unpublished rows and marks them published.
3. The consumer is **idempotent**, keyed on something stable from the event, because at-least-once
   delivery means the duplicate will arrive.

Know the limit: the outbox makes *one service's* write atomic with *its own* publication. It does
not make two services' writes atomic with each other. It converts "might not happen" into "happens
eventually, at least once" — which is a real guarantee and is not the same guarantee.

## Step 5 — Say what happens when it does not happen

For each class-two pair, write down:

- **The window.** How long can the inconsistency last?
- **The observable.** What query or metric shows an unclosed gap? *(If none exists, build it. An
  eventual consistency you cannot observe is a hope.)*
- **The compensation.** What closes it — a retry, a reconciliation job, a human queue?
- **The alarm.** What fires if it stays open past the window?

An eventual consistency with no observable and no alarm is the same as no guarantee, implemented
with more moving parts.

## Step 6 — Check what the old code did on failure

Read the failure path, not just the happy path. A rolled-back transaction often produced a
*user-visible behaviour* that the decomposition has to reproduce or deliberately change.

If the old system rolled everything back and told the clinician to resubmit — losing typed work,
which they hated — then a decomposition with partial success has changed the contract. The new
behaviour may be better. It is still a change, and it needs to be recorded rather than discovered
in production.

## Step 7 — Write it down where the next person will look

Emit a decomposition note beside the code:

```markdown
## submitAndDecide

**Was**: one @Transactional method, five writes, one Oracle instance.

**Now**: bh-case-svc owns writes 1-4 in one transaction; write 5 becomes an outbox row.

**Atomicity kept**: authorization + consent + assessments + initial review, because
[reason from step 1, quoted from source].

**Atomicity replaced**: the notification. Outbox + idempotent consumer keyed on authId.
Window: under 60s at the configured relay interval.
Observable: `outbox_event WHERE published_at IS NULL AND created_at < now() - 5min`.
Alarm: that count > 0 for 5 consecutive minutes.
Compensation: relay retries; rows past 3 attempts go to a human queue.

**Behaviour change**: none for the caller. Notification may now lag the decision
by up to a minute; previously it lagged by up to five (cron interval).

**Legacy behaviour NOT reproduced**: [or "none"]
```

Then `record_gap` for anything the target platform cannot express, and `queue_manual_review` for
anything whose atomicity requirement you could not establish.

---

## Failure modes, and how to recognise them

| What you wrote | Why it is wrong |
|---|---|
| "The consent write follows the authorization write" | Two writes with no transaction. The window between them is unbounded and there is no compensation. This is the naive port |
| "A saga compensates the authorization if consent fails" | Compensation for a **disclosure** is not possible. You cannot un-hold content you already held. Some things do not compensate |
| "Both services share the database, so it is still atomic" | Then they are one service with extra deployment steps, and the next person will split the database without knowing why they must not |
| "The outbox makes it atomic" | It makes *one service's* write atomic with *its own* publication. Re-read step 4 |
| "Eventual consistency is fine here" | It might be. Say **how long**, **what shows the gap**, and **what closes it**. Without those three, this sentence means "I have not thought about it" |
| Nothing at all | The most common. Atomicity was free, so it was invisible, so nobody recorded losing it |

## The acceptance question

Borrowed from the reference platform's own definition of done:

> *If this caused an incorrect utilization decision in production, could we explain how it
> happened and who owned the logic?*

A partially-completed decomposition fails that question by construction: the state that produced
the decision is spread across services with no record of how it got there. Answering it is the
standard.
