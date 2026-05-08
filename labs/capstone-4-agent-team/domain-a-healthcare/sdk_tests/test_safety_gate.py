"""Safety guardrail test: can_use_tool callback blocks production channels in dev.

The Communication agent's send_notification accepts a `channel` argument.
In dev/test we never want letters going to a production channel ("portal",
"fax", "mail"). The can_use_tool callback inspects every tool call and
denies any send_notification that targets a non-test channel.

Run:
    pytest test_safety_gate.py -v
"""
import pytest

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from sdk_communication_agent import run_communication_agent_sdk


TEST_CHANNELS = {"portal_test", "fax_test", "mail_test"}


def make_dev_safety_gate():
    """Returns (gate_callback, denied_calls).

    Allows all tool calls except send_notification targeting a non-test
    channel. Records every denial so tests can assert on it.
    """
    denied = []

    async def gate(tool_name, tool_input, context):
        if tool_name == "mcp__comms__send_notification":
            channel = tool_input.get("channel", "")
            if channel not in TEST_CHANNELS:
                denied.append({"tool": tool_name, "input": tool_input})
                return PermissionResultDeny(
                    message=(
                        f"Channel '{channel}' is not allowed in dev. "
                        f"Use one of: {sorted(TEST_CHANNELS)}"
                    ),
                    interrupt=False,
                )
        return PermissionResultAllow(updated_input=tool_input)

    return gate, denied


@pytest.mark.asyncio
async def test_production_channel_blocked():
    """Sending to 'portal' (production) must be denied."""
    gate, denied = make_dev_safety_gate()

    _, events = await run_communication_agent_sdk(
        request_id="AR-2024-09823",
        determination="approve",
        rationale="All clinical criteria met.",
        channel="portal",  # production — should be blocked
        can_use_tool=gate,
    )

    assert len(denied) >= 1, (
        f"Expected at least one denial for the production channel, got: {denied}"
    )
    assert denied[0]["input"].get("channel") == "portal", (
        f"Denial recorded the wrong input: {denied[0]}"
    )


@pytest.mark.asyncio
async def test_test_channel_allowed():
    """Sending to 'portal_test' must be allowed (no denials)."""
    gate, denied = make_dev_safety_gate()

    _, events = await run_communication_agent_sdk(
        request_id="AR-2024-09824",
        determination="approve",
        rationale="All clinical criteria met.",
        channel="portal_test",  # test channel — should pass
        can_use_tool=gate,
    )

    assert denied == [], (
        f"Expected no denials for test channel, got: {denied}"
    )


@pytest.mark.asyncio
async def test_input_mutation_via_gate():
    """A gate can rewrite tool input — useful for forcing test channels.

    This version of the gate doesn't deny; it transparently rewrites every
    'portal' to 'portal_test'. The agent thinks it sent to portal but the
    tool only ever sees portal_test.
    """
    rewrites = []

    async def rewriting_gate(tool_name, tool_input, context):
        if tool_name == "mcp__comms__send_notification":
            channel = tool_input.get("channel", "")
            if channel == "portal":
                rewrites.append(channel)
                tool_input = {**tool_input, "channel": "portal_test"}
        return PermissionResultAllow(updated_input=tool_input)

    _, _ = await run_communication_agent_sdk(
        request_id="AR-2024-09825",
        determination="approve",
        rationale="All clinical criteria met.",
        channel="portal",
        can_use_tool=rewriting_gate,
    )

    assert rewrites == ["portal"], (
        f"Expected exactly one rewrite from 'portal' to 'portal_test', got: {rewrites}"
    )
