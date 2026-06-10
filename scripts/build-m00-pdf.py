"""Build a print-friendly PDF of M00: Course Overview — Agent Lifecycle.

Transformations applied:
  - Dark theme → light print theme (CSS variable overrides)
  - Each .animation-container → static HTML diagram
  - Quiz → plain readable Q&A (options shown, correct marked)
  - Sidebar, progress bar, nav → removed
  - No code panels (M00 is code-free)

Output: output/pdf/M00-course-overview-print.pdf
"""
from __future__ import annotations
import re, shutil, subprocess, sys, tempfile
from pathlib import Path
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "output" / "M00-course-overview-agent-lifecycle.html"
OUT  = ROOT / "output" / "pdf" / "M00-course-overview-print.pdf"

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


# ── Print CSS override ────────────────────────────────────────────────────────

PRINT_CSS = """
<style id="print-override">
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

@page { size: A4; margin: 16mm 18mm 18mm 18mm; }

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

/* ── Tooltips ── */
.term-tooltip { color: #1d4ed8 !important; border-bottom: none !important; cursor: default !important; }
.term-tooltip .tooltip-content { display: none !important; }

/* ── Quiz ── */
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

/* ── General ── */
a { color: #1d4ed8 !important; }
strong { color: #0a1628 !important; }
p, li { color: #1a1f2e !important; }
ul, ol { color: #1a1f2e !important; }
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
</style>
"""


# ── Static diagram functions ──────────────────────────────────────────────────

def diag_seven_eras() -> str:
    eras = [
        ("1948–2000s", "Rule-Based",        "Shannon, Turing, McCarthy",    "#6366F1"),
        ("2000s–2015", "Machine Learning",   "Hinton, AlexNet, GANs",        "#7c3aed"),
        ("2017–2020",  "Transformers + NLP", "Attention, BERT, GPT-3",       "#8b5cf6"),
        ("2020–2023",  "Generative AI",      "ChatGPT, DALL-E, Copilot",     "#0ea5e9"),
        ("2023–2024",  "LLMs Mature",        "Claude 3, RAG, fine-tune",     "#10b981"),
        ("2024–NOW",   "Agentic AI",         "Tool use, MCP, A2A, Strands",  "#f59e0b"),
        ("2025–2026+", "The Frontier",       "Multi-modal, in-context learn", "#ef4444"),
    ]
    nodes = ""
    for i, (period, label, detail, color) in enumerate(eras):
        nodes += f"""
      <div style="flex:1;display:flex;flex-direction:column;align-items:center;text-align:center">
        <div style="width:12px;height:12px;border-radius:50%;background:{color};
                    border:2px solid #fff;box-shadow:0 0 0 2px {color};margin-bottom:0.3rem"></div>
        <div style="font-size:7pt;color:#6b7280;line-height:1.2;margin-bottom:0.15rem">{period}</div>
        <div style="font-size:8pt;font-weight:700;color:{color};line-height:1.2;margin-bottom:0.15rem">{label}</div>
        <div style="font-size:7pt;color:#6b7280;line-height:1.3">{detail}</div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">Seven Eras of AI — Each Era Adds, Nothing Is Removed</div>
  <div style="position:relative;padding:0.4rem 0 0">
    <div style="position:absolute;top:0.6rem;left:3%;right:3%;height:2px;
                background:linear-gradient(90deg,#6366F1,#ef4444)"></div>
    <div style="display:flex;justify-content:space-between;gap:0.15rem;position:relative">
      {nodes}
    </div>
  </div>
  <div style="margin-top:0.75rem;padding:0.4rem 0.7rem;background:#eff6ff;border:1px solid #bfdbfe;
              border-radius:5px;font-size:8pt;color:#1d4ed8">
    Key insight: every new era <strong>adds</strong> capability on top of the previous — rule-based logic
    still runs inside every modern LLM call.
  </div>
</div>"""


