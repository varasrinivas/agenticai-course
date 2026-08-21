"""Guardrails -- YOU BUILD THIS FILE.

Four guards, in order of how much damage they prevent:

  1. enforce_oracle_readonly  -- nothing may ever write to the source.
  2. protect_pg_target        -- nothing may drop, or escape the target schema.
  3. hitl_cutover_gate        -- the one irreversible action needs a human.
  4. audit_log                -- everything that happened, with secrets removed.

The first three must return `PermissionResultDeny` from a `can_use_tool`
callback, which runs BEFORE the tool executes. A hook that logs the DROP
after the fact is an excellent post-mortem and a useless guardrail.

Verify with:  pytest tests/test_hooks_readonly.py tests/test_hooks_pg_guard.py \
                     tests/test_cutover_hitl.py -v
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

import config

# ---------------------------------------------------------------------
# 1. Oracle is read-only.
# ---------------------------------------------------------------------
# TODO(1a): Build an ALLOW-LIST, not a deny-list.
#
# A deny-list of dangerous verbs is a losing game. You will remember DROP
# and DELETE. You will forget TRUNCATE, or FLASHBACK, or PURGE, or a
# PL/SQL block that wraps an UPDATE inside BEGIN...END. An allow-list
# fails closed: anything you did not explicitly permit is refused.
#
# Permit exactly three shapes:
#   - statements starting with SELECT or WITH
#   - DBMS_METADATA.GET_DDL / SET_TRANSFORM_PARAM calls
#   - reads of ALL_* / USER_* / DBA_* dictionary views
_ORACLE_READ_PREFIXES = ()      # TODO
_ORACLE_READ_CALLS = ()         # TODO
_ORACLE_DICTIONARY = None       # TODO: compile a regex for the dictionary views

_WRITE_VERBS = None             # TODO: compile a regex used only to NAME the
                                # offending verb in the denial message


def _statement_of(tool_input: dict[str, Any]) -> str:
    """Best-effort extraction of whatever SQL this call would run.

    Given complete -- the structured tools (oracle_row_count and friends)
    carry no free-form SQL at all, because they build their own SELECT
    from a validated identifier. Those must pass through.
    """
    for key in ("sql", "ddl", "statement", "query"):
        if isinstance(tool_input.get(key), str):
            return tool_input[key]
    return ""


async def enforce_oracle_readonly(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on mcp__oracle_src__* -- deny anything that is not a read."""
    # TODO(1b): Return PermissionResultAllow() immediately for any tool
    # that is not an oracle_src tool. If you skip this, the Oracle guard
    # also blocks every PostgreSQL write -- and the migration will do
    # nothing at all while appearing to be well protected.

    # TODO(1c): Extract the statement. If there is none, allow.

    # TODO(1d): Allow the three permitted shapes.

    # TODO(1e): Otherwise deny. Name the offending verb in the message --
    # a bare "denied" teaches the model nothing and it will simply try
    # again with a synonym.
    raise NotImplementedError("Build enforce_oracle_readonly")


# ---------------------------------------------------------------------
# 2. Protect the PostgreSQL target.
# ---------------------------------------------------------------------
# TODO(2a): Two regexes.
#   _PG_FORBIDDEN -- DROP DATABASE / SCHEMA / OWNED / ROLE / TABLESPACE
#   _PG_CREATES   -- capture the object name from CREATE|ALTER statements
#                    so you can check which schema it lands in
_PG_FORBIDDEN = None
_PG_CREATES = None


