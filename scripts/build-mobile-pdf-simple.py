"""Build a condensed cheat-sheet PDF from all mobile module HTMLs.

Per module, extracts: track badge, module number, title, subtitle, first
"Big Idea" paragraph, and key takeaway. Lays them out as compact cards so
multiple modules fit on a page. Output: output/mobile/all-mobile-modules.pdf
(overwrites the long version).
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

ROOT = Path(__file__).resolve().parent.parent
MOBILE_DIR = ROOT / "output" / "mobile"
OUT_PDF = MOBILE_DIR / "all-mobile-modules.pdf"


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


def extract(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    title_card = soup.select_one(".title-card")
    track = text_of(title_card.select_one(".track-badge")) if title_card else ""
    module_num = text_of(title_card.select_one(".module-number")) if title_card else ""
    title = text_of(title_card.select_one("h1")) if title_card else ""
    subtitle = text_of(title_card.select_one(".subtitle")) if title_card else ""

    big_idea_para = ""
    big_idea_heading = ""
    for card in soup.select(".mobile-card"):
        label = card.select_one(".card-label")
        if label and "big idea" in label.get_text(strip=True).lower():
            big_idea_heading = text_of(card.select_one("h2"))
            p = card.select_one("p")
            big_idea_para = text_of(p)
            break

    takeaway_text = ""
    takeaway_box = soup.select_one(".takeaway")
    if takeaway_box:
        first_p = takeaway_box.select_one("p")
        takeaway_text = text_of(first_p)

    return {
        "file": html_path.name,
        "track": track,
        "module_num": module_num,
        "title": title,
        "subtitle": subtitle,
        "big_idea_heading": big_idea_heading,
        "big_idea": big_idea_para,
        "takeaway": takeaway_text,
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Course Cheat Sheet — Building AI Agents with Claude</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
  @page { size: A4; margin: 14mm 14mm 14mm 14mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    color: #1a1f2e;
    font-family: 'Source Sans 3', -apple-system, sans-serif;
    font-size: 10pt;
    line-height: 1.45;
    background: #fff;
  }
  h1, h2, h3 { font-family: 'Bricolage Grotesque', sans-serif; }
  .cover {
    page-break-after: always;
    text-align: center;
    padding-top: 30vh;
  }
  .cover .eyebrow {
    font-size: 11pt;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #8a6a1a;
    font-weight: 700;
    margin-bottom: 1.5rem;
  }
  .cover h1 {
    font-size: 28pt;
    font-weight: 800;
    margin: 0 0 0.75rem;
    color: #0A1628;
    letter-spacing: -0.01em;
  }
  .cover .sub {
    font-size: 13pt;
    color: #4a5568;
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.5;
  }
  .cover .meta {
    margin-top: 3rem;
    font-size: 10pt;
    color: #718096;
  }
  .module {
    border: 1px solid #e2e8f0;
    border-left: 4px solid #6366F1;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    page-break-inside: avoid;
    background: #fafbfc;
  }
  .module .head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.4rem;
    margin-bottom: 0.5rem;
  }
  .module .num {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 9pt;
    font-weight: 700;
    color: #6366F1;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    white-space: nowrap;
  }
  .module .track {
    font-size: 8.5pt;
    color: #718096;
    font-weight: 600;
    text-align: right;
  }
  .module h2 {
    font-size: 13pt;
    font-weight: 700;
    margin: 0 0 0.35rem;
    color: #0A1628;
    line-height: 1.25;
  }
  .module .sub {
    font-size: 9pt;
    color: #4a5568;
    margin: 0 0 0.5rem;
    font-style: italic;
  }
  .module .lede {
    margin: 0.4rem 0;
    font-size: 9.5pt;
    color: #2d3748;
  }
  .module .takeaway {
    margin-top: 0.5rem;
    padding: 0.45rem 0.65rem;
    background: rgba(212, 168, 67, 0.08);
    border-left: 3px solid #D4A843;
    border-radius: 3px;
    font-size: 9pt;
    color: #2d3748;
  }
  .module .takeaway::before {
    content: "Takeaway · ";
    color: #8a6a1a;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 7.5pt;
    letter-spacing: 0.08em;
  }
  /* Track-color tinting */
  .track-1 { border-left-color: #6366F1; } .track-1 .num { color: #6366F1; }
  .track-2 { border-left-color: #10B981; } .track-2 .num { color: #10B981; }
  .track-3 { border-left-color: #F59E0B; } .track-3 .num { color: #B45309; }
  .track-4 { border-left-color: #8B5CF6; } .track-4 .num { color: #7c3aed; }
  .track-5 { border-left-color: #F43F5E; } .track-5 .num { color: #be123c; }
  .track-6 { border-left-color: #3B82F6; } .track-6 .num { color: #2563eb; }
  .track-7 { border-left-color: #14B8A6; } .track-7 .num { color: #0f766e; }
  .track-8 { border-left-color: #EC4899; } .track-8 .num { color: #be185d; }
  .track-9 { border-left-color: #D4A843; } .track-9 .num { color: #8a6a1a; }
</style>
</head>
<body>
<section class="cover">
  <div class="eyebrow">Cheat Sheet</div>
  <h1>Building AI Agents with Claude</h1>
  <div class="sub">A condensed reference of every module — the big idea and key takeaway, in one sitting.</div>
  <div class="meta">__MODULE_COUNT__ modules · From Hello World to Autonomous Production Systems</div>
</section>
__MODULES__
</body>
</html>
"""


def track_class(track: str) -> str:
    m = re.search(r"Track\s*(\d+)", track)
    return f"track-{m.group(1)}" if m else "track-1"


def render_module(mod: dict) -> str:
    klass = track_class(mod["track"])
    parts = [f'<div class="module {klass}">',
             '<div class="head">',
             f'<span class="num">{mod["module_num"] or "Module"}</span>',
             f'<span class="track">{mod["track"]}</span>',
             '</div>',
             f'<h2>{mod["title"]}</h2>']
    if mod["subtitle"]:
        parts.append(f'<p class="sub">{mod["subtitle"]}</p>')
    if mod["big_idea"]:
        parts.append(f'<p class="lede">{mod["big_idea"]}</p>')
    if mod["takeaway"]:
        parts.append(f'<div class="takeaway">{mod["takeaway"]}</div>')
    parts.append('</div>')
    return "\n".join(parts)


def main() -> None:
    browser = find_browser()
    files = sorted(MOBILE_DIR.glob("M*-mobile.html"), key=lambda p: order_key(p.name))
    if not files:
        sys.exit(f"No mobile HTML files found in {MOBILE_DIR}")

    modules = [extract(f) for f in files]
    body = "\n".join(render_module(m) for m in modules)
    html_doc = HTML_TEMPLATE.replace("__MODULES__", body).replace("__MODULE_COUNT__", str(len(modules)))

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mobile-pdf-simple-", dir=OUT_PDF.parent) as tmp:
        tmp_dir = Path(tmp)
        tmp_html = tmp_dir / "cheatsheet.html"
        tmp_html.write_text(html_doc, encoding="utf-8")
        tmp_pdf = tmp_dir / "out.pdf"
        OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--virtual-time-budget=8000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        try:
            tmp_pdf.replace(OUT_PDF)
            final_path = OUT_PDF
        except PermissionError:
            final_path = OUT_PDF.with_name(OUT_PDF.stem + ".new.pdf")
            tmp_pdf.replace(final_path)
            print(f"NOTE: {OUT_PDF.name} is locked (open in viewer?); wrote to {final_path.name} instead.")

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
