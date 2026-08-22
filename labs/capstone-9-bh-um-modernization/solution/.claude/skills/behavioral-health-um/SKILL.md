---
name: behavioral-health-um
description: Behavioral-health utilization management domain knowledge — ASAM levels and the six dimensions, LOCUS/CALOCUS, concurrent review cadence, 42 CFR Part 2, MHPAEA parity, BH code sets, and the reviewer-licensure rule. Load this before reading, classifying, or generating anything in a behavioral-health prior-authorization system.
---

# Behavioral health utilization management

You are working on a system that authorizes behavioral-health care. It is **not** medical prior
authorization with different codes. Four things differ structurally, and each one breaks an
assumption the medical platform is built on.

Read this file first. Load a reference below only when you actually need its detail — they are
long, and pulling one in speculatively wastes the context you need for the code.

| Reference | Load it when |
|---|---|
| `references/asam-levels.md` | Classifying a level of care, reading the ladder, or writing a decision table |
| `references/part2-redisclosure.md` | Anything touching consent, disclosure, logging, eventing, or search |
| `references/bh-code-sets.md` | Validating or emitting a service, diagnosis, or instrument code |
| `references/parity-nqtl.md` | A rule applies to BH that may have no med/surg analogue |

`scripts/validate_bh_codes.py` checks a code against the sets in the third reference. Run it
rather than reasoning about whether `H0018` is a real HCPCS code.

---

## 1. The criteria are a ladder, not a yes/no

Medical prior auth asks: *is this procedure medically necessary for this diagnosis?* One
question, one answer.

Behavioral health asks: **at what intensity of care should this person be treated right now?**
The answer is a rung on a ladder — ASAM 1.0 outpatient through 4.0 medically managed intensive
inpatient — chosen from six independently scored dimensions.

So a behavioral-health engine that can only approve or deny the level that was *requested* is
missing the domain. It has to be able to grant a **different** level than the one asked for, in
either direction, and say why.

**The one that catches people: dimension 4 is readiness to change, and a LOW score argues
AGAINST residential placement.** Every other dimension reads "higher means more care". Dimension 4
inverts, because placing someone with no engagement into residential treatment historically
produces an against-medical-advice discharge within 72 hours. Treat all six as severity
indicators and you will get this backwards and never notice.

## 2. Authorization is a series, not an event

A medical case is decided once. A behavioral-health case is decided, and then **reviewed again on
a cadence set by the level of care**, until the member is discharged or steps down. This is
*concurrent review* — for residential care it is roughly weekly, at the most intensive levels
every three days.

Three consequences for any system design:

- An approval is not terminal. It must schedule its own next review.
- **A next-review date is a regulatory deadline, not a reminder.** A residential authorization not
  re-reviewed inside its interval is out of compliance, whether or not anyone was told.
- The process model needs a timer-driven loop. A workflow that terminates after the first
  decision cannot express the domain at all.

Anything you generate that treats "approved" as an end state is wrong here, no matter how
faithfully it mirrors the platform it was copied from.

## 3. Two privacy regimes, not one

HIPAA covers everything. **42 CFR Part 2 additionally covers records from federally assisted
substance-use-disorder treatment programs**, and it is much stricter:

- Disclosure requires a consent that **names the specific recipient**. There is no
  treatment/payment/operations exception and no "minimum necessary" shortcut.
- The consent states a **purpose** and a **scope**, and it **expires**.
- The disclosure must carry a **redisclosure notice** — the recipient is bound too.
- The program must be able to produce an **accounting of disclosures**.

A system can be fully HIPAA-compliant and still violate Part 2 on every request. That is the
usual failure, and it is almost always a plumbing failure rather than a policy one: the narrative
goes into a log line, an event payload and a search index because that is what the architecture
does with fields, and none of those three sinks has a consent scope.

**Load `references/part2-redisclosure.md` before you write or classify anything that moves clinical
free text.**

## 4. Parity is a design constraint

MHPAEA requires that a limitation applied to behavioral health be **no more restrictive than the
comparable limitation on medical/surgical care**. Non-quantitative treatment limitations — review
frequency, step-down requirements, criteria strictness, network standards — are in scope, and a
BH-only limitation with no med/surg analogue is an exposure.

You will find these in legacy code as rules that look reasonable in isolation. When you find one,
**do not silently port it and do not silently drop it.** Porting carries the exposure forward;
dropping it changes outcomes for real members. Escalate it.

---

## The reviewer-licensure rule

This one is load-bearing and it is easy to lose in a port because it is often encoded somewhere
that does not look like authorization code.

> **A nurse reviewer may approve. A nurse may never deny. Only a physician may issue an adverse
> determination.**

It is a separation of duties required by accreditation. It is why a `PENDED` status exists at all
— that is the state a case waits in for someone licensed to deny it, and a system without it has
either auto-denials or no denials.

In behavioral health it goes further: an adverse determination on a **substance-use** or
**psychiatric** level of care is expected to come from a **same-specialty** peer reviewer, not
merely from any physician.

Watch for this rule implemented in:

- a template conditional wrapped around a button
- a role bitmask tested numerically rather than bitwise
- a workflow task's candidate group — **or its absence**, which silently deletes the rule
- nowhere at all, on three of four code paths into the same service

## Vocabulary

| Term | Meaning |
|---|---|
| **Carve-out** | Behavioral health contracted to a separate vendor with its own network, criteria, claims platform **and member identifiers**. Explains why BH systems key on an identifier the health plan does not recognise |
| **Concurrent review** | The recurring continued-stay review described above |
| **PHP** | Partial hospitalization, ASAM 2.5. Day treatment, member goes home at night |
| **IOP** | Intensive outpatient, ASAM 2.1 |
| **LOCUS / CALOCUS** | Level of Care Utilization System — the psychiatric analogue of ASAM. CALOCUS is the child/adolescent version |
| **C-SSRS** | Columbia Suicide Severity Rating Scale, 0–5. Scores of 4 and 5 are active ideation with intent |
| **PHQ-9 / GAD-7** | Depression (0–27) and anxiety (0–21) severity instruments |
| **NQTL** | Non-quantitative treatment limitation — the parity concept above |
| **TAT** | Turnaround time. Expedited requests typically 72 hours, standard 14 calendar days. Missing it can force an automatic approval depending on line of business |
| **Adverse determination** | A denial, or an approval at a lower level than requested. The regulated event |
| **Step-down** | Moving to a less intensive level. Normal and expected; not a denial |

## What to do when the domain and the architecture disagree

That is the whole job. The reference platform was built for medical prior auth and is correct for
it. Where it cannot express something above — a loop, a licensure requirement, a consent scope, a
denial with a criterion — **say so explicitly and classify it**, rather than generating something
that compiles and quietly means the wrong thing.

Use `record_gap` with `must-build-new` or `must-not-port` and cite the evidence. A gap you name is
a finding. A gap you paper over is a defect with a plausible shape.
