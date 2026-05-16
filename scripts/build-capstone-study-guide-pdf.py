"""Build study-guide PDFs for Capstones 1–7 (all domains).

For each capstone HTML file this script produces a print-friendly PDF that:
  1. Strips non-study sections: quiz, extensions, references, reflection, rubric,
     and all animation containers (C6 has seven; C7 has four).
  2. Converts Python / TypeScript code blocks to compact pseudocode using the
     same pipeline as `build-capstone7-print-pdf.py` (imported at runtime).
  3. Light-themes the page for paper output and hides interactive chrome.

Outputs: output/CAPSTONE-{N}-DOMAIN-{X}-study.pdf
         output/CAPSTONE-6-data-pipeline-testing-study.pdf

Usage:
    python scripts/build-capstone-study-guide-pdf.py          # all capstones
    python scripts/build-capstone-study-guide-pdf.py --c 3    # capstone 3 only
    python scripts/build-capstone-study-guide-pdf.py --c 6    # C6 (single file)
    python scripts/build-capstone-study-guide-pdf.py --c 7    # C7 all domains
    python scripts/build-capstone-study-guide-pdf.py --c 7 --domain B
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"

# ---------------------------------------------------------------------------
# Import shared pseudocode + browser helpers from build-capstone7-print-pdf.py
# ---------------------------------------------------------------------------

_C7_SCRIPT = Path(__file__).parent / "build-capstone7-print-pdf.py"
_spec = importlib.util.spec_from_file_location("_c7", _C7_SCRIPT)
_c7 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c7)

find_browser         = _c7.find_browser
_label_code_panels   = _c7._label_code_panels
_pseudocodify_all    = _c7._pseudocodify_all
_wrap_comments_in_code = _c7._wrap_comments_in_code
PRINT_FINALIZE_JS    = _c7.PRINT_FINALIZE_JS


# ---------------------------------------------------------------------------
# Capstone registry
# ---------------------------------------------------------------------------

# (num, domain|None, src_filename, out_filename, extra_strip_ids)
_CAPSTONE_REGISTRY: list[dict] = []

for _n in [1, 2, 3, 4, 5]:
    for _d in ["A", "B", "C"]:
        _CAPSTONE_REGISTRY.append({
            "num": _n, "domain": _d,
            "src": OUTPUT_DIR / f"CAPSTONE-{_n}-DOMAIN-{_d}.html",
            "out": OUTPUT_DIR / f"CAPSTONE-{_n}-DOMAIN-{_d}-study.pdf",
            "extra_strip": [],
        })

# C6 — single file, seven animation sections
_CAPSTONE_REGISTRY.append({
    "num": 6, "domain": None,
    "src": OUTPUT_DIR / "CAPSTONE-6-data-pipeline-testing.html",
    "out": OUTPUT_DIR / "CAPSTONE-6-data-pipeline-testing-study.pdf",
    "extra_strip": [
        "anim-map", "anim-swarm", "anim-pipeline", "anim-formats",
        "anim-checks", "anim-dashboard", "anim-errors",
    ],
})

# C7 — three domain variants (already has -print.pdf; study guide is a lighter cut)
for _d in ["A", "B", "C"]:
    _CAPSTONE_REGISTRY.append({
        "num": 7, "domain": _d,
        "src": OUTPUT_DIR / f"CAPSTONE-7-DOMAIN-{_d}.html",
        "out": OUTPUT_DIR / f"CAPSTONE-7-DOMAIN-{_d}-study.pdf",
        "extra_strip": [
            "anim-lanes", "anim-waterfall", "anim-time", "anim-spec", "anim-arch",
        ],
    })

# Sections always stripped from every capstone
_COMMON_STRIP = ("quiz", "extensions", "references", "reflection", "rubric")


# ---------------------------------------------------------------------------
# Print CSS — light theme, compact, pseudocode-aesthetic code blocks
# ---------------------------------------------------------------------------

STUDY_GUIDE_CSS = r"""
<style id="study-guide-print-overrides">
  @page { size: A4; margin: 10mm 11mm 12mm 11mm; }

  html, body {
    background: #ffffff !important;
    color: #1a1f2e !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    font-size: 9.8pt !important;
    line-height: 1.42 !important;
  }

  /* Light-mode CSS variables */
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
  }

  /* Hide interactive chrome */
  .top-progress, .sidebar-toggle, .sidebar-nav,
  .listen-fab, .listen-panel, .animation-controls,
  .copy-btn, button.copy, .module-nav,
  .term-tooltip .tooltip-content { display: none !important; }

  /* Single-column layout */
  .page-container { display: block !important; max-width: 100% !important; padding: 0 !important; gap: 0 !important; }
  .content { max-width: 100% !important; }

  /* Course / capstone header */
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
  h2 { font-size: 13.5pt !important; line-height: 1.22 !important;
       border-top: 1px solid #cbd5e1 !important; padding-top: 0.55rem !important; margin-top: 0.7rem !important; }
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

  /* Callouts */
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

  /* Term tooltip */
  .term-tooltip { color: #b45309 !important; border-bottom: 1px dotted #b45309 !important; }

  /* Bridge sentence */
  .bridge {
    font-style: italic; color: #475569 !important;
    background: #f8fafc !important; border-left: 2.5px solid #cbd5e1 !important;
    padding: 0.4rem 0.7rem !important; margin: 0.5rem 0 !important;
    font-size: 9.4pt !important;
    page-break-inside: avoid;
  }

  /* === Code blocks — pseudocode aesthetic === */
  .code-block-wrapper {
    background: transparent !important;
    border: 0 !important; border-radius: 0 !important;
    margin: 0.4rem 0 !important;
    overflow: visible !important;
    page-break-inside: avoid;
  }
  .code-tabs {
    background: transparent !important; border: 0 !important;
    padding: 0 0 0.15rem 0 !important; margin: 0 !important;
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
  .code-panel { display: block !important; position: relative; margin: 0.15rem 0 0.3rem !important; }
  .code-panel pre {
    margin: 0 !important; padding: 0.42rem 0.6rem !important;
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
    border: 0 !important; padding: 0 !important;
    font-size: inherit !important; font-family: inherit !important;
  }
  .code-panel pre .cmt { color: #6b7280 !important; font-style: italic; }
  .code-panel pre .kw  { color: #7c3aed !important; font-weight: 700; }
  .code-panel[id]::before {
    content: attr(data-lang);
    display: block;
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700; font-size: 6.8pt; letter-spacing: 0.08em;
    text-transform: uppercase; color: #6d28d9;
    margin: 0 0 0.12rem;
  }

  /* Tables */
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
  thead th {
    background: #f1f5f9 !important; color: #0A1628 !important;
    font-family: 'Bricolage Grotesque', sans-serif !important; font-weight: 700 !important;
    font-size: 8pt !important; text-transform: uppercase; letter-spacing: 0.03em;
  }

  /* Architecture / phase cards (common across capstones) */
  .phase-card, .arch-card, .step-card, .phase-block {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 4px;
    padding: 0.55rem 0.75rem !important;
    margin: 0.4rem 0 !important;
    page-break-inside: avoid;
  }

  /* Build-guide steps */
  .build-step, .phase-step, .step {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 3px solid #6366F1 !important;
    border-radius: 4px;
    padding: 0.5rem 0.7rem !important;
    margin: 0.45rem 0 !important;
    orphans: 3; widows: 3;
  }

  /* Animation containers — light card with visible content */
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
    max-width: 100% !important; max-height: 145mm !important;
    height: auto !important; display: block; margin: 0 auto;
  }

  /* Force reveal-by-opacity elements visible */
  .arch-block, .lifecycle-stage, .ccd-box, .wf-step, .roadmap-track, .demo-step,
  .step, .lane, .iter-card, .compare-row, .phase-card, .build-step {
    opacity: 1 !important; transform: none !important;
    animation: none !important; transition: none !important;
  }
  svg [opacity="0"], svg [opacity="0.0"], svg [opacity="0.3"] { opacity: 1 !important; }

  /* Page-break */
  section.section { page-break-before: auto; }
  h2, h3 { page-break-after: avoid; }

  /* Reduce-motion safety */
  *, *::before, *::after { animation-duration: 0.001s !important; transition-duration: 0.001s !important; }
</style>
"""


# ---------------------------------------------------------------------------
# HTML transformation pipeline
# ---------------------------------------------------------------------------

def _strip_sections(html: str, ids: tuple[str, ...]) -> str:
    for sec_id in ids:
        pattern = re.compile(
            r'<section\b[^>]*\bid="' + re.escape(sec_id) + r'"[^>]*>.*?</section>\s*',
            re.DOTALL,
        )
        new_html, n = pattern.subn("", html)
        if n == 0:
            pass  # silently skip missing sections
        html = new_html
        # Clean sidebar anchor
        html = re.sub(
            r'<a\s+href="#' + re.escape(sec_id) + r'"[^>]*>.*?</a>\s*',
            '', html, flags=re.DOTALL,
        )
    return html


def build_study_html(src_html: str, extra_strip: list[str]) -> str:
    strip_ids = _COMMON_STRIP + tuple(extra_strip)
    html = _strip_sections(src_html, strip_ids)
    html = _label_code_panels(html)
    html = _pseudocodify_all(html)
    html = _wrap_comments_in_code(html)
    if "</body>" not in html:
        sys.exit("Source HTML has no </body> tag.")
    return html.replace("</body>", STUDY_GUIDE_CSS + PRINT_FINALIZE_JS + "</body>", 1)


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def _find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("Could not find Chrome or Edge.")


def render_one(entry: dict, browser: str) -> None:
    src: Path = entry["src"]
    out: Path = entry["out"]
    label = out.stem

    if not src.exists():
        print(f"  [skip] {src.name} — file not found")
        return

    print(f"[{label}] Reading {src.name} ...", flush=True)
    src_html = src.read_text(encoding="utf-8")
    study_html = build_study_html(src_html, entry["extra_strip"])

    out.parent.mkdir(parents=True, exist_ok=True)

    # Preserve previous output
    if out.exists():
        backup = out.with_name(f"{out.stem}-v1.pdf")
        try:
            if backup.exists():
                backup.unlink()
            shutil.copy2(out, backup)
            print(f"[{label}] Preserved previous as {backup.name}")
        except Exception as e:
            print(f"[{label}] (could not preserve previous: {e})")

    with tempfile.TemporaryDirectory(prefix=f"cap-study-{label}-", dir=out.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / f"{label}.html"
        tmp_html.write_text(study_html, encoding="utf-8")
        tmp_pdf = tmp_dir / "out.pdf"

        print(f"[{label}] Rendering PDF ...", flush=True)
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
            sys.exit(f"[{label}] Chrome exited with code {result.returncode}")
        if not tmp_pdf.exists():
            sys.exit(f"[{label}] Chrome did not produce a PDF.")

        try:
            shutil.move(str(tmp_pdf), out)
        except PermissionError:
            sys.exit(f"[{label}] Could not write {out}.")

    size_kb = out.stat().st_size / 1024
    print(f"[{label}] Wrote {out.name} ({size_kb:.0f} KB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--c", dest="capstone", type=int, default=None,
                    help="Build only this capstone number (1-7). Default: all.")
    ap.add_argument("--domain", choices=["A", "B", "C"], default=None,
                    help="For multi-domain capstones: build only this domain.")
    args = ap.parse_args()

    browser = _find_browser()

    entries = _CAPSTONE_REGISTRY
    if args.capstone is not None:
        entries = [e for e in entries if e["num"] == args.capstone]
    if args.domain is not None:
        entries = [e for e in entries if e.get("domain") == args.domain]

    if not entries:
        sys.exit("No matching capstones found — check --c and --domain values.")

    print(f"Building {len(entries)} study-guide PDF(s) ...\n")
    for entry in entries:
        render_one(entry, browser)

    print("\nDone.")


if __name__ == "__main__":
    main()
