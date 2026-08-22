"""The cutover gate, and the audit log's redaction.

The gate is one line of logic and it is the most important line in the
project: an agent cannot approve its own irreversible operation. The tests
below assert that in both directions -- denied without approval, allowed
with it -- because a gate that is always closed is not a gate, it is a bug
that happens to look safe.
"""

from __future__ import annotations

import json

import pytest
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from hooks import audit_log, can_use_tool, hitl_cutover_gate, redact

CUTOVER = "mcp__pg_target__pg_cutover"


@pytest.mark.asyncio
async def test_cutover_denied_without_human_approval(no_cutover_approval):
    result = await hitl_cutover_gate(CUTOVER, {"confirm_token": "whatever"}, None)
    assert isinstance(result, PermissionResultDeny)
    assert "HUMAN APPROVAL" in result.message


@pytest.mark.asyncio
async def test_denial_tells_the_operator_exactly_what_to_do(no_cutover_approval):
    """A gate that blocks without saying how to proceed just gets worked
    around. The message must name the command."""
    result = await hitl_cutover_gate(CUTOVER, {}, None)
    assert "--approve-cutover" in result.message


@pytest.mark.asyncio
async def test_cutover_allowed_once_a_human_approves(monkeypatch):
    import config

    monkeypatch.setattr(config, "CUTOVER_APPROVED", True)
    result = await hitl_cutover_gate(CUTOVER, {"confirm_token": "x"}, None)
    assert isinstance(result, PermissionResultAllow)


@pytest.mark.asyncio
async def test_gate_only_applies_to_cutover(no_cutover_approval):
    result = await hitl_cutover_gate(
        "mcp__pg_target__pg_row_count", {"table_name": "ucc_filing"}, None
    )
    assert isinstance(result, PermissionResultAllow)


@pytest.mark.asyncio
async def test_composed_guard_blocks_cutover(no_cutover_approval):
    """can_use_tool chains all three guards; the cutover denial must
    survive the composition."""
    result = await can_use_tool(CUTOVER, {"confirm_token": "x"}, None)
    assert isinstance(result, PermissionResultDeny)


# ------------------------------------------------------------ redaction
@pytest.mark.parametrize(
    "raw,leaked",
    [
        ("host=db user=migration password=hunter2", "hunter2"),
        ("ORACLE_PWD=MeridianSys#2003", "MeridianSys#2003"),
        ("postgres://migration:s3cret@postgres:5432/meridian", "s3cret"),
        ("key sk-ant-api03-abcdefghijklmnop", "abcdefghijklmnop"),
    ],
)
def test_redact_removes_credentials(raw, leaked):
    cleaned = redact(raw)
    assert leaked not in cleaned, f"leaked {leaked!r} in {cleaned!r}"
    assert "***" in cleaned


def test_redact_leaves_ordinary_text_alone():
    text = "Migrated 5000 rows from UCC_FILING to ucc_migrated.ucc_filing"
    assert redact(text) == text


@pytest.mark.asyncio
async def test_audit_log_writes_one_line_per_call(audit_log_path):
    response = {"content": [{"type": "text", "text": json.dumps({"row_count": 5000})}]}
    await audit_log("mcp__oracle_src__oracle_row_count",
                    {"table_name": "UCC_FILING"}, response, None)
    await audit_log("mcp__pg_target__pg_row_count",
                    {"table_name": "ucc_filing"}, response, None)

    lines = audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["tool_name"] == "mcp__oracle_src__oracle_row_count"
    assert first["row_count"] == 5000
    assert "timestamp" in first


@pytest.mark.asyncio
async def test_audit_log_redacts_params(audit_log_path):
    response = {"content": [{"type": "text", "text": "{}"}]}
    await audit_log(
        "mcp__pg_target__pg_query",
        {"sql": "connect host=db user=migration password=hunter2"},
        response,
        None,
    )
    contents = audit_log_path.read_text(encoding="utf-8")
    assert "hunter2" not in contents
    assert "***" in contents


@pytest.mark.asyncio
async def test_audit_log_survives_a_malformed_response(audit_log_path):
    """A tool that returns something unexpected must not take down the
    migration by crashing the audit hook."""
    await audit_log("weird_tool", {"x": 1}, {"not": "the usual shape"}, None)
    assert audit_log_path.exists()
    entry = json.loads(audit_log_path.read_text(encoding="utf-8").strip())
    assert entry["tool_name"] == "weird_tool"
