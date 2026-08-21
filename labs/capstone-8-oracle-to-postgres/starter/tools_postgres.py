"""MCP server `pg_target` -- the PostgreSQL 16 destination.

Unlike the Oracle side, this server genuinely writes. So the interesting
design work is in what it refuses:

  - `pg_apply_ddl` runs every statement inside a transaction that is
    ROLLED BACK first as a syntax check, then re-run and committed. A
    statement that cannot parse never reaches the real schema.
  - Everything is created inside `ucc_migrated`, never `public`. The
    PreToolUse hook enforces that; this module makes it the default by
    setting search_path.
  - `pg_cutover` is the only irreversible operation in the system, and
    it is gated on a human approval token the agent cannot mint.
"""

from __future__ import annotations

import csv
import json
import os
import time
from typing import Any

import psycopg
from claude_agent_sdk import create_sdk_mcp_server, tool

import config


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


def _connect():
    conn = psycopg.connect(config.POSTGRES.dsn(), autocommit=False)
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {config.POSTGRES.target_schema}")
        cur.execute(f"SET search_path TO {config.POSTGRES.target_schema}, public")
    conn.commit()
    return conn


@tool(
    "pg_apply_ddl",
    "Apply generated PostgreSQL DDL. The statement is first executed in "
    "a rolled-back transaction as a syntax check; only if that succeeds "
    "is it applied for real.",
    {"ddl": str},
)
async def pg_apply_ddl(args: dict) -> dict:
    ddl = (args.get("ddl") or "").strip()
    if not ddl:
        return _err("ddl is required")

    started = time.perf_counter()
    try:
        # ---- pass 1: parse/plan check, always rolled back -------------
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.rollback()
    except psycopg.Error as exc:
        return _ok(
            {
                "applied": False,
                "stage": "syntax_check",
                "error": str(exc).strip(),
                "hint": "The DDL was rejected before touching the schema. "
                "Nothing was changed.",
            }
        )

    try:
        # ---- pass 2: for real ----------------------------------------
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()
    except psycopg.Error as exc:
        return _ok({"applied": False, "stage": "apply", "error": str(exc).strip()})

    return _ok(
        {
            "applied": True,
            "schema": config.POSTGRES.target_schema,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    )


@tool(
    "pg_copy_load",
    "Bulk-load a CSV into a target table with COPY. `null_as` controls "
    "which token means NULL -- set it explicitly, or Oracle NULLs arrive "
    "as PostgreSQL empty strings and every IS NULL check downstream "
    "quietly stops matching.",
    {"table_name": str, "csv_path": str, "null_as": str},
)
async def pg_copy_load(args: dict) -> dict:
    table = (args.get("table_name") or "").lower()
    path = args.get("csv_path") or ""
    null_as = args.get("null_as")
    if null_as is None:
        null_as = "\\N"

    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")
    if not os.path.exists(path):
        return _err(f"CSV not found: {path}")

    try:
        with open(path, newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        collist = ", ".join(h.strip().lower() for h in header)

        loaded = 0
        with _connect() as conn:
            with conn.cursor() as cur:
                copy_sql = (
                    f"COPY {config.POSTGRES.target_schema}.{table} ({collist}) "
                    f"FROM STDIN WITH (FORMAT csv, HEADER true, NULL '{null_as}')"
                )
                with cur.copy(copy_sql) as copy, open(path, "rb") as data:
                    while chunk := data.read(65536):
                        copy.write(chunk)
                cur.execute(f"SELECT COUNT(*) FROM {config.POSTGRES.target_schema}.{table}")
                loaded = cur.fetchone()[0]
            conn.commit()
        return _ok({"table_name": table, "rows_in_table": loaded, "null_as": null_as})
    except (psycopg.Error, OSError) as exc:
        return _err(f"pg_copy_load failed for {table}: {exc}")


@tool(
    "pg_query",
    "Run a read query against the target schema and return rows as JSON.",
    {"sql": str},
)
async def pg_query(args: dict) -> dict:
    sql = (args.get("sql") or "").strip()
    if not sql:
        return _err("sql is required")
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description is None:
                    conn.commit()
                    return _ok({"rows": [], "rowcount": cur.rowcount})
                cols = [d.name for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            conn.rollback()
        return _ok({"columns": cols, "rows": rows[:500], "returned": len(rows)})
    except psycopg.Error as exc:
        return _err(f"pg_query failed: {exc}")


@tool(
    "pg_row_count",
    "Exact COUNT(*) for one migrated table.",
    {"table_name": str},
)
async def pg_row_count(args: dict) -> dict:
    table = (args.get("table_name") or "").lower()
    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {config.POSTGRES.target_schema}.{table}")
                count = cur.fetchone()[0]
            conn.rollback()
        return _ok({"table_name": table, "row_count": int(count)})
    except psycopg.Error as exc:
        return _err(f"pg_row_count failed for {table}: {exc}")


@tool(
    "pg_checksum",
    "Fingerprint a migrated table, plus per-column NULL counts AND "
    "per-column empty-string counts. The empty-string counts have no "
    "Oracle counterpart by design: any non-zero value on a column that "
    "was NULL-only in Oracle is the migration defect this whole capstone "
    "is built around.",
    {"table_name": str, "columns": str},
)
async def pg_checksum(args: dict) -> dict:
    table = (args.get("table_name") or "").lower()
    columns = [c.strip().lower() for c in (args.get("columns") or "").split(",") if c.strip()]
    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")
    if not columns or not all(c.replace("_", "").isalnum() for c in columns):
        return _err("columns must be a comma-separated list of identifiers")

    try:
        concat = " || '|' || ".join(f"coalesce({c}::text, '<NULL>')" for c in columns)
        nulls = ", ".join(
            f"count(*) FILTER (WHERE {c} IS NULL) AS null_{c}" for c in columns
        )
        # Only text-ish columns can hold ''. Cast defensively so a numeric
        # column does not blow up the query.
        empties = ", ".join(
            f"count(*) FILTER (WHERE {c}::text = '') AS empty_{c}" for c in columns
        )
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT sum(hashtext({concat})::bigint) AS fingerprint,
                           count(*)                        AS row_count,
                           {nulls},
                           {empties}
                      FROM {config.POSTGRES.target_schema}.{table}
                    """
                )
                cols = [d.name for d in cur.description]
                result = dict(zip(cols, cur.fetchone()))
            conn.rollback()

        divergent = [c for c in columns if (result.get(f"empty_{c}") or 0) > 0]
        return _ok(
            {
                "table_name": table,
                "columns": columns,
                **result,
                "empty_string_columns": divergent,
                "warning": (
                    f"Columns {divergent} contain empty strings. If those were "
                    f"NULL in Oracle, this load is defective."
                )
                if divergent
                else None,
            }
        )
    except psycopg.Error as exc:
        return _err(f"pg_checksum failed for {table}: {exc}")


@tool(
    "pg_cutover",
    "Promote the migrated schema to production by renaming it to public. "
    "IRREVERSIBLE. Requires a human approval token that the agent cannot "
    "generate for itself.",
    {"confirm_token": str},
)
async def pg_cutover(args: dict) -> dict:
    token = args.get("confirm_token") or ""

    # Belt and braces. The hook in hooks.py denies this tool outright
    # unless CUTOVER_APPROVED is set, so this branch should be
    # unreachable -- but an unreachable guard on an irreversible
    # operation is cheap insurance against a future refactor that moves
    # the hook.
    if not config.CUTOVER_APPROVED:
        return _err(
            "Cutover not approved. A human must review the validation "
            "report and re-run with --approve-cutover."
        )
    if token != os.environ.get("CUTOVER_TOKEN", ""):
        return _err("confirm_token does not match CUTOVER_TOKEN.")

    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("ALTER SCHEMA public RENAME TO public_pre_migration")
                cur.execute(
                    f"ALTER SCHEMA {config.POSTGRES.target_schema} RENAME TO public"
                )
            conn.commit()
        return _ok({"cutover": "complete", "rolled_back_schema": "public_pre_migration"})
    except psycopg.Error as exc:
        return _err(f"pg_cutover failed: {exc}")


pg_server = create_sdk_mcp_server(
    name="pg_target",
    version="1.0.0",
    tools=[pg_apply_ddl, pg_copy_load, pg_query, pg_row_count, pg_checksum, pg_cutover],
)
