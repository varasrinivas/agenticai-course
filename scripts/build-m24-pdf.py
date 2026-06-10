"""Build a print-friendly PDF of M24: What's Next — The Agent Frontier.

Transformations applied:
  - Dark theme → light print theme (CSS variable overrides)
  - Each .animation-container → static SVG/HTML diagram
  - Code tab panels → both Python + Node.js shown stacked
  - Quiz → plain readable Q&A
  - Sidebar, progress bar, nav → removed

Output: output/pdf/M24-whats-next-print.pdf
"""
from __future__ import annotations
import re, shutil, subprocess, sys, tempfile
from pathlib import Path
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "output" / "M24-whats-next-agent-frontier.html"
OUT  = ROOT / "output" / "pdf" / "M24-whats-next-print.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists(): return p
    sys.exit("No Chrome or Edge found.")

# ── Print CSS override (injects at end of <head>) ─────────────────────────────

PRINT_CSS = """
<style id="print-override">
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

@page { size: A4; margin: 16mm 18mm 18mm 18mm; }

/* ── Kill dark theme, reset layout ── */
html, body {
  background: #fff !important;
  color: #1a1f2e !important;
  font-family: 'Source Sans 3', sans-serif !important;
  font-size: 10pt !important;
  line-height: 1.6 !important;
  margin: 0 !important; padding: 0 !important;
}

/* ── Hide interactive chrome ── */
.top-progress, .course-header, .sidebar-nav,
.animation-controls, .anim-btn,
.copy-btn, .code-tabs,
.next-module-nav, .module-nav, .progress-bar { display: none !important; }

/* ── Page layout: single column ── */
.page-container { display: block !important; max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
.content { max-width: 100% !important; }

/* ── Module hero ── */
.module-hero, .hero-section {
  background: #f0f4ff !important;
  border-bottom: 2px solid #6366F1 !important;
  color: #1a1f2e !important;
  padding: 1.5rem !important;
  margin-bottom: 1.5rem !important;
  border-radius: 0 !important;
  page-break-after: avoid;
}
.module-hero *, .hero-section * { color: #1a1f2e !important; }
.module-hero h1, .hero-section h1 { font-size: 22pt !important; color: #0a1628 !important; margin-bottom: 0.4rem !important; }
.hero-meta, .module-meta { color: #4a5568 !important; font-size: 9pt !important; }
.track-badge { background: rgba(99,102,241,0.1) !important; border-color: #6366F1 !important; color: #4338ca !important; }

/* ── Headings ── */
h1 { font-size: 20pt !important; color: #0a1628 !important; }
h2 { font-size: 14pt !important; color: #0a1628 !important; border-top: 1.5px solid #e2e8f0 !important; padding-top: 0.75rem !important; margin-top: 1.5rem !important; page-break-after: avoid; }
h3 { font-size: 11.5pt !important; color: #1a1f2e !important; page-break-after: avoid; }
h4 { font-size: 10.5pt !important; color: #374151 !important; page-break-after: avoid; }

/* ── Callout boxes ── */
.analogy-box, .tech-def-box, .callout-why, .callout-warning,
.callout-security, .callout-cost, .callout-cert {
  background: #f8fafc !important;
  color: #1a1f2e !important;
  border-radius: 0 6px 6px 0 !important;
  padding: 0.8rem 1rem !important;
  margin: 1rem 0 !important;
  page-break-inside: avoid;
}
.analogy-box { background: #fffbeb !important; border-left-color: #d4a843 !important; }
.tech-def-box { background: #eff6ff !important; border-left-color: #3b82f6 !important; }
.callout-why  { background: #f0fdf4 !important; border-left-color: #10b981 !important; }
.callout-warning { background: #fffbeb !important; border-left-color: #f59e0b !important; }
.callout-security { background: #fff1f2 !important; border-left-color: #f43f5e !important; }
.callout-cert { background: #fffbeb !important; border-left-color: #d4a843 !important; }
.box-label { color: inherit !important; }
.analogy-box .box-label { color: #b45309 !important; }
.tech-def-box .box-label { color: #1d4ed8 !important; }
.callout-why .box-label  { color: #065f46 !important; }
.callout-warning .box-label { color: #92400e !important; }
.callout-security .box-label { color: #9f1239 !important; }

/* ── Tooltips: show definition inline ── */
.term-tooltip { color: #1d4ed8 !important; border-bottom: none !important; cursor: default !important; }
.term-tooltip .tooltip-content { display: none !important; }

/* ── Code blocks ── */
.code-block-wrapper {
  background: #f5f7fa !important;
  border: 1px solid #d1d9e6 !important;
  border-radius: 8px !important;
  margin: 1rem 0 !important;
  page-break-inside: avoid;
}
.code-panel { display: block !important; }
.code-panel pre {
  background: #f5f7fa !important;
  color: #1a2133 !important;
  padding: 0.85rem 1rem !important;
  font-size: 8.5pt !important;
  margin: 0 !important;
  border-bottom: 1px solid #e2e8f0;
}
.code-panel:last-child pre { border-bottom: none !important; }
.code-panel pre code { color: #1a2133 !important; background: none !important; }
/* Prism override */
.token.comment, .token.prolog { color: #6b7280 !important; }
.token.keyword { color: #7c3aed !important; }
.token.string  { color: #065f46 !important; }
.token.function { color: #1d4ed8 !important; }
.token.number  { color: #b45309 !important; }
.output-block {
  background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important;
  color: #065f46 !important; border-radius: 6px !important;
  font-size: 8.5pt !important; page-break-inside: avoid;
}
.output-label { color: #374151 !important; }

/* ── Quiz section: readable Q&A ── */
.quiz-question { background: #f8fafc !important; border: 1px solid #e2e8f0 !important; color: #1a1f2e !important; border-radius: 8px !important; page-break-inside: avoid; }
.quiz-question h4 { color: #0a1628 !important; }
.quiz-option { border-color: #d1d9e6 !important; color: #1a1f2e !important; }
.quiz-option.correct { background: #f0fdf4 !important; border-color: #10b981 !important; }
.quiz-marker { border-color: #9ca3af !important; }

/* ── Tables ── */
table { border-collapse: collapse; width: 100%; margin: 0.75rem 0; page-break-inside: avoid; }
th { background: #f0f4ff !important; color: #0a1628 !important; font-size: 9pt; padding: 0.45rem 0.65rem; border: 1px solid #c7d2e8; }
td { padding: 0.38rem 0.65rem; border: 1px solid #dde3ec; font-size: 9pt; color: #1a1f2e !important; background: #fff !important; vertical-align: top; }
tr:nth-child(even) td { background: #f9fafb !important; }

/* ── Static diagram base ── */
.static-diagram {
  border: 1px solid #e2e8f0;
  border-top: 3px solid #6366F1;
  border-radius: 0 0 8px 8px;
  background: #fafbff;
  padding: 1.25rem;
  margin: 1rem 0;
  page-break-inside: avoid;
}
.diag-title {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 9.5pt; font-weight: 700; color: #4338ca;
  text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 0.9rem; padding-bottom: 0.4rem;
  border-bottom: 1px solid #e0e7ff;
}

/* ── General overrides ── */
a { color: #1d4ed8 !important; }
strong { color: #0a1628 !important; }
p, li { color: #1a1f2e !important; }
ul, ol { color: #1a1f2e !important; }
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
</style>
"""

