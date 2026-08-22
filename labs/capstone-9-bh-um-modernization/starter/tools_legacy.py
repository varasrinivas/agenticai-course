"""MCP server `legacy_src` -- the domain donor, READ-ONLY.

Seven tools. None writes; the `enforce_source_readonly` hook catches traversal.

Two design decisions worth stating.

**Every result passes through the protected-content gate before it reaches the
model.** The gate lives at this boundary because a PreToolUse hook runs before
the tool and therefore cannot see what it returns. This is the honest place for
the guarantee: where the data actually appears.

**`legacy_sample_rows` returns SHAPE by default, not values.** An archaeologist
does not need to read a clinical narrative to establish that it is a CLOB, that
it is non-null on 11 of 12 rows, that it reaches three sinks, and that the
intake DTO discards it. Values are available from the synthetic fixture, under
budget, when explicitly asked for -- and asking is a deliberate act rather than
a default.
"""

# =============================================================================
# GIVEN COMPLETE. Read it, do not rewrite it.
#
# This file is plumbing, not the lesson. Your work is in the files carrying
# numbered TODOs -- run `grep -rn "TODO [0-9]" starter/` to list them in order.
# =============================================================================


from __future__ import annotations

import json
import os
import re
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

import config
import hooks

_ROOT = config.LEGACY_ROOT
_SKIP_DIRS = {".git", "target", "__pycache__", ".idea"}

# Columns whose values are protected wherever they appear.
_PROTECTED_COLUMNS = {"CLINICAL_NARRATIVE", "OLD_NARRATIVE", "NEW_NARRATIVE", "PAYLOAD"}


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


def _safe(relative: str) -> str | None:
    target = os.path.normpath(os.path.join(_ROOT, relative or "."))
    root = os.path.normpath(_ROOT)
    return target if target == root or target.startswith(root + os.sep) else None


