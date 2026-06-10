"""Build an interview-style PDF from all mobile HTML module files.

For each mobile module file in output/mobile/, extracts:
  - Module ID + title   (from <title>)
  - Track name + color  (from body track-label elements)
  - Core Idea           (first .analogy-box inner HTML)
  - Key Pseudocode      (first .pseudocode block)
  - Remember            (first .misconception .wrong/.right)

Output: output/mobile/study-guide-interview.pdf
"""
from __future__ import annotations

import html as html_mod
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup

# ── Config ───────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).resolve().parent.parent
MOBILE = ROOT / "output" / "mobile"
OUT    = ROOT / "output" / "mobile" / "study-guide-interview.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

TRACK_COLORS: dict[str, str] = {
    "0": "#6366F1", "1": "#6366F1", "2": "#10B981",
    "3": "#B45309", "4": "#7c3aed", "5": "#be123c",
    "6": "#2563eb", "7": "#0f766e", "8": "#be185d",
    "9": "#8a6a1a",
}
_DEFAULT_COLOR = "#6366F1"

# ── File ordering ─────────────────────────────────────────────────────────────

def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("No Chrome or Edge installation found.")


def _sort_key(p: Path) -> tuple[int, int, str]:
    m = re.match(r"^M(\d+)(B?)", p.stem, re.IGNORECASE)
    if m:
        return int(m.group(1)), (1 if m.group(2).upper() == "B" else 0), p.stem
    return 9999, 0, p.stem


def get_mobile_files() -> list[Path]:
    files = [
        f for f in MOBILE.glob("M*.html")
        if not f.stem.endswith("-v1") and f.stem != "index"
    ]
    files.sort(key=_sort_key)
    return files


# ── Extraction helpers ────────────────────────────────────────────────────────

def _parse_title(raw: str, filename: str) -> tuple[str, str]:
    """Return (mod_id, human_title) from the <title> tag text."""
    t = html_mod.unescape(raw).strip()
    for pat in [
        r"^(M\w+):\s*(.+?)\s*\(Mobile\)",               # M01: Title (Mobile) | ...
        r"^(M\w+)\s*[·•]\s*(.+?)\s*[—–-]\s*Mobile",     # M14 · Title — Mobile
        r"^(M\w+)\s+Mobile:\s*(.+?)(?:\s*\||$)",         # M02 Mobile: Title | ...
        r"^(M\w+)\s*:\s*(.+?)(?:\s*\||$)",               # fallback colon-sep
    ]:
        m = re.match(pat, t)
        if m:
            return m.group(1), html_mod.unescape(m.group(2).strip())
    # Last resort: derive from filename
    stem = Path(filename).stem
    m2 = re.match(r"^(M[\w]+?)-", stem)
    mod_id = m2.group(1).upper() if m2 else "M??"
    title  = re.sub(r"-mobile$", "", stem).replace("-", " ").title()
    return mod_id, title


def _parse_track(soup: BeautifulSoup) -> tuple[str, str, str]:
    """Return (track_num, track_label, hex_color)."""
    for sel in [".top-bar-track", "#track-label", ".track-chip", ".title-badge"]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"Track\s+(\d+)", text)
            if m:
                num   = m.group(1)
                label = re.sub(r"\s*[·•:]\s*", " — ", text, count=1).strip()
                return num, label, TRACK_COLORS.get(num, _DEFAULT_COLOR)
    # Fallback: search body text
    body = soup.get_text(" ", strip=True)
    m = re.search(r"Track\s+(\d+)\s*[·•:—\-]+\s*([A-Za-z &]+)", body)
    if m:
        num, name = m.group(1), m.group(2).strip()
        return num, f"Track {num} — {name}", TRACK_COLORS.get(num, _DEFAULT_COLOR)
    return "1", "Track 1 — Foundations", _DEFAULT_COLOR


def _extract_analogy(soup: BeautifulSoup) -> str:
    """Return inner HTML of the first analogy-box (or takeaway as fallback)."""
    box = soup.select_one(".analogy-box") or soup.select_one(".takeaway")
    if not box:
        return ""
    for lbl in box.select(".analogy-label, .takeaway-label, .box-label"):
        lbl.decompose()
    # Remove inline margin styles that won't look right in print
    for p in box.find_all("p", style=True):
        del p["style"]
    return box.decode_contents().strip()


def _extract_pseudocode(soup: BeautifulSoup) -> str:
    """Return inner HTML of the first pseudocode block (class varies across files)."""
    el = soup.select_one(".pseudocode") or soup.select_one("pre.pseudo")
    return el.decode_contents() if el else ""