async def protect_pg_target(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on pg_apply_ddl -- no drops, nothing outside ucc_migrated.

    Harder than the Oracle guard, because this one has to ALLOW writes --
    the migration's whole job is to write. It must permit exactly the
    right ones.

    Why the schema rule matters: cutover is a single atomic
    `ALTER SCHEMA ucc_migrated RENAME TO public`. One object accidentally
    created in `public` and that rename either collides or leaves an
    orphan behind.
    """
    # TODO(2b): Ignore any tool that is not pg_apply_ddl.
    # TODO(2c): Deny anything matching _PG_FORBIDDEN.
    # TODO(2d): For each CREATE/ALTER, if the name is schema-qualified and
    #           the schema is not config.POSTGRES.target_schema, deny.
    #           Unqualified names are fine -- search_path handles them.
    raise NotImplementedError("Build protect_pg_target")


# ---------------------------------------------------------------------
# 3. Human-in-the-loop cutover gate.
# ---------------------------------------------------------------------
async def hitl_cutover_gate(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on pg_cutover -- the agent can never approve itself.

    Note what this must NOT do: it must not ask the model to consider
    whether cutover seems reasonable. Self-approval is not a gate. The
    only thing that opens it is `config.CUTOVER_APPROVED`, which a human
    sets by passing --approve-cutover on the command line.
    """
    # TODO(3a): Ignore any tool that is not pg_cutover.
    # TODO(3b): If config.CUTOVER_APPROVED, allow.
    # TODO(3c): Otherwise read artifacts/validation_summary.json (it may
    #           not exist yet -- handle that) and deny with a message that
    #           carries the validation state AND names the exact command
    #           the operator has to run. A gate that blocks without saying
    #           how to proceed just gets worked around.
    raise NotImplementedError("Build hitl_cutover_gate")


# ---------------------------------------------------------------------
# 4. Audit log.
# ---------------------------------------------------------------------
# TODO(4a): Patterns for anything credential-shaped: `password=`,
# `ORACLE_PWD=`, `user:pass@host` inside a URL, and API keys.
# Be aggressive. An audit log that over-redacts is annoying; one that
# leaks a production DSN into a file someone commits is an incident.
_SECRET_PATTERNS: list[re.Pattern] = []


def redact(text: str) -> str:
    """Strip anything that looks like a credential."""
    # TODO(4b): substitute each pattern, keeping the label and replacing
    # only the secret with ***
    raise NotImplementedError("Build redact")


async def audit_log(tool_name: str, tool_input: dict, tool_response: Any, context: Any):
    """PostToolUse on * -- append one JSON line per tool call."""
    # TODO(4c): Build an entry with timestamp, tool_name, REDACTED params,
    #           and duration.
    # TODO(4d): Pull a row count out of the response if there is one -- it
    #           is the single most useful field when reconciling later.
    #           The response shape is
    #           {"content": [{"type": "text", "text": "<json>"}]}
    #           and a tool that returns something unexpected must NOT
    #           crash the hook and take down the migration with it.
    # TODO(4e): Append to config.AUDIT_LOG. A failed audit write must not
    #           halt the run, but it must be visible.
    raise NotImplementedError("Build audit_log")


# ---------------------------------------------------------------------
# Composed permission callback
# ---------------------------------------------------------------------
async def can_use_tool(tool_name: str, tool_input: dict, context: Any):
    """Runs every PreToolUse guard in order; first denial wins.

    Given complete -- but it only works once the three guards above do.
    """
    for guard in (enforce_oracle_readonly, protect_pg_target, hitl_cutover_gate):
        result = await guard(tool_name, tool_input, context)
        if isinstance(result, PermissionResultDeny):
            print(f"[guard] DENY {tool_name}: {result.message.splitlines()[0]}")
            return result
    return PermissionResultAllow()


class TokenBudget:
    """Circuit breaker for cost. Given complete.

    Checked between phases rather than mid-object: a migration that has
    burned its budget should stop between objects, not halfway through
    writing one.
    """

    def __init__(self, ceiling: int = config.TOKEN_BUDGET):
        self.ceiling = ceiling
        self.spent = 0
        self.started = time.time()

    def add(self, output_tokens: int) -> None:
        self.spent += output_tokens

    def exceeded(self) -> bool:
        return self.spent >= self.ceiling

    def remaining(self) -> int:
        return max(0, self.ceiling - self.spent)

    def __str__(self) -> str:
        pct = (self.spent / self.ceiling * 100) if self.ceiling else 0
        return f"{self.spent:,}/{self.ceiling:,} output tokens ({pct:.0f}%)"