def diag_three_pipelines() -> str:
    return """
<div class="static-diagram">
  <div class="diag-title">Same Data, Three Pipelines</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.6rem;font-size:8.5pt">

    <div style="border:1px solid #c7d2e8;border-top:3px solid #64748b;border-radius:0 0 6px 6px;padding:0.6rem">
      <div style="font-weight:800;color:#475569;margin-bottom:0.5rem;font-size:9pt">APPROACH 1: SCRIPT</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#f1f5f9;border-radius:4px;padding:0.4rem;margin-bottom:0.4rem;color:#334155">
        User: 6 numbers<br>predict_delinquency()<br>→ 0.823
      </div>
      <div style="color:#9f1239;font-size:7.5pt">✗ No explanation<br>✗ Misses name variants<br>✗ Hardcoded states</div>
    </div>

    <div style="border:1px solid #c7d2e8;border-top:3px solid #3b82f6;border-radius:0 0 6px 6px;padding:0.6rem">
      <div style="font-weight:800;color:#1d4ed8;margin-bottom:0.5rem;font-size:9pt">APPROACH 2: FASTAPI + ML</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#eff6ff;border-radius:4px;padding:0.4rem;margin-bottom:0.4rem;color:#1e40af">
        POST /predict {"company_name"}<br>SQL: ILIKE 'Acme...'<br>→ HIGH RISK (0.823)
      </div>
      <div style="color:#9f1239;font-size:7.5pt">✗ Hardcoded SQL patterns<br>✗ Returns 3/9 filings<br>✗ No reasoning shown</div>
    </div>

    <div style="border:1px solid #bbf7d0;border-top:3px solid #10b981;border-radius:0 0 6px 6px;padding:0.6rem">
      <div style="font-weight:800;color:#065f46;margin-bottom:0.5rem;font-size:9pt">APPROACH 3: AGENT</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#f0fdf4;border-radius:4px;padding:0.4rem;margin-bottom:0.4rem;color:#065f46">
        "Assess Acme Corp risk"<br>search("Acme Corp") → 3<br>search("ACME CORP") → 4<br>search("ACME") → 2 (DBA)
      </div>
      <div style="color:#15803d;font-size:7.5pt">✓ Finds all 9 filings<br>✓ Explains reasoning<br>✓ Adapts at runtime</div>
    </div>

  </div>
</div>"""


def diag_architecture_comparison() -> str:
    return """
<div class="static-diagram">
  <div class="diag-title">Architecture Comparison — Same Infrastructure, Different Brain</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;font-size:8.5pt">

    <div style="border:1px solid #c7d2e8;border-top:3px solid #3b82f6;border-radius:0 0 6px 6px;padding:0.7rem">
      <div style="font-weight:800;color:#1d4ed8;margin-bottom:0.5rem">Approach 2 — ML in FastAPI</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#eff6ff;border-radius:4px;padding:0.4rem;margin-bottom:0.5rem;color:#1e40af">
        POST /predict {"company_name": "Acme"}<br>
        1. Parse input<br>
        2. Query DB ← hardcoded SQL<br>
        3. Load pickle model<br>
        4. Predict → 0.823<br>
        5. Return JSON
      </div>
      <div style="font-size:8pt;color:#64748b;font-style:italic">Logic: YOUR CODE decides everything</div>
    </div>

    <div style="border:1px solid #bbf7d0;border-top:3px solid #10b981;border-radius:0 0 6px 6px;padding:0.7rem">
      <div style="font-weight:800;color:#065f46;margin-bottom:0.5rem">Approach 3 — Agent in FastAPI</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#f0fdf4;border-radius:4px;padding:0.4rem;margin-bottom:0.5rem;color:#065f46">
        POST /query {"question": "Assess Acme"}<br>
        1. Parse input<br>
        2. → Claude reasons about approach<br>
        3. → Claude calls search tools<br>
        4. → Claude synthesizes findings<br>
        5. Return explanation + risk
      </div>
      <div style="font-size:8pt;color:#64748b;font-style:italic">Logic: CLAUDE decides path at runtime</div>
    </div>

  </div>
</div>"""


