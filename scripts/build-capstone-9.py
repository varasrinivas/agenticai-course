#!/usr/bin/env python3
"""Build CAPSTONE-9-behavioral-health-modernization.html.

    python scripts/build-capstone-9.py

The head, the design-system CSS and the shared JS scaffolding are READ FROM
CAPSTONE-8 rather than re-typed. That is the point: the two modules then share
one visual language by construction, and a change to the palette or the quiz
widget does not silently diverge between them.

Everything below the scaffold -- sections, six animations, the quiz -- is this
module's own.

BUILD ORDER MATTERS. `scripts/build-search-assistant.mjs` INJECTS the search
widget into every page it indexes, so this script must run FIRST:

    python scripts/build-capstone-9.py
    node scripts/build-search-assistant.mjs claude-agents

Re-running this script after the search build overwrites the page and silently
drops the widget -- the page still renders, so nothing fails, which is exactly
why it is worth writing down.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output", "courses", "claude-agents")
DONOR = os.path.join(OUT_DIR, "CAPSTONE-8-oracle-to-postgres-migration.html")
TARGET = os.path.join(OUT_DIR, "CAPSTONE-9-behavioral-health-modernization.html")

TITLE = ("Capstone 9 &mdash; Behavioral Health UM Modernization | "
         "Building AI Agents with Claude")
DESCRIPTION = (
    "Build a coordinator and eight specialist subagents that modernize a legacy "
    "behavioral-health prior-authorization monolith onto a distributed clinical "
    "platform -- and that report where the modern platform is not good enough for "
    "the new domain. Skills carry the knowledge; agents carry the control flow.")


# ---------------------------------------------------------------- scaffold


def donor_parts() -> tuple[str, str, str]:
    """(head_and_css, shared_js, prism_scripts) lifted from Capstone 8."""
    with open(DONOR, encoding="utf-8") as fh:
        s = fh.read()

    head = s[: s.index("</style>") + len("</style>")]
    head = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", head, flags=re.S)
    head = re.sub(r'<meta name="description" content=".*?">',
                  f'<meta name="description" content="{DESCRIPTION}">',
                  head, flags=re.S)

    tail = s[s.index("</main>"):]
    prism = tail[tail.index("<script src="): tail.index("<script>\n// ========== SHARED UI")]

    js_start = tail.index("// ========== SHARED UI")
    js_end = tail.index("// ========== ANIMATION 1:")
    shared_js = tail[js_start:js_end]

    # CRITICAL: the shared slice CONTAINS Capstone 8's QUIZ_EXPLANATIONS.
    #
    # Lifting it wholesale gave every "Check Answer" in this module a
    # confident, well-written explanation about Oracle DATE truncation. The
    # page rendered, the quiz worked, and every answer was about the wrong
    # subject -- which is the worst failure mode available, because nothing
    # looks broken.
    from c9_quiz import QUIZ_EXPLANATIONS_JS
    donor_block = re.search(r"const QUIZ_EXPLANATIONS = \{.*?\n\};", shared_js, re.S)
    if donor_block is None:
        raise RuntimeError(
            "Capstone 8's QUIZ_EXPLANATIONS block was not found in the shared "
            "slice. Its shape changed; re-check the substitution before "
            "shipping, or this module ships the donor's answers.")
    shared_js = shared_js.replace(donor_block.group(0), QUIZ_EXPLANATIONS_JS, 1)

    return head, shared_js, prism


EXTRA_CSS = """
<style>
  /* ---- Capstone 9 animation styles --------------------------------- */
  .c9-grid { display: grid; gap: 0.6rem; }
  .c9-row { display: grid; grid-template-columns: 150px 1fr; gap: 0.75rem;
            align-items: center; font-size: 0.85rem; }
  .c9-chip { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 4px;
             font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
             font-weight: 600; letter-spacing: 0.02em; }
  .c9-lane { border: 1px solid var(--code-border); border-radius: 8px;
             background: var(--bg-card); padding: 0.6rem 0.8rem;
             opacity: 0.25; transition: opacity var(--transition-normal),
             border-color var(--transition-normal), background var(--transition-normal); }
  .c9-lane.on { opacity: 1; }
  .c9-lane.hot { border-color: var(--error); background: var(--error-bg); }
  .c9-lane.good { border-color: var(--success); background: var(--success-bg); }
  .c9-lane.warn { border-color: var(--warning); background: var(--warning-bg); }
  .c9-lane .lane-title { font-family: 'Bricolage Grotesque', sans-serif;
             font-weight: 700; font-size: 0.85rem; }
  .c9-lane .lane-note { color: var(--text-secondary); font-size: 0.8rem;
             margin-top: 0.2rem; }
  .c9-note { min-height: 3.2rem; margin-top: 0.9rem; padding: 0.7rem 0.9rem;
             border-left: 3px solid var(--accent-primary);
             background: var(--accent-muted); border-radius: 0 6px 6px 0;
             font-size: 0.86rem; color: var(--text-primary); }
  .c9-split { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 720px) { .c9-split, .c9-row { grid-template-columns: 1fr; } }
  .c9-col-title { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
             font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em;
             color: var(--text-muted); margin-bottom: 0.5rem; }
  .c9-mono { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
  .verdict-port   { background: rgba(16,185,129,0.18); color: #6EE7B7; }
  .verdict-extend { background: rgba(59,130,246,0.18); color: #93C5FD; }
  .verdict-build  { background: rgba(245,158,11,0.18); color: #FCD34D; }
  .verdict-not    { background: rgba(244,63,94,0.18); color: #FDA4AF; }
  .c9-sink { border: 1px dashed var(--code-border); border-radius: 6px;
             padding: 0.45rem 0.6rem; text-align: center; font-size: 0.78rem;
             opacity: 0.3; transition: all var(--transition-normal); }
  .c9-sink.lit { opacity: 1; border-style: solid; border-color: var(--error);
             background: var(--error-bg); color: #FDA4AF; }
  .c9-sinkrow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem;
             margin-top: 0.6rem; }
  .c9-plane { border: 1px solid var(--code-border); border-radius: 8px;
             padding: 0.75rem; background: var(--bg-card); }
  .c9-plane.knowledge { border-color: var(--info); }
  .c9-plane.control { border-color: var(--accent-primary); }
  .c9-item { padding: 0.3rem 0.5rem; margin: 0.25rem 0; border-radius: 4px;
             font-size: 0.8rem; background: var(--bg-surface); opacity: 0.3;
             transition: opacity var(--transition-normal); }
  .c9-item.on { opacity: 1; }
  .data-table { width: 100%; border-collapse: collapse; margin: 1.25rem 0;
             font-size: 0.88rem; }
  .data-table th, .data-table td { border: 1px solid var(--code-border);
             padding: 0.5rem 0.7rem; text-align: left; vertical-align: top; }
  .data-table th { background: var(--bg-surface); font-family: 'Bricolage Grotesque',
             sans-serif; font-weight: 600; }
  .data-table code { font-size: 0.82rem; }
  .step-box { border: 1px solid var(--code-border); border-left: 4px solid
             var(--accent-primary); border-radius: 0 8px 8px 0;
             background: var(--bg-card); padding: 1rem 1.25rem; margin: 1.5rem 0; }
  .step-box .step-num { font-family: 'Bricolage Grotesque', sans-serif;
             font-weight: 700; color: var(--accent-primary); font-size: 0.8rem;
             text-transform: uppercase; letter-spacing: 0.08em; }
  .box-label { display: block; font-family: 'Bricolage Grotesque', sans-serif;
             font-weight: 700; font-size: 0.78rem; text-transform: uppercase;
             letter-spacing: 0.08em; margin-bottom: 0.4rem; }
</style>
"""


HEADER = """
</head>
<body>

<header class="course-header">
  <div class="course-header-inner">
    <div>
      <div class="course-title">Building AI Agents with Claude</div>
      <div style="display:flex;align-items:center;gap:1rem;margin-top:0.5rem;flex-wrap:wrap;">
        <span class="track-badge"><span class="dot"></span> Capstone Project 9</span>
        <span class="diff-badge" aria-label="Difficulty: 5 of 5 stars"><span class="diff-star">&#9733;</span><span class="diff-star">&#9733;</span><span class="diff-star">&#9733;</span><span class="diff-star">&#9733;</span><span class="diff-star">&#9733;</span></span>
      </div>
    </div>
    <div class="header-meta"><span>Capstone 9 &mdash; Bonus</span><span>14&ndash;18 hours</span><span>Behavioral Health</span></div>
  </div>
</header>

<div class="module-nav" style="max-width:1200px;margin:0 auto;padding:0.75rem 2rem;border-top:none;">
  <a href="CAPSTONE-8-oracle-to-postgres-migration.html">&larr; Capstone 8: Oracle &rarr; PostgreSQL</a>
  <a href="index.html" aria-label="Course Home" title="Course Home" style="font-size:1.2rem;">&#x1F3E0; Home</a>
  <a href="index.html">Course Home &rarr;</a>
</div>

<div class="page-container">
  <nav class="sidebar-nav" aria-label="Capstone sections">
    <div class="sidebar-title">Capstone 9</div>
    <a href="#brief">Project Brief</a>
    <a href="#prerequisites">Prerequisites</a>
    <a href="#why-bh">Why BH &ne; Clinical</a>
    <a href="#term-map">Vocabularies Collide</a>
    <a href="#donor">The Donor and Its Holes</a>
    <a href="#monolith">The Monolith</a>
    <a href="#glossary">Domain Glossary</a>
    <a href="#anim-decompose">Monolith &rarr; Distributed</a>
    <a href="#anim-gap">The Gap Register</a>
    <a href="#anim-hitpolicy">Hit Policy</a>
    <a href="#anim-leak">The Part 2 Leak</a>
    <a href="#anim-planes">Skills vs Agents</a>
    <a href="#anim-screen">JSP &rarr; Route</a>
    <a href="#planes">Skill, Subagent, Command</a>
    <a href="#no-phi">No PHI in Prompts</a>
    <a href="#env-setup">Environment Setup</a>
    <a href="#file-tree">File Structure</a>
    <a href="#phase-9a">Phase 9A: Backend</a>
    <a href="#phase-9b">Phase 9B: Frontend</a>
    <a href="#spec-driven">Track 2 &amp; The Diff</a>
    <a href="#guardrails">Guardrails &amp; HITL</a>
    <a href="#validation">Validation &amp; Evals</a>
    <a href="#deploy">Deployment</a>
    <a href="#part2">HIPAA &amp; 42 CFR Part 2</a>
    <a href="#troubleshooting">Troubleshooting</a>
    <a href="#extensions">Going Further</a>
    <a href="#what-you-built">What You Built</a>
    <a href="#quiz">Knowledge Check</a>
    <a href="#references">References</a>
  </nav>

  <main class="content">
    <h1>Capstone 9 &mdash; Behavioral Health UM Modernization</h1>
    <p style="color:var(--text-secondary);font-size:1.1rem;margin-bottom:2rem;">Build a coordinator and eight specialist subagents that move a 2011 Spring MVC/JSP monolith onto a modern distributed platform &mdash; and that report, with evidence, every place where the modern platform is <em>not good enough</em> for the domain being moved onto it. The deliverable is a working repository <strong>and a gap register</strong>.</p>
"""


def build() -> str:
    head, shared_js, prism = donor_parts()

    from c9_sections import SECTIONS          # noqa: E402  (built below)
    from c9_animations import ANIMATION_JS    # noqa: E402

    return "".join([
        head, EXTRA_CSS, HEADER,
        SECTIONS,
        "\n  </main>\n</div>\n",
        prism,
        "<script>\n", shared_js, ANIMATION_JS, "\n</script>\n",
        "</body>\n</html>\n",
    ])


def main() -> int:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    html = build()
    with open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print(f"wrote {TARGET}")
    print(f"  {len(html):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
