#!/usr/bin/env python3
"""Rebuild the print-edition PDFs by driving a headless Chromium.

The PDFs under output/ that this script rebuilds were never made with
reportlab, whatever prompts/19-study-guide.md says -- every one of them carries
`Producer: Skia/PDF` and a Mozilla creator string, i.e. a browser print of the
styled HTML. This script is that pipeline, written down:

    source HTML  ->  inject print CSS  ->  headless --print-to-pdf  ->  merge

    python scripts/build-print-pdfs.py --list
    python scripts/build-print-pdfs.py --target cc-study-guide
    python scripts/build-print-pdfs.py                    # every target

Why the CSS injection is not optional: the mobile decks set
`.deck { height: 100vh; overflow-y: auto }` for swipe navigation, so a plain
print renders the first card and stops. M02 prints as 1 page untouched and 20
pages with the override.

Not reproduced here: quick-reference-all-concepts.pdf and
CC-study-guide-condensed.pdf. Those are condensed *derivations* -- content
extracted and re-laid-out, not pages printed -- and the logic that produced
them was never committed. scripts/build-study-guide.py is the supported way to
build that shape for the agents course.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    sys.exit("pypdf is required:  pip install pypdf")

REPO = Path(__file__).resolve().parent.parent
PRINT_TIMEOUT = 180  # seconds per page; the big decks are genuinely slow


# ---------------------------------------------------------------------
# Print CSS
# ---------------------------------------------------------------------
# Applied to every page before printing. Three jobs: unroll any viewport-locked
# scroller, drop the on-screen navigation chrome that means nothing on paper,
# and keep the dark theme (browsers drop backgrounds in print unless told).
_PRINT_CSS_BODY = """
  html, body { height: auto !important; overflow: visible !important; }

  /* Deck generation 1 -- vertical scroll-snap container. */
  .deck { height: auto !important; overflow: visible !important;
          scroll-snap-type: none !important; display: block !important; }
  .mobile-card { min-height: 0 !important; height: auto !important;
                 padding: .55rem .75rem !important;
                 scroll-snap-align: none !important; }

  /* Deck generation 2 -- HORIZONTAL flex deck: #deck is display:flex with
     overflow-x:auto and .card is flex:0 0 100vw. Without this block the whole
     module prints as a single page; that is how M24 shipped as 1 page. */
  #deck { display: block !important; overflow: visible !important;
          scroll-snap-type: none !important; }
  #deck > .card, .card { flex: none !important; width: auto !important;
                         height: auto !important; overflow: visible !important;
                         scroll-snap-align: none !important; }

  /* On-screen chrome, across all generations. */
  .module-nav-row, .deck-progress, .card-menu, .sidebar, .toc-sidebar,
  .search-assistant, .search-widget, #search-assistant, .back-to-top,
  .module-nav-btn, .skip-link, .menu-fab, .menu-overlay,
  #top-bar, #bottom-nav, #nav-dots, #progress-bar-wrap { display: none !important; }

  /* Cross-page navigation links. The CC pages mark these up with an
     aria-label and an inline style and no class, so match the label. */
  a[aria-label*="Home" i], a[aria-label*="Previous" i],
  a[aria-label*="Next module" i] { display: none !important; }

  /* Backgrounds and accent colours survive the print pipeline. */
  * { -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important; }

  /* Never strand a heading at the foot of a page. */
  h1, h2, h3 { break-after: avoid; page-break-after: avoid; }
"""

# Whether a card may be split across a page boundary. Keeping cards whole costs
# roughly a third more pages (M02: 20 vs 15) because a card taller than half a
# page pushes to the next one -- but a deck is card-shaped by design and a
# reference you flip through is worth more than a shorter one.
DENSITY = {
    "readable": ".card-inner { break-inside: avoid; page-break-inside: avoid; }",
    "compact": "",
}


def print_css(density: str = "readable") -> str:
    return (f'<style id="print-edition-overrides">@media print {{'
            f'{_PRINT_CSS_BODY}{DENSITY[density]}}}</style>')

COVER_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{ margin: 0; }}
  html, body {{ margin: 0; padding: 0; height: 100%; }}
  body {{ background: #0A1628; color: #E8ECF1; display: flex; height: 100vh;
          flex-direction: column; align-items: center; justify-content: center;
          font-family: 'Segoe UI', system-ui, sans-serif; text-align: center;
          -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .kicker {{ font-size: 13px; letter-spacing: .32em; text-transform: uppercase;
             color: #D4A843; margin-bottom: 2.4rem; }}
  h1 {{ font-size: 44px; font-weight: 800; margin: 0 0 1rem; max-width: 22ch;
        line-height: 1.12; }}
  p {{ color: #93A3B8; font-size: 16px; max-width: 46ch; line-height: 1.6;
       margin: 0 0 2.6rem; }}
  .meta {{ font-size: 12.5px; color: #6B7C93; letter-spacing: .05em; }}
  .rule {{ width: 64px; height: 3px; background: #D4A843; margin: 0 0 2.2rem; }}
</style>
<div class="kicker">Print Edition</div>
<h1>{title}</h1>
<div class="rule"></div>
<p>{blurb}</p>
<div class="meta">{meta}</div>
"""


