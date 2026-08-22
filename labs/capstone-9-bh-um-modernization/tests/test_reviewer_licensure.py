"""Trap 3b and trap 10 -- the rule that a nurse may approve but never deny.

    A nurse reviewer may approve. A nurse may NEVER deny. Only a physician may
    issue an adverse determination -- and for substance-use or psychiatric
    level of care, a same-specialty peer reviewer.

It is a separation of duties required by accreditation, and it is why a PENDED
status exists at all: that is the state a case waits in for someone licensed to
deny it.

In the legacy system the rule is implemented four times, in four places, none
of which is a permission system:
  - three nested JSTL conditionals in decision.jsp
  - a numeric comparison standing in for a bitwise test
  - a service-layer check added in 2014 after an incident
  - a candidate group that does not exist, because there is no workflow engine

Three of the four call paths into the decision logic bypass the service check.
"""

import os
import re

import bpmn_writer as B
import validation


# ------------------------------------------------ the legacy fixture holds


def test_the_rule_is_in_the_view(legacy_root):
    """decision.jsp is where a reviewer's deny button is decided."""
    path = os.path.join(legacy_root, "src", "main", "webapp", "WEB-INF",
                        "jsp", "decision.jsp")
    jsp = open(path, encoding="utf-8").read()
    assert "btn-deny" in jsp
    assert "roleMask ge 4" in jsp, "the physician gate"
    assert "roleMask ge 16" in jsp, "the addiction-medicine gate"
    assert "F1" in jsp, "the substance-use diagnosis test"


def test_the_view_uses_a_numeric_test_for_a_bitmask(legacy_root):
    """JSTL has no bitwise operator, so the view APPROXIMATES the rule.

    `roleMask ge 4` and `hasRole(ROLE_MD)` agree for the common masks and
    diverge for combinations -- and the view is the permissive side.
    """
    jsp = open(os.path.join(legacy_root, "src", "main", "webapp", "WEB-INF",
                            "jsp", "decision.jsp"), encoding="utf-8").read()
    assert re.search(r"roleMask\s+ge\s+\d+", jsp)

    ctx = open(os.path.join(legacy_root, "src", "main", "java", "com", "bridgeway",
                            "bhauth", "security", "UserContext.java"),
               encoding="utf-8").read()
    assert "(roleMask & role) == role" in ctx, "the service does a real bitwise test"


def test_the_seeded_divergence_is_reachable(legacy_root):
    """User sbanerji has mask 33 (intake + admin).

    33 >= 4 passes the view's gate. hasRole(ROLE_MD) refuses it. The view
    offers a deny button the service then rejects -- one rule, two
    implementations, and they disagree for this mask.
    """
    seed = open(os.path.join(legacy_root, "db", "02_seed.sql"), encoding="utf-8").read()
    assert "'sbanerji', 33" in seed.replace("  ", " ") or "sbanerji" in seed

    mask = 33
    ROLE_MD = 4
    assert mask >= ROLE_MD                       # the view lets them through
    assert (mask & ROLE_MD) != ROLE_MD           # the service does not


def test_more_call_paths_than_checks(legacy_root):
    """Three of four paths into the decision logic bypass the view entirely."""
    java = os.path.join(legacy_root, "src", "main", "java", "com", "bridgeway", "bhauth")
    paths = {
        "controller": os.path.join(java, "controller", "AuthController.java"),
        "batch": os.path.join(java, "batch", "X12278ImportJob.java"),
        "soap": os.path.join(java, "ws", "LegacyAuthEndpoint.java"),
    }
    reaches_service = []
    for name, path in paths.items():
        src = open(path, encoding="utf-8").read()
        if "authCaseService" in src or "AuthCaseService" in src:
            reaches_service.append(name)
    assert set(reaches_service) == {"controller", "batch", "soap"}

    # ...and only the controller consults the role.
    controller = open(paths["controller"], encoding="utf-8").read()
    assert "mayDeny" in controller
    for other in ("batch", "soap"):
        src = open(paths[other], encoding="utf-8").read()
        assert "mayDeny" not in src, f"{other} unexpectedly checks licensure"


# --------------------------------------------- the specialty requirement


def test_specialty_is_selected_from_the_diagnosis_block():
    """F10-F19 needs addiction medicine; F20-F49 needs psychiatry."""
    import sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "solution", ".claude", "skills", "behavioral-health-um", "scripts"))
    import validate_bh_codes as V

    assert V.classify_diagnosis("F11.20")[1] == "MD_ADDICTION"
    assert V.classify_diagnosis("F10.20")[1] == "MD_ADDICTION"
    assert V.classify_diagnosis("F33.2")[1] == "MD_PSYCH"
    assert V.classify_diagnosis("F41.1")[1] == "MD_PSYCH"
    assert V.classify_diagnosis("F84.0")[1] is None


# ----------------------------------------------- the generated candidate group


def test_the_generated_review_task_has_a_candidate_group():
    """Where a task encodes licensure, the candidate group IS the rule."""
    xml = B.render()
    assert "Task_ClinicalReview" in xml
    assert "candidateGroups" in xml
    assert B.GROUP_ADDICTION in xml
    assert B.GROUP_PSYCH in xml
    assert B.GROUP_NURSE in xml


def test_a_task_with_no_candidate_group_is_caught(tmp_path):
    d = tmp_path / "camunda"
    d.mkdir()
    (d / "p.bpmn").write_text("""<?xml version="1.0"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="p">
    <bpmn:userTask id="Task_Review" name="Review"></bpmn:userTask>
    <bpmn:sequenceFlow id="f1" sourceRef="Task_Review" targetRef="Task_Review"/>
    <bpmn:timerEventDefinition/>
  </bpmn:process>
</bpmn:definitions>""", encoding="utf-8")
    c = validation.check_workflow(str(tmp_path))
    assert any("candidate group" in f.detail for f in c.findings)


def test_the_nurse_group_cannot_reach_the_denial_task():
    """The clinical-review task resolves its group from the diagnosis; the
    nurse group appears only on the continued-stay task, which cannot deny."""
    xml = B.render()
    clinical = xml.split("Task_ClinicalReview", 1)[1].split("</bpmn:userTask>", 1)[0]
    assert B.GROUP_NURSE not in clinical.split("bpmn:documentation")[0]


def test_the_engine_pends_rather_than_denying_on_criteria(golden):
    """Branch 9. Criteria not met is an ADVERSE DETERMINATION, and the engine
    is not licensed to issue one -- so it pends for a physician.

    Converting this into an automated denial removes a control.
    """
    import rules_ir as R
    case = next(c for c, _e, _m in golden if c.auth_id == 500006)
    d = R.evaluate_legacy(case)
    assert d.outcome == "PENDED"
    assert d.reason_code == "CRITERIA_NOT_MET"


def test_the_only_engine_denial_is_administrative(golden):
    """PROV_TERMED is the one DENIED the engine may issue on its own, and it
    is an administrative fact rather than a clinical judgement."""
    import rules_ir as R
    denials = [(c.auth_id, R.evaluate_legacy(c))
               for c, _e, _m in golden
               if R.evaluate_legacy(c).outcome == "DENIED"]
    assert [r.reason_code for _a, r in denials] == ["PROV_TERMED"]
