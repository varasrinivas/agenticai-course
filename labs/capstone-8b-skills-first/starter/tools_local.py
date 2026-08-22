"""Local (non-database) tools: artifact writing.

## Notice what is NOT here

The subagent build of this migration (Capstone 8) also exposed a
`scan_app_sql` MCP tool from this file. In the skills build it is gone -- the
same scanning logic ships as
`.claude/skills/appsql-rewriting/scripts/find_oracleisms.py` instead, and the
agent runs it with Bash.

Before you write anything, work out why that move is the point rather than a
detail. Two questions to answer for yourself:

  1. An MCP tool is described in the tool list of every request, whether or
     not the current phase needs it. A skill script is loaded only when its
     skill loads. What does that do to the context budget across five phases?

  2. Where does the *rationale* for `scan_app_sql` live in each design? In the
     subagent build the regex was here and the guidance was in two different
     subagent prompts, with no link between them. What went wrong with that?

Then answer the harder question: `write_artifact` STAYS an MCP tool. Why does
that one not move into a skill? The distinction you need is between a
capability and a piece of knowledge -- and it has to do with what must hold
true in phases where no relevant skill is loaded at all.

Write your answer in the module docstring. The reasoning is assessed, not the
code -- `write_artifact` itself is only twenty lines.
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
    # TODO(1): validate that relative_path and content are both present.

    # TODO(2): resolve the target under config.ARTIFACT_DIR and REFUSE
    # anything that escapes it. A `..` in a model-supplied path is usually
    # just wrong rather than malicious, but the failure mode is identical
    # either way -- so this is a boundary, not a lint.
    #
    # os.path.commonpath on the two absolute paths is the check. Compare
    # resolved paths, not the string the model sent.

    # TODO(3): create parent directories, write UTF-8 with newline="\n", and
    # return the relative path plus the byte count. Turn OSError into an
    # error payload rather than letting it propagate -- a failed artifact
    # write should not take down the migration.
    raise NotImplementedError("Build write_artifact")


local_server = create_sdk_mcp_server(
    name="migration_local",
    version="2.0.0",
    tools=[write_artifact],
)
