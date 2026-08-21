"""Local (non-database) tools: application-source scanning and artifact
writing.

`scan_app_sql` deliberately does the *detection* in plain Python regex
rather than asking the model to eyeball whole files. Finding
`ROWNUM` is a job for a regex; deciding what the rewrite should be, and
whether the surrounding logic still holds, is the job for the model.
Spending tokens on the first half would be waste, and would also miss
things -- a regex does not get bored on file 400.
"""

from __future__ import annotations

import json
import os
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

import config

# The construct registry lives in oracle_constructs.py -- no SDK import, so
# it can be unit-tested without an API key or the agent framework.
from oracle_constructs import CONSTRUCTS, UNTRANSLATABLE


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


@tool(
    "scan_app_sql",
    "Scan application source files for Oracle-specific SQL constructs. "
    "Returns file, line number, the offending snippet, and which "
    "constructs were matched -- the model decides the rewrite, the regex "
    "just finds the candidates.",
    {"path": str, "extensions": str},
)
async def scan_app_sql(args: dict) -> dict:
    root = args.get("path") or config.APP_SOURCE_DIR
    exts = tuple(
        e.strip() if e.strip().startswith(".") else f".{e.strip()}"
        for e in (args.get("extensions") or ".py,.java,.sql").split(",")
        if e.strip()
    )

    if not os.path.isdir(root):
        return _err(f"Not a directory: {root}")

    findings: list[dict] = []
    files_scanned = 0

    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in sorted(filenames):
            if not filename.endswith(exts):
                continue
            full = os.path.join(dirpath, filename)
            files_scanned += 1
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError as exc:
                findings.append({"file": full, "error": str(exc)})
                continue

            for number, line in enumerate(lines, start=1):
                matched = [
                    {
                        "construct": c.label,
                        "note": c.note,
                        "translatable": c.translatable,
                    }
                    for c in CONSTRUCTS
                    if c.found_in(line)
                ]
                if matched:
                    findings.append(
                        {
                            "file": os.path.relpath(full, root),
                            "line": number,
                            "snippet": line.rstrip()[:220],
                            "oracle_constructs": matched,
                        }
                    )

    by_construct: dict[str, int] = {}
    for finding in findings:
        for match in finding.get("oracle_constructs", []):
            by_construct[match["construct"]] = by_construct.get(match["construct"], 0) + 1

    blocked = sorted(set(by_construct) & UNTRANSLATABLE)

    return _ok(
        {
            "root": root,
            "files_scanned": files_scanned,
            "finding_count": len(findings),
            "by_construct": dict(sorted(by_construct.items(), key=lambda kv: -kv[1])),
            # Constructs with no safe translation. These must be REFUSED and
            # queued for redesign, not rewritten -- a plausible-looking
            # translation here passes review and breaks in production.
            "requires_manual_redesign": blocked,
            "findings": findings,
        }
    )


@tool(
    "write_artifact",
    "Write generated DDL, PL/pgSQL, or a unified diff under artifacts/. "
    "Paths are confined to that directory -- a subagent cannot write "
    "over the source tree.",
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
    version="1.0.0",
    tools=[scan_app_sql, write_artifact],
)
