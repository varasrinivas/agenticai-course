"""Trap 3a -- the process must loop.

A medical prior-auth case has one decision. A behavioral-health case has an
initial decision plus a series of continued-stay reviews on a cadence set by
level of care, until discharge or step-down.

The reference platform's process is one-shot. Port it verbatim and approval
becomes terminal, which deletes the single biggest structural difference
between the two domains -- silently, because the diagram still looks complete.
"""

import xml.etree.ElementTree as ET

import pytest

import bpmn_writer as B
import validation
from rules_ir import REVIEW_INTERVAL, review_interval


def emit(tmp_path, xml, name="bh-prior-auth.bpmn"):
    d = tmp_path / "camunda"
    d.mkdir(exist_ok=True)
    (d / name).write_text(xml, encoding="utf-8")
    return str(tmp_path)


ONE_SHOT = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="p" isExecutable="true">
    <bpmn:startEvent id="Start"/>
    <bpmn:serviceTask id="Task_AutoDecision"/>
    <bpmn:exclusiveGateway id="Gateway_NeedsReview"/>
    <bpmn:userTask id="Task_ManualReview"/>
    <bpmn:serviceTask id="Task_NotifyDecision"/>
    <bpmn:endEvent id="End"/>
    <bpmn:sequenceFlow id="f1" sourceRef="Start" targetRef="Task_AutoDecision"/>
    <bpmn:sequenceFlow id="f2" sourceRef="Task_AutoDecision" targetRef="Gateway_NeedsReview"/>
    <bpmn:sequenceFlow id="f3" sourceRef="Gateway_NeedsReview" targetRef="Task_ManualReview"/>
    <bpmn:sequenceFlow id="f4" sourceRef="Gateway_NeedsReview" targetRef="Task_NotifyDecision"/>
    <bpmn:sequenceFlow id="f5" sourceRef="Task_ManualReview" targetRef="Task_NotifyDecision"/>
    <bpmn:sequenceFlow id="f6" sourceRef="Task_NotifyDecision" targetRef="End"/>
  </bpmn:process>
</bpmn:definitions>
"""


# ------------------------------------------------- the reference platform


def test_a_verbatim_port_of_the_one_shot_process_is_caught(tmp_path):
    """All three findings at once: no loop, no timer, unassigned review task."""
    root = emit(tmp_path, ONE_SHOT)
    c = validation.check_workflow(root)
    details = " ".join(f.detail for f in c.findings)
    assert "does not loop" in details
    assert "no timer" in details
    assert "no assignee or candidate group" in details


def test_the_reference_platform_process_really_is_one_shot(reference_root):
    """Read from the vendored donor, not asserted from memory."""
    import os
    path = os.path.join(reference_root, "camunda", "prior-auth.bpmn")
    text = open(path, encoding="utf-8").read()
    edges = []
    import re
    for tag in re.findall(r"<(?:\w+:)?sequenceFlow\b[^>]*>", text):
        s = re.search(r'sourceRef="([^"]+)"', tag)
        t = re.search(r'targetRef="([^"]+)"', tag)
        if s and t:
            edges.append((s.group(1), t.group(1)))
    assert not validation._has_cycle(edges), "the donor process is expected to be one-shot"
    assert "timerEventDefinition" not in text
    assert "candidateGroups" not in text


# ------------------------------------------------------- what we generate


def test_the_generated_process_loops(tmp_path):
    root = emit(tmp_path, B.render())
    c = validation.check_workflow(root)
    assert not any("does not loop" in f.detail for f in c.findings)


def test_the_generated_process_has_a_timer_and_escalation(tmp_path):
    xml = B.render()
    assert xml.count("timerEventDefinition") >= 2      # turnaround AND cadence
    assert "Task_EscalateOverdue" in xml
    assert "Task_EscalateTat" in xml


def test_the_generated_process_is_clean(tmp_path):
    root = emit(tmp_path, B.render())
    assert validation.check_workflow(root).count == 0


def test_the_generated_process_is_well_formed():
    ET.fromstring(B.render())


# --------------------------------------------------------- the preflight


@pytest.mark.parametrize("missing,expected", [
    ("continued_stay_loop", "does not loop"),
    ("review_timer", "no timer"),
    ("escalation", "no escalation path"),
])
def test_the_writer_refuses_an_incomplete_process(missing, expected):
    spec = B.default_spec()
    spec[missing] = False
    with pytest.raises(B.BpmnEmitError, match=expected):
        B.render(spec)


def test_the_writer_refuses_a_process_with_no_candidate_groups():
    spec = B.default_spec()
    spec["candidate_groups"] = {}
    with pytest.raises(B.BpmnEmitError, match="candidate group"):
        B.render(spec)


# ----------------------------------------------------------- the cadence


def test_cadence_follows_the_level_not_the_units():
    """A 14-day approval at ASAM 3.5 still returns for review in 7 days."""
    assert review_interval("4.0") == 3
    assert review_interval("3.7") == 5
    assert review_interval("3.5") == 7
    assert review_interval("1.0") == 90


def test_every_asam_level_has_a_cadence():
    for loc in ("1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0"):
        assert loc in REVIEW_INTERVAL


def test_the_cadence_table_is_in_the_generated_process():
    """The durations have to reach the process, not just the docs."""
    xml = B.render()
    for loc, days in REVIEW_INTERVAL.items():
        assert f"{loc} -> P{days}D" in xml


def test_approval_schedules_its_own_next_review():
    xml = B.render()
    assert "Task_ScheduleReview" in xml
    assert 'sourceRef="Gateway_Outcome" targetRef="Task_ScheduleReview"' in xml