# ── Static diagram HTML ───────────────────────────────────────────────────────

def diag_a2a() -> str:
    return """
<div class="static-diagram">
  <div class="diag-title">Agent-to-Agent Protocol Handshake</div>
  <div style="display:grid;grid-template-columns:1fr 2.2fr 1fr;gap:0.5rem;align-items:start;font-size:9pt">
    <div style="text-align:center">
      <div style="background:#6366F1;color:#fff;border-radius:8px;padding:0.5rem 0.6rem;font-weight:700;font-size:9pt">Orchestrator</div>
      <div style="color:#6b7280;font-size:8pt;margin-top:0.2rem">coordinator</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:0.5rem;padding-top:0.1rem">
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:5px;padding:0.35rem 0.6rem;font-family:monospace;font-size:8pt">
        <span style="color:#6366F1;font-weight:700">①</span> GET <code>/.well-known/agent.json</code> &rarr; <em>discover capabilities</em>
      </div>
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:5px;padding:0.35rem 0.6rem;font-family:monospace;font-size:8pt;text-align:right">
        <span style="color:#10b981;font-weight:700">②</span> CARD <code>{ skills: [deduction-analysis, …] }</code>
      </div>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:5px;padding:0.35rem 0.6rem;font-family:monospace;font-size:8pt">
        <span style="color:#6366F1;font-weight:700">③</span> POST <code>tasks/send { input: "$85K income" }</code>
      </div>
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:5px;padding:0.35rem 0.6rem;font-family:monospace;font-size:8pt;text-align:right">
        <span style="color:#10b981;font-weight:700">④</span> task: completed <code>{ savings: $2,728 }</code>
      </div>
      <div style="text-align:center;font-size:8pt;color:#6b7280;margin-top:0.2rem">
        &uarr; routed via <strong>Agent Marketplace</strong> (discovery broker)
      </div>
    </div>
    <div style="text-align:center">
      <div style="background:#10b981;color:#fff;border-radius:8px;padding:0.5rem 0.6rem;font-weight:700;font-size:9pt">Tax Specialist</div>
      <div style="color:#6b7280;font-size:8pt;margin-top:0.2rem">domain expert</div>
    </div>
  </div>
</div>"""


