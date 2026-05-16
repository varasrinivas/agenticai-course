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

from bs4 import BeautifulSoup, NavigableString, Tag

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
    # Desktop-link inner blocks. Class names seen:
    #   .desktop-link, .desktop-link-card, .desktop-btn, .desktop-link-btn
    if card.find(class_=lambda c: c and (
        c == "desktop-link" or "desktop-btn" in c or "desktop-link-btn" in c
        or "desktop-link-card" in c
    )):
        return True
    # The 2026 revamp marks the closing card with aria-label="Continue to desktop"
    aria = (card.get("aria-label") or "").lower()
    if "continue to desktop" in aria or "continue on desktop" in aria:
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
    """Extract title-card metadata across mobile-template revisions.

    Current (2026 revamp):
      .title-card section with .title-meta (module number),
      .module-name (h1-equivalent, may contain <br> + subtitle span),
      .pill-track / .pill-time pills, and an intro <p>.

    Legacy variants kept for safety:
      .title-card / .card-title / .card-center / .card-inner with
      .track-badge, .module-number / .module-num / .module-label, <h1>.

    We try the new selectors first, then fall back to legacy.
    """
    # Title — current revamp uses .module-name (a div, not an h1)
    title_node = soup.select_one(".module-name")
    if title_node:
        # .module-name often holds "Title<br><span>Subtitle</span>".
        # Grab the leading text before the first <br>, otherwise full text.
        leading = ""
        for child in title_node.children:
            if isinstance(child, NavigableString):
                leading += str(child)
            elif getattr(child, "name", None) == "br":
                break
            else:
                # Stop at the first non-text element after we have something
                if leading.strip():
                    break
                leading += child.get_text(" ", strip=True)
        title = re.sub(r"\s+", " ", leading).strip() or text_of(title_node)
    else:
        h1 = soup.find("h1")
        title = text_of(h1) if h1 else "Module"

    # Module number
    module_num = text_of(soup.select_one(
        ".title-meta, "
        ".module-number, .module-num, .module-label, .card-number"
    ))

    # Track — try pill-track first, then legacy track-badge
    track = text_of(soup.select_one(".pill-track")) or text_of(soup.select_one(".track-badge"))
    # Pill-track text usually starts with a non-textual dot; the text_of helper
    # already collapses whitespace, but some sources embed a leading bullet.
    track = re.sub(r"^[•·\s]+", "", track).strip()

    # Subtitle — intro <p> inside title-card, or .subtitle, or the span after the <br>
    subtitle = ""
    title_card = soup.select_one(".title-card")
    if title_card:
        p = title_card.find("p")
        if p:
            subtitle = text_of(p)
    if not subtitle:
        subtitle = text_of(soup.select_one(".subtitle"))
    if not subtitle and title_node:
        # Use the trailing portion of .module-name after the <br>, if any
        br = title_node.find("br")
        if br and br.next_sibling:
            tail = ""
            for sib in br.next_siblings:
                tail += sib.get_text(" ", strip=True) if hasattr(sib, "get_text") else str(sib)
            subtitle = re.sub(r"\s+", " ", tail).strip()

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


# Two kinds of colors break SVGs on a white page:
#   1. Light fills/strokes meant for dark backgrounds — invisible on white.
#      Map these to dark text color.
#   2. Dark "card background" fills (#162033 / #0A1628 / etc.) — cover the
#      diagram in big dark rectangles on white paper. Map these to transparent.

_LIGHT_TO_DARK = [
    (re.compile(r"#E8ECF1", re.I), "#1a1f2e"),           # mobile --text-primary
    (re.compile(r"#B8C2D1", re.I), "#4a5568"),           # mobile --text-secondary
    (re.compile(r"#FFFFFF\b", re.I), "#1a1f2e"),
    (re.compile(r"#FFF\b", re.I), "#1a1f2e"),
    (re.compile(r"\bwhite\b", re.I), "#1a1f2e"),
    (re.compile(r"rgba?\(\s*255\s*,\s*255\s*,\s*255[^)]*\)", re.I), "#1a1f2e"),
    (re.compile(r"rgba?\(\s*232\s*,\s*236\s*,\s*241[^)]*\)", re.I), "#1a1f2e"),
]
_DARK_BG_TO_TRANSPARENT = [
    re.compile(r"#0A1628", re.I),   # bg-primary
    re.compile(r"#111D33", re.I),   # bg-secondary
    re.compile(r"#162033", re.I),   # bg-card
    re.compile(r"#1A2740", re.I),   # bg-surface
    re.compile(r"#0a0a1a", re.I),   # legacy dark page bg
]


