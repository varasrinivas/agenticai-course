"""Build a print-friendly PDF from the CC condensed module HTMLs.

Each output/cc/condensed/CC{N}-condensed.html is a content fragment with the
structure:

  <section class="module-condensed" id="CC0">
    <header class="cm-header">
      <span class="cm-track">CC0 — Foundations</span>
      <h2 class="cm-title">CC0: Getting Started with Claude Code</h2>
      <p class="cm-tagline">...</p>
    </header>
    <h3>The Big Idea</h3> <p>...</p>
    <h3>Analogy</h3> <p>...</p>
    <h3>How It Works</h3> <ol>...</ol>
    <h3>Pseudocode</h3> <pre><code>...</code></pre>
    <h3>Common Misconceptions</h3> <ul>...</ul>
    <h3>Key Takeaway</h3> <div class="cm-takeaway">...</div>
    <h3>Quick Quiz</h3> <div class="cm-quiz">...</div>...
  </section>

We strip the .cm-quiz blocks plus the Quick Quiz heading, wrap each fragment
in a light-themed page (cover + TOC + per-module section), and render via
headless Chrome. Outline bookmarks added with pypdf.

Output: output/cc/CC-study-guide-condensed.pdf
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, Tag

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

ROOT = Path(__file__).resolve().parent.parent
CC_DIR = ROOT / "output" / "cc" / "condensed"
OUT_PDF = ROOT / "output" / "cc" / "CC-study-guide-condensed.pdf"

# Track-name → CSS class. Tracks come from the cm-track span ("CC0 — Foundations").
TRACK_CLASSES = {
    "foundations":  "track-foundations",
    "configuration": "track-config",
    "safety":       "track-safety",
    "extension":    "track-extension",
    "delegation":   "track-delegation",
    "automation":   "track-automation",
    "integration":  "track-integration",
    "capabilities": "track-capabilities",
    "quality":      "track-quality",
    "knowledge":    "track-knowledge",
    "patterns":     "track-patterns",
    "production":   "track-production",
}

_QUIZ_HEADING_RE = re.compile(r"^\s*quick\s*quiz\s*$", re.I)


def find_browser() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    sys.exit("No Chrome or Edge install found.")


def order_key(name: str) -> int:
    m = re.match(r"CC(\d+)", name)
    return int(m.group(1)) if m else 9999


def text_of(node) -> str:
    if node is None:
        return ""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def split_track(raw: str) -> tuple[str, str]:
    """'CC0 — Foundations' -> ('CC0', 'Foundations')."""
    if not raw:
        return ("", "")
    parts = re.split(r"\s*[—–-]\s*", raw, maxsplit=1)
    if len(parts) == 2:
        return (parts[0].strip(), parts[1].strip())
    return (raw.strip(), "")


def track_class(track_name: str) -> str:
    return TRACK_CLASSES.get(track_name.lower(), "track-foundations")


def strip_quizzes(section: Tag) -> None:
    """Remove .cm-quiz blocks and the preceding 'Quick Quiz' heading."""
    for quiz in section.select(".cm-quiz"):
        quiz.decompose()
    for h3 in section.find_all("h3"):
        if _QUIZ_HEADING_RE.match(h3.get_text(strip=True)):
            h3.decompose()


def extract_module(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    section = soup.select_one("section.module-condensed")
    if section is None:
        # fragment without wrapper — wrap everything in a synthetic section
        section = soup.new_tag("section", attrs={"class": "module-condensed"})
        for child in list(soup.children):
            section.append(child.extract())

    strip_quizzes(section)

    header = section.select_one(".cm-header")
    track_raw = text_of(header.select_one(".cm-track")) if header else ""
    module_id, track_name = split_track(track_raw)
    title = text_of(header.select_one(".cm-title")) if header else "Module"
    tagline = text_of(header.select_one(".cm-tagline")) if header else ""

    # Strip the original header from the body — we re-render it
    if header:
        header.decompose()

    body_html = "".join(str(c) for c in section.children).strip()

    return {
        "module_id": module_id or html_path.stem.replace("-condensed", "").upper(),
        "track": track_name,
        "title": title,
        "tagline": tagline,
        "body": body_html,
        "klass": track_class(track_name),
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Claude Code Mastery — Study Guide (Condensed)</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  @page { size: A4; margin: 14mm 14mm 14mm 14mm; }
  * { box-sizing: border-box; }

  html, body {
    margin: 0; padding: 0;
    background: #fff; color: #1a1f2e;
    font-family: 'Source Sans 3', -apple-system, sans-serif;
    font-size: 10.5pt; line-height: 1.5;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', sans-serif; color: #0A1628; }
  p { margin: 0 0 0.55rem; }
  ul, ol { margin: 0.4rem 0 0.7rem 1.25rem; padding: 0; }
  li { margin-bottom: 0.3rem; }
  strong { font-weight: 700; }
  a { color: #2563eb; text-decoration: none; }
  code { font-family: 'JetBrains Mono', monospace; font-size: 9pt; background: rgba(99,102,241,0.08); padding: 0.05rem 0.3rem; border-radius: 3px; }

  /* === Cover === */
  .cover { page-break-after: always; text-align: center; padding-top: 26vh; }
  .cover .eyebrow {
    font-size: 11pt; letter-spacing: 0.2em; text-transform: uppercase;
    color: #8a6a1a; font-weight: 700; margin-bottom: 1.5rem;
  }
  .cover h1 {
    font-size: 30pt; font-weight: 800; margin: 0 0 0.75rem;
    color: #0A1628; letter-spacing: -0.01em;
  }
  .cover .sub {
    font-size: 13pt; color: #4a5568; max-width: 520px;
    margin: 0 auto; line-height: 1.5;
  }
  .cover .meta { margin-top: 3rem; font-size: 10pt; color: #718096; }

  /* === TOC === */
  .toc { page-break-before: always; page-break-after: always; padding-top: 0.5rem; }
  .toc h1 {
    font-size: 24pt; font-weight: 800;
    margin: 0 0 0.4rem; color: #0A1628; letter-spacing: -0.01em;
  }
  .toc .toc-hint {
    font-size: 9pt; color: #718096; font-style: italic; margin: 0 0 1rem;
  }
  .toc-list { list-style: none; margin: 0; padding: 0; }
  .toc-item { border-bottom: 1px dotted #cbd5e0; page-break-inside: avoid; }
  .toc-item a {
    display: flex; align-items: baseline; gap: 0.9rem;
    padding: 0.5rem 0.25rem; color: #1a1f2e; text-decoration: none;
  }
  .toc-item a:hover { background: #f7fafc; }
  .toc-num {
    flex: 0 0 auto; width: 3.4em;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 9.5pt; font-weight: 700;
    color: var(--track-color); letter-spacing: 0.04em; white-space: nowrap;
  }
  .toc-title {
    flex: 1 1 auto;
    font-size: 10.5pt; font-weight: 600; color: #0A1628;
    line-height: 1.3; min-width: 0;
  }
  .toc-track {
    flex: 0 0 auto;
    font-size: 8.5pt; color: #718096; font-weight: 600;
    text-align: right; white-space: nowrap;
  }

  /* === Module === */
  .module {
    page-break-before: always;
    border-top: 4px solid var(--track-color);
    padding-top: 0.55rem;
  }
  .module-head {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 1rem; padding-bottom: 0.4rem;
    border-bottom: 1px solid #e2e8f0; margin-bottom: 0.75rem;
  }
  .module-head .num {
    font-family: 'Bricolage Grotesque', sans-serif; font-size: 9.5pt;
    font-weight: 700; color: var(--track-color);
    letter-spacing: 0.06em; text-transform: uppercase; white-space: nowrap;
  }
  .module-head .track {
    font-size: 9pt; color: #718096; font-weight: 600; text-align: right;
  }
  .module h1.module-title {
    font-size: 20pt; font-weight: 800; line-height: 1.2;
    margin: 0 0 0.25rem; color: #0A1628;
  }
  .module .module-sub {
    font-size: 10.5pt; color: #4a5568; font-style: italic;
    margin: 0 0 0.8rem; line-height: 1.4;
  }

  /* === Sub-sections (h3 like "The Big Idea", "Analogy", etc.) === */
  .module h3 {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 11.5pt; font-weight: 700;
    color: var(--track-color);
    margin: 0.85rem 0 0.35rem;
    text-transform: uppercase; letter-spacing: 0.06em;
    border-left: 3px solid var(--track-color);
    padding-left: 0.5rem;
    page-break-after: avoid;
  }

  /* === Pseudocode (pre/code) === */
  .module pre {
    background: rgba(99, 102, 241, 0.06);
    border-left: 3px solid var(--track-color);
    border-radius: 0 4px 4px 0;
    padding: 0.6rem 0.85rem; margin: 0.45rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.75pt; line-height: 1.55;
    white-space: pre-wrap; word-break: break-word;
    color: #1a1f2e; overflow: visible;
    page-break-inside: avoid;
  }
  .module pre code {
    background: transparent; padding: 0; font-size: inherit;
  }

  /* === Takeaway === */
  .cm-takeaway {
    background: rgba(212, 168, 67, 0.1);
    border-left: 3px solid #b8860b;
    border-radius: 0 4px 4px 0;
    padding: 0.6rem 0.85rem; margin: 0.5rem 0;
    font-size: 10pt; color: #1a1f2e;
    page-break-inside: avoid;
  }

  /* === Lists === */
  .module ul li, .module ol li { margin-bottom: 0.35rem; line-height: 1.45; }
  .module ul li strong { color: #0A1628; }

  /* Drop any stray quiz remnants if the strip pass missed them */
  .cm-quiz, .cm-answer { display: none !important; }

  /* === Track-color tinting ===
     CC0/1/2 Foundations  → indigo
     CC3   Configuration → teal
     CC4   Safety        → crimson
     CC5   Extension     → violet
     CC6   Delegation    → blue
     CC7   Automation    → amber
     CC8/9 Integration   → emerald
     CC10  Capabilities  → pink
     CC11  Quality       → green
     CC12  Knowledge     → sky
     CC13  Patterns      → purple
     CC14/15 Production  → gold
  */
  .track-foundations  { --track-color: #6366F1; }
  .track-config       { --track-color: #14B8A6; }
  .track-safety       { --track-color: #be123c; }
  .track-extension    { --track-color: #7c3aed; }
  .track-delegation   { --track-color: #2563eb; }
  .track-automation   { --track-color: #B45309; }
  .track-integration  { --track-color: #047857; }
  .track-capabilities { --track-color: #be185d; }
  .track-quality      { --track-color: #10B981; }
  .track-knowledge    { --track-color: #0284c7; }
  .track-patterns     { --track-color: #8B5CF6; }
  .track-production   { --track-color: #b8860b; }
  /* Default for items that don't have a track class (e.g. the TOC list itself) */
  .toc { --track-color: #6366F1; }
</style>
</head>
<body>
<section class="cover">
  <div class="eyebrow">Print Edition</div>
  <h1>Claude Code Mastery</h1>
  <div class="sub">A condensed study guide covering every Claude Code module — the mental model, mechanics, pseudocode, misconceptions, and takeaway from CC0 through CC15.</div>
  <div class="meta">__MODULE_COUNT__ modules · From Getting Started to the Agent SDK</div>
</section>
__MODULES__
</body>
</html>
"""


