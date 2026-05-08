"""Build a full-content PDF from all mobile module HTMLs in cheat-sheet style.

For each module, keeps the original card markup (Big Idea, Analogy, How It
Works, Pseudocode, Misconceptions, Takeaway, Quiz) but renders it inside a
light, print-friendly template that overrides the dark mobile theme.

SVG diagrams are wrapped in a dark mini-viewport so their original colors
(designed for dark backgrounds) stay readable on the printed page. Quiz
answers are revealed by default since this is print, not interactive.

Output: output/mobile/all-mobile-modules.pdf
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
MOBILE_DIR = ROOT / "output" / "mobile"
OUT_PDF = MOBILE_DIR / "all-mobile-modules.pdf"

# Cards to drop entirely (navigation chrome and quizzes — not core content)
SKIP_CARD_CLASSES = {"desktop-link-card", "desktop-link", "quiz-card"}


def find_browser() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    sys.exit("No Chrome or Edge install found.")


def order_key(name: str) -> tuple[int, str]:
    m = re.match(r"M(\d+)([A-Z]?)", name)
    return (int(m.group(1)), m.group(2) or "") if m else (9999, "")


def text_of(node) -> str:
    if node is None:
        return ""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


_QUIZ_HEADINGS = (
    "quick quiz",
    "test your understanding",
    "test yourself",
    "check your understanding",
    "knowledge check",
    "quiz",
)


def is_skippable_card(card: Tag) -> bool:
    classes = set(card.get("class", []))
    if classes & SKIP_CARD_CLASSES:
        return True
    # Desktop-link inner blocks (M00 / M09 navigation card variants)
    if card.find(class_=lambda c: c and ("desktop-btn" in c or "desktop-link" == c)):
        return True
    # Inner quiz markup — both naming conventions:
    #   M01-style: <div class="quiz-item">
    #   M03-style: <div class="quiz-card">  (clashes with the outer-card class name)
    if card.find(class_=lambda c: c and (
        c == "quiz-item" or "quiz-item" in (c if isinstance(c, list) else [c])
    )):
        return True
    if card.find(class_=lambda c: c and (
        c == "quiz-card" or (isinstance(c, list) and "quiz-card" in c)
    )):
        return True
    # M01-style label callout
    label = card.find(class_=lambda c: c and c in ("card-label", "section-label"))
    if label and "quiz" in label.get_text(strip=True).lower():
        return True
    # M03-style: heading text alone signals a quiz card
    h2 = card.find(["h2", "h3"])
    if h2:
        heading = h2.get_text(strip=True).lower()
        if any(phrase in heading for phrase in _QUIZ_HEADINGS):
            return True
    return False


def is_title_card(card: Tag) -> bool:
    classes = set(card.get("class", []))
    return bool(classes & {"title-card", "card-title"})


def get_header(soup: BeautifulSoup) -> dict:
    title_card = soup.select_one(".title-card") or soup.select_one(".card-title")
    track = ""
    module_num = ""
    title = ""
    subtitle = ""
    if title_card:
        track = text_of(title_card.select_one(".track-badge"))
        module_num = text_of(
            title_card.select_one(".module-number, .module-num, .module-label, .card-number")
        )
        h1 = title_card.select_one("h1")
        title = text_of(h1) if h1 else ""
        subtitle = text_of(title_card.select_one(".subtitle"))
    # Fallback: first h1 anywhere
    if not title:
        h1 = soup.find("h1")
        title = text_of(h1) if h1 else "Module"
    return {
        "track": track,
        "module_num": module_num,
        "title": title,
        "subtitle": subtitle,
    }


def reveal_quiz_answers(soup: BeautifulSoup) -> None:
    """Force-reveal quiz answers in print and strip tap hints."""
    for hint in soup.select(".tap-hint, .quiz-reveal-btn"):
        hint.decompose()
    for ans in soup.select(".quiz-answer"):
        ans["data-revealed"] = "1"


def strip_problem_attrs(soup: BeautifulSoup) -> None:
    for el in soup.find_all(True):
        for attr in ("onclick", "ontouchstart", "tabindex", "role", "aria-label"):
            if attr in el.attrs:
                del el.attrs[attr]


def strip_card_labels(soup: BeautifulSoup) -> None:
    """Remove the small uppercase 'BIG IDEA' / 'THE ANALOGY' tags."""
    for label in soup.select(".card-label, .section-label, .analogy-label"):
        label.decompose()


# Colors used by mobile SVGs that vanish on a white page — remap to dark.
_LIGHT_COLOR_PATTERNS = [
    re.compile(r"#E8ECF1", re.I),
    re.compile(r"#FFFFFF\b", re.I),
    re.compile(r"#FFF\b", re.I),
    re.compile(r"\bwhite\b", re.I),
    re.compile(r"rgba?\(\s*255\s*,\s*255\s*,\s*255[^)]*\)", re.I),
    re.compile(r"rgba?\(\s*232\s*,\s*236\s*,\s*241[^)]*\)", re.I),
]
_DARK_REPLACEMENT = "#1a1f2e"


def _recolor_value(value: str) -> str:
    out = value
    for pat in _LIGHT_COLOR_PATTERNS:
        out = pat.sub(_DARK_REPLACEMENT, out)
    return out


def recolor_svgs_for_print(soup: BeautifulSoup) -> None:
    """Replace light fills/strokes inside SVGs so they're visible on white.

    Handles three places SVGs hide colors:
      1. fill/stroke/color attributes on shapes and text
      2. inline style="..." attributes
      3. <style>...</style> blocks inside the SVG (CSS classes like .d-text)
    """
    for svg in soup.find_all("svg"):
        # 1+2: walk every descendant element
        for el in svg.find_all(True):
            for attr in ("fill", "stroke", "color", "stop-color"):
                if attr in el.attrs:
                    el[attr] = _recolor_value(el[attr])
            if "style" in el.attrs:
                el["style"] = _recolor_value(el["style"])
        # 3: rewrite the text content of any embedded <style> blocks
        for style_el in svg.find_all("style"):
            css = style_el.string
            if css:
                style_el.string.replace_with(_recolor_value(css))
        # Top-level svg attrs
        for attr in ("fill", "stroke", "color"):
            if attr in svg.attrs:
                svg[attr] = _recolor_value(svg[attr])
        if "style" in svg.attrs:
            svg["style"] = _recolor_value(svg["style"])


def extract_content_cards(soup: BeautifulSoup) -> str:
    cards = soup.select(".mobile-card")
    parts: list[str] = []
    for card in cards:
        if is_title_card(card) or is_skippable_card(card):
            continue
        parts.append(str(card))
    return "\n".join(parts)


def track_class(track: str) -> str:
    m = re.search(r"Track\s*(\d+)", track)
    return f"track-{m.group(1)}" if m else "track-1"


def extract_module(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    # Drop top nav, progress bar, hamburger menu, scripts
    for sel in (".module-nav", ".progress-bar", ".hamburger-btn",
                ".hamburger-menu", ".menu-overlay", "script", "noscript"):
        for el in soup.select(sel):
            el.decompose()
    reveal_quiz_answers(soup)
    strip_problem_attrs(soup)
    strip_card_labels(soup)
    recolor_svgs_for_print(soup)
    header = get_header(soup)
    body = extract_content_cards(soup)
    return {**header, "body": body, "klass": track_class(header["track"])}


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Mobile Course (Print Edition) — Building AI Agents with Claude</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  @page { size: A4; margin: 14mm 14mm 14mm 14mm; }
  * { box-sizing: border-box; }

  /* === Light-theme overrides for dark mobile vars === */
  :root {
    --bg-primary: #ffffff;
    --bg-card: #fafbfc;
    --text-primary: #1a1f2e;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --accent-primary: #b8860b;
    --track-color: #6366F1;
    --track-foundations: #6366F1;
    --success: #047857;
    --error: #be123c;
    --warning: #b45309;
    --info: #2563eb;
    --code-bg: rgba(99, 102, 241, 0.06);
    --code-border: #6366F1;
  }

  html, body {
    margin: 0; padding: 0;
    background: #fff; color: var(--text-primary);
    font-family: 'Source Sans 3', -apple-system, sans-serif;
    font-size: 10pt; line-height: 1.5;
  }
  h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', sans-serif; color: #0A1628; }
  p { margin: 0 0 0.55rem; }
  ul, ol { margin: 0.4rem 0 0.6rem 1.2rem; padding: 0; }
  li { margin-bottom: 0.25rem; }
  strong { font-weight: 700; }
  a { color: #2563eb; text-decoration: none; }

  /* === Cover page === */
  .cover {
    page-break-after: always;
    text-align: center;
    padding-top: 28vh;
  }
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

  /* === Module page === */
  .module {
    page-break-before: always;
    border-top: 4px solid var(--track-color);
    padding-top: 0.5rem;
  }
  .module:first-of-type { /* keep page-break for cleanliness */ }
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
    margin: 0 0 0.75rem; line-height: 1.4;
  }

  /* === Each card flows as a plain section, no box chrome === */
  .mobile-card {
    background: transparent;
    border: 0;
    padding: 0;
    margin: 0.55rem 0 0.75rem;
    page-break-inside: avoid;
  }
  .mobile-card h2 {
    font-size: 12.5pt; font-weight: 700; line-height: 1.3;
    margin: 0.4rem 0 0.35rem; color: #0A1628;
  }
  .mobile-card h3 { font-size: 10.5pt; margin: 0.5rem 0 0.3rem; }
  .card-label, .section-label, .analogy-label { display: none !important; }

  /* === Pseudocode block === */
  .pseudocode {
    background: var(--code-bg);
    border-left: 3px solid var(--code-border);
    border-radius: 0 4px 4px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5pt; line-height: 1.5;
    padding: 0.6rem 0.8rem; margin: 0.45rem 0;
    white-space: pre-wrap; word-break: break-word;
    color: #1a1f2e;
    overflow: visible;
  }

  /* === Takeaway box === */
  .takeaway {
    background: rgba(212, 168, 67, 0.1);
    border-left: 3px solid #b8860b;
    border-radius: 0 4px 4px 0;
    padding: 0.55rem 0.8rem; margin: 0.45rem 0;
  }
  .takeaway h3 { color: #8a6a1a; margin-top: 0; font-size: 10pt; }
  .takeaway p:last-child { margin-bottom: 0; }

  /* === Misconception (myth/reality) box === */
  .misconception {
    background: rgba(244, 63, 94, 0.05);
    border-left: 3px solid #be123c;
    border-radius: 0 4px 4px 0;
    padding: 0.45rem 0.7rem; margin-bottom: 0.4rem;
  }
  .misconception .myth {
    display: block; font-weight: 700;
    color: #be123c; font-size: 9pt; margin-bottom: 0.2rem;
  }
  .misconception .reality {
    color: #4a5568; font-size: 9pt;
  }
  .misconception strong { color: #be123c; }

  /* === Analogy box (M09+ variant) === */
  .analogy-box {
    background: rgba(212, 168, 67, 0.08);
    border-left: 3px solid #b8860b;
    border-radius: 0 4px 4px 0;
    padding: 0.55rem 0.8rem; margin: 0.45rem 0;
  }
  .analogy-label {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 8pt;
    color: #8a6a1a; margin-bottom: 0.25rem;
    text-transform: uppercase; letter-spacing: 0.08em;
  }

  /* === Step list === */
  .steps-list, .step-list {
    list-style: none; counter-reset: step;
    margin: 0.4rem 0; padding-left: 0;
  }
  .steps-list li, .step-list li {
    counter-increment: step;
    position: relative;
    padding: 0.35rem 0 0.35rem 2rem;
    border-bottom: 1px solid #edf2f7;
    font-size: 9.5pt;
  }
  .steps-list li:last-child, .step-list li:last-child { border-bottom: none; }
  .steps-list li::before, .step-list li::before {
    content: counter(step);
    position: absolute; left: 0; top: 0.4rem;
    width: 1.3rem; height: 1.3rem; border-radius: 50%;
    background: rgba(99, 102, 241, 0.15);
    color: var(--track-color);
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 8pt;
    display: flex; align-items: center; justify-content: center;
    line-height: 1;
  }

  /* === Key insight === */
  .key-insight {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 4px;
    padding: 0.5rem 0.75rem; margin-top: 0.5rem;
    font-size: 9pt;
  }
  .key-insight strong { color: var(--track-color); }

  /* === Quiz === */
  .quiz-card .quiz-item {
    background: rgba(99, 102, 241, 0.04);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 4px;
    padding: 0.5rem 0.7rem; margin-bottom: 0.4rem;
  }
  .quiz-question { font-weight: 700; font-size: 9.5pt; margin-bottom: 0.25rem; }
  .quiz-answer {
    display: block !important;
    color: #047857; font-size: 9pt;
    padding-top: 0.3rem; margin-top: 0.3rem;
    border-top: 1px solid #cbd5e0;
  }
  .quiz-answer::before {
    content: "Answer: "; font-weight: 700; color: #047857;
  }

  /* === SVG diagrams render directly on the white page === */
  .diagram-container, .agent-diagram {
    background: transparent;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 0.55rem;
    margin: 0.5rem 0;
    text-align: center;
    page-break-inside: avoid;
  }
  .diagram-container svg, .agent-diagram svg {
    max-width: 100%; height: auto;
  }
  /* Any remaining dark backgrounds on diagram inner shapes — neutralize */
  .diagram-container svg [fill="#0A1628" i],
  .agent-diagram svg [fill="#0A1628" i] { fill: transparent; }

  /* === M00-specific block layout (course overview) === */
  .block-modules { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.5rem; margin-top: 0.5rem; }
  .block-item {
    background: rgba(99,102,241,0.05);
    border: 1px solid #e2e8f0;
    border-radius: 4px; padding: 0.5rem;
    font-size: 9pt;
  }
  .block-icon { font-size: 1.2rem; margin-bottom: 0.25rem; }
  .block-name { font-weight: 700; font-size: 9pt; color: #0A1628; }
  .block-desc { font-size: 8.5pt; color: #4a5568; margin-top: 0.2rem; }

  /* Inline span fallbacks */
  .myth { color: #be123c; font-weight: 700; }
  .reality { color: #4a5568; }

  /* Track-color tinting (matches track index) */
  .track-1 { --track-color: #6366F1; }
  .track-2 { --track-color: #10B981; }
  .track-3 { --track-color: #B45309; }
  .track-4 { --track-color: #7c3aed; }
  .track-5 { --track-color: #be123c; }
  .track-6 { --track-color: #2563eb; }
  .track-7 { --track-color: #0f766e; }
  .track-8 { --track-color: #be185d; }
  .track-9 { --track-color: #8a6a1a; }

  /* Drop scroll-snap / fixed-position artifacts */
  .card-container { display: block !important; overflow: visible !important; height: auto !important; }
  .swipe-hint, .read-time, .nav-links, .desktop-btn { display: none !important; }
  /* Hide stray decorative spans */
  .progress-dots, .progress-bar, .module-nav, .hamburger-btn { display: none !important; }
</style>
</head>
<body>
<section class="cover">
  <div class="eyebrow">Print Edition</div>
  <h1>Building AI Agents with Claude</h1>
  <div class="sub">The mobile course, condensed for offline reading. Every module's big idea, analogy, mechanics, pseudocode, misconceptions, takeaway, and quiz — in one document.</div>
  <div class="meta">__MODULE_COUNT__ modules · From Hello World to Autonomous Production Systems</div>
</section>
__MODULES__
</body>
</html>
"""