def diag_timeline() -> str:
    steps = [
        ("Text Only",     "Chatbot",           "#6366F1"),
        ("Tool Use",      "API Integrator",    "#8b5cf6"),
        ("Vision",        "Doc Processor",     "#7c3aed"),
        ("Computer Use",  "SW Operator",       "#6d28d9"),
        ("Ext. Thinking", "Complex Planner",   "#5b21b6"),
        ("Skills",        "Reusable Specialist","#4c1d95"),
    ]
    nodes = ""
    for label, role, color in steps:
        nodes += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex:1">
          <div style="width:14px;height:14px;border-radius:50%;background:{color};border:2px solid #fff;box-shadow:0 0 0 2px {color};margin-bottom:0.35rem"></div>
          <div style="font-size:8pt;font-weight:700;color:{color};text-align:center;line-height:1.2">{label}</div>
          <div style="font-size:7.5pt;color:#6b7280;text-align:center;margin-top:0.15rem">{role}</div>
        </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">Claude Capability Evolution Timeline</div>
  <div style="position:relative;padding:0.5rem 0 0.5rem">
    <div style="position:absolute;top:0.85rem;left:5%;right:5%;height:2px;background:linear-gradient(90deg,#6366F1,#4c1d95)"></div>
    <div style="display:flex;justify-content:space-between;gap:0.25rem;position:relative">
      {nodes}
    </div>
  </div>
