"""Build a clean, readable interview guide PDF from output/study-guide.html.

Single-column layout with generous spacing. Each module is a self-contained
card: module ID chip, title, Core Idea (highlighted), Key Pseudocode, and
the myth-vs-truth Remember box. Modules flow naturally — no forced page
breaks per module, so content breathes without excessive whitespace.

Source  : output/study-guide.html
Output  : output/pdf/interview-guide.pdf
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "output" / "study-guide.html"
OUT  = ROOT / "output" / "pdf" / "interview-guide.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

TRACK_COLORS = {
    "t0": "#6366F1", "t1": "#6366F1", "t2": "#10B981",
    "t3": "#B45309", "t4": "#7c3aed", "t5": "#be123c",
    "t6": "#2563eb", "t7": "#0f766e", "t8": "#be185d",
    "t9": "#8a6a1a", "t10": "#6366F1",
}

# ---------------------------------------------------------------------------

def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("No Chrome or Edge installation found.")


def extract_modules(src: Path) -> list[dict]:
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")
    modules: list[dict] = []

    for section in soup.select("section.track"):
        track_id    = section.get("data-track", "t0")
        color       = TRACK_COLORS.get(track_id, "#6366F1")
        head_el     = section.select_one(".track-head")
        track_label = head_el.get_text(strip=True) if head_el else ""

        for details in section.select("details.module"):
            mid_el  = details.select_one("summary .mid")
            ttl_el  = details.select_one("summary .ttl")
            mid     = mid_el.get_text(strip=True) if mid_el else ""
            title   = ttl_el.get_text(strip=True) if ttl_el else ""
            body    = details.select_one(".body")

            core_html  = ""
            code_inner = ""
            myth       = ""
            truth      = ""

            if body:
                core_el = body.select_one(".core")
                if core_el:
                    # preserve any inline <em class="tag"> styling
                    for em in core_el.find_all("em", class_="tag"):
                        em["style"] = "color:#8a6a1a;font-style:normal;font-weight:600"
                    core_html = core_el.decode_contents()

                code_el = body.select_one("pre.code")
                if code_el:
                    code_inner = code_el.decode_contents()

                misc_el = body.select_one(".misc")
                if misc_el:
                    for row in misc_el.select(".row"):
                        x_span = row.select_one(".x")
                        v_span = row.select_one(".v")
                        if x_span:
                            em = row.select_one("em")
                            myth = em.get_text(strip=True) if em else ""
                        elif v_span:
                            v_span.extract()
                            truth = row.get_text(separator=" ", strip=True)

            modules.append({
                "track_id":    track_id,
                "track_label": track_label,
                "color":       color,
                "mid":         mid,
                "title":       title,
                "core":        core_html,
                "code":        code_inner,
                "myth":        myth,
                "truth":       truth,
            })

    return modules


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

PAGE_CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
@page :first { margin-top: 0; }

*, *::before, *::after { box-sizing: border-box; }

html, body {
  margin: 0; padding: 0;
  background: #fff; color: #1a1f2e;
  font-family: 'Source Sans 3', system-ui, sans-serif;
  font-size: 10.5pt; line-height: 1.58;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}

h1, h2, h3 { font-family: 'Bricolage Grotesque', sans-serif; color: #0A1628; }
p { margin: 0 0 0.4rem; }
strong { font-weight: 700; }
em { font-style: italic; }

/* ── Cover ─────────────────────────────────────────────── */
.cover {
  page-break-after: always;
  min-height: 100vh;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center; padding: 0 24mm;
  background:
    radial-gradient(ellipse at 30% 25%, rgba(99,102,241,.06) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 75%, rgba(212,168,67,.08) 0%, transparent 60%);
}
.cover-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt; letter-spacing: 0.24em; text-transform: uppercase;
  color: #b8860b; margin-bottom: 1.2rem;
}
.cover h1 {
  font-size: 30pt; font-weight: 800; color: #0A1628;
  line-height: 1.12; margin: 0 0 0.6rem;
}
.cover-sub {
  font-size: 13pt; color: #4a5568;
  max-width: 380px; line-height: 1.45; margin-bottom: 2rem;
}
.cover-divider {
  width: 48px; height: 3px; background: #d4a843;
  border-radius: 2px; margin: 0 auto 2rem;
}
.cover-topics {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 0.4rem 2rem; text-align: left;
  font-size: 9.5pt; color: #4a5568;
  margin-bottom: 2rem;
}
.cover-topics span::before { content: "▸ "; color: #b8860b; }
.cover-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt; color: #718096;
}

/* ── Track divider ──────────────────────────────────────── */
.track-section { margin-top: 0.5rem; }
.track-label {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 8pt; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--tc);
  padding: 0.45rem 0;
  border-bottom: 2px solid var(--tc);
  margin-bottom: 1.25rem;
  page-break-after: avoid;
}

/* ── Module card ────────────────────────────────────────── */
.mod {
  border: 1px solid #e2e8f0;
  border-left: 4px solid var(--tc);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.3rem 1rem 1.1rem;
  margin-bottom: 1.5rem;
  break-inside: avoid;
  page-break-inside: avoid;
}

.mod-header {
  display: flex; align-items: center;
  gap: 0.75rem; margin-bottom: 0.65rem;
  flex-wrap: wrap;
}
.mod-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt; font-weight: 700; letter-spacing: 0.05em;
  color: var(--tc);
  background: rgba(0,0,0,0.04);
  padding: 0.18rem 0.6rem; border-radius: 4px;
  white-space: nowrap;
}
.mod-title {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 14pt; font-weight: 800; color: #0A1628;
  line-height: 1.18; flex: 1;
}
.mod-track-chip {
  font-size: 7pt; font-weight: 600; color: #718096;
  background: #f5f7fa; padding: 0.18rem 0.55rem;
  border-radius: 3px; white-space: nowrap;
}

/* Section sub-labels */
.section-lbl {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 7.5pt; font-weight: 700;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: #718096; margin: 0.85rem 0 0.35rem;
}

/* Core Idea */
.core-idea {
  background: rgba(212,168,67,0.09);
  border-left: 3px solid #d4a843;
  border-radius: 0 6px 6px 0;
  padding: 0.65rem 1rem;
  font-size: 11pt; font-style: italic;
  color: #1a1f2e; line-height: 1.45;
}

/* Pseudocode */
pre.code {
  background: rgba(99,102,241,0.07);
  border-left: 3px solid #6366F1;
  border-radius: 0 6px 6px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt; line-height: 1.58;
  padding: 0.8rem 1rem;
  white-space: pre-wrap; word-break: break-word;
  color: #1a1f2e; overflow: visible;
  margin: 0;
}

/* Remember */
.remember {
  background: rgba(244,63,94,0.04);
  border: 1px solid rgba(244,63,94,0.18);
  border-radius: 6px;
  padding: 0.65rem 1rem;
}
.myth-line {
  font-size: 9.5pt; color: #be123c;
  margin-bottom: 0.4rem; line-height: 1.4;
}
.myth-line .mk { font-weight: 800; margin-right: 0.25rem; }
.truth-line {
  font-size: 9.5pt; color: #15803d;
  line-height: 1.45;
}
.truth-line .mk { font-weight: 800; margin-right: 0.25rem; }
"""

