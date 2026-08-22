# ASAM levels and the six dimensions

The ASAM Criteria are the standard framework for placing a person in substance-use treatment.
This reference is a **teaching simplification** sufficient to read and rebuild the legacy rules —
it is not the criteria themselves, and it is not clinical guidance.

## The levels

| Level | Name | What it is | Typical review cadence |
|---|---|---|---|
| **0.5** | Early intervention | Education and assessment, not yet treatment | — |
| **1.0** | Outpatient | Under 9 hours a week | 90 days |
| **2.1** | Intensive outpatient (IOP) | 9+ hours a week, lives at home | 30 days |
| **2.5** | Partial hospitalization (PHP) | 20+ hours a week, day treatment, home at night | 14 days |
| **3.1** | Clinically managed low-intensity residential | 24-hour structure, 5+ hours clinical a week | 14 days |
| **3.5** | Clinically managed high-intensity residential | 24-hour structure, high-intensity treatment | 7 days |
| **3.7** | Medically monitored intensive inpatient | 24-hour nursing, physician availability | 5 days |
| **4.0** | Medically managed intensive inpatient | 24-hour nursing **and** daily physician care | 3 days |

**The cadence column is the point.** Interval is a function of level, not of the number of units
approved. A fourteen-day approval at 3.5 still comes back for review in seven days.

Note where the boundaries fall. 3.1 → 3.5 is an increase in treatment intensity within the same
setting. 3.5 → 3.7 crosses into **medical monitoring** — that is a different kind of facility with
nursing staff, and it is where the placement argument gets hardest and legacy rules get
knottiest.

## The six dimensions

Each is scored, conventionally 0–4. They are assessed independently and then weighed together.

| # | Dimension | What a high score means |
|---|---|---|
| **1** | Acute intoxication and/or withdrawal potential | Severe or dangerous withdrawal. A high score here alone can justify medically managed care regardless of everything else |
| **2** | Biomedical conditions and complications | Physical health problems needing concurrent attention |
| **3** | Emotional, behavioral, or cognitive conditions | Co-occurring mental-health severity |
| **4** | **Readiness to change** | **High = engaged. LOW is the risk.** See below |
| **5** | Relapse, continued use, or continued problem potential | High risk of resuming use without structure |
| **6** | Recovery / living environment | The environment is unsupportive or actively harmful |

### Dimension 4 inverts

Dimensions 1, 2, 3, 5 and 6 all read "higher score → more intensive care". **Dimension 4 does
not.** A low readiness score argues *against* residential placement, because someone with no
engagement placed in a residential setting historically leaves against medical advice within
72 hours — consuming a bed, achieving nothing, and often making the next engagement harder.

A rules engine expressing this will *subtract* from its severity score when dimension 4 is low.
If you are translating such a rule and it looks like a bug, it is not.

### Dimensions 5 and 6 together are the residential argument

They are what separates 3.5 from 3.7 in practice, and they are why level of care is not a function
of diagnosis severity alone. A person can be clinically stable and still need residential care
because the place they would otherwise go home to makes outpatient treatment futile. Both high is
a materially stronger signal than either alone, which is why legacy rules commonly score the
conjunction separately from the disjunction.

## Reading a legacy ASAM engine

Engines of this era are almost never declarative. Expect:

- **A running score mutated across branches.** Some branches decide and return; others adjust the
  score and fall through. Which is which is load-bearing.
- **First-match commitment.** The first branch that decides wins, so branch *order* is part of the
  logic and two branches can both be true for the same input.
- **Thresholds with no recorded provenance.** A clinical policy team maintains them by spreadsheet.
  Do not invent a rationale for a specific number; record it as given.
- **Rules split across layers** — some in the database, some in application code, applied after the
  first layer has already committed. Neither layer alone is the rule set.

When the second layer runs *after* the first has decided, it can usually only **downgrade or
pend, never upgrade**. That asymmetry is real behaviour and must survive translation.

## The 3.5 / 3.7 boundary

This is where a first-match ladder most often hides an overlap: a case can satisfy both the 3.7
test and the 3.5 test, and only branch ordering decides which one it gets.

Flattening those two branches into an unordered decision table makes the answer depend entirely on
the hit policy:

| Hit policy | Result on an overlapping row |
|---|---|
| `FIRST` | The higher branch — **only if row order survived translation** |
| `UNIQUE` | An error at evaluation time; two rules matched |
| `PRIORITY` | Whichever output the priority list ranks higher |
| `COLLECT` | Both, and the caller has to choose |

There is no neutral choice. See the `rules-to-dmn` skill for how to state and justify one.

## LOCUS and CALOCUS

The psychiatric analogue, used for mental-health rather than substance-use placement. LOCUS scores
six evaluation parameters and maps to six levels of care; CALOCUS is the child and adolescent
version. A behavioral-health system typically runs **both** frameworks — ASAM for substance use,
LOCUS/CALOCUS for psychiatric — and the choice of framework follows the diagnosis, not the
member.

If you find a system applying ASAM to psychiatric admissions, that is a finding worth recording,
not a convention worth copying.
