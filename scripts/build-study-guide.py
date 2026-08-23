#!/usr/bin/env python3
"""Build the condensed study guide PDF described in prompts/19-study-guide.md.

Reads the mobile module decks in output/mobile/, pulls four things out of each
one -- title, the Big Idea, the key pseudocode, the misconception worth
remembering -- and lays them out as a print-ready reference with a cover page,
a table of contents with real page numbers, and the quick-reference cards from
scripts/study-guide-quickref.md.

    python scripts/build-study-guide.py --check          # extract only, report gaps
    python scripts/build-study-guide.py                  # A4 + Letter
    python scripts/build-study-guide.py --size a4 --one-per-page

A note on what this does NOT do. The PDFs that used to live in output/mobile/
and output/courses/cc/ were not made with reportlab -- every one of them
reports `Producer: Skia/PDF`, i.e. a headless Chromium print of the styled
HTML. Those are page-faithful renders of the course pages. This script builds
the *condensed* guide from prompts/19-study-guide.md, which is a different
artifact and never existed as a file. It does not reproduce them.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import os
import re
import sys
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    sys.exit("bs4 is required:  pip install beautifulsoup4")

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        KeepTogether,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        Preformatted,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
except ImportError:  # pragma: no cover
    sys.exit("reportlab is required:  pip install reportlab")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE_DIR = os.path.join(REPO, "output", "mobile")
QUICKREF = os.path.join(REPO, "scripts", "study-guide-quickref.md")
INDEX_HTML = os.path.join(REPO, "output", "courses", "claude-agents", "index.html")
DEFAULT_OUT = os.path.join(REPO, "output")

COURSE_TITLE = "Building AI Agents with Claude"
COURSE_SUB = "From Hello World to Autonomous Production Systems"

# Course palette, from prompts/19-study-guide.md.
BG = colors.HexColor("#0A1628")
CARD_BG = colors.HexColor("#122036")
TEXT = colors.HexColor("#E8ECF1")
MUTED = colors.HexColor("#93A3B8")
GOLD = colors.HexColor("#D4A843")
RULE = colors.HexColor("#22344F")

MAX_PATTERN_LINES = 8


# ---------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------
# The course faces (Bricolage Grotesque, Source Sans 3, JetBrains Mono) are
# webfonts and are not on disk here. Preference order: real course fonts if
# someone drops them in assets/fonts/, then any Unicode system TTF, then the
# base-14 Type1 faces -- which are WinAnsi-only, so that last case also turns
# on transliteration of the arrows and math symbols the course prose uses.

_FONT_CANDIDATES = {
    "sans": [
        ("assets/fonts", ("SourceSans3-Regular.ttf", "BricolageGrotesque-Regular.ttf")),
        ("C:/Windows/Fonts", ("segoeui.ttf", "arial.ttf", "calibri.ttf")),
        ("/usr/share/fonts/truetype/dejavu", ("DejaVuSans.ttf",)),
        ("/System/Library/Fonts", ("Helvetica.ttc",)),
    ],
    "sans_bold": [
        ("assets/fonts", ("SourceSans3-Bold.ttf", "BricolageGrotesque-Bold.ttf")),
        ("C:/Windows/Fonts", ("segoeuib.ttf", "arialbd.ttf", "calibrib.ttf")),
        ("/usr/share/fonts/truetype/dejavu", ("DejaVuSans-Bold.ttf",)),
    ],
    "mono": [
        ("assets/fonts", ("JetBrainsMono-Regular.ttf",)),
        ("C:/Windows/Fonts", ("consola.ttf", "cour.ttf")),
        ("/usr/share/fonts/truetype/dejavu", ("DejaVuSansMono.ttf",)),
    ],
    "mono_bold": [
        ("assets/fonts", ("JetBrainsMono-Bold.ttf",)),
        ("C:/Windows/Fonts", ("consolab.ttf", "courbd.ttf")),
        ("/usr/share/fonts/truetype/dejavu", ("DejaVuSansMono-Bold.ttf",)),
    ],
}

_BASE14 = {
    "sans": "Helvetica",
    "sans_bold": "Helvetica-Bold",
    "mono": "Courier",
    "mono_bold": "Courier-Bold",
}

# Only consulted when we fall back to base-14, which cannot encode these.
_TRANSLIT = {
    "\u2192": "->", "\u2190": "<-", "\u2194": "<->", "\u21d2": "=>",
    "\u2248": "~=", "\u2264": "<=", "\u2265": ">=", "\u2260": "!=",
    "\u00d7": "x", "\u2022": "*", "\u2026": "...", "\u2713": "y",
    "\u2717": "n", "\u23f1": "", "\u2500": "-", "\u2502": "|",
}


def resolve_fonts(verbose: bool = False) -> tuple[dict[str, str], bool]:
    """Register the best fonts available. Returns (names, unicode_ok)."""
    names: dict[str, str] = {}
    for role, candidates in _FONT_CANDIDATES.items():
        for directory, filenames in candidates:
            base = directory if os.path.isabs(directory) else os.path.join(REPO, directory)
            for filename in filenames:
                path = os.path.join(base, filename)
                if not os.path.isfile(path):
                    continue
                registered = f"guide-{role}"
                try:
                    pdfmetrics.registerFont(TTFont(registered, path))
                except Exception:
                    continue
                names[role] = registered
                if verbose:
                    print(f"  font {role:10s} -> {path}")
                break
            if role in names:
                break

    unicode_ok = "sans" in names and "mono" in names
    for role, fallback in _BASE14.items():
        names.setdefault(role, fallback)
    if not unicode_ok and verbose:
        print("  no Unicode TTF found -- using base-14 and transliterating symbols")
    return names, unicode_ok


# ---------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------
@dataclass
class Module:
    ident: str                       # "M03B"
    sort_key: tuple                  # (3, "B")
    path: str
    name: str = ""
    tagline: str = ""
    track: str = "Unsorted"
    meta: str = ""
    core: str = ""
    pattern: str = ""
    watch_out: str = ""
    gaps: list[str] = field(default_factory=list)


_IDENT = re.compile(r"^(M)(\d+)([A-Z]*)-", re.I)

# Headings that are navigation furniture, never the module's central claim.
_NOT_A_BIG_IDEA = {
    "concept index", "concept map", "module", "what you'll learn",
    "what you will learn", "contents", "analogy", "how it works",
}

_TRACK_HEAD = re.compile(r"Track\s*(\d)\s*[:—-]\s*([A-Za-z0-9 &;,'\-]{3,40})")


def load_track_map(index_path: str = INDEX_HTML) -> dict[str, str]:
    """Module -> track, read from the course landing page.

    index.html is the only place that states the track structure once. The
    mobile decks each carry their own track string and they disagree with each
    other ("Track 7: Production" vs "Track 7: Production Deployment",
    "Foundation Track" vs "Track 1: Foundations"), so the landing page wins and
    the deck is only a fallback.

    First assignment wins on purpose: the Track 9 block on that page is the
    full learning path and re-lists every module, so a last-wins scan would
    file the entire course under Certification.
    """
    if not os.path.isfile(index_path):
        return {}
    with open(index_path, encoding="utf-8") as fh:
        html = fh.read()

    heads: list[tuple[int, str]] = []
    for match in _TRACK_HEAD.finditer(html):
        name = f"Track {match.group(1)}: {match.group(2).strip().rstrip('&;,-').strip()}"
        if heads and heads[-1][1].split(":")[0] == name.split(":")[0]:
            continue
        heads.append((match.start(), name))

    mapping: dict[str, str] = {}
    for i, (start, name) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(html)
        for ident in re.findall(r"\bM(\d{2}[A-Z]?)\b", html[start:end]):
            mapping.setdefault(f"M{ident}", name)
    return mapping


def _sort_key(filename: str) -> tuple:
    m = _IDENT.match(os.path.basename(filename))
    if not m:
        return (999, "")
    return (int(m.group(2)), m.group(3).upper())


def _ident(filename: str) -> str:
    m = _IDENT.match(os.path.basename(filename))
    return f"M{int(m.group(2)):02d}{m.group(3).upper()}" if m else "M??"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


# Three title shapes are in the wild:
#   "M02 Mobile: Tokens | Claude Agent Course"
#   "M00: Course Overview & Agent Lifecycle (Mobile) | Building AI Agents..."
#   "M14 · Multi-Agent Systems — Mobile"
_TITLE_LEAD = re.compile(r"^\s*M\d+[A-Z]*\s*(?:Mobile\s*:|[:·–—-])\s*", re.I)
_TITLE_TAIL = re.compile(r"\s*(?:\(\s*Mobile\s*\)|[–—-]\s*Mobile)\s*$", re.I)


def _name_from_title(raw: str) -> str:
    text = _clean(raw).split("|")[0]
    text = _TITLE_LEAD.sub("", text)
    text = _TITLE_TAIL.sub("", text)
    return _clean(text)


def _first_sentences(text: str, limit: int = 240) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: stop + 1] if stop > 60 else cut.rstrip() + "\u2026").strip()


def _pattern_from(block) -> str:
    """Flatten a .pseudocode block, preserving its own line breaks."""
    raw = block.get_text()
    lines = [ln.rstrip() for ln in raw.splitlines()]
    # The syntax-highlight spans leave stray blank lines behind; collapse them.
    out: list[str] = []
    for line in lines:
        if not line.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line)
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    # Prefer signal over leading commentary when we have to truncate.
    if len(out) > MAX_PATTERN_LINES:
        while out and out[0].lstrip().startswith("#") and len(out) > MAX_PATTERN_LINES:
            out.pop(0)
        out = out[:MAX_PATTERN_LINES]
        out.append("...")
    return "\n".join(out)


def _canonical_for_number(track_map: dict[str, str], number: str) -> str | None:
    """The landing page's name for 'Track N', if it names one."""
    prefix = f"Track {number}:"
    for name in track_map.values():
        if name.startswith(prefix):
            return name
    return None