# ---------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------
@dataclass
class Target:
    name: str
    out: str                          # repo-relative output PDF
    glob: str                         # repo-relative glob for source pages
    title: str = ""
    blurb: str = ""
    cover: bool = True
    zip_it: bool = False
    order: object = None              # optional sort key over Path
    extra_css: str = ""
    sources: list = field(default_factory=list)


def _module_order(path: Path) -> tuple:
    """M9 before M10, CC9 before CC10 -- digits sort numerically."""
    import re
    m = re.match(r"^(?:M|CC)(\d+)([A-Z]*)", path.name, re.I)
    return (int(m.group(1)), m.group(2).upper()) if m else (999, path.name)


TARGETS = [
    Target(
        name="mobile-print-edition",
        out="output/mobile/all-mobile-modules.pdf",
        glob="output/mobile/M*-mobile.html",
        title="Building AI Agents with Claude",
        blurb="The mobile course as one document. Every module's big idea, "
              "analogy, mechanics, pseudocode and misconceptions, laid out "
              "for offline reading.",
        cover=True,
        zip_it=True,
        order=_module_order,
    ),
    Target(
        name="cc-study-guide",
        out="output/courses/cc/CC-study-guide.pdf",
        glob="output/courses/cc/CC[0-9]*.html",
        title="Claude Code Mastery",
        # The committed CC-study-guide.pdf opens on CC0, not a cover page.
        cover=False,
        order=_module_order,
    ),
]


# ---------------------------------------------------------------------
# Browser
# ---------------------------------------------------------------------
_BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
_ON_PATH = ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge")


def find_browser(explicit: str | None = None) -> str:
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit(f"--browser not found: {explicit}")
        return explicit
    for candidate in _BROWSERS:
        if os.path.isfile(candidate):
            return candidate
    for name in _ON_PATH:
        found = shutil.which(name)
        if found:
            return found
    sys.exit(
        "No Chromium-family browser found. Install Chrome or Edge, or pass\n"
        "  --browser /path/to/chrome"
    )