</div>"""


def diag_decision() -> str:
    rows = [
        ("What&rsquo;s the status of order PO-2024-8847?",
         "PROCEED", "#16a34a", "#f0fdf4", "#bbf7d0",
         "Routine query, within scope, no risk"),
        ("Compare loan rates for these two applicants",
         "FLAG — BIAS", "#b45309", "#fffbeb", "#fde68a",
         "Potential for demographic bias &mdash; flag for human review"),
        ("Approve this $50,000 surgical pre-auth",
         "ESCALATE", "#be123c", "#fff1f2", "#fecdd3",
         "High-stakes medical decision — requires physician sign-off"),
    ]
    rows_html = ""
    for query, verdict, color, bg, border, reason in rows:
        rows_html += f"""
      <tr>
        <td style="width:38%;font-style:italic;color:#374151">&ldquo;{query}&rdquo;</td>
        <td style="width:18%;text-align:center">
          <span style="background:{bg};border:1px solid {border};color:{color};border-radius:5px;padding:0.2rem 0.5rem;font-weight:700;font-size:8.5pt;white-space:nowrap">{verdict}</span>
        </td>
        <td style="width:44%;color:#374151;font-size:9pt">{reason}</td>
      </tr>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">Agent Decision Scenarios — Escalation Framework</div>
  <table style="margin:0">
    <thead>
      <tr>
        <th style="width:38%">Query</th>
        <th style="width:18%;text-align:center">Decision</th>
        <th style="width:44%">Reason</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""


def diag_ecosystem(container: Tag) -> str:
    text = container.get_text(" ", strip=True)
    # Extract communities and reading lists from raw text
    return f"""
<div class="static-diagram">
  <div class="diag-title">The Agent Developer Ecosystem</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;font-size:9pt">
    <div>
      <div style="font-weight:700;color:#4338ca;margin-bottom:0.4rem;font-size:9.5pt">👥 Communities</div>
      <ul style="margin:0;padding-left:1.1rem;color:#374151;line-height:1.7">
        <li>Anthropic Developer Forum</li>
        <li>AI Engineer community</li>
        <li>LangChain Discord</li>
        <li>LlamaIndex Discord</li>
        <li>Weights &amp; Biases community</li>
      </ul>
    </div>
    <div>
      <div style="font-weight:700;color:#4338ca;margin-bottom:0.4rem;font-size:9.5pt">📚 Essential Reading</div>
      <ul style="margin:0;padding-left:1.1rem;color:#374151;line-height:1.7">
        <li>Anthropic research publications</li>
        <li>Claude documentation guides</li>
        <li>Simon Willison&rsquo;s AI blog</li>
        <li>Constitutional AI papers</li>
        <li>RLHF research</li>
      </ul>
    </div>
  </div>
</div>"""


def diag_framework_table(container: Tag) -> str:
    # The animation already contains a table or table-like content; extract it
    existing_table = container.find("table")
    if existing_table:
        return f'<div class="static-diagram"><div class="diag-title">Agent Frameworks Comparison</div>{existing_table}</div>'
    rows = [
        ("Anthropic Agent SDK", "Native Claude agent framework with tools, hooks, sessions",
         "Designed for Claude, tight integration, maintained by Anthropic", "Claude-only, newer ecosystem"),
        ("LangChain", "General-purpose LLM framework with chains, agents, tools",
         "Huge ecosystem, many integrations, extensive docs", "Abstraction leaks, rapid API churn"),
        ("LlamaIndex", "Data-centric: RAG pipelines, document indexing, retrieval",
         "Best-in-class document ingestion and retrieval", "Narrower scope, less agent tooling"),
        ("CrewAI", "Role-based multi-agent collaboration framework",
         "Intuitive role/task model, easy multi-agent setup", "Less control over low-level loop"),
        ("Raw API", "Direct Messages API calls, no framework",
         "Full control, no abstraction overhead, easiest to debug", "You build everything from scratch"),
    ]
    rows_html = "".join(f"""<tr>
      <td style="font-weight:700;color:#1d4ed8;white-space:nowrap">{name}</td>
      <td>{does}</td>
      <td style="color:#065f46">{pros}</td>
      <td style="color:#9f1239">{cons}</td>
    </tr>""" for name, does, pros, cons in rows)
    return f"""
<div class="static-diagram">
  <div class="diag-title">Agent Frameworks — Comparison</div>
  <table style="margin:0;font-size:8.5pt">
    <thead><tr>
      <th style="width:18%">Framework</th>
      <th style="width:30%">What It Does</th>
      <th style="width:26%">Pros</th>
      <th style="width:26%">Cons</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""


def diag_sdk_table(container: Tag) -> str:
    existing_table = container.find("table")
    if existing_table:
        return f'<div class="static-diagram"><div class="diag-title">Vendor SDK Comparison</div>{existing_table}</div>'
    rows = [
        ("Anthropic", "claude-agent-sdk", "Claude Opus/Sonnet/Haiku 4.x", "BYO (Bash/Edit tools)", "Via wrapper", "Python, TypeScript"),
        ("OpenAI", "openai-agents", "GPT-5 / GPT-4.x / o-series", "Yes — hosted Code Interpreter", "Yes (native)", "Python, TypeScript"),
        ("Google", "genai-agents", "Gemini 2.x", "Yes — hosted code runner", "Partial", "Python, Java, Go"),
        ("Microsoft", "Azure AI Agent Service", "GPT-4o, Phi-3, custom", "Yes — Azure Functions", "Roadmap", "Python, C#, JS"),
    ]
    rows_html = "".join(f"""<tr>
      <td style="font-weight:700;white-space:nowrap">{vendor}</td>
      <td style="font-family:monospace;font-size:8pt">{sdk}</td>
      <td>{models}</td>
      <td style="font-size:8pt">{sandbox}</td>
      <td style="text-align:center">{a2a}</td>
      <td style="font-size:8pt">{langs}</td>
    </tr>""" for vendor, sdk, models, sandbox, a2a, langs in rows)
    return f"""