def render_module(mod: dict) -> str:
    head = (
        f'<header class="module-head">'
        f'<span class="num">{mod["module_num"] or "Module"}</span>'
        f'<span class="track">{mod["track"]}</span>'
        f'</header>'
        f'<h1 class="module-title">{mod["title"]}</h1>'
    )
    if mod["subtitle"]:
        head += f'<p class="module-sub">{mod["subtitle"]}</p>'
    return f'<section class="module {mod["klass"]}">{head}{mod["body"]}</section>'


def main() -> None:
    browser = find_browser()
    files = sorted(MOBILE_DIR.glob("M*-mobile.html"), key=lambda p: order_key(p.name))
    if not files:
        sys.exit(f"No mobile HTML files found in {MOBILE_DIR}")

    print(f"Parsing {len(files)} mobile modules ...", flush=True)
    modules = []
    for f in files:
        modules.append(extract_module(f))
        print(f"  · {f.name}", flush=True)

    body = "\n".join(render_module(m) for m in modules)
    html_doc = HTML_TEMPLATE.replace("__MODULES__", body).replace(
        "__MODULE_COUNT__", str(len(modules))
    )

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mobile-pdf-full-", dir=OUT_PDF.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / "fullbook.html"
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

    size_kb = final_path.stat().st_size / 1024
    pages = "?"
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(final_path)).pages)
    except Exception:
        pass
    print(f"Wrote {final_path} ({size_kb:.0f} KB, {pages} pages, {len(modules)} modules)")


if __name__ == "__main__":
    main()