def diag_intelligence_layer() -> str:
    layers = [
        ("LAYER 3 — INTELLIGENCE (Claude)", "reasoning · planning · synthesis · explanation",
         "#6366F1", "#eff6ff", "#c7d2fe", "NEW with agents — what Claude adds on top"),
        ("LAYER 2 — CAPABILITIES",          "search_filings() · predict_delinquency() · ML model",
         "#0ea5e9", "#f0f9ff", "#bae6fd", "Same in both approaches"),
        ("LAYER 1 — INFRASTRUCTURE",        "FastAPI · Docker · HTTP · auth · rate limits",
         "#64748b", "#f8fafc", "#e2e8f0", "Same in both approaches"),
    ]
    rows = ""
    for label, items, color, bg, border, note in layers:
        rows += f"""
      <div style="border:1px solid {border};border-left:4px solid {color};border-radius:0 6px 6px 0;
                  background:{bg};padding:0.5rem 0.75rem;margin-bottom:0.4rem">
        <div style="font-weight:700;font-size:8.5pt;color:{color};margin-bottom:0.15rem">{label}</div>
        <div style="font-family:monospace;font-size:8pt;color:#374151">{items}</div>
        <div style="font-size:7.5pt;color:#6b7280;margin-top:0.15rem;font-style:italic">{note}</div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">The Three-Layer Stack — What Agents Actually Add</div>
  {rows}
  <div style="text-align:center;font-size:8pt;color:#6366F1;font-weight:700;margin-top:0.4rem">
    ↑ Intelligence layer is what transforms a pipeline into an agent
  </div>
</div>"""


def diag_three_levels() -> str:
    cols = [
        ("LEVEL 1: CALL", "#64748b", "#f8fafc", "#e2e8f0",
         [("Question", ""), ("Claude (1 call)", ""), ("Answer", "")],
         "YOUR code decided everything. Fixed path, no branching."),
        ("LEVEL 2: WORKFLOW", "#3b82f6", "#eff6ff", "#c7d2fe",
         [("Question", ""), ("Claude: extract", ""), ("Claude: classify", ""), ("Claude: report", ""), ("Answer", "")],
         "Fixed order. YOUR code chose the sequence."),
        ("LEVEL 3: AGENT", "#6366F1", "#f0f0ff", "#c7d2fe",
         [("Question", ""), ("Claude decides:", "thinks"), ("search_filings", "tool"), ("get_details", "tool"), ("calc_risk", "tool"), ("loop until end_turn", ""), ("Answer (when ready)", "")],
         "CLAUDE decides path at runtime — open-ended loop."),
    ]
    def make_col(title, color, bg, border, steps, note):
        step_html = ""
        for step, tag in steps:
            tag_html = f' <span style="font-size:6.5pt;background:{color};color:#fff;border-radius:3px;padding:0.05rem 0.3rem;font-weight:700">{tag}</span>' if tag else ""
            step_html += f'<div style="padding:0.2rem 0.4rem;border:1px solid {border};border-radius:4px;background:#fff;font-size:7.5pt;margin-bottom:0.2rem;font-family:monospace">{step}{tag_html}</div>'
        return f"""
      <div style="border:1px solid {border};border-top:3px solid {color};border-radius:0 0 6px 6px;padding:0.6rem;background:{bg}">
        <div style="font-weight:800;color:{color};font-size:8.5pt;margin-bottom:0.5rem">{title}</div>
        {step_html}
        <div style="font-size:7.5pt;color:#6b7280;margin-top:0.4rem;font-style:italic">{note}</div>
      </div>"""
    cols_html = "".join(make_col(*c) for c in cols)
    return f"""
<div class="static-diagram">
  <div class="diag-title">Three Levels of AI Integration — Side by Side</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.6rem;font-size:8.5pt">
    {cols_html}
  </div>
</div>"""


