"""UNDER THE HOOD -- for understanding, not for production.

This is what `claude_agent_sdk.query()` is doing on your behalf: a while
loop that checks `stop_reason`, dispatches tool calls, appends
`tool_result` blocks, and goes round again.

Read it once. Then use the SDK.

Not because the loop is hard -- it is about forty lines. Because
everything AROUND the loop is hard, and the SDK has already solved it:

  - Guardrails. Here, a `PermissionResultDeny` equivalent means writing
    your own check at every dispatch site and remembering it every time
    you add a tool. In the SDK it is one `can_use_tool` callback that
    cannot be forgotten.
  - Subagents. Here, every specialist would need its own client, its own
    message list, and hand-written context isolation. In the SDK it is a
    markdown file in `.claude/agents/`.
  - Sessions, hooks, audit logging, streaming, retries on overload,
    prompt caching. All of it, by hand, forever.

The reason this file exists at all is that you cannot debug the SDK
version if you have never seen the loop. When a tool result comes back
malformed and the agent starts hallucinating around it, the mental model
you need is right here: it is just messages in a list.

Run:  python appendix/manual-loop.py
      (needs ANTHROPIC_API_KEY; connects to nothing else -- the tools are
       stubbed so you can watch the loop without a database)
"""

from __future__ import annotations

import json
import os
import sys

from anthropic import Anthropic

# --------------------------------------------------------------- tools
# Hand-written JSON Schema. The SDK generates this from the @tool
# decorator's type hints; here you maintain it by hand, and it drifts out
# of sync with the implementation the first time someone adds a parameter.
TOOLS = [
    {
        "name": "oracle_get_ddl",
        "description": "Return the CREATE statement for one Oracle object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_type": {"type": "string"},
                "object_name": {"type": "string"},
            },
            "required": ["object_name"],
        },
    },
    {
        "name": "pg_apply_ddl",
        "description": "Apply PostgreSQL DDL to the target schema.",
        "input_schema": {
            "type": "object",
            "properties": {"ddl": {"type": "string"}},
            "required": ["ddl"],
        },
    },
]

STUB_DDL = """CREATE TABLE "MERIDIAN"."UCC_FILING"
 (  "FILING_ID" NUMBER(12,0) NOT NULL ENABLE,
    "FILING_NUMBER" VARCHAR2(20 BYTE) NOT NULL ENABLE,
    "STATE_CODE" CHAR(2) NOT NULL ENABLE,
    "FILED_DATE" DATE NOT NULL ENABLE,
    "LAPSE_DATE" DATE,
    "COLLATERAL_DESC" CLOB,
    "FILING_FEE" NUMBER(9,2),
     PRIMARY KEY ("FILING_ID")
 );"""


def dispatch(name: str, args: dict) -> str:
    """Execute one tool call.

    Note the guardrail here: it is a hand-written `if` in the middle of
    the dispatcher. Add a third tool and you have to remember to guard it
    too. Nothing enforces that you did. This is the single strongest
    argument for the SDK's `can_use_tool`: the check lives in one place
    and applies to every tool by construction.
    """
    if name == "oracle_get_ddl":
        return STUB_DDL

    if name == "pg_apply_ddl":
        ddl = args.get("ddl", "")
        lowered = ddl.lower()
        if "drop schema" in lowered or "drop database" in lowered:
            return json.dumps({"applied": False, "error": "refused: destructive DDL"})
        return json.dumps({"applied": True, "note": "stub -- nothing was executed"})

    return json.dumps({"error": f"unknown tool {name}"})


# ---------------------------------------------------------------- loop
def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set.")
        return 1

    client = Anthropic()

    messages = [
        {
            "role": "user",
            "content": (
                "Fetch the DDL for the Oracle table UCC_FILING, translate it to "
                "PostgreSQL 16, and apply it. Oracle DATE carries a time "
                "component, so map it to timestamp(0), not date. Do not quote "
                "identifiers."
            ),
        }
    ]

    for turn in range(1, 11):
        print(f"\n--- turn {turn} " + "-" * 50)

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as exc:                       # noqa: BLE001
            # The SDK retries overloads and rate limits with backoff.
            # Here, you write that yourself, or you do not have it.
            print(f"API call failed: {type(exc).__name__}: {exc}")
            return 1

        for block in response.content:
            if block.type == "text":
                print(block.text)

        messages.append({"role": "assistant", "content": response.content})

        # THE loop condition. Everything hinges on stop_reason.
        if response.stop_reason != "tool_use":
            print(f"\nDone (stop_reason={response.stop_reason})")
            break

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  -> {block.name}({json.dumps(block.input)[:90]}...)")
            output = dispatch(block.name, block.input)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                }
            )

        # Tool results go back as a USER message. Getting this shape wrong
        # is the single most common bug in a hand-rolled loop -- and the
        # error it produces looks like the model behaving strangely rather
        # than like a malformed request.
        messages.append({"role": "user", "content": results})
    else:
        print("\nHit the turn ceiling without finishing.")

    print(f"\n{len(messages)} messages in the transcript.")
    print("Now go read coordinator.py, which does all of this in one query() call.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
