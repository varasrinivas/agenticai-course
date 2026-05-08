"""SDK port of the Communication agent from the capstone-4-A pipeline.

Same three tools as solution/pipeline.py (draft_determination_letter,
check_hipaa_compliance, send_notification) but the tool-use loop is
managed by the Claude Agent SDK instead of the manual run_agent().

The tests in this folder import run_communication_agent_sdk and exercise
its behavior with hooks and the can_use_tool callback.
"""
import json
import os
import sys

# Allow imports from the capstone solution.
HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION = os.path.normpath(os.path.join(HERE, "..", "solution"))
if SOLUTION not in sys.path:
    sys.path.insert(0, SOLUTION)

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)

from mock_tools import (
    check_hipaa_compliance,
    draft_determination_letter,
    send_notification,
)


# --- Tool wrappers ---
# Each @tool decorator turns a plain function into an MCP-shaped tool the
# SDK can dispatch by name. Return shape MUST be {"content": [{"type": "text", ...}]}.

@tool(
    "draft_determination_letter",
    "Draft an approve/deny/request-info letter for a pre-auth determination.",
    {
        "request_id": str,
        "determination": str,
        "rationale": str,
        "member_name": str,
    },
)
async def sdk_draft_letter(args):
    result = draft_determination_letter(
        request_id=args["request_id"],
        determination=args["determination"],
        rationale=args.get("rationale", ""),
        member_name=args.get("member_name", "Member"),
    )
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


@tool(
    "check_hipaa_compliance",
    "Verify a letter contains no PHI leaks before sending. "
    "Always run this before send_notification.",
    {"letter_text": str, "letter_type": str},
)
async def sdk_check_hipaa(args):
    result = check_hipaa_compliance(args["letter_text"], args["letter_type"])
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


@tool(
    "send_notification",
    "Send the letter via the given channel. Refuse if HIPAA compliance failed.",
    {"letter_id": str, "channel": str},
)
async def sdk_send(args):
    result = send_notification(letter_id=args["letter_id"], channel=args["channel"])
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


# --- MCP server ---

comms_server = create_sdk_mcp_server(
    name="comms_tools",
    version="1.0.0",
    tools=[sdk_draft_letter, sdk_check_hipaa, sdk_send],
)


# --- Agent runner ---

SYSTEM_PROMPT = (
    "You are the Communication agent for a healthcare pre-authorization system. "
    "For each determination, you MUST: "
    "(1) draft the determination letter using draft_determination_letter, "
    "(2) verify HIPAA compliance using check_hipaa_compliance on the drafted letter, "
    "(3) send the letter using send_notification ONLY if compliant=True. "
    "If compliant=False, do NOT call send_notification — return an error explanation. "
    "Always run check_hipaa_compliance before send_notification."
)


async def run_communication_agent_sdk(
    request_id: str,
    determination: str,
    rationale: str,
    member_name: str = "Test Member",
    channel: str = "portal",
    *,
    hooks=None,
    can_use_tool=None,
    model: str = "claude-haiku-4-5-20251001",
    max_turns: int = 8,
):
    """Run the Communication agent for one determination.

    Returns (final_text, events) — events is the captured event stream so
    tests can assert on tool ordering, message content, etc.
    """
    options_kwargs = dict(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"comms": comms_server},
        allowed_tools=[
            "mcp__comms__draft_determination_letter",
            "mcp__comms__check_hipaa_compliance",
            "mcp__comms__send_notification",
        ],
        max_turns=max_turns,
        model=model,
    )
    if hooks is not None:
        options_kwargs["hooks"] = hooks
    if can_use_tool is not None:
        options_kwargs["can_use_tool"] = can_use_tool

    options = ClaudeAgentOptions(**options_kwargs)

    prompt = (
        f"Process this determination and send the letter.\n"
        f"request_id: {request_id}\n"
        f"determination: {determination}\n"
        f"rationale: {rationale}\n"
        f"member_name: {member_name}\n"
        f"channel: {channel}"
    )

    final_text = ""
    events = []
    async for msg in query(prompt=prompt, options=options):
        events.append(msg)
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if hasattr(block, "text"):
                    final_text = block.text

    return final_text, events