def section_anchor(mod: dict) -> str:
    return f"mod-{mod['module_id'].lower()}"


def render_module(mod: dict) -> str:
    anchor = section_anchor(mod)
    head = (
        f'<header class="module-head">'
        f'<span class="num">{mod["module_id"]}</span>'
        f'<span class="track">{mod["track"]}</span>'
        f'</header>'
        f'<h1 class="module-title">{mod["title"]}</h1>'
    )
    if mod["tagline"]:
        head += f'<p class="module-sub">{mod["tagline"]}</p>'
    return f'<section class="module {mod["klass"]}" id="{anchor}">{head}{mod["body"]}</section>'


def render_toc(modules: list[dict]) -> str:
    rows = []
    for mod in modules:
        anchor = section_anchor(mod)
        rows.append(
            f'<li class="toc-item {mod["klass"]}">'
            f'<a href="#{anchor}">'
            f'<span class="toc-num">{mod["module_id"]}</span>'
            f'<span class="toc-title">{mod["title"]}</span>'
            f'<span class="toc-track">{mod["track"]}</span>'
            f'</a></li>'
        )
    return (
        '<section class="toc">'
        '<h1>Table of Contents</h1>'
        '<p class="toc-hint">Click any entry to jump to that module.</p>'
        f'<ol class="toc-list">{"".join(rows)}</ol>'
        '</section>'
    )


