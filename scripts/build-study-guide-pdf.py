"""Build a compact, interview-prep study guide PDF from the mobile module HTMLs.

This is a tighter variant of build-mobile-pdf-full.py:

- Same source content (every output/mobile/M*-mobile.html)
- Same extraction helpers (BeautifulSoup-based card parser, SVG recolor)
- Different CSS: smaller margins, smaller fonts, tighter card padding,
  no forced per-module page-break, skip concept-index cards
- Interview-prep framed cover and TOC

Output: output/mobile/study-guide-interview.pdf

Reuse: rather than copy 600 lines of well-tested helpers, we import
build-mobile-pdf-full.py via importlib (its module name has a hyphen
so a normal `import` won't work).
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# Import helpers from the sibling full-content script
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
_FULL_SCRIPT = SCRIPT_DIR / "build-mobile-pdf-full.py"

_spec = importlib.util.spec_from_file_location("mobile_pdf_full", _FULL_SCRIPT)
mobile_pdf_full = importlib.util.module_from_spec(_spec)
sys.modules["mobile_pdf_full"] = mobile_pdf_full
_spec.loader.exec_module(mobile_pdf_full)

find_browser = mobile_pdf_full.find_browser
order_key = mobile_pdf_full.order_key
get_header = mobile_pdf_full.get_header
reveal_quiz_answers = mobile_pdf_full.reveal_quiz_answers
strip_problem_attrs = mobile_pdf_full.strip_problem_attrs
recolor_svgs_for_print = mobile_pdf_full.recolor_svgs_for_print
is_skippable_card = mobile_pdf_full.is_skippable_card
is_title_card = mobile_pdf_full.is_title_card
track_class = mobile_pdf_full.track_class
short_module_id = mobile_pdf_full.short_module_id
add_pdf_bookmarks = mobile_pdf_full.add_pdf_bookmarks
is_capstone_module = mobile_pdf_full.is_capstone_module


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
MOBILE_DIR = ROOT / "output" / "mobile"
OUT_PDF = MOBILE_DIR / "study-guide-interview.pdf"


# ---------------------------------------------------------------------------
# Extra skip rules — the study guide is tighter than the full PDF
# ---------------------------------------------------------------------------

def is_concept_index_card(card: Tag) -> bool:
    """Skip the per-module "The N concepts of ..." index cards.

    These cards are pure navigation — useful in interactive mobile reading,
    pure whitespace in a printed study guide.
    """
    aria = (card.get("aria-label") or "").lower()
    if "concept index" in aria:
        return True
    if card.find(class_="index-list"):
        return True
    # Heading text fallback: "The N concepts of ..."
    h2 = card.find(["h2", "h3"])
    if h2 and re.match(r"^\s*the\s+\d+\s+concepts?\b", h2.get_text(strip=True), re.I):
        return True
    return False


def is_big_idea_card(card: Tag) -> bool:
    """Skip cards whose role is "The Big Idea".

    Most modules have an explicit Big Idea card with a `.section-label` of
    "The Big Idea" or an aria-label ending in "- Big Idea". The framing it
    provides is largely redundant with the module title + analogy + how-it-
    works trio in an interview-prep context, so we drop it to save pages.
    """
    aria = (card.get("aria-label") or "").lower()
    if "big idea" in aria:
        return True
    for label_cls in ("section-label", "card-label"):
        label = card.find(class_=label_cls)
        if label and "big idea" in label.get_text(strip=True).lower():
            return True
    return False


_CAPSTONE_ARIA_PATTERNS = (
    re.compile(r"three\s+agents\s*-", re.I),     # M00 mobile capstone preview cluster
    re.compile(r"\bcapstone\b", re.I),           # generic capstone-tagged cards
)


def is_capstone_themed_card(card: Tag) -> bool:
    """Skip cards whose entire purpose is capstone-project content.

    Detects:
      - aria-label like "Three Agents - Big Idea" (the M00 5-card preview
        cluster that previews Capstones 1/3/5)
      - aria-label containing the word "Capstone" (treated as a whole word
        so we don't accidentally match unrelated content)
      - cards whose h2 begins with "Capstone " (e.g. "Capstone 1 vs 3 vs 5")

    Incidental inline mentions of capstones inside other cards (e.g. the
    sentence "you'll build this in Capstone 1") are intentionally NOT
    skipped — they're useful context, not capstone content.
    """
    aria = card.get("aria-label") or ""
    for pat in _CAPSTONE_ARIA_PATTERNS:
        if pat.search(aria):
            return True
    h2 = card.find(["h2", "h3"])
    if h2:
        text = h2.get_text(strip=True)
        if re.match(r"^\s*Capstone\s+\d", text, re.I):
            return True
    return False


def is_extra_skippable(card: Tag) -> bool:
    """Combine the upstream skip rules with our extra study-guide rules."""
    if is_skippable_card(card):
        return True
    if is_concept_index_card(card):
        return True
    if is_big_idea_card(card):
        return True
    if is_capstone_themed_card(card):
        return True
    return False


def extract_content_cards(soup: BeautifulSoup) -> str:
    """Mirror upstream extract_content_cards but using our extended skip rule."""
    parts: list[str] = []
    for card in soup.select(".mobile-card"):
        if is_title_card(card) or is_extra_skippable(card):
            continue
        parts.append(str(card))
    return "\n".join(parts)


_CLUSTER_ARIA_RE = re.compile(r"^\s*(.+?)\s*-\s*(.+?)\s*$")


def inject_cluster_context(soup: BeautifulSoup) -> None:
    """Rewrite each card's section-label to include the cluster name.

    Mobile cards have aria-labels like "Caching - Analogy" or "ReAct Loop
    - How It Works". Without the Big Idea card (which we drop), the reader
    has no anchor for which concept cluster a given Analogy / How-It-Works
    / Misconceptions card belongs to. We surface that by prepending the
    cluster name to the existing section-label text:

        "The Analogy" -> "Caching · The Analogy"

    This is a no-op for cards without an aria-label or section-label, and
    no-op (idempotent) if the cluster name already appears in the label.
    """
    # MUST run BEFORE strip_problem_attrs() (which removes aria-label).
    for card in soup.select(".mobile-card"):
        aria = card.get("aria-label") or ""
        m = _CLUSTER_ARIA_RE.match(aria)
        if not m:
            continue
        cluster = m.group(1).strip()
        if not cluster:
            continue
        label = None
        for cls in ("section-label", "card-label", "analogy-label"):
            label = card.find(class_=cls)
            if label:
                break
        if label is None:
            continue
        existing = label.get_text(strip=True)
        if not existing or cluster.lower() in existing.lower():
            continue
        # Wrap in spans so CSS can style cluster vs section-type separately.
        label.clear()
        cluster_span = soup.new_tag("span", attrs={"class": "cl-cluster"})
        cluster_span.string = cluster
        sep_span = soup.new_tag("span", attrs={"class": "cl-sep"})
        sep_span.string = " · "
        type_span = soup.new_tag("span", attrs={"class": "cl-type"})
        type_span.string = existing
        label.append(cluster_span)
        label.append(sep_span)
        label.append(type_span)


def extract_module(html_path: Path) -> dict:
    """Mirror upstream extract_module but route through our cards filter."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    for sel in (".module-nav", ".progress-bar", ".hamburger-btn",
                ".hamburger-menu", ".menu-overlay", "script", "noscript"):
        for el in soup.select(sel):
            el.decompose()
    reveal_quiz_answers(soup)
    # IMPORTANT: inject cluster context BEFORE strip_problem_attrs() because
    # the latter wipes aria-label, which we need to parse the cluster name.
    inject_cluster_context(soup)
    strip_problem_attrs(soup)
    recolor_svgs_for_print(soup)
    header = get_header(soup)
    body = extract_content_cards(soup)
    return {
        **header,
        "body": body,
        "klass": track_class(header["track"]),
    }


