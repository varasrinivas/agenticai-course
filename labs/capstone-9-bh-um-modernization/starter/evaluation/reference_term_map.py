"""The reference term map, read out of both trees.

Twenty-two mappings. The five that matter most are the ones where the name is
IDENTICAL and the meaning is not — because those are the ones a synthesizer
maps 1:1 without reading, and nothing objects.
"""

from __future__ import annotations

from term_map import (ENTITY, EVENT, FIELD, NONE, PATTERN, ROLE, STATUS,
                      TermMap, TermMapping)


def build() -> TermMap:
    tm = TermMap()

    # =====================================================================
    # SAME NAME, DIFFERENT MEANING. The silent quadrant.
    # =====================================================================

    tm.add(TermMapping(
        kind=STATUS, clinical="APPROVED", behavioral="APPROVED",
        same_semantics=False,
        evidence="donor: CaseStatus.APPROVED, reached from Task_AutoDecision and "
                 "never left. legacy: AuthStatusService.advance() case "
                 "\"APPROVED\" sets status to IN_REVIEW.",
        divergence="Terminal in the clinical platform. In behavioral health an "
                   "approved authorization RE-ENTERS REVIEW on its cadence — "
                   "every 3 days at ASAM 4.0, every 7 at 3.5 — until discharge "
                   "or step-down. The legacy switch loops it back to IN_REVIEW.",
        action="Do NOT map 1:1. The emitted process must loop, and an approval "
               "must schedule its own next review. A state machine that treats "
               "APPROVED as an end state deletes concurrent review while every "
               "status name still matches.",
        trap_id=3))

    tm.add(TermMapping(
        kind=STATUS, clinical="PENDED", behavioral="PENDED",
        same_semantics=False,
        evidence="donor: CaseStatus.PENDED, set by the gateway when the DMN "
                 "returns needsReview. legacy: PKG_LOC_RULES branch 9 returns "
                 "PENDED for CRITERIA_NOT_MET, and AuthStatusService refuses "
                 "DENIED from a non-physician.",
        divergence="A generic hold in the clinical platform. In behavioral "
                   "health it is a SEPARATION-OF-DUTIES CONTROL: the state a "
                   "case waits in for someone LICENSED to deny it. A nurse may "
                   "approve and may never issue an adverse determination.",
        action="Preserve the control, not just the value. The criteria-not-met "
               "path must still PEND rather than deny, and the review task "
               "needs a candidate group carrying the licensure requirement.",
        trap_id=3))

    tm.add(TermMapping(
        kind=STATUS, clinical="IN_REVIEW", behavioral="IN_REVIEW",
        same_semantics=False,
        evidence="donor: CaseStatus.IN_REVIEW is declared and NEVER ASSIGNED — "
                 "no code path sets it. legacy: it is the target of the "
                 "continued-stay loop, set from APPROVED on every cadence.",
        divergence="Dead enum value on the clinical side; the busiest state on "
                   "the behavioral side. Mapping by name copies a value that "
                   "means nothing onto one that carries the domain's central "
                   "cycle.",
        action="Make it reachable and make it the loop target. Then check the "
               "rest of the donor's enum for the same shape — a declared value "
               "nothing assigns is a capability that was planned and not built.",
        trap_id=3))

    tm.add(TermMapping(
        kind=STATUS, clinical="DENIED", behavioral="DENIED",
        same_semantics=False,
        evidence="donor: pa-decision.dmn has NO rule that can output DENIED, so "
                 "the status is unreachable from the engine. legacy: reachable, "
                 "but only from PKG_LOC_RULES branch 1 (PROV_TERMED); every "
                 "clinical adverse determination pends for a physician instead.",
        divergence="Unreachable on one side. On the other, reachable ONLY for "
                   "an administrative fact — a terminated provider — which is "
                   "why the engine may issue it without a physician. The "
                   "distinction is 'cannot deny' versus 'must not deny HERE', "
                   "and they are not the same defect.",
        action="Make a denial reachable WITH a criterion-traceable reason code, "
               "and preserve branch 9's pend. Converting the criteria-not-met "
               "path into an automated denial removes a control.",
        trap_id=4))

    tm.add(TermMapping(
        kind=STATUS, clinical="SUBMITTED", behavioral="SUBMITTED",
        same_semantics=True,
        evidence="donor: set on intake, before the DMN runs. legacy: set by "
                 "AuthCaseService.submitAndDecide() as write 1. The initial "
                 "state on both sides, and the one status that does map 1:1."))

    tm.add(TermMapping(
        kind=FIELD, clinical="member_id", behavioral="MEMBER_ID",
        same_semantics=False,
        evidence="donor: prior_auth_case.member_id VARCHAR(32), opaque, no "
                 "member table, no FK. legacy: BH_MEMBER.MEMBER_ID is "
                 "BRIDGEWAY's carve-out key; the health plan's key is a "
                 "separate nullable column, PLAN_MEMBER_ID.",
        divergence="One identifier on the clinical side, TWO on the behavioral "
                   "side. MEMBER_ID is the carve-out vendor's; PLAN_MEMBER_ID "
                   "is the plan's and is null for 3 of 10 seeded members "
                   "(31% in production, per BHA-1180).",
        action="Carry both as distinct columns. Key anything crossing to the "
               "health plan on the PLAN identifier. The donor's opaque column "
               "accepts either without objecting, so a wrong choice matches by "
               "luck for whichever formats coincide and fails silently for the "
               "rest.",
        trap_id=6))

    tm.add(TermMapping(
        kind=FIELD, clinical="diagnosis", behavioral="DIAGNOSIS_CODE",
        same_semantics=False,
        evidence="donor: present on the event payload, NOT an input to "
                 "pa-decision.dmn. legacy: DIAGNOSIS_CODE drives branch 9 and "
                 "selects the peer-reviewer specialty in decision.jsp.",
        divergence="Carried but unused in the clinical decision. In behavioral "
                   "health it decides both the level-of-care path and WHO IS "
                   "LICENSED to deny — F10–F19 needs an addiction-medicine "
                   "reviewer, F20–F49 a psychiatrist.",
        action="Add diagnosis as a decision-table input, and resolve the BPMN "
               "candidate group from its block.",
        trap_id=4))

    tm.add(TermMapping(
        kind=PATTERN, clinical="audit", behavioral="BH_AUDIT_LOG",
        same_semantics=False,
        evidence="donor: no audit table at all; transitionTo() is unguarded. "
                 "legacy: TRG_BH_AUTH_AUDIT records OLD and NEW status — and "
                 "the full clinical narrative — on every update.",
        divergence="The word means a CHANGE LOG on both sides. 42 CFR Part 2 "
                   "requires something different: an ACCOUNTING OF DISCLOSURES "
                   "— who a record went to, under which consent, for what "
                   "purpose. Neither system has one.",
        action="Build two things, not one: a guarded transition history with "
               "actor attribution, AND a disclosure register. They answer "
               "different questions and only the second satisfies Part 2. Do "
               "not carry the narrative columns across.",
        trap_id=5))

    # =====================================================================
    # DIFFERENT NAME, SAME CONCEPT.
    # =====================================================================

    tm.add(TermMapping(
        kind=ENTITY, clinical="prior_auth_case", behavioral="BH_AUTH",
        same_semantics=True,
        evidence="donor: V1__init.sql. legacy: 01_schema.sql. Both are the "
                 "authorization aggregate."))

    tm.add(TermMapping(
        kind=FIELD, clinical="procedureCode", behavioral="SERVICE_CODE",
        same_semantics=True,
        evidence="donor: SubmitPriorAuthDto.procedureCode, a CPT. legacy: "
                 "BH_AUTH.SERVICE_CODE, CPT or HCPCS."))

    tm.add(TermMapping(
        kind=FIELD, clinical="requestedUnits", behavioral="REQUESTED_UNITS",
        same_semantics=True,
        evidence="donor: an input to pa-decision.dmn. legacy: capped by "
                 "LEAST() in every committing branch of PKG_LOC_RULES."))

    tm.add(TermMapping(
        kind=PATTERN, clinical="outbox_event", behavioral="BH_AUTH_QUEUE",
        same_semantics=True,
        evidence="donor: V2__outbox.sql plus a relay worker. legacy: a table "
                 "plus poll_queue.sh on a five-minute cron, written inside "
                 "submitAndDecide()'s transaction. Same guarantee — a queue "
                 "row exists if and only if the authorization committed — "
                 "built in 2011 by people who would not have called it a "
                 "transactional outbox."))

    tm.add(TermMapping(
        kind=EVENT, clinical="pa.submitted", behavioral="AUTH_SUBMITTED",
        same_semantics=True,
        evidence="donor: libs/events. legacy: BH_AUTH_QUEUE.EVENT_TYPE."))

    tm.add(TermMapping(
        kind=EVENT, clinical="pa.decisioned", behavioral="AUTH_DECIDED",
        same_semantics=True,
        evidence="donor: libs/events. legacy: BH_AUTH_QUEUE.EVENT_TYPE, "
                 "enqueued as write 5 of submitAndDecide()."))

    tm.add(TermMapping(
        kind=PATTERN, clinical="transitionTo()", behavioral="AuthStatusService.advance()",
        same_semantics=True,
        evidence="donor: PriorAuthCase.transitionTo(), unguarded. legacy: a "
                 "switch over the status column. Neither validates the "
                 "transition; both are the whole state machine."))

    tm.add(TermMapping(
        kind=ENTITY, clinical="intake DTO", behavioral="authSubmit.jsp form",
        same_semantics=True,
        evidence="donor: SubmitPriorAuthDto. legacy: the intake form binds "
                 "straight onto the Auth bean — there is no DTO layer."))

    # =====================================================================
    # THE FIELD WITH THE SAME CONCEPT AND THE OPPOSITE FATE.
    # =====================================================================

    tm.add(TermMapping(
        kind=FIELD, clinical="notes", behavioral="CLINICAL_NARRATIVE",
        same_semantics=False,
        evidence="donor: @IsOptional @IsString @Length(0,2000) on the intake "
                 "DTO — and then not a column, not an entity field, not in "
                 "either event payload. legacy: BH_AUTH.CLINICAL_NARRATIVE "
                 "CLOB, non-null on 14 of 15 seeded rows.",
        divergence="Same concept — clinician free text — and the OPPOSITE "
                   "fate. The clinical platform validates it and discards it, "
                   "so the caller gets a 201 and believes it landed. In "
                   "behavioral health it is simultaneously the "
                   "medical-necessity evidence a reviewer reads AND the 42 CFR "
                   "Part 2 protected content.",
        action="Persist it: migration column, entity field, round-trip to the "
               "response. And keep it out of every sink — log statements, "
               "event payloads, search mappings, audit rows, error paths.",
        trap_id=2))

    # =====================================================================
    # NO COUNTERPART. Usually the most interesting rows in the map.
    # =====================================================================

    tm.add(TermMapping(
        kind=ENTITY, clinical=NONE, behavioral="BH_LOC_REVIEW",
        same_semantics=False,
        evidence="legacy: REVIEW_SEQ, NEXT_REVIEW_DUE, REVIEW_INTERVAL_DAYS, "
                 "unique on (AUTH_ID, REVIEW_SEQ). Nothing in the donor's two "
                 "tables corresponds.",
        divergence="Concurrent review has no analogue in medical prior auth. "
                   "An authorization is not one decision; it is an initial "
                   "determination plus a series on a cadence set by level of "
                   "care.",
        action="must-build-new. Include the composite unique — it is the only "
               "thing preventing a corrupt review ladder, and the donor's "
               "schema has no composite uniques at all.",
        trap_id=3))

    tm.add(TermMapping(
        kind=ENTITY, clinical=NONE, behavioral="BH_CONSENT",
        same_semantics=False,
        evidence="legacy: RECIPIENT_NAME, SCOPE, EXPIRES_TS, REVOKED_TS, "
                 "REDISCLOSURE_NOTICE_SENT. No consent concept anywhere in the "
                 "donor.",
        divergence="42 CFR Part 2 disclosure requires a consent that NAMES the "
                   "recipient, states a purpose and scope, and expires. HIPAA "
                   "has no equivalent requirement, so the clinical platform "
                   "never needed the concept.",
        action="must-build-new, written in the same transaction as the "
               "authorization and enforced by a NOT NULL foreign key rather "
               "than by convention.",
        trap_id=8))

    tm.add(TermMapping(
        kind=ENTITY, clinical=NONE, behavioral="BH_ASSESSMENT",
        same_semantics=False,
        evidence="legacy: six ASAM dimensions plus PHQ9/GAD7/CSSRS, read "
                 "directly by PKG_LOC_RULES. Donor's DMN takes procedure code "
                 "and units only.",
        divergence="The clinical engine decides from the procedure. The "
                   "behavioral engine decides from a six-dimension assessment, "
                   "one of which inverts.",
        action="must-build-new, and pass the dimensions to the decision "
               "explicitly rather than having the engine read them from a "
               "table that now belongs to another service.",
        trap_id=1))

    tm.add(TermMapping(
        kind=ROLE, clinical=NONE, behavioral="BH_USER_ROLE.ROLE_MASK",
        same_semantics=False,
        evidence="donor: um.security.enabled=false by default; authentication "
                 "only when enabled — no roles, no scopes, no method security. "
                 "legacy: a bitmask, 1 intake / 2 nurse / 4 MD / 8 psych / "
                 "16 addiction / 32 admin.",
        divergence="There is nothing on the clinical side to map roles ONTO. "
                   "The behavioral side needs them for a rule required by "
                   "accreditation.",
        action="must-build-new on both sides of the wire. And do not carry the "
               "bitmask: JSTL tests it numerically because it has no bitwise "
               "operator, and `roleMask >= 4` is the PERMISSIVE side of that "
               "divergence — mask 33 passes it and fails hasRole(MD).",
        trap_id=10))

    tm.add(TermMapping(
        kind=STATUS, clinical=NONE, behavioral="EXPIRED",
        same_semantics=False,
        evidence="legacy: CK_BH_AUTH_STATUS permits EXPIRED; "
                 "AuthStatusService treats it as terminal. Absent from "
                 "CaseStatus.",
        divergence="An authorization whose continued-stay cadence was missed. "
                   "Only reachable in a domain that HAS a cadence.",
        action="Add it, and make it reachable from the boundary timer rather "
               "than from a nightly query nobody watches.",
        trap_id=3))

    tm.add(TermMapping(
        kind=STATUS, clinical="APPEALED", behavioral=NONE,
        same_semantics=False,
        evidence="donor BACKLOG.md #7 lists an appeals path and an APPEALED "
                 "status as planned-and-unbuilt. legacy: DENIED is terminal; "
                 "appeals are handled outside the system entirely, in a shared "
                 "mailbox and a spreadsheet.",
        divergence="NEITHER system has it, and both need it. The platform team "
                   "raised it; our own gap analysis did not.",
        action="Escalate rather than decide. Behavioral-health denials are "
               "appealed at least as often as medical ones, but whether "
               "appeals come in-system is a programme decision."))

    tm.add(TermMapping(
        kind=FIELD, clinical=NONE, behavioral="LEGACY_OVERRIDE",
        same_semantics=False,
        evidence="legacy: BHA-2291, February 2013, ticket body in full 'per DM "
                 "request'. Handled in PKG_LOC_RULES branch 0 and "
                 "AuthStatusService case PENDED. Set on ~400 live rows.",
        divergence="No counterpart, and no surviving explanation on the side "
                   "that has it.",
        action="DO NOT MAP. Reproduce the behaviour verbatim and queue it for "
               "human decision. A map that assigns this a meaning has guessed, "
               "and nobody at Bridgeway can check the answer."))

    tm.add(TermMapping(
        kind=PATTERN, clinical="feature flags", behavioral=NONE,
        same_semantics=False,
        evidence="donor: 7 *_ENABLED flags in application.yml, each gating one "
                 "capability. legacy: no flags at all.",
        divergence="The idiom is worth copying — it is what keeps the platform "
                   "runnable one capability at a time. But it was designed for "
                   "capabilities, and this domain has controls.",
        action="Mirror it for capabilities. Never gate consent enforcement, "
               "the disclosure accounting or licensure checks: a control that "
               "can be switched off in configuration is a default.",
        trap_id=7))

    return tm


#: Every status in the donor's enum. The map must account for each one,
#: because the ones that match by name are the ones that get mapped without
#: being read.
DONOR_STATUSES = {"SUBMITTED", "IN_REVIEW", "APPROVED", "DENIED", "PENDED"}


if __name__ == "__main__":
    print(build().render())
