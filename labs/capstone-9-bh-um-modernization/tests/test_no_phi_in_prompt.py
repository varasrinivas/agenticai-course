"""The hard constraint: no PHI in prompts, ever.

This is the one check that must report ZERO. The other four negative checks
exist to find flaws in the port; this one exists to prove the gate that lets an
agent read a regulated codebase at all is actually working.

The gate detects by SHAPE, not by keyword. A clinical narrative does not
announce itself, and matching on "alcohol" or "opioid" catches the obvious
cases while missing everything a clinician wrote in a hurry.
"""

import asyncio

import pytest
from claude_agent_sdk import PermissionResultDeny

import config
import hooks


# ------------------------------------------------------------- detection


def test_planted_narrative_is_detected(narrative):
    assert hooks.looks_like_protected_content(narrative)


@pytest.mark.parametrize("text", [
    "public class AuthDao { private JdbcTemplate jdbc; public Auth findById(long id) "
    "{ return jdbc.queryForObject(SQL, MAPPER); } }",
    "CREATE TABLE BH_LOC_REVIEW (REVIEW_ID NUMBER(12) NOT NULL, AUTH_ID NUMBER(12));",
    "bhauth.db.url=jdbc:oracle:thin:@//host:1521/BHAUTH\nbhauth.smtp.host=relay",
    "<c:if test=\"${sessionScope.roleMask ge 2}\"><pre>${auth.clinicalNarrative}</pre></c:if>",
    "",
    "short",
])
def test_code_and_config_are_not_flagged(text):
    """Over-eager gates get switched off. The JSTL case matters especially:
    a template REFERENCING the field is not the field's contents."""
    assert not hooks.looks_like_protected_content(text)


def test_detection_is_by_shape_not_by_keyword():
    """Prose with clinical register and no give-away vocabulary."""
    prose = (
        "The individual was seen twice in the preceding fortnight and reports "
        "that the previously agreed plan has not been followed. Engagement with "
        "the community team remains inconsistent. A step up in structure is "
        "requested pending review."
    )
    assert hooks.looks_like_protected_content(prose)


# ------------------------------------------------------------- allowlist


def test_only_the_synthetic_fixture_is_allowlisted():
    assert hooks.is_allowlisted(config.PHI_ALLOWLIST[0])
    assert not hooks.is_allowlisted(config.LEGACY_ROOT + "/src/AuthCaseService.java")
    assert not hooks.is_allowlisted(None)
    assert not hooks.is_allowlisted("/etc/passwd")


def test_allowlist_does_not_leak_via_prefix():
    """`/x/02_seed.sql.bak` must not inherit `/x/02_seed.sql`'s allowance."""
    assert not hooks.is_allowlisted(config.PHI_ALLOWLIST[0] + ".bak")


# ------------------------------------------------------------ redaction


def test_redaction_leaves_no_clinical_sentence_standing(narrative):
    """The trailing-sentence bug.

    An earlier version required whitespace after the final full stop, so the
    LAST sentence of every narrative survived redaction. One clinical sentence
    is a disclosure.
    """
    out = hooks.redact_narrative(narrative)
    for word in ("ideation", "triage", "inpatient", "stabilisation",
                 "emergency", "irregular"):
        assert word not in out, f"{word!r} survived redaction"
    assert "PROTECTED-CONTENT-REDACTED" in out


def test_redaction_is_tagged_not_silent(narrative):
    """The model must know something was withheld.

    Silently removing it leads the model to conclude the field is empty and
    report the clinical narrative as absent -- the opposite of the finding.
    """
    out = hooks.redact_narrative(narrative)
    assert "REDACTED" in out
    assert "chars" in out


# ------------------------------------------------------- the result gate


def test_result_from_a_non_allowlisted_path_is_redacted(narrative):
    text, modified = hooks.filter_tool_result(
        "mcp__legacy_src__legacy_read_java",
        {"fqcn": config.LEGACY_ROOT + "/src/AuthCaseService.java"}, narrative)
    assert modified
    assert "ideation" not in text
    assert "not on the synthetic-fixture allowlist" in text


def test_result_from_the_fixture_is_budgeted_not_blocked(narrative):
    """Synthetic content passes, but an agent reading the whole seed file
    accumulates a clinical record in its transcript one call at a time."""
    long_text = narrative * 6
    text, modified = hooks.filter_tool_result(
        "mcp__legacy_src__legacy_read_sql",
        {"path": config.PHI_ALLOWLIST[0]}, long_text)
    assert modified
    assert len(text) < len(long_text)
    assert "excerpt budget" in text


def test_ordinary_content_passes_through_untouched():
    code = "public void decide(long id) { service.evaluate(id); }"
    text, modified = hooks.filter_tool_result("x", {"path": "/a/B.java"}, code)
    assert not modified and text == code


# ------------------------------------------------------------- the hook


def test_writing_narrative_into_an_artifact_is_denied(narrative):
    result = asyncio.run(hooks.can_use_tool(
        "mcp__local__write_artifact",
        {"relative_path": "apps/bh-case-svc/Fixture.java", "content": narrative},
        None))
    assert isinstance(result, PermissionResultDeny)
    assert "no PHI in prompts" in result.message


def test_narrative_in_gap_evidence_is_denied(narrative):
    """Evidence fields are prose, which makes them the natural place to paste
    a narrative while explaining why it matters."""
    result = asyncio.run(hooks.can_use_tool(
        "mcp__local__record_gap",
        {"capability": "narrative handling", "verdict": "extend",
         "evidence": narrative}, None))
    assert isinstance(result, PermissionResultDeny)


def test_the_gate_reports_zero_against_the_real_fixtures():
    """THE ASSERTION THAT MATTERS.

    Walk every file in the legacy tree that is NOT the synthetic seed, and
    confirm none of them would reach the model carrying narrative-shaped
    content. This is the check that must be zero.
    """
    import os

    leaks = []
    for dirpath, dirnames, filenames in os.walk(config.LEGACY_ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", "target"}]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if hooks.is_allowlisted(path):
                continue
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    raw = fh.read()
            except OSError:
                continue
            filtered, _ = hooks.filter_tool_result("read", {"path": path}, raw)
            if hooks.looks_like_protected_content(filtered):
                leaks.append(os.path.relpath(path, config.LEGACY_ROOT))

    assert leaks == [], f"protected content would reach the model from: {leaks}"
