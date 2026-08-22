"""MCP server `local` -- the five tools that produce output.

`write_artifact`            emit a file, confined to bh-um-lite/
`record_gap`                append to the gap register, with its constraints enforced
`queue_manual_review`       refuse to convert something, and say why
`eval_rules`                run one case through either engine, for the divergence diff
`finalize_modernization`    HITL-gated. Always denied without human approval.

The constraint checks in `record_gap` are enforced HERE rather than left to the
subagent prompt. A prompt that says "must-not-port requires a named harm" is a
request; a tool that returns an error is a rule. The distinction matters
because softening a must-not-port is exactly the failure this register exists
to prevent.
"""

from __future__ import annotations

import json
import os
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

import config
import hooks
from gap_register import GapEntry, GapRegister, RegisterError
from rules_ir import Case, HitPolicyError, evaluate_ir, evaluate_legacy

_REGISTER_PATH = os.path.join(config.ARTIFACT_DIR, "gap-register.json")
_QUEUE_PATH = os.path.join(config.ARTIFACT_DIR, "manual-review-queue.json")
_IR_PATH = os.path.join(config.ARTIFACT_DIR, "rules-ir.json")


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str, **extra: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message, **extra})}]}


def _load_register() -> GapRegister:
    if os.path.exists(_REGISTER_PATH):
        try:
            return GapRegister.load(_REGISTER_PATH)
        except (OSError, ValueError, TypeError):
            pass
    return GapRegister()


@tool(
    "write_artifact",
    "Write one generated file into the new workspace. Paths are relative to "
    "bh-um-lite/ and confined to it -- a subagent cannot write over either "
    "source tree, and the agent's own configuration is not part of its output.",
    {"relative_path": str, "content": str},
)
async def write_artifact(args: dict) -> dict:
    relative = str(args.get("relative_path") or "").strip().lstrip("/\\")
    content = args.get("content")
    if not relative:
        return _err("relative_path is required")
    if content is None:
        return _err("content is required")

    target = os.path.normpath(os.path.join(config.EMIT_ROOT, relative))
    root = os.path.normpath(config.EMIT_ROOT)
    if not (target == root or target.startswith(root + os.sep)):
        return _err(f"{relative!r} resolves outside bh-um-lite/")

    # Second line of defence behind the hook. A generated log statement or event
    # payload carrying clinical narrative is the leak this whole run exists to
    # prevent, and it would be absurd to let the agent write one.
    if hooks.looks_like_protected_content(str(content)):
        return _err(
            "Refused: this content looks like clinical narrative. Generated code "
            "must not embed protected content -- not in a fixture, not in a test, "
            "not in a comment. Use a placeholder and reference the synthetic seed.",
            path=relative,
        )

    try:
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(str(content))
    except OSError as exc:
        return _err(f"could not write {relative}: {exc}")

    return _ok({"written": relative, "bytes": len(str(content)),
                "absolute": target})


@tool(
    "record_gap",
    "Append one entry to the gap register. verdict is port-as-is, extend, "
    "must-build-new, or must-not-port. must-not-port REQUIRES a named harm; "
    "must-build-new REQUIRES a requirement. Every verdict cites evidence.",
    {"capability": str, "verdict": str, "evidence": str,
     "harm": str, "requirement": str, "trap_id": int, "backlog": str},
)
async def record_gap(args: dict) -> dict:
    # --------------------------------------------------------------------
    # TODO 19 -- Append to the gap register, enforcing its constraints.
    #
    # Return the constraint violation as an ERROR rather than accepting it with
    # a warning. A register that accepts a must-not-port with no harm is a
    # register whose most important verdict means nothing.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


@tool(
    "queue_manual_review",
    "Refuse to convert something, and say why. Use for undocumented flags, "
    "thresholds with no provenance, and rules a compliance note flagged. "
    "A refusal with a reason is a useful output; a confident wrong translation is not.",
    {"artifact": str, "reason": str, "question": str, "evidence": str},
)
async def queue_manual_review(args: dict) -> dict:
    # --------------------------------------------------------------------
    # TODO 20 -- Refuse to convert something, and say why.
    #
    # Require a QUESTION. Queueing an item without stating what a human has to
    # decide produces a list nobody can act on.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


@tool(
    "eval_rules",
    "Evaluate one case through the legacy ladder or through the emitted decision "
    "table, and return the decision. Run every golden case through both and diff: "
    "a non-zero divergence on the first pass is the expected result.",
    {"engine": str, "case_json": str},
)
async def eval_rules(args: dict) -> dict:
    # --------------------------------------------------------------------
    # TODO 21 -- Run one case through either engine.
    #
    # A HitPolicyError is not a crash to route around: it is the table
    # reporting that the ladder's ordering carried information it does not.
    # Return it as a finding.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


@tool(
    "finalize_modernization",
    "Mark the run complete. HUMAN-GATED: this always denies until a person has "
    "read the gap register and re-run with --approve. The agent cannot approve "
    "its own modernization.",
    {"confirm_token": str},
)
async def finalize_modernization(args: dict) -> dict:
    # The hook denies this before it executes. Reaching this body means a human
    # set the environment variable, so the body is the approved path -- and it
    # still refuses if the register says the run is not ready, because approval
    # of a broken run is a decision a person should have to make twice.
    register = _load_register()
    problems = register.acceptance_problems()
    if problems:
        return _err(
            "Approved by a human, but the gap register does not meet the run's "
            "acceptance criteria. Fix these or approve deliberately after "
            "reading them: " + "; ".join(problems)
        )

    marker = os.path.join(config.ARTIFACT_DIR, "FINALIZED")
    os.makedirs(os.path.dirname(marker) or ".", exist_ok=True)
    with open(marker, "w", encoding="utf-8") as fh:
        fh.write(register.render())
    return _ok({"finalized": True, "entries": len(register.entries),
                "distribution": register.distribution()})


local_server = create_sdk_mcp_server(
    name="local",
    version="1.0.0",
    tools=[write_artifact, record_gap, queue_manual_review,
           eval_rules, finalize_modernization],
)
