# BHAuthTrack 4.2

Bridgeway Behavioral Health — carve-out utilization management.

Java 8 · Spring MVC 4.3 · JSP/JSTL · single WAR on Tomcat 8 · Oracle 11g · Quartz · Log4j 1.x.

Deployed 2011. Last schema change March 2016. The original author left the following month.

**This is the capstone's domain donor. It is read-only, enforced in code.**

---

## Why a separate system exists at all

Behavioral health was a **carve-out**. For thirty years payers contracted behavioral health to a
separate vendor with its own network, its own clinical criteria, its own claims platform — and its
own member identifiers. That history is not trivia; it is the reason `BH_MEMBER.MEMBER_ID` is
Bridgeway's identifier rather than the health plan's, and it is the reason a third of the pre-2014
rows cannot be joined to the plan at all.

The plan has now in-sourced behavioral health. This system has to move onto the medical platform's
architecture.

---

## Layout

```
src/main/java/com/bridgeway/bhauth/
  controller/   @Controller classes returning JSP view names
  service/      @Service + @Transactional -- where the business logic mostly lives
  dao/          JdbcTemplate and some Hibernate 3
  domain/       plain beans
  batch/        Quartz jobs, including the nightly X12 278 import
  security/     AuthFilter, UserContext, LDAP lookup
src/main/webapp/WEB-INF/jsp/    the view layer -- READ THESE, THEY CONTAIN RULES
src/main/resources/             web.xml, dispatcher-servlet.xml, applicationContext.xml, log4j.xml
db/                             schema, seed, PL/SQL, and the hand-maintained change log
```

---

## Where to start reading

Read these five, in this order. Between them they contain everything that makes the modernization
hard.

| # | File | Why |
|---|---|---|
| 1 | `db/schema_changes.txt` | The hand-maintained change log. **Closer to production than the schema file is.** Records two known drifts and the identifier problem |
| 2 | `db/01_schema.sql` | The data model, with real foreign keys. Note `BH_LOC_REVIEW` — concurrent review has no analogue in medical prior auth — and `BH_CONSENT` |
| 3 | `db/03_PKG_LOC_RULES.sql` | The level-of-care engine. A **stateful first-match ladder**, not a rule set. Branch 7 is where two conditions overlap and only ordering decides the answer |
| 4 | `service/AuthCaseService.java` | The submit-and-decide path. Five writes in **one transaction**, on purpose, for a documented reason |
| 5 | `webapp/WEB-INF/jsp/decision.jsp` | Three business rules and two derived values implemented in a template |

---

## Things that will bite you

**The rules are in two places.** `PKG_LOC_RULES` holds the ladder; `LocRulesService` layers parity,
benefit and network adjustments on top in Java. Neither alone is the rule set. The Java layer runs
*after* the ladder has committed, so it can only downgrade or pend — never upgrade. That asymmetry
is load-bearing.

**Branch 7 overlaps.** In `PKG_LOC_RULES.EVAL_LOC`, a case with a running score of 10 and a
dimension-1 score of 3 satisfies both the ASAM 3.7 test and the 3.5 test below it. Because the ladder
commits on first match it lands on 3.7 and the 3.5 branch never runs. Flatten those into an unordered
decision table and the answer depends entirely on the hit policy you choose.

**`LEGACY_OVERRIDE`.** Added under BHA-2291 in 2013. The ticket body reads, in full, *"per DM
request"*. It is handled in two places and is set on roughly 400 live rows. Nobody currently at
Bridgeway can say what it means. **Do not guess. Escalate it.**

**The audit trigger copies the clinical narrative.** `TRG_BH_AUTH_AUDIT` writes the full old and new
`CLINICAL_NARRATIVE` into `BH_AUDIT_LOG` on every update. That was a 2012 decision made for the
appeals team and signed off by appeals. It was never reviewed by privacy.

**Log4j concatenates the narrative into log lines.** `AuthCaseService.submitAndDecide()` logs it, for
the same appeals-reconstruction reason. Those files roll to the app server and are backed up nightly
to the share the reporting team reads from. On this system that is one sink; a distributed port
turns it into several.

**Roles are a bitmask.** `BH_USER_ROLE.ROLE_MASK`: 1 intake, 2 nurse, 4 physician, 8 psychiatric peer
reviewer, 16 addiction-medicine peer reviewer, 32 admin. The nurse/physician split is not a
convenience — a nurse may approve but may never deny, and only a physician may issue an adverse
determination. For substance-use and psychiatric level-of-care the reviewer is expected to be
same-specialty, which is why 8 and 16 exist separately from 4.

**There is no message broker.** `BH_AUTH_QUEUE` is a table. `poll_queue.sh` runs from cron every five
minutes. If the process dies mid-batch the row stays `LOCKED` and a human clears it on Monday.

**There is no workflow engine.** `AuthStatusService.advance()` is a switch over a status column. Note
that `APPROVED` is not terminal: an approved authorization re-enters review on its cadence. That loop
*is* concurrent review, and it is the single biggest structural difference from medical prior auth.

**Two clocks exist only in a JSP.** The continued-stay countdown and the regulatory turnaround clock
are computed in scriptlets in `decision.jsp` and nowhere else in the codebase. Reporting
reimplemented both in Crystal and the two have disagreed since 2015.

---

## Data

All data in `db/02_seed.sql` is **synthetic**, generated from a documented seed. No real member,
provider, or clinical narrative appears anywhere in this tree. Codes are real and correctly
formatted; the people are not.

This matters beyond good manners: the agent that reads this system operates under a hard *"no PHI in
prompts, ever"* constraint, enforced by a `PreToolUse` hook that inspects tool results before they
reach the model. The synthetic fixtures are what make it possible to point an agent at this codebase
at all.
