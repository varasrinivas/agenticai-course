#!/usr/bin/env python3
"""Build the reference run into expected_output/.

    python evaluation/build_reference_run.py

What a good run produces: the gap register, the seam map, the manual-review
queue, the rules IR, the emitted workspace, the parity report, and the briefing
the human sees at the gate.

GENERATED, NOT HAND-WRITTEN. The DMN comes out of dmn_writer, the BPMN out of
bpmn_writer, the register through gap_register's constraints, the seam map
through seam_map's. If a constraint tightens, this output changes with it --
which is the only way a reference answer stays honest.

It is the reference, not the destination. A student's agent produces its own,
and the interesting work is diffing the two and deciding which is right.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION = os.path.dirname(HERE)
LAB = os.path.dirname(SOLUTION)
for _p in (SOLUTION, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpmn_writer                                  # noqa: E402
import dmn_writer                                   # noqa: E402
import reference_screen_inventory as RSI            # noqa: E402
import reference_term_map as RTM                    # noqa: E402
import route_writer                                 # noqa: E402
import rules_ir as R                                # noqa: E402
import seam_map as SM                               # noqa: E402
import validation                                   # noqa: E402
from gap_register import (EXTEND, MUST_BUILD_NEW, MUST_NOT_PORT, PORT_AS_IS,
                          GapEntry, GapRegister)    # noqa: E402

OUT = os.path.join(LAB, "expected_output")
ARTIFACTS = os.path.join(OUT, "artifacts")
EMIT = os.path.join(OUT, "bh-um-lite")


def write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


# ---------------------------------------------------------- gap register


def build_register() -> GapRegister:
    reg = GapRegister()

    reg.add(GapEntry(
        capability="transactional outbox",
        verdict=PORT_AS_IS,
        evidence="outbox_event table + relay worker + idempotent consumer in "
                 "um-case-svc. Domain-neutral and correct.",
        backlog="not listed -- already built"))

    reg.add(GapEntry(
        capability="feature-flag capability layering",
        verdict=PORT_AS_IS,
        evidence="7 flags in apps/um-case-svc/.../application.yml, each gating one "
                 "capability so the stack stays runnable with any subset enabled",
        backlog="not listed -- already built"))

    reg.add(GapEntry(
        capability="decision table",
        verdict=EXTEND,
        evidence="camunda/pa-decision.dmn: hitPolicy FIRST, 3 rules, outputs "
                 "{APPROVED, PENDED}, inputs {Procedure code, Requested units}. "
                 "No DENIED output and no diagnosis input.",
        trap_id=4,
        backlog="agrees -- their #6, 'Extend DMN medical-necessity criteria'"))

    reg.add(GapEntry(
        capability="process model",
        verdict=EXTEND,
        evidence="camunda/prior-auth.bpmn is one-shot: 6 sequence flows, no cycle, "
                 "no timerEventDefinition. Correct for a case with one decision.",
        trap_id=3,
        backlog="agrees -- their #8, 'SLA turnaround timer + auto-escalation'"))

    reg.add(GapEntry(
        capability="concurrent review",
        verdict=MUST_BUILD_NEW,
        evidence="nothing in the reference platform corresponds. The legacy "
                 "BH_LOC_REVIEW table carries REVIEW_SEQ, NEXT_REVIEW_DUE and a "
                 "per-level cadence; the donor schema has 2 tables and no review "
                 "history at all.",
        requirement="A review ladder keyed (auth_id, review_seq) with a unique "
                    "constraint, a next-review date derived from the GRANTED LEVEL, "
                    "and a boundary timer that escalates when it passes.",
        trap_id=3,
        backlog="not listed -- the concept does not exist in their domain"))

    reg.add(GapEntry(
        capability="decision audit and disclosure accounting",
        verdict=MUST_BUILD_NEW,
        evidence="donor has no audit table, no createdBy/updatedBy, no transition "
                 "history, and transitionTo() is unguarded. The legacy system has "
                 "an audit trigger, but it records CHANGES to records, not "
                 "DISCLOSURES of them.",
        requirement="Two separate things: a guarded transition history with actor "
                    "attribution, AND a disclosure register recording recipient, "
                    "scope, consent id and timestamp. They answer different "
                    "questions and only the second satisfies Part 2.",
        trap_id=5,
        backlog="agrees -- their #1 and #2"))

    reg.add(GapEntry(
        capability="42 CFR Part 2 consent model",
        verdict=MUST_BUILD_NEW,
        evidence="no consent concept anywhere in the reference platform. Part 2 "
                 "disclosure requires a consent naming the recipient, stating a "
                 "purpose and scope, and expiring.",
        requirement="A consent entity with recipient, type, purpose, scope, signed, "
                    "expires, revoked and redisclosure-notice-sent; written in the "
                    "same transaction as the authorization; enforced by a NOT NULL "
                    "foreign key rather than by convention.",
        trap_id=8,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="role-based authorization and reviewer licensure",
        verdict=MUST_BUILD_NEW,
        evidence="um.security.enabled=false by default, and authentication-only "
                 "when enabled: no roles, no scopes, no method security. The "
                 "manual-review task has neither assignee nor candidate group.",
        requirement="Named roles, method-level checks on every call path (not only "
                    "the one the UI uses), and a BPMN candidate group resolved from "
                    "the diagnosis block so a substance-use adverse determination "
                    "routes to an addiction-medicine reviewer.",
        trap_id=10,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="test suite",
        verdict=MUST_BUILD_NEW,
        evidence="zero tests in the entire reference repository; CI runs "
                 "`npm test --if-present`, so their absence never fails the build.",
        requirement="Tests for every item above, and a CI configuration that fails "
                    "when they are missing rather than passing vacuously.",
        backlog="not listed"))

    reg.add(GapEntry(
        capability="cleartext PHI in logs, events and search",
        verdict=MUST_NOT_PORT,
        evidence="donor interpolates member identifiers into log statements, ships "
                 "plain JSON to an unauthenticated broker, and indexes cases into "
                 "Elasticsearch with no TLS anywhere.",
        harm="This content is 42 CFR Part 2 protected. The monolith had ONE log "
             "sink; decomposition multiplies it into one per service plus a broker "
             "plus an index. Copying the idiom produces unlawful disclosure at "
             "several sinks instead of one, and nobody decided to make it worse -- "
             "fan-out is simply what the architecture does with a field.",
        trap_id=5,
        backlog="not listed -- their domain is HIPAA-only"))

    reg.add(GapEntry(
        capability="consent enforcement as a feature flag",
        verdict=MUST_NOT_PORT,
        evidence="the donor applies its flag idiom uniformly to all seven "
                 "capabilities and ships SECURITY_ENABLED=false by default.",
        harm="A week of CONSENT_ENABLED=false is an unlawful disclosure, not a slow "
             "page. A regulatory control that can be switched off in configuration "
             "is a default, not a control. Mirror the idiom for capabilities; never "
             "for consent, the disclosure accounting, or licensure checks.",
        trap_id=7,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="validated-then-discarded free-text field",
        verdict=MUST_NOT_PORT,
        evidence="the intake DTO validates `notes` with @IsOptional @IsString "
                 "@Length(0,2000) and then drops it: not a column, not an entity "
                 "field, not in either event payload.",
        harm="In behavioral health that field is simultaneously the "
             "medical-necessity evidence a reviewer reads AND the Part 2 protected "
             "content. Two failures at once, and the 201 response hides both -- the "
             "caller believes the clinical justification was recorded.",
        trap_id=2,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="entity resolution across the carve-out boundary",
        verdict=MUST_BUILD_NEW,
        evidence="donor stores one opaque member_id VARCHAR(32) with no member "
                 "table and no foreign key. Legacy BH_MEMBER carries TWO keys and "
                 "3 of 10 seeded members (30%) have no plan identifier at all.",
        requirement="Carry both identifiers as distinct columns; key anything "
                    "crossing to the health plan on the plan's. Report the "
                    "unresolvable population as a number rather than resolving it "
                    "by guesswork.",
        trap_id=6,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="referential integrity",
        verdict=EXTEND,
        evidence="donor schema has 2 tables and ZERO foreign keys -- a "
                 "database-per-service consequence, not a preference. The legacy "
                 "schema has real foreign keys and a composite unique on "
                 "(AUTH_ID, REVIEW_SEQ).",
        trap_id=None,
        backlog="not listed"))

    reg.add(GapEntry(
        capability="frontend",
        verdict=MUST_BUILD_NEW,
        evidence="one unrouted form. app.config.ts provides only provideHttpClient() "
                 "-- @angular/router is a declared dependency that was never wired. "
                 "libs/ui's TaskListComponent, CaseSearchComponent and "
                 "CaseCreateComponent are never imported. Service URL hardcoded.",
        requirement="Seven routed, role-guarded screens consuming libs/ui, with the "
                    "rules currently living in JSTL relocated to route guards and "
                    "server-side checks.",
        trap_id=9,
        backlog="agrees in part -- their #4, 'Case list + filter endpoint & UI'"))

    reg.backlog_crosscheck = {
        "agreements": [
            "#1 guard case status transitions -> our 'decision audit' entry",
            "#2 persist decision rationale + decidedBy -> our 'decision audit' entry",
            "#4 case list + filter endpoint & UI -> our 'frontend' entry",
            "#6 extend DMN medical-necessity criteria -> our 'decision table' entry",
            "#8 SLA turnaround timer + auto-escalation -> our 'process model' entry",
        ],
        "we_found_they_did_not": [
            "42 CFR Part 2 consent model -- their domain is HIPAA-only, so the "
            "concept does not arise for them",
            "concurrent review -- a medical case has one decision",
            "reviewer licensure as a workflow candidate group",
            "carve-out entity resolution -- they have one identifier and no "
            "second organisation to reconcile with",
            "cleartext PHI fan-out across decomposed sinks",
        ],
        "they_list_we_missed": [
            "#7 appeals path + APPEALED status -- IN SCOPE FOR BH TOO and we did "
            "not raise it. Behavioral-health denials are appealed at least as "
            "often. Added to the queue as a follow-up.",
            "#10 dead-letter retry + alerting -- their pa.dead-letter topic has no "
            "producer and no consumer; we noted the dangling topic but did not "
            "carry it into a verdict.",
        ],
    }
    return reg


# -------------------------------------------------------------- seam map


def build_seam_map() -> SM.SeamMap:
    sm = SM.SeamMap()

    sm.add_unit(SM.TransactionalUnit(
        method="AuthCaseService.submitAndDecide",
        failure_behaviour="everything rolls back and the clinician is told to "
                          "resubmit. There is no draft, so they retype the "
                          "narrative -- the most complained-about behaviour in the "
                          "application, and a direct consequence of the atomicity "
                          "that makes it correct.",
        writes=[
            SM.Write("BH_AUTH", "the authorization", "anchor"),
            SM.Write("BH_ASSESSMENT", "the rules engine's inputs",
                     "the engine reads these from the database rather than being "
                     "passed them; a decision computed from missing inputs is not "
                     "reproducible"),
            SM.Write("BH_CONSENT", "the Part 2 disclosure permission",
                     "an authorization from a federally assisted SUD program with "
                     "no consent record is protected content held with no record of "
                     "who the member agreed it could be shared with. The 2013 merge "
                     "comment says the services were combined because split "
                     "boundaries produced orphaned consent rows."),
            SM.Write("BH_LOC_REVIEW", "the initial determination, seq 1",
                     "NEXT_REVIEW_DUE drives the worklist; an approval without it "
                     "is an authorization nobody looks at again"),
            SM.Write("BH_AUTH_QUEUE", "the outbound notification",
                     "a queue row exists if and only if the authorization "
                     "committed. This is a transactional outbox, built in 2011 by "
                     "people who would not have called it that."),
        ]))

    # The seam that is NOT cut. Recording a rejection is a result.
    sm.add_seam(SM.Seam(
        name="authorization | consent",
        left="bh-case-svc", right="bh-consent-svc",
        crosses=["AuthCaseService.submitAndDecide"],
        coupling=SM.MUST_BE_ATOMIC,
        rejected_because=(
            "The intermediate state -- protected treatment content held with no "
            "record of consent -- is one the organisation cannot be in, even "
            "briefly, even with a compensation queued. A disclosure does not "
            "compensate: you cannot un-hold content you have already held. So "
            "bh-case-svc owns both writes and the seam moves.")))

    sm.add_seam(SM.Seam(
        name="case | notification",
        left="bh-case-svc", right="bh-notify-svc",
        crosses=["AuthCaseService.submitAndDecide"],
        coupling=SM.EVENTUAL_GUARANTEED,
        replacement=SM.AtomicityReplacement(
            mechanism="transactional outbox in bh-case-svc + idempotent consumer "
                      "keyed on (auth_id, review_seq)",
            window="under 60s at the configured relay interval; the legacy cron "
                   "polled every 5 minutes, so this is tighter than what it replaces",
            observable="SELECT count(*) FROM outbox_event WHERE published_at IS NULL "
                       "AND created_at < now() - interval '5 minutes'",
            compensation="relay retries with backoff; rows past 3 attempts move to a "
                         "human queue, because the legacy FAILED state was where "
                         "rows went to be forgotten",
            alarm="that count > 0 for 5 consecutive minutes pages the on-call")))

    sm.add_seam(SM.Seam(
        name="intake | case",
        left="bh-intake-svc", right="bh-case-svc",
        crosses=[],
        coupling=SM.INDEPENDENT))

    return sm


# ------------------------------------------------------ emitted workspace


def build_workspace(ir: dict):
    """Emit both phases and return the screen inventory 9B was built from."""
    if os.path.isdir(EMIT):
        shutil.rmtree(EMIT)

    write(os.path.join(EMIT, "camunda", "bh-loc-decision.dmn"), dmn_writer.render(ir))
    write(os.path.join(EMIT, "camunda", "bh-prior-auth.bpmn"), bpmn_writer.render())

    write(os.path.join(EMIT, "apps", "bh-case-svc", "src", "main", "resources",
                       "db", "migration", "V1__init.sql"), """\
