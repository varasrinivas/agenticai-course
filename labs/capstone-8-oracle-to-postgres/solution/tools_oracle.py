"""MCP server `oracle_src` -- READ-ONLY access to the legacy database.

Three independent things stop this server from writing to Oracle:

  1. The database user (`migration_reader`) has SELECT and nothing else.
  2. Every function below opens a connection and only ever runs SELECT
     or DBMS_METADATA calls -- there is no execute-arbitrary-SQL tool.
  3. The PreToolUse hook in hooks.py inspects the effective statement
     and denies anything that is not a read.

Any one of those would probably be enough. All three are there because
"probably enough" is not a thing you say about someone's production
database.
"""

from __future__ import annotations

import json
import os
from typing import Any

import oracledb
from claude_agent_sdk import create_sdk_mcp_server, tool

import config

# python-oracledb runs in "thin" mode by default -- no Oracle Instant
# Client install needed, which is the only reason this lab is runnable
# on a stock Python image.
_pool: oracledb.ConnectionPool | None = None


def _ok(payload: Any) -> dict:
    """Every tool returns the SDK's content-block shape."""
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


def _fixture(name: str) -> dict | None:
    """Replay a canned response when FIXTURE_MODE is on."""
    if not config.FIXTURE_MODE:
        return None
    path = os.path.join(config.FIXTURE_DIR, f"{name}.json")
    if not os.path.exists(path):
        return {"error": f"No fixture for {name}; run without FIXTURE_MODE"}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _connect():
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=config.ORACLE.user,
            password=config.ORACLE.password,
            dsn=config.ORACLE.dsn,
            min=1,
            max=4,
            increment=1,
        )
    return _pool.acquire()


def _rows(cursor) -> list[dict]:
    cols = [c[0].lower() for c in cursor.description]
    out = []
    for row in cursor:
        record = {}
        for col, value in zip(cols, row):
            # LOBs must be read before the cursor moves on.
            if isinstance(value, oracledb.LOB):
                value = value.read()
            if isinstance(value, bytes):
                value = value.hex()
            record[col] = value
        out.append(record)
    return out


# ---------------------------------------------------------------- tools
@tool(
    "oracle_describe_schema",
    "Inventory every object in the legacy Oracle schema: tables, columns "
    "with exact Oracle types, sequences, triggers, views, materialized "
    "views, packages, procedures and functions.",
    {"owner": str},
)
async def oracle_describe_schema(args: dict) -> dict:
    owner = (args.get("owner") or config.ORACLE.schema).upper()

    canned = _fixture("describe_schema")
    if canned is not None:
        return _ok(canned)

    try:
        with _connect() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT object_type, object_name, status
                  FROM all_objects
                 WHERE owner = :owner
                   AND object_type IN ('TABLE','VIEW','MATERIALIZED VIEW',
                                       'SEQUENCE','TRIGGER','PACKAGE',
                                       'PACKAGE BODY','PROCEDURE','FUNCTION')
                 ORDER BY object_type, object_name
                """,
                owner=owner,
            )
            objects = _rows(cur)

            cur.execute(
                """
                SELECT table_name, column_name, column_id, data_type,
                       data_length, data_precision, data_scale,
                       nullable, data_default, char_used
                  FROM all_tab_columns
                 WHERE owner = :owner
                 ORDER BY table_name, column_id
                """,
                owner=owner,
            )
            columns = _rows(cur)

            cur.execute(
                """
                SELECT table_name, num_rows
                  FROM all_tables
                 WHERE owner = :owner
                 ORDER BY table_name
                """,
                owner=owner,
            )
            counts = {r["table_name"]: r["num_rows"] for r in _rows(cur)}

            cur.close()

        by_table: dict[str, list[dict]] = {}
        for col in columns:
            by_table.setdefault(col["table_name"], []).append(col)

        return _ok(
            {
                "owner": owner,
                "object_counts": {
                    t: sum(1 for o in objects if o["object_type"] == t)
                    for t in {o["object_type"] for o in objects}
                },
                "objects": objects,
                "tables": [
                    {
                        "table_name": name,
                        "estimated_rows": counts.get(name),
                        "columns": cols,
                    }
                    for name, cols in sorted(by_table.items())
                ],
            }
        )
    except oracledb.Error as exc:
        return _err(f"oracle_describe_schema failed: {exc}")


@tool(
    "oracle_get_ddl",
    "Return the exact CREATE statement for one Oracle object via "
    "DBMS_METADATA.GET_DDL.",
    {"object_type": str, "object_name": str},
)
async def oracle_get_ddl(args: dict) -> dict:
    object_type = (args.get("object_type") or "TABLE").upper().replace(" ", "_")
    object_name = (args.get("object_name") or "").upper()
    if not object_name:
        return _err("object_name is required")

    canned = _fixture(f"ddl_{object_name.lower()}")
    if canned is not None:
        return _ok(canned)

    try:
        with _connect() as conn:
            cur = conn.cursor()
            # Readable output: no storage clauses, no tablespace noise.
            cur.callproc(
                "dbms_metadata.set_transform_param",
                ["SESSION_TRANSFORM", "STORAGE", False],
            )
            cur.callproc(
                "dbms_metadata.set_transform_param",
                ["SESSION_TRANSFORM", "SEGMENT_ATTRIBUTES", False],
            )
            cur.callproc(
                "dbms_metadata.set_transform_param",
                ["SESSION_TRANSFORM", "SQLTERMINATOR", True],
            )
            cur.execute(
                "SELECT dbms_metadata.get_ddl(:t, :n, :o) FROM dual",
                t=object_type,
                n=object_name,
                o=config.ORACLE.schema,
            )
            row = cur.fetchone()
            ddl = row[0].read() if isinstance(row[0], oracledb.LOB) else row[0]
            cur.close()
        return _ok({"object_type": object_type, "object_name": object_name, "ddl": ddl})
    except oracledb.Error as exc:
        return _err(f"oracle_get_ddl failed for {object_type} {object_name}: {exc}")


@tool(
    "oracle_get_plsql_source",
    "Return the full PL/SQL source of a package, package body, procedure, "
    "function or trigger from ALL_SOURCE.",
    {"object_name": str},
)
async def oracle_get_plsql_source(args: dict) -> dict:
    object_name = (args.get("object_name") or "").upper()
    if not object_name:
        return _err("object_name is required")

    canned = _fixture(f"plsql_{object_name.lower()}")
    if canned is not None:
        return _ok(canned)

    try:
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT type, line, text
                  FROM all_source
                 WHERE owner = :owner
                   AND name  = :name
                 ORDER BY type, line
                """,
                owner=config.ORACLE.schema,
                name=object_name,
            )
            rows = _rows(cur)

            if not rows:
                # Triggers live in ALL_TRIGGERS, not ALL_SOURCE.
                cur.execute(
                    """
                    SELECT trigger_type, triggering_event, table_name,
                           description, trigger_body
                      FROM all_triggers
                     WHERE owner = :owner AND trigger_name = :name
                    """,
                    owner=config.ORACLE.schema,
                    name=object_name,
                )
                trig = _rows(cur)
                cur.close()
                if not trig:
                    return _err(f"No source found for {object_name}")
                return _ok({"object_name": object_name, "trigger": trig[0]})

            cur.close()

        bodies: dict[str, list[str]] = {}
        for row in rows:
            bodies.setdefault(row["type"], []).append(row["text"])

        return _ok(
            {
                "object_name": object_name,
                "sources": {k: "".join(v) for k, v in bodies.items()},
                "line_count": len(rows),
            }
        )
    except oracledb.Error as exc:
        return _err(f"oracle_get_plsql_source failed for {object_name}: {exc}")