def extract(path: str, track_map: dict[str, str] | None = None) -> Module:
    track_map = track_map or {}
    mod = Module(ident=_ident(path), sort_key=_sort_key(path), path=path)
    with open(path, encoding="utf-8") as fh:
        soup = BeautifulSoup(fh.read(), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    title_card = soup.select_one(".title-card")

    # Name comes from <title>, which is the only field all three deck
    # generations format consistently. The .module-name element looks like the
    # obvious source but nests the tagline inside itself in some generations
    # and part of the name in others, so reading it structurally yields
    # "Planning &" as often as it yields a whole title.
    if soup.title:
        mod.name = _name_from_title(soup.title.get_text())
    if not mod.name:
        holder = title_card.select_one(".module-name") if title_card else None
        if holder is not None:
            mod.name = _clean(holder.get_text(" "))
    if not mod.name:
        heading = soup.find("h1")
        if heading is not None:
            mod.name = _clean(heading.get_text(" "))
    if not mod.name:
        mod.name = mod.ident
        mod.gaps.append("name")

    # A tagline only counts when .module-name is the name plus something extra;
    # otherwise the nested element is part of the name and already captured.
    holder = title_card.select_one(".module-name") if title_card else None
    if holder is not None:
        whole = _clean(holder.get_text(" "))
        if whole.lower().startswith(mod.name.lower()) and len(whole) > len(mod.name) + 4:
            mod.tagline = whole[len(mod.name):].strip(" -—:·")

    if title_card and title_card.select_one(".title-meta"):
        mod.meta = _clean(title_card.select_one(".title-meta").get_text())

    # Track: landing page first, the deck's own claim second.
    if mod.ident in track_map:
        mod.track = track_map[mod.ident]
    else:
        row = title_card.select_one(".track-row") if title_card else None
        claimed = _clean(row.get_text("|", strip=True).split("|")[0]) if row else ""
        # A module the landing page omits still knows its own track number.
        # Fold it into the canonical name for that number rather than letting
        # "Track 7: Production" stand as a track of its own alongside
        # "Track 7: Deployment" (this is how M21B surfaced as an 11th track).
        number = re.match(r"Track\s*(\d)", claimed)
        canonical = _canonical_for_number(track_map, number.group(1)) if number else None
        mod.track = canonical or claimed or "Unsorted"
        if not claimed:
            mod.gaps.append("track")

    # Core. Three deck generations shipped over the life of this course and
    # each labels its Big Idea differently, so try them in order of how
    # explicit the signal is and only fall back to bare headings last.
    heading = None
    for label in soup.select(".section-label, .card-label, .card-type-chip"):
        if "big idea" not in label.get_text(strip=True).lower():
            continue
        card = label.find_parent(class_=("card-inner", "card")) or label.parent
        heading = card.find(["h2", "h3"]) or label.find_next(["h2", "h3"])
        if heading is not None:
            break
    if heading is None:
        for candidate in soup.find_all(["h2", "h3"]):
            text = _clean(candidate.get_text(" "))
            if text and text.lower().rstrip(":") not in _NOT_A_BIG_IDEA and len(text) > 8:
                heading = candidate
                break
    if heading is not None:
        mod.core = _clean(heading.get_text(" "))
        # A heading like "Two different crafts" is a title, not a definition.
        if len(mod.core) < 55:
            para = heading.find_next("p")
            if para is not None:
                mod.core = f"{mod.core} \u2014 {_first_sentences(para.get_text(' '), 150)}"
    if not mod.core:
        mod.core = mod.tagline
        if not mod.core:
            mod.gaps.append("core")

    block = soup.select_one(".pseudocode") or soup.select_one("pre.pseudo") \
        or soup.find("pre")
    if block is not None:
        mod.pattern = _pattern_from(block)
    if not mod.pattern:
        mod.gaps.append("pattern")

    # Watch out: the correction, never the myth. Older decks put the myth in a
    # label and the correction in a bare <p> sibling.
    mis = soup.select_one(".misconception")
    if mis is not None:
        right = mis.select_one(".right, .mc-right")
        if right is not None:
            mod.watch_out = _first_sentences(right.get_text(" "))
        else:
            para = mis.find("p")
            if para is not None:
                mod.watch_out = _first_sentences(para.get_text(" "))
            else:
                mod.watch_out = _first_sentences(mis.get_text(" "))
    if not mod.watch_out:
        takeaway = soup.select_one(".takeaway")
        if takeaway is not None:
            text = takeaway.get_text(" ", strip=True)
            mod.watch_out = _first_sentences(re.sub(r"^\W*Key Takeaway\s*", "", text))
    if not mod.watch_out:
        mod.gaps.append("watch_out")

    return mod


def collect(mobile_dir: str) -> list[Module]:
    paths = [
        p for p in glob.glob(os.path.join(mobile_dir, "*-mobile.html"))
        if _IDENT.match(os.path.basename(p))
    ]
    if not paths:
        sys.exit(f"no mobile module HTML found in {mobile_dir}")
    track_map = load_track_map()
    if not track_map:
        print("  ! no track map from index.html; using each deck's own label")
    return sorted((extract(p, track_map) for p in paths), key=lambda m: m.sort_key)


# ---------------------------------------------------------------------
# Quick reference cards
# ---------------------------------------------------------------------
@dataclass
class Card:
    title: str
    blocks: list[tuple[str, str]]    # ("text"|"code", body)


def load_cards(path: str) -> list[Card]:
    if not os.path.isfile(path):
        print(f"  ! no quick-reference data at {path}; cards omitted")
        return []
    cards: list[Card] = []
    current: Card | None = None
    in_code = False
    buf: list[str] = []

    def flush(kind: str) -> None:
        nonlocal buf
        body = "\n".join(buf).strip("\n")
        if current is not None and body.strip():
            current.blocks.append((kind, body))
        buf = []

    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if line.startswith("~~~"):
                flush("code" if in_code else "text")
                in_code = not in_code
                continue
            if not in_code and line.startswith("## "):
                flush("text")
                current = Card(title=line[3:].strip(), blocks=[])
                cards.append(current)
                continue
            if not in_code and (line.startswith("# ") or line.startswith("<!--")):
                continue
            if in_code:
                buf.append(line)
            elif line.strip():
                buf.append(line.strip())
            else:
                flush("text")
    flush("code" if in_code else "text")
    return cards


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------
class GuideDoc(BaseDocTemplate):
    """BaseDocTemplate that feeds real page numbers to the TOC."""

    def afterFlowable(self, flowable) -> None:
        level = getattr(flowable, "_toc_level", None)
        if level is not None:
            self.notify("TOCEntry", (level, flowable._toc_text, self.page))


def _tag(flowable, level: int, text: str):
    flowable._toc_level = level
    flowable._toc_text = text
    return flowable


def _styles(fonts: dict[str, str]) -> dict[str, ParagraphStyle]:
    sans, bold, mono = fonts["sans"], fonts["sans_bold"], fonts["mono"]
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName=bold, fontSize=30, leading=35,
            textColor=TEXT, alignment=TA_CENTER),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName=sans, fontSize=13.5, leading=19,
            textColor=GOLD, alignment=TA_CENTER),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName=sans, fontSize=10, leading=15,
            textColor=MUTED, alignment=TA_CENTER),
        "track": ParagraphStyle(
            "track", fontName=bold, fontSize=17, leading=21,
            textColor=GOLD, spaceBefore=0, spaceAfter=3),
        "module": ParagraphStyle(
            "module", fontName=bold, fontSize=12.5, leading=16,
            textColor=TEXT, spaceBefore=0, spaceAfter=1),
        "meta": ParagraphStyle(
            "meta", fontName=sans, fontSize=8, leading=11,
            textColor=MUTED, spaceAfter=4),
        "label": ParagraphStyle(
            "label", fontName=bold, fontSize=7.5, leading=10,
            textColor=GOLD, spaceBefore=3, spaceAfter=1),
        "body": ParagraphStyle(
            "body", fontName=sans, fontSize=9.5, leading=13.5,
            textColor=TEXT, spaceAfter=2),
        "muted": ParagraphStyle(
            "muted", fontName=sans, fontSize=9, leading=13,
            textColor=MUTED, spaceAfter=2),
        "code": ParagraphStyle(
            "code", fontName=mono, fontSize=7.6, leading=10.2,
            textColor=TEXT),
        "toc0": ParagraphStyle(
            "toc0", fontName=bold, fontSize=10.5, leading=16,
            textColor=GOLD, spaceBefore=7),
        "toc1": ParagraphStyle(
            "toc1", fontName=sans, fontSize=9, leading=13,
            textColor=TEXT, leftIndent=14),
    }


