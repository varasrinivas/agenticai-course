"""Local (non-database) tools: artifact writing.

## What is NOT here, and why

The subagent build of this migration (Capstone 8) also exposed a
`scan_app_sql` MCP tool here. In the skills build it is gone -- the same
scanning logic now ships as
`.claude/skills/appsql-rewriting/scripts/find_oracleisms.py`, and the agent
runs it with Bash.

That is not a cosmetic move. It is the difference the two architectures are
built to show:

  MCP tool     always present, described in every request's tool list,
               costs context whether or not this phase needs it, and its
               *rationale* lives somewhere else entirely -- in a subagent
               prompt that the tool has no link to.

  Skill script loaded only when the skill loads, and it sits next to the
               SKILL.md that explains when to run it and how to read the
               output. Knowledge and executable arrive together or not at
               all.

A regex that finds `ROWNUM` does not need to be a protocol-level tool. It
needs to be reachable at the moment someone is deciding what `ROWNUM`
becomes.

`write_artifact` stays an MCP tool, because it is genuinely a capability
rather than knowledge: it enforces the artifacts/ confinement boundary, and
that boundary must hold in every phase regardless of which skills happen to
be loaded.
"""

from __future__ import annotations

import json
import os
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

import config


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


@tool(
    "write_artifact",
    "Write generated DDL, PL/pgSQL, or a unified diff under artifacts/. "
    "Paths are confined to that directory -- the agent cannot write over "
    "the source tree.",
    {"relative_path": str, "content": str},
)
async def write_artifact(args: dict) -> dict:
    relative = (args.get("relative_path") or "").strip().lstrip("/\\")
    content = args.get("content")
    if not relative:
        return _err("relative_path is required")
    if content is None:
        return _err("content is required")

    base = os.path.abspath(config.ARTIFACT_DIR)
    target = os.path.abspath(os.path.join(base, relative))

    # Path traversal check. `..` in a model-supplied path is not
    # necessarily malicious -- it is usually just wrong -- but the
    # failure mode is the same either way.
    if os.path.commonpath([base, target]) != base:
        return _err(f"Refusing to write outside {config.ARTIFACT_DIR}: {relative!r}")

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    except OSError as exc:
        return _err(f"write_artifact failed for {relative}: {exc}")

    return _ok({"path": os.path.relpath(target, base), "bytes": len(content.encode())})


local_server = create_sdk_mcp_server(
    name="migration_local",
    version="2.0.0",
    tools=[write_artifact],
)
