"""The reference screen inventory, built from the actual JSPs.

Seven screens, and the reference platform contributes an equivalent for
exactly one of them.

Every rule here was read out of a template in `bhauthtrack/`. The ones whose
`server_side_equivalent` is NONE are the interesting ones: they are enforced
by markup and nothing else, so a port that treats the screen as markup deletes
them, and the deletion is invisible until someone issues a determination they
were not licensed to issue.
"""

from __future__ import annotations

from screen_inventory import (API_OMISSION, COMPUTED_FIELD, DECISION_INPUT,
                              DERIVED_VALUE, FIELD_VISIBILITY, ROLE_GATE_ACTION,
                              ROLE_GATE_SCREEN, ROUTE_GUARD, SERVICE_CHECK,
                              WORKFLOW_GROUP, Screen, ScreenInventory, ViewRule)

NURSE = "bh-nurse"
PHYSICIAN = "bh-physician"
INTAKE = "bh-intake"
ADMIN = "bh-admin"
ADDICTION = "bh-addiction-medicine-reviewer"


def build() -> ScreenInventory:
    inv = ScreenInventory()

    # ------------------------------------------------------------ worklist
    worklist = inv.add(Screen(
        jsp="worklist.jsp", route="/worklist",
        controller="WorklistController.worklist",
        reachable_from=[],
        note="The home screen and the work-distribution mechanism. There is no "
             "task engine: a nightly query builds rows, the JSP renders them "
             "role-filtered, and whoever opens a row first works it."))

    worklist.add_rule(ViewRule(
        kind=ROLE_GATE_ACTION,
        source='<c:when test="${i.status eq \'PENDED\' and sessionScope.roleMask lt 4}">',
        rule="A case pended for an adverse determination offers no action to a "
             "non-physician",
        server_side_equivalent="WorklistDao.forReviewer() filters PENDED rows in "
                               "SQL for a non-MD -- BY A DIFFERENT RULE than this "
                               "one, so the two do not agree",
        proposed_home=SERVICE_CHECK,
        note="Two filters, in two layers, neither a superset of the other. "
             "'What work is mine?' has two answers depending on which you ask. "
             "Pick one before moving it."))

    worklist.add_rule(ViewRule(
        kind=ROLE_GATE_ACTION,
        source='<c:when test="${... fn:startsWith(i.diagnosisCode, \'F1\') '
               'and sessionScope.roleMask lt 16}">',
        rule="A substance-use diagnosis pended for denial offers no action to a "
             "physician who is not addiction-medicine",
        server_side_equivalent="NONE in the worklist query -- the SQL does not "
                               "know about specialty, so these rows sit on every "
                               "physician's list, counted in the totals and "
                               "unactionable by most of them",
        proposed_home=SERVICE_CHECK))

    worklist.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source="TRUNC(NVL(r.NEXT_REVIEW_DUE, SYSDATE) - SYSDATE) AS DAYS_UNTIL_DUE",
        rule="Days until the continued-stay review is due; negative means the "
             "authorization is out of compliance",
        server_side_equivalent="computed in SQL here, and AGAIN in a decision.jsp "
                               "scriptlet with different rounding",
        proposed_home=COMPUTED_FIELD,
        note="Same value, two implementations, two roundings. A case can sort as "
             "'due today' and display as '1 day'."))

    # ---------------------------------------------------------- authSubmit
    submit = inv.add(Screen(
        jsp="authSubmit.jsp", route="/auth/new",
        controller="AuthController.newAuth",
        reachable_from=["worklist.jsp"],
        required_roles=[INTAKE, NURSE],
        note="One form, three entities: the authorization, six ASAM dimension "
             "scores and the Part 2 consent, posted together because the service "
             "writes them together. The shape of this form IS the shape of that "
             "transaction."))

    submit.add_rule(ViewRule(
        kind=ROLE_GATE_SCREEN,
        source='if (!userContext.hasRole(ROLE_INTAKE) && !userContext.hasRole(ROLE_NURSE))',
        rule="Only intake coordinators and nurses may create a request",
        server_side_equivalent="AuthController.newAuth redirects",
        proposed_home=ROUTE_GUARD))

    submit.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='<input type="text" name="dim1" size="2" value="0"/>',
        rule="ASAM dimension scores are 0-4",
        server_side_equivalent="NONE -- no validation in the controller and no "
                               "CHECK constraint on the score column. A "
                               "fat-fingered 40 in dimension 1 approves ASAM 4.0 "
                               "without comment",
        proposed_home=DECISION_INPUT))

    # ---------------------------------------------------------- authDetail
    detail = inv.add(Screen(
        jsp="authDetail.jsp", route="/auth/:id",
        controller="AuthController.detail",
        reachable_from=["worklist.jsp", "search.jsp"],
        note="Four tabs. All four are in the HTML regardless of which is showing "
             "-- the tabs are anchors, not requests."))

    detail.add_rule(ViewRule(
        kind=FIELD_VISIBILITY,
        source='<c:if test="${sessionScope.roleMask ge 2}"> ... clinical tab',
        rule="Intake coordinators are non-clinical and must not read the clinical "
             "narrative",
        server_side_equivalent="NONE -- AuthController.detail loads the narrative "
                               "unconditionally; the guard controls RENDERING, not "
                               "RETRIEVAL, so the content is in the response body "
                               "either way",
        proposed_home=API_OMISSION,
        note="A role check that emits content into the response and hides it with "
             "a conditional is not a control. The fix is that the endpoint does "
             "not return the field."))

    detail.add_rule(ViewRule(
        kind=FIELD_VISIBILITY,
        source='<c:if test="${sessionScope.roleMask ge 4}"> ... audit tab',
        rule="Only physicians may see the audit trail",
        server_side_equivalent="NONE -- auditDao.findByAuth is called for every "
                               "viewer",
        proposed_home=API_OMISSION))

    detail.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='<c:when test="${empty member.planMemberId}"> ... unresolved to plan',
        rule="A member with no health-plan identifier cannot be reconciled with "
             "the plan",
        server_side_equivalent="Member.isUnresolvedToPlan()",
        proposed_home=COMPUTED_FIELD,
        note="The ONLY place the carve-out identity problem is visible to a user: "
             "a warning triangle on one tab of one screen. Nothing blocks, "
             "nothing alerts, nothing reports."))

    # ------------------------------------------------------------ decision
    decision = inv.add(Screen(
        jsp="decision.jsp", route="/auth/:id/decide",
        controller="AuthController.decideForm",
        reachable_from=["worklist.jsp", "authDetail.jsp"],
        required_roles=[NURSE, PHYSICIAN],
        note="THE screen. Three business rules and two derived values live in "
             "this template."))

    decision.add_rule(ViewRule(
        kind=ROLE_GATE_ACTION,
        source='<c:when test="${sessionScope.roleMask ge 4}"> ... '
               '<c:when test="${sessionScope.roleMask ge 16}"> ... btn-deny',
        rule="A nurse may approve and may NEVER deny. Only a physician may issue "
             "an adverse determination, and a substance-use diagnosis requires an "
             "addiction-medicine reviewer",
        server_side_equivalent="AuthCaseService.issueDenial -- added in 2014 after "
                               "an incident, and reached by only 2 of the 4 call "
                               "paths into the decision logic",
        proposed_home=WORKFLOW_GROUP,
        note="Separation of duties required by accreditation, expressed as three "
             "nested JSTL conditionals. Note also that `roleMask ge 4` is a "
             "NUMERIC test standing in for a bitwise one, and it is the "
             "permissive side: mask 33 (intake+admin) passes it and fails "
             "hasRole(MD)."))

    decision.add_rule(ViewRule(
        kind=FIELD_VISIBILITY,
        source='<c:if test="${sessionScope.roleMask ge 2}"><pre>'
               '${auth.clinicalNarrative}</pre></c:if>',
        rule="The clinical narrative is minimum-necessary-restricted to clinical "
             "staff",
        server_side_equivalent="NONE here -- and SearchController exposes a "
                               "full-text search over the same column to any "
                               "authenticated user with no role check at all",
        proposed_home=API_OMISSION,
        note="The control on this screen is undone by its absence on another. "
             "That pair is one finding, not two."))

    decision.add_rule(ViewRule(
        kind=FIELD_VISIBILITY,
        source='<c:if test="${provider.part2Program}"> ... part2-banner',
        rule="A record from a federally assisted SUD program carries a "
             "redisclosure prohibition, and the reviewer must be told",
        server_side_equivalent="NONE -- this banner is the only place in the "
                               "application that surfaces Part 2 status, and "
                               "there is no corresponding server-side control",
        proposed_home=COMPUTED_FIELD))

    decision.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source="long msLeft = lastReview.getNextReviewDue().getTime() - "
               "System.currentTimeMillis();",
        rule="Continued-stay countdown; overdue means the authorization is out of "
             "compliance",
        server_side_equivalent="NONE -- computed in a scriptlet on every page "
                               "render, and reimplemented separately in a Crystal "
                               "report. The two have disagreed since 2015",
        proposed_home=COMPUTED_FIELD))

    decision.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='int allowedHours = "EXPEDITED".equals(a.getUrgency()) ? 72 : 336;',
        rule="Regulatory turnaround: 72 hours expedited, 14 calendar days "
             "standard. Missing it can force an automatic approval depending on "
             "line of business",
        server_side_equivalent="NONE -- this is the ONLY implementation of that "
                               "rule in the codebase",
        proposed_home=COMPUTED_FIELD,
        note="A regulatory deadline that exists in a JSP scriptlet. In the new "
             "process it is also a BPMN boundary timer."))

    # ----------------------------------------------------------- locReview
    review = inv.add(Screen(
        jsp="locReview.jsp", route="/auth/:id/review",
        controller="ReviewController.form",
        reachable_from=["worklist.jsp", "authDetail.jsp"],
        required_roles=[NURSE, PHYSICIAN],
        note="Continued-stay review. NO EQUIVALENT ANYWHERE IN THE REFERENCE "
             "PLATFORM -- the whole concept is absent from medical prior auth."))

    review.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='String[] ladder = { "1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0" }; '
               "... for (int i = idx - 1; i >= 0; i--)",
        rule="Continued-stay review offers the current level or a step DOWN. "
             "Stepping up is not offered: an increase in level of care is a new "
             "determination with its own turnaround clock and its own appeal "
             "rights",
        server_side_equivalent="the ladder also exists in LocRulesService.LADDER "
                               "and in PKG_LOC_RULES -- three copies, currently "
                               "in agreement",
        proposed_home=DECISION_INPUT))

    review.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source="if (interval > 0 && daysLate >= interval) { lateBanner = ... }",
        rule="A review more than one full interval late means the member has been "
             "at this level with no authorized clinical justification for that "
             "period",
        server_side_equivalent="NONE -- no flag, no report, no escalation. The "
                               "banner tells the reviewer and nothing else reacts",
        proposed_home=COMPUTED_FIELD))

    review.add_rule(ViewRule(
        kind=ROLE_GATE_ACTION,
        source='<option value="DENIED">Denied &mdash; adverse determination '
               '(physician only)</option>',
        rule="A continued-stay denial is an adverse determination and requires a "
             "physician",
        server_side_equivalent="ReviewController.record checks the role -- but "
                               "does NOT check specialty, and does NOT update "
                               "BH_AUTH.STATUS, so the case reads DENIED to the "
                               "worklist and APPROVED to every report",
        proposed_home=SERVICE_CHECK,
        note="The option is offered to everyone and refused afterwards."))

    # -------------------------------------------------------- consentAdmin
    consent = inv.add(Screen(
        jsp="consentAdmin.jsp", route="/member/:id/consent",
        controller="ConsentController.list",
        reachable_from=["authDetail.jsp"],
        required_roles=[ADMIN],
        note="The one screen whose role check is in the CONTROLLER rather than "
             "the markup -- written in 2012 by a different developer, before the "
             "guard-in-JSTL convention took hold. Two conventions coexist and an "
             "inventory has to find both."))

    consent.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='<c:set var="expired" value="${not empty k.expiresTs and '
               'k.expiresTs.time lt now}"/>',
        rule="A consent is usable only if signed, unexpired and unrevoked",
        server_side_equivalent="Consent.isUsable() implements exactly this -- and "
                               "this page does not call it, because a Date "
                               "comparison did not work in EL and the author "
                               "worked around it here",
        proposed_home=COMPUTED_FIELD,
        note="Two implementations of one rule. They agree today."))

    consent.add_rule(ViewRule(
        kind=FIELD_VISIBILITY,
        source='<c:if test="${k.scope eq \'FULL_RECORD\'}">narrative</c:if>',
        rule="Only a FULL_RECORD consent permits the clinical narrative to leave "
             "the system",
        server_side_equivalent="NONE -- the queue payload built in "
                               "AuthCaseService carries the narrative regardless "
                               "of scope",
        proposed_home=SERVICE_CHECK,
        note="The screen states the rule the system does not enforce."))

    # --------------------------------------------------------------- search
    search = inv.add(Screen(
        jsp="search.jsp", route="/search",
        controller="SearchController.search",
        reachable_from=["worklist.jsp"],
        required_roles=[NURSE, PHYSICIAN],
        note="Three search modes, and they are not equally safe."))

    search.add_rule(ViewRule(
        kind=ROLE_GATE_SCREEN,
        source='<c:if test="${sessionScope.roleMask ge 2}">'
               '<li><a href="/search">Search</a></li></c:if>  (header.jsp)',
        rule="Clinical search is for clinical staff",
        server_side_equivalent="NONE -- SearchController has no role check at all. "
                               "Hiding the link is the entire control, and the URL "
                               "is /search?mode=clinical&q=",
        proposed_home=SERVICE_CHECK,
        note="The sharpest finding in the view layer. A careful role guard on the "
             "detail screen is undone by an unguarded full-text search over the "
             "same column."))

    search.add_rule(ViewRule(
        kind=DERIVED_VALUE,
        source='<c:if test="${matchedOn eq \'PLAN_MEMBER_ID\'}">',
        rule="Which member identifier matched -- the carve-out vendor's or the "
             "health plan's",
        server_side_equivalent="SearchController tries one then the other and "
                               "reports which hit",
        proposed_home=COMPUTED_FIELD,
        note="The only place a user ever learns there are two identifiers, and "
             "only after searching with the plan's."))

    inv.navigation = [
        {"from": "worklist.jsp", "to": "authDetail.jsp", "via": "auth id link"},
        {"from": "worklist.jsp", "to": "decision.jsp", "via": "Review action"},
        {"from": "worklist.jsp", "to": "locReview.jsp", "via": "Continued stay action"},
        {"from": "worklist.jsp", "to": "authSubmit.jsp", "via": "header nav"},
        {"from": "worklist.jsp", "to": "search.jsp", "via": "header nav"},
        {"from": "authDetail.jsp", "to": "locReview.jsp", "via": "Record continued stay"},
        {"from": "authDetail.jsp", "to": "consentAdmin.jsp", "via": "consent tab link"},
        {"from": "search.jsp", "to": "authDetail.jsp", "via": "result link"},
    ]
    return inv


if __name__ == "__main__":
    print(build().render())