def add_pdf_bookmarks(pdf_path: Path, modules: list[dict]) -> int:
    """Insert sidebar bookmarks for cover, TOC, and each module."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return 0

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        print(f"  (skipping bookmarks: cannot open PDF — {exc})")
        return 0

    page_count = len(reader.pages)
    page_texts: list[str] = []
    for p in reader.pages:
        try:
            page_texts.append((p.extract_text() or "").lower())
        except Exception:
            page_texts.append("")

    matches: list[tuple[int, dict]] = []
    used_pages: set[int] = set()
    for mod in modules:
        title_needle = mod["title"].strip().lower()[:40]
        id_needle = mod["module_id"].strip().lower()
        found = None
        for idx, text in enumerate(page_texts):
            if idx in used_pages:
                continue
            if title_needle and title_needle in text:
                found = idx
                break
            if id_needle and id_needle in text:
                found = idx
                break
        if found is not None:
            used_pages.add(found)
            matches.append((found, mod))

    if not matches:
        return page_count

    writer = PdfWriter(clone_from=reader)
    writer.add_outline_item("Cover", 0)
    if page_count > 1:
        writer.add_outline_item("Table of Contents", 1)
    for page_idx, mod in matches:
        label = f"{mod['module_id']} — {mod['title']}"
        try:
            writer.add_outline_item(label, page_idx)
        except Exception:
            continue

    try:
        with open(pdf_path, "wb") as fh:
            writer.write(fh)
    except PermissionError:
        print(f"  (cannot rewrite {pdf_path.name} — close any open viewer to add bookmarks)")
    return page_count


def main() -> None:
    browser = find_browser()
    files = sorted(
        (f for f in CC_DIR.glob("CC*-condensed.html") if f.name != "combined.html"),
        key=lambda p: order_key(p.name),
    )
    if not files:
        sys.exit(f"No CC condensed HTML files found in {CC_DIR}")

    print(f"Parsing {len(files)} CC modules ...", flush=True)
    modules = []
    for f in files:
        modules.append(extract_module(f))
        print(f"  · {f.name}", flush=True)

    toc = render_toc(modules)
    body = "\n".join([toc, *[render_module(m) for m in modules]])
    html_doc = HTML_TEMPLATE.replace("__MODULES__", body).replace(
        "__MODULE_COUNT__", str(len(modules))
    )

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cc-pdf-", dir=OUT_PDF.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / "ccbook.html"
        tmp_html.write_text(html_doc, encoding="utf-8")
        tmp_pdf = tmp_dir / "out.pdf"
        print("Rendering PDF ...", flush=True)
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--virtual-time-budget=12000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        candidates = [OUT_PDF] + [
            OUT_PDF.with_name(f"{OUT_PDF.stem}.new{i if i else ''}.pdf")
            for i in range(0, 10)
        ]
        final_path = None
        last_err = None
        for cand in candidates:
            try:
                tmp_pdf.replace(cand)
                final_path = cand
                if cand != OUT_PDF:
                    print(f"NOTE: {OUT_PDF.name} is locked; wrote to {cand.name} instead.")
                break
            except PermissionError as e:
                last_err = e
                continue
        if final_path is None:
            sys.exit(f"All output paths are locked. Close any open PDF viewers. Last error: {last_err}")

    pages = add_pdf_bookmarks(final_path, modules)
    size_kb = final_path.stat().st_size / 1024
    print(f"Wrote {final_path} ({size_kb:.0f} KB, {pages} pages, {len(modules)} modules)")


if __name__ == "__main__":
    main()
