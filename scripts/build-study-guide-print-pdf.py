"""Generate a printer-friendly PDF from output/study-guide.html.

Transforms the interactive dark-theme HTML into a clean A4 print layout:
- All <details> expanded (no hidden content)
- Controls bar removed
- White background, black text
- Proper page breaks between tracks
- Colour-coded section labels preserved
- Pseudocode blocks styled for print

Output: output/pdf/study-guide-print-clean.pdf
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths / Chrome
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "output" / "study-guide.html"
OUT_PDF  = ROOT / "output" / "pdf" / "study-guide-print-clean.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("No Chrome or Edge installation found on this machine.")


# ---------------------------------------------------------------------------
# Print-override CSS injected into the <head>
# ---------------------------------------------------------------------------

PRINT_CSS = """
<style id="print-override">
/* ── Page layout ── */
@page {
  size: A4;
  margin: 12mm 12mm 12mm 12mm;
}
@page :first {
  margin-top: 18mm;
}

html, body {
  background: #fff !important;
  color: #111 !important;
  font-family: 'Source Sans 3', system-ui, sans-serif;
  font-size: 9pt;
  line-height: 1.45;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* ── Hide interactive chrome ── */
.controls,
.toc-toggle,
.filter-pills,
.empty,
footer { display: none !important; }

/* ── Cover ── */
header.cover {
  background: none !important;
  border-bottom: 2px solid #ccc !important;
  margin-bottom: 1rem;
  padding: 1.5rem 0 1rem !important;
  page-break-after: avoid;
}
.cover .eyebrow { color: #7a5a00 !important; font-size: 8pt; }
.cover h1 { color: #0A1628 !important; font-size: 20pt; }
.cover .tag { color: #333 !important; }
.cover .meta { color: #666 !important; }

/* ── Wrap ── */
.wrap { max-width: none !important; padding: 0 !important; }

/* ── Track sections ── */
section.track {
  page-break-inside: avoid;
  break-inside: avoid;
}
section.track:not(:first-of-type) {
  page-break-before: auto;
  margin-top: 1.2rem;
}
.track-head {
  color: #7a5a00 !important;
  border-bottom: 2px solid #d4a843 !important;
  font-size: 8pt;
  margin-bottom: 0.5rem;
  padding-bottom: 0.3rem;
}

/* ── Module cards: always expanded ── */
details.module {
  background: #fff !important;
  border: 1px solid #ccc !important;
  border-radius: 6px !important;
  margin-bottom: 0.45rem;
  page-break-inside: avoid;
  break-inside: avoid;
  overflow: visible !important;
}
details.module[open] { border-color: #d4a843 !important; }

details.module summary {
  background: #f8f5ec !important;
  color: #111 !important;
  padding: 0.5rem 0.75rem !important;
  min-height: auto !important;
  cursor: default;
  font-size: 10pt;
  font-weight: 700;
}
details.module summary .mid {
  color: #7a5a00 !important;
  background: #fdf3d4 !important;
  border-color: #e7cb6a !important;
  font-size: 8pt;
}
details.module summary .arrow { display: none !important; }

/* Force body visible even on non-[open] details (print fallback) */
details.module .body,
details.module:not([open]) .body {
  display: block !important;
}

/* ── Body internals ── */
.body { padding: 0.4rem 0.75rem 0.6rem !important; }
.body .label {
  color: #4a5568 !important;
  font-size: 7.5pt;
  margin-top: 0.6rem;
  margin-bottom: 0.2rem;
}
.body .core {
  color: #111 !important;
  font-size: 9pt;
}
.body .core em.tag { color: #7a5a00 !important; }

/* ── Pseudocode ── */
pre.code {
  background: #f4f4f8 !important;
  color: #111 !important;
  border-left-color: #6366F1 !important;
  border-radius: 0 4px 4px 0 !important;
  font-size: 7.5pt !important;
  line-height: 1.5 !important;
  padding: 0.5rem 0.75rem !important;
  white-space: pre-wrap !important;
  overflow: visible !important;
}

/* Syntax highlight in print */
pre.code .kw  { color: #7c3aed !important; font-weight: 700; }
pre.code .fn  { color: #0e6e5e !important; }
pre.code .str { color: #1565a0 !important; }
pre.code .cm  { color: #6b7280 !important; font-style: italic; }
pre.code .num { color: #166534 !important; }

/* ── Misconception box ── */
.misc {
  background: #fff5f5 !important;
  border-color: rgba(220,38,38,.4) !important;
  font-size: 8.5pt !important;
}
.misc .x { color: #b91c1c !important; }
.misc .v { color: #15803d !important; }
.misc em { font-style: italic; color: #b91c1c !important; }

/* ── Quick Reference Cards ── */
.qrc { border-top: 2px solid #ccc !important; page-break-before: always; margin-top: 0 !important; }
.qrc h2 { color: #7a5a00 !important; font-size: 14pt; }
.qrc h3 { color: #111 !important; border-left-color: #d4a843 !important; font-size: 10pt; }
.qrc-grid {
  background: #f8f8f8 !important;
  border-color: #ccc !important;
  font-size: 8.5pt;
}
.qrc-grid .k { color: #7a5a00 !important; }
.qrc-grid .v { color: #333 !important; }
</style>
"""


# ---------------------------------------------------------------------------
# Transform HTML for print
# ---------------------------------------------------------------------------

def build_print_html(src: Path) -> str:
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")

    # 1. Open all <details> elements
    for details in soup.find_all("details"):
        details["open"] = ""

    # 2. Remove interactive elements
    for sel in [".controls", "#filters", "#empty", "#q"]:
        for el in soup.select(sel):
            el.decompose()

    # 3. Remove the footer link back to desktop
    for footer in soup.find_all("footer"):
        footer.decompose()

    # 4. Inject print CSS just before </head>
    head = soup.find("head")
    if head:
        head.append(BeautifulSoup(PRINT_CSS, "html.parser"))

    # 5. Update title
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = "Study Guide — Building AI Agents with Claude (Print)"

    return str(soup)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not SRC_HTML.exists():
        sys.exit(f"Source not found: {SRC_HTML}")

    browser = find_browser()
    print(f"Source : {SRC_HTML}")
    print(f"Browser: {browser}")

    print("Transforming HTML for print …")
    html_doc = build_print_html(SRC_HTML)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sg-print-") as tmp:
        tmp_html = Path(tmp) / "study-guide-print.html"
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
                "--virtual-time-budget=15000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )

        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF — check Chrome flags support.")

        # Move (shutil handles cross-drive moves)
        candidates = [OUT_PDF] + [
            OUT_PDF.with_name(f"{OUT_PDF.stem}-new{i}.pdf") for i in range(1, 10)
        ]
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

    size_kb = dest.stat().st_size / 1024
    print(f"Wrote  : {dest}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