<div class="static-diagram">
  <div class="diag-title">Vendor SDK Comparison</div>
  <table style="margin:0;font-size:8pt">
    <thead><tr>
      <th>Vendor</th><th>SDK</th><th>Models</th>
      <th>Hosted Sandbox</th><th>A2A</th><th>Languages</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""


def diag_comparison() -> str:
    left = [
        ("Receive question", "#6366F1"),
        ("Loop: think → tool → observe", "#6366F1"),
        ("Stop on end_turn", "#6366F1"),
        ("Return answer", "#6366F1"),
    ]
    right = [
        ("Read repo: layout, conventions, CLAUDE.md", "#7c3aed"),
        ("Plan: write spec, decompose tasks", "#7c3aed"),
        ("Loop across files/tests/runs", "#7c3aed"),
        ("Commit, PR, iterate on feedback", "#7c3aed"),
    ]
    def steps(items):
        html = ""
        for i, (text, color) in enumerate(items, 1):
            html += f'<div style="display:flex;align-items:flex-start;gap:0.4rem;margin-bottom:0.35rem"><span style="background:{color};color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:7.5pt;font-weight:700;flex-shrink:0;margin-top:1px">{i}</span><span style="font-size:8.5pt;color:#374151">{text}</span></div>'
        return html
    def meta(label, horizon, context, state, color):
        return f'<div style="font-size:7.5pt;color:#6b7280;margin-top:0.5rem;padding-top:0.4rem;border-top:1px dashed #e2e8f0"><strong style="color:{color}">Horizon:</strong> {horizon} &nbsp;·&nbsp; <strong style="color:{color}">Context:</strong> {context} &nbsp;·&nbsp; <strong style="color:{color}">State:</strong> {state}</div>'
    return f"""
<div class="static-diagram">
  <div class="diag-title">One-Shot Agent vs Long-Horizon Coding Agent</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
    <div style="border:1px solid #c7d2fe;border-top:3px solid #6366F1;border-radius:0 0 6px 6px;padding:0.65rem 0.75rem;background:#fafbff">
      <div style="font-weight:800;color:#4338ca;font-size:9.5pt;margin-bottom:0.55rem">One-Shot Agent <span style="font-weight:400;font-size:8pt">(M15B-style)</span></div>
      {steps(left)}
      {meta("", "seconds – minutes", "single window", "in-memory list", "#6366F1")}
    </div>
    <div style="border:1px solid #ddd6fe;border-top:3px solid #7c3aed;border-radius:0 0 6px 6px;padding:0.65rem 0.75rem;background:#faf8ff">
      <div style="font-weight:800;color:#6d28d9;font-size:9.5pt;margin-bottom:0.55rem">Long-Horizon Coding Agent</div>
      {steps(right)}
      {meta("", "hours – days", "disk + vector DB", "file system + DB", "#7c3aed")}
    </div>
  </div>
</div>"""


