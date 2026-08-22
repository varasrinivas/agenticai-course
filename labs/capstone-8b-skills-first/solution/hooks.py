"""Guardrails.

Four of them, in order of how much damage they prevent:

  1. `enforce_oracle_readonly`   -- nothing may ever write to the source.
  2. `protect_pg_target`         -- nothing may drop or escape the target schema.
  3. `hitl_cutover_gate`         -- the one irreversible action needs a human.
  4. `audit_log`                 -- everything that happened, with secrets removed.

The first three are `can_use_tool` denials, which is the important
detail: they run BEFORE the tool executes and return
`PermissionResultDeny`, so the dangerous call never happens. A hook that
logged the DROP after the fact would be a very good post-mortem and a
very bad guardrail.
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
# Allow-list, not deny-list. A deny-list of dangerous verbs is a losing
# game -- you will forget TRUNCATE, or COMMENT ON, or FLASHBACK, or a
# PL/SQL block that wraps an UPDATE. An allow-list fails closed.
_ORACLE_READ_PREFIXES = ("select", "with")
_ORACLE_READ_CALLS = ("dbms_metadata.get_ddl", "dbms_metadata.set_transform_param")
_ORACLE_DICTIONARY = re.compile(r"\b(all|user|dba)_[a-z_]+\b", re.I)

_WRITE_VERBS = re.compile(
    r"\b(insert|update|delete|merge|truncate|drop|alter|create|grant|revoke|"
    r"comment|flashback|lock|rename|purge|call|execute|begin|declare)\b",
    re.I,
)


def _statement_of(tool_input: dict[str, Any]) -> str:
    """Best-effort extraction of whatever SQL this call would run."""
    for key in ("sql", "ddl", "statement", "query"):
        if isinstance(tool_input.get(key), str):
            return tool_input[key]
    # Structured tools (oracle_row_count etc.) carry no free-form SQL --
    # they build it themselves from a validated identifier.
    return ""


async def enforce_oracle_readonly(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on mcp__oracle_src__* -- deny anything that is not a read."""
    if not tool_name.startswith("mcp__oracle_src__"):
        return PermissionResultAllow()

    statement = _statement_of(tool_input).strip()

    # No free-form SQL in the call: these tools only ever run the SELECT
    # they construct internally from a validated identifier.
    if not statement:
        return PermissionResultAllow()

    lowered = statement.lower().lstrip("( \n\t")

    if lowered.startswith(_ORACLE_READ_PREFIXES):
        return PermissionResultAllow()
    if any(call in lowered for call in _ORACLE_READ_CALLS):
        return PermissionResultAllow()
    if _ORACLE_DICTIONARY.search(lowered) and not _WRITE_VERBS.match(lowered):
        return PermissionResultAllow()

    offending = _WRITE_VERBS.search(lowered)
    verb = offending.group(0).upper() if offending else "non-SELECT"
    return PermissionResultDeny(
        message=(
            f"Source database is read-only: {verb} rejected. "
            f"The Oracle system is live production for eleven Secretary of "
            f"State offices; the migration reads it and never writes to it. "
            f"If you need a derived value, compute it on the PostgreSQL side."
        )
    )


# ---------------------------------------------------------------------
# 2. Protect the PostgreSQL target.
# ---------------------------------------------------------------------
_PG_FORBIDDEN = re.compile(
    r"\b(drop\s+database|drop\s+schema|drop\s+owned|drop\s+role|"
    r"drop\s+tablespace)\b",
    re.I,
)
_PG_CREATES = re.compile(
    r"\b(create|alter)\s+(table|view|materialized\s+view|index|sequence|"
    r"function|procedure|type|trigger)\s+(if\s+not\s+exists\s+)?([a-z0-9_\".]+)",
    re.I,
)


