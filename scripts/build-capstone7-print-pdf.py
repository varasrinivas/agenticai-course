"""Build print-friendly PDFs for the Capstone 7 series (three domains).

Capstone 7 ("Build the Same Agent Three Ways") has three domain variants:
  A — Healthcare Pre-Authorization Decision Agent
  B — B2B Order Exception Agent
  C — UCC Filing Risk Analyzer

For each, we render a print-friendly PDF that:
  1. Strips interactive chrome — sidebar, listen FAB, copy buttons, quiz,
     rubric, reflection prompts, extensions, animation play/pause controls.
  2. Drops 3 of the 5 hero animations (lanes / waterfall / time-comparison)
     which animate numbers but add little value when frozen. Keeps the two
     useful static diagrams (architecture per iteration, spec-to-code flow).
  3. Light-themes the page for paper output — same palette as the M00 print
     PDF — and forces all reveal-by-opacity elements to fully visible so
     diagrams render complete.
  4. Injects a "Three Iterations at a Glance" front-matter card right after
     the hero — a four-row side-by-side summary (lines / time / debug
     method / key insight) so the printed copy works as a stand-alone
     study reference.

Output: output/CAPSTONE-7-DOMAIN-{A,B,C}-print.pdf

Defaults to building all three; pass `--domain A` (or B/C) to render one.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
PDF_DIR    = ROOT / "output" / "pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


# ---------------------------------------------------------------------------
# Per-domain metadata (drives the front-matter "At a Glance" card)
# ---------------------------------------------------------------------------

DOMAINS: dict[str, dict] = {
    "A": {
        "src": OUTPUT_DIR / "CAPSTONE-7-DOMAIN-A.html",
        "out": PDF_DIR / "CAPSTONE-7-DOMAIN-A-print.pdf",
        "scenario": "Healthcare Pre-Authorization Decision Agent",
        "subtitle": "Build the same pre-auth agent three ways — raw API, Agent SDK + Claude Code, spec-driven.",
        "compliance": "HIPAA / PHI redaction baked in via hooks; every determination cites a policy_id.",
    },
    "B": {
        "src": OUTPUT_DIR / "CAPSTONE-7-DOMAIN-B.html",
        "out": PDF_DIR / "CAPSTONE-7-DOMAIN-B-print.pdf",
        "scenario": "B2B Order Exception Agent",
        "subtitle": "Build the same order-exception agent three ways — raw API, Agent SDK + Claude Code, spec-driven.",
        "compliance": "Tier-aware tone enforcement (ENTERPRISE vs SMB) and overpromise detection in PostToolUse hooks.",
    },
    "C": {
        "src": OUTPUT_DIR / "CAPSTONE-7-DOMAIN-C.html",
        "out": PDF_DIR / "CAPSTONE-7-DOMAIN-C-print.pdf",
        "scenario": "UCC Filing Risk Analyzer",
        "subtitle": "Build the same filing-risk agent three ways — raw API, Agent SDK + Claude Code, spec-driven.",
        "compliance": "Name-variant search + lien-risk scoring; query results must trace back to source filings.",
    },
}


# ---------------------------------------------------------------------------
# Sections we remove entirely from the printed PDF
# ---------------------------------------------------------------------------

STRIP_SECTION_IDS = (
    "anim-lanes",       # numbers-animation, no value as a static
    "anim-waterfall",   # bar-chart that animates in — keep as table elsewhere
    "anim-time",        # animated timeline; the comparison table covers this
    "anim-spec",        # JS-dependent (empty placeholders without script run)
    "rubric",           # grading rubric — instructional only, not study material
    "reflection",       # interactive reflection prompts
    "quiz",             # quiz section (multi-class id so we match by id)
    "extensions",       # "going further" suggestions, not core
)

# Sidebar anchor ids we clean up after stripping their target sections.
STRIPPED_ANCHORS = STRIP_SECTION_IDS + (
    # H3-level debugging anchors are kept (their target sections are kept).
    # Animation sub-anchors are gone with their parent sections.
)


def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("Could not find Chrome or Edge. Install one or edit CHROME_CANDIDATES.")


# ---------------------------------------------------------------------------
# Print CSS overrides — light theme, compact, single-column
# ---------------------------------------------------------------------------

PRINT_OVERRIDES_CSS = r"""
<style id="pdf-print-overrides">
  @page { size: A4; margin: 10mm 11mm 12mm 11mm; }

  html, body {
    background: #ffffff !important;
    color: #1a1f2e !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    font-size: 9.8pt !important;
    line-height: 1.42 !important;
  }

  /* Light-mode CSS variable overrides — same palette as the M00 print PDF */
  :root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-card: #ffffff;
    --bg-surface: #f1f5f9;
    --text-primary: #1a1f2e;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --code-bg: #f6f8fa;
    --code-border: #d0d7de;
    --code-text: #1a1f2e;
    --accent-primary: #b8860b;
    --accent-hover: #9a7209;
    --success: #047857;
    --warning: #b45309;
    --error: #be123c;
    --info: #2563eb;
    --purple: #7c3aed;
    --iter1: #be123c;
    --iter2: #2563eb;
    --iter3: #047857;
  }

  /* Hide interactive chrome */
  .top-progress,
  .sidebar-toggle,
  .sidebar-nav,
  .listen-fab,
  .listen-panel,
  .animation-controls,
  .copy-btn,
  button.copy,
  .module-nav,
  .term-tooltip .tooltip-content {
    display: none !important;
  }

  /* Collapse the two-column grid to single column */
  .page-container { display: block !important; max-width: 100% !important; padding: 0 !important; gap: 0 !important; }
  .content { max-width: 100% !important; }

  /* Course / capstone header — keep simplified */
  .course-header {
    background: #f8fafc !important;
    border-bottom: 1px solid #cbd5e1 !important;
    padding: 0.4rem 0.9rem !important;
    margin-bottom: 0.7rem !important;
  }
  .course-title, .header-meta { color: #334155 !important; }
  .track-badge { background: rgba(124,58,237,0.10) !important; color: #6d28d9 !important; border-color: #6d28d9 !important; }
  .track-badge .dot { background: #6d28d9 !important; }

  /* Headings */
  h1, h2, h3, h4 { color: #0A1628 !important; page-break-after: avoid; }
  h1 { font-size: 18pt !important; line-height: 1.18 !important; }
  h2 { font-size: 13.5pt !important; line-height: 1.22 !important; border-top: 1px solid #cbd5e1 !important; padding-top: 0.55rem !important; margin-top: 0.7rem !important; }
  h2:first-of-type { border-top: 0 !important; padding-top: 0 !important; margin-top: 0 !important; }
  h3 { font-size: 11pt !important; line-height: 1.26 !important; margin-top: 0.5rem !important; }
  h4 { font-size: 10.5pt !important; }

  /* Body */
  p, li, td, th { color: #1a1f2e !important; }
  p { margin: 0 0 0.4rem !important; }
  ul, ol { margin: 0.3rem 0 0.5rem 1.1rem !important; padding: 0 !important; }
  li { margin: 0 0 0.2rem !important; }
  a { color: #2563eb !important; }
  code { background: #f1f5f9 !important; color: #b45309 !important; border: 1px solid #e2e8f0 !important;
         padding: 0.05rem 0.3rem !important; border-radius: 3px !important; font-size: 8.6pt !important; }

  /* Iteration banners — anchor the iteration, attach to next content.
     `page-break-after: avoid` + `break-after: avoid-page` tell the engine
     to keep this banner glued to whatever comes next (no orphaned banner). */
  .iter-header {
    background: #fafbfc !important;
    border: 1px solid !important;
    border-radius: 8px !important;
    padding: 0.7rem 0.9rem !important;
    margin: 1rem 0 0.7rem !important;
    page-break-after: avoid !important;
    break-after: avoid-page !important;
    page-break-inside: avoid;
  }
  .iter-header.iter-1 { border-color: #be123c !important; background: rgba(244,63,94,0.06) !important; }
  .iter-header.iter-2 { border-color: #2563eb !important; background: rgba(59,130,246,0.06) !important; }
  .iter-header.iter-3 { border-color: #047857 !important; background: rgba(16,185,129,0.06) !important; }
  .iter-header h2 { font-size: 16pt !important; margin: 0.2rem 0 0.3rem !important; border-top: 0 !important; padding-top: 0 !important; }
  .iter-header.iter-1 h2 { color: #be123c !important; }
  .iter-header.iter-2 h2 { color: #2563eb !important; }
  .iter-header.iter-3 h2 { color: #047857 !important; }
  .iter-meta {
    display: flex; flex-wrap: wrap; gap: 0.8rem; font-size: 8.6pt !important; color: #475569 !important;
    margin-top: 0.4rem !important;
  }
  .iter-meta span { background: rgba(0,0,0,0.04) !important; padding: 0.1rem 0.45rem !important; border-radius: 999px; }

  /* Pills (iteration tags + general) */
  .pill {
    display: inline-block; font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 7.8pt; padding: 0.1rem 0.5rem; border-radius: 999px;
    letter-spacing: 0.04em; text-transform: uppercase;
  }
  .pill-iter1 { background: rgba(244,63,94,0.13) !important; color: #be123c !important; }
  .pill-iter2 { background: rgba(59,130,246,0.13) !important; color: #2563eb !important; }
  .pill-iter3 { background: rgba(16,185,129,0.13) !important; color: #047857 !important; }

  /* Steps (each step inside an iteration)
     IMPORTANT: do NOT page-break-inside: avoid. Steps often contain large
     code blocks; if the whole step has to fit on one page, the iter-header
     above it ends up stranded alone on a page (looks like the iteration
     section has no content). Let steps split naturally; protect their
     headers from being orphaned via orphans/widows + page-break-after. */
  .step {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 3px solid #cbd5e1 !important;
    border-radius: 4px;
    padding: 0.55rem 0.75rem !important;
    margin: 0.55rem 0 !important;
    orphans: 3; widows: 3;
  }
  .step-header, .step-meta {
    page-break-after: avoid;
    break-after: avoid-page;
  }
  .step-header {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 10.5pt;
    color: #0A1628 !important; margin-bottom: 0.15rem !important;
  }
  .step-meta {
    display: flex; flex-wrap: wrap; gap: 0.5rem; font-size: 8pt; color: #64748b;
    margin-bottom: 0.4rem;
  }
  .step-meta span { background: #f1f5f9 !important; padding: 0.05rem 0.4rem !important; border-radius: 3px; }

  /* Callouts — keep tint on light bg */
  .analogy-box, .tech-def-box, .callout-why, .callout-warning,
  .callout-security, .callout-cost, .callout-cert, .callout-info {
    color: #1a1f2e !important;
    padding: 0.5rem 0.7rem !important;
    margin: 0.5rem 0 !important;
    page-break-inside: avoid;
    border-radius: 0 4px 4px 0;
  }
  .analogy-box     { background: rgba(184,134,11,0.07) !important; border-left: 3px solid #b8860b !important; }
  .tech-def-box    { background: rgba(59,130,246,0.07) !important; border-left: 3px solid #2563eb !important; }
  .callout-why     { background: rgba(16,185,129,0.07) !important; border-left: 3px solid #059669 !important; }
  .callout-warning { background: rgba(245,158,11,0.09) !important; border-left: 3px solid #d97706 !important; }
  .callout-security{ background: rgba(244,63,94,0.07)  !important; border-left: 3px solid #be123c !important; }
  .callout-cost    { background: rgba(184,134,11,0.06) !important; border-left: 3px solid #b8860b !important; }
  .callout-cert    { background: rgba(184,134,11,0.06) !important; border-left: 3px solid #b8860b !important; }
  .callout-info    { background: rgba(59,130,246,0.06) !important; border-left: 3px solid #2563eb !important; }
  .box-label {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
    font-size: 8pt; letter-spacing: 0.08em; text-transform: uppercase;
    display: block; margin-bottom: 0.2rem;
  }

  /* Term tooltip — show the dotted underline only, popups are killed above */
  .term-tooltip { color: #b45309 !important; border-bottom: 1px dotted #b45309 !important; }

  /* Bridge sentence */
  .bridge {
    font-style: italic; color: #475569 !important;
    background: #f8fafc !important; border-left: 2.5px solid #cbd5e1 !important;
    padding: 0.4rem 0.7rem !important; margin: 0.5rem 0 !important;
    font-size: 9.4pt !important;
    page-break-inside: avoid;
  }

  /* === Code blocks — rendered as PSEUDOCODE-AESTHETIC for print ===
     Same visual idea as the mobile pseudocode card: subtle indigo-tinted
     background, accent left border, monospace, comment-muted, no syntax
     highlighting. Reads more like an outlined algorithm than IDE code. */
  .code-block-wrapper {
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    margin: 0.4rem 0 !important;
    overflow: visible !important;
    page-break-inside: avoid;
  }
  /* Tabs row: show the file/snippet label as a small uppercase eyebrow,
     not as clickable buttons. Multi-tab examples keep all tabs side-by-side. */
  .code-tabs {
    background: transparent !important;
    border: 0 !important;
    padding: 0 0 0.15rem 0 !important;
    margin: 0 !important;
    font-size: 7.6pt !important;
    display: flex; flex-wrap: wrap; gap: 0.5rem;
  }
  .code-tab {
    background: transparent !important; color: #6d28d9 !important;
    border: 0 !important; padding: 0 !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 700 !important; font-size: 7.4pt !important;
    text-transform: uppercase; letter-spacing: 0.06em;
    cursor: default !important;
  }
  .code-tab.active { color: #5b21b6 !important; }
  .code-tab + .code-tab::before { content: " · "; color: #cbd5e1; margin-right: 0.5rem; }

  /* Show all panels stacked (instead of only the active tab) so multi-tab
     examples don't lose information in print. */
  .code-panel { display: block !important; position: relative; margin: 0.15rem 0 0.3rem !important; }
  .code-panel pre {
    margin: 0 !important;
    padding: 0.42rem 0.6rem !important;
    overflow: visible !important;
    white-space: pre-wrap !important; word-break: break-word !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 7.2pt !important; line-height: 1.5 !important;
    color: #1a1f2e !important;
    background: rgba(99,102,241,0.05) !important;
    border-left: 2.5px solid #6366F1 !important;
    border-radius: 0 3px 3px 0 !important;
  }
  .code-panel pre code {
    background: transparent !important; color: inherit !important;
    border: 0 !important; padding: 0 !important; font-size: inherit !important;
    font-family: inherit !important;
  }
  /* Comment lines (injected by the Python pre-processor as `<span class="cmt">`)
     get a muted italic style — the mobile pseudocode convention. */
  .code-panel pre .cmt { color: #6b7280 !important; font-style: italic; }
  /* Pseudocode keywords (FUNCTION, IF, FOR, RETURN, etc.) — uppercased and
     wrapped by _pseudocodify_all. Color them violet for visual rhythm. */
  .code-panel pre .kw { color: #7c3aed !important; font-weight: 700; }
  /* Multi-panel examples (Python tab + TypeScript tab side by side): show
     each panel's title inline so the reader knows which language. */
  .code-panel[id]::before {
    content: attr(data-lang);
    display: block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 6.8pt; letter-spacing: 0.08em;
    text-transform: uppercase; color: #6d28d9;
    margin: 0 0 0.12rem;
  }

  /* === Architecture diagrams (plain HTML/CSS replacement for anim-arch) ===
     We strip the source's ASCII-art + tab system and inject three clean
     iteration-colored cards via replace_arch_animation(). Style them here. */
  .arch-card-stack { display: flex; flex-direction: column; gap: 0.7rem; margin: 0.4rem 0 0.6rem; }
  .arch-card {
    border: 2px solid; border-radius: 8px;
    padding: 0.55rem 0.75rem;
    page-break-inside: avoid;
  }
  .arch-card.arch-1 { border-color: #be123c; background: rgba(244,63,94,0.04) !important; }
  .arch-card.arch-2 { border-color: #2563eb; background: rgba(59,130,246,0.04) !important; }
  .arch-card.arch-3 { border-color: #047857; background: rgba(16,185,129,0.04) !important; }
  .arch-head {
    display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.5rem;
    border-bottom: 1px solid rgba(0,0,0,0.07);
    padding-bottom: 0.32rem; margin-bottom: 0.45rem;
  }
  .arch-num {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
    font-size: 8.4pt; letter-spacing: 0.08em;
    padding: 0.1rem 0.45rem; border-radius: 3px;
  }
  .arch-card.arch-1 .arch-num { color: #fff; background: #be123c; }
  .arch-card.arch-2 .arch-num { color: #fff; background: #2563eb; }
  .arch-card.arch-3 .arch-num { color: #fff; background: #047857; }
  .arch-name {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
    font-size: 12pt; color: #0A1628;
  }
  .arch-own {
    margin-left: auto; font-size: 7.6pt; color: #475569;
    font-style: italic; white-space: nowrap;
  }
  .arch-main {
    background: #ffffff; border: 1px solid #d4dae3; border-radius: 4px;
    padding: 0.4rem 0.55rem; margin: 0.3rem 0;
  }
  .arch-main-title {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    font-size: 9.5pt; color: #0A1628; margin-bottom: 0.25rem;
  }
  .arch-size {
    font-family: 'Source Sans 3', sans-serif; font-weight: 400;
    font-size: 7.6pt; color: #64748b; font-style: italic;
  }
  .arch-flow {
    list-style: none; padding: 0; margin: 0;
    font-family: 'JetBrains Mono', monospace; font-size: 7.4pt; line-height: 1.55;
    color: #1a1f2e;
  }
  .arch-flow > li { padding: 0.05rem 0; margin: 0; }
  .arch-substeps {
    list-style: none; padding: 0 0 0 1.2rem; margin: 0.05rem 0 0;
    font-size: 7.2pt; color: #475569;
  }
  .arch-substeps li { padding: 0; }
  .arch-kw { color: #7c3aed; font-weight: 700; margin-right: 0.2rem; }
  .arch-call { color: #b45309; font-weight: 600; }
  .arch-note {
    margin-left: 0.6rem; font-style: italic; color: #6b7280;
    font-family: 'Source Sans 3', sans-serif; font-size: 7pt;
  }
  .arch-note-block {
    font-size: 7.6pt; color: #475569; font-style: italic;
    line-height: 1.42; margin-top: 0.3rem;
  }
  .arch-fanout {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.35rem;
    margin: 0.35rem 0;
  }
  .arch-fanout-2col { grid-template-columns: repeat(2, 1fr) !important; }
  .arch-leaf {
    background: #ffffff; border: 1px solid #d4dae3; border-radius: 4px;
    padding: 0.32rem 0.45rem;
    display: flex; flex-direction: column; gap: 0.1rem;
  }
  .arch-leaf-name {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    font-size: 8pt; color: #0A1628;
  }
  .arch-leaf-note {
    font-size: 7pt; color: #64748b; font-style: italic;
  }
  .arch-leaf-list {
    font-family: 'JetBrains Mono', monospace; font-size: 6.6pt; color: #1a1f2e;
    line-height: 1.45;
  }
  .arch-deploy {
    margin-top: 0.25rem; padding: 0.3rem 0.55rem;
    background: #ffffff; border: 1px dashed #d4dae3; border-radius: 4px;
    font-size: 7.8pt; color: #1a1f2e;
  }
  .arch-arrow {
    text-align: center; font-size: 14pt; color: #94a3b8;
    line-height: 1; margin: 0.15rem 0;
  }
  .arch-spec-sections {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.18rem 0.7rem;
    font-family: 'JetBrains Mono', monospace; font-size: 7.4pt; color: #1a1f2e;
    margin-top: 0.2rem;
  }

  /* Tables — denser */
  table, .compare-table, .info-table {
    width: 100%; border-collapse: collapse;
    background: #ffffff !important; border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important; font-size: 8.4pt !important;
    margin: 0.5rem 0 !important; page-break-inside: avoid;
  }
  th, td {
    padding: 0.3rem 0.5rem !important; border-bottom: 1px solid #e2e8f0 !important;
    vertical-align: top !important; color: #1a1f2e !important;
  }
  thead th { background: #f1f5f9 !important; color: #0A1628 !important;
             font-family: 'Bricolage Grotesque', sans-serif !important; font-weight: 700 !important;
             font-size: 8pt !important; text-transform: uppercase; letter-spacing: 0.03em; }

  /* Debug-block + debug-method (the structure we just fixed in the source) */
  .debug-block {
    background: rgba(124,58,237,0.05) !important;
    border: 1px solid #c4b5fd !important;
    border-radius: 8px !important;
    padding: 0.7rem 0.85rem !important;
    margin: 0.8rem 0 !important;
    page-break-inside: avoid;
  }
  .debug-block h3 { color: #6d28d9 !important; margin: 0 0 0.4rem !important; font-size: 12pt !important; }
  .debug-method {
    background: #ffffff !important;
    border-left: 2.5px solid #7c3aed !important;
    border-radius: 0 4px 4px 0;
    padding: 0.45rem 0.7rem !important;
    margin: 0.4rem 0 !important;
    page-break-inside: avoid;
  }
  .debug-method-title {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    color: #6d28d9 !important; font-size: 9.5pt; margin-bottom: 0.25rem;
  }

  /* "Three Iterations at a Glance" front-matter card we inject */
  .at-a-glance {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
    padding: 0.6rem 0.7rem !important;
    margin: 0.6rem 0 1rem !important;
    page-break-inside: avoid;
  }
  .at-a-glance .glance-title {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
    font-size: 11.5pt; color: #0A1628; margin: 0 0 0.4rem;
    letter-spacing: -0.005em;
  }
  .at-a-glance .glance-sub {
    font-size: 8.6pt; color: #64748b; margin: 0 0 0.45rem; font-style: italic;
  }
  .glance-grid {
    display: grid; grid-template-columns: 100px repeat(3, 1fr); gap: 0;
    border-top: 1px solid #e2e8f0; font-size: 8.6pt;
  }
  .glance-grid > div {
    padding: 0.32rem 0.45rem;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
  }
  .glance-grid > div:nth-child(4n) { border-right: 0; }
  .glance-grid .glance-row-header {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    background: #f8fafc; color: #334155; font-size: 8pt;
    letter-spacing: 0.04em; text-transform: uppercase;
  }
  .glance-grid .glance-col-1 { background: rgba(244,63,94,0.04); }
  .glance-grid .glance-col-2 { background: rgba(59,130,246,0.04); }
  .glance-grid .glance-col-3 { background: rgba(16,185,129,0.04); }
  .glance-grid .glance-col-head {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
    font-size: 9.5pt; padding: 0.4rem 0.45rem;
  }
  .glance-grid .glance-col-head.glance-col-1 { color: #be123c; }
  .glance-grid .glance-col-head.glance-col-2 { color: #2563eb; }
  .glance-grid .glance-col-head.glance-col-3 { color: #047857; }

  /* Force every reveal-by-opacity to visible (architecture animation, etc.) */
  .arch-block, .lifecycle-stage, .ccd-box, .wf-step, .roadmap-track, .demo-step,
  .step, .lane, .iter-card, .compare-row {
    opacity: 1 !important; transform: none !important; animation: none !important; transition: none !important;
  }
  .arch-grid, .lifecycle-flow, .workflow-steps, .claude-code-diagram {
    min-height: auto !important;
  }
  svg [opacity="0"], svg [opacity="0.0"], svg [opacity="0.3"] { opacity: 1 !important; }

  /* Animation containers — light card */
  .animation-container {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
    overflow: visible !important;
    min-height: auto !important;
    padding: 0.55rem 0.7rem !important;
    margin: 0.5rem 0 !important;
    page-break-inside: avoid;
  }
  .animation-container .animation-title { color: #475569 !important; font-weight: 700 !important; font-size: 9pt; }
  .animation-container svg {
    max-width: 100% !important; max-height: 145mm !important; height: auto !important; display: block; margin: 0 auto;
  }

  /* Page-break rules — let content flow naturally.
     We deliberately do NOT force a page-break-before on iterations, because
     pairing that with .step's previous page-break-inside-avoid stranded
     iter-headers alone on a page. The strong .iter-header banner is enough
     of a visual anchor; the eye finds it inside continuous flow. */
  section.section { page-break-before: auto; }

  /* Reduce-motion safety net */
  *, *::before, *::after { animation-duration: 0.001s !important; transition-duration: 0.001s !important; }
</style>
"""


# ---------------------------------------------------------------------------
# Finalize JS — light all reveal-by-opacity elements, remap dark SVG fills
# ---------------------------------------------------------------------------

PRINT_FINALIZE_JS = r"""
<script id="pdf-print-finalize">
  (function () {
    // Dark SVG fills -> light backgrounds (mirrors M00 print pass).
    var DARK_FILL_REMAP = {
      '#0a1628': '#ffffff', '#1a2740': '#f1f5f9', '#162033': '#f8fafc',
      '#111d33': '#f8fafc', '#2a2a3e': '#f1f5f9', '#1a1a2e': '#ffffff',
      '#1e3a5f': '#dbeafe', '#3a3a3a': '#e5e7eb', '#3a2a5e': '#ede9fe',
      '#21262d': '#e2e8f0', '#0d1117': '#f8fafc'
    };
    var LIGHT_TEXT_REMAP = {
      '#e8ecf1': '#0A1628', '#fff': '#0A1628', '#ffffff': '#0A1628',
      '#ddd': '#0A1628', '#dddddd': '#0A1628',
      '#aaa': '#475569', '#aaaaaa': '#475569', '#888': '#475569', '#888888': '#475569',
      '#b8b0f0': '#5b21b6', '#7fdecc': '#065f46', '#f0d98c': '#92400e', '#f0a090': '#9a3412'
    };
    function norm(v) { return v ? String(v).trim().toLowerCase() : ''; }
    function remap(el, attr, table) {
      var v = norm(el.getAttribute(attr));
      if (v && table[v]) el.setAttribute(attr, table[v]);
      var s = el.getAttribute('style');
      if (s && /\bfill\s*:\s*#[0-9a-fA-F]+/i.test(s)) {
        var ns = s.replace(/\bfill\s*:\s*(#[0-9a-fA-F]+)/gi, function (_, h) {
          var k = h.toLowerCase(); return 'fill:' + (table[k] || h);
        });
        if (ns !== s) el.setAttribute('style', ns);
      }
    }
    function recolorSvgs() {
      document.querySelectorAll('.animation-container svg, .iter-arch-svg, .spec-flow-svg').forEach(function (svg) {
        svg.querySelectorAll('rect, circle, ellipse, path, polygon, g').forEach(function (e) { remap(e, 'fill', DARK_FILL_REMAP); });
        svg.querySelectorAll('text, tspan').forEach(function (e) { remap(e, 'fill', LIGHT_TEXT_REMAP); });
      });
    }
    function finalize() {
      // Light every animation step / lit element used by interactive driver scripts.
      ['.arch-block', '.lifecycle-stage', '.ccd-box', '.wf-step',
       '.roadmap-track', '.demo-step', '.lane', '.iter-card', '.compare-row',
       '.step'].forEach(function (sel) {
        document.querySelectorAll(sel).forEach(function (el) {
          el.classList.add('lit', 'visible', 'playing');
          el.style.opacity = '1'; el.style.transform = 'none';
        });
      });
      document.querySelectorAll('.animation-container').forEach(function (el) { el.classList.add('playing'); });
      recolorSvgs();
      // Stop any rAF / setTimeout loops the source page might have queued.
      var maxId = setTimeout(function () {}, 0);
      for (var t = 0; t < maxId; t++) {
        try { clearTimeout(t); clearInterval(t); } catch (e) {}
      }
      // Close listen panel if a startup script opened it.
      var lp = document.getElementById('listenPanel'); if (lp) { lp.style.display = 'none'; }
      var lf = document.getElementById('listenFab');   if (lf) { lf.style.display = 'none'; }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', finalize);
    } else {
      finalize();
    }
    setTimeout(finalize, 700);
  })();
</script>
"""


# ---------------------------------------------------------------------------
# Code-block pre-processor: comment lines get a .cmt span, panels get a
# data-lang attribute derived from the tab they belong to.
# ---------------------------------------------------------------------------

# ---- Pseudocode converter ---------------------------------------------------
#
# For Python / TypeScript / JavaScript blocks we transform the source to a
# compact pseudocode-style representation:
#   • Strip triple-quoted docstrings.
#   • Strip param type hints (`x: int` -> `x`).
#   • Strip `await` and `async` keywords.
#   • UPPERCASE flow keywords and wrap them in <span class="kw"> for color.
#   • Strip @decorators except `@tool` (the @tool name carries meaning).
#   • Drop redundant `pass` lines.
#   • Collapse runs of blank lines to a single blank.
#   • If the block is > 25 lines, keep first 14 + ellipsis + last 6.
#
# JSON / shell / Dockerfile / markdown blocks are left verbatim.

_LANG_CODE_LIKE = {"python", "py", "typescript", "ts", "javascript", "js", "jsx", "tsx"}

# Languages we explicitly SKIP — leave their blocks verbatim (no pseudocode).
_LANG_SKIP = {
    "json", "jsonc", "yaml", "yml", "toml", "ini", "env",
    "bash", "sh", "shell", "zsh", "fish", "powershell", "ps1",
    "dockerfile", "css", "scss", "html", "xml", "svg",
    "sql", "graphql", "markdown", "md", "text", "txt", "plaintext",
}

# Full-block signal patterns — any match anywhere in the block means "this is code".
# Anchored to start-of-line (re.MULTILINE) to avoid false positives in prose.
_CODE_SIGNAL_RE = re.compile(
    r"^\s*(async\s+)?def\s+\w+\s*\("           # Python function def
    r"|^\s*class\s+\w+"                         # Python / TS class
    r"|^\s*from\s+[\w.]+\s+import\b"            # Python import
    r"|^\s*import\s+[\w{'\"]"                   # Python / JS/TS import
    r"|^\s*(export\s+)?(const|let|var)\s+\w+"   # JS/TS variable declaration
    r"|^\s*(export\s+)?(async\s+)?function\s+\w+" # JS/TS function declaration
    r"|^\s*interface\s+\w+\s*[{<]"             # TS interface
    r"|^\s*type\s+\w+\s*="                      # TS type alias
    r"|^\s*@\w+"                                 # Python/TS decorator
    r"|\bclient\.messages\.create\b"             # Anthropic API call
    r"|\banthropc\.Anthropic\b"                  # client = anthropic.Anthropic(
    r"|\bclaude_agent_sdk\b"                     # Agent SDK import
    r"|\bquery\s*\(\s*prompt"                    # SDK query() call
    r"|\bClaudeAgentOptions\b"                   # SDK options class
    r"|^\s*\w+\s*=\s*\{$",                      # dict/object literal start
    re.MULTILINE,
)

# Rules are anchored to syntactic context wherever possible so we don't
# accidentally rewrite plain English words like "in" or "new" inside comments
# or strings. Order matters: longer/multi-word rules first.
_PY_KW_RULES = [
    # Function / class definitions (Python and JS/TS)
    (re.compile(r"\basync\s+def\s+(\w+)"), r"FUNCTION \1"),
    (re.compile(r"\bdef\s+(\w+)"), r"FUNCTION \1"),
    (re.compile(r"\bfunction\s+(\w+)"), r"FUNCTION \1"),   # JS/TS
    (re.compile(r"\bclass\s+(\w+)"), r"CLASS \1"),
    # Control flow with anchors (colon or end-of-line) so we don't rewrite
    # the same word inside comments / strings.
    (re.compile(r"\belif\s+"), r"ELIF "),
    (re.compile(r"(?<=[\s\(])if\s+"), r"IF "),
    (re.compile(r"^if\s+", re.M), r"IF "),
    (re.compile(r"\belse\s*:"), r"ELSE:"),
    # `for X in Y:` -> `FOR X IN Y:` — single rule handles both kw transforms
    (re.compile(r"\bfor\s+([^:\n]+?)\s+in\s+"), r"FOR \1 IN "),
    (re.compile(r"\bwhile\s+"), r"WHILE "),
    (re.compile(r"^\s*return\b", re.M), lambda m: m.group(0).replace("return", "RETURN")),
    (re.compile(r"^\s*yield\b", re.M), lambda m: m.group(0).replace("yield", "YIELD")),
    (re.compile(r"^\s*try\s*:", re.M), lambda m: m.group(0).replace("try", "TRY")),
    (re.compile(r"\bexcept(\s+\w+)?(\s+as\s+\w+)?\s*:"), r"CATCH:"),
    (re.compile(r"\bfinally\s*:"), r"FINALLY:"),
    (re.compile(r"^\s*with\s+", re.M), lambda m: m.group(0).replace("with", "WITH")),
    (re.compile(r"^\s*import\s+", re.M), lambda m: m.group(0).replace("import", "IMPORT")),
    (re.compile(r"^\s*from\s+"), r"FROM "),
    (re.compile(r"^\s*raise\s+", re.M), lambda m: m.group(0).replace("raise", "RAISE")),
    (re.compile(r"^\s*break\s*$", re.M), lambda m: m.group(0).replace("break", "BREAK")),
    (re.compile(r"^\s*continue\s*$", re.M), lambda m: m.group(0).replace("continue", "CONTINUE")),
    # JS/TS variable declarations — anchored to line start so `const` inside a
    # string mid-line doesn't get rewritten. `export const` is handled by stripping
    # the export keyword first via the broader line-start anchor.
    (re.compile(r"^\s*export\s+const\s+", re.M), lambda m: m.group(0).replace("const", "CONST")),
    (re.compile(r"^\s*export\s+let\s+", re.M), lambda m: m.group(0).replace("let", "LET")),
    (re.compile(r"^\s*const\s+", re.M), lambda m: m.group(0).replace("const", "CONST")),
    (re.compile(r"^\s*let\s+", re.M), lambda m: m.group(0).replace("let", "LET")),
    # TS interface / type alias
    (re.compile(r"^\s*export\s+interface\s+", re.M), lambda m: m.group(0).replace("interface", "INTERFACE")),
    (re.compile(r"^\s*interface\s+(\w+)", re.M), r"INTERFACE \1"),
    (re.compile(r"^\s*export\s+type\s+(\w+)", re.M), r"TYPE \1"),
    (re.compile(r"^\s*type\s+(\w+)\s*=", re.M), r"TYPE \1 ="),
    # JS/TS only — never rewrite a generic word `new`; require `new SomeIdentifier(`
    (re.compile(r"\bnew\s+([A-Z]\w*\()"), r"NEW \1"),
    # Strip async / await markers
    (re.compile(r"\bawait\s+"), r""),
    (re.compile(r"\basync\s+"), r""),
]

# Words we recognize as the uppercased keywords; we wrap these for CSS color.
_KW_HIGHLIGHT_RE = re.compile(
    r"\b(FUNCTION|CLASS|IF|ELIF|ELSE|FOR|WHILE|IN|RETURN|YIELD|TRY|CATCH|FINALLY|"
    r"WITH|IMPORT|FROM|RAISE|BREAK|CONTINUE|NEW|CONST|LET|INTERFACE|TYPE)\b"
)

# Strip Python type hints: `x: SomeType = ...` -> `x = ...`,
# and `-> ReturnType` -> ``. Conservative: only inside parens for def args,
# and trailing `-> X:` at end of signature.
_PY_TYPED_PARAM_RE = re.compile(r"(\w+)\s*:\s*[\w\[\],\.\s\"\'\|]+?(?=[,\)=])")
_PY_RETURN_HINT_RE = re.compile(r"\s*->\s*[\w\[\],\.\s\"\'\|]+?(?=:)")

# Triple-quoted docstrings (single or double, on their own block).
_DOCSTRING_RE = re.compile(r'^(\s*)"""[\s\S]*?"""\s*$', re.MULTILINE)
_DOCSTRING_SINGLE_RE = re.compile(r"^(\s*)'''[\s\S]*?'''\s*$", re.MULTILINE)

# Strip @decorator lines except @tool (which carries domain meaning).
_DECORATOR_RE = re.compile(r"^\s*@(?!tool\b)\w[\w\.]*\(?[^)\n]*\)?\s*$", re.MULTILINE)


def _looks_like_code(lang: str | None, code_text: str) -> bool:
    if lang:
        lang_lower = lang.lower()
        if lang_lower in _LANG_CODE_LIKE:
            return True
        if lang_lower in _LANG_SKIP:
            return False
    # No explicit lang (or unrecognized lang): scan the FULL block for structural
    # code signals. This catches blocks that begin with comments, blank lines, or
    # setup code before the first def/import/class.
    return bool(_CODE_SIGNAL_RE.search(code_text))


def _to_pseudocode(code_text: str) -> str:
    """Transform Python/JS/TS source into compact pseudocode."""
    text = code_text

    # 1. Strip docstrings.
    text = _DOCSTRING_RE.sub(r"\1", text)
    text = _DOCSTRING_SINGLE_RE.sub(r"\1", text)

    # 2. Strip non-`@tool` decorators.
    text = _DECORATOR_RE.sub("", text)

    # 3. Strip type hints (Python style; harmless on JS/TS where same syntax).
    text = _PY_RETURN_HINT_RE.sub("", text)
    text = _PY_TYPED_PARAM_RE.sub(r"\1", text)

    # 4. Apply keyword rewrites line-by-line. Skip lines that are entirely
    #    comments or string literals so we don't rewrite plain English words
    #    inside `#` / `//` comments or quoted strings.
    new_lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped:
            new_lines.append(line)
            continue
        # Skip pure-comment and pure-string-literal lines.
        if stripped.startswith(("#", "//", "'", '"')):
            new_lines.append(line)
            continue
        new_line = line
        for pat, repl in _PY_KW_RULES:
            new_line = pat.sub(repl, new_line)
        new_lines.append(new_line)
    text = "\n".join(new_lines)

    # 5. Drop bare `pass` lines (now meaningless after stripping bodies).
    text = re.sub(r"^\s*pass\s*$", "", text, flags=re.MULTILINE)

    # 6. Collapse runs of blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 7. Trim leading/trailing blank lines.
    text = text.strip("\n")

    # 8. Length cap.
    lines = text.split("\n")
    if len(lines) > 25:
        head = lines[:14]
        tail = lines[-6:]
        text = "\n".join(head + ["", "    # … (full source in the desktop HTML) …", ""] + tail)

    return text


def _wrap_keywords(text: str) -> str:
    """Wrap UPPERCASED keywords (post-conversion) in <span class="kw">."""
    return _KW_HIGHLIGHT_RE.sub(r'<span class="kw">\1</span>', text)


def _detect_lang_from_pre(pre_open_tag: str) -> str | None:
    """Pull language=X from `<pre><code class="language-X">` if present."""
    m = re.search(r'class="[^"]*\blanguage-(\w+)', pre_open_tag)
    return m.group(1).lower() if m else None


def _pseudocodify_all(html: str) -> str:
    """For every <pre><code>...</code></pre> block, convert Python/JS/TS to
    pseudocode and wrap UPPERCASE keywords in span.kw. Leave non-code blocks
    (JSON, shell, Dockerfile, markdown) verbatim."""
    pre_re = re.compile(r"(<pre[^>]*>)(<code[^>]*>)([\s\S]*?)(</code></pre>)")

    def transform(match):
        pre_open, code_open, body, closing = match.group(1), match.group(2), match.group(3), match.group(4)
        # Unescape minimal HTML entities so regex can work on real text.
        unesc = body.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
        lang = _detect_lang_from_pre(code_open) or _detect_lang_from_pre(pre_open)
        if not _looks_like_code(lang, unesc):
            return match.group(0)   # leave non-code as-is
        new_text = _to_pseudocode(unesc)
        # Re-escape <, >, & in the rendered output so HTML doesn't see them.
        # Keep our injected <span class="kw"> tags intact by wrapping AFTER.
        escaped = new_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        wrapped = _wrap_keywords(escaped)
        return pre_open + code_open + wrapped + closing

    return pre_re.sub(transform, html)


def _wrap_comments_in_code(html: str) -> str:
    """For every <pre><code>...</code></pre>, wrap leading-`#` and leading-`//`
    comment lines (whole-line comments only) in `<span class="cmt">...</span>`
    so the print CSS can mute them like mobile pseudocode does.

    Whole-line only: an inline trailing `# note` won't be wrapped, to avoid
    splitting URLs that contain `#` and to keep the regex robust.
    """
    pre_re = re.compile(r"(<pre[^>]*><code[^>]*>)(.*?)(</code></pre>)", re.DOTALL)

    def transform(match):
        opening, body, closing = match.group(1), match.group(2), match.group(3)
        lines = body.split("\n")
        out_lines = []
        for line in lines:
            stripped = line.lstrip()
            indent = line[: len(line) - len(stripped)]
            # Skip lines that are HTML-encoded entities like &gt; (Claude Code
            # prompt indicator) — those aren't comments.
            if stripped.startswith("#") and not stripped.startswith("##"):
                out_lines.append(f'{indent}<span class="cmt">{stripped}</span>')
            elif stripped.startswith("//"):
                out_lines.append(f'{indent}<span class="cmt">{stripped}</span>')
            else:
                out_lines.append(line)
        return opening + "\n".join(out_lines) + closing

    return pre_re.sub(transform, html)


def _label_code_panels(html: str) -> str:
    """Add a `data-lang="<tab-text>"` attribute to each `.code-panel` so the
    print CSS can show the tab name above the panel (since tabs become a
    flat eyebrow rather than clickable buttons).

    Strategy: for each `.code-block-wrapper`, parse its `.code-tabs` button
    text and pair them in order with the `.code-panel` children.
    """
    wrapper_re = re.compile(
        r'(<div class="code-block-wrapper"[^>]*>)(.*?)(</div>\s*</div>\s*</div>|</div>\s*</div>)',
        re.DOTALL,
    )
    # Simpler: walk wrappers with BeautifulSoup if available.
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return html

    soup = BeautifulSoup(html, "html.parser")
    for wrapper in soup.select(".code-block-wrapper"):
        tab_texts = [t.get_text(strip=True) for t in wrapper.select(".code-tab")]
        panels = wrapper.select(".code-panel")
        for panel, label in zip(panels, tab_texts):
            if label and not panel.get("data-lang"):
                panel["data-lang"] = label
    return str(soup)


# ---------------------------------------------------------------------------
# Drop TypeScript / JavaScript panels — keep Python only
# ---------------------------------------------------------------------------

# Tab labels (lowercased) that identify TypeScript/JavaScript panels.
_TS_LANG_LABELS = {
    "typescript", "ts", "node.js", "node.js / typescript",
    "javascript", "js", "jsx", "tsx", "node",
}


def _is_ts_panel(panel) -> bool:
    """Return True if the code panel contains TypeScript/JavaScript code."""
    lang = (panel.get("data-lang") or "").lower()
    if any(lbl in lang for lbl in _TS_LANG_LABELS):
        return True
    # Fallback: inspect the first non-blank line of the code itself.
    code_el = panel.find("code")
    if not code_el:
        return False
    text = code_el.get_text()
    first = next((l.strip() for l in text.splitlines() if l.strip()), "")
    # TypeScript/JS file headers: `// filename.ts` or `// filename.tsx` etc.
    if re.match(r"//\s*\S+\.(?:ts|tsx|js|jsx|mjs|cjs)\b", first):
        return True
    # TypeScript-specific shell invocations
    if re.match(r"npx\s+(ts-node|tsc)\b", first):
        return True
    return False


def _drop_ts_panels(html: str) -> str:
    """Remove every TypeScript/Node.js code panel (and its tab button) from
    each .code-block-wrapper, leaving only Python (and language-agnostic)
    panels. Cleans up empty tab rows and marks remaining panels active."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return html

    soup = BeautifulSoup(html, "html.parser")

    for wrapper in soup.select(".code-block-wrapper"):
        tabs_div = wrapper.find(class_="code-tabs")
        tab_btns = tabs_div.select(".code-tab") if tabs_div else []
        panels = wrapper.select(".code-panel")

        # Pair each panel with its tab button (may have more panels than tabs).
        pairs = list(zip(tab_btns, panels))
        if len(panels) > len(tab_btns):
            pairs += [(None, p) for p in panels[len(tab_btns):]]

        to_drop_panels = []
        to_drop_tabs = []
        for tab, panel in pairs:
            if _is_ts_panel(panel):
                to_drop_panels.append(panel)
                if tab:
                    to_drop_tabs.append(tab)

        for el in to_drop_tabs + to_drop_panels:
            el.decompose()

        # If wrapper is now empty, remove it entirely.
        remaining = wrapper.select(".code-panel")
        if not remaining:
            wrapper.decompose()
            continue

        # Clean up the tab eyebrow: remove if empty, or hide if single tab.
        if tabs_div:
            left_tabs = tabs_div.select(".code-tab")
            if not left_tabs:
                tabs_div.decompose()
            # If only one tab remains keep it as a label (CSS handles it fine).

        # Make all remaining panels visible (tabs are now cosmetic in print).
        for panel in wrapper.select(".code-panel"):
            cls = panel.get("class") or []
            if "active" not in cls:
                cls = list(cls) + ["active"]
                panel["class"] = cls

    return str(soup)


# ---------------------------------------------------------------------------
# Section stripping
# ---------------------------------------------------------------------------

def strip_sections(html: str) -> str:
    for sec_id in STRIP_SECTION_IDS:
        # `class="section"` may have extra classes (e.g. quiz-section), so we
        # match anywhere inside the section's opening attributes.
        pattern = re.compile(
            r'<section\b[^>]*\bid="' + re.escape(sec_id) + r'"[^>]*>.*?</section>\s*',
            re.DOTALL,
        )
        new_html, n = pattern.subn("", html)
        if n == 0:
            print(f"  (warn) strip pattern matched 0 times for id='{sec_id}'")
        html = new_html

    # Clean sidebar anchors whose target section is now gone.
    for anchor in STRIPPED_ANCHORS:
        html = re.sub(
            r'<a\s+href="#' + re.escape(anchor) + r'"[^>]*>.*?</a>\s*',
            '',
            html,
            flags=re.DOTALL,
        )
    return html


# ---------------------------------------------------------------------------
# Front-matter injection: "Three Iterations at a Glance"
# ---------------------------------------------------------------------------

def at_a_glance_html(domain: str) -> str:
    """Side-by-side cheat-sheet card. Same shape for every domain."""
    return f"""
    <section class="section at-a-glance" id="at-a-glance">
      <div class="glance-title">Three Iterations at a Glance</div>
      <div class="glance-sub">Same agent, same business question, same five tools, same mock data. Three layers of abstraction.</div>
      <div class="glance-grid">
        <div class="glance-row-header">&nbsp;</div>
        <div class="glance-col-head glance-col-1">Iter 1 — Raw API</div>
        <div class="glance-col-head glance-col-2">Iter 2 — Agent SDK + Claude Code</div>
        <div class="glance-col-head glance-col-3">Iter 3 — Spec-Driven</div>

        <div class="glance-row-header">Lines you write</div>
        <div class="glance-col-1">~250 lines of Python</div>
        <div class="glance-col-2">~120 lines (SDK + hooks + sessions)</div>
        <div class="glance-col-3">~100 lines of spec (no agent code)</div>

        <div class="glance-row-header">Time to build</div>
        <div class="glance-col-1">~3 hours</div>
        <div class="glance-col-2">~2 hours</div>
        <div class="glance-col-3">~1 hour</div>

        <div class="glance-row-header">Loop lives in</div>
        <div class="glance-col-1">Your <code>while True</code></div>
        <div class="glance-col-2">SDK's <code>query()</code></div>
        <div class="glance-col-3">Generated for you by Claude Code</div>

        <div class="glance-row-header">Debug method</div>
        <div class="glance-col-1"><code>print()</code> in the loop + manual message inspection</div>
        <div class="glance-col-2">Hooks as probes + Anthropic Console + Langfuse traces</div>
        <div class="glance-col-3">Spec ↔ code comparison + tests + evals</div>

        <div class="glance-row-header">Key insight</div>
        <div class="glance-col-1">Builds the mental model — every line is yours</div>
        <div class="glance-col-2">Half the code; modular debug; sessions + hooks for free</div>
        <div class="glance-col-3">The spec IS the documentation auditors read</div>
      </div>
    </section>
    """


# Where to inject the "at a glance" card: right after the <h2 id="brief-heading">
# block, before the next <section>. Use a regex that finds the closing </section>
# of the brief and inserts the at-a-glance before the following section open.

def inject_front_matter(html: str, domain: str) -> str:
    # Find the closing </section> after the brief section and inject our card.
    pattern = re.compile(
        r'(<section[^>]*\bid="brief"[^>]*>.*?</section>\s*)',
        re.DOTALL,
    )
    if not pattern.search(html):
        # Fallback: prepend just after <main> or the first <section>
        return html
    return pattern.sub(r'\1' + at_a_glance_html(domain), html, count=1)


# ---------------------------------------------------------------------------
# Plain-diagram replacement for the anim-arch section
# ---------------------------------------------------------------------------
#
# The source uses ASCII-art inside .arch-diagram <pre> blocks plus a tab system
# that hides 2 of 3 panels by default. In print this rendered as cramped
# unreadable monospace text. We replace the entire section content with hand-
# crafted HTML diagrams — three iteration-colored cards, each a clean flow of
# boxes labelled with the right files/components. No SVG, no JS, no tabs.

ARCH_DIAGRAMS_HTML = """
<section class="section" id="anim-arch">
  <h2 id="anim-arch-heading">Architecture Per Iteration</h2>
  <p>Each iteration produces the same logical agent (system prompt + 5 tools + a loop). What changes is the <em>physical</em> architecture &mdash; how much you own, how much the SDK owns, and how much is generated for you.</p>

  <div class="arch-card-stack">
    <!-- ITER 1 -->
    <div class="arch-card arch-1">
      <div class="arch-head">
        <span class="arch-num">ITER 1</span>
        <span class="arch-name">Raw API Loop</span>
        <span class="arch-own">You own everything</span>
      </div>
      <div class="arch-main">
        <div class="arch-main-title">agent.py &nbsp;<span class="arch-size">~250 lines, all hand-written</span></div>
        <ul class="arch-flow">
          <li><span class="arch-kw">while True:</span><span class="arch-note">the loop you wrote</span></li>
          <li><span class="arch-call">client.messages.create(...)</span></li>
          <li><span class="arch-kw">if</span> response.stop_reason == &ldquo;end_turn&rdquo;: <span class="arch-kw">break</span></li>
          <li><span class="arch-kw">for</span> block <span class="arch-kw">in</span> response.content:
            <ul class="arch-substeps">
              <li>validate_input · check_cost_cap · log · execute_tool · redact_phi · append · audit_log</li>
            </ul>
          </li>
        </ul>
      </div>
      <div class="arch-fanout">
        <div class="arch-leaf"><span class="arch-leaf-name">tools.py</span><span class="arch-leaf-note">5 clinical tools you wrote</span></div>
        <div class="arch-leaf"><span class="arch-leaf-name">circuit_breaker.py</span><span class="arch-leaf-note">you built</span></div>
        <div class="arch-leaf"><span class="arch-leaf-name">audit_log.jsonl</span><span class="arch-leaf-note">you rotate</span></div>
      </div>
      <div class="arch-deploy">server.py (FastAPI) + Dockerfile &mdash; you wrote both</div>
    </div>

    <!-- ITER 2 -->
    <div class="arch-card arch-2">
      <div class="arch-head">
        <span class="arch-num">ITER 2</span>
        <span class="arch-name">Agent SDK + Claude Code</span>
        <span class="arch-own">You own the tools and config; SDK owns the loop</span>
      </div>
      <div class="arch-main">
        <div class="arch-main-title">agent.py &nbsp;<span class="arch-size">~90 lines</span></div>
        <ul class="arch-flow">
          <li><span class="arch-call">@tool(&ldquo;lookup_clinical_criteria&rdquo;, ...)</span>&nbsp;&times;5 functions</li>
          <li><span class="arch-call">preauth_server = create_sdk_mcp_server(tools=[...])</span></li>
          <li><span class="arch-call">OPTIONS = ClaudeAgentOptions(system_prompt=..., mcp_servers=..., hooks=...)</span></li>
          <li><span class="arch-kw">async for</span> msg <span class="arch-kw">in</span> query(prompt=..., options=OPTIONS): ...</li>
        </ul>
        <div class="arch-note-block">The loop, message-passing, retries, and streaming live inside <code>claude-agent-sdk</code>. You do not write them.</div>
      </div>
      <div class="arch-fanout arch-fanout-2col">
        <div class="arch-leaf">
          <span class="arch-leaf-name">Claude Code generated</span>
          <span class="arch-leaf-list">server.py · Dockerfile · tests · .claude/settings.json · hooks/*.py</span>
        </div>
        <div class="arch-leaf">
          <span class="arch-leaf-name">claude-agent-sdk managed</span>
          <span class="arch-leaf-list">query() loop · MCP transport · HookMatcher · resume tokens · streaming</span>
        </div>
      </div>
    </div>

    <!-- ITER 3 -->
    <div class="arch-card arch-3">
      <div class="arch-head">
        <span class="arch-num">ITER 3</span>
        <span class="arch-name">Spec-Driven</span>
        <span class="arch-own">You own only the spec</span>
      </div>
      <div class="arch-main">
        <div class="arch-main-title">spec/agent-spec.md &nbsp;<span class="arch-size">~100 lines &mdash; the only file you write</span></div>
        <div class="arch-spec-sections">
          <div>1. Overview</div><div>2. Configuration</div><div>3. Tools (5)</div>
          <div>4. System Prompt</div><div>5. Hooks (PHI / tone / risk)</div><div>6. Sessions</div>
          <div>7. Mock Data</div><div>8. API Wrapper</div><div>9. Deployment</div>
          <div>10. Tests</div><div>11. Evaluation</div><div>12. File Structure</div>
        </div>
      </div>
      <div class="arch-arrow">&darr;</div>
      <div class="arch-main">
        <div class="arch-main-title"><code>/generate-from-spec spec/agent-spec.md</code></div>
        <div class="arch-note-block">Claude Code reads the spec, generates ~18 files: <code>agent.py</code> · <code>sessions.py</code> · <code>mock_data/*.json</code> &times;4 · <code>server.py</code> · <code>Dockerfile</code> · <code>.claude/settings.json</code> · <code>hooks/*.py</code> · <code>.claude/commands/*.md</code> · <code>tests/test_*.py</code> &times;5 · <code>appendix/manual-loop.py</code> (Iter-1 reference).</div>
      </div>
    </div>
  </div>
</section>
"""


def replace_arch_animation(html: str) -> str:
    """Strip the original anim-arch section (ASCII + tabs) and substitute a
    clean static-diagram replacement. No-op if anim-arch is already gone."""
    pattern = re.compile(
        r'<section\b[^>]*\bid="anim-arch"[^>]*>.*?</section>\s*',
        re.DOTALL,
    )
    if pattern.search(html):
        html = pattern.sub(ARCH_DIAGRAMS_HTML, html, count=1)
    return html


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build_print_html(src_html: str, domain: str) -> str:
    html = strip_sections(src_html)
    html = replace_arch_animation(html)
    html = inject_front_matter(html, domain)
    html = _label_code_panels(html)
    html = _drop_ts_panels(html)        # keep Python only
    # Pseudocode pass MUST run before _wrap_comments_in_code: the comment-
    # wrapper looks for raw `#` lines, but _pseudocodify_all escapes the
    # contents and runs keyword-wrapping. Order: pseudocode (rewrite + escape
    # + kw wrap) -> comment wrap (looks for # at line-start).
    html = _pseudocodify_all(html)
    html = _wrap_comments_in_code(html)
    needle = "</body>"
    if needle not in html:
        sys.exit("Source HTML has no </body> tag.")
    return html.replace(needle, PRINT_OVERRIDES_CSS + PRINT_FINALIZE_JS + needle, 1)


def reserve_path(target: Path) -> Path:
    if not target.exists():
        return target
    for i in range(0, 10):
        suffix = "" if i == 0 else str(i)
        cand = target.with_name(f"{target.stem}.new{suffix}.pdf") if i > 0 else target
        try:
            with open(cand, "ab"):
                return cand
        except PermissionError:
            continue
    sys.exit(f"All output paths locked for {target.name}.")


def render_pdf(browser: str, src_html_path: Path, out_pdf: Path, domain: str) -> None:
    if not src_html_path.exists():
        sys.exit(f"Source HTML not found: {src_html_path}")

    print(f"[{domain}] Reading {src_html_path.name} ...", flush=True)
    src_html = src_html_path.read_text(encoding="utf-8")
    print_html = build_print_html(src_html, domain)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Preserve previous output if any (project rule).
    if out_pdf.exists():
        backup = out_pdf.with_name(f"{out_pdf.stem}-v1.pdf")
        try:
            if backup.exists():
                backup.unlink()
            shutil.copy2(out_pdf, backup)
            print(f"[{domain}] Preserved previous as {backup.name}")
        except Exception as e:
            print(f"[{domain}] (could not preserve previous: {e})")

    with tempfile.TemporaryDirectory(prefix=f"c7-print-{domain}-", dir=out_pdf.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / f"c7-{domain}-print.html"
        tmp_html.write_text(print_html, encoding="utf-8")
        tmp_pdf = tmp_dir / "out.pdf"
        print(f"[{domain}] Rendering PDF ...", flush=True)
        result = subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("Chrome stderr:\n" + (result.stderr or ""), file=sys.stderr)
            sys.exit(f"[{domain}] Chrome exited with code {result.returncode}")
        if not tmp_pdf.exists():
            sys.exit(f"[{domain}] Chrome did not produce a PDF.")

        final_path = reserve_path(out_pdf)
        try:
            shutil.move(str(tmp_pdf), final_path)
        except PermissionError:
            sys.exit(f"[{domain}] Could not write {final_path}.")

    size_kb = final_path.stat().st_size / 1024
    print(f"[{domain}] Wrote {final_path.name} ({size_kb:.0f} KB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", choices=["A", "B", "C", "all"], default="all",
                    help="Which domain to render (default: all three)")
    args = ap.parse_args()

    browser = find_browser()
    domains_to_render = [args.domain] if args.domain != "all" else ["A", "B", "C"]

    for d in domains_to_render:
        meta = DOMAINS[d]
        render_pdf(browser, meta["src"], meta["out"], d)


if __name__ == "__main__":
    main()
