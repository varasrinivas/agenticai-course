"""Both source trees are read-only, and writes are confined to bh-um-lite/.

Enforced in code, not by convention. The trees are EVIDENCE: a parity validator
that diffs the port against a tree the agent can edit is diffing against a
moving target, and nobody would notice.
"""

import asyncio
import json
import os

import pytest
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

import config
import hooks


def guard(tool, args):
    return asyncio.run(hooks.can_use_tool(tool, args, None))


def denied(tool, args) -> bool:
    return isinstance(guard(tool, args), PermissionResultDeny)


# ------------------------------------------------------ no write tools


def test_neither_source_server_exposes_a_write_tool():
    """First line of defence: there is nothing to call."""
    import tools_legacy
    import tools_reference

    for module in (tools_reference, tools_legacy):
        names = [n for n in dir(module) if not n.startswith("_")]
        for name in names:
            obj = getattr(module, name)
            if not hasattr(obj, "handler"):
                continue
            assert not any(v in name for v in ("write", "update", "delete",
                                               "insert", "apply", "exec")), \
                f"{module.__name__}.{name} looks like a write tool"


# ------------------------------------------------------ path traversal


@pytest.mark.parametrize("bad", [
    "../../../etc/passwd",
    "../bhauthtrack/db/01_schema.sql",
    "../../solution/hooks.py",
])
def test_traversal_out_of_the_reference_tree_is_denied(bad):
    assert denied("mcp__reference_src__ref_read_file", {"path": bad})


@pytest.mark.parametrize("bad", [
    "../reference-umlite/nx.json",
    "../../../../Windows/System32/drivers/etc/hosts",
])
def test_traversal_out_of_the_legacy_tree_is_denied(bad):
    assert denied("mcp__legacy_src__legacy_read_java", {"path": bad})


def test_ordinary_reads_are_allowed():
    assert not denied("mcp__reference_src__ref_read_file", {"path": "nx.json"})
    assert not denied("mcp__legacy_src__legacy_read_jsp", {"view": "decision.jsp"})


def test_the_tool_itself_also_refuses_traversal():
    """Defence in depth: the hook and the tool both check, independently."""
    import tools_reference as T
    result = asyncio.run(T.ref_read_file.handler({"path": "../../../etc/passwd"}))
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload
    assert "outside" in payload["error"]


# -------------------------------------------------- writes are confined


@pytest.mark.parametrize("bad", [
    "../bhauthtrack/db/01_schema.sql",
    "../reference-umlite/nx.json",
    "../solution/hooks.py",
    "../../etc/cron.d/x",
])
def test_writes_outside_the_emit_root_are_denied(bad):
    assert denied("mcp__local__write_artifact",
                  {"relative_path": bad, "content": "x"})


def test_absolute_paths_are_denied():
    assert denied("mcp__local__write_artifact",
                  {"relative_path": os.path.abspath("/tmp/x"), "content": "x"})


def test_writes_inside_the_emit_root_are_allowed():
    assert not denied("mcp__local__write_artifact",
                      {"relative_path": "apps/bh-case-svc/V1__init.sql",
                       "content": "CREATE TABLE bh_auth (auth_id BIGSERIAL);"})


def test_a_write_with_no_path_is_refused():
    assert denied("mcp__local__write_artifact", {"content": "x"})


def test_the_emit_tool_refuses_escape_independently(emit_root):
    """Even if the hook were bypassed."""
    import importlib

    import tools_emit
    importlib.reload(tools_emit)
    result = asyncio.run(tools_emit.write_artifact.handler(
        {"relative_path": "../escaped.txt", "content": "x"}))
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload


# ------------------------------------------------------- the settings file


def test_settings_declares_a_guard_for_every_boundary():
    path = os.path.join(os.path.dirname(config.__file__), ".claude", "settings.json")
    cfg = json.load(open(path, encoding="utf-8"))

    matchers = [g["matcher"] for g in cfg["hooks"]["PreToolUse"]]
    assert ".*" in matchers, "the protected-content gate must match every tool"
    assert any("reference_src" in m for m in matchers)
    assert any("legacy_src" in m for m in matchers)
    assert any("write_artifact" in m for m in matchers)
    assert any("finalize_modernization" in m for m in matchers)
    assert cfg["hooks"]["PostToolUse"][0]["matcher"] == ".*"


def test_settings_denies_writes_to_both_source_trees():
    """Belt and braces: the permission list closes the shell routes around
    the hooks."""
    path = os.path.join(os.path.dirname(config.__file__), ".claude", "settings.json")
    cfg = json.load(open(path, encoding="utf-8"))
    deny = " ".join(cfg["permissions"]["deny"])
    assert "bhauthtrack" in deny
    assert "reference-umlite" in deny


def test_there_is_no_consent_flag_in_the_environment():
    """A regulatory control that can be switched off in configuration is a
    default, not a control -- so the key does not exist."""
    path = os.path.join(os.path.dirname(config.__file__), ".claude", "settings.json")
    cfg = json.load(open(path, encoding="utf-8"))
    for key in cfg.get("env", {}):
        assert "CONSENT" not in key.upper() or "ALLOWLIST" in key.upper()


# ------------------------------------------------------------ the audit log


def test_the_audit_log_redacts_credentials_and_narrative(narrative, tmp_path,
                                                         monkeypatch):
    log = tmp_path / "audit.jsonl"
    monkeypatch.setattr(config, "AUDIT_LOG", str(log))

    asyncio.run(hooks.audit_log(
        "mcp__legacy_src__legacy_read_sql",
        {"object_name": "BH_AUTH", "dsn": "user=app password=Secret#2026"},
        {"content": [{"type": "text", "text": json.dumps({"content": narrative})}]},
        None))

    text = log.read_text(encoding="utf-8")
    assert "Secret#2026" not in text
    assert "ideation" not in text
    entry = json.loads(text.strip().splitlines()[0])
    assert entry["tool_name"].endswith("legacy_read_sql")
    assert "timestamp" in entry