# ---------------------------------------------------------------------------
# CSS: compact, interview-prep, print-friendly
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI Agent Engineering — Interview Study Guide</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  /* === Ultra-compact 2-column layout === */
  @page { size: A4; margin: 5mm 5mm 5mm 5mm; }
  * { box-sizing: border-box; }

  :root {
    --bg-surface: #f5f7fa;
    --text-primary: #1a1f2e;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --accent-primary: #b8860b;
    --track-color: #6366F1;
    --code-bg: rgba(99, 102, 241, 0.06);
    --code-border: #6366F1;
  }

  /* Single-column body; each module gets its own 2-column page */
  html, body {
    margin: 0; padding: 0;
    background: #fff; color: var(--text-primary);
    font-family: 'Source Sans 3', -apple-system, sans-serif;
    font-size: 7pt; line-height: 1.28;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', sans-serif; color: #0A1628; }
  h1 { font-size: 11pt; line-height: 1.18; margin: 0.3rem 0 0.15rem; }
  h2 { font-size: 8.5pt; line-height: 1.2; margin: 0.22rem 0 0.1rem; }
  h3 { font-size: 7pt; line-height: 1.24; margin: 0.18rem 0 0.08rem; }
  p  { margin: 0 0 0.18rem; }
  ul, ol { margin: 0.12rem 0 0.2rem 0.75rem; padding: 0; }
  li { margin-bottom: 0.08rem; }
  strong { font-weight: 700; }
  a { color: #2563eb; text-decoration: none; }
  code {
    font-family: 'JetBrains Mono', monospace; font-size: 6pt;
    background: rgba(99,102,241,0.07); padding: 0.02rem 0.2rem;
    border-radius: 2px; border: 1px solid rgba(99,102,241,0.15);
  }
  em { color: var(--text-secondary); font-style: italic; }

  /* === Cover: compact banner, full width === */
  .cover {
    text-align: center;
    padding: 2.5mm 0 2mm;
    border-bottom: 1.5px solid #d4a843;
    margin-bottom: 2mm;
  }
  .cover .eyebrow {
    font-size: 6pt; letter-spacing: 0.2em; text-transform: uppercase;
    color: #8a6a1a; font-weight: 700;
  }
  .cover h1 {
    font-size: 14pt; margin: 0.8mm 0 0.5mm; color: #0A1628;
    font-family: 'Bricolage Grotesque', sans-serif;
  }
  .cover .sub { display: none; }
  .cover ul.coverage { display: none; }
  .cover .meta { font-size: 6pt; color: #718096; }

  /* === TOC: full-width index, then page break before modules === */
  .toc {
    padding: 1.5mm 0 2mm;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 2mm;
    break-after: always;
  }
  .toc h1 { font-size: 9pt; margin: 0 0 1mm; }
  .toc .toc-hint { display: none; }
  .toc-list { list-style: none; margin: 0; padding: 0; column-count: 3; column-gap: 3mm; }
  .toc-item { border-bottom: none; break-inside: avoid; }
  .toc-item a { display: flex; align-items: baseline; gap: 0.3rem; padding: 0.1rem 0; color: #1a1f2e; }
  .toc-num { flex: 0 0 auto; width: 2.1em;
             font-family: 'Bricolage Grotesque', sans-serif;
             font-size: 6.5pt; font-weight: 700; color: var(--track-color); white-space: nowrap; }
  .toc-title { flex: 1 1 auto; font-size: 6.5pt; font-weight: 600; color: #0A1628;
               line-height: 1.2; min-width: 0; }
  .toc-track { display: none; }

  /* === Module — each on its own page, 2-column content inside === */
  .module {
    border-top: 3px solid var(--track-color);
    padding-top: 0.3rem;
    margin-top: 0;
    break-before: always;
  }
  .module.first-module { break-before: auto; }

  /* 2-column layout scoped to each module's card content */
  .module-body-cols {
    columns: 2;
    column-gap: 5mm;
    margin-top: 0.3rem;
  }
  .module-head {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 0.3rem; margin-bottom: 0.12rem;
  }
  .module-head .num {
    font-family: 'Bricolage Grotesque', sans-serif; font-size: 7pt; font-weight: 800;
    color: var(--track-color); letter-spacing: 0.06em; text-transform: uppercase;
    white-space: nowrap;
  }
  .module-head .track {
    font-size: 5.8pt; color: #4a5568; font-weight: 600;
    background: var(--bg-surface); padding: 0.04rem 0.28rem; border-radius: 2px;
  }
  .module h1.module-title {
    font-size: 11pt; line-height: 1.18; font-weight: 800;
    margin: 0 0 0.1rem; color: #0A1628;
  }
  .module .module-sub {
    font-size: 6.5pt; color: #4a5568; font-style: italic;
    margin: 0 0 0.22rem; line-height: 1.28;
    padding-bottom: 0.18rem; border-bottom: 1px dotted #d1d5db;
  }

  /* === Cards: ultra-tight === */
  .mobile-card {
    background: transparent; border: 0;
    padding: 0.2rem 0 0;
    margin: 0.28rem 0 0.2rem;
    break-inside: avoid;
    border-top: 1px solid #e8edf3;
  }
  .mobile-card:first-child { border-top: 0; padding-top: 0; margin-top: 0.15rem; }
  .mobile-card h2 {
    font-size: 8.5pt; line-height: 1.2;
    margin: 0.1rem 0 0.1rem; color: #0A1628;
  }
  .mobile-card h3 { font-size: 7pt; line-height: 1.22; margin: 0.15rem 0 0.08rem; }

  /* === Card header chip === */
  .card-label, .section-label, .analogy-label {
    display: inline-block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 7pt; font-weight: 700;
    letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--track-color);
    background: rgba(99, 102, 241, 0.06);
    padding: 0.1rem 0.38rem 0.1rem 0.32rem;
    border-radius: 2px;
    border-left: 2px solid var(--track-color);
    line-height: 1.28;
  }
  .section-label .cl-cluster,
  .card-label .cl-cluster,
  .analogy-label .cl-cluster { color: #0A1628; font-weight: 800; }
  .section-label .cl-sep,
  .card-label .cl-sep,
  .analogy-label .cl-sep { color: var(--track-color); opacity: 0.5; margin: 0 0.1rem; }
  .section-label .cl-type,
  .card-label .cl-type,
  .analogy-label .cl-type { color: var(--track-color); font-weight: 600; }

  .concept-chip {
    display: inline-block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 6pt; font-weight: 700;
    letter-spacing: 0.04em; text-transform: uppercase;
    color: #6a4f0e; background: rgba(212, 168, 67, 0.13);
    padding: 0.08rem 0.3rem; border-radius: 2px;
    margin: 0 0 0 0.3rem; vertical-align: middle;
  }

  /* === Pseudocode === */
  .pseudocode {
    background: var(--code-bg);
    border-left: 2px solid var(--code-border);
    border-radius: 0 2px 2px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 6pt; line-height: 1.35;
    padding: 0.22rem 0.4rem; margin: 0.18rem 0;
    white-space: pre-wrap; word-break: break-word;
    color: #1a1f2e; overflow: visible;
  }
  .pseudocode .kw  { color: #7c3aed; font-weight: 700; }
  .pseudocode .cmt { color: #6b7280; font-style: italic; }
  .pseudocode .var { color: #b45309; }
  .pseudocode .str { color: #047857; }

  /* === Takeaway === */
  .takeaway {
    background: rgba(212, 168, 67, 0.08);
    border-left: 2px solid #b8860b;
    border-radius: 0 2px 2px 0;
    padding: 0.2rem 0.38rem; margin: 0.18rem 0;
    font-size: 7pt;
  }
  .takeaway::before {
    content: "Takeaway"; display: block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 6pt; font-weight: 800; letter-spacing: 0.1em;
    text-transform: uppercase; color: #8a6a1a;
    margin-bottom: 0.08rem;
  }
  .takeaway h3 { display: none; }
  .takeaway p { margin: 0 0 0.12rem; }
  .takeaway p:last-child { margin-bottom: 0; }

  /* === Misconceptions === */
  .misconception {
    background: rgba(244, 63, 94, 0.04);
    border-left: 2px solid #be123c;
    border-radius: 0 2px 2px 0;
    padding: 0.18rem 0.35rem; margin: 0 0 0.18rem;
  }
  .misconception .icon { display: none; }
  .misconception .wrong, .misconception .myth {
    display: block; font-weight: 700; color: #be123c; font-size: 7pt;
    margin-bottom: 0.08rem;
  }
  .misconception .right, .misconception .reality {
    color: #2d3748; font-size: 7pt; line-height: 1.3;
  }

  /* === Analogy box === */
  .analogy-box {
    background: rgba(212, 168, 67, 0.06);
    border-left: 2px solid #b8860b;
    border-radius: 0 2px 2px 0;
    padding: 0.2rem 0.38rem; margin: 0.18rem 0;
  }
  .analogy-box p { margin: 0 0 0.15rem; font-size: 7pt; }
  .analogy-box p:last-child { margin-bottom: 0; }

  /* === Step list === */
  .step-list, .steps-list {
    list-style: none; counter-reset: step; margin: 0.15rem 0; padding: 0;
  }
  .step-list li, .steps-list li {
    counter-increment: step; position: relative;
    padding: 0.18rem 0.25rem 0.18rem 1.3rem;
    margin-bottom: 0.14rem;
    background: rgba(99, 102, 241, 0.04);
    border-left: 1.5px solid var(--track-color);
    border-radius: 0 2px 2px 0;
    font-size: 7pt; color: #2d3748;
  }
  .step-list li::before, .steps-list li::before {
    content: counter(step); position: absolute; left: 0.22rem; top: 0.22rem;
    width: 0.78rem; height: 0.78rem; border-radius: 50%;
    background: var(--track-color); color: #fff;
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 5.5pt;
    display: flex; align-items: center; justify-content: center; line-height: 1;
  }
  .step-list li strong, .steps-list li strong {
    display: block; margin-bottom: 0.06rem; color: #0A1628;
    font-family: 'Bricolage Grotesque', sans-serif;
  }

  /* === Tables === */
  table, .compare-table, .framework-table, .decision-table, .domain-table {
    display: table !important; border-collapse: collapse;
    font-size: 6.5pt; width: 100%; margin: 0.18rem 0; break-inside: avoid;
  }
  thead { display: table-header-group; }
  tbody { display: table-row-group; }
  tr { display: table-row; }
  th, td { display: table-cell; padding: 0.18rem 0.3rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
  th { background: var(--bg-surface); font-family: 'Bricolage Grotesque', sans-serif;
       font-weight: 700; font-size: 6.2pt; text-align: left; color: var(--text-secondary);
       text-transform: uppercase; letter-spacing: 0.03em; }

  /* === Grid "tables" === */
  .pattern-grid { display: block; margin: 0.18rem 0; border-top: 1px solid #e2e8f0; }
  .pattern-row {
    display: grid; grid-template-columns: 2.1rem 1fr; gap: 0.3rem;
    padding: 0.18rem 0.22rem; border-bottom: 1px solid #e2e8f0;
    break-inside: avoid; font-size: 7pt;
  }
  .pattern-row .pn {
    font-family: 'JetBrains Mono', monospace; font-weight: 700;
    color: var(--track-color); font-size: 6.5pt; align-self: center;
  }
  .pattern-row .pname {
    display: block; font-weight: 700; color: #0A1628;
    font-family: 'Bricolage Grotesque', sans-serif; font-size: 7pt;
  }
  .pattern-row .psub { display: block; font-size: 6.5pt; color: #4a5568; margin-top: 0.05rem; }

  .compare-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.3rem; margin: 0.2rem 0; }
  .compare-card {
    background: var(--bg-surface); border: 1px solid #e2e8f0; border-radius: 3px;
    padding: 0.28rem 0.38rem; break-inside: avoid; font-size: 6.5pt;
  }
  .compare-card .ttl {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 7pt;
    margin-bottom: 0.15rem; padding-bottom: 0.12rem; border-bottom: 1px solid #e2e8f0;
  }
  .compare-card .row {
    display: flex; justify-content: space-between; gap: 0.3rem;
    padding: 0.1rem 0; border-bottom: 1px dotted #e2e8f0;
  }
  .compare-card .row:last-child { border-bottom: 0; }
  .compare-card .row > span:first-child { color: #4a5568; }
  .compare-card .row > span:last-child { color: #0A1628; font-weight: 600; text-align: right; }

  .col-raw  { color: #6366F1; font-weight: 700; }
  .col-sdk  { color: #10B981; font-weight: 700; }
  .col-spec { color: #B45309; font-weight: 700; }

  .track-row { display: flex; flex-wrap: wrap; gap: 0.25rem; margin: 0.15rem 0; font-size: 6.5pt; }
  .track-row .pill { background: var(--bg-surface); border: 1px solid #e2e8f0; padding: 0.04rem 0.3rem; border-radius: 999px; color: #4a5568; }

  /* === SVG diagrams === */
  .diagram-container, .agent-diagram, .analogy-svg-wrap {
    background: transparent; border: 1px solid #e2e8f0;
    border-radius: 2px; padding: 0.3rem;
    margin: 0.2rem 0; text-align: center; break-inside: avoid;
  }
  svg { max-width: 100%; max-height: 50mm; height: auto; display: block; margin: 0 auto; }
  svg [fill="#0A1628" i], svg [fill="#162033" i],
  svg [fill="#111D33" i], svg [fill="#1A2740" i] { fill: transparent; }

  /* === Track-color tinting === */
  .track-1 { --track-color: #6366F1; }
  .track-2 { --track-color: #10B981; }
  .track-3 { --track-color: #B45309; }
  .track-4 { --track-color: #7c3aed; }
  .track-5 { --track-color: #be123c; }
  .track-6 { --track-color: #2563eb; }
  .track-7 { --track-color: #0f766e; }
  .track-8 { --track-color: #be185d; }
  .track-9 { --track-color: #8a6a1a; }

  .myth { color: #be123c; font-weight: 700; }
  .reality { color: #4a5568; }

  .card-container { display: block !important; overflow: visible !important; height: auto !important; }
  .swipe-hint, .read-time, .nav-links, .desktop-btn { display: none !important; }
  .progress-dots, .progress-bar, .module-nav, .hamburger-btn { display: none !important; }
</style>
</head>
<body>
<section class="cover">
  <div class="eyebrow">Interview Study Guide &mdash; AI Agent Engineering</div>
  <h1>Building AI Agents with Claude</h1>
  <div class="meta">__MODULE_COUNT__ modules &middot; 2-column compact edition</div>
</section>
__MODULES__
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def section_anchor(mod: dict, index: int) -> str:
    return f"mod-{short_module_id(mod, index).lower()}"


def render_module(mod: dict, index: int) -> str:
    anchor = section_anchor(mod, index)
    extra_class = " first-module" if index == 1 else ""
    head = (
        f'<header class="module-head">'
        f'<span class="num">{mod["module_num"] or "Module"}</span>'
        f'<span class="track">{mod["track"]}</span>'
        f'</header>'
        f'<h1 class="module-title">{mod["title"]}</h1>'
    )
    if mod["subtitle"]:
        head += f'<p class="module-sub">{mod["subtitle"]}</p>'
    body_cols = f'<div class="module-body-cols">{mod["body"]}</div>'
    return f'<section class="module {mod["klass"]}{extra_class}" id="{anchor}">{head}{body_cols}</section>'


def render_toc(modules: list[dict]) -> str:
    rows = []
    for i, mod in enumerate(modules, 1):
        anchor = section_anchor(mod, i)
        num = short_module_id(mod, i)
        rows.append(
            f'<li class="toc-item {mod["klass"]}">'
            f'<a href="#{anchor}">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-title">{mod["title"]}</span>'
            f'</a></li>'
        )
    return (
        '<section class="toc">'
        '<h1>Table of Contents</h1>'
        '<p class="toc-hint">Modules below cover the agent-engineering scope a senior interviewer expects in 2026.</p>'
        f'<ol class="toc-list">{"".join(rows)}</ol>'
        '</section>'
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    browser = find_browser()
    files = sorted(MOBILE_DIR.glob("M*-mobile.html"), key=lambda p: order_key(p.name))
    if not files:
        sys.exit(f"No mobile HTML files found in {MOBILE_DIR}")

    print(f"Parsing {len(files)} mobile modules ...", flush=True)
    modules = []
    for f in files:
        mod = extract_module(f)
        mod["_source"] = f.name
        modules.append(mod)
        print(f"  · {f.name}", flush=True)

    # Capstone modules are pseudocode-heavy build labs — not interview material.
    modules = [m for m in modules if not is_capstone_module(m)]

    # Drop Claude Code + certification-specific modules. These are vendor-
    # and cert-specific (Claude Code config, hooks/sessions/Agent SDK, the
    # Certified Architect exam) — not core agent-engineering interview content.
    _DROPPED_PREFIXES = ("M25-", "M26-", "M27-", "M27B-")
    before = len(modules)
    modules = [m for m in modules if not m["_source"].startswith(_DROPPED_PREFIXES)]
    dropped = before - len(modules)
    if dropped:
        print(f"Dropped {dropped} Claude-Code / cert modules (M25-M27/M27B).", flush=True)

    toc = render_toc(modules)
    body_parts = [toc]
    body_parts.extend(render_module(m, i) for i, m in enumerate(modules, 1))
    body = "\n".join(body_parts)
    html_doc = HTML_TEMPLATE.replace("__MODULES__", body).replace(
        "__MODULE_COUNT__", str(len(modules))
    )

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="study-guide-pdf-", dir=OUT_PDF.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / "study-guide.html"
        tmp_html.write_text(html_doc, encoding="utf-8")
        tmp_pdf = tmp_dir / "out.pdf"
        print("Rendering PDF (compact mode) ...", flush=True)
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        # Atomic move, with .new* fallback if the canonical name is locked.
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
