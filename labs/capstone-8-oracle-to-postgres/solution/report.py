"""Migration reporting: console dashboard, JSON, and a standalone HTML page.

The HTML report is the artifact a human reads before approving cutover,
so it is built around one question -- "is there any reason not to go
live?" -- rather than around a percentage. Defects are listed first, in
full, before any success metric. A report that leads with "94% passed"
buries the 6% that matters.
"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone

from observability.metrics import costliest, slowest, summarize
from observability.tracer import Span


def _fmt_ms(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    if ms < 60_000:
        return f"{ms / 1000:.1f}s"
    return f"{ms / 60_000:.1f}m"


def _load_validation(artifact_dir: str) -> dict:
    path = os.path.join(artifact_dir, "validation_summary.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


# ------------------------------------------------------------- console
def render_console(spans: list[Span], budget) -> None:
    stats = summarize(spans)

    print("\n" + "=" * 74)
    print("  MIGRATION REPORT".ljust(56) + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 74)

    print(f"\n  {'PHASE':<12}{'OBJECTS':>9}{'TOKENS':>12}{'TIME':>10}{'ERRORS':>9}")
    print("  " + "-" * 70)
    for phase, data in stats["by_phase"].items():
        flag = "  <-- FAILURES" if data["errors"] else ""
        print(
            f"  {phase:<12}{data['count']:>9}{data['tokens']:>12,}"
            f"{_fmt_ms(data['ms']):>10}{data['errors']:>9}{flag}"
        )
    print("  " + "-" * 70)
    print(
        f"  {'TOTAL':<12}{stats['spans']:>9}{stats['total_output_tokens']:>12,}"
        f"{_fmt_ms(stats['total_ms']):>10}{stats['errors']:>9}"
    )

    print(f"\n  Budget    : {budget}")
    print(f"  Est. cost : ${stats['estimated_usd']:.2f} (output tokens only)")

    if spans:
        print("\n  Slowest objects:")
        for span in slowest(spans, 3):
            print(f"    {_fmt_ms(span.duration_ms):>8}  {span.label}")
        print("\n  Most tokens:")
        for span in costliest(spans, 3):
            print(f"    {span.tokens:>8,}  {span.label}")

    errors = [s for s in spans if s.error]
    if errors:
        print(f"\n  {len(errors)} FAILED SPAN(S):")
        for span in errors:
            print(f"    {span.label}: {span.error}")

    print("\n" + "=" * 74 + "\n")


# ---------------------------------------------------------------- json
def write_json_report(spans: list[Span], budget, artifact_dir: str) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "budget": {"spent": budget.spent, "ceiling": budget.ceiling},
        "validation": _load_validation(artifact_dir),
        **summarize(spans),
        "spans": [s.to_dict() for s in spans],
    }
    os.makedirs(artifact_dir, exist_ok=True)
    path = os.path.join(artifact_dir, "migration_report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return path


# ---------------------------------------------------------------- html
_CSS = """
:root { --bg:#0A1628; --panel:#132339; --text:#E8EEF7; --muted:#8FA3BF;
        --accent:#D4A843; --ok:#10B981; --bad:#EF4444; --warn:#F59E0B; }
* { box-sizing:border-box; }
body { margin:0; padding:2rem; background:var(--bg); color:var(--text);
       font:16px/1.6 "Source Sans 3",system-ui,sans-serif; }
h1 { font-size:1.6rem; margin:0 0 .25rem; color:var(--accent); }
h2 { font-size:1.15rem; margin:2rem 0 .75rem; border-bottom:1px solid #24384f;
     padding-bottom:.35rem; }
.sub { color:var(--muted); margin:0 0 1.5rem; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
         gap:1rem; }
.card { background:var(--panel); border-radius:10px; padding:1rem 1.15rem;
        border-left:3px solid var(--accent); }
.card .n { font-size:1.7rem; font-weight:700; font-family:"JetBrains Mono",monospace; }
.card .l { color:var(--muted); font-size:.8rem; text-transform:uppercase;
           letter-spacing:.06em; }
.card.bad { border-left-color:var(--bad); } .card.bad .n { color:var(--bad); }
.card.ok  { border-left-color:var(--ok); }  .card.ok .n  { color:var(--ok); }
table { width:100%; border-collapse:collapse; font-size:.9rem; }
th,td { text-align:left; padding:.5rem .65rem; border-bottom:1px solid #24384f; }
th { color:var(--muted); font-weight:600; text-transform:uppercase;
     font-size:.72rem; letter-spacing:.06em; }
td.num { text-align:right; font-family:"JetBrains Mono",monospace; }
.defect { background:rgba(239,68,68,.08); border-left:3px solid var(--bad);
          padding:.85rem 1rem; border-radius:6px; margin:.6rem 0; }
.defect b { color:var(--bad); }
.gate { background:rgba(245,158,11,.1); border-left:3px solid var(--warn);
        padding:1rem 1.15rem; border-radius:6px; margin:1.25rem 0; }
.wrap { overflow-x:auto; }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
"""


def write_html_report(spans: list[Span], budget, artifact_dir: str) -> str:
    stats = summarize(spans)
    validation = _load_validation(artifact_dir)
    defects = validation.get("defects", [])

    def esc(value) -> str:
        return html.escape(str(value))

    rows = "\n".join(
        f"<tr><td>{esc(p)}</td>"
        f"<td class='num'>{d['count']}</td>"
        f"<td class='num'>{d['tokens']:,}</td>"
        f"<td class='num'>{_fmt_ms(d['ms'])}</td>"
        f"<td class='num'>{d['errors']}</td></tr>"
        for p, d in stats["by_phase"].items()
    )

    span_rows = "\n".join(
        f"<tr><td>{esc(s.phase)}</td><td>{esc(s.target)}</td>"
        f"<td class='num'>{s.tokens:,}</td>"
        f"<td class='num'>{_fmt_ms(s.duration_ms)}</td>"
        f"<td>{esc(s.error or '')}</td></tr>"
        for s in spans
    )

    defect_html = (
        "".join(
            f"<div class='defect'><b>{esc(d.get('check', 'DEFECT'))}</b> &mdash; "
            f"{esc(d.get('object', ''))}<br>{esc(d.get('detail', ''))}</div>"
            for d in defects
        )
        or "<p style='color:var(--ok)'>No defects reported by the validator. "
           "Confirm the validator actually ran &mdash; an empty defect list and "
           "a validator that never executed look identical here.</p>"
    )

    gate = (
        "<div class='gate'><b>Cutover is blocked pending human approval.</b><br>"
        "Review the defects above, then run "
        "<code>python coordinator.py --phase cutover --approve-cutover</code>."
        "</div>"
    )

    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Migration Report &mdash; Oracle to PostgreSQL</title>
<style>{_CSS}</style></head><body>
<h1>Oracle &rarr; PostgreSQL Migration Report</h1>
<p class="sub">Generated {esc(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
&middot; Meridian Public Records &middot; UCC filing system</p>

<h2>Defects</h2>
{defect_html}
{gate}

<h2>At a glance</h2>
<div class="cards">
  <div class="card"><div class="n">{stats['spans']}</div><div class="l">Objects processed</div></div>
  <div class="card {'bad' if stats['errors'] else 'ok'}"><div class="n">{stats['errors']}</div><div class="l">Failed spans</div></div>
  <div class="card {'bad' if defects else 'ok'}"><div class="n">{len(defects)}</div><div class="l">Validation defects</div></div>
  <div class="card"><div class="n">{stats['total_output_tokens']:,}</div><div class="l">Output tokens</div></div>
  <div class="card"><div class="n">${stats['estimated_usd']:.2f}</div><div class="l">Est. cost</div></div>
  <div class="card"><div class="n">{_fmt_ms(stats['total_ms'])}</div><div class="l">Agent time</div></div>
</div>

<h2>By phase</h2>
<div class="wrap"><table>
<thead><tr><th>Phase</th><th>Objects</th><th>Tokens</th><th>Time</th><th>Errors</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Every object</h2>
<div class="wrap"><table>
<thead><tr><th>Phase</th><th>Target</th><th>Tokens</th><th>Time</th><th>Error</th></tr></thead>
<tbody>{span_rows}</tbody></table></div>

</body></html>"""

    os.makedirs(artifact_dir, exist_ok=True)
    path = os.path.join(artifact_dir, "migration_report.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return path