async def protect_pg_target(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on pg_apply_ddl -- no drops, nothing outside ucc_migrated."""
    if tool_name != "mcp__pg_target__pg_apply_ddl":
        return PermissionResultAllow()

    ddl = (tool_input.get("ddl") or "").strip()
    if not ddl:
        return PermissionResultAllow()

    forbidden = _PG_FORBIDDEN.search(ddl)
    if forbidden:
        return PermissionResultDeny(
            message=(
                f"Refused: '{forbidden.group(0)}' is never part of a migration. "
                f"Objects are created inside {config.POSTGRES.target_schema} and "
                f"the schema is promoted at cutover; nothing is ever dropped."
            )
        )

    # Any created object must be either unqualified (search_path puts it
    # in the target schema) or explicitly qualified into the target.
    for match in _PG_CREATES.finditer(ddl):
        name = match.group(4).strip('"')
        if "." in name:
            schema = name.split(".", 1)[0].strip('"').lower()
            if schema != config.POSTGRES.target_schema:
                return PermissionResultDeny(
                    message=(
                        f"Refused: '{name}' targets schema '{schema}'. Every "
                        f"migrated object must be created in "
                        f"'{config.POSTGRES.target_schema}' so the cutover is a "
                        f"single atomic schema rename."
                    )
                )

    return PermissionResultAllow()


# ---------------------------------------------------------------------
# 3. Human-in-the-loop cutover gate.
# ---------------------------------------------------------------------
async def hitl_cutover_gate(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on pg_cutover -- the agent can never approve itself.

    Note what this does NOT do: it does not ask the model to consider
    whether cutover seems reasonable. Self-approval is not a gate. The
    only thing that opens it is a human passing --approve-cutover on the
    command line, which sets an environment variable this process reads
    but cannot write.
    """
    if tool_name != "mcp__pg_target__pg_cutover":
        return PermissionResultAllow()

    if config.CUTOVER_APPROVED:
        return PermissionResultAllow()

    summary_path = os.path.join(config.ARTIFACT_DIR, "validation_summary.json")
    summary = "no validation report found -- run phase 5 first"
    if os.path.exists(summary_path):
        try:
            with open(summary_path, encoding="utf-8") as fh:
                data = json.load(fh)
            summary = (
                f"{data.get('tables_validated', '?')} tables validated, "
                f"{data.get('checks_passed', '?')} checks passed, "
                f"{data.get('checks_failed', '?')} failed"
            )
        except (OSError, json.JSONDecodeError):
            summary = "validation report present but unreadable"

    return PermissionResultDeny(
        message=(
            "CUTOVER REQUIRES HUMAN APPROVAL.\n"
            f"Current validation state: {summary}\n"
            "A person must read artifacts/validation_report.html and re-run:\n"
            "    python coordinator.py --phase cutover --approve-cutover\n"
            "Do not attempt to work around this. Report the validation state "
            "to the operator and stop."
        )
    )


# ---------------------------------------------------------------------
# 4. Audit log.
# ---------------------------------------------------------------------
_SECRET_PATTERNS = [
    re.compile(r"(password\s*=\s*)(\S+)", re.I),
    re.compile(r"(ORACLE_PWD\s*=\s*)(\S+)", re.I),
    re.compile(r"(://[^:/\s]+:)([^@/\s]+)(@)"),        # user:pass@host
    re.compile(r"(\buser\s*=\s*\S+\s+password\s*=\s*)(\S+)", re.I),
    re.compile(r"(sk-ant-[A-Za-z0-9_-]{6})([A-Za-z0-9_-]+)"),
]


def redact(text: str) -> str:
    """Strip anything that looks like a credential.

    Deliberately aggressive. An audit log that over-redacts is annoying;
    one that leaks a production DSN into a file someone commits is an
    incident.

    Call this on individual string VALUES, not on serialized JSON -- see
    `redact_structure`. The patterns end in greedy runs of non-whitespace,
    which happily eat a closing quote and brace if handed a JSON document.
    """
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 3:
            text = pattern.sub(r"\1***\3", text)
        else:
            text = pattern.sub(r"\1***", text)
    return text


def redact_structure(value: Any) -> Any:
    """Redact every string inside a nested structure, in place of the value.

    This exists because redacting the serialized JSON instead corrupts it:
    a DSN like `password=hunter2` sits at the end of a JSON string, and the
    `\\S+` that matches the secret also matches the `"` and `}` that close
    the document. `json.loads` on the result then raises, inside a
    PostToolUse hook, on precisely the tool calls that carry credentials --
    so the audit log loses the entries that matter most and the migration
    dies at the same time.

    Redacting per-value cannot break the structure, because the structure
    is never turned into text first.
    """
    if isinstance(value, dict):
        return {key: redact_structure(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_structure(item) for item in value]
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact(str(value))


async def audit_log(tool_name: str, tool_input: dict, tool_response: Any, context: Any):
    """PostToolUse on * -- append one JSON line per tool call."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "params": redact_structure(tool_input),
        "duration_ms": getattr(context, "duration_ms", None),
    }

    # Pull a row count out of the response if there is one -- it is the
    # single most useful field when reconciling later.
    try:
        text = tool_response["content"][0]["text"]
        payload = json.loads(text)
        for key in ("row_count", "rows_in_table", "returned", "finding_count"):
            if key in payload:
                entry["row_count"] = payload[key]
                break
        if payload.get("error"):
            entry["error"] = redact(str(payload["error"]))[:400]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        pass

    try:
        os.makedirs(os.path.dirname(config.AUDIT_LOG) or ".", exist_ok=True)
        with open(config.AUDIT_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        # A failed audit write must not take down the migration, but it
        # must be visible.
        print(f"[audit] WARNING: could not write to {config.AUDIT_LOG}")

    return {}


# ---------------------------------------------------------------------
# Composed permission callback
# ---------------------------------------------------------------------
async def can_use_tool(tool_name: str, tool_input: dict, context: Any):
    """Runs every PreToolUse guard in order; first denial wins."""
    for guard in (enforce_oracle_readonly, protect_pg_target, hitl_cutover_gate):
        result = await guard(tool_name, tool_input, context)
        if isinstance(result, PermissionResultDeny):
            print(f"[guard] DENY {tool_name}: {result.message.splitlines()[0]}")
            return result
    return PermissionResultAllow()


class TokenBudget:
    """Circuit breaker for cost.

    Not a hook -- the coordinator checks it between phases. A migration
    that has already burned the budget should stop between objects, not
    halfway through writing one.
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
