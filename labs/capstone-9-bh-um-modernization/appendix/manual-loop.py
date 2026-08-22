"""UNDER THE HOOD -- for understanding, not for production.

This is the ONLY file in this capstone that calls `client.messages.create()`.
Everything else uses `claude_agent_sdk`, and the tier policy says so. This file
is the exception because you cannot debug the SDK version if you have never
seen the loop underneath it.

The loop is about forty lines: check `stop_reason`, dispatch the tool calls,
append `tool_result` blocks, go round again. It is not hard.

WHAT IS HARD IS EVERYTHING AROUND IT, and for this capstone in particular:

  * **The protected-content gate.** Look at `_dispatch` below. The narrative
    check happens at ONE call site, because there is one call site. Add a
    second tool tomorrow and you must remember to check there too. Forget once
    and a substance-use treatment record enters the transcript, the provider's
    logs, and every summary that follows -- and there is no taking it back.
    In the SDK that is `can_use_tool`, one callback, on every tool, that cannot
    be forgotten.

  * **The human gate.** Here, "the agent may not finalize" is an `if` in the
    dispatcher that the agent's own code path controls. In the SDK the denial
    comes from a hook the agent cannot reach, keyed on an environment variable
    the agent cannot write. That asymmetry is the whole control, and it does
    not exist in this file.

  * **Subagents.** Eight specialists, each needing its own client, its own
    message list and hand-written context isolation. In the SDK each is a
    markdown file in `.claude/agents/`. The isolation matters here: the
    monolith archaeologist reads 54 files, and if that reading shares a context
    window with the rules extraction, the extraction gets the leftovers.

  * **Skills.** The ASAM ladder, 42 CFR Part 2, the code sets -- pasted into
    eight system prompts here, drifting the moment one is edited, and costing
    tokens on every turn. In the SDK it is one skill loaded on demand.

Run:  python appendix/manual-loop.py
      Needs ANTHROPIC_API_KEY. Connects to nothing else -- the tools are
      stubbed against the synthetic fixture so you can watch the loop without
      a database.
"""

from __future__ import annotations

import json
import os
import re
import sys

from anthropic import Anthropic

MODEL = os.environ.get("MANUAL_LOOP_MODEL", "claude-sonnet-4-6")

# --------------------------------------------------------------- the tools
#
# Two, stubbed. The real run has eighteen across three MCP servers, and that
# difference is most of the argument for the SDK: every one of them would need
# its own entry in the dispatcher below, its own guard, and its own error
# handling, written by hand and remembered forever.

TOOLS = [
    {
        "name": "legacy_read_sql",
        "description": "Read a database object from the legacy monolith.",
        "input_schema": {
            "type": "object",
            "properties": {"object_name": {"type": "string"}},
            "required": ["object_name"],
        },
    },
    {
        "name": "finalize_modernization",
        "description": "Mark the modernization complete.",
        "input_schema": {
            "type": "object",
            "properties": {"confirm_token": {"type": "string"}},
            "required": ["confirm_token"],
        },
    },
]

# A fragment of the real ladder, enough to reason about.
_PKG_LOC_RULES = """\
-- BRANCH 7 -- THE OVERLAP. Read carefully.
--
-- Both of the next two conditions can be true at once. A case with
-- v_score = 10 and v_d1 = 3 satisfies the 3.7 test AND would satisfy the
-- 3.5 test below it. Because this is a first-commit ladder it lands on
-- 3.7, and the 3.5 branch never runs.
IF v_score >= 10 AND v_d1 >= 3 THEN
    r.granted_loc := '3.7'; RETURN r;
END IF;
IF v_score >= 8 THEN
    r.granted_loc := '3.5'; RETURN r;
END IF;
"""

# A narrative-shaped string, to show the gate firing. Synthetic.
_WITH_NARRATIVE = """\
INSERT INTO BH_AUTH VALUES (500001, 'BW-1000401', 'BWP-2002', 'H0019', 'F33.2',
  '3.7', 10,
  'Member presents following a third emergency department contact this quarter.
   Reports escalating passive ideation with a specific plan disclosed at triage.
   Outpatient contact has been irregular.',
  'IN_REVIEW', 'STANDARD', 'N', DATE '2026-08-18', NULL, NULL, NULL);
"""

_PROSE = re.compile(r"(?:[A-Z][^.!?\n]{25,}[.!?]\s*){2,}")


def _looks_protected(text: str) -> bool:
    """The gate, in miniature. See solution/hooks.py for the real one."""
    return bool(_PROSE.search(text))


def _dispatch(name: str, args: dict) -> str:
    """Run one tool.

    NOTE WHERE THE GUARDS LIVE: inline, in this function, once per tool. That
    is the point of this file. Every guard the SDK version declares once, this
    version repeats at every call site and relies on you to remember.
    """
    if name == "legacy_read_sql":
        obj = (args.get("object_name") or "").upper()
        result = _WITH_NARRATIVE if "SEED" in obj or "02" in obj else _PKG_LOC_RULES

        # GUARD 1 -- the protected-content gate, at one call site of one tool.
        if _looks_protected(result):
            return json.dumps({
                "error": "Protected clinical content blocked.",
                "note": "Work from the SHAPE of the field, not its contents.",
            })
        return json.dumps({"object": obj, "content": result})

    if name == "finalize_modernization":
        # GUARD 2 -- the human gate. Note that this `if` is inside the
        # dispatcher the agent's own loop calls. In the SDK the denial comes
        # from a hook the agent cannot reach, keyed on a variable it cannot
        # write. Here it is an honour system with an if-statement.
        return json.dumps({
            "error": "FINALIZATION REQUIRES HUMAN APPROVAL.",
            "note": "A person must read the gap register and re-run with "
                    "--approve. Report this and stop.",
        })

    return json.dumps({"error": f"unknown tool {name}"})


SYSTEM = """\
You are modernizing a behavioral-health utilization-management monolith.

Two things to do, in order:

1. Call legacy_read_sql for PKG_LOC_RULES and explain, in two sentences, why
   the branch-7 overlap makes the DMN hit policy a real decision rather than a
   formality.
2. Call legacy_read_sql for 02_seed to see the protected-content gate fire,
   then call finalize_modernization and report what happened.

Do not paraphrase any clinical narrative you encounter.
"""


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 2

    client = Anthropic()
    messages = [{"role": "user",
                 "content": "Begin. Work through both steps."}]

    print("=" * 70)
    print("  THE LOOP, BY HAND")
    print("  Watch the stop_reason. That is the whole control flow.")
    print("=" * 70)

    for turn in range(1, 9):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        print(f"\n--- turn {turn}   stop_reason={response.stop_reason}")

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\n{block.text.strip()}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            print("\n" + "=" * 70)
            print("  Loop ended. stop_reason was not tool_use, so there was")
            print("  nothing left to dispatch.")
            print("=" * 70)
            return 0

        # THE DISPATCH. Every tool_use block gets a tool_result block, in the
        # same order, keyed on the same id. Get this wrong -- one missing
        # result, one mismatched id -- and the next turn is nonsense that looks
        # like a model failure.
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"    -> {block.name}({json.dumps(block.input)})")
            out = _dispatch(block.name, block.input)
            print(f"    <- {out[:140]}")
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": out,
            })
        messages.append({"role": "user", "content": results})

    print("\nturn limit reached -- and note that the limit is a variable in "
          "this file, not a configured guardrail.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
