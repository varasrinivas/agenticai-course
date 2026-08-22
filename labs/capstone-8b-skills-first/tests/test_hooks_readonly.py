"""The Oracle source must be unwritable. These tests are the proof.

They run without any database: the guard is pure logic over the tool name
and the statement text, which is exactly why it can be tested this fast
and this thoroughly. A guardrail you can only exercise against a live
production system is a guardrail nobody exercises.
"""

from __future__ import annotations

import pytest
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from hooks import enforce_oracle_readonly

ORACLE_TOOL = "mcp__oracle_src__oracle_sample_rows"


async def _decide(statement: str, tool: str = ORACLE_TOOL):
    return await enforce_oracle_readonly(tool, {"sql": statement}, None)


# --------------------------------------------------------------- denied
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statement",
    [
        "DROP TABLE meridian.ucc_filing",
        "drop table ucc_filing",
        "TRUNCATE TABLE meridian.ucc_debtor",
        "DELETE FROM ucc_filing WHERE filing_id = 1",
        "UPDATE ucc_filing SET status = 'LAPSED'",
        "INSERT INTO filing_audit (audit_id) VALUES (1)",
        "MERGE INTO state_sos_source t USING dual s ON (1=1)",
        "ALTER TABLE ucc_filing ADD col NUMBER",
        "GRANT SELECT ON ucc_filing TO PUBLIC",
        "CREATE TABLE scratch AS SELECT * FROM ucc_filing",
        "BEGIN pkg_filing_maint.log_audit(1,'X','Y'); END;",
        "DECLARE v NUMBER; BEGIN UPDATE ucc_filing SET status='X'; END;",
        "RENAME ucc_filing TO ucc_filing_old",
        "COMMENT ON TABLE ucc_filing IS 'x'",
        "LOCK TABLE ucc_filing IN EXCLUSIVE MODE",
    ],
)
async def test_writes_are_denied(statement):
    result = await _decide(statement)
    assert isinstance(result, PermissionResultDeny), f"{statement!r} was allowed"
    assert "read-only" in result.message.lower()


@pytest.mark.asyncio
async def test_denial_names_the_verb():
    """The message has to be actionable. 'Denied' with no reason teaches
    the model nothing and it will simply try again."""
    result = await _decide("DROP TABLE ucc_filing")
    assert "DROP" in result.message


# -------------------------------------------------------------- allowed
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statement",
    [
        "SELECT * FROM ucc_filing",
        "select count(*) from meridian.ucc_debtor",
        "  SELECT 1 FROM dual",
        "WITH x AS (SELECT 1 FROM dual) SELECT * FROM x",
        "SELECT dbms_metadata.get_ddl('TABLE','UCC_FILING') FROM dual",
        "SELECT table_name FROM all_tables WHERE owner = 'MERIDIAN'",
        "SELECT text FROM all_source WHERE name = 'PKG_RISK_CALC'",
    ],
)
async def test_reads_are_allowed(statement):
    result = await _decide(statement)
    assert isinstance(result, PermissionResultAllow), f"{statement!r} was denied"


@pytest.mark.asyncio
async def test_structured_tools_pass_through():
    """oracle_row_count carries no free-form SQL -- it builds its own
    SELECT from a validated identifier. The guard must not block it just
    because there is nothing to inspect."""
    result = await enforce_oracle_readonly(
        "mcp__oracle_src__oracle_row_count", {"table_name": "UCC_FILING"}, None
    )
    assert isinstance(result, PermissionResultAllow)


@pytest.mark.asyncio
async def test_guard_ignores_non_oracle_tools():
    """A PostgreSQL write must not be caught by the Oracle guard -- that
    would make the target read-only too, and the migration would do
    nothing at all while appearing to be protected."""
    result = await enforce_oracle_readonly(
        "mcp__pg_target__pg_apply_ddl", {"ddl": "CREATE TABLE x (id int)"}, None
    )
    assert isinstance(result, PermissionResultAllow)


@pytest.mark.asyncio
async def test_allowlist_not_denylist():
    """A verb nobody thought of must still be denied.

    This is the test that justifies the allow-list design. FLASHBACK and
    PURGE are not in the deny regex by name, and they must still fail.
    """
    for statement in ["FLASHBACK TABLE ucc_filing TO TIMESTAMP x",
                      "PURGE RECYCLEBIN",
                      "EXPLAIN PLAN FOR DELETE FROM ucc_filing"]:
        result = await _decide(statement)
        assert isinstance(result, PermissionResultDeny), f"{statement!r} was allowed"