def _recolor_value(value: str) -> str:
    out = value
    for pat, replacement in _LIGHT_TO_DARK:
        out = pat.sub(replacement, out)
    for pat in _DARK_BG_TO_TRANSPARENT:
        out = pat.sub("transparent", out)
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


_CAPSTONE_TITLE_PATTERN = re.compile(r"capstone", re.I)


def is_capstone_module(mod: dict) -> bool:
    """Capstone modules go into a pseudocode-only appendix at the end.

    Detected by title (M26 "Capstone Project Series") so we don't sweep in
    Track-8 neighbours like M27 "What's Next — The Agent Frontier" which is
    actually conceptual content.
    """
    return bool(_CAPSTONE_TITLE_PATTERN.search(mod.get("title") or ""))


def extract_capstone_pseudocode(soup: BeautifulSoup) -> str:
    """For capstone modules, keep only h2/h3 + nearby pseudocode blocks."""
    parts: list[str] = []
    for card in soup.select(".mobile-card"):
        if is_title_card(card) or is_skippable_card(card):
            continue
        pre = card.select_one(".pseudocode")
        if pre is None:
            continue
        heading = card.find(["h2", "h3"])
        heading_html = str(heading) if heading else ""
        parts.append(f'<div class="capstone-block">{heading_html}{str(pre)}</div>')
    return "\n".join(parts)


