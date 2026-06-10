"""Build a condensed quick-reference PDF from all mobile HTML module files.

Covers M00–M24 (excludes Claude Code & cert-prep track M25–M27B).
Per cluster: one-sentence big idea + pseudocode + takeaway + top misconception.
Target: ≤ 50 pages.

Output: output/mobile/quick-reference-all-concepts.pdf
"""
from __future__ import annotations

import html as html_mod
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, Tag

ROOT   = Path(__file__).resolve().parent.parent
MOBILE = ROOT / "output" / "mobile"
OUT    = ROOT / "output" / "mobile" / "quick-reference-all-concepts.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

TRACK_COLORS: dict[str, str] = {
    "0": "#6366F1", "1": "#6366F1", "2": "#10B981",
    "3": "#B45309", "4": "#7c3aed", "5": "#be123c",
    "6": "#2563eb", "7": "#0f766e", "8": "#be185d",
    "9": "#8a6a1a",
}
_DEFAULT_COLOR = "#6366F1"

# Cert-prep and Claude Code track — excluded from this condensed reference
EXCLUDED_MODS = {"M25", "M26", "M27", "M27B"}


# ── File ordering ─────────────────────────────────────────────────────────────

def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("No Chrome or Edge installation found.")


def _sort_key(p: Path) -> tuple[int, int, str]:
    m = re.match(r"^M(\d+)(B?)", p.stem, re.IGNORECASE)
    if m:
        return int(m.group(1)), (1 if m.group(2).upper() == "B" else 0), p.stem
    return 9999, 0, p.stem


def get_mobile_files() -> list[Path]:
    files = [
        f for f in MOBILE.glob("M*.html")
        if not f.stem.endswith("-v1") and f.stem != "index"
    ]
    files.sort(key=_sort_key)
    return files


def _mod_id_from_path(p: Path) -> str:
    m = re.match(r"^(M\d+B?)", p.stem, re.IGNORECASE)
    return m.group(1).upper() if m else ""


# ── Text helpers ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Collapse whitespace and unescape HTML entities."""
    return re.sub(r"\s+", " ", html_mod.unescape(text)).strip()


def _get_text(el: Tag | None, sep: str = " ") -> str:
    if el is None:
        return ""
    return _clean(el.get_text(sep, strip=True))


