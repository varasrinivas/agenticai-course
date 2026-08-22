"""Trap 8 -- the lost transaction boundary. The deepest one.

`AuthCaseService.submitAndDecide()` writes five rows in one Oracle transaction.
Two of them -- the authorization and its 42 CFR Part 2 consent -- must commit
together, because an authorization from a protected program with no consent
record is protected content held with no record of who the member agreed it
could be shared with. Under the legacy design that state is unrepresentable.

Decomposed, it becomes representable again. The tests below assert both halves
of the check: that the STATE is clean, and that something ENFORCES it. The
second is the one that matters, because state can be clean today and reachable
tomorrow.
"""

import os

import pytest

import seam_map as S
import validation


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ------------------------------------------------------------ the schema


def test_no_consent_table_at_all_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql",
          "CREATE TABLE bh_auth (auth_id BIGSERIAL PRIMARY KEY);")
    c = validation.check_consent_atomicity(root)
    assert c.count == 1
    assert "no consent table" in c.findings[0].detail


def test_consent_table_with_nothing_enforcing_the_link_is_caught(tmp_path):
    """The naive port. A table exists, so it looks handled."""
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql", """
        CREATE TABLE bh_auth (auth_id BIGSERIAL PRIMARY KEY);
        CREATE TABLE bh_consent (
          consent_id BIGSERIAL PRIMARY KEY,
          auth_id BIGINT,
          recipient_name VARCHAR(120) NOT NULL
        );
    """)
    c = validation.check_consent_atomicity(root)
    assert c.count >= 1
    assert "clean today and reachable tomorrow" in c.findings[0].detail


def test_an_enforced_link_is_clean(tmp_path):
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql", """
        CREATE TABLE bh_consent (consent_id BIGSERIAL PRIMARY KEY);
        CREATE TABLE bh_auth (
          auth_id BIGSERIAL PRIMARY KEY,
          consent_id BIGINT NOT NULL REFERENCES bh_consent(consent_id)
        );
    """)
    assert validation.check_consent_atomicity(root).count == 0


# -------------------------------------------------------------- the seam


def test_a_seam_crossing_the_submit_transaction_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql", """
        CREATE TABLE bh_consent (consent_id BIGSERIAL PRIMARY KEY);
        CREATE TABLE bh_auth (auth_id BIGSERIAL PRIMARY KEY,
                              consent_id BIGINT NOT NULL REFERENCES bh_consent(consent_id));
    """)
    sm = {"seams": [{"name": "intake|case", "crosses": ["AuthCaseService.submitAndDecide"]}]}
    c = validation.check_consent_atomicity(root, sm)
    assert any("un-hold protected content" in f.detail for f in c.findings)


# ------------------------------------------- the seam map refuses silence


def test_seam_map_refuses_a_seam_with_no_replacement():
    sm = S.SeamMap()
    sm.add_unit(S.TransactionalUnit(
        method="AuthCaseService.submitAndDecide",
        writes=[S.Write("bh_auth", "the request", "anchor"),
                S.Write("bh_consent", "disclosure permission",
                        "protected content with no record of consent")]))
    with pytest.raises(S.SeamError, match="no replacement|not an answer"):
        sm.add_seam(S.Seam(name="intake|case", left="intake", right="case",
                           crosses=["AuthCaseService.submitAndDecide"]))


def test_seam_map_refuses_an_incomplete_replacement():
    """An eventual consistency with no observable and no alarm is the same as
    no guarantee, implemented with more moving parts."""
    sm = S.SeamMap()
    with pytest.raises(S.SeamError, match="missing"):
        sm.add_seam(S.Seam(
            name="case|notify", left="case", right="notify",
            crosses=["AuthCaseService.submitAndDecide"],
            replacement=S.AtomicityReplacement(
                mechanism="outbox", window="", observable="",
                compensation="", alarm="")))


def test_seam_map_refuses_to_cut_a_must_be_atomic_pair():
    """Sometimes the right answer is that the seam moves."""
    sm = S.SeamMap()
    with pytest.raises(S.SeamError, match="cannot be cut here"):
        sm.add_seam(S.Seam(
            name="auth|consent", left="case", right="consent",
            crosses=["AuthCaseService.submitAndDecide"],
            coupling=S.MUST_BE_ATOMIC))


def test_a_rejected_seam_is_a_legitimate_result():
    """Recording that a seam was considered and rejected is an answer, and it
    is the answer for the authorization/consent pair."""
    sm = S.SeamMap()
    seam = sm.add_seam(S.Seam(
        name="auth|consent", left="case", right="consent",
        crosses=["AuthCaseService.submitAndDecide"],
        coupling=S.MUST_BE_ATOMIC,
        rejected_because="an authorization from a Part 2 program without its "
                         "consent record is content we cannot lawfully act on, "
                         "and a disclosure does not compensate"))
    assert seam not in sm.accepted_seams()


def test_a_complete_replacement_is_accepted():
    sm = S.SeamMap()
    sm.add_seam(S.Seam(
        name="case|notify", left="case", right="notify",
        crosses=["AuthCaseService.submitAndDecide"],
        replacement=S.AtomicityReplacement(
            mechanism="transactional outbox + idempotent consumer keyed on authId",
            window="under 60s at the configured relay interval",
            observable="outbox_event WHERE published_at IS NULL "
                       "AND created_at < now() - interval '5 minutes'",
            compensation="relay retries; rows past 3 attempts go to a human queue",
            alarm="that count > 0 for 5 consecutive minutes")))
    assert len(sm.accepted_seams()) == 1


def test_a_write_with_no_recorded_reason_is_reported():
    """The `why_atomic` column is the one most likely to be undocumented, and
    it is the one that decides whether a pair can be split at all."""
    sm = S.SeamMap()
    sm.add_unit(S.TransactionalUnit(
        method="AuthCaseService.submitAndDecide",
        writes=[S.Write("bh_auth", "the request", "anchor"),
                S.Write("bh_consent", "disclosure permission", "")]))
    assert any("bh_consent" in p for p in sm.problems())


def test_the_legacy_transaction_really_does_write_five_rows(legacy_root):
    """Baseline, read from the fixture rather than asserted from memory."""
    path = os.path.join(legacy_root, "src", "main", "java", "com", "bridgeway",
                        "bhauth", "service", "AuthCaseService.java")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    assert "@Transactional" in src
    for dao in ("authDao.insert", "assessmentDao.insertAsamDimension",
                "consentDao.insert", "locReviewDao.insert", "queueDao.enqueue"):
        assert dao in src, f"{dao} missing from the submit path"