COVER_HTML = """
<section class="cover">
  <div class="cover-eyebrow">Interview Study Guide</div>
  <h1>Building AI Agents<br>with Claude</h1>
  <p class="cover-sub">From Hello World to Autonomous Production Systems</p>
  <div class="cover-divider"></div>
  <div class="cover-topics">
    <span>LLM mental model &amp; tokens</span>
    <span>Structured output &amp; tool use</span>
    <span>MCP &amp; multi-tool orchestration</span>
    <span>Conversation memory &amp; RAG</span>
    <span>ReAct loop &amp; planning</span>
    <span>Multi-agent architecture</span>
    <span>Input &amp; output guardrails</span>
    <span>Evaluation &amp; tracing</span>
    <span>API design &amp; cost tuning</span>
    <span>Deployment &amp; the agent frontier</span>
  </div>
  <div class="cover-meta">__MODULE_COUNT__ modules &nbsp;·&nbsp; core concepts only &nbsp;·&nbsp; 2026</div>
</section>
"""


def escape_html(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_modules(modules: list[dict]) -> str:
    parts: list[str] = []
    current_track = None

    for mod in modules:
        # Track divider
        if mod["track_id"] != current_track:
            if current_track is not None:
                parts.append("</section>")
            parts.append(
                f'<section class="track-section" style="--tc:{mod["color"]}">'
                f'<div class="track-label">{escape_html(mod["track_label"])}</div>'
            )
            current_track = mod["track_id"]

        # Module card
        myth_html  = escape_html(mod["myth"])
        truth_html = escape_html(mod["truth"])

        parts.append(f"""
<div class="mod" style="--tc:{mod['color']}">
  <div class="mod-header">
    <span class="mod-id">{escape_html(mod['mid'])}</span>
    <span class="mod-title">{escape_html(mod['title'])}</span>
    <span class="mod-track-chip">{escape_html(mod['track_label'])}</span>
  </div>

  <div class="section-lbl">Core Idea</div>
  <div class="core-idea">{mod['core']}</div>

  <div class="section-lbl">Key Pseudocode</div>
  <pre class="code">{mod['code']}</pre>

  <div class="section-lbl">Remember</div>
  <div class="remember">
    <div class="myth-line"><span class="mk">✗</span>{myth_html}</div>
    <div class="truth-line"><span class="mk">✓</span>{truth_html}</div>
  </div>
</div>""")

    if current_track is not None:
        parts.append("</section>")

    return "\n".join(parts)


def build_html(modules: list[dict]) -> str:
    cover   = COVER_HTML.replace("__MODULE_COUNT__", str(len(modules)))
    content = render_modules(modules)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Interview Guide — Building AI Agents with Claude</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
{PAGE_CSS}
</style>
</head>
<body>
{cover}
{content}
</body>
</html>"""


# ---------------------------------------------------------------------------

def main() -> None:
    if not SRC.exists():
        sys.exit(f"Source not found: {SRC}")

    browser = find_browser()
    print(f"Source : {SRC}")
    print(f"Browser: {browser}")

    print("Extracting modules …")
    modules = extract_modules(SRC)
    print(f"  {len(modules)} modules found")

    html_doc = build_html(modules)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="interview-guide-") as tmp:
        tmp_html = Path(tmp) / "interview-guide.html"
        tmp_pdf  = Path(tmp) / "out.pdf"

        tmp_html.write_text(html_doc, encoding="utf-8")
        print("Rendering PDF …")

        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--virtual-time-budget=20000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )

        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        candidates = [OUT] + [OUT.with_name(f"{OUT.stem}-new{i}.pdf") for i in range(1, 10)]
        dest = None
        for cand in candidates:
            try:
                shutil.move(str(tmp_pdf), str(cand))
                dest = cand
                break
            except PermissionError:
                continue

        if dest is None:
            sys.exit("All output paths locked — close any open PDF viewers and retry.")

    size_kb = dest.stat().st_size // 1024
    try:
        import pypdf
        pages = len(pypdf.PdfReader(str(dest)).pages)
        print(f"Wrote  : {dest}  ({size_kb} KB, {pages} pages)")
    except Exception:
        print(f"Wrote  : {dest}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
