"""MCP server `reference_src` -- the architecture donor, READ-ONLY.

Six tools, none of which writes. That is the first line of defence; the
`enforce_source_readonly` hook is the second, catching path traversal.

The tools are shaped to encourage reading the FILES rather than the README.
`ref_read_config` and `ref_read_migrations` return parsed structure with counts
attached, because the cartographer's job is to report that there are two tables
and zero foreign keys, and a count it did not compute itself is a count it will
get wrong.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

import config
import hooks

_ROOT = config.REFERENCE_ROOT

# Never walked. node_modules would swamp any listing, and the vendored copy
# excludes it anyway -- but a student who runs npm install should not then get
# a 40,000-file inventory.
_SKIP_DIRS = {"node_modules", ".git", "dist", "target", ".nx", ".angular", "__pycache__"}


def _ok(payload: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"error": message})}]}


def _safe(relative: str) -> str | None:
    """Resolve inside the tree, or None. Defence in depth with the hook."""
    target = os.path.normpath(os.path.join(_ROOT, relative or "."))
    root = os.path.normpath(_ROOT)
    if target == root or target.startswith(root + os.sep):
        return target
    return None


def _read(path: str, tool_input: dict) -> tuple[str | None, str | None]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return None, str(exc)
    # Every result passes the gate before it reaches the model. The reference
    # platform should carry no clinical content at all -- if this ever trims
    # something, that is itself a finding worth reporting.
    filtered, _modified = hooks.filter_tool_result("ref_read", tool_input, text)
    return filtered, None


@tool(
    "ref_list_tree",
    "Inventory of the reference platform under a subpath: file, type and size. "
    "Start here; the layout is the first thing to map.",
    {"subpath": str},
)
async def ref_list_tree(args: dict) -> dict:
    subpath = args.get("subpath") or "."
    root = _safe(subpath)
    if root is None:
        return _err(f"{subpath!r} resolves outside the reference tree")
    if not os.path.exists(root):
        return _err(f"not found: {subpath}")

    files: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                size = -1
            files.append({
                "path": os.path.relpath(full, _ROOT).replace(os.sep, "/"),
                "ext": os.path.splitext(name)[1],
                "bytes": size,
            })
    return _ok({"root": subpath, "file_count": len(files), "files": files})


@tool(
    "ref_read_file",
    "Read one file from the reference platform. Use it to check what a "
    "convention ACTUALLY is rather than recalling it.",
    {"path": str},
)
async def ref_read_file(args: dict) -> dict:
    relative = args.get("path") or ""
    target = _safe(relative)
    if target is None:
        return _err(f"{relative!r} resolves outside the reference tree")
    if not os.path.isfile(target):
        return _err(f"not a file: {relative}")
    text, error = _read(target, args)
    if error:
        return _err(error)
    return _ok({"path": relative, "bytes": len(text), "content": text})


@tool(
    "ref_read_config",
    "Parsed configuration: nx workspace, docker compose, helm, gateway routes, "
    "or the Spring application yaml. Returns structure plus counts.",
    {"kind": str},
)
async def ref_read_config(args: dict) -> dict:
    kind = (args.get("kind") or "").strip().lower()
    candidates = {
        "nx": ["nx.json", "package.json"],
        "compose": ["docker-compose.yml", "docker-compose.yaml"],
        "helm": ["infra/helm"],
        "kong": ["infra/kong", "infra/gateway"],
        "gateway": ["infra/kong", "infra/gateway"],
        "application-yml": [
            "apps/um-case-svc/src/main/resources/application.yml",
            "apps/um-case-svc/src/main/resources/application.yaml",
        ],
    }
    if kind not in candidates:
        return _err(f"unknown kind {kind!r}; expected one of {sorted(candidates)}")

    out: dict[str, Any] = {"kind": kind, "sources": []}
    for relative in candidates[kind]:
        target = _safe(relative)
        if target is None or not os.path.exists(target):
            continue
        if os.path.isdir(target):
            for dirpath, dirnames, filenames in os.walk(target):
                dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    text, error = _read(full, args)
                    if text is not None:
                        out["sources"].append({
                            "path": os.path.relpath(full, _ROOT).replace(os.sep, "/"),
                            "content": text})
        else:
            text, error = _read(target, args)
            if text is not None:
                out["sources"].append({"path": relative, "content": text})
                if relative.endswith(".json"):
                    try:
                        out["parsed"] = json.loads(text)
                    except json.JSONDecodeError:
                        pass

    if not out["sources"]:
        return _err(f"no {kind} configuration found in the reference tree")

    # Scanned across the WHOLE tree rather than across the requested kind. The
    # flags live in docker-compose.yml and the service yaml, so a cartographer
    # asking for `nx` would otherwise be told there are none -- and "no feature
    # flags" is a wrong answer about the platform's single best idea.
    out["feature_flags"] = _scan_feature_flags()
    return _ok(out)


def _sequence_flows(text: str) -> list[tuple[str, str]]:
    """(source, target) for every sequence flow in a BPMN document."""
    edges = []
    for tag in re.findall(r"<(?:\w+:)?sequenceFlow\b[^>]*>", text):
        src = re.search(r'sourceRef="([^"]+)"', tag)
        dst = re.search(r'targetRef="([^"]+)"', tag)
        if src and dst:
            edges.append((src.group(1), dst.group(1)))
    return edges


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    """Real cycle detection over the flow graph.

    Counting flows against nodes looked like a cheap proxy and is not one: a
    one-shot process with a single branch has more flows than tasks, so the
    count heuristic reports a loop where there is none. Reporting "this process
    already loops" about a process that terminates would tell the synthesizer
    it has nothing to build, which is the whole finding inverted.
    """
    graph: dict[str, list[str]] = {}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)

    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {}

    def visit(node: str) -> bool:
        colour[node] = GREY
        for nxt in graph.get(node, ()):
            state = colour.get(nxt, WHITE)
            if state == GREY:          # back edge -- a cycle
                return True
            if state == WHITE and visit(nxt):
                return True
        colour[node] = BLACK
        return False

    return any(colour.get(n, WHITE) == WHITE and visit(n) for n in list(graph))


def _scan_feature_flags() -> list[dict]:
    """Every *_ENABLED flag anywhere in the tree, with where it appears.

    Each one still has to be CLASSIFIED before it is mirrored. A cache flag and
    a consent flag are not the same kind of thing: ask what a week of `false`
    in production would cost, and if the answer is an unlawful disclosure
    rather than a slow page, it must not be a flag at all.
    """
    found: dict[str, set[str]] = {}
    scannable = {".yml", ".yaml", ".ts", ".java", ".json", ".env", ".properties", ".md"}
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if os.path.splitext(name)[1] not in scannable:
                continue
            full = os.path.join(dirpath, name)
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            rel = os.path.relpath(full, _ROOT).replace(os.sep, "/")
            for flag in set(re.findall(r"\b([A-Z][A-Z0-9_]*_ENABLED)\b", text)):
                found.setdefault(flag, set()).add(rel)
    return [{"flag": f, "appears_in": sorted(v)} for f, v in sorted(found.items())]


@tool(
    "ref_read_workflow",
    "The Camunda BPMN process or DMN decision table as XML. Read both: the "
    "process says whether it can loop, the table says what it can output.",
    {"artifact": str},
)
async def ref_read_workflow(args: dict) -> dict:
    artifact = (args.get("artifact") or "").strip().lower()
    if artifact not in {"bpmn", "dmn"}:
        return _err("artifact must be 'bpmn' or 'dmn'")

    camunda = _safe("camunda")
    if camunda is None or not os.path.isdir(camunda):
        return _err("no camunda/ directory in the reference tree")

    found = []
    for name in sorted(os.listdir(camunda)):
        if not name.endswith(f".{artifact}"):
            continue
        text, error = _read(os.path.join(camunda, name), args)
        if text is None:
            continue
        entry = {"file": f"camunda/{name}", "content": text}

        if artifact == "dmn":
            # Surface the two things a mirrored table gets wrong: the hit
            # policy, and which outputs are actually reachable.
            entry["hit_policy"] = (re.search(r'hitPolicy="(\w+)"', text) or [None, None])[1]
            entry["rule_count"] = len(re.findall(r"<rule\b", text))
            outputs = set(re.findall(r"<outputEntry[^>]*>\s*<text>\s*\"?(\w+)\"?", text))
            entry["reachable_outputs"] = sorted(o for o in outputs if o.isupper())
            entry["inputs"] = sorted(set(re.findall(r'<input[^>]*label="([^"]+)"', text)))
        else:
            # The elements are namespaced (<bpmn:userTask .../>), so the prefix
            # is optional in every pattern below. Without it the parse reports
            # "no user tasks", which reads as "there is no manual review step"
            # -- the exact opposite of the finding.
            entry["user_tasks"] = re.findall(
                r"<(?:\w+:)?userTask[^>]*\bid=\"([^\"]+)\"", text)
            entry["has_timer"] = "timerEventDefinition" in text
            entry["assignees"] = re.findall(
                r'(?:\w+:)?(?:assignee|candidateGroups|candidateUsers)="([^"]*)"', text)
            # An unassigned user task is a task nobody is responsible for. Where
            # the task encodes a licensure requirement, the missing candidate
            # group has silently deleted the rule while leaving the diagram
            # looking complete.
            entry["unassigned_user_tasks"] = (
                entry["user_tasks"] if not entry["assignees"] else [])
            edges = _sequence_flows(text)
            entry["flow_count"] = len(edges)
            entry["loops_back"] = _has_cycle(edges)
            # Whether the process can come back around is the single most
            # important thing about it here: concurrent review IS a loop, and a
            # process that terminates after one decision cannot express the
            # domain no matter how faithfully everything else is copied.
        found.append(entry)

    if not found:
        return _err(f"no .{artifact} files in camunda/")
    return _ok({"artifact": artifact, "count": len(found), "files": found})


@tool(
    "ref_read_migrations",
    "Every Flyway migration in order, with its DDL and a count of tables and "
    "foreign keys. Count them yourself before reporting on referential integrity.",
    {},
)
async def ref_read_migrations(args: dict) -> dict:
    migrations: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if "migration" not in dirpath.replace(os.sep, "/"):
            continue
        for name in sorted(filenames):
            if not name.endswith(".sql"):
                continue
            text, error = _read(os.path.join(dirpath, name), args)
            if text is None:
                continue
            migrations.append({
                "file": os.path.relpath(os.path.join(dirpath, name), _ROOT).replace(os.sep, "/"),
                "version": (re.match(r"V(\d+)__", name) or [None, None])[1],
                "content": text,
            })

    migrations.sort(key=lambda m: int(m["version"] or 0))
    blob = "\n".join(m["content"] for m in migrations)
    return _ok({
        "count": len(migrations),
        "tables": sorted(set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", blob, re.I))),
        "foreign_keys": len(re.findall(r"\bREFERENCES\b", blob, re.I)),
        "unique_constraints": len(re.findall(r"\bUNIQUE\b", blob, re.I)),
        "migrations": migrations,
    })


@tool(
    "ref_read_backlog",
    "The reference platform team's own enhancement backlog. Cross-check the gap "
    "register against it: agreement is signal, disagreement is worth investigating.",
    {},
)
async def ref_read_backlog(args: dict) -> dict:
    path = config.BACKLOG_PATH
    if not os.path.isfile(path):
        return _err(
            f"backlog not found at {path}. Report the gap register WITHOUT a "
            f"cross-check rather than inventing one -- a missing cross-check is "
            f"a stated limitation; a fabricated one is worse than none."
        )
    text, error = _read(path, {"path": path})
    if error:
        return _err(error)

    # The enhancements are markdown TABLE rows numbered in the first cell, not
    # bullet points. Scraping bullets returns the legend and the sprint notes
    # and none of the actual backlog -- a cross-check against the wrong seven
    # lines is worse than no cross-check, because it looks like one.
    items: list[dict] = []
    for row in re.findall(r"^\|\s*(\d+)\s*\|(.+)$", text, re.M):
        number, rest = row
        cells = [c.strip() for c in rest.split("|")]
        title = re.sub(r"\*\*(.+?)\*\*", r"\1", cells[0]) if cells else ""
        items.append({
            "id": int(number),
            "title": title.split("—")[0].split(" - ")[0].strip(),
            "detail": title,
            "files": cells[1] if len(cells) > 1 else "",
            "risk": cells[3] if len(cells) > 3 else "",
        })

    return _ok({
        "path": os.path.basename(path),
        "item_count": len(items),
        "items": items,
        "note": (
            "These are the platform team's OWN planned-and-unbuilt items. Where "
            "the gap register agrees with one, that is the strongest kind of "
            "finding: two independent readings reached the same conclusion. "
            "Report agreements and disagreements as separate lists."
        ),
        "content": text,
    })


reference_server = create_sdk_mcp_server(
    name="reference_src",
    version="1.0.0",
    tools=[ref_list_tree, ref_read_file, ref_read_config,
           ref_read_workflow, ref_read_migrations, ref_read_backlog],
)