def diag_chatbot_vs_agent() -> str:
    chatbot_steps = [
        ("User", "What's Acme Corp's total lien exposure?"),
        ("Claude", "I don't have access to filing databases. I can explain what a UCC lien is in general terms..."),
        ("Done", "Single turn — no tools, no data access"),
    ]
    agent_steps = [
        ("User", "What's Acme Corp's total lien exposure?"),
        ("Think", "I need to search the UCC filing database..."),
        ("Tool", 'search_filings("Acme Corporation") → 7 results'),
        ("Think", "Check for name variations too..."),
        ("Tool", 'search_filings("ACME CORP") → 4 more'),
        ("Think", "Check for DBA filings..."),
        ("Tool", 'search_filings("ACME") → 2 DBA hits'),
        ("Claude", "Total exposure: $2.4M across 13 filings in 4 states. Breakdown by creditor: ..."),
    ]
    def make_step(role, text, color):
        return f'<div style="margin-bottom:0.3rem;font-size:7.5pt"><strong style="color:{color}">{role}:</strong> {text}</div>'
    chatbot_html = "".join(make_step(r, t, "#64748b" if r != "User" else "#0a1628") for r, t in chatbot_steps)
    agent_html = ""
    for role, text in agent_steps:
        c = "#6366F1" if role == "Think" else ("#10b981" if role == "Tool" else ("#0a1628" if role == "User" else "#065f46"))
        agent_html += make_step(role, text, c)
    return f"""
<div class="static-diagram">
  <div class="diag-title">Chatbot vs Agent — Side by Side</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;font-size:8.5pt">
    <div style="border:1px solid #e2e8f0;border-top:3px solid #64748b;border-radius:0 0 6px 6px;padding:0.7rem;background:#f8fafc">
      <div style="font-weight:800;color:#475569;margin-bottom:0.5rem">Chatbot (one turn)</div>
      {chatbot_html}
      <div style="margin-top:0.5rem;background:#fff1f2;border:1px solid #fecdd3;border-radius:4px;padding:0.3rem 0.5rem;font-size:7.5pt;color:#9f1239">
        ✗ No real data · No tool access · Stateless
      </div>
    </div>
    <div style="border:1px solid #bbf7d0;border-top:3px solid #10b981;border-radius:0 0 6px 6px;padding:0.7rem;background:#f0fdf4">
      <div style="font-weight:800;color:#065f46;margin-bottom:0.5rem">Agent (multi-step loop)</div>
      {agent_html}
      <div style="margin-top:0.5rem;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:4px;padding:0.3rem 0.5rem;font-size:7.5pt;color:#065f46">
        ✓ Real data · Tool use · Reasoning trace · 13 filings found
      </div>
    </div>
  </div>
</div>"""


def diag_script_vs_agent() -> str:
    return """
<div class="static-diagram">
  <div class="diag-title">Script Approach vs Agent Approach</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;font-size:8.5pt">

    <div style="border:1px solid #e2e8f0;border-top:3px solid #64748b;border-radius:0 0 6px 6px;padding:0.7rem;background:#f8fafc">
      <div style="font-weight:800;color:#475569;margin-bottom:0.5rem">SCRIPT APPROACH</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#f1f5f9;border-radius:4px;padding:0.4rem;margin-bottom:0.4rem;color:#334155">
        name_list = ["Acme Corp", "ACME CORP", ...]  # 5 hardcoded<br>
        state_list = ["CA","NY","TX","IL","FL","GA"]  # 6 hardcoded<br>
        for state in state_list:<br>
        &nbsp;&nbsp;for name in name_list:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;search(name, state)<br>
        &nbsp;&nbsp;&nbsp;&nbsp;if status == "ACTIVE": ...  # rigid match
      </div>
      <div style="color:#9f1239;font-size:7.5pt">
        ✗ Misses DBAs and alternate names<br>
        ✗ Misses OH, PA, and other states<br>
        ✗ Hardcoded template output<br>
        ✗ Requires developer to update rules
      </div>
    </div>

    <div style="border:1px solid #bbf7d0;border-top:3px solid #6366F1;border-radius:0 0 6px 6px;padding:0.7rem;background:#fafbff">
      <div style="font-weight:800;color:#4338ca;margin-bottom:0.5rem">AGENT APPROACH</div>
      <div style="font-family:monospace;font-size:7.5pt;background:#f0f0ff;border-radius:4px;padding:0.4rem;margin-bottom:0.4rem;color:#3730a3">
        Think: "Search exact name first"<br>
        search("Acme Corp") → 4 hits<br>
        Think: "Check DBAs too..."<br>
        search("ACME") → found DBA!<br>
        Think: "Expand to more states..."<br>
        search(states=all) → 4 more<br>
        Synthesize: 8 total filings, 4 states
      </div>
      <div style="color:#15803d;font-size:7.5pt">
        ✓ Finds DBAs and name variations<br>
        ✓ Adapts state list at runtime<br>
        ✓ Synthesized narrative output<br>
        ✓ No developer changes needed
      </div>
    </div>

  </div>
</div>"""


