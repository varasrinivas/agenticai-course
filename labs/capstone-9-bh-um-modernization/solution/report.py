"""Render the modernization report.

Written for one reader: the person deciding whether to approve a modernization
that changes how medical-necessity determinations are made.

Two consequences for the ordering and the tone:

  * The gap register comes FIRST, because it is the deliverable. Coverage and
    cost come last, because they are the least important thing on the page and
    putting them at the top invites reading the run as a throughput exercise.

  * Nothing is softened. An unresolved divergence is not "a note". A run that
    is not ready says so in its first line.
"""

from __future__ import annotations

import html
import json
import os

import config
from gap_register import GapRegister
from observability import Metrics


def _read(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def collect(artifact_dir: str | None = None) -> dict:
    """Everything the report needs, read from artifacts rather than from the
    agent's account of them. The agent's summary of its own run is the thing
    under review."""
    d = artifact_dir or config.ARTIFACT_DIR
    return {
        "register": _read(os.path.join(d, "gap-register.json")),
        "parity": _read(os.path.join(d, "parity-report.json")),
        "queue": _read(os.path.join(d, "manual-review-queue.json")),
        "rules_ir": _read(os.path.join(d, "rules-ir.json")),
        "seam_map": _read(os.path.join(d, "seam-map.json")),
        "screens": _read(os.path.join(d, "screen-inventory.json")),
        "metrics": _read(os.path.join(d, "metrics.json")),
    }


def verdict(data: dict) -> tuple[str, list[str]]:
    """Ready, or not, and why. This is the report's first line."""
    blocking: list[str] = []

    register = data.get("register")
    if not register:
        blocking.append("no gap register -- the gap-analysis phase did not complete")
    else:
        blocking.extend(register.get("acceptance_problems", []))

    parity = data.get("parity")
    if not parity:
        blocking.append("no parity report -- the validation phase did not complete")
    else:
        blocking.extend(parity.get("blocking", []))
        for check in parity.get("checks", []):
            if check.get("expected_nonzero") and check.get("count") == 0:
                blocking.append(
                    f"check {check.get('id')} ({check.get('name')}) came back clean "
                    f"and is expected to be non-zero. Suspect the validator "
                    f"before the port.")

    queue = (data.get("queue") or {}).get("items", [])
    if not queue:
        blocking.append(
            "nothing queued for human decision. This system contains branches "
            "nobody can explain; a run that queues nothing has guessed at one.")

    return ("NOT READY" if blocking else "READY FOR REVIEW"), blocking


# ---------------------------------------------------------------- console


def render_console(data: dict) -> str:
    state, blocking = verdict(data)
    lines = ["", "=" * 74, f"  MODERNIZATION REPORT -- {state}", "=" * 74, ""]

    if blocking:
        lines.append("BLOCKING:")
        for b in blocking:
            lines.append(f"  * {b}")
        lines.append("")

    register = data.get("register")
    if register:
        reg = GapRegister()
        from gap_register import GapEntry
        reg.entries = [
            GapEntry(**{k: v for k, v in e.items() if k in GapEntry.__annotations__})
            for e in register.get("entries", [])]
        reg.backlog_crosscheck = register.get("backlog_crosscheck", reg.backlog_crosscheck)
        lines.append(reg.render())
        lines.append("")

    parity = data.get("parity")
    if parity:
        lines.append("PARITY CHECKS")
        lines.append("-" * 74)
        for c in parity.get("checks", []):
            note = ""
            if c.get("expected_nonzero"):
                note = "  (expected non-zero)" if c.get("count") else \
                       "  <-- CLEAN, AND EXPECTED NON-ZERO"
            lines.append(f"  [{c.get('id')}] {c.get('name'):<34} "
                         f"{c.get('count')}{note}")
        lines.append("")

    queue = (data.get("queue") or {}).get("items", [])
    lines.append(f"QUEUED FOR HUMAN DECISION ({len(queue)})")
    lines.append("-" * 74)
    for item in queue:
        lines.append(f"  {item.get('artifact')}")
        lines.append(f"      why : {item.get('reason')}")
        lines.append(f"      ASK : {item.get('question')}")
    if not queue:
        lines.append("  none -- see BLOCKING above")
    lines.append("")

    metrics = data.get("metrics")
    if metrics:
        lines.append("COVERAGE AND COST")
        lines.append("-" * 74)
        lines.append("  " + str(metrics.get("coverage", "")).replace("\n", "\n  "))
        lines.append(f"  output tokens : {metrics.get('output_tokens', 0):,}")
        lines.append(f"  wall time     : {metrics.get('wall_ms', 0) / 1000:.1f}s")
        for w in metrics.get("warnings", []):
            lines.append(f"  ! {w}")
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------- html

_CSS = """
body{font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;
     background:#f6f7f9;color:#1a1a1a}
.wrap{max-width:960px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:30px 0 10px;
   border-bottom:1px solid #d8dbe0;padding-bottom:5px}
.state{display:inline-block;padding:4px 12px;border-radius:3px;font-weight:600;
       font-size:13px;letter-spacing:.02em}
.ready{background:#dcefdc;color:#22551f}.notready{background:#fbe3e3;color:#7a1f1f}
table{border-collapse:collapse;width:100%;margin:10px 0;background:#fff}
th,td{border:1px solid #dfe2e6;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#eef1f5;font-weight:600}
.v-must-not-port{background:#fbe3e3}.v-must-build-new{background:#fdf3d8}
.v-extend{background:#eef4fb}.v-port-as-is{background:#f4f7f4}
.harm{color:#7a1f1f;font-weight:600}
.blocking{background:#fbe3e3;border:1px solid #7a1f1f;padding:10px 14px;margin:14px 0}
.clean-suspect{background:#fbe3e3;font-weight:600}
.muted{color:#666;font-size:12px}
code{background:#eef1f5;padding:1px 4px;border-radius:2px;font-size:12px}
"""


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def render_html(data: dict) -> str:
    state, blocking = verdict(data)
    cls = "notready" if blocking else "ready"
    out = [
        "<!doctype html><meta charset='utf-8'>",
        "<title>BH UM modernization report</title>",
        f"<style>{_CSS}</style><div class='wrap'>",
        "<h1>Behavioral health UM modernization</h1>",
        f"<span class='state {cls}'>{_esc(state)}</span>",
    ]

    if blocking:
        out.append("<div class='blocking'><strong>Blocking:</strong><ul>")
        out += [f"<li>{_esc(b)}</li>" for b in blocking]
        out.append("</ul></div>")

    register = data.get("register") or {}
    entries = register.get("entries", [])
    if entries:
        out.append("<h2>Gap register</h2>")
        dist = register.get("distribution", {})
        out.append("<p class='muted'>" + " &middot; ".join(
            f"{_esc(k)}: {_esc(v)}" for k, v in dist.items()) + "</p>")
        out.append("<table><tr><th>Capability</th><th>Verdict</th>"
                   "<th>Evidence</th><th>Harm / requirement</th><th>Backlog</th></tr>")
        order = {"must-not-port": 0, "must-build-new": 1, "extend": 2, "port-as-is": 3}
        for e in sorted(entries, key=lambda e: order.get(e.get("verdict"), 9)):
            detail = e.get("harm") or e.get("requirement") or ""
            harm_cls = " class='harm'" if e.get("harm") else ""
            out.append(
                f"<tr class='v-{_esc(e.get('verdict'))}'>"
                f"<td>{_esc(e.get('capability'))}</td>"
                f"<td>{_esc(e.get('verdict'))}</td>"
                f"<td>{_esc(e.get('evidence'))}</td>"
                f"<td{harm_cls}>{_esc(detail)}</td>"
                f"<td>{_esc(e.get('backlog'))}</td></tr>")
        out.append("</table>")

        cc = register.get("backlog_crosscheck", {})
        out.append("<h2>Backlog cross-check</h2>")
        for key, label in (("agreements", "Agreements (strongest findings)"),
                           ("we_found_they_did_not", "We found, they did not"),
                           ("they_list_we_missed", "They list, we missed")):
            items = cc.get(key, [])
            out.append(f"<p><strong>{_esc(label)}</strong> ({len(items)})</p><ul>")
            out += [f"<li>{_esc(i)}</li>" for i in items]
            out.append("</ul>")

    parity = data.get("parity")
    if parity:
        out.append("<h2>Parity checks</h2><table>"
                   "<tr><th>#</th><th>Check</th><th>Count</th><th>Note</th></tr>")
        for c in parity.get("checks", []):
            suspect = c.get("expected_nonzero") and not c.get("count")
            note = "CLEAN, AND EXPECTED NON-ZERO &mdash; suspect the validator" \
                if suspect else ("expected non-zero" if c.get("expected_nonzero") else "")
            row_cls = " class='clean-suspect'" if suspect else ""
            out.append(f"<tr{row_cls}><td>{_esc(c.get('id'))}</td>"
                       f"<td>{_esc(c.get('name'))}</td>"
                       f"<td>{_esc(c.get('count'))}</td><td>{note}</td></tr>")
        out.append("</table>")

    queue = (data.get("queue") or {}).get("items", [])
    out.append(f"<h2>Queued for human decision ({len(queue)})</h2>")
    if queue:
        out.append("<table><tr><th>Artifact</th><th>Why</th>"
                   "<th>The question</th></tr>")
        for i in queue:
            out.append(f"<tr><td><code>{_esc(i.get('artifact'))}</code></td>"
                       f"<td>{_esc(i.get('reason'))}</td>"
                       f"<td><strong>{_esc(i.get('question'))}</strong></td></tr>")
        out.append("</table>")
    else:
        out.append("<div class='blocking'>Nothing queued. A run over this system "
                   "that queues nothing has guessed at something.</div>")

    metrics = data.get("metrics")
    if metrics:
        out.append("<h2>Coverage and cost</h2>")
        out.append(f"<p>{_esc(metrics.get('coverage'))}</p>")
        out.append(f"<p class='muted'>{metrics.get('output_tokens', 0):,} output "
                   f"tokens &middot; {metrics.get('wall_ms', 0) / 1000:.1f}s</p>")
        for w in metrics.get("warnings", []):
            out.append(f"<p class='harm'>! {_esc(w)}</p>")

    out.append("</div>")
    return "\n".join(out)


def write(artifact_dir: str | None = None) -> dict[str, str]:
    d = artifact_dir or config.ARTIFACT_DIR
    data = collect(d)
    os.makedirs(d, exist_ok=True)

    html_path = os.path.join(d, "modernization_report.html")
    json_path = os.path.join(d, "modernization_report.json")

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(render_html(data))

    state, blocking = verdict(data)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump({"verdict": state, "blocking": blocking, **data}, fh, indent=2)

    return {"html": html_path, "json": json_path}


if __name__ == "__main__":
    paths = write()
    print(render_console(collect()))
    print(f"wrote {paths['html']}\nwrote {paths['json']}")
