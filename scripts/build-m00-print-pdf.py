"""Build a print-friendly PDF of M00 (Course Overview — Agent Lifecycle).

Strategy
--------
The source HTML at output/M00-course-overview-agent-lifecycle.html is a
self-contained interactive module: dark theme, a sidebar, a "Listen Mode"
audio FAB, multiple SVG animations that reveal their pieces via opacity
transitions, and an interactive quiz with click handlers.

For a printer-friendly PDF we:

  1. Strip the two hands-on lab subsections (they are 30-minute typing labs
     that don't belong in a printed reference):
       - Part 2 of the Prelude (`#prelude-lab` … just before `#prelude-diagram`)
       - "20-Minute Hands-On: Build All Three" inside the Agent Boundary section.

  2. Inject a `<style id="pdf-print-overrides">` block that:
     - re-paints the whole page in a light theme (white bg, dark slate text)
     - INCLUDING every `.animation-container` (now light-card, not dark) so
       the document is reasonable on a black-and-white printer
     - hides interactive-only chrome: sidebar, top progress, listen FAB/panel,
       animation play/pause buttons, copy buttons, module prev/next nav
     - forces every animation step to `opacity: 1 !important` so the
       animations render as complete static diagrams
     - adds page-break-inside: avoid for tables, callouts, and animation cards

  3. Inject a `<script id="pdf-print-finalize">` block that:
     - lights all `m00-era-*` groups and extends the AI timeline gradient line
     - marks every `.demo-step` `.visible`
     - adds `.playing` to every `.animation-container`
     - WALKS EVERY SVG inside `.animation-container` and remaps dark fills
       (e.g. `#1A2740`, `#2a2a3e`, `#1a1a2e`, `#1e3a5f`, `#3a3a3a`, `#3a2a5e`)
       to light backgrounds, and light text fills (`#E8ECF1`, `#ddd`, `#aaa`,
       `#fff`) to dark slate so the diagrams stay readable on white paper.

The page is then rendered to PDF via headless Chrome with a generous
`virtual-time-budget` so any SMIL/CSS animations that *do* run reach their
`fill="freeze"` / `forwards` end state before the snapshot.

Output: output/M00-course-overview-agent-lifecycle-print.pdf
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "output" / "M00-course-overview-agent-lifecycle.html"
OUT_PDF = ROOT / "output" / "M00-course-overview-agent-lifecycle-print.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


PRINT_OVERRIDES_CSS = r"""
<style id="pdf-print-overrides">
  /* === Page setup === */
  @page { size: A4; margin: 10mm 11mm 11mm 11mm; }

  html, body {
    background: #ffffff !important;
    color: #1a1f2e !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    font-size: 9.5pt !important;
    line-height: 1.38 !important;
  }

  /* Tighten default paragraph / list spacing globally. */
  p { margin: 0 0 0.35rem !important; }
  ul, ol { margin: 0.3rem 0 0.5rem 1.1rem !important; padding: 0 !important; }
  li { margin: 0 0 0.18rem !important; }
  h1 { font-size: 18pt !important; margin: 0.6rem 0 0.4rem !important; line-height: 1.2 !important; }
  h2 { font-size: 14pt !important; margin: 0.7rem 0 0.35rem !important; line-height: 1.2 !important; }
  h3 { font-size: 11.5pt !important; margin: 0.55rem 0 0.25rem !important; line-height: 1.25 !important; }
  h4 { font-size: 10.5pt !important; margin: 0.4rem 0 0.2rem !important; line-height: 1.25 !important; }

  /* === Light-mode theme variable overrides ===
     SVGs hard-code their own colors and live inside .animation-container,
     which we KEEP dark below — so this only affects the surrounding page. */
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
    --accent-muted: rgba(184, 134, 11, 0.10);
    --success-bg: rgba(16, 185, 129, 0.10);
    --warning-bg: rgba(245, 158, 11, 0.10);
    --error-bg:   rgba(244, 63, 94, 0.10);
    --info-bg:    rgba(59, 130, 246, 0.10);
    --accent-primary: #b8860b;
    --accent-hover:   #9a7209;
  }

  /* === Hide interactive chrome === */
  .top-progress,
  .sidebar-toggle,
  .sidebar-nav,
  .listen-fab,
  .listen-panel,
  .animation-controls,
  .copy-btn, button.copy,
  .module-nav,
  .quiz-section nav,
  details > summary::-webkit-details-marker,
  .term-tooltip .tooltip-content {
    display: none !important;
  }

  /* === Layout: collapse to single column === */
  .page-container {
    display: block !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
  }
  .content { max-width: 100% !important; }

  /* Course header — keep simplified */
  .course-header {
    background: #f8fafc !important;
    border-bottom: 1px solid #cbd5e1 !important;
    padding: 0.35rem 0.8rem !important;
    margin-bottom: 0.5rem !important;
  }
  .course-title { color: #334155 !important; }
  .track-badge { background: rgba(99,102,241,0.10) !important; color: #4338ca !important; border-color: #4338ca !important; }
  .track-badge .dot { background: #4338ca !important; }
  .header-meta { color: #475569 !important; }

  /* Headings */
  h1, h2, h3, h4 { color: #0A1628 !important; page-break-after: avoid; }
  h2 { border-top: 1px solid #cbd5e1 !important; padding-top: 0.4rem !important; }
  h2:first-of-type { border-top: none !important; padding-top: 0 !important; }

  /* Body text + links + inline code */
  p, li, td, th { color: #1a1f2e !important; }
  a { color: #2563eb !important; }
  code { background: #f1f5f9 !important; color: #b45309 !important; border: 1px solid #e2e8f0 !important; padding: 0.05rem 0.3rem !important; border-radius: 3px !important; }

  /* Tables — light variant */
  .info-table, table {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
    page-break-inside: avoid;
  }
  .info-table thead th, table thead th {
    background: #f1f5f9 !important;
    color: #0A1628 !important;
    border-bottom: 2px solid #94a3b8 !important;
  }
  .info-table td, .info-table th, table td, table th {
    border-color: #e2e8f0 !important;
    color: #1a1f2e !important;
  }
  .table-container { overflow: visible !important; }

  /* Callouts — keep tint but on light background */
  .analogy-box, .tech-def-box, .callout-why, .callout-warning,
  .callout-security, .callout-cost, .callout-cert {
    color: #1a1f2e !important;
    page-break-inside: avoid;
    padding: 0.45rem 0.65rem !important;
    margin: 0.35rem 0 !important;
  }
  .analogy-box     { background: rgba(184,134,11,0.08) !important; border-left-color: #b8860b !important; }
  .tech-def-box    { background: rgba(59,130,246,0.08) !important; border-left-color: #2563eb !important; }
  .callout-why     { background: rgba(16,185,129,0.08) !important; border-left-color: #059669 !important; }
  .callout-warning { background: rgba(245,158,11,0.10) !important; border-left-color: #d97706 !important; }
  .callout-security{ background: rgba(244,63,94,0.08)  !important; border-left-color: #be123c !important; }
  .callout-cert    { background: rgba(184,134,11,0.06) !important; border-left-color: #b8860b !important; }
  .box-label { color: inherit !important; }

  /* Tooltip underline — show but no popup */
  .term-tooltip {
    color: #b45309 !important;
    border-bottom: 1px dotted #b45309 !important;
    cursor: text !important;
  }

  /* Code blocks (pre) — light, printer-friendly */
  pre, .code-block {
    background: #f6f8fa !important;
    color: #0A1628 !important;
    border: 1px solid #d0d7de !important;
    overflow: visible !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    font-size: 8.5pt !important;
    line-height: 1.35 !important;
    padding: 0.5rem 0.7rem !important;
    margin: 0.35rem 0 !important;
  }
  pre code { background: transparent !important; color: inherit !important; border: 0 !important; }
  /* Headings inside the code prompt comments — many <pre> blocks lead with
     "# title" lines; keep them readable on the light card. */
  pre, pre code { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

  /* === Animation containers — LIGHT for printer friendliness === */
  .animation-container {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
    overflow: visible !important;
    min-height: auto !important;
    padding: 0.5rem 0.6rem !important;
    margin: 0.35rem 0 !important;
    page-break-inside: avoid;
  }
  /* Let SVGs use their natural aspect-ratio; only cap absurdly tall ones. */
  .animation-container svg {
    width: 100% !important;
    height: auto !important;
    max-width: 100% !important;
    max-height: 165mm !important;
    display: block !important;
  }
  .animation-container .animation-title {
    color: #475569 !important;
    font-weight: 700 !important;
  }
  .animation-container svg { max-width: 100% !important; height: auto !important; }
  .animation-container h4 { color: #0A1628 !important; }

  /* Comparison sides (chatbot vs agent) — light cards */
  .comparison-side { background: #f8fafc !important; border-color: #cbd5e1 !important; }
  .comparison-side h4 { color: #0A1628 !important; }
  .comparison-side.chatbot-side h4 { color: #475569 !important; }
  .comparison-side.agent-side h4 { color: #b8860b !important; }
  .msg-bubble { color: #1a1f2e !important; }
  .msg-user { background: rgba(99,102,241,0.10) !important; border-color: rgba(99,102,241,0.30) !important; color: #1a1f2e !important; }
  .msg-llm  { background: #ffffff !important; border-color: #cbd5e1 !important; color: #1a1f2e !important; }
  .msg-tool { background: rgba(184,134,11,0.10) !important; border-color: rgba(184,134,11,0.30) !important; color: #78350f !important; }
  .msg-think{ background: rgba(139,92,246,0.10) !important; border-color: rgba(139,92,246,0.30) !important; color: #5b21b6 !important; }
  .badge-done { background: #f1f5f9 !important; color: #475569 !important; border: 1px solid #cbd5e1 !important; }
  .agent-side .badge-done { background: rgba(16,185,129,0.10) !important; color: #065f46 !important; border-color: rgba(16,185,129,0.30) !important; }

  /* UCC demo steps — light cards */
  .demo-step {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
  }
  #anim-ucc-demo .demo-step .step-content,
  .demo-step .step-content,
  .demo-step .step-label { color: #1a1f2e !important; }

  /* Architecture / lifecycle blocks — light */
  .arch-block, .lifecycle-stage, .ccd-box, .wf-step, .roadmap-track {
    background: #ffffff !important;
    border-color: #cbd5e1 !important;
    color: #1a1f2e !important;
  }

  /* === Render class-driven reveal animations as a complete static diagram ===
     These blocks start at opacity 0/0.3 in the live page and only get
     `.lit` / `.visible` / `.active` classes when their JS driver runs.
     In a print render no JS runs, so we force the final state here. */
  .arch-block,
  .arch-block.lit,
  .lifecycle-stage,
  .lifecycle-stage.lit,
  .lifecycle-arrow,
  .lifecycle-arrow.visible,
  .ccd-box,
  .ccd-box.visible,
  .ccd-arrow,
  .ccd-arrow.visible,
  .wf-step,
  .wf-step.visible,
  .roadmap-track,
  .roadmap-track.visible,
  .demo-step,
  .demo-step.visible {
    opacity: 1 !important;
    transform: none !important;
    animation: none !important;
    transition: none !important;
  }
  .lifecycle-arrow, .ccd-arrow { color: #475569 !important; }
  /* Workflow step "tool" tag in print — use accent gold on light */
  .wf-tool { color: #b8860b !important; }
  /* Arrows between rows of the Claude Code diagram */
  .ccd-row { gap: 0.4rem !important; }
  .claude-code-diagram, .arch-grid, .workflow-steps, .lifecycle-flow {
    min-height: auto !important;
  }

  /* === Force every reveal-by-opacity element to fully visible === */
  /* Three-lanes (script / fastapi / agent comparison) */
  #anim-three-lanes .step,
  #anim-three-lanes .arr,
  #anim-three-lanes .lane-1 .step,
  #anim-three-lanes .lane-2 .step,
  #anim-three-lanes .lane-3 .step { opacity: 1 !important; animation: none !important; }

  /* Three-levels SVG (single-call / chained / agent loop) */
  #anim-three-levels .three-levels-step { opacity: 1 !important; animation: none !important; }

  /* Layer stack (intelligence layer appears) */
  #layer-stack-anim .layer3-group,
  #layer-stack-anim .layer3-label { opacity: 1 !important; animation: none !important; transform: none !important; }

  /* Chatbot vs Agent */
  #anim-chatbot-vs-agent .msg-bubble,
  #anim-chatbot-vs-agent .badge-done { opacity: 1 !important; transform: none !important; animation: none !important; }

  /* UCC demo steps */
  #anim-ucc-demo .demo-step { opacity: 1 !important; transform: none !important; animation: none !important; }
  #anim-ucc-demo .demo-step .step-content { color: #E8ECF1 !important; }
  #anim-ucc-demo .demo-step .step-label { font-weight: 600; }

  /* AI timeline eras (inline opacity="0.25" on dim eras) */
  #anim-ai-timeline g[id^="m00-era-"] { opacity: 1 !important; }
  #anim-ai-timeline #m00-stack-visual { opacity: 1 !important; }

  /* SMIL animations on script-vs-agent — neutralize so initial state shows */
  #anim-script-vs-agent svg animate { /* nothing — chrome handles freeze */ }
  #anim-script-vs-agent svg rect,
  #anim-script-vs-agent svg ellipse,
  #anim-script-vs-agent svg line,
  #anim-script-vs-agent svg path { opacity: 1 !important; }

  /* Quiz — show questions but suppress hover state coloring; keep answers hidden
     since the learner has no way to click in print. Render as a static "exercises" list. */
  .quiz-section .quiz-feedback { display: none !important; }
  .quiz-section .quiz-question {
    background: #f8fafc !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
    page-break-inside: avoid;
  }
  .quiz-section .quiz-option {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1a1f2e !important;
    cursor: default !important;
  }
  .quiz-section .quiz-marker { border-color: #94a3b8 !important; color: #334155 !important; }
  .quiz-section .quiz-score { display: none !important; }

  /* Section breaks — let content flow, no forced per-section page break.
     Just keep headings attached to the following content and prevent ugly orphans. */
  section.section { page-break-before: auto; margin: 0 !important; padding: 0 !important; }
  section.section h2 { page-break-after: avoid; }
  p, li { orphans: 3; widows: 3; }

  /* Print footer hint — no-op since we pass --no-pdf-header-footer */

  /* Listen-mode helpers used as anchors inline — kill any decorative pulse */
  .listen-section-active::before { animation: none !important; display: none !important; }

  /* Reduce-motion safety net */
  *, *::before, *::after {
    animation-duration: 0.001s !important;
    transition-duration: 0.001s !important;
  }
</style>
"""


PRINT_FINALIZE_JS = r"""
<script id="pdf-print-finalize">
  (function () {
    // Dark SVG fills → light backgrounds (printer-friendly remap).
    var DARK_FILL_REMAP = {
      '#0a1628': '#ffffff',
      '#1a2740': '#f1f5f9',
      '#162033': '#f8fafc',
      '#111d33': '#f8fafc',
      '#2a2a3e': '#f1f5f9',
      '#1a1a2e': '#ffffff',
      '#1e3a5f': '#dbeafe',
      '#3a3a3a': '#e5e7eb',
      '#3a2a5e': '#ede9fe',
      '#21262d': '#e2e8f0',
      '#0d1117': '#f8fafc'
    };
    // Light text fills (on dark) → dark text (on light).
    var LIGHT_TEXT_REMAP = {
      '#e8ecf1': '#0A1628',
      '#fff':    '#0A1628',
      '#ffffff': '#0A1628',
      '#ddd':    '#0A1628',
      '#dddddd': '#0A1628',
      '#dbeafe': '#1e3a5f',
      '#93c5fd': '#1e3a5f',
      '#aaa':    '#475569',
      '#aaaaaa': '#475569',
      '#888':    '#475569',
      '#888888': '#475569',
      '#94a3b8': '#475569',
      '#64748b': '#334155',
      '#b8b0f0': '#5b21b6',
      '#7fdecc': '#065f46',
      '#f0d98c': '#92400e',
      '#f0a090': '#9a3412',
      '#c4b5fd': '#5b21b6'
    };
    // Light strokes that disappear on white → darken.
    var LIGHT_STROKE_REMAP = {
      '#777':    '#94a3b8',
      '#777777': '#94a3b8',
      '#888':    '#475569',
      '#888888': '#475569',
      '#666':    '#94a3b8',
      '#666666': '#94a3b8',
      '#555':    '#94a3b8',
      '#555555': '#94a3b8'
    };
    function normalizeHex(v) {
      if (!v) return '';
      v = String(v).trim().toLowerCase();
      if (v.charAt(0) !== '#') return '';
      return v;
    }
    function remapAttr(el, attr, table) {
      var cur = normalizeHex(el.getAttribute(attr));
      if (cur && table[cur]) el.setAttribute(attr, table[cur]);
      // Also handle inline `style="fill:..."` if present.
      var style = el.getAttribute('style');
      if (style && /\bfill\s*:\s*#[0-9a-fA-F]+/i.test(style)) {
        var newStyle = style.replace(/\bfill\s*:\s*(#[0-9a-fA-F]+)/gi, function (_, hex) {
          var k = hex.toLowerCase();
          return 'fill:' + (table[k] || hex);
        });
        if (newStyle !== style) el.setAttribute('style', newStyle);
      }
    }
    function remapSvgColors() {
      document.querySelectorAll('.animation-container svg').forEach(function (svg) {
        // 1. Remap fills on shapes (rect, circle, ellipse, path, polygon).
        svg.querySelectorAll('rect, circle, ellipse, path, polygon, g').forEach(function (el) {
          remapAttr(el, 'fill', DARK_FILL_REMAP);
        });
        // 2. Remap text fills (light-on-dark → dark-on-light).
        svg.querySelectorAll('text, tspan').forEach(function (el) {
          remapAttr(el, 'fill', LIGHT_TEXT_REMAP);
        });
        // 3. Remap too-light strokes so arrows/dividers still show on white.
        svg.querySelectorAll('line, path, polyline, rect, circle, ellipse').forEach(function (el) {
          remapAttr(el, 'stroke', LIGHT_STROKE_REMAP);
        });
      });
    }

    function finalize() {
      // 1. AI timeline: light all era groups + extend the gradient fill line to its end.
      var fill = document.getElementById('m00-era-fill');
      if (fill) { fill.setAttribute('x2', '1020'); }
      for (var i = 1; i <= 7; i++) {
        var el = document.getElementById('m00-era-' + i);
        if (el) { el.setAttribute('opacity', '1'); el.style.opacity = '1'; }
      }

      // 2. Mark every .demo-step visible so the UCC walkthrough renders fully.
      document.querySelectorAll('.demo-step').forEach(function (el) {
        el.classList.add('visible');
        el.style.opacity = '1';
        el.style.transform = 'none';
      });

      // 2b. Light all class-driven reveal animations (arch, lifecycle, ccd, workflow,
      //     roadmap). The CSS already targets these, but adding the canonical class
      //     keeps any descendant-selector styling (e.g. arch-block.lit shadows) intact.
      var REVEAL_TARGETS = [
        ['.arch-block', 'lit'],
        ['.lifecycle-stage', 'lit'],
        ['.lifecycle-arrow', 'visible'],
        ['.ccd-box', 'visible'],
        ['.ccd-arrow', 'visible'],
        ['.wf-step', 'visible'],
        ['.roadmap-track', 'visible']
      ];
      REVEAL_TARGETS.forEach(function (pair) {
        document.querySelectorAll(pair[0]).forEach(function (el) {
          el.classList.add(pair[1]);
          el.style.opacity = '1';
          el.style.transform = 'none';
        });
      });

      // 3. Add .playing to every .animation-container.
      document.querySelectorAll('.animation-container').forEach(function (el) {
        el.classList.add('playing');
      });

      // 4. Remap dark SVG colors to light variants (printer-friendly).
      remapSvgColors();

      // 5. Kill stray timers / rAF loops from the page's animation drivers.
      var maxId = setTimeout(function () {}, 0);
      for (var t = 0; t < maxId; t++) {
        try { clearTimeout(t); clearInterval(t); } catch (e) {}
      }

      // 6. Close the Listen panel if any startup code opened it.
      var lp = document.getElementById('listenPanel');
      if (lp) { lp.classList.remove('open'); lp.style.display = 'none'; }
      var lf = document.getElementById('listenFab');
      if (lf) { lf.style.display = 'none'; }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', finalize);
    } else {
      finalize();
    }
    setTimeout(finalize, 800);
  })();
</script>
"""


# -- Lab stripping ---------------------------------------------------------
# Two hands-on subsections live inside otherwise-conceptual sections, so we
# can't just drop a whole <section>. We pattern-match the H3 anchor that
# opens each lab and remove up to the next conceptual H3 (or its closing tag).

import re

LAB_STRIP_PATTERNS = [
    # Prelude Part 2: from <h3 id="prelude-lab"...> up to (but not including)
    # <h3 id="prelude-diagram"...>.
    (
        re.compile(
            r'<h3\s+id="prelude-lab"[^>]*>.*?(?=<h3\s+id="prelude-diagram")',
            re.DOTALL,
        ),
        "",
    ),
    # 20-Minute Hands-On block inside #agent-boundary section.
    (
        re.compile(
            r'<!--\s*20-Minute Hands-On\s*-->\s*<h3\s+id="agent-handson"[^>]*>.*?</ol>\s*',
            re.DOTALL,
        ),
        "",
    ),
]

# Course-meta sections — non-learning content, dropped from the printable.
SECTION_STRIP_PATTERNS = [
    # "Course Roadmap — What You'll Learn and When" — course-meta, not learning content.
    (
        re.compile(
            r'<section\s+class="section"\s+id="roadmap"[^>]*>.*?</section>\s*',
            re.DOTALL,
        ),
        "",
    ),
    # "Knowledge Check" — interactive quiz, no value in a static print reference.
    (
        re.compile(
            r'<section\s+class="section"\s+id="quiz"[^>]*>.*?</section>\s*',
            re.DOTALL,
        ),
        "",
    ),
    # "Three Agents You'll Build in This Course" — capstone preview, redundant in
    # a static print reference (the capstones have their own HTML files).
    (
        re.compile(
            r'<section\s+class="section"\s+id="three-agents"[^>]*>.*?</section>\s*',
            re.DOTALL,
        ),
        "",
    ),
]

# Sidebar anchor ids whose links should be cleaned up after their content is stripped.
STRIPPED_ANCHORS = (
    'prelude-lab',
    'agent-handson',
    'roadmap',
    'learning-paths',  # H3 anchor that lived inside #roadmap
    'quiz',
    'three-agents',
)


def strip_non_learning_sections(html: str) -> str:
    for pat, repl in LAB_STRIP_PATTERNS + SECTION_STRIP_PATTERNS:
        new_html, n = pat.subn(repl, html)
        if n == 0:
            print(f"  WARN: strip pattern matched 0 times: {pat.pattern[:60]}...")
        html = new_html
    # Drop sidebar entries for everything we stripped so the TOC stays consistent.
    for anchor in STRIPPED_ANCHORS:
        html = re.sub(
            r'<a\s+href="#' + anchor + r'"[^>]*>.*?</a>\s*',
            '',
            html,
            flags=re.DOTALL,
        )
    return html


def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("Could not find Chrome or Edge on this machine. Install one or "
             "edit CHROME_CANDIDATES at the top of this script.")


def build_print_html(src_html: str) -> str:
    """Strip non-learning content, then inject print overrides + finalize script."""
    html = strip_non_learning_sections(src_html)
    needle = "</body>"
    if needle not in html:
        sys.exit("Source HTML has no </body> tag — cannot inject overrides.")
    return html.replace(needle, PRINT_OVERRIDES_CSS + PRINT_FINALIZE_JS + needle, 1)


def reserve_output_path(target: Path) -> Path:
    """If target is locked by an open PDF viewer, fall back to a .new.pdf sibling."""
    if not target.exists():
        return target
    candidates = [target] + [
        target.with_name(f"{target.stem}.new{i if i else ''}.pdf")
        for i in range(0, 10)
    ]
    for c in candidates:
        try:
            with open(c, "ab") as fh:
                pass
            return c
        except PermissionError:
            continue
    sys.exit("All candidate output paths are locked. Close any open PDF viewer.")


def main() -> None:
    if not SRC_HTML.exists():
        sys.exit(f"Source HTML not found: {SRC_HTML}")
    browser = find_browser()

    print(f"Reading {SRC_HTML.name} ...", flush=True)
    src_html = SRC_HTML.read_text(encoding="utf-8")
    print_html = build_print_html(src_html)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    # Preserve previous version if one exists (per project memory rule).
    if OUT_PDF.exists():
        backup = OUT_PDF.with_name(f"{OUT_PDF.stem}-v1.pdf")
        try:
            if backup.exists():
                backup.unlink()
            shutil.copy2(OUT_PDF, backup)
            print(f"Preserved previous output as {backup.name}")
        except Exception as e:
            print(f"  (could not preserve previous: {e})")

    with tempfile.TemporaryDirectory(prefix="m00-print-", dir=OUT_PDF.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / "m00-print.html"
        tmp_html.write_text(print_html, encoding="utf-8")
        tmp_pdf = tmp_dir / "m00.pdf"

        print("Rendering PDF via headless Chrome ...", flush=True)
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
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("Chrome stderr:\n" + (result.stderr or ""), file=sys.stderr)
            sys.exit(f"Chrome exited with code {result.returncode}")
        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        final_path = reserve_output_path(OUT_PDF)
        try:
            shutil.move(str(tmp_pdf), final_path)
        except PermissionError:
            # Final fallback: pick the first writable sibling.
            for i in range(1, 10):
                alt = OUT_PDF.with_name(f"{OUT_PDF.stem}.new{i}.pdf")
                try:
                    shutil.move(str(tmp_pdf), alt)
                    final_path = alt
                    print(f"NOTE: target locked, wrote {alt.name} instead.")
                    break
                except PermissionError:
                    continue
            else:
                sys.exit("All output paths locked — close any PDF viewers and retry.")

    size_kb = final_path.stat().st_size / 1024
    print(f"Wrote {final_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