def diag_roadmap() -> str:
    milestones = [
        ("1", "Complete Capstone Project", "Weeks 1–2", "Build the capstone end-to-end; document what you learned."),
        ("2", "First Production Deploy",   "Month 1",   "Ship one agent to real users; instrument with tracing."),
        ("3", "Novel Agent Project",       "Months 2–3","Tackle a problem you care about; go beyond course examples."),
        ("4", "Community Contribution",    "Months 3–6","Publish a library, blog post, or open-source agent."),
        ("5", "Deep Specialization",       "Ongoing",   "Pick one domain (RAG, multi-agent, eval) and go deep."),
    ]
    items = ""
    for num, title, when, desc in milestones:
        items += f"""
      <div style="display:flex;gap:0.75rem;margin-bottom:0.65rem;break-inside:avoid">
        <div style="flex-shrink:0;width:26px;height:26px;background:#6366F1;border-radius:50%;color:#fff;font-weight:800;font-size:9pt;display:flex;align-items:center;justify-content:center;margin-top:2px">{num}</div>
        <div>
          <div style="font-weight:700;font-size:9.5pt;color:#0a1628">{title} <span style="font-weight:400;font-size:8.5pt;color:#6366F1">&mdash; {when}</span></div>
          <div style="font-size:8.5pt;color:#374151">{desc}</div>
        </div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">Your 90-Day Agent Developer Roadmap</div>
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:5px;padding:0.4rem 0.7rem;font-size:8.5pt;color:#1d4ed8;font-weight:600;margin-bottom:0.75rem">
    ★ YOU ARE HERE — Module 24 of 24 complete
  </div>
  {items}
</div>"""


# ── Transformation pipeline ───────────────────────────────────────────────────

def replace_animations(soup: BeautifulSoup) -> None:
    containers = soup.find_all(class_="animation-container")
    for c in containers:
        title_el = c.find(class_="animation-title")
        title = title_el.get_text(strip=True) if title_el else ""
        text  = c.get_text(" ", strip=True)

        if "Protocol Handshake" in title or "A2A" in title:
            html = diag_a2a()
        elif "Capability Evolution" in title or "timeline" in title.lower():
            html = diag_timeline()
        elif "Decision Scenario" in title:
            html = diag_decision()
        elif "Ecosystem" in title:
            html = diag_ecosystem(c)
        elif "Long-Horizon" in title or "One-Shot" in title:
            html = diag_comparison()
        elif "90-Day" in title or "Roadmap" in title:
            html = diag_roadmap()
        elif "LangChain" in text and "CrewAI" in text:
            html = diag_framework_table(c)
        elif "Anthropic" in text and "claude-agent-sdk" in text:
            html = diag_sdk_table(c)
        else:
            # Generic: wrap as a simple diagram box
            html = f'<div class="static-diagram"><div class="diag-title">{title}</div>{c.decode_contents()}</div>'

        c.replace_with(BeautifulSoup(html, "html.parser"))