@tool(
    "oracle_sample_rows",
    "Fetch a small sample of rows from one table, preserving the Oracle "
    "type name for each column so type-mapping decisions can be made "
    "from real values rather than from the DDL alone.",
    {"table_name": str, "limit": int},
)
async def oracle_sample_rows(args: dict) -> dict:
    table = (args.get("table_name") or "").upper()
    limit = min(int(args.get("limit") or 20), 200)
    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")

    canned = _fixture(f"sample_{table.lower()}")
    if canned is not None:
        return _ok(canned)

    try:
        with _connect() as conn:
            cur = conn.cursor()
            # Table name is validated above and interpolated because
            # Oracle does not allow binds for identifiers.
            cur.execute(
                f"SELECT * FROM {config.ORACLE.schema}.{table} "
                f"FETCH FIRST :n ROWS ONLY",
                n=limit,
            )
            types = {
                d[0].lower(): oracledb.DB_TYPE_NAMES.get(d[1], str(d[1]))
                if hasattr(oracledb, "DB_TYPE_NAMES")
                else str(d[1])
                for d in cur.description
            }
            rows = _rows(cur)
            cur.close()
        return _ok({"table_name": table, "column_types": types, "rows": rows})
    except oracledb.Error as exc:
        return _err(f"oracle_sample_rows failed for {table}: {exc}")


@tool(
    "oracle_row_count",
    "Exact COUNT(*) for one table. Used for reconciliation, so it is a "
    "real count, not the optimizer's estimate.",
    {"table_name": str},
)
async def oracle_row_count(args: dict) -> dict:
    table = (args.get("table_name") or "").upper()
    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")

    canned = _fixture(f"count_{table.lower()}")
    if canned is not None:
        return _ok(canned)

    try:
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {config.ORACLE.schema}.{table}")
            count = cur.fetchone()[0]
            cur.close()
        return _ok({"table_name": table, "row_count": int(count)})
    except oracledb.Error as exc:
        return _err(f"oracle_row_count failed for {table}: {exc}")


@tool(
    "oracle_checksum",
    "Fingerprint a table with SUM(ORA_HASH(...)) over the given columns, "
    "plus a per-column NULL count. The NULL counts are what catch the "
    "empty-string trap: Oracle reports '' as NULL, PostgreSQL does not.",
    {"table_name": str, "columns": str},
)
async def oracle_checksum(args: dict) -> dict:
    table = (args.get("table_name") or "").upper()
    columns = [c.strip().upper() for c in (args.get("columns") or "").split(",") if c.strip()]
    if not table.replace("_", "").isalnum():
        return _err(f"Refusing suspicious table name: {table!r}")
    if not columns or not all(c.replace("_", "").isalnum() for c in columns):
        return _err("columns must be a comma-separated list of identifiers")

    canned = _fixture(f"checksum_{table.lower()}")
    if canned is not None:
        return _ok(canned)

    try:
        concat = " || '|' || ".join(f"NVL(TO_CHAR({c}), '<NULL>')" for c in columns)
        null_counts = ", ".join(
            f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS null_{c.lower()}"
            for c in columns
        )
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT SUM(ORA_HASH({concat})) AS fingerprint,
                       COUNT(*)                AS row_count,
                       {null_counts}
                  FROM {config.ORACLE.schema}.{table}
                """
            )
            result = _rows(cur)[0]
            cur.close()
        return _ok({"table_name": table, "columns": columns, **result})
    except oracledb.Error as exc:
        return _err(f"oracle_checksum failed for {table}: {exc}")


oracle_server = create_sdk_mcp_server(
    name="oracle_src",
    version="1.0.0",
    tools=[
        oracle_describe_schema,
        oracle_get_ddl,
        oracle_get_plsql_source,
        oracle_sample_rows,
        oracle_row_count,
        oracle_checksum,
    ],
)