def print_page(browser: str, src: Path, dst: Path, extra_css: str = "",
               density: str = "readable") -> int:
    """Print one HTML file. Returns the page count."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    html = src.read_text(encoding="utf-8", errors="replace")

    # Anchor on the LAST </body>: course pages show markup inside code samples,
    # and splitting on the first one injects the CSS into a code block.
    close = html.lower().rfind("</body>")
    payload = print_css(density) + (f"<style>@media print{{{extra_css}}}</style>" if extra_css else "")
    staged = src.parent / f".print-{os.getpid()}-{src.name}"
    staged.write_text(
        html + payload if close == -1 else html[:close] + payload + html[close:],
        encoding="utf-8",
    )
    # Staged next to the original on purpose: relative asset paths and any
    # same-directory links have to keep resolving.
    try:
        proc = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--no-sandbox", "--run-all-compositor-stages-before-draw",
             "--virtual-time-budget=10000",
             f"--print-to-pdf={dst}", staged.as_uri()],
            capture_output=True, timeout=PRINT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        staged.unlink(missing_ok=True)
        raise RuntimeError(f"timed out after {PRINT_TIMEOUT}s printing {src.name}")
    finally:
        staged.unlink(missing_ok=True)

    if not dst.is_file() or dst.stat().st_size == 0:
        tail = (proc.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-3:]
        raise RuntimeError(f"no PDF produced for {src.name}: {' | '.join(tail)}")
    return len(PdfReader(str(dst)).pages)


def render_cover(browser: str, target: Target, count: int, workdir: Path,
                 built_on: str) -> Path:
    meta = f"{count} modules  ·  built {built_on}"
    html = COVER_TEMPLATE.format(title=target.title, blurb=target.blurb, meta=meta)
    src = workdir / "cover.html"
    src.write_text(html, encoding="utf-8")
    dst = workdir / "cover.pdf"
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--no-sandbox", f"--print-to-pdf={dst}", src.as_uri()],
        capture_output=True, timeout=PRINT_TIMEOUT,
    )
    if not dst.is_file():
        raise RuntimeError("cover page failed to render")
    return dst


def merge(parts: list[Path], out: Path) -> int:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    # Each part embeds its own font subsets; this is what keeps the merged file
    # from being the naive sum of its inputs.
    try:
        writer.compress_identical_objects()
    except AttributeError:
        pass
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        writer.write(fh)
    return len(writer.pages)


# ---------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------
def resolve_sources(target: Target) -> list[Path]:
    paths = sorted(REPO.glob(target.glob))
    paths = [p for p in paths if not p.name.startswith(".print-")]
    if target.order is not None:
        paths.sort(key=target.order)
    return paths


def build(target: Target, browser: str, keep: bool, built_on: str,
          density: str = "readable") -> bool:
    sources = resolve_sources(target)
    if not sources:
        print(f"  ! {target.name}: no sources match {target.glob} -- skipped")
        return False

    print(f"\n{target.name}  ({len(sources)} pages -> {target.out})")
    workdir = Path(tempfile.mkdtemp(prefix=f"printpdf-{target.name}-"))
    parts: list[Path] = []
    collapsed: list[str] = []
    try:
        if target.cover:
            parts.append(render_cover(browser, target, len(sources), workdir, built_on))
            print("    cover")
        for i, src in enumerate(sources, 1):
            dst = workdir / f"{i:03d}-{src.stem}.pdf"
            pages = print_page(browser, src, dst, target.extra_css, density)
            parts.append(dst)
            # A viewport-locked scroller this script does not know how to
            # unroll collapses to a single page and is otherwise silent.
            suspect = "  <-- SUSPECT: scroller not unrolled?" if pages <= 1 else ""
            if suspect:
                collapsed.append(src.name)
            print(f"    [{i:2d}/{len(sources)}] {src.name[:46]:46s} {pages:3d} pp{suspect}")

        out = REPO / target.out
        total = merge(parts, out)
        size_mb = out.stat().st_size / 1048576
        print(f"    -> {target.out}  {total} pages, {size_mb:.1f} MB")

        if collapsed:
            print(f"    ! {len(collapsed)} page(s) printed as a single page and are "
                  f"probably missing content:")
            for name in collapsed:
                print(f"        {name}")

        if target.zip_it:
            archive = out.with_suffix(".zip")
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(out, out.name)
            print(f"    -> {archive.relative_to(REPO)}  "
                  f"{archive.stat().st_size / 1048576:.1f} MB")
        return True
    finally:
        if keep:
            print(f"    intermediates kept in {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", action="append",
                    help="build only this target (repeatable)")
    ap.add_argument("--list", action="store_true", help="list targets and exit")
    ap.add_argument("--browser", help="path to a Chromium-family browser")
    ap.add_argument("--keep-intermediates", action="store_true",
                    help="leave the per-page PDFs on disk for inspection")
    ap.add_argument("--date", default=None, help="override the cover build date")
    ap.add_argument("--density", choices=tuple(DENSITY), default="readable",
                    help="readable keeps every card whole (default); "
                         "compact lets cards split across pages, ~25%% fewer pages")
    args = ap.parse_args()

    if args.list:
        print("Targets:")
        for t in TARGETS:
            found = len(resolve_sources(t))
            print(f"  {t.name:22s} {found:3d} source pages -> {t.out}")
        print("\nNot built by this script (condensed derivations, not prints):")
        print("  output/mobile/quick-reference-all-concepts.pdf")
        print("  output/courses/cc/CC-study-guide-condensed.pdf")
        print("  -> see scripts/build-study-guide.py")
        return 0

    wanted = TARGETS
    if args.target:
        names = {t.name for t in TARGETS}
        unknown = set(args.target) - names
        if unknown:
            sys.exit(f"unknown target(s): {', '.join(sorted(unknown))}\n"
                     f"known: {', '.join(sorted(names))}")
        wanted = [t for t in TARGETS if t.name in set(args.target)]

    browser = find_browser(args.browser)
    print(f"Browser: {browser}")
    built_on = args.date or _dt.date.today().isoformat()

    failures = 0
    for target in wanted:
        try:
            if not build(target, browser, args.keep_intermediates, built_on,
                         args.density):
                failures += 1
        except (RuntimeError, OSError) as exc:
            print(f"    FAILED: {exc}")
            failures += 1

    print(f"\n{len(wanted) - failures}/{len(wanted)} targets built")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