def extract_module(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    # Drop top nav, progress bar, hamburger menu, scripts
    for sel in (".module-nav", ".progress-bar", ".hamburger-btn",
                ".hamburger-menu", ".menu-overlay", "script", "noscript"):
        for el in soup.select(sel):
            el.decompose()
    reveal_quiz_answers(soup)
    strip_problem_attrs(soup)
    # NOTE: Section labels (.section-label, .card-label, .analogy-label) are
    # NOW kept — they're the primary wayfinders in the revamped mobile
    # content ("The Big Idea" / "Analogy" / "How It Works" / etc.). Styling
    # below renders them as small uppercase chips above each h2.
    recolor_svgs_for_print(soup)
    header = get_header(soup)
    body = extract_content_cards(soup)
    pseudocode_only = extract_capstone_pseudocode(soup)
    return {
        **header,
        "body": body,
        "pseudocode_only": pseudocode_only,
        "klass": track_class(header["track"]),
    }


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
    --bg-secondary: #f1f5f9;
    --bg-card: #fafbfc;
    --bg-surface: #f8fafc;
    --text-primary: #1a1f2e;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --accent-primary: #b8860b;
    --accent-hover: #c9912e;
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

  /* === Table of contents === */
  .toc {
    page-break-before: always;
    page-break-after: always;
    padding-top: 0.5rem;
  }
  .toc h1 {
    font-size: 24pt;
    font-weight: 800;
    margin: 0 0 0.4rem;
    color: #0A1628;
    letter-spacing: -0.01em;
  }
  .toc .toc-hint {
    font-size: 9pt;
    color: #718096;
    font-style: italic;
    margin: 0 0 1rem;
  }
  .toc-list {
    list-style: none;
    margin: 0;
    padding: 0;
    counter-reset: tocrow;
  }
  .toc-item {
    border-bottom: 1px dotted #cbd5e0;
    page-break-inside: avoid;
  }
  .toc-item a {
    display: flex;
    align-items: baseline;
    gap: 0.9rem;
    padding: 0.5rem 0.25rem;
    color: #1a1f2e;
    text-decoration: none;
  }
  .toc-item a:hover { background: #f7fafc; }
  .toc-num {
    flex: 0 0 auto;
    width: 3.4em;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 9pt;
    font-weight: 700;
    color: var(--track-color);
    letter-spacing: 0.04em;
    white-space: nowrap;
  }
  .toc-title {
    flex: 1 1 auto;
    font-size: 10.5pt;
    font-weight: 600;
    color: #0A1628;
    line-height: 1.3;
    /* Allow long titles to wrap rather than push the track off-screen */
    min-width: 0;
  }
  .toc-track {
    flex: 0 0 auto;
    font-size: 8.5pt;
    color: #718096;
    font-weight: 600;
    text-align: right;
    white-space: nowrap;
  }

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

  /* === Cards flow as plain sections — no chrome (matches reference layout) === */
  .mobile-card {
    background: transparent;
    border: 0;
    padding: 0;
    margin: 0.6rem 0 0.5rem;
    page-break-inside: avoid;
  }
  .mobile-card h2 {
    font-size: 12.5pt; font-weight: 700; line-height: 1.3;
    margin: 0.5rem 0 0.4rem; color: #0A1628;
  }
  .mobile-card h3 { font-size: 10.5pt; margin: 0.5rem 0 0.3rem; }

  /* Section labels stay visible but quietly — small uppercase tag, no chip */
  .card-label, .section-label, .analogy-label {
    display: block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--track-color);
    margin: 0.5rem 0 0.1rem;
  }
  /* Concept chip (e.g. "Concept 1 of 2") — small inline pill */
  .concept-chip {
    display: inline-block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 7pt;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #8a6a1a;
    background: rgba(212, 168, 67, 0.1);
    padding: 0.05rem 0.4rem;
    border-radius: 3px;
    margin-bottom: 0.3rem;
  }

  /* === Capstone appendix === */
  .appendix {
    page-break-before: always;
    padding-top: 0.5rem;
  }
  .appendix-title {
    font-size: 24pt; font-weight: 800;
    margin: 0 0 0.4rem; color: #0A1628;
    letter-spacing: -0.01em;
  }
  .appendix-sub {
    font-size: 10pt; color: #4a5568;
    font-style: italic;
    margin: 0 0 1.5rem;
    max-width: 640px;
  }
  .capstone-mod {
    page-break-inside: avoid;
    margin-bottom: 1.2rem;
  }
  .capstone-mod-title {
    font-size: 14pt; font-weight: 700;
    color: #0A1628;
    margin: 0.5rem 0 0.25rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid var(--track-color);
  }
  .capstone-mod-sub {
    font-size: 10pt; color: #4a5568;
    font-style: italic;
    margin: 0 0 0.6rem;
  }
  .capstone-block { margin: 0.6rem 0; page-break-inside: avoid; }
  .capstone-block h2,
  .capstone-block h3 {
    font-size: 11pt; font-weight: 700;
    margin: 0.4rem 0 0.3rem; color: #0A1628;
  }
  .capstone-empty { font-size: 9.5pt; color: #718096; }
  .toc-appendix .toc-num { color: #8a6a1a; }

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
    padding: 0.45rem 0.4rem 0.45rem 2.1rem;
    margin-bottom: 0.35rem;
    background: rgba(99, 102, 241, 0.05);
    border-left: 3px solid var(--track-color);
    border-radius: 0 4px 4px 0;
    font-size: 9.5pt;
    color: #2d3748;
  }
  .steps-list li::before, .step-list li::before {
    content: counter(step);
    position: absolute; left: 0.5rem; top: 0.5rem;
    width: 1.2rem; height: 1.2rem; border-radius: 50%;
    background: var(--track-color);
    color: #fff;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 8pt;
    display: flex; align-items: center; justify-content: center;
    line-height: 1;
  }
  .steps-list li strong, .step-list li strong {
    display: block; margin-bottom: 0.15rem;
    color: #0A1628;
    font-family: 'Bricolage Grotesque', sans-serif;
  }

  /* === Concept index card === */
  .index-list { list-style: none; margin: 0.4rem 0; padding: 0; }
  .index-list li { margin-bottom: 0.45rem; page-break-inside: avoid; }
  .index-list a {
    display: flex; gap: 0.7rem; align-items: baseline;
    padding: 0.45rem 0.5rem;
    background: rgba(99, 102, 241, 0.05);
    border-left: 3px solid var(--track-color);
    border-radius: 0 4px 4px 0;
    color: #1a1f2e; text-decoration: none;
  }
  .idx-num {
    flex: 0 0 auto;
    width: 1.4rem; height: 1.4rem; border-radius: 50%;
    background: var(--track-color); color: #fff;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 8pt;
    display: inline-flex; align-items: center; justify-content: center;
    line-height: 1;
  }
  .idx-sub { display: block; font-size: 8.5pt; color: #718096; margin-top: 0.1rem; }

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
  .diagram-container, .agent-diagram, .analogy-svg-wrap {
    background: transparent;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 0.55rem;
    margin: 0.5rem 0;
    text-align: center;
    page-break-inside: avoid;
  }
  .diagram-container svg, .agent-diagram svg, .analogy-svg-wrap svg {
    max-width: 100%; height: auto;
  }
  /* Belt-and-suspenders: kill dark page-bg fills the recolor pass missed */
  svg [fill="#0A1628" i], svg [fill="#162033" i],
  svg [fill="#111D33" i], svg [fill="#1A2740" i] { fill: transparent; }

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


def short_module_id(mod: dict, index: int) -> str:
    """Normalize the wildly-varying module-num strings to a short tag.

    "MODULE 1 of 30"        → M01
    "Module 02 of 30"       → M02
    "MODULE M03B · 5 of 32" → M03B
    "Module 5 of 30"        → M05
    Falls back to M{index:02d} if no match.
    """
    raw = mod.get("module_num") or ""
    # Strip a leading "M" if there's no digit attached, then look for the first <digits><optional letter>
    m = re.search(r"M?\s*(\d+)\s*([A-Z])?", raw, flags=re.I)
    if not m:
        return f"M{index:02d}"
    num = int(m.group(1))
    letter = (m.group(2) or "").upper()
    return f"M{num:02d}{letter}"


def section_anchor(mod: dict, index: int) -> str:
    return f"mod-{short_module_id(mod, index).lower()}"


def render_module(mod: dict, index: int) -> str:
    anchor = section_anchor(mod, index)
    head = (
        f'<header class="module-head">'
        f'<span class="num">{mod["module_num"] or "Module"}</span>'
        f'<span class="track">{mod["track"]}</span>'
        f'</header>'
        f'<h1 class="module-title">{mod["title"]}</h1>'
    )
    if mod["subtitle"]:
        head += f'<p class="module-sub">{mod["subtitle"]}</p>'
    return f'<section class="module {mod["klass"]}" id="{anchor}">{head}{mod["body"]}</section>'


def render_toc(modules: list[dict], has_capstone_appendix: bool = False) -> str:
    rows = []
    for i, mod in enumerate(modules, 1):
        anchor = section_anchor(mod, i)
        num = short_module_id(mod, i)
        track = mod.get("track") or ""
        track_html = f'<span class="toc-track">{track}</span>' if track else ""
        rows.append(
            f'<li class="toc-item {mod["klass"]}">'
            f'<a href="#{anchor}">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-title">{mod["title"]}</span>'
            f'{track_html}'
            f'</a></li>'
        )
    if has_capstone_appendix:
        rows.append(
            '<li class="toc-item toc-appendix">'
            '<a href="#appendix-capstones">'
            '<span class="toc-num">APPX</span>'
            '<span class="toc-title">Capstone Projects (pseudocode reference)</span>'
            '<span class="toc-track">Appendix</span>'
            '</a></li>'
        )
    return (
        '<section class="toc">'
        '<h1>Table of Contents</h1>'
        '<p class="toc-hint">Click any entry to jump to that module.</p>'
        f'<ol class="toc-list">{"".join(rows)}</ol>'
        '</section>'
    )


def render_capstone_appendix(capstones: list[dict]) -> str:
    """A pseudocode-only appendix for capstone modules."""
    parts = [
        '<section class="appendix capstones" id="appendix-capstones">',
        '<h1 class="appendix-title">Capstone Projects</h1>',
        '<p class="appendix-sub">Pseudocode reference for the capstone build patterns. Concept material is covered in the modules above; this appendix collects only the executable scaffolding.</p>',
    ]
    for mod in capstones:
        anchor = f'cap-{re.sub(r"[^a-z0-9]+", "-", (mod.get("title") or "capstone").lower()).strip("-")}'
        parts.append(f'<section class="capstone-mod" id="{anchor}">')
        parts.append(f'<h2 class="capstone-mod-title">{mod["title"]}</h2>')
        if mod.get("subtitle"):
            parts.append(f'<p class="capstone-mod-sub">{mod["subtitle"]}</p>')
        if mod.get("pseudocode_only"):
            parts.append(mod["pseudocode_only"])
        else:
            parts.append('<p class="capstone-empty"><em>This capstone has no pseudocode block — see the desktop module for the full reference.</em></p>')
        parts.append('</section>')
    parts.append('</section>')
    return "\n".join(parts)


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

    concepts = [m for m in modules if not is_capstone_module(m)]
    capstones = [m for m in modules if is_capstone_module(m)]

    toc = render_toc(concepts, has_capstone_appendix=bool(capstones))
    body_parts = [toc]
    body_parts.extend(render_module(m, i) for i, m in enumerate(concepts, 1))
    if capstones:
        body_parts.append(render_capstone_appendix(capstones))
    body = "\n".join(body_parts)
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

    pages = add_pdf_bookmarks(final_path, modules)
    size_kb = final_path.stat().st_size / 1024
    print(f"Wrote {final_path} ({size_kb:.0f} KB, {pages} pages, {len(modules)} modules)")


def add_pdf_bookmarks(pdf_path: Path, modules: list[dict]) -> int:
    """Scan the rendered PDF and insert sidebar bookmarks for each module.

    Strategy: extract text per page, locate the page where each module's
    title (or "MODULE X OF") first appears, then add an outline entry. Falls
    back to no bookmarks if extraction fails — never aborts the build.
    """
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

    concepts = [m for m in modules if not is_capstone_module(m)]
    capstones = [m for m in modules if is_capstone_module(m)]

    # Find first page for each concept module.
    matches: list[tuple[int, dict]] = []
    used_pages: set[int] = set()
    for mod in concepts:
        title_needle = mod["title"].strip().lower()[:40]
        num_needle = (mod["module_num"] or "").lower()
        found = None
        for idx, text in enumerate(page_texts):
            if idx in used_pages:
                continue
            if title_needle and title_needle in text:
                found = idx
                break
            if num_needle and num_needle in text:
                found = idx
                break
        if found is not None:
            used_pages.add(found)
            matches.append((found, mod))

    # Find the appendix start (first page after main content mentioning "Capstone Projects")
    appendix_page = None
    appendix_needle = "capstone projects"
    for idx in range(len(page_texts) - 1, -1, -1):
        if appendix_needle in page_texts[idx]:
            appendix_page = idx
            break

    if not matches and appendix_page is None:
        return page_count

    writer = PdfWriter(clone_from=reader)
    writer.add_outline_item("Cover", 0)
    if page_count > 1:
        writer.add_outline_item("Table of Contents", 1)
    for page_idx, mod in matches:
        label = f"{mod['module_num']} — {mod['title']}" if mod["module_num"] else mod["title"]
        try:
            writer.add_outline_item(label, page_idx)
        except Exception:
            continue
    if appendix_page is not None and capstones:
        try:
            appendix_parent = writer.add_outline_item("Appendix — Capstone Projects", appendix_page)
            for mod in capstones:
                # Find the page that first mentions this capstone title in the appendix
                cap_needle = mod["title"].strip().lower()[:40]
                cap_page = appendix_page
                for idx in range(appendix_page, len(page_texts)):
                    if cap_needle in page_texts[idx]:
                        cap_page = idx
                        break
                try:
                    writer.add_outline_item(mod["title"], cap_page, parent=appendix_parent)
                except Exception:
                    continue
        except Exception:
            pass

    try:
        with open(pdf_path, "wb") as fh:
            writer.write(fh)
    except PermissionError:
        print(f"  (cannot rewrite {pdf_path.name} — close any open viewer to add bookmarks)")
    return page_count


if __name__ == "__main__":
    main()