def _read_filtered(path: str, tool_input: dict) -> tuple[str | None, bool, str | None]:
    """Read a file and run it past the protected-content gate."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return None, False, str(exc)
    filtered, modified = hooks.filter_tool_result("legacy_read", tool_input, text)
    return filtered, modified, None


@tool(
    "legacy_list_tree",
    "Inventory of the legacy monolith under a subpath. Read db/schema_changes.txt "
    "before the schema file -- the hand-maintained log is closer to production.",
    {"subpath": str},
)
async def legacy_list_tree(args: dict) -> dict:
    subpath = args.get("subpath") or "."
    root = _safe(subpath)
    if root is None:
        return _err(f"{subpath!r} resolves outside the legacy tree")
    if not os.path.exists(root):
        return _err(f"not found: {subpath}")

    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, _ROOT).replace(os.sep, "/")
            try:
                size = os.path.getsize(full)
            except OSError:
                size = -1
            files.append({"path": rel, "ext": os.path.splitext(name)[1], "bytes": size})
    return _ok({"root": subpath, "file_count": len(files), "files": files})


@tool(
    "legacy_read_java",
    "One Java class, by fully-qualified name or by path. Business logic lives in "
    "service/; the DAOs carry the SQL that defines the real data model.",
    {"fqcn": str},
)
async def legacy_read_java(args: dict) -> dict:
    ref = (args.get("fqcn") or "").strip()
    if not ref:
        return _err("fqcn is required")

    if ref.endswith(".java") or "/" in ref or "\\" in ref:
        candidate = _safe(ref)
    else:
        candidate = _safe(os.path.join("src", "main", "java", *ref.split(".")) + ".java")

    if candidate is None:
        return _err(f"{ref!r} resolves outside the legacy tree")

    if not os.path.isfile(candidate):
        # Fall back to a basename search, because an archaeologist reasonably
        # says "AuthCaseService" without knowing the package.
        simple = ref.split(".")[-1].replace(".java", "")
        for dirpath, dirnames, filenames in os.walk(os.path.join(_ROOT, "src")):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            if f"{simple}.java" in filenames:
                candidate = os.path.join(dirpath, f"{simple}.java")
                break
        else:
            return _err(f"no such class: {ref}")

    text, modified, error = _read_filtered(candidate, args)
    if error:
        return _err(error)
    return _ok({
        "path": os.path.relpath(candidate, _ROOT).replace(os.sep, "/"),
        "content": text,
        "content_filtered": modified,
    })


@tool(
    "legacy_read_jsp",
    "One JSP view. TREAT THESE AS A SOURCE OF RULES, NOT AS MARKUP -- role "
    "guards, scriptlet derivations and field visibility live here and nowhere else.",
    {"view": str},
)
async def legacy_read_jsp(args: dict) -> dict:
    view = (args.get("view") or "").strip()
    if not view:
        return _err("view is required")
    if not view.endswith(".jsp"):
        view += ".jsp"

    candidate = _safe(view) if ("/" in view or "\\" in view) else None
    if candidate is None or not os.path.isfile(candidate):
        base = os.path.join(_ROOT, "src", "main", "webapp", "WEB-INF", "jsp")
        found = None
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            if os.path.basename(view) in filenames:
                found = os.path.join(dirpath, os.path.basename(view))
                break
        if found is None:
            return _err(f"no such view: {view}")
        candidate = found

    text, modified, error = _read_filtered(candidate, args)
    if error:
        return _err(error)

    # Surfaced rather than left to be noticed. These three counts are the
    # difference between reading a template as a screen and reading it as a
    # place where rules were left.
    role_guards = re.findall(r"<c:(?:if|when)\s+test=\"\$\{[^}]*role[^}]*\}\"", text or "", re.I)
    scriptlets = re.findall(r"<%(?!--|@|=)(.*?)%>", text or "", re.S)
    return _ok({
        "path": os.path.relpath(candidate, _ROOT).replace(os.sep, "/"),
        "content": text,
        "content_filtered": modified,
        "role_conditional_count": len(role_guards),
        "scriptlet_count": len(scriptlets),
        "form_actions": re.findall(r"<form[^>]*action=\"([^\"]+)\"", text or "", re.I),
        "hint": (
            "A conditional testing a role is an AUTHORIZATION RULE. A scriptlet "
            "computing a value is a BUSINESS RULE with no other home. Report each "
            "with a proposed new home -- a route guard, a service method, or a "
            "decision-table input -- never as markup to be translated."
        ),
    })


@tool(
    "legacy_read_xml",
    "One XML configuration: web (the deployment descriptor and the complete "
    "inventory of what is deployed), dispatcher-servlet, applicationContext "
    "(where the transaction manager is), log4j, or quartz.",
    {"name": str},
)
async def legacy_read_xml(args: dict) -> dict:
    name = (args.get("name") or "").strip().lower().replace(".xml", "")
    known = {
        "web": "src/main/webapp/WEB-INF/web.xml",
        "dispatcher-servlet": "src/main/webapp/WEB-INF/dispatcher-servlet.xml",
        "dispatcher": "src/main/webapp/WEB-INF/dispatcher-servlet.xml",
        "applicationcontext": "src/main/resources/applicationContext.xml",
        "log4j": "src/main/resources/log4j.xml",
        "quartz": "src/main/resources/applicationContext.xml",   # triggers live there
    }
    if name not in known:
        return _err(f"unknown config {name!r}; expected one of {sorted(set(known))}")

    candidate = _safe(known[name])
    if candidate is None or not os.path.isfile(candidate):
        return _err(f"not found: {known[name]}")
    text, modified, error = _read_filtered(candidate, args)
    if error:
        return _err(error)
    return _ok({"path": known[name], "content": text, "content_filtered": modified})


@tool(
    "legacy_read_sql",
    "DDL or PL/SQL for one database object, or a whole db/ file by name. The "
    "rules engine is PKG_LOC_RULES; the drift log is schema_changes.txt.",
    {"object_name": str},
)
async def legacy_read_sql(args: dict) -> dict:
    ref = (args.get("object_name") or "").strip()
    if not ref:
        return _err("object_name is required")

    db_dir = os.path.join(_ROOT, "db")
    if not os.path.isdir(db_dir):
        return _err("no db/ directory in the legacy tree")

    # A file name, if it is one.
    for name in sorted(os.listdir(db_dir)):
        if ref.lower() in (name.lower(), os.path.splitext(name)[0].lower()):
            text, modified, error = _read_filtered(os.path.join(db_dir, name), args)
            if error:
                return _err(error)
            return _ok({"path": f"db/{name}", "content": text, "content_filtered": modified})

    # Otherwise, the DDL for one object, extracted from whichever file holds it.
    upper = ref.upper()
    for name in sorted(os.listdir(db_dir)):
        if not name.endswith((".sql", ".txt")):
            continue
        raw, modified, error = _read_filtered(os.path.join(db_dir, name), args)
        if error or raw is None:
            continue
        pattern = re.compile(
            r"(CREATE(?:\s+OR\s+REPLACE)?\s+"
            r"(?:TABLE|VIEW|TRIGGER|SEQUENCE|INDEX|PACKAGE(?:\s+BODY)?)\s+"
            + re.escape(upper) + r"\b.*?)(?=\n(?:CREATE|--\s*=====)|\Z)",
            re.I | re.S)
        chunks = pattern.findall(raw)
        if chunks:
            return _ok({
                "object": upper,
                "path": f"db/{name}",
                "definitions": len(chunks),
                "content": "\n\n".join(chunks),
                "content_filtered": modified,
            })

    available = sorted(n for n in os.listdir(db_dir))
    return _err(f"no object or file named {ref!r}. db/ contains: {available}")


@tool(
    "legacy_sample_rows",
    "SHAPE of a table's rows: column names, types, null counts, distinct counts. "
    "Set include_values=true for actual values from the synthetic fixture -- "
    "protected columns stay redacted either way.",
    {"table_name": str, "limit": int, "include_values": bool},
)
async def legacy_sample_rows(args: dict) -> dict:
    table = (args.get("table_name") or "").strip().upper()
    if not table:
        return _err("table_name is required")
    limit = int(args.get("limit") or 20)
    include_values = bool(args.get("include_values"))

    rows, error = _parse_inserts(table)
    if error:
        return _err(error)
    if not rows:
        return _err(f"no rows for {table} in db/02_seed.sql")

    width = max(len(r) for r in rows)
    columns = _column_names(table, width)

    shape = []
    for i, col in enumerate(columns):
        values = [r[i] if i < len(r) else None for r in rows]
        non_null = [v for v in values if v is not None and v != "NULL"]
        entry = {
            "column": col,
            "non_null": len(non_null),
            "null": len(values) - len(non_null),
            "distinct": len(set(non_null)),
            "protected": col in _PROTECTED_COLUMNS,
        }
        if not entry["protected"] and non_null:
            entry["example"] = str(non_null[0])[:60]
        shape.append(entry)

    payload = {
        "table": table,
        "row_count": len(rows),
        "shape": shape,
        "note": (
            "Shape is usually enough. You do not need to read a clinical "
            "narrative to establish that it is a CLOB, that it is non-null on "
            "most rows, and that it reaches the log, the queue payload and the "
            "audit trigger."
        ),
    }

    if include_values:
        out = []
        for r in rows[:limit]:
            row = {}
            for i, col in enumerate(columns):
                v = r[i] if i < len(r) else None
                row[col] = "[PROTECTED-COLUMN]" if col in _PROTECTED_COLUMNS else v
            out.append(row)
        payload["rows"] = out
        payload["values_note"] = (
            "All data is synthetic, generated from documented seed 20260822. "
            "Protected columns are redacted regardless."
        )
    return _ok(payload)


@tool(
    "legacy_row_count",
    "Exact row count for a table in the synthetic fixture. Use it for the "
    "identity audit -- a real number beats 'some'.",
    {"table_name": str},
)
async def legacy_row_count(args: dict) -> dict:
    table = (args.get("table_name") or "").strip().upper()
    rows, error = _parse_inserts(table)
    if error:
        return _err(error)

    payload = {"table": table, "row_count": len(rows)}

    # The identity audit, computed rather than described. A third of pre-2014
    # members have no health-plan identifier, and a port that keys on the wrong
    # one matches by luck for whatever subset of formats coincides.
    if table == "BH_MEMBER" and rows:
        unresolved = sum(1 for r in rows if len(r) > 1 and (r[1] is None or r[1] == "NULL"))
        plan_ids = [r[1] for r in rows if len(r) > 1 and r[1] not in (None, "NULL")]
        payload["unresolved_to_plan"] = unresolved
        payload["unresolved_pct"] = round(100.0 * unresolved / len(rows), 1)
        payload["duplicate_plan_ids"] = len(plan_ids) - len(set(plan_ids))
        payload["note"] = (
            "MEMBER_ID is the carve-out vendor's key; PLAN_MEMBER_ID is the health "
            "plan's and is nullable. Anything crossing to the plan must key on the "
            "second. The modern platform stores one opaque member_id with no member "
            "table, so it accepts either without objecting."
        )
    return _ok(payload)


# ---------------------------------------------------------------------
# Seed parsing
# ---------------------------------------------------------------------

_SEED = os.path.join(_ROOT, "db", "02_seed.sql")


def _column_names(table: str, width: int) -> list[str]:
    """Column names from the CREATE TABLE in 01_schema.sql, or positional."""
    schema = os.path.join(_ROOT, "db", "01_schema.sql")
    try:
        with open(schema, encoding="utf-8", errors="replace") as fh:
            ddl = fh.read()
    except OSError:
        return [f"col{i + 1}" for i in range(width)]

    m = re.search(rf"CREATE TABLE {re.escape(table)}\s*\((.*?)\n\);", ddl, re.I | re.S)
    if not m:
        return [f"col{i + 1}" for i in range(width)]

    cols = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("--") or line.upper().startswith("CONSTRAINT"):
            continue
        name = line.split()[0].strip(",")
        if name.upper() not in {"PRIMARY", "FOREIGN", "UNIQUE", "CHECK"}:
            cols.append(name.upper())
    while len(cols) < width:
        cols.append(f"col{len(cols) + 1}")
    return cols[:width]


def _parse_inserts(table: str) -> tuple[list[list[str | None]], str | None]:
    """Values from every INSERT for one table in the seed file.

    A small SQL-literal splitter rather than a SQL parser: the fixture is a
    known file with a known shape, and a dependency-free reader keeps this
    module importable in CI without a database.
    """
    if not os.path.isfile(_SEED):
        return [], f"seed fixture not found at {_SEED}"

    with open(_SEED, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    rows: list[list[str | None]] = []
    for m in re.finditer(rf"INSERT INTO {re.escape(table)}\s+VALUES\s*\(", text, re.I):
        start = m.end()
        depth, i, in_str = 1, start, False
        while i < len(text) and depth:
            ch = text[i]
            if in_str:
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        i += 1
                    else:
                        in_str = False
            elif ch == "'":
                in_str = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        rows.append(_split_values(text[start:i - 1]))
    return rows, None


def _split_values(blob: str) -> list[str | None]:
    out: list[str | None] = []
    buf, depth, in_str = [], 0, False
    i = 0
    while i < len(blob):
        ch = blob[i]
        if in_str:
            if ch == "'":
                if i + 1 < len(blob) and blob[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_str = False
            else:
                buf.append(ch)
        elif ch == "'":
            in_str = True
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            out.append(_clean("".join(buf)))
            buf = []
        else:
            buf.append(ch)
        i += 1
    out.append(_clean("".join(buf)))
    return out


def _clean(token: str) -> str | None:
    t = token.strip().replace("||", "")
    t = re.sub(r"\s+", " ", t).strip()
    if t.upper() == "NULL" or t == "":
        return None
    if t.upper().startswith("DATE "):
        return t[5:].strip().strip("'")
    return t


legacy_server = create_sdk_mcp_server(
    name="legacy_src",
    version="1.0.0",
    tools=[legacy_list_tree, legacy_read_java, legacy_read_jsp, legacy_read_xml,
           legacy_read_sql, legacy_sample_rows, legacy_row_count],
)
