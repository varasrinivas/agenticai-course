"""Trap 4 -- a decision table that cannot deny.

The reference platform's table has three rules, no diagnosis input, and no rule
that can output DENIED. Mirroring its shape produces a level-of-care engine
that approves everything and can never produce a criterion-traceable denial.

In behavioral health the denial is the REGULATED EVENT: parity requires each
adverse determination to trace to a published, applied criterion. An engine
that cannot deny leaves the organisation unable to answer the comparative
question for any individual case.

Note the distinction this file draws and the lab keeps drawing: "cannot deny"
is a defect; "must not deny HERE" is a control. Branch 9 pends on purpose.
"""

import copy
import xml.etree.ElementTree as ET

import pytest

import dmn_writer as D
import validation


def emit(tmp_path, xml, name="bh-loc-decision.dmn"):
    d = tmp_path / "camunda"
    d.mkdir(exist_ok=True)
    (d / name).write_text(xml, encoding="utf-8")
    return str(tmp_path)


# ------------------------------------------------- the reference platform


def test_the_donor_table_cannot_deny(reference_root):
    """Read from the vendored donor rather than asserted from memory."""
    import os
    import re
    text = open(os.path.join(reference_root, "camunda", "pa-decision.dmn"),
                encoding="utf-8").read()
    outputs = set(re.findall(r"<outputEntry[^>]*>\s*<text>\s*\"?(\w+)\"?", text))
    upper = {o for o in outputs if o.isupper()}
    assert "DENIED" not in upper, "the donor is expected to be unable to deny"
    assert upper <= {"APPROVED", "PENDED"}

    inputs = " ".join(re.findall(r"<inputExpression[^>]*>\s*<text>([^<]*)", text))
    assert not re.search(r"diagnos|\bdx\b", inputs, re.I), \
        "the donor is expected to have no diagnosis input"


def test_mirroring_the_donor_shape_is_caught(tmp_path):
    root = emit(tmp_path, """<?xml version="1.0"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/">
  <decision id="d"><decisionTable id="t" hitPolicy="FIRST">
    <input id="i1"><inputExpression id="e1"><text>requestedUnits</text></inputExpression></input>
    <rule id="r1"><outputEntry id="o1"><text>"APPROVED"</text></outputEntry></rule>
    <rule id="r2"><outputEntry id="o2"><text>"PENDED"</text></outputEntry></rule>
  </decisionTable></decision>
</definitions>""")
    c = validation.check_decision_table(root)
    details = " ".join(f.detail for f in c.findings)
    assert "no rule can output DENIED" in details
    assert "no diagnosis input" in details


def test_a_table_with_no_hit_policy_is_caught(tmp_path):
    root = emit(tmp_path, """<?xml version="1.0"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/">
  <decision id="d"><decisionTable id="t">
    <input id="i1"><inputExpression id="e1"><text>diagnosis_block</text></inputExpression></input>
    <rule id="r1"><outputEntry id="o1"><text>"DENIED"</text></outputEntry></rule>
  </decisionTable></decision>
</definitions>""")
    assert any("no hit policy" in f.detail
               for f in validation.check_decision_table(root).findings)


# ---------------------------------------------------- the reference answer


def test_the_reference_table_can_deny(tmp_path, reference_ir):
    root = emit(tmp_path, D.render(reference_ir))
    assert validation.check_decision_table(root).count == 0


def test_the_reference_table_is_well_formed(reference_ir):
    ET.fromstring(D.render(reference_ir))


def test_the_reference_table_states_its_policy(reference_ir):
    xml = D.render(reference_ir)
    assert 'hitPolicy="UNIQUE"' in xml


def test_the_denial_is_reachable_and_administrative(reference_ir, golden_cases):
    """The one DENIED row fires on a terminated provider -- an administrative
    fact -- not on a clinical judgement."""
    import rules_ir as R
    terminated = next(c for c in golden_cases if c.network_status == "TERMED")
    d = R.evaluate_ir(reference_ir, terminated)
    assert d.outcome == "DENIED"
    assert d.reason_code == "PROV_TERMED"


# --------------------------------------------------------- the preflight


def test_the_writer_refuses_a_table_that_cannot_deny(reference_ir):
    ir = copy.deepcopy(reference_ir)
    for b in ir["branches"]:
        if (b.get("outputs") or {}).get("outcome") == "DENIED":
            b["outputs"]["outcome"] = "PENDED"
    with pytest.raises(D.DmnEmitError, match="DENIED"):
        D.render(ir)


def test_the_writer_refuses_a_table_with_no_diagnosis_input(reference_ir):
    ir = copy.deepcopy(reference_ir)
    ir["inputs"] = [i for i in ir["inputs"]
                    if not str(i["name"]).startswith("diagnosis")]
    with pytest.raises(D.DmnEmitError, match="diagnosis"):
        D.render(ir)


def test_the_writer_refuses_an_unjustified_hit_policy(reference_ir):
    ir = copy.deepcopy(reference_ir)
    ir["hit_policy_justification"] = ""
    with pytest.raises(D.DmnEmitError, match="justification"):
        D.render(ir)


def test_the_writer_refuses_an_unresolved_overlap(reference_ir):
    ir = copy.deepcopy(reference_ir)
    ir["overlaps"][0].pop("resolution")
    with pytest.raises(D.DmnEmitError, match="unresolved overlaps"):
        D.render(ir)


def test_the_writer_refuses_a_cell_it_cannot_express_honestly():
    """A cross-input exclusion cannot be one cell.

    The honest answer is a named derived input, not a guessed cell -- which is
    why the reference IR carries `overlap_upper`.
    """
    with pytest.raises(D.DmnEmitError, match="cannot express"):
        D.to_feel("score >= 8 and score >= 3 and score <= 9", "score")


def test_feel_cells_render_correctly():
    assert D.to_feel("score >= 8", "score") == ">=8"
    assert D.to_feel("dim1 < 4 and dim1 >= 3", "dim1") == "[3..4)"
    assert D.to_feel("cssrs == 3", "cssrs") == "3"
    assert D.to_feel("score >= 8", "dim1") == "-"


def test_the_generated_xml_escapes_comment_unsafe_prose(reference_ir):
    """`--` cannot appear inside an XML comment body.

    The hit-policy justification is prose written for humans, who use double
    dashes freely; interpolating it into a comment produced a file that looked
    fine and did not parse. Parsing the output is what caught it, which is why
    these tests parse rather than grep.
    """
    import re
    xml = D.render(reference_ir)
    ET.fromstring(xml)

    bodies = re.findall(r"<!--(.*?)-->", xml, re.S)
    assert bodies, "expected the generated table to carry explanatory comments"
    for body in bodies:
        assert "--" not in body, f"illegal `--` inside an XML comment: {body[:120]!r}"