def _codebox(text: str, style: ParagraphStyle, width: float) -> Table:
    inner = Preformatted(escape(text), style)
    table = Table([[inner]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _painter(pagesize, fonts: dict[str, str], sanitize):
    width, height = pagesize

    def paint(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        if doc.page > 1:
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.5)
            canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
            canvas.setFont(fonts["sans"], 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(18 * mm, 9.5 * mm, sanitize(COURSE_TITLE))
            canvas.drawRightString(width - 18 * mm, 9.5 * mm, str(doc.page))
        canvas.restoreState()

    return paint


def build_pdf(modules, cards, out_path, pagesize, fonts, unicode_ok,
              one_per_page=False, built_on=None):
    sanitize = (lambda s: s) if unicode_ok else (
        lambda s: "".join(_TRANSLIT.get(ch, ch if ord(ch) < 256 else "?") for ch in s)
    )
    st = _styles(fonts)
    width, height = pagesize
    margin = 18 * mm
    frame_w = width - 2 * margin

    doc = GuideDoc(
        out_path, pagesize=pagesize,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=20 * mm,
        title=f"{COURSE_TITLE} \u2014 Study Guide", author="Claude Agent Course",
    )
    frame = Frame(margin, 20 * mm, frame_w, height - margin - 20 * mm, id="body")
    paint = _painter(pagesize, fonts, sanitize)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=paint),
        PageTemplate(id="body", frames=[frame], onPage=paint),
    ])

    def para(text: str, style: str) -> Paragraph:
        return Paragraph(escape(sanitize(text)), st[style])

    story: list = []

    # --- cover -------------------------------------------------------
    story.append(Spacer(1, height * 0.24))
    story.append(para(COURSE_TITLE, "cover_title"))
    story.append(Spacer(1, 7))
    story.append(para(COURSE_SUB, "cover_sub"))
    story.append(Spacer(1, 26))
    story.append(para("CONDENSED STUDY GUIDE", "cover_meta"))
    story.append(Spacer(1, 9))
    tracks = len({m.track for m in modules})
    story.append(para(
        f"{len(modules)} modules · {tracks} tracks · "
        f"built {built_on or _dt.date.today().isoformat()}", "cover_meta"))
    story.append(Spacer(1, 4))
    story.append(para("Generated from the mobile decks by scripts/build-study-guide.py",
                      "cover_meta"))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # --- contents ----------------------------------------------------
    story.append(para("Contents", "track"))
    story.append(Spacer(1, 8))
    toc = TableOfContents()
    toc.levelStyles = [st["toc0"], st["toc1"]]
    toc.dotsMinLevel = 1
    story.append(toc)
    story.append(PageBreak())

    # --- modules -----------------------------------------------------
    seen_track = None
    for mod in modules:
        chunk: list = []
        if mod.track != seen_track:
            if seen_track is not None:
                story.append(PageBreak())
            seen_track = mod.track
            heading = para(mod.track, "track")
            story.append(_tag(heading, 0, sanitize(mod.track)))
            story.append(Spacer(1, 5))

        label = f"{mod.ident}: {mod.name}"
        chunk.append(_tag(para(label, "module"), 1, sanitize(label)))
        subtitle = " \u00b7 ".join(x for x in (mod.meta, mod.tagline) if x)
        if subtitle:
            chunk.append(para(subtitle, "meta"))
        if mod.core:
            chunk.append(para("CORE", "label"))
            chunk.append(para(mod.core, "body"))
        if mod.pattern:
            chunk.append(para("PATTERN", "label"))
            chunk.append(_codebox(sanitize(mod.pattern), st["code"], frame_w))
        if mod.watch_out:
            chunk.append(para("WATCH OUT", "label"))
            chunk.append(para(mod.watch_out, "muted"))
        chunk.append(Spacer(1, 11))

        story.append(KeepTogether(chunk))
        if one_per_page:
            story.append(PageBreak())

    # --- quick reference ---------------------------------------------
    if cards:
        story.append(PageBreak())
        title = para("Quick Reference Cards", "track")
        story.append(_tag(title, 0, "Quick Reference Cards"))
        story.append(Spacer(1, 7))
        for card in cards:
            chunk = [_tag(para(card.title, "module"), 1, sanitize(card.title))]
            for kind, body in card.blocks:
                if kind == "code":
                    chunk.append(_codebox(sanitize(body), st["code"], frame_w))
                else:
                    chunk.append(para(body, "body"))
                chunk.append(Spacer(1, 3))
            chunk.append(Spacer(1, 9))
            story.append(KeepTogether(chunk))

    doc.multiBuild(story)
    return out_path


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def _rel(path: str) -> str:
    """relpath, but tolerate an output directory on another drive (Windows)."""
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def report(modules) -> int:
    print(f"  extracted {len(modules)} modules")
    fields = ("name", "track", "core", "pattern", "watch_out")
    missing = {f: [m.ident for m in modules if f in m.gaps] for f in fields}
    for name, idents in missing.items():
        state = "OK" if not idents else f"MISSING in {len(idents)}: {', '.join(idents)}"
        print(f"    {name:10s} {state}")
    tracks: dict[str, int] = {}
    for m in modules:
        tracks[m.track] = tracks.get(m.track, 0) + 1
    print("  tracks:")
    for track, count in tracks.items():
        print(f"    {count:2d}  {track}")
    return sum(len(v) for v in missing.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", choices=("a4", "letter", "both"), default="both")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    ap.add_argument("--mobile", default=MOBILE_DIR, help="mobile HTML directory")
    ap.add_argument("--check", action="store_true",
                    help="extract and report coverage without writing a PDF")
    ap.add_argument("--one-per-page", action="store_true",
                    help="force a page break after every module")
    ap.add_argument("--date", default=None, help="override the build date on the cover")
    args = ap.parse_args()

    print("Extracting from", _rel(args.mobile))
    modules = collect(args.mobile)
    gaps = report(modules)

    if args.check:
        print("\ncheck only; no PDF written")
        return 1 if gaps else 0

    print("\nFonts:")
    fonts, unicode_ok = resolve_fonts(verbose=True)
    cards = load_cards(QUICKREF)
    print(f"  quick-reference cards: {len(cards)}")

    sizes = {"a4": ("A4", A4), "letter": ("Letter", LETTER)}
    wanted = list(sizes) if args.size == "both" else [args.size]
    os.makedirs(args.out, exist_ok=True)

    print("\nBuilding:")
    for key in wanted:
        label, pagesize = sizes[key]
        suffix = "" if key == "a4" else f"-{key}"
        path = os.path.join(args.out, f"study-guide{suffix}.pdf")
        build_pdf(modules, cards, path, pagesize, fonts, unicode_ok,
                  one_per_page=args.one_per_page, built_on=args.date)
        size_kb = os.path.getsize(path) / 1024
        print(f"  {label:6s} {_rel(path)}  ({size_kb:,.0f} KB)")

    if gaps:
        print(f"\n{gaps} field(s) could not be extracted; see the report above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