def diag_nine_steps() -> str:
    steps = [
        ("1", "User message arrives",       '"What\'s the total lien exposure for Acme Corporation across all states?"',  "#6366F1"),
        ("2", "LLM thinks",                 'Claude reads the question: "I need to search the UCC filing database for this entity."', "#7c3aed"),
        ("3", "Tool call: search_filings",   'search_filings("Acme Corporation") — calls the DB with the exact company name.',       "#8b5cf6"),
        ("4", "Tool returns results",        "3 active filings found. Claude reads them and decides: need to check variations.",     "#0ea5e9"),
        ("5", "Second tool call",            'search_filings("ACME CORP") → 4 more. search_filings("ACME") → 2 DBA hits.',          "#10b981"),
        ("6", "LLM synthesizes",             "Claude now has all 9 filings. Calculates total exposure: $2.4M across 4 states.",      "#16a34a"),
        ("7", "Response generated",          "Claude drafts the answer with breakdown by creditor, state, and filing date.",         "#f59e0b"),
        ("8", "Tool result appended",        "The final tool results and reasoning are added to the conversation context.",          "#ef4444"),
        ("9", "Answer returned to user",     "Full explanation delivered — no developer wrote any of this logic.",                   "#6366F1"),
    ]
    rows = ""
    for num, title, desc, color in steps:
        rows += f"""
      <div style="display:flex;gap:0.6rem;margin-bottom:0.4rem;break-inside:avoid">
        <div style="flex-shrink:0;width:22px;height:22px;background:{color};border-radius:50%;color:#fff;
                    font-weight:800;font-size:8pt;display:flex;align-items:center;justify-content:center;margin-top:1px">{num}</div>
        <div style="flex:1">
          <div style="font-weight:700;font-size:8.5pt;color:{color}">{title}</div>
          <div style="font-size:8pt;color:#374151">{desc}</div>
        </div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">UCC Filing Research Agent — 9-Step Interaction</div>
  {rows}
</div>"""


def diag_seven_blocks() -> str:
    blocks = [
        ("The Brain",       "M01–M04", "LLM prompting, context, reasoning, memory",     "#6366F1"),
        ("The Tools",       "M05–M07", "Function calling, APIs, computer use",           "#8b5cf6"),
        ("The Memory",      "M08–M11", "Context windows, embeddings, RAG, vector DBs",   "#7c3aed"),
        ("The Plan",        "M12–M15", "ReAct loop, multi-agent, orchestration",         "#0ea5e9"),
        ("The Guardrails",  "M16–M18", "Safety, evals, red-teaming, human oversight",   "#ef4444"),
        ("The Eyes",        "M19–M20", "Observability, tracing, monitoring",             "#f59e0b"),
        ("The Home",        "M21–M22", "Deployment: Docker, Cloud Run, Lambda",          "#10b981"),
    ]
    cells = ""
    for label, modules, desc, color in blocks:
        cells += f"""
      <div style="border:1px solid {color}33;border-top:3px solid {color};border-radius:0 0 6px 6px;
                  padding:0.55rem 0.65rem;background:#fafbff;break-inside:avoid">
        <div style="font-weight:800;color:{color};font-size:9pt">{label}</div>
        <div style="font-size:7.5pt;color:#6b7280;font-weight:600;margin-bottom:0.2rem">{modules}</div>
        <div style="font-size:7.5pt;color:#374151">{desc}</div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">The 7 Building Blocks of a Production Agent</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;font-size:8.5pt">
    {cells}
  </div>
</div>"""


def diag_lifecycle() -> str:
    stages = [
        ("Design",   "Tracks 1–2", "Define goals, choose tools, write spec",       "#6366F1"),
        ("Build",    "Tracks 2–4", "Implement brain, tools, memory, planner",      "#7c3aed"),
        ("Protect",  "Track 5",    "Add guardrails, evals, safety checks",         "#ef4444"),
        ("Observe",  "Track 6",    "Trace calls, monitor costs, detect drift",     "#f59e0b"),
        ("Deploy",   "Track 7",    "Containerize, ship to cloud, operate",         "#10b981"),
    ]
    nodes = ""
    for i, (stage, tracks, desc, color) in enumerate(stages):
        arrow = ' <span style="color:#9ca3af;font-size:10pt;align-self:center">→</span>' if i < len(stages)-1 else ""
        nodes += f"""
      <div style="flex:1;text-align:center;padding:0.4rem 0.2rem">
        <div style="width:44px;height:44px;border-radius:50%;background:{color};color:#fff;
                    font-weight:800;font-size:8.5pt;display:flex;align-items:center;
                    justify-content:center;margin:0 auto 0.3rem;line-height:1.2">{stage}</div>
        <div style="font-size:7.5pt;color:{color};font-weight:700">{tracks}</div>
        <div style="font-size:7pt;color:#6b7280;line-height:1.3;margin-top:0.15rem">{desc}</div>
      </div>{arrow}"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">The 5 Stages of the Agent Lifecycle</div>
  <div style="display:flex;align-items:flex-start;gap:0.2rem;justify-content:space-between">
    {nodes}
  </div>
</div>"""