-- Behavioral health authorization schema.
--
-- The reference platform has two tables and zero foreign keys, which is a
-- database-per-service consequence rather than a preference. Where a
-- constraint is dropped here, the comment says what replaces it.

CREATE TABLE bh_member (
    member_id       VARCHAR(24) PRIMARY KEY,
    -- The health plan's identifier, and the one anything crossing the
    -- organisational boundary must key on. NULLABLE because the carve-out
    -- vendor's eligibility feed did not carry it until 2014; roughly a third
    -- of pre-2014 members have none and cannot be reconciled in either
    -- direction. Carried explicitly rather than collapsed into one opaque id.
    plan_member_id  VARCHAR(24),
    line_of_business VARCHAR(20) NOT NULL
);

CREATE TABLE bh_consent (
    consent_id      BIGSERIAL PRIMARY KEY,
    member_id       VARCHAR(24) NOT NULL REFERENCES bh_member(member_id),
    recipient_name  VARCHAR(120) NOT NULL,
    recipient_type  VARCHAR(24)  NOT NULL,
    purpose         VARCHAR(200) NOT NULL,
    -- FULL_RECORD is the only scope under which the clinical narrative may
    -- leave this system. AUTH_DECISION_ONLY permits the determination and not
    -- the justification, and it is the common case.
    scope           VARCHAR(24)  NOT NULL,
    signed_ts       TIMESTAMPTZ  NOT NULL,
    expires_ts      TIMESTAMPTZ  NOT NULL,
    revoked_ts      TIMESTAMPTZ,
    redisclosure_notice_sent BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE bh_authorization (
    auth_id         BIGSERIAL PRIMARY KEY,
    member_id       VARCHAR(24) NOT NULL REFERENCES bh_member(member_id),
    service_code    VARCHAR(10) NOT NULL,
    diagnosis_code  VARCHAR(10) NOT NULL,
    requested_loc   VARCHAR(8)  NOT NULL,
    requested_units INT         NOT NULL,
    -- PERSISTED, not validated-and-discarded. This is the medical-necessity
    -- evidence a reviewer reads AND the Part 2 protected content.
    clinical_narrative TEXT,
    status          VARCHAR(20) NOT NULL,
    urgency         VARCHAR(12) NOT NULL DEFAULT 'STANDARD',
    -- The invariant that was a transaction boundary in the monolith is a
    -- constraint here. NOT NULL, so an authorization cannot exist without its
    -- consent -- enforced, rather than merely currently true.
    consent_id      BIGINT      NOT NULL REFERENCES bh_consent(consent_id)
);

CREATE TABLE bh_loc_review (
    review_id       BIGSERIAL PRIMARY KEY,
    auth_id         BIGINT      NOT NULL REFERENCES bh_authorization(auth_id),
    review_seq      INT         NOT NULL,
    reviewed_loc    VARCHAR(8)  NOT NULL,
    approved_units  INT         NOT NULL,
    review_interval_days INT    NOT NULL,
    -- A regulatory deadline, derived from the LEVEL rather than from the units.
    next_review_due DATE,
    outcome         VARCHAR(20) NOT NULL,
    reviewer_user_id VARCHAR(64) NOT NULL,
    reviewer_credential VARCHAR(20) NOT NULL,
    -- The only thing preventing a corrupt review ladder. Dropping it turns a
    -- crash into silent duplicate reviews.
    CONSTRAINT uq_bh_loc_review_seq UNIQUE (auth_id, review_seq)
);
""")

    write(os.path.join(EMIT, "apps", "bh-case-svc", "src", "main", "resources",
                       "db", "migration", "V3__decision_audit.sql"), """\
-- Two tables, because a change audit and a disclosure accounting answer
-- different questions and only the second satisfies 42 CFR Part 2.

-- 1. What changed, who changed it, and was the transition legal.
CREATE TABLE bh_case_transition (
    transition_id   BIGSERIAL PRIMARY KEY,
    auth_id         BIGINT      NOT NULL REFERENCES bh_authorization(auth_id),
    from_status     VARCHAR(20),
    to_status       VARCHAR(20) NOT NULL,
    actor_user_id   VARCHAR(64) NOT NULL,
    actor_roles     VARCHAR(200) NOT NULL,
    -- The rule path from the decision engine. In the legacy system this string
    -- existed for the length of a page render and was then discarded, so no
    -- determination could be explained after the fact.
    rule_path       TEXT,
    reason_code     VARCHAR(32),
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. What was disclosed, TO WHOM, and under which consent.
--
-- Note what is absent: no narrative column. The legacy audit trigger copied
-- the full clinical narrative on every update, accumulating one protected copy
-- per touch in a table with no consent scope and no expiry.
CREATE TABLE bh_disclosure (
    disclosure_id   BIGSERIAL PRIMARY KEY,
    auth_id         BIGINT      NOT NULL REFERENCES bh_authorization(auth_id),
    consent_id      BIGINT      NOT NULL REFERENCES bh_consent(consent_id),
    recipient_name  VARCHAR(120) NOT NULL,
    scope_disclosed VARCHAR(24) NOT NULL,
    redisclosure_notice_sent BOOLEAN NOT NULL,
    disclosed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")

    write(os.path.join(EMIT, "apps", "bh-case-svc", "src", "main", "resources",
                       "application.yml"), """\
# Capability flags, mirroring the reference platform's layering idiom.
#
# Every flag below gates a CAPABILITY: switch one off for a week and the
# consequence is a slower or less featureful system.
bh:
  events-enabled:   ${EVENTS_ENABLED:true}
  outbox-enabled:   ${OUTBOX_ENABLED:true}
  workflow-enabled: ${WORKFLOW_ENABLED:true}
  cache-enabled:    ${CACHE_ENABLED:false}
  search-enabled:   ${SEARCH_ENABLED:false}
  replica-enabled:  ${REPLICA_ENABLED:false}

# THERE IS DELIBERATELY NO FLAG FOR:
#   consent enforcement
#   the disclosure accounting
#   reviewer licensure checks
#
# Switch one of those off for a week and the consequence is an unlawful
# disclosure or an unlicensed determination. A regulatory control that can be
# switched off in configuration is a default, not a control -- so these are
# unconditional and there is no key here to turn them off.
""")

    write(os.path.join(EMIT, "apps", "bh-case-svc", "src", "main", "java",
                       "DecisionService.java"), """\
package com.plan.bh.casesvc;

/** Records a determination. */
public class DecisionService {

    public void record(Authorization auth, LocDecision decision, Actor actor) {
        // Identifiers and outcomes only. The clinical narrative is Part 2
        // protected content and this logger ships to the enterprise index;
        // the legacy system logged it here for the appeals team, which is how
        // it reached the backup share.
        log.info("decided authId={} outcome={} loc={} by={}",
                 auth.getAuthId(), decision.getOutcome(),
                 decision.getGrantedLoc(), actor.getUserId());

        transitions.record(auth, decision, actor);
    }
}
""")

    write(os.path.join(EMIT, "apps", "bh-intake-svc", "src", "dto",
                       "submit-auth.dto.ts"), """\
export class SubmitAuthDto {
  @IsString() memberId!: string;
  @IsString() serviceCode!: string;
  @IsString() diagnosisCode!: string;
  @IsString() requestedLoc!: string;
  @IsInt() requestedUnits!: number;

  // Validated AND PERSISTED. The reference platform validates its equivalent
  // field and then drops it, which returns a 201 while discarding the
  // medical-necessity evidence.
  @IsOptional() @IsString() @Length(0, 8000) clinicalNarrative?: string;
}
""")

    write(os.path.join(EMIT, "apps", "bh-case-svc", "src", "main", "java",
                       "domain", "Authorization.java"), """\
package com.plan.bh.casesvc.domain;

@Entity
@Table(name = "bh_authorization")
public class Authorization {
    @Id @GeneratedValue private Long authId;
    @Column(name = "member_id") private String memberId;
    @Column(name = "clinical_narrative") private String clinicalNarrative;
    @Column(name = "consent_id", nullable = false) private Long consentId;
}
""")

    # ---- phase 9B: the client, emitted from the screen inventory ----------
    inventory = RSI.build()
    route_writer.emit(
        inventory,
        lambda rel, content: write(os.path.join(EMIT, rel), content),
        # Phase 9A emitted a server-side check for every rule the inventory
        # marks for one. Passing the set explicitly is how the writer refuses
        # to guard around a rule the backend cannot actually enforce.
        server_side_checks={r.rule for r in inventory.all_rules()})

    write(os.path.join(EMIT, "libs", "events", "envelope.ts"), """\
export interface EventEnvelope<T> {
  eventId: string;
  eventType: string;
  occurredAt: string;
  payload: T;
}

// The decision event. Carries the determination and NOT the justification:
// the common consent scope is AUTH_DECISION_ONLY, which permits one and not
// the other. Building the payload from the consent scope rather than from the
// entity is the whole difference.
export interface BhDecisioned {
  authId: number;
  planMemberId: string | null;
  outcome: 'APPROVED' | 'PENDED' | 'DENIED';
  grantedLoc: string | null;
  reasonCode: string | null;
  nextReviewDue: string | null;
}
""")

    return inventory


# ------------------------------------------------------------------ main


def main() -> int:
    with open(os.path.join(HERE, "reference_rules_ir.json"), encoding="utf-8") as fh:
        ir = json.load(fh)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)

    reg = build_register()
    reg.save(os.path.join(ARTIFACTS, "gap-register.json"))
    write(os.path.join(OUT, "gap_register.txt"), reg.render() + "\n")

    sm = build_seam_map()
    sm.save(os.path.join(ARTIFACTS, "seam-map.json"))
    write(os.path.join(OUT, "seam_map.txt"), sm.render() + "\n")

    with open(os.path.join(ARTIFACTS, "rules-ir.json"), "w", encoding="utf-8") as fh:
        json.dump(ir, fh, indent=2)

    queue = {"items": [
        {"artifact": "BH_AUTH.LEGACY_OVERRIDE / PKG_LOC_RULES branch 0",
         "reason": "Added under BHA-2291 in 2013. The ticket body reads, in full, "
                   "'per DM request'. No design note, no acceptance criteria, no "
                   "test. Handled in two places and set on roughly 400 live rows.",
         "question": "Which determinations was LEGACY_OVERRIDE meant to cover, who "
                     "authorised it, and what should happen to the ~400 rows that "
                     "carry it?",
         "evidence": "db/schema_changes.txt BHA-2291; PKG_LOC_RULES branch 0; "
                     "AuthStatusService.advance() case PENDED"},
        {"artifact": "LocRulesService adjustment B -- the frequency pend",
         "reason": "Three or more adverse determinations in a rolling year pend the "
                   "case regardless of clinical criteria. Compliance flagged it in "
                   "2016: 'The medical side does not apply an equivalent "
                   "frequency-based pend to med/surg requests. If we keep this we "
                   "need a comparative analysis on file. -- K.O.' Never actioned.",
         "question": "Is this a non-quantitative treatment limitation applied to "
                     "behavioral health alone, and does a comparative analysis "
                     "exist? Porting it carries the exposure forward; dropping it "
                     "changes outcomes for real members. Neither is an engineering "
                     "decision.",
         "evidence": "LocRulesService.evaluate(), adjustment B, with the 2016 note "
                     "quoted verbatim in the source"},
        {"artifact": "LocRulesService adjustment C -- network-adequacy step-down",
         "reason": "No in-network capacity at the granted level steps the member "
                   "DOWN a level rather than authorising out-of-network. The "
                   "med/surg side authorises out-of-network.",
         "question": "Is a capacity-driven step-down a parity exposure? It also "
                     "runs off a table populated by a Monday spreadsheet upload.",
         "evidence": "LocRulesService.evaluate(), adjustment C; BH_FACILITY_CAPACITY "
                     "is not under this system's change control"},
        {"artifact": "X12278ImportJob.impliedConsent / LegacyAuthEndpoint.impliedConsent",
         "reason": "Two independent code paths FABRICATE a Part 2 consent on the "
                   "submitter's behalf, asserting that consent was obtained on paper "
                   "at the facility. Nobody verifies that, and most requests arrive "
                   "by one of these paths.",
         "question": "Who consents when a machine submits? This is a question for a "
                     "compliance officer, not an architect.",
         "evidence": "both methods, identical in effect, written six years apart"},
        {"artifact": "appeals path",
         "reason": "The platform team's backlog #7 lists an appeals path and an "
                   "APPEALED status as planned-and-unbuilt. Our register did not "
                   "raise it; behavioral-health denials are appealed at least as "
                   "often as medical ones, and the legacy system handles appeals "
                   "entirely outside itself, in a shared mailbox and a spreadsheet.",
         "question": "Should the appeals path be in scope for this modernization, or "
                     "does it stay out-of-system as today?",
         "evidence": "reference-umlite/BACKLOG.md #7; AuthStatusService treats "
                     "DENIED as terminal"},
    ]}
    with open(os.path.join(ARTIFACTS, "manual-review-queue.json"), "w",
              encoding="utf-8") as fh:
        json.dump(queue, fh, indent=2)

    term_map = RTM.build()
    term_map.save(os.path.join(ARTIFACTS, "term-map.json"))
    write(os.path.join(OUT, "term_map.txt"), term_map.render() + "\n")

    inventory = build_workspace(ir)
    inventory.save(os.path.join(ARTIFACTS, "screen-inventory.json"))
    write(os.path.join(OUT, "screen_inventory.txt"), inventory.render() + "\n")

    result = validation.run_all(
        EMIT, ir=ir, seam_map=sm.to_dict(), register=reg.to_dict(),
        inventory=inventory.to_dict(),
        term_map=term_map.to_dict(), donor_statuses=RTM.DONOR_STATUSES,
        legacy_counts={"unresolved_to_plan": 3, "unresolved_pct": 30.0})
    validation.save(result, os.path.join(ARTIFACTS, "parity-report.json"))

    lines = ["RULES DIVERGENCE", "=" * 72, ""]
    divergences = R.diff_engines(ir, R.golden_cases())
    lines.append(f"  golden cases      : {len(R.golden_cases())}")
    lines.append(f"  covers the overlap: {R.covers_overlap(R.golden_cases())}")
    lines.append(f"  divergences       : {len(divergences)}")
    lines.append("")
    if divergences:
        for d in divergences:
            lines.append(f"  {d.auth_id}: {d.legacy} vs {d.emitted}")
    else:
        lines.append("  The tightened UNIQUE table reproduces the ladder on every")
        lines.append("  golden case, INCLUDING case 500001 where two rows overlap")
        lines.append("  and only the ladder's ordering decided the answer.")
        lines.append("")
        lines.append("  A clean divergence report is only meaningful because the")
        lines.append("  case set covers that boundary. Without case 500001 this")
        lines.append("  report would be clean and would prove nothing.")
    write(os.path.join(OUT, "rules_divergence.txt"), "\n".join(lines) + "\n")

    import config as cfg
    cfg.ARTIFACT_DIR = ARTIFACTS
    import hooks
    write(os.path.join(OUT, "hitl_approval_prompt.txt"),
          "FINALIZATION REQUIRES HUMAN APPROVAL.\n\n"
          + hooks.finalization_briefing()
          + "\n\nA person must read artifacts/modernization_report.html and re-run:\n"
            "    python coordinator.py --phase finalize --approve\n")

    import report
    data = report.collect(ARTIFACTS)
    write(os.path.join(OUT, "modernization_report.html"), report.render_html(data))
    with open(os.path.join(ARTIFACTS, "modernization_report.json"), "w",
              encoding="utf-8") as fh:
        state, blocking = report.verdict(data)
        json.dump({"verdict": state, "blocking": blocking, **data}, fh, indent=2)
    write(os.path.join(OUT, "modernization_report.txt"), report.render_console(data))

    print(f"wrote {OUT}")
    print(f"  parity verdict : {result['verdict']}")
    for b in result["blocking"]:
        print(f"    blocking: {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