def _extract_misconception(soup: BeautifulSoup) -> tuple[str, str]:
    """Return (myth_text, truth_text) from the first .misconception block.

    Handles two layouts:
      Layout A: .wrong / .right children  (most modules)
      Layout B: .misconception-label + <p> (M14, M24 style)
    """
    misc = soup.select_one(".misconception")
    if not misc:
        return "", ""

    # Layout A
    wrong_el = misc.select_one(".wrong, .mc-wrong")
    right_el = misc.select_one(".right, .mc-right")
    if wrong_el or right_el:
        myth  = re.sub(r"^[❌✗×✖]\s*", "", wrong_el.get_text(strip=True) if wrong_el else "").strip('"')
        truth = re.sub(r"^[✅✓✔]\s*", "", right_el.get_text(strip=True) if right_el else "").strip()
        return myth, truth

    # Layout B: .misconception-label is the myth; next <p> is the truth
    label_el = misc.select_one(".misconception-label")
    p_el     = misc.find("p")
    myth  = label_el.get_text(strip=True) if label_el else ""
    truth = p_el.get_text(strip=True)     if p_el     else ""
    # Strip leading "Myth: " prefix if present
    myth = re.sub(r"^Myth:\s*", "", myth).strip()
    return myth, truth


def extract_module(path: Path) -> dict | None:
    try:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    except Exception as e:
        print(f"  WARN: {path.name}: {e}")
        return None
    title_tag = soup.find("title")
    if not title_tag:
        return None
    mod_id, title           = _parse_title(title_tag.get_text(), path.name)
    track_num, track_label, color = _parse_track(soup)
    myth, truth             = _extract_misconception(soup)
    return {
        "mod_id":      mod_id,
        "title":       title,
        "track_num":   track_num,
        "track_label": track_label,
        "color":       color,
        "core":        _extract_analogy(soup),
        "code":        _extract_pseudocode(soup),
        "myth":        myth,
        "truth":       truth,
    }


# ── PDF HTML generation ───────────────────────────────────────────────────────

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
p:last-child { margin-bottom: 0; }
strong { font-weight: 700; }
em { font-style: italic; }

