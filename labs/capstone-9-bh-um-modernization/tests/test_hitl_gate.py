"""The agent cannot approve its own modernization.

`finalize_modernization` always denies until a human passes --approve, which
sets an environment variable this process reads and has no way to write. That
asymmetry IS the gate; the briefing it returns is presentation.

The gate matters here more than in most labs because of what is being approved:
a change to how medical-necessity determinations are made. "The agent said it
was ready" is not a control.
"""

import asyncio
import json
import os

import pytest
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

import config
import hooks
from gap_register import (MUST_BUILD_NEW, MUST_NOT_PORT, GapEntry, GapRegister)


def guard(args=None):
    return asyncio.run(hooks.hitl_finalization_gate(
        "mcp__local__finalize_modernization", args or {"confirm_token": "ready"}, None))


# ---------------------------------------------------------- always denies


def test_finalization_is_denied_by_default(monkeypatch):
    monkeypatch.setattr(config, "FINALIZATION_APPROVED", False)
    result = guard()
    assert isinstance(result, PermissionResultDeny)
    assert "REQUIRES HUMAN APPROVAL" in result.message


def test_the_denial_tells_the_agent_not_to_work_around_it(monkeypatch):
    monkeypatch.setattr(config, "FINALIZATION_APPROVED", False)
    msg = guard().message
    assert "not an obstacle to work around" in msg
    assert "report the state above to the operator and stop" in msg.lower()


def test_other_tools_are_unaffected(monkeypatch):
    monkeypatch.setattr(config, "FINALIZATION_APPROVED", False)
    result = asyncio.run(hooks.hitl_finalization_gate(
        "mcp__local__write_artifact", {"relative_path": "a.txt"}, None))
    assert isinstance(result, PermissionResultAllow)


def test_human_approval_opens_the_gate(monkeypatch):
    monkeypatch.setattr(config, "FINALIZATION_APPROVED", True)
    assert isinstance(guard(), PermissionResultAllow)


def test_the_agent_has_no_path_to_set_approval():
    """The flag is read from the environment at import and never written by
    anything the agent can reach. This test is a tripwire: if a future edit
    adds a setter, it fails."""
    import inspect

    src = inspect.getsource(hooks)
    assert "FINALIZATION_APPROVED = " not in src
    assert "os.environ[" not in src

    tools_src = inspect.getsource(__import__("tools_emit"))
    assert "FINALIZATION_APPROVED" not in tools_src
    assert "os.environ[" not in tools_src


# ------------------------------------------------------------- the briefing


def test_the_briefing_reports_missing_artifacts_honestly(artifacts, monkeypatch):
    monkeypatch.setattr(config, "FINALIZATION_APPROVED", False)
    briefing = hooks.finalization_briefing()
    assert "GAP REGISTER: MISSING" in briefing
    assert "PARITY: MISSING" in briefing


def test_the_briefing_flags_an_empty_manual_review_queue(artifacts):
    """A run that queues nothing has guessed at something."""
    briefing = hooks.finalization_briefing()
    assert "QUEUED FOR HUMAN DECISION: 0" in briefing
    assert "LEGACY_OVERRIDE" in briefing


def test_the_briefing_surfaces_must_not_port_harms(artifacts):
    reg = GapRegister()
    reg.add(GapEntry(
        capability="cleartext PHI logging", verdict=MUST_NOT_PORT,
        evidence="donor interpolates member ids into log statements",
        harm="decomposition multiplies one log sink into several; this content "
             "is Part 2 protected"))
    reg.add(GapEntry(
        capability="disclosure accounting", verdict=MUST_BUILD_NEW,
        evidence="no audit table in the donor",
        requirement="recipient, scope, consent id, timestamp"))
    reg.save(os.path.join(artifacts, "gap-register.json"))

    briefing = hooks.finalization_briefing()
    assert "MUST-NOT-PORT" in briefing
    assert "harm:" in briefing
    assert "must-build-new" in briefing


def test_the_briefing_flags_a_suspiciously_clean_check(artifacts):
    """The single most dangerous thing a validator can report."""
    with open(os.path.join(artifacts, "parity-report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"verdict": "READY FOR REVIEW", "checks": [
            {"id": 1, "name": "rules divergence", "count": 0,
             "expected_nonzero": True}]}, fh)

    briefing = hooks.finalization_briefing()
    assert "SUSPECT THE VALIDATOR" in briefing


def test_the_briefing_is_assembled_from_artifacts_not_from_a_summary(artifacts):
    """The agent's account of its own run is the thing under review, so the
    briefing reads the files rather than the agent's report of them."""
    import inspect

    src = inspect.getsource(hooks.finalization_briefing)
    assert "_read_json" in src
    assert "gap-register.json" in src
    assert "parity-report.json" in src


# ------------------------------------------------- approval is not enough


def test_approval_still_refuses_a_register_that_fails_acceptance(artifacts,
                                                                 monkeypatch):
    """Approving a broken run should take two deliberate acts, not one."""
    import importlib

    import tools_emit
    importlib.reload(tools_emit)

    reg = GapRegister()
    reg.add(GapEntry(capability="outbox", verdict="port-as-is",
                     evidence="domain-agnostic"))
    reg.save(os.path.join(artifacts, "gap-register.json"))

    result = asyncio.run(tools_emit.finalize_modernization.handler(
        {"confirm_token": "ready"}))
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload
    assert "acceptance criteria" in payload["error"]


def test_the_cli_flag_is_what_sets_approval():
    """Read the coordinator, not the docs."""
    import inspect

    import coordinator
    src = inspect.getsource(coordinator.main)
    assert "--approve" in inspect.getsource(coordinator)
    assert "BH_FINALIZATION_APPROVED" in src
    assert "The agent cannot set this" in inspect.getsource(coordinator)
