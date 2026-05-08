"""Combine all mobile module HTMLs into one PDF.

Renders each output/mobile/M*-mobile.html via headless Chrome, then merges the
per-module PDFs in curriculum order (M00, M01, M02, M03, M03B, M04, ...).
Output: output/mobile/all-mobile-modules.pdf
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfWriter

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
    sys.exit("No Chrome or Edge install found in standard Windows locations.")


def order_key(name: str) -> tuple[int, str]:
    m = re.match(r"M(\d+)([A-Z]?)", name)
    if not m:
        return (9999, "")
    return (int(m.group(1)), m.group(2) or "")


def html_to_pdf(browser: str, html: Path, pdf: Path) -> None:
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--virtual-time-budget=8000",
            f"--print-to-pdf={pdf}",
            html.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    browser = find_browser()
    files = sorted(MOBILE_DIR.glob("M*-mobile.html"), key=lambda p: order_key(p.name))
    if not files:
        sys.exit(f"No mobile HTML files found in {MOBILE_DIR}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="mobile-pdf-"))
    try:
        pdfs: list[Path] = []
        for i, html in enumerate(files, 1):
            pdf = tmp_dir / f"{i:02d}-{html.stem}.pdf"
            print(f"[{i:2d}/{len(files)}] rendering {html.name}", flush=True)
            html_to_pdf(browser, html, pdf)
            pdfs.append(pdf)

        print(f"Merging {len(pdfs)} PDFs ...", flush=True)
        writer = PdfWriter()
        for pdf in pdfs:
            writer.append(str(pdf))
        OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_PDF, "wb") as fh:
            writer.write(fh)
        size_kb = OUT_PDF.stat().st_size / 1024
        print(f"Wrote {OUT_PDF} ({size_kb:.0f} KB, {len(pdfs)} modules)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