def diag_course_agent() -> str:
    return """
<div class="static-diagram">
  <div class="diag-title">The Agent That Built This Course</div>
  <div style="display:grid;grid-template-columns:auto 1fr auto;gap:0.75rem;align-items:start;font-size:8.5pt">

    <div style="text-align:center">
      <div style="background:#6366F1;color:#fff;border-radius:8px;padding:0.5rem 0.7rem;font-weight:700;min-width:70px">Course<br>Author</div>
      <div style="font-size:7.5pt;color:#6b7280;margin-top:0.2rem">types /generate-module M09</div>
    </div>

    <div style="display:flex;flex-direction:column;gap:0.4rem">
      <div style="background:#f0f0ff;border:1px solid #c7d2fe;border-radius:5px;padding:0.35rem 0.6rem;font-size:8pt">
        <strong style="color:#4338ca">CLAUDE.md</strong> — project rules + standards
      </div>
      <div style="background:#f0f0ff;border:1px solid #c7d2fe;border-radius:5px;padding:0.35rem 0.6rem;font-size:8pt">
        <strong style="color:#4338ca">Slash Commands</strong> — /generate, /review, /fix
      </div>
      <div style="background:#f0f0ff;border:1px solid #c7d2fe;border-radius:5px;padding:0.35rem 0.6rem;font-size:8pt">
        <strong style="color:#4338ca">Prompt Files</strong> — design specs, depth rules
      </div>
      <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:5px;padding:0.35rem 0.6rem;font-size:8pt">
        <strong style="color:#b45309">ReAct Loop:</strong> Think → Read specs → Generate HTML → Check quality → Edit → Repeat
      </div>
    </div>

    <div style="text-align:center">
      <div style="background:#10b981;color:#fff;border-radius:8px;padding:0.5rem 0.7rem;font-weight:700;min-width:70px">Output<br>HTML</div>
      <div style="font-size:7.5pt;color:#6b7280;margin-top:0.2rem">self-contained module file</div>
    </div>

  </div>
</div>"""


def diag_module_build_steps() -> str:
    steps = [
        ("1", "Human types",             "/generate-module M09  [Command]",               "#6366F1"),
        ("2", "Agent reads",             "8 specification files (prompts/, CLAUDE.md)",    "#7c3aed"),
        ("3", "Agent generates",         "Complete HTML — animations, code blocks, quizzes [LLM Brain]", "#8b5cf6"),
        ("4", "Agent writes",            "File to disk (100–200 KB)  [Write tool]",        "#0ea5e9"),
        ("5", "Agent runs",              "16-point quality checklist  [Grep + Bash]",      "#10b981"),
        ("6", "Human reviews",           "Previews in browser, requests changes  [HITL]",  "#f59e0b"),
        ("7", "Agent fixes",             "Addresses feedback, re-checks, re-writes",       "#ef4444"),
    ]
    rows = ""
    for num, title, desc, color in steps:
        rows += f"""
      <div style="display:flex;gap:0.55rem;margin-bottom:0.4rem;break-inside:avoid">
        <div style="flex-shrink:0;width:20px;height:20px;background:{color};border-radius:50%;color:#fff;
                    font-weight:800;font-size:7.5pt;display:flex;align-items:center;justify-content:center;margin-top:2px">{num}</div>
        <div>
          <span style="font-weight:700;color:{color};font-size:8.5pt">{title}: </span>
          <span style="font-size:8.5pt;color:#374151">{desc}</span>
        </div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">How One Module Gets Built — 7 Steps</div>
  {rows}
</div>"""