def fix_code_tabs(soup: BeautifulSoup) -> None:
    """Show all code panels (remove hidden-by-default panels) and add lang label."""
    for wrapper in soup.find_all(class_="code-block-wrapper"):
        tabs = wrapper.find(class_="code-tabs")
        if tabs:
            # Add language labels directly to each panel
            panels = wrapper.find_all(class_="code-panel")
            tab_btns = tabs.find_all(class_="code-tab") if tabs else []
            for panel, btn in zip(panels, tab_btns):
                panel["class"] = ["code-panel", "active"]
                lang = btn.get_text(strip=True) if btn else ""
                if lang:
                    label = soup.new_tag("div", attrs={"style": "font-family:'JetBrains Mono',monospace;font-size:7.5pt;font-weight:700;color:#6b7280;padding:0.25rem 0.85rem;background:#edf0f7;border-bottom:1px solid #d1d9e6"})
                    label.string = lang
                    panel.insert(0, label)
            tabs.decompose()


def fix_quiz(soup: BeautifulSoup) -> None:
    """Make quiz readable: show all options, mark correct ones."""
    for q in soup.find_all(class_="quiz-question"):
        for opt in q.find_all(class_="quiz-option"):
            opt["style"] = opt.get("style", "") + ";pointer-events:none;"


def strip_chrome(soup: BeautifulSoup) -> None:
    """Remove nav, progress bars, sidebar, tooltips, sticky elements."""
    for sel in [".top-progress", ".course-header", ".sidebar-nav",
                ".animation-controls", ".anim-btn", ".copy-btn",
                ".next-module-nav", ".module-nav", ".code-tabs"]:
        for el in soup.select(sel):
            el.decompose()

    # Unwrap page-container grid so content is full width
    pc = soup.find(class_="page-container")
    if pc:
        pc["style"] = "display:block;max-width:100%;padding:0;margin:0"

    # Tooltip content: remove interactive tooltip, keep the term text
    for tt in soup.find_all(class_="term-tooltip"):
        tc = tt.find(class_="tooltip-content")
        if tc: tc.decompose()


def inject_print_css(soup: BeautifulSoup) -> None:
    head = soup.find("head")
    if head:
        head.append(BeautifulSoup(PRINT_CSS, "html.parser"))


def add_code_panel_labels(soup: BeautifulSoup) -> None:
    """Called after fix_code_tabs — ensure all panels visible."""
    for panel in soup.find_all(class_="code-panel"):
        classes = panel.get("class", [])
        if "active" not in classes:
            panel["class"] = list(classes) + ["active"]


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    global OUT
    browser = find_browser()
    print(f"Browser : {browser}")
    print(f"Source  : {SRC}")

    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")

    print("Stripping interactive chrome…")
    strip_chrome(soup)

    print("Replacing animations with static diagrams…")
    replace_animations(soup)

    print("Fixing code tabs…")
    fix_code_tabs(soup)
    add_code_panel_labels(soup)

    print("Fixing quiz…")
    fix_quiz(soup)

    print("Injecting print CSS…")
    inject_print_css(soup)

    html = str(soup)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="m24-pdf-") as tmp:
        tmp_html = Path(tmp) / "m24-print.html"
        tmp_pdf  = Path(tmp) / "out.pdf"

        tmp_html.write_text(html, encoding="utf-8")
        print(f"HTML size: {tmp_html.stat().st_size // 1024} KB")
        print("Rendering PDF…")

        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--no-pdf-header-footer", "--virtual-time-budget=20000",
             f"--print-to-pdf={tmp_pdf}", tmp_html.resolve().as_uri()],
            check=True, capture_output=True,
        )

        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        if OUT.exists():
            for i in range(1, 10):
                cand = OUT.with_name(f"{OUT.stem}-v{i}.pdf")
                if not cand.exists():
                    try: OUT.rename(cand); print(f"Preserved: {cand.name}")
                    except PermissionError: OUT = cand
                    break

        shutil.move(str(tmp_pdf), str(OUT))

    size_kb = OUT.stat().st_size // 1024
    try:
        import pypdf
        pages = len(pypdf.PdfReader(str(OUT)).pages)
        print(f"\nWrote : {OUT}")
        print(f"Size  : {size_kb} KB, {pages} pages")
    except Exception:
        print(f"\nWrote : {OUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
