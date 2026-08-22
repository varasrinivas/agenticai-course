"""Trap 7 -- not everything may be a feature flag.

The reference platform gates capabilities behind flags so the stack stays
runnable with any subset enabled. That is its best structural idea and it is
worth mirroring.

But a cache flag and a consent flag are not the same kind of thing. The test to
apply, every time:

    If this were false in production for a week, is the consequence a slow
    system, or an unlawful disclosure?

A regulatory control that can be switched off in configuration is not a
control. It is a default.
"""

import os

import validation
from gap_register import (MUST_NOT_PORT, GapEntry, GapRegister, RegisterError)


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ------------------------------------------------- the reference platform


def test_the_donor_gates_security_behind_a_flag(reference_root):
    """Defensible for a teaching platform. Indefensible here."""
    yml = os.path.join(reference_root, "apps", "um-case-svc", "src", "main",
                       "resources", "application.yml")
    text = open(yml, encoding="utf-8").read()
    assert "SECURITY_ENABLED" in text


def test_the_donor_has_a_flag_idiom_worth_copying(reference_root):
    """Seven of them, all in one place -- the layering that makes the platform
    runnable one capability at a time."""
    import tools_reference as T
    flags = T._scan_feature_flags()
    names = {f["flag"] for f in flags}
    assert {"EVENTS_ENABLED", "OUTBOX_ENABLED", "WORKFLOW_ENABLED",
            "CACHE_ENABLED", "SEARCH_ENABLED"} <= names
    assert len(names) >= 7


# ------------------------------------------------------------- the check


def test_a_capability_flag_is_fine(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/application.yml", """
        bh:
          cache-enabled: ${CACHE_ENABLED:false}
          search-enabled: ${SEARCH_ENABLED:false}
          events-enabled: ${EVENTS_ENABLED:true}
    """)
    assert validation.check_flag_classification(root).count == 0


def test_a_consent_flag_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/application.yml",
          "bh:\n  consent-enforcement: ${CONSENT_ENABLED:false}\n")
    c = validation.check_flag_classification(root)
    assert c.count == 1
    assert "unlawful disclosure, not a slow page" in c.findings[0].detail


def test_an_audit_flag_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/application.yml",
          "bh:\n  audit: ${AUDIT_ENABLED:true}\n")
    assert validation.check_flag_classification(root).count == 1


def test_a_licensure_flag_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "infra/helm/values.yaml", "env:\n  LICENSURE_CHECK_ENABLED: 'false'\n")
    assert validation.check_flag_classification(root).count == 1


def test_carrying_the_donors_security_flag_across_is_caught(tmp_path):
    """The specific mistake: mirroring the idiom uniformly, including onto the
    one capability that must not be optional."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/application.yml",
          "bh:\n  security-enabled: ${SECURITY_ENABLED:false}\n")
    assert validation.check_flag_classification(root).count == 1


def test_several_regulated_flags_are_all_reported(tmp_path):
    root = str(tmp_path)
    write(root, "a/application.yml", "x: ${CONSENT_ENABLED:false}")
    write(root, "b/values.yaml", "y: ${PART2_REDISCLOSURE_ENABLED:false}")
    write(root, "c/config.ts", "const f = process.env.DISCLOSURE_LOG_ENABLED;")
    assert validation.check_flag_classification(root).count == 3


# ------------------------------------------------- the register's verdict


def test_a_flag_gating_a_control_is_recorded_as_must_not_port():
    """The capability may be must-build-new; the FLAG is must-not-port. Two
    different statements about the same thing, and the register needs both."""
    reg = GapRegister()
    reg.add(GapEntry(
        capability="consent enforcement as a feature flag",
        verdict=MUST_NOT_PORT,
        evidence="the donor applies its flag idiom uniformly to all seven "
                 "capabilities, and ships SECURITY_ENABLED=false by default",
        harm="a week of CONSENT_ENABLED=false is unlawful disclosure, not "
             "degraded performance. A control that can be switched off in "
             "configuration is a default.",
        trap_id=7))
    assert len(reg.by_verdict(MUST_NOT_PORT)) == 1


def test_must_not_port_without_a_named_harm_is_refused():
    """The verdict people soften. Softening it is how a defect gets copied
    with a note attached."""
    reg = GapRegister()
    try:
        reg.add(GapEntry(capability="x", verdict=MUST_NOT_PORT,
                         evidence="it is not ideal"))
    except RegisterError as exc:
        assert "NAMED HARM" in str(exc)
    else:
        raise AssertionError("expected a must-not-port with no harm to be refused")
