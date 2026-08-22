"""Trap 2 -- the clinical field validated, then discarded.

The reference platform's intake DTO validates its free-text field and then
drops it: not a column, not an entity field, not in either event payload. The
caller gets a 201 and believes the data landed.

In behavioral health that field is simultaneously the medical-necessity
evidence a reviewer reads AND the 42 CFR Part 2 protected content. Two failures
at once, and the successful HTTP status hides both.

The check asserts against the migration, not the DTO -- because asserting
against the DTO is exactly the mistake that lets this through.
"""

import os

import validation


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def test_validated_then_discarded_is_caught(tmp_path):
    """The reference platform's exact behaviour, reproduced."""
    root = str(tmp_path)
    write(root, "apps/bh-intake-svc/dto/SubmitAuthDto.ts", """
        export class SubmitAuthDto {
          @IsString() memberId: string;
          @IsOptional() @IsString() @Length(0, 4000) clinicalNarrative?: string;
        }
    """)
    write(root, "apps/bh-case-svc/db/migration/V1__init.sql", """
        CREATE TABLE bh_auth (
          auth_id BIGSERIAL PRIMARY KEY,
          member_id VARCHAR(32) NOT NULL,
          requested_loc VARCHAR(8) NOT NULL
        );
    """)
    c = validation.check_narrative_roundtrip(root)
    assert c.count >= 1
    assert "discarded" in c.findings[0].detail


def test_full_round_trip_is_clean(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-intake-svc/dto/SubmitAuthDto.ts",
          "export class SubmitAuthDto { @IsString() clinicalNarrative?: string; }")
    write(root, "apps/bh-case-svc/db/migration/V1__init.sql", """
        CREATE TABLE bh_auth (
          auth_id BIGSERIAL PRIMARY KEY,
          clinical_narrative TEXT
        );
    """)
    write(root, "apps/bh-case-svc/domain/Authorization.java", """
        @Entity public class Authorization {
          @Column(name = "clinical_narrative") private String clinicalNarrative;
        }
    """)
    assert validation.check_narrative_roundtrip(root).count == 0


def test_column_without_an_entity_field_is_caught(tmp_path):
    """A column nothing maps to is a column nothing writes."""
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/db/migration/V1__init.sql",
          "CREATE TABLE bh_auth (auth_id BIGSERIAL, clinical_narrative TEXT);")
    write(root, "apps/bh-case-svc/domain/Authorization.java",
          "@Entity public class Authorization { private Long authId; }")
    c = validation.check_narrative_roundtrip(root)
    assert any("no entity field" in f.detail for f in c.findings)


def test_no_column_at_all_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-case-svc/db/migration/V1__init.sql",
          "CREATE TABLE bh_auth (auth_id BIGSERIAL PRIMARY KEY);")
    assert validation.check_narrative_roundtrip(root).count >= 1


def test_check_is_expected_to_be_nonzero_on_a_naive_port(tmp_path):
    c = validation.check_narrative_roundtrip(str(tmp_path))
    assert c.expected_nonzero


def test_the_legacy_system_does_persist_it(legacy_root):
    """Baseline. The thing being replaced gets this right, which is why losing
    it in the port is a regression rather than a known gap."""
    schema = os.path.join(legacy_root, "db", "01_schema.sql")
    with open(schema, encoding="utf-8") as fh:
        ddl = fh.read()
    assert "CLINICAL_NARRATIVE" in ddl
    assert "CLOB" in ddl