/* Cover */
.cover {
  page-break-after: always; min-height: 100vh;
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
.cover h1 { font-size: 30pt; font-weight: 800; color: #0A1628; line-height: 1.12; margin: 0 0 0.6rem; }
.cover-sub { font-size: 13pt; color: #4a5568; max-width: 380px; line-height: 1.45; margin-bottom: 2rem; }
.cover-divider { width: 48px; height: 3px; background: #d4a843; border-radius: 2px; margin: 0 auto 2rem; }
.cover-topics {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 0.4rem 2rem; text-align: left;
  font-size: 9.5pt; color: #4a5568; margin-bottom: 2rem;
}
.cover-topics span::before { content: "▸ "; color: #b8860b; }
.cover-meta { font-family: 'JetBrains Mono', monospace; font-size: 8pt; color: #718096; }

/* Track divider */
.track-section { margin-top: 0.5rem; }
.track-label {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 8pt; font-weight: 700; letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--tc); padding: 0.45rem 0;
  border-bottom: 2px solid var(--tc); margin-bottom: 1.25rem;
  page-break-after: avoid;
}

/* Module card */
.mod {
  border: 1px solid #e2e8f0; border-left: 4px solid var(--tc);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.3rem 1rem 1.1rem; margin-bottom: 1.5rem;
  break-inside: avoid; page-break-inside: avoid;
}
.mod-header {
  display: flex; align-items: center; gap: 0.75rem;
  margin-bottom: 0.65rem; flex-wrap: wrap;
}
.mod-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt; font-weight: 700; letter-spacing: 0.05em;
  color: var(--tc); background: rgba(0,0,0,0.04);
  padding: 0.18rem 0.6rem; border-radius: 4px; white-space: nowrap;
}
.mod-title {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 14pt; font-weight: 800; color: #0A1628;
  line-height: 1.18; flex: 1;
}
.mod-track-chip {
  font-size: 7pt; font-weight: 600; color: #718096;
  background: #f5f7fa; padding: 0.18rem 0.55rem; border-radius: 3px; white-space: nowrap;
}

/* Section labels */
.section-lbl {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 7.5pt; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
  color: #718096; margin: 0.85rem 0 0.35rem;
}

/* Core Idea — analogy box */
.core-idea {
  background: rgba(212,168,67,0.09); border-left: 3px solid #d4a843;
  border-radius: 0 6px 6px 0; padding: 0.65rem 1rem;
  font-size: 9.5pt; color: #1a1f2e; line-height: 1.5;
}
.core-idea p { margin: 0 0 0.35rem; }
/* BEFORE / PAIN / MAPPING labels */
.analogy-step { color: #b8860b; font-weight: 700; font-style: normal; }

/* Pseudocode */
pre.code {
  background: rgba(99,102,241,0.07); border-left: 3px solid #6366F1;
  border-radius: 0 6px 6px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt; line-height: 1.58;
  padding: 0.8rem 1rem; white-space: pre-wrap; word-break: break-word;
  color: #1a1f2e; overflow: visible; margin: 0;
}
/* Syntax highlight spans from mobile HTML */
.kw, .ps-kw   { color: #c4162a; font-weight: 600; }
.cm, .ps-comment { color: #6b7280; font-style: italic; }
.fn           { color: #6f42c1; }
.str          { color: #032f62; }
.num          { color: #005cc5; }

/* Remember */
.remember {
  background: rgba(244,63,94,0.04); border: 1px solid rgba(244,63,94,0.18);
  border-radius: 6px; padding: 0.65rem 1rem;
}
.myth-line  { font-size: 9.5pt; color: #be123c; margin-bottom: 0.4rem; line-height: 1.4; }
.truth-line { font-size: 9.5pt; color: #15803d; line-height: 1.45; }
.mk { font-weight: 800; margin-right: 0.25rem; }
"""

COVER_HTML = """
<section class="cover">
  <div class="cover-eyebrow">Mobile Module Study Guide</div>
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
    <span>Deployment &amp; cert prep</span>
  </div>
  <div class="cover-meta">__MODULE_COUNT__ modules &nbsp;·&nbsp; extracted from mobile card decks &nbsp;·&nbsp; 2026</div>
</section>
"""


def _esc(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_modules(modules: list[dict]) -> str:
    parts: list[str] = []
    current_track = None

    for mod in modules:
        if mod["track_num"] != current_track:
            if current_track is not None:
                parts.append("</section>")
            parts.append(
                f'<section class="track-section" style="--tc:{mod["color"]}">'
                f'<div class="track-label">{_esc(mod["track_label"])}</div>'
            )
            current_track = mod["track_num"]

        core_content = mod["core"] or "<em>No analogy found in this module.</em>"
        code_content = mod["code"] or "<em>No pseudocode in this module.</em>"
        myth_html    = _esc(mod["myth"])  if mod["myth"]  else "No misconception found."
        truth_html   = _esc(mod["truth"]) if mod["truth"] else ""

        parts.append(f"""
<div class="mod" style="--tc:{mod['color']}">
  <div class="mod-header">
    <span class="mod-id">{_esc(mod['mod_id'])}</span>
    <span class="mod-title">{_esc(mod['title'])}</span>
    <span class="mod-track-chip">{_esc(mod['track_label'])}</span>
  </div>

  <div class="section-lbl">Core Idea — Analogy</div>
  <div class="core-idea">{core_content}</div>

  <div class="section-lbl">Key Pseudocode</div>
  <pre class="code">{code_content}</pre>

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
<title>Mobile Study Guide — Building AI Agents with Claude</title>
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


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    browser = find_browser()
    files   = get_mobile_files()
    print(f"Browser : {browser}")
    print(f"Scanning {len(files)} mobile HTML files …")

    modules: list[dict] = []
    for f in files:
        mod = extract_module(f)
        if mod:
            modules.append(mod)
            code_flag = "code" if mod["code"] else "    "
            myth_flag = "myth" if mod["myth"] else "    "
            print(f"  OK {mod['mod_id']:6s}  [{code_flag}] [{myth_flag}]  {mod['title'][:55]}")
        else:
            print(f"  SKIP {f.name}")

    print(f"\nBuilding PDF for {len(modules)} modules …")
    html_doc = build_html(modules)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mobile-study-guide-") as tmp:
        tmp_html = Path(tmp) / "mobile-study-guide.html"
        tmp_pdf  = Path(tmp) / "out.pdf"

        tmp_html.write_text(html_doc, encoding="utf-8")
        print("Rendering PDF via headless Chrome …")

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
        print(f"\nWrote : {dest}")
        print(f"Size  : {size_kb} KB, {pages} pages")
    except Exception:
        print(f"\nWrote : {dest}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
