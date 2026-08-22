"""Render the behavioral-health prior-authorization process as Camunda BPMN.

The reference platform's process is one-shot: start, decide, gateway, maybe a
manual review, notify, end. That is correct for medical prior authorization,
where a case has one decision.

It cannot express behavioral health, and this module exists to make the three
differences structural rather than aspirational:

  1. **The process loops.** An approval schedules its next continued-stay
     review and the case comes back around. Approval is not a terminal state.
  2. **There is a timer.** The continued-stay cadence is a regulatory deadline,
     so it is a boundary timer with an escalation path -- not a weekday email
     to a shared mailbox, which is what the legacy system had and which misses
     every weekend deadline because the interval is in calendar days.
  3. **The review task has a candidate group.** Where a task encodes "only a
     physician may issue an adverse determination, same-specialty for
     substance-use and psychiatric", the candidate group IS that rule. The
     reference platform's review task has neither assignee nor candidate group,
     which deletes the rule while leaving the diagram looking complete.

`preflight` refuses to emit a process missing any of the three.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from rules_ir import REVIEW_INTERVAL


class BpmnEmitError(RuntimeError):
    """The process would not express the domain."""


# Candidate groups. The nurse/physician split is a separation of duties
# required by accreditation; the specialty split exists because an adverse
# determination on substance-use or psychiatric level of care is expected to
# come from a same-specialty peer reviewer.
GROUP_NURSE = "bh-nurse-reviewer"
GROUP_PHYSICIAN = "bh-physician-reviewer"
GROUP_ADDICTION = "bh-addiction-medicine-reviewer"
GROUP_PSYCH = "bh-psychiatric-reviewer"


def preflight(spec: dict) -> list[str]:
    problems: list[str] = []
    if not spec.get("continued_stay_loop"):
        problems.append(
            "process does not loop. An approved behavioral-health authorization "
            "re-enters review on its cadence; a process that terminates after "
            "one decision cannot express concurrent review, which is the single "
            "biggest structural difference from medical prior auth.")
    if not spec.get("review_timer"):
        problems.append(
            "no timer on the continued-stay review. The cadence is a regulatory "
            "deadline -- three days at ASAM 4.0 -- and a reminder job is not a "
            "deadline, it is a hope with a cron expression.")
    if not spec.get("escalation"):
        problems.append(
            "timer with no escalation path. An overdue review that fires a timer "
            "nobody is assigned to is the legacy system's shared mailbox with "
            "extra XML.")
    for task, group in (spec.get("candidate_groups") or {}).items():
        if not group:
            problems.append(f"user task {task!r} has no candidate group")
    if not (spec.get("candidate_groups") or {}):
        problems.append(
            "no candidate groups declared. Where a task encodes reviewer "
            "licensure, the candidate group is the rule -- an unassigned task "
            "silently deletes it.")
    return problems


def render(spec: dict | None = None, *, process_id: str = "bh-prior-auth") -> str:
    spec = dict(spec or default_spec())
    problems = preflight(spec)
    if problems:
        raise BpmnEmitError(
            "refusing to emit a process:\n  - " + "\n  - ".join(problems))

    groups = spec["candidate_groups"]
    # ISO 8601 durations, one per ASAM level. Camunda resolves the expression
    # at runtime from the granted level, so the cadence follows the LEVEL rather
    # than the unit count -- a 14-day approval at 3.5 still returns in 7 days.
    cadence = "".join(
        f'\n           {loc} -> P{days}D' for loc, days in sorted(REVIEW_INTERVAL.items()))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                  id="{process_id}-definitions"
                  targetNamespace="http://bridgeway.example/bh-um">

  <!--
    Behavioral-health prior authorization.

    THREE THINGS HERE HAVE NO COUNTERPART IN THE REFERENCE PLATFORM'S PROCESS,
    and each is deliberate:

    1. Task_ContinuedStayReview loops back to the decision. An approval is not
       terminal; the case returns on its cadence until discharge or step-down.

    2. Timer_ReviewDue is a boundary timer carrying the regulatory deadline.
       Cadence by level:{cadence}

    3. Every user task carries a candidateGroups. The reference platform's
       manual-review task has neither assignee nor candidate group, which
       removes the "only a physician may deny" rule while leaving the diagram
       looking complete.
  -->

  <bpmn:process id="{process_id}" name="BH prior authorization" isExecutable="true">

    <bpmn:startEvent id="Start_Submitted" name="Request submitted">
      <bpmn:outgoing>flow_to_decision</bpmn:outgoing>
    </bpmn:startEvent>

    <!-- The decision table. Note that it may PEND rather than deny: only a
         physician may issue an adverse determination, and that separation of
         duties is why a PENDED state exists at all. -->
    <bpmn:businessRuleTask id="Task_LocDecision" name="Evaluate level of care"
                           camunda:decisionRef="bh-loc-decision"
                           camunda:mapDecisionResult="singleResult"
                           camunda:resultVariable="locDecision">
      <bpmn:incoming>flow_to_decision</bpmn:incoming>
      <bpmn:incoming>flow_review_back</bpmn:incoming>
      <bpmn:outgoing>flow_to_gateway</bpmn:outgoing>
    </bpmn:businessRuleTask>

    <bpmn:exclusiveGateway id="Gateway_Outcome" name="Engine outcome?">
      <bpmn:incoming>flow_to_gateway</bpmn:incoming>
      <bpmn:outgoing>flow_approved</bpmn:outgoing>
      <bpmn:outgoing>flow_pended</bpmn:outgoing>
      <bpmn:outgoing>flow_denied_admin</bpmn:outgoing>
    </bpmn:exclusiveGateway>

    <!-- PENDED: a human reviewer, licensed for this diagnosis. The candidate
         group is chosen from the diagnosis block, because a substance-use
         adverse determination needs an addiction-medicine peer reviewer and a
         psychiatric one needs a psychiatrist. -->
    <bpmn:userTask id="Task_ClinicalReview" name="Clinical review"
                   camunda:candidateGroups="${{reviewerGroup}}"
                   camunda:formKey="bh-clinical-review">
      <bpmn:documentation>
        reviewerGroup is resolved at instantiation:
          diagnosis F10-F19  -> {GROUP_ADDICTION}
          diagnosis F20-F49  -> {GROUP_PSYCH}
          otherwise          -> {GROUP_PHYSICIAN}
        A nurse ({GROUP_NURSE}) may approve and may NEVER deny.
      </bpmn:documentation>
      <bpmn:incoming>flow_pended</bpmn:incoming>
      <bpmn:outgoing>flow_review_done</bpmn:outgoing>
    </bpmn:userTask>

    <!-- The regulatory turnaround clock: 72 hours expedited, 14 calendar days
         standard. In the legacy system this existed only in a JSP scriptlet
         and, separately and differently, in a Crystal report. -->
    <bpmn:boundaryEvent id="Timer_Turnaround" attachedToRef="Task_ClinicalReview"
                        cancelActivity="false">
      <bpmn:timerEventDefinition>
        <bpmn:timeDuration xsi:type="bpmn:tFormalExpression"
                           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        >${{turnaroundDuration}}</bpmn:timeDuration>
      </bpmn:timerEventDefinition>
      <bpmn:outgoing>flow_tat_breach</bpmn:outgoing>
    </bpmn:boundaryEvent>

    <bpmn:serviceTask id="Task_EscalateTat" name="Escalate turnaround breach"
                      camunda:topic="bh-escalate-tat">
      <bpmn:incoming>flow_tat_breach</bpmn:incoming>
      <bpmn:outgoing>flow_tat_escalated</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:endEvent id="End_TatEscalated">
      <bpmn:incoming>flow_tat_escalated</bpmn:incoming>
    </bpmn:endEvent>

    <bpmn:exclusiveGateway id="Gateway_ReviewOutcome" name="Reviewer decision?">
      <bpmn:incoming>flow_review_done</bpmn:incoming>
      <bpmn:outgoing>flow_review_approved</bpmn:outgoing>
      <bpmn:outgoing>flow_review_denied</bpmn:outgoing>
    </bpmn:exclusiveGateway>

    <bpmn:serviceTask id="Task_RecordDenial" name="Record adverse determination"
                      camunda:topic="bh-record-denial">
      <bpmn:documentation>
        Persists the rule path and the reviewer's credential alongside the
        determination. Every adverse determination must trace to an applied,
        published criterion -- that is a parity requirement, not a nicety.
      </bpmn:documentation>
      <bpmn:incoming>flow_review_denied</bpmn:incoming>
      <bpmn:incoming>flow_denied_admin</bpmn:incoming>
      <bpmn:outgoing>flow_to_notify_denied</bpmn:outgoing>
    </bpmn:serviceTask>

    <!-- Approval schedules its own next review. This is the loop. -->
    <bpmn:serviceTask id="Task_ScheduleReview" name="Schedule continued-stay review"
                      camunda:topic="bh-schedule-review">
      <bpmn:documentation>
        Writes next_review_due from the GRANTED LEVEL, not from the units
        approved. An approval with no scheduled review is an authorization
        nobody will look at again.
      </bpmn:documentation>
      <bpmn:incoming>flow_approved</bpmn:incoming>
      <bpmn:incoming>flow_review_approved</bpmn:incoming>
      <bpmn:outgoing>flow_to_continued_stay</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:userTask id="Task_ContinuedStayReview" name="Continued-stay review"
                   camunda:candidateGroups="{GROUP_NURSE},{GROUP_PHYSICIAN}"
                   camunda:formKey="bh-continued-stay">
      <bpmn:documentation>
        Offers continue, step down, or discharge. STEP UP IS NOT OFFERED: an
        increase in level of care is a new determination with its own
        turnaround clock and its own appeal rights.
      </bpmn:documentation>
      <bpmn:incoming>flow_to_continued_stay</bpmn:incoming>
      <bpmn:outgoing>flow_cs_done</bpmn:outgoing>
    </bpmn:userTask>

    <!-- The regulatory deadline. Interrupting, because a missed continued-stay
         review is a compliance event and not a notification. -->
    <bpmn:boundaryEvent id="Timer_ReviewDue" attachedToRef="Task_ContinuedStayReview"
                        cancelActivity="true">
      <bpmn:timerEventDefinition>
        <bpmn:timeDuration xsi:type="bpmn:tFormalExpression"
                           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        >${{reviewInterval}}</bpmn:timeDuration>
      </bpmn:timerEventDefinition>
      <bpmn:outgoing>flow_review_overdue</bpmn:outgoing>
    </bpmn:boundaryEvent>

    <bpmn:serviceTask id="Task_EscalateOverdue" name="Escalate overdue review"
                      camunda:topic="bh-escalate-overdue">
      <bpmn:incoming>flow_review_overdue</bpmn:incoming>
      <bpmn:outgoing>flow_overdue_back</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:exclusiveGateway id="Gateway_ContinuedStay" name="Continued stay?">
      <bpmn:incoming>flow_cs_done</bpmn:incoming>
      <bpmn:incoming>flow_overdue_back</bpmn:incoming>
      <bpmn:outgoing>flow_review_back</bpmn:outgoing>
      <bpmn:outgoing>flow_discharged</bpmn:outgoing>
    </bpmn:exclusiveGateway>

    <bpmn:serviceTask id="Task_NotifyDecision" name="Notify determination"
                      camunda:topic="bh-notify">
      <bpmn:documentation>
        Consent-scoped. A consent of AUTH_DECISION_ONLY permits the
        determination and NOT the clinical narrative; the notification payload
        is built from the scope, not from the entity.
      </bpmn:documentation>
      <bpmn:incoming>flow_to_notify_denied</bpmn:incoming>
      <bpmn:incoming>flow_discharged</bpmn:incoming>
      <bpmn:outgoing>flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:endEvent id="End_Complete" name="Episode closed">
      <bpmn:incoming>flow_to_end</bpmn:incoming>
    </bpmn:endEvent>

    <bpmn:sequenceFlow id="flow_to_decision" sourceRef="Start_Submitted" targetRef="Task_LocDecision" />
    <bpmn:sequenceFlow id="flow_to_gateway" sourceRef="Task_LocDecision" targetRef="Gateway_Outcome" />
    <bpmn:sequenceFlow id="flow_approved" sourceRef="Gateway_Outcome" targetRef="Task_ScheduleReview">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      >${{locDecision.outcome == "APPROVED"}}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="flow_pended" sourceRef="Gateway_Outcome" targetRef="Task_ClinicalReview">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      >${{locDecision.outcome == "PENDED"}}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="flow_denied_admin" sourceRef="Gateway_Outcome" targetRef="Task_RecordDenial">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      >${{locDecision.outcome == "DENIED"}}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="flow_review_done" sourceRef="Task_ClinicalReview" targetRef="Gateway_ReviewOutcome" />
    <bpmn:sequenceFlow id="flow_review_approved" sourceRef="Gateway_ReviewOutcome" targetRef="Task_ScheduleReview" />
    <bpmn:sequenceFlow id="flow_review_denied" sourceRef="Gateway_ReviewOutcome" targetRef="Task_RecordDenial" />
    <bpmn:sequenceFlow id="flow_tat_breach" sourceRef="Timer_Turnaround" targetRef="Task_EscalateTat" />
    <bpmn:sequenceFlow id="flow_tat_escalated" sourceRef="Task_EscalateTat" targetRef="End_TatEscalated" />
    <bpmn:sequenceFlow id="flow_to_continued_stay" sourceRef="Task_ScheduleReview" targetRef="Task_ContinuedStayReview" />
    <bpmn:sequenceFlow id="flow_cs_done" sourceRef="Task_ContinuedStayReview" targetRef="Gateway_ContinuedStay" />
    <bpmn:sequenceFlow id="flow_review_overdue" sourceRef="Timer_ReviewDue" targetRef="Task_EscalateOverdue" />
    <bpmn:sequenceFlow id="flow_overdue_back" sourceRef="Task_EscalateOverdue" targetRef="Gateway_ContinuedStay" />
    <!-- THE LOOP. Continued stay re-enters the decision. -->
    <bpmn:sequenceFlow id="flow_review_back" sourceRef="Gateway_ContinuedStay" targetRef="Task_LocDecision">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      >${{csOutcome != "DISCHARGED"}}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="flow_discharged" sourceRef="Gateway_ContinuedStay" targetRef="Task_NotifyDecision">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      >${{csOutcome == "DISCHARGED"}}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="flow_to_notify_denied" sourceRef="Task_RecordDenial" targetRef="Task_NotifyDecision" />
    <bpmn:sequenceFlow id="flow_to_end" sourceRef="Task_NotifyDecision" targetRef="End_Complete" />

  </bpmn:process>
</bpmn:definitions>
"""


def default_spec() -> dict:
    """The minimum a behavioral-health process has to declare."""
    return {
        "continued_stay_loop": True,
        "review_timer": True,
        "escalation": True,
        "candidate_groups": {
            "Task_ClinicalReview": "${reviewerGroup}",
            "Task_ContinuedStayReview": f"{GROUP_NURSE},{GROUP_PHYSICIAN}",
        },
    }
