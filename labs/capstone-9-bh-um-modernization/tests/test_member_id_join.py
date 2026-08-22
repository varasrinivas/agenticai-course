"""Trap 6 -- carve-out identity.

Behavioral health was contracted to a separate vendor with its own network, its
own criteria, its own claims platform and its own member identifiers. That
history is why `BH_MEMBER.MEMBER_ID` is Bridgeway's key rather than the health
plan's, and why `PLAN_MEMBER_ID` is nullable.

The reference platform stores one opaque `member_id VARCHAR(32)` with no member
table and no foreign key, so it accepts either identifier without objecting. A
1:1 port therefore matches BY LUCK for whichever subset of formats happens to
coincide, and fails silently for the rest.

That is the worst shape a defect can have: partial, silent, and plausible.
"""

import asyncio
import json
import os

import validation


def call(fn, **kw):
    return json.loads(asyncio.run(fn.handler(kw))["content"][0]["text"])


# --------------------------------------------------- the legacy fixture


def test_a_third_of_members_cannot_be_resolved_to_the_plan():
    """The documented figure is 31%. Computed here, not recalled."""
    import tools_legacy as L
    rc = call(L.legacy_row_count, table_name="BH_MEMBER")
    assert rc["row_count"] == 10
    assert rc["unresolved_to_plan"] == 3
    assert 25 <= rc["unresolved_pct"] <= 35


def test_plan_identifiers_are_not_unique():
    """The 2014 backfill matched on name and date of birth. Twins share both.

    MemberDao.findByPlanMemberId returns a LIST for this reason, and the search
    screen shows only the first -- so one twin's authorizations are invisible.
    """
    import tools_legacy as L
    rc = call(L.legacy_row_count, table_name="BH_MEMBER")
    assert rc["duplicate_plan_ids"] >= 1


def test_the_two_identifiers_have_different_formats(legacy_root):
    """BW-nnnnnnn versus a nine-digit string. Different enough that a wrong
    join fails loudly for most rows -- and quietly for the rest."""
    seed = open(os.path.join(legacy_root, "db", "02_seed.sql"), encoding="utf-8").read()
    assert "'BW-1000401','483920117'" in seed.replace(" ", "")


def test_the_legacy_schema_records_which_key_is_which(legacy_root):
    ddl = open(os.path.join(legacy_root, "db", "01_schema.sql"), encoding="utf-8").read()
    assert "MEMBER_ID" in ddl and "PLAN_MEMBER_ID" in ddl
    assert "PLAN_MEMBER_ID     VARCHAR2(24)," in ddl, "the plan's key is NULLABLE"


def test_the_drift_log_explains_the_problem(legacy_root):
    """BHA-1180. The reason this is discoverable at all."""
    log = open(os.path.join(legacy_root, "db", "schema_changes.txt"),
               encoding="utf-8").read()
    assert "BHA-1180" in log
    assert "31%" in log
    assert "quietly wrong" in log


# ------------------------------------------------------------- the check


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def test_a_single_opaque_identifier_is_caught(tmp_path):
    """The naive port: MEMBER_ID -> member_id, and nothing objects."""
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql", """
        CREATE TABLE bh_auth (
          auth_id BIGSERIAL PRIMARY KEY,
          member_id VARCHAR(32) NOT NULL
        );
    """)
    c = validation.check_identity(root)
    assert c.count == 1
    assert "matches by luck" in c.findings[0].detail


def test_carrying_both_identifiers_is_clean(tmp_path):
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql", """
        CREATE TABLE bh_member (
          member_id VARCHAR(24) PRIMARY KEY,
          plan_member_id VARCHAR(24)
        );
        CREATE TABLE bh_auth (
          auth_id BIGSERIAL PRIMARY KEY,
          member_id VARCHAR(24) NOT NULL REFERENCES bh_member(member_id)
        );
    """)
    assert validation.check_identity(root).count == 0


def test_the_unresolvable_count_is_reported_as_a_number(tmp_path):
    """'Some members' is not actionable. A count is."""
    root = str(tmp_path)
    write(root, "db/migration/V1__init.sql",
          "CREATE TABLE bh_member (member_id VARCHAR(24), plan_member_id VARCHAR(24));")
    c = validation.check_identity(root, {"unresolved_to_plan": 3, "unresolved_pct": 30.0})
    assert "3 legacy members" in c.note
    assert "cannot be reconciled" in c.note