def diag_roadmap() -> str:
    tracks = [
        ("Track 1: Foundations",           "#6366F1", ["M01", "M02", "M03", "M04"]),
        ("Track 2: Tool Use",              "#7c3aed", ["M05", "M06", "M07"]),
        ("Track 3: Memory & Context",      "#8b5cf6", ["M08", "M09", "M10", "M11"]),
        ("Track 4: Agent Architectures",   "#0ea5e9", ["M12", "M13", "M14", "M15", "M15B"]),
        ("Track 5: Guardrails & Safety",   "#ef4444", ["M16", "M17", "M18"]),
        ("Track 6: Observability",         "#f59e0b", ["M19", "M20"]),
        ("Track 7: Production",            "#10b981", ["M21", "M22", "M22B"]),
        ("Track 8: Capstones",             "#16a34a", ["M23", "M24"]),
        ("Track 9: Certification",         "#64748b", ["M25", "M26", "M27"]),
    ]
    rows = ""
    for name, color, modules in tracks:
        mods_html = " ".join(
            f'<span style="background:{color}22;border:1px solid {color}66;color:{color};border-radius:4px;padding:0.1rem 0.35rem;font-size:7.5pt;font-weight:700;white-space:nowrap">{m}</span>'
            for m in modules
        )
        rows += f"""
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0;border-bottom:1px solid #f0f0f0">
        <div style="min-width:155px;font-size:8pt;font-weight:700;color:{color}">{name}</div>
        <div style="display:flex;flex-wrap:wrap;gap:0.25rem">{mods_html}</div>
      </div>"""
    return f"""
<div class="static-diagram">
  <div class="diag-title">Course Roadmap — 9 Tracks, 28 Modules</div>
  {rows}
</div>"""


# ── Transformation pipeline ───────────────────────────────────────────────────

def replace_animations(soup: BeautifulSoup) -> None:
    containers = soup.find_all(class_="animation-container")
    for c in containers:
        text = c.get_text(" ", strip=True)

        if "Seven Eras" in text or "Each Era Adds" in text:
            html = diag_seven_eras()
        elif "Three Pipelines" in text or "APPROACH 1: SCRIPT" in text:
            html = diag_three_pipelines()
        elif "Same Infrastructure, Different Brain" in text:
            html = diag_architecture_comparison()
        elif "Intelligence Layer" in text or "LAYER 1" in text:
            html = diag_intelligence_layer()
        elif "Three Levels Side by Side" in text or "LEVEL 1: CALL" in text:
            html = diag_three_levels()
        elif "Chatbot vs Agent" in text or "Chatbot (one turn)" in text:
            html = diag_chatbot_vs_agent()
        elif "Script Approach vs Agent Approach" in text or "SCRIPT APPROACH" in text:
            html = diag_script_vs_agent()
        elif "9-Step" in text or "Behind the Scenes" in text or "lien exposure for Acme" in text:
            html = diag_nine_steps()
        elif "7 Building Blocks" in text or "The Brain" in text:
            html = diag_seven_blocks()
        elif "5 Stages" in text or "Agent Lifecycle" in text:
            html = diag_lifecycle()
        elif "Agent That Built This Course" in text or "Course Author" in text:
            html = diag_course_agent()
        elif "How One Module Gets Built" in text:
            html = diag_module_build_steps()
        elif "Course Roadmap" in text or "9 Tracks" in text:
            html = diag_roadmap()
        else:
            # Generic fallback: keep content in a styled box
            title_el = c.find(class_="animation-title")
            title = title_el.get_text(strip=True) if title_el else "Diagram"
            html = f'<div class="static-diagram"><div class="diag-title">{title}</div>{c.decode_contents()}</div>'

        c.replace_with(BeautifulSoup(html, "html.parser"))


def fix_quiz(soup: BeautifulSoup) -> None:
    for q in soup.find_all(class_="quiz-question"):
        for opt in q.find_all(class_="quiz-option"):
            opt["style"] = opt.get("style", "") + ";pointer-events:none;"


def strip_chrome(soup: BeautifulSoup) -> None:
    for sel in [".top-progress", ".course-header", ".sidebar-nav",
                ".animation-controls", ".anim-btn", ".copy-btn",
                ".next-module-nav", ".module-nav", ".code-tabs"]:
        for el in soup.select(sel):
            el.decompose()

    pc = soup.find(class_="page-container")
    if pc:
        pc["style"] = "display:block;max-width:100%;padding:0;margin:0"

    for tt in soup.find_all(class_="term-tooltip"):
        tc = tt.find(class_="tooltip-content")
        if tc: tc.decompose()


def inject_print_css(soup: BeautifulSoup) -> None:
    head = soup.find("head")
    if head:
        head.append(BeautifulSoup(PRINT_CSS, "html.parser"))


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

    print("Fixing quiz…")
    fix_quiz(soup)

    print("Injecting print CSS…")
    inject_print_css(soup)

    html = str(soup)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="m00-pdf-") as tmp:
        tmp_html = Path(tmp) / "m00-print.html"
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
