"""Behavior test: hook-based assertion that tools are called in the right order.

The Communication agent MUST call check_hipaa_compliance before
send_notification. If the model ever drafts and sends without checking,
the PreToolUse hook will block send_notification and the agent will
either retry correctly or fail loudly.

Run:
    pytest test_tool_order.py -v
"""
import pytest

from claude_agent_sdk import HookMatcher

from sdk_communication_agent import run_communication_agent_sdk


def make_order_hook():
    """Returns (hook_callback, calls_log).

    The hook records every PreToolUse event and blocks send_notification
    if check_hipaa_compliance has not been called yet.
    """
    calls = []

    async def hook(input_data, tool_use_id, context):
        name = input_data.get("tool_name", "")
        calls.append(name)
        if name == "mcp__comms__send_notification":
            if "mcp__comms__check_hipaa_compliance" not in calls:
                return {
                    "decision": "block",
                    "reason": "send_notification called before check_hipaa_compliance",
                }
        return {}

    return hook, calls


@pytest.mark.asyncio
async def test_hipaa_check_runs_before_send():
    """Happy path — agent should call HIPAA check before send."""
    hook, calls = make_order_hook()
    hooks = {"PreToolUse": [HookMatcher(matcher=None, hooks=[hook])]}

    _, _ = await run_communication_agent_sdk(
        request_id="AR-2024-09821",
        determination="approve",
        rationale="All clinical criteria met for TKA (CPT 27447).",
        hooks=hooks,
    )

    # Both tools must have been called
    assert "mcp__comms__check_hipaa_compliance" in calls, (
        f"HIPAA check was never called. Calls: {calls}"
    )
    assert "mcp__comms__send_notification" in calls, (
        f"send_notification was never called. Calls: {calls}"
    )

    # And HIPAA check must precede send
    hipaa_idx = calls.index("mcp__comms__check_hipaa_compliance")
    send_idx = calls.index("mcp__comms__send_notification")
    assert hipaa_idx < send_idx, (
        f"HIPAA check ({hipaa_idx}) must precede send ({send_idx}). "
        f"Calls: {calls}"
    )


@pytest.mark.asyncio
async def test_draft_runs_before_hipaa_check():
    """The draft step must come before the HIPAA check, since the check
    inspects the drafted text."""
    hook, calls = make_order_hook()
    hooks = {"PreToolUse": [HookMatcher(matcher=None, hooks=[hook])]}

    _, _ = await run_communication_agent_sdk(
        request_id="AR-2024-09822",
        determination="deny",
        rationale="Conservative treatment trial not yet completed.",
        hooks=hooks,
    )

    draft_idx = calls.index("mcp__comms__draft_determination_letter")
    hipaa_idx = calls.index("mcp__comms__check_hipaa_compliance")
    assert draft_idx < hipaa_idx, (
        f"Draft ({draft_idx}) must precede HIPAA check ({hipaa_idx}). "
        f"Calls: {calls}"
    )
