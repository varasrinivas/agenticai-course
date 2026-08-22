"""Trap 5 -- 42 CFR Part 2 content reaching sinks that have no consent scope.

The legacy system logs the clinical narrative on purpose, for the appeals team,
into one rolling file. The reference platform logs member identifiers, ships
plain JSON to an unauthenticated broker, and indexes into Elasticsearch.

Port both faithfully and the same content reaches THREE sinks instead of one --
not because anyone decided to make it worse, but because fan-out is what a
distributed architecture does with a field.

These tests plant each leak and assert the check finds it.
"""

import os

import validation


def write(root: str, rel: str, content: str) -> str:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def test_clean_output_has_no_findings(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/CaseService.java", """
        public void decide(Auth auth) {
            log.info("decided authId={} outcome={}", auth.getId(), outcome);
        }
    """)
    assert validation.check_protected_content_leak(root).count == 0


def test_narrative_in_a_log_statement_is_found(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/CaseService.java", """
        public void decide(Auth auth) {
            log.info("decided authId={} narrative={}", auth.getId(),
                     auth.getClinicalNarrative());
        }
    """)
    c = validation.check_protected_content_leak(root)
    assert c.count == 1
    assert "log" in c.findings[0].detail


def test_narrative_in_an_event_payload_is_found(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-intake-svc/producer.ts", """
        const payload = { authId, memberId, clinicalNarrative: dto.clinicalNarrative };
        await this.producer.send({ topic: 'bh.submitted', payload });
    """)
    assert validation.check_protected_content_leak(root).count >= 1


def test_narrative_in_a_search_mapping_is_found(tmp_path):
    root = str(tmp_path)
    write(root, "infra/search/mapping.json",
          '{"mappings":{"properties":{"clinical_narrative":{"type":"text","index":true}}}}')
    assert validation.check_protected_content_leak(root).count >= 1


def test_narrative_in_an_audit_column_is_found(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/db/migration/V3__audit.sql", """
        CREATE TABLE bh_audit_event (
          audit_id BIGSERIAL PRIMARY KEY,
          old_narrative TEXT,
          new_narrative TEXT
        );
    """)
    assert validation.check_protected_content_leak(root).count >= 1


def test_an_error_path_leak_is_found(tmp_path):
    """The one people miss. A stack trace is a sink."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/Handler.java", """
        catch (Exception e) {
            throw new IllegalStateException("failed for narrative=" + clinicalNarrative);
        }
    """)
    assert validation.check_protected_content_leak(root).count >= 1


def test_a_comment_naming_the_field_is_not_a_leak(tmp_path):
    """Over-eager checks get switched off. Naming the field in a comment is
    how a developer warns the next one, and flagging it teaches the wrong
    lesson."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/CaseService.java", """
        // Do NOT log clinicalNarrative here -- it is Part 2 content and this
        // logger ships to the enterprise search index.
        log.info("decided authId={}", auth.getId());
    """)
    assert validation.check_protected_content_leak(root).count == 0


def test_fan_out_is_counted_per_sink(tmp_path):
    """One monolith log sink becomes several. The count going up IS the finding."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/A.java",
          'log.info("narrative=" + auth.getClinicalNarrative());')
    write(root, "apps/bh-intake-svc/b.ts",
          'const payload = { clinicalNarrative };')
    write(root, "infra/search/mapping.json",
          '{"properties":{"clinical_narrative":{"index":true}}}')
    c = validation.check_protected_content_leak(root)
    assert c.count >= 3
    assert len({f.where for f in c.findings}) >= 3


def test_check_reports_nothing_emitted_rather_than_passing(tmp_path):
    """An empty directory must not read as a clean bill of health."""
    c = validation.check_protected_content_leak(str(tmp_path / "nope"))
    assert c.count == 0
    assert "nothing emitted" in c.note


def test_a_check_that_scanned_nothing_is_not_a_pass(tmp_path):
    """Clean is suspicious when the check COULD NOT HAVE FIRED.

    Not when it is merely clean. A good port is supposed to come back clean on
    all four expected-non-zero checks; treating that as a failure would mean
    the reference answer could never pass, which is how a check teaches people
    to ignore it.

    What distinguishes the two is `scanned` -- did it look at anything.
    """
    c = validation.check_protected_content_leak(str(tmp_path))
    assert c.expected_nonzero
    assert c.count == 0
    assert c.scanned == 0
    assert "did not run" in c.suspect
    assert "suspect" in c.to_dict()


def test_a_clean_result_over_real_files_is_a_genuine_pass(tmp_path):
    """The other half. Scanned something, found nothing, no suspicion."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/CaseService.java",
          'log.info("decided authId={} outcome={}", auth.getId(), outcome);')
    c = validation.check_protected_content_leak(root)
    assert c.count == 0
    assert c.scanned >= 1
    assert c.suspect == ""
    assert "suspect" not in c.to_dict()