def _esc(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _pre_html(el: Tag) -> str:
    """Return inner text of pseudocode block preserving whitespace."""
    # Use get_text with newlines to preserve structure
    lines = el.decode_contents()
    # Strip span tags but keep their text
    lines = re.sub(r"<span[^>]*>", "", lines)
    lines = re.sub(r"</span>", "", lines)
    lines = re.sub(r"<br\s*/?>", "\n", lines, flags=re.IGNORECASE)
    lines = html_mod.unescape(lines)
    # Limit to 50 lines to avoid page blowout
    all_lines = lines.splitlines()
    if len(all_lines) > 50:
        all_lines = all_lines[:50] + ["  ... (truncated)"]
    return "\n".join(all_lines)


# ── Module extraction ─────────────────────────────────────────────────────────

def _parse_title(raw: str, filename: str) -> tuple[str, str]:
    t = _clean(raw)
    for pat in [
        r"^(M\w+):\s*(.+?)\s*\(Mobile\)",
        r"^(M\w+)\s*[·•]\s*(.+?)\s*[—–-]\s*Mobile",
        r"^(M\w+)\s+Mobile:\s*(.+?)(?:\s*\||$)",
        r"^(M\w+)\s*:\s*(.+?)(?:\s*\||$)",
    ]:
        m = re.match(pat, t)
        if m:
            return m.group(1), _clean(m.group(2))
    stem = Path(filename).stem
    m2 = re.match(r"^(M[\w]+?)-", stem)
    mod_id = m2.group(1).upper() if m2 else "M??"
    title = re.sub(r"-mobile$", "", stem).replace("-", " ").title()
    return mod_id, title


def _parse_track(soup: BeautifulSoup) -> tuple[str, str, str]:
    for sel in [".top-bar-track", "#track-label", ".track-chip", ".title-badge", ".pill-track"]:
        el = soup.select_one(sel)
        if el:
            text = _get_text(el)
            m = re.search(r"Track\s+(\d+)", text)
            if m:
                num = m.group(1)
                label = re.sub(r"\s*[·•:]\s*", " — ", text, count=1).strip()
                return num, label, TRACK_COLORS.get(num, _DEFAULT_COLOR)
    body = soup.get_text(" ", strip=True)
    m = re.search(r"Track\s+(\d+)\s*[·•:—\-]+\s*([A-Za-z &]+)", body)
    if m:
        num, name = m.group(1), m.group(2).strip()
        return num, f"Track {num} — {name}", TRACK_COLORS.get(num, _DEFAULT_COLOR)
    return "1", "Track 1 — Foundations", _DEFAULT_COLOR


def _find_cards(soup: BeautifulSoup) -> list[Tag]:
    """Find all content cards (various class patterns across modules)."""
    results = []
    # Pattern 1: section.mobile-card
    for el in soup.find_all("section", class_=lambda c: c and "mobile-card" in c):
        results.append(el)
    if results:
        return results
    # Pattern 2: article.card or div.card (M01/M12-style — only class is "card")
    for tag in ("article", "div"):
        for el in soup.find_all(tag, class_="card"):
            if el.get("class") == ["card"]:
                results.append(el)
    if results:
        return results
    # Pattern 3: div.mobile-card
    for el in soup.find_all(["div", "article"], class_=lambda c: c and "mobile-card" in c):
        results.append(el)
    return results


def _concept_num(card: Tag) -> int | None:
    chip = card.find(class_="concept-chip")
    if not chip:
        return None
    m = re.search(r"\b(\d+)\b", _get_text(chip))
    return int(m.group(1)) if m else None


def _card_type(card: Tag) -> str:
    for cls in ["card-type-chip", "section-label"]:
        el = card.find(class_=cls)
        if el:
            return _get_text(el).lower()
    return ""


def _extract_steps(card: Tag) -> list[str]:
    steps = []
    for cls in ["step-list", "steps-list", "steps"]:
        el = card.find(["ol", "ul"], class_=cls)
        if el:
            for li in el.find_all("li", recursive=False):
                strong = li.find("strong")
                label = _get_text(strong) if strong else ""
                full = _get_text(li)
                if label and full.startswith(label):
                    body = full[len(label):].strip().lstrip(":").strip()
                    steps.append(f"**{label}** {body}" if label else body)
                else:
                    steps.append(full)
    return steps[:8]  # cap at 8 steps


def _extract_pseudocode(card: Tag) -> str:
    for cls in ["pseudocode"]:
        el = card.find(class_=cls)
        if el:
            return _pre_html(el)
    pre = card.find("pre")
    if pre:
        return _pre_html(pre)
    return ""


def _extract_misconceptions(card: Tag) -> list[tuple[str, str]]:
    out = []
    for misc in card.find_all(class_="misconception"):
        wrong_el = misc.find(class_=["wrong", "mc-wrong"])
        right_el = misc.find(class_=["right", "mc-right"])
        wrong = re.sub(r"^[❌✗×✖]\s*", "", _get_text(wrong_el)).strip('"')
        right = re.sub(r"^[✅✓✔]\s*", "", _get_text(right_el)).strip()
        if wrong or right:
            out.append((wrong, right))
    return out


def _extract_takeaway(card: Tag) -> str:
    t = card.find(class_="takeaway")
    if not t:
        return ""
    for lbl in t.find_all(class_=["takeaway-label", "analogy-label", "box-label"]):
        lbl.decompose()
    return _get_text(t)


def _extract_analogy(card: Tag) -> str:
    box = card.find(class_="analogy-box")
    if box:
        for lbl in box.find_all(class_=["analogy-label", "box-label"]):
            lbl.decompose()
        return _get_text(box)
    # Fallback: get paragraphs from the card
    paras = [_get_text(p) for p in card.find_all("p") if _get_text(p)]
    return " ".join(paras[:3])


def _extract_big_idea(card: Tag) -> str:
    paras = [_get_text(p) for p in card.find_all("p") if _get_text(p)]
    return " ".join(paras[:2])


def _extract_index_names(soup: BeautifulSoup) -> dict[int, str]:
    """Extract concept names from the index card."""
    names: dict[int, str] = {}
    # Pattern A: ul.index-list with span.idx-num
    for a in soup.select("ul.index-list li a, ol.index-list li a"):
        num_el = a.find(class_="idx-num")
        if num_el:
            try:
                num = int(_get_text(num_el))
            except ValueError:
                continue
            # Get the first span text after idx-num (not idx-sub)
            texts = [t.strip() for t in a.stripped_strings]
            # Remove the number itself
            label_parts = [t for t in texts if t != _get_text(num_el) and not t.startswith("id")]
            if label_parts:
                names[num] = label_parts[0]
    # Pattern B: a.concept-index-item with div.concept-num
    if not names:
        for a in soup.select("a.concept-index-item, .concept-index-item"):
            num_el = a.find(class_="concept-num")
            if num_el:
                try:
                    num = int(_get_text(num_el))
                except ValueError:
                    continue
                divs = [d for d in a.find_all("div") if d is not num_el]
                if divs:
                    names[num] = _get_text(divs[0]).split("\n")[0].strip()
    return names


def extract_module(path: Path) -> dict | None:
    try:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    except Exception as e:
        print(f"  WARN {path.name}: {e}")
        return None

    title_tag = soup.find("title")
    if not title_tag:
        return None

    mod_id, title = _parse_title(_get_text(title_tag), path.name)
    track_num, track_label, color = _parse_track(soup)
    index_names = _extract_index_names(soup)

    cards = _find_cards(soup)
    clusters: dict[int, dict] = {}

    for card in cards:
        cnum = _concept_num(card)
        if cnum is None:
            continue

        if cnum not in clusters:
            clusters[cnum] = {
                "name": index_names.get(cnum, f"Concept {cnum}"),
                "big_idea_h": "",
                "big_idea": "",
                "analogy": "",
                "steps": [],
                "pseudocode": "",
                "misconceptions": [],
                "takeaway": "",
            }

        ctype = _card_type(card)
        h2 = card.find("h2")
        h2_text = _get_text(h2) if h2 else ""

        # Big idea card
        if "big idea" in ctype or "the big idea" in ctype:
            if not clusters[cnum]["big_idea_h"]:
                clusters[cnum]["big_idea_h"] = h2_text
            clusters[cnum]["big_idea"] = _extract_big_idea(card)

        # Analogy card
        elif "analogy" in ctype:
            clusters[cnum]["analogy"] = _extract_analogy(card)

        # Steps cards
        steps = _extract_steps(card)
        if steps and not clusters[cnum]["steps"]:
            clusters[cnum]["steps"] = steps

        # Pseudocode (any card)
        if not clusters[cnum]["pseudocode"]:
            pc = _extract_pseudocode(card)
            if pc.strip():
                clusters[cnum]["pseudocode"] = pc

        # Misconceptions
        miscs = _extract_misconceptions(card)
        clusters[cnum]["misconceptions"].extend(miscs)

        # Takeaway
        if not clusters[cnum]["takeaway"]:
            clusters[cnum]["takeaway"] = _extract_takeaway(card)

        # Fallback: use big-idea text from any card that has heading but no labeled type
        if not clusters[cnum]["big_idea"] and h2_text:
            clusters[cnum]["big_idea"] = _extract_big_idea(card)
        if not clusters[cnum]["big_idea_h"] and h2_text:
            clusters[cnum]["big_idea_h"] = h2_text

    if not clusters:
        return None

    return {
        "mod_id": mod_id,
        "title": title,
        "track_num": track_num,
        "track_label": track_label,
        "color": color,
        "clusters": dict(sorted(clusters.items())),
    }


# ── HTML / CSS ────────────────────────────────────────────────────────────────

PAGE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap');

@page { size: A4; margin: 10mm 11mm 12mm 11mm; }
@page :first { margin-top: 0; }
*, *::before, *::after { box-sizing: border-box; }

html, body {
  margin: 0; padding: 0;
  background: #fff; color: #1a1f2e;
  font-family: 'Source Sans 3', system-ui, sans-serif;
  font-size: 8pt; line-height: 1.38;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', sans-serif; margin: 0; }
p { margin: 0; }
strong { font-weight: 700; }

/* ── COVER ── */
.cover {
  page-break-after: always; min-height: 100vh;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center; padding: 0 24mm;
}
.cover-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt; letter-spacing: 0.22em; text-transform: uppercase;
  color: #b8860b; margin-bottom: 1.2rem;
}
.cover h1 { font-size: 30pt; font-weight: 800; color: #0A1628; line-height: 1.1; margin-bottom: 0.5rem; }
.cover-sub { font-size: 11.5pt; color: #4a5568; max-width: 380px; line-height: 1.4; margin-bottom: 1.3rem; }
.cover-divider { width: 44px; height: 3px; background: #d4a843; border-radius: 2px; margin: 0 auto 1.3rem; }
.cover-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 0.25rem 2.5rem; text-align: left;
  font-size: 8.5pt; color: #4a5568; margin-bottom: 1.3rem;
}
.cover-grid span::before { content: "▸ "; color: #b8860b; }
.cover-meta { font-family: 'JetBrains Mono', monospace; font-size: 7pt; color: #718096; }

/* ── TOC ── */
.toc-page { page-break-after: always; }
.toc-page h2 { font-size: 14pt; color: #0A1628; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.35rem; margin-bottom: 0.6rem; }
.toc-table { width: 100%; border-collapse: collapse; font-size: 7.5pt; }
.toc-table tr:nth-child(even) { background: #f9fafb; }
.toc-table td { padding: 0.2rem 0.45rem; vertical-align: top; }
.toc-id { font-family: 'JetBrains Mono', monospace; color: var(--tc); font-weight: 700; width: 3.2rem; }
.toc-title { font-weight: 600; color: #0A1628; }
.toc-track { color: #718096; font-size: 7pt; }

/* ── ALL MODULES: 2-column flow ── */
.main-content {
  column-count: 2;
  column-gap: 0.9rem;
}

/* ── MODULE SECTION ── */
.mod-section { margin-bottom: 0.6rem; }
.mod-header {
  background: var(--tc); color: #fff;
  padding: 0.32rem 0.6rem;
  display: flex; align-items: center; justify-content: space-between;
  border-radius: 6px 6px 0 0;
  break-after: avoid;
}
.mod-header-left { display: flex; align-items: center; gap: 0.45rem; }
.mod-id-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7pt; font-weight: 700;
  background: rgba(0,0,0,0.25); border-radius: 3px;
  padding: 0.08rem 0.4rem; white-space: nowrap; letter-spacing: 0.04em;
}
.mod-title { font-size: 10.5pt; font-weight: 800; line-height: 1.2; letter-spacing: -0.01em; }
.mod-track { font-size: 6.5pt; opacity: 0.8; font-weight: 600; white-space: nowrap; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.03em; }

.mod-body {
  background: #f7f9fc;
  border: 1px solid #dde3ec; border-top: none;
  border-radius: 0 0 6px 6px;
  padding: 0.45rem 0.5rem 0.5rem;
}

/* ── CONCEPT CLUSTER — single clean card, no nested boxes ── */
.cluster {
  break-inside: avoid;
  background: #fff;
  border: 1px solid #e4e9f0;
  border-top: 2.5px solid var(--tc);
  border-radius: 6px;
  padding: 0.38rem 0.52rem 0.42rem;
  margin-bottom: 0.45rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.cluster:last-child { margin-bottom: 0; }

.cluster-header {
  display: flex; align-items: center; gap: 0.38rem;
  padding-bottom: 0.28rem;
  margin-bottom: 0.3rem;
  border-bottom: 1px solid #f0f4f8;
}
.cluster-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6pt; font-weight: 700;
  background: var(--tc); color: #fff;
  border-radius: 50%; width: 14px; height: 14px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cluster-name { font-size: 8.5pt; font-weight: 800; color: #0a1628; line-height: 1.2; }

/* ── SECTION LABELS — small coloured tag, no extra box ── */
.lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 5.5pt; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--tc); opacity: 0.7;
  margin: 0.3rem 0 0.12rem;
  display: block;
}

/* ── CORE IDEA — plain readable text, no border ── */
.idea-text {
  font-size: 8pt; color: #2d3748; line-height: 1.42;
}

/* ── PATTERN — light print-friendly code block ── */
pre.code {
  background: #f4f6fa;
  color: #1a2133;
  border: 1px solid #d8deea;
  border-left: 2.5px solid var(--tc);
  border-radius: 0 5px 5px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.8pt; line-height: 1.48;
  padding: 0.42rem 0.55rem;
  white-space: pre-wrap; word-break: break-word;
  overflow: visible; margin: 0;
}

/* ── TAKEAWAY — gold left rule, italic, no box ── */
.takeaway-text {
  font-size: 7.5pt; color: #5c4a1e; line-height: 1.4;
  font-style: italic;
  padding-left: 0.5rem;
  border-left: 2px solid #d4a843;
}

/* ── MISCONCEPTION — coloured text only, no box ── */
.misc-row { font-size: 7.5pt; line-height: 1.38; }
.mis-x { color: #be123c; font-weight: 700; margin-right: 0.18rem; }
.mis-wrong { color: #9f1239; }
.mis-check { color: #16a34a; font-weight: 700; margin-right: 0.18rem; }
.mis-right { color: #15803d; }
"""

COVER_HTML = """
<section class="cover">
  <div class="cover-eyebrow">Quick Reference · Condensed</div>
  <h1>Building AI Agents<br>with Claude</h1>
  <p class="cover-sub">Every concept distilled to its core idea, pattern, and key insight</p>
  <div class="cover-divider"></div>
  <div class="cover-grid">
    <span>LLM mental model &amp; tokens</span>
    <span>Structured output &amp; tool use</span>
    <span>MCP &amp; multi-tool orchestration</span>
    <span>Conversation memory &amp; RAG</span>
    <span>ReAct loop &amp; planning</span>
    <span>Multi-agent architecture</span>
    <span>Input &amp; output guardrails</span>
    <span>Evaluation &amp; tracing</span>
    <span>API design &amp; cost optimization</span>
    <span>Production deployment</span>
  </div>
  <div class="cover-meta">__MODULE_COUNT__ modules &nbsp;·&nbsp; M00–M24 &nbsp;·&nbsp; 2026</div>
</section>
"""


def render_toc(modules: list[dict]) -> str:
    rows = []
    for mod in modules:
        n_clusters = len(mod["clusters"])
        rows.append(
            f'<tr style="--tc:{mod["color"]}">'
            f'<td class="toc-id">{_esc(mod["mod_id"])}</td>'
            f'<td class="toc-title">{_esc(mod["title"])}</td>'
            f'<td class="toc-track">{_esc(mod["track_label"])}</td>'
            f'<td style="color:#718096;font-size:7pt;white-space:nowrap">{n_clusters}c</td>'
            f'</tr>'
        )
    return f"""
<div class="toc-page">
  <h2>Contents</h2>
  <table class="toc-table">
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""


def render_cluster(cnum: int, cl: dict) -> str:
    has_code = bool(cl["pseudocode"] and cl["pseudocode"].strip())
    parts = []

    # Header: number badge + concept name
    name = cl["big_idea_h"] or cl["name"]
    parts.append(
        f'<div class="cluster-header">'
        f'<span class="cluster-num">{cnum}</span>'
        f'<span class="cluster-name">{_esc(name)}</span>'
        f'</div>'
    )

    # Big idea — 1-2 sentences, capped at 220 chars
    idea = cl["big_idea"]
    if idea:
        if len(idea) > 220:
            # Try to cut at sentence boundary
            cut = idea[:220]
            dot = cut.rfind(". ")
            idea = (cut[:dot + 1] if dot > 100 else cut[:220]) + "…"
        parts.append(f'<div class="lbl">Core Idea</div>'
                     f'<div class="idea-text">{_esc(idea)}</div>')

    # Pseudocode — max 15 lines
    if has_code:
        pc = cl["pseudocode"].strip()
        lines = pc.splitlines()
        if len(lines) > 15:
            lines = lines[:15] + ["  ..."]
        pc = "\n".join(lines)
        parts.append(f'<div class="lbl">Pattern</div>'
                     f'<pre class="code">{_esc(pc)}</pre>')

    # Takeaway — 1-2 sentences, capped at 200 chars
    ta = cl["takeaway"]
    if ta:
        if len(ta) > 200:
            cut = ta[:200]
            dot = cut.rfind(". ")
            ta = (cut[:dot + 1] if dot > 80 else cut[:200]) + "…"
        parts.append(f'<div class="lbl">Takeaway</div>'
                     f'<div class="takeaway-text">{_esc(ta)}</div>')

    # Top misconception only — one ✗ line + one ✓ line
    if cl["misconceptions"]:
        wrong, right = cl["misconceptions"][0]
        if len(wrong) > 120: wrong = wrong[:117] + "…"
        if len(right) > 140: right = right[:137] + "…"
        parts.append(
            f'<div class="misc-row">'
            f'<span class="mis-x">✗</span><span class="mis-wrong">{_esc(wrong)}</span><br>'
            f'<span class="mis-check">✓</span><span class="mis-right">{_esc(right)}</span>'
            f'</div>'
        )

    return f'<div class="cluster">{"".join(parts)}</div>'


def render_module(mod: dict) -> str:
    clusters_html = "".join(
        render_cluster(cnum, cl)
        for cnum, cl in mod["clusters"].items()
    )
    return (
        f'<section class="mod-section" style="--tc:{mod["color"]}">'
        f'<div class="mod-header">'
        f'<div class="mod-header-left">'
        f'<span class="mod-id-badge">{_esc(mod["mod_id"])}</span>'
        f'<span class="mod-title">{_esc(mod["title"])}</span>'
        f'</div>'
        f'<span class="mod-track">{_esc(mod["track_label"])}</span>'
        f'</div>'
        f'<div class="mod-body">{clusters_html}</div>'
        f'</section>'
    )


def build_html(modules: list[dict]) -> str:
    cover = COVER_HTML.replace("__MODULE_COUNT__", str(len(modules)))
    toc = render_toc(modules)
    body = '<div class="main-content">' + "\n".join(render_module(m) for m in modules) + "</div>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quick Reference — Building AI Agents with Claude</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
{PAGE_CSS}
</style>
</head>
<body>
{cover}
{toc}
{body}
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    browser = find_browser()
    files = get_mobile_files()
    print(f"Browser : {browser}")
    print(f"Scanning {len(files)} mobile HTML files …\n")

    modules: list[dict] = []
    for f in files:
        mid = _mod_id_from_path(f)
        if mid in EXCLUDED_MODS:
            print(f"  EXCL {f.name}")
            continue
        mod = extract_module(f)
        if mod:
            n = len(mod["clusters"])
            print(f"  OK  {mod['mod_id']:8s}  {n} clusters  {mod['title'][:50]}")
            modules.append(mod)
        else:
            print(f"  SKIP {f.name}")

    print(f"\nBuilding HTML for {len(modules)} modules …")
    html_doc = build_html(modules)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="all-concepts-pdf-") as tmp:
        tmp_html = Path(tmp) / "all-concepts.html"
        tmp_pdf = Path(tmp) / "out.pdf"

        tmp_html.write_text(html_doc, encoding="utf-8")
        print(f"HTML size: {tmp_html.stat().st_size // 1024} KB")
        print("Rendering PDF via headless Chrome …")

        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--virtual-time-budget=25000",
                f"--print-to-pdf={tmp_pdf}",
                tmp_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )

        if not tmp_pdf.exists():
            sys.exit("Chrome did not produce a PDF.")

        # Rename existing output to preserve it (skip if file is locked)
        dest = OUT
        if OUT.exists():
            stem = OUT.stem
            for i in range(1, 20):
                cand = OUT.with_name(f"{stem}-v{i}.pdf")
                if not cand.exists():
                    try:
                        OUT.rename(cand)
                        print(f"Preserved previous: {cand.name}")
                    except PermissionError:
                        # File is open — write to a new versioned name instead
                        dest = cand
                        print(f"Note: existing PDF is locked, writing to {cand.name}")
                    break

        shutil.move(str(tmp_pdf), str(dest))

    size_kb = dest.stat().st_size // 1024
    try:
        import pypdf
        pages = len(pypdf.PdfReader(str(dest)).pages)
        print(f"\nWrote : {dest}")
        print(f"Size  : {size_kb} KB, {pages} pages")
    except Exception:
        print(f"\nWrote : {dest}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
