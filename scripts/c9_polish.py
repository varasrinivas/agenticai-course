#!/usr/bin/env python3
"""Add dual-language tabs and first-use tooltips to the Capstone 9 sections.

Run once, in place, against the c9_sections_*.py content modules. Idempotent:
re-running is a no-op because every substitution is anchored on text that the
substitution itself removes.

Two checklist items:

  * "Both Python AND Node/TypeScript for every code example" -- applied to the
    four blocks where a TypeScript twin actually helps a reader. NOT applied to
    the PL/SQL ladder, the Java switch, the JSTL, the shell or the markdown:
    you cannot write an Oracle package in TypeScript, and a fake twin teaches
    less than an honest single tab.

  * "Every technical term gets a tooltip on first use."
"""

from __future__ import annotations

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def tabify(block_id: str, py_lang: str, ts_id: str, ts_lang: str, ts_code: str):
    """Turn a single-tab block into Python | Node/TypeScript."""
    old_tabs = (f'<div class="code-tabs"><button class="code-tab active" '
                f'onclick="switchTab(this,\'{block_id}\')">Python</button></div>')
    new_tabs = (
        f'<div class="code-tabs">\n'
        f'          <button class="code-tab active" onclick="switchTab(this,\'{block_id}\')">Python</button>\n'
        f'          <button class="code-tab" onclick="switchTab(this,\'{ts_id}\')">Node / TypeScript</button>\n'
        f'        </div>')
    new_panel = (f'\n        <div class="code-panel" id="{ts_id}"><pre>'
                 f'<code class="language-{ts_lang}">{ts_code}</code></pre></div>')
    return old_tabs, new_tabs, new_panel


SEAM_TS = """// solution/seam-map.ts
sm.addSeam({
  name: 'case | notification',
  left: 'bh-case-svc', right: 'bh-notify-svc',
  crosses: ['AuthCaseService.submitAndDecide'],
  coupling: Coupling.EventualGuaranteed,
  replacement: {
    mechanism: 'transactional outbox in bh-case-svc + idempotent consumer ' +
               'keyed on (authId, reviewSeq)',
    window: 'under 60s at the configured relay interval; the legacy cron ' +
            'polled every 5 minutes, so this is tighter than what it replaces',
    observable: `SELECT count(*) FROM outbox_event WHERE published_at IS NULL
                   AND created_at &lt; now() - interval '5 minutes'`,
    compensation: 'relay retries with backoff; rows past 3 attempts move to a ' +
                  'human queue, because the legacy FAILED state was where rows ' +
                  'went to be forgotten',
    alarm: 'that count &gt; 0 for 5 consecutive minutes pages the on-call',
  },
});

// All five fields are required by the type, not by a convention. An eventual
// consistency with no observable and no alarm is the same as no guarantee,
// implemented with more moving parts.
interface AtomicityReplacement {
  mechanism: string;
  window: string;
  observable: string;
  compensation: string;
  alarm: string;
}"""

HARM_TS = """// solution/gap-register.ts
if (entry.verdict === Verdict.MustNotPort &amp;&amp; !entry.harm?.trim()) {
  throw new RegisterError(
    `${entry.capability}: must-not-port requires a NAMED HARM. ` +
    `If you cannot name what goes wrong and for whom, the verdict is 'extend'.`);
}

// Note that this is a THROW, not a warning. A register that accepts a
// must-not-port with no harm is a register whose most important verdict
// means nothing -- and softening that verdict is exactly how a defect gets
// copied forward with a note attached."""

PHI_TS = """// solution/hooks.ts
//
// THE LIMIT OF THIS APPROACH, STATED PLAINLY: shape detection is defence in
// depth, not a proof. A narrative written without any of these words will
// pass, and no regex closes that gap. The control that actually holds is that
// every fixture in this lab is SYNTHETIC.
const CLINICAL_REGISTER =
  /\\b(member|patient|client|individual|resident|he|she|they)\\b[\\s\\S]{0,100}\\b(present(s|ed|ing)?|report(s|ed|ing)?|ideation|withdrawal|relapse|treatment|therapy|counsel(ling|ing)?|episode|referral|admission|engagement|symptom|dose|medication|prescrib|diagnos)\\b/i;

// Several sentences of prose, not code and not a column list.
//
// The trailing \\s* rather than \\s+ matters. With \\s+ the LAST sentence of a
// narrative goes unmatched -- there is no whitespace after its full stop --
// so redaction leaves one clinical sentence standing. That was a real leak,
// found by running the gate over the seed fixture rather than over a mock.
const PROSE = /(?:[A-Z][^.!?\\n]{25,}[.!?]\\s*){2,}/;"""

TERMMAP_TS = """// solution/term-map.ts
interface TermMapping {
  kind: TermKind;
  clinical: string;
  behavioral: string;
  /**
   * REQUIRED, NO OPTIONAL MARKER. The whole point of this module.
   *
   * A name-identical pair recorded without answering this is the failure
   * mode the map exists to prevent, so it cannot be recorded at all.
   */
  sameSemantics: boolean;
  evidence: string;
  divergence?: string;   // required when sameSemantics is false
  action?: string;       // required when sameSemantics is false
}

/** Same name, different meaning. The dangerous quadrant. */
function silentTrap(m: TermMapping): boolean {
  return m.clinical.trim().toLowerCase() === m.behavioral.trim().toLowerCase()
      &amp;&amp; !m.sameSemantics;
}"""


#: (file, term, tooltip) -- applied to the FIRST occurrence only.
TOOLTIPS = [
    ("c9_sections_a.py", "carve-out",
     "Behavioral health contracted to a separate vendor with its own network, "
     "criteria, claims platform and member identifiers. Explains why a BH "
     "system keys on an identifier the health plan does not recognise."),
    ("c9_sections_a.py", "42 CFR Part 2",
     "The federal rule protecting records from federally assisted "
     "substance-use-disorder treatment programs. Disclosure requires a consent "
     "that NAMES the recipient, states a purpose and scope, and expires."),
    ("c9_sections_a.py", "adverse determination",
     "A denial, or an approval at a level lower than the one requested. The "
     "regulated event in behavioral health, and the one that must trace to a "
     "published, applied criterion."),
    ("c9_sections_a.py", "transactional outbox",
     "Write the entity and an outbox row in one local transaction; a separate "
     "worker publishes the row and marks it published. Makes persist-and-"
     "publish atomic within ONE service -- it does not make two services' "
     "writes atomic with each other."),
    ("c9_sections_a.py", "C-SSRS",
     "Columbia Suicide Severity Rating Scale, 0-5. Scores of 4 and 5 are "
     "active ideation with intent -- a threshold, not a gradient."),
    ("c9_sections_b.py", "hit policy",
     "A DMN decision table's rule for what to do when more than one row "
     "matches: FIRST, UNIQUE, PRIORITY, ANY or COLLECT. On an overlapping "
     "table there is no neutral choice."),
    ("c9_sections_b.py", "seam map",
     "The record of where a monolith is cut, which transactional units each "
     "cut crosses, and what replaces the atomicity the cut breaks."),
    ("c9_sections_c.py", "NQTL",
     "Non-quantitative treatment limitation. A process-level limit -- review "
     "frequency, step therapy, criteria strictness, network standards -- that "
     "parity puts in scope alongside numeric caps."),
]


def add_tooltip(text: str, term: str, definition: str) -> tuple[str, bool]:
    """Wrap the first bare occurrence of `term` in a tooltip span."""
    marker = f'<span class="term-tooltip">{term}'
    if marker in text:
        return text, False                      # already done

    # Skip occurrences inside a tag, a code span, or a heading.
    idx = 0
    while True:
        idx = text.find(term, idx)
        if idx == -1:
            return text, False
        before = text[max(0, idx - 120):idx]
        if ("<code>" in before and "</code>" not in before.split("<code>")[-1]):
            idx += len(term); continue
        if before.rstrip().endswith(("<h2", "<h3", "<h4", 'id="')):
            idx += len(term); continue
        line_start = text.rfind("\n", 0, idx)
        line = text[line_start:idx]
        if line.count("<") > line.count(">"):   # mid-tag
            idx += len(term); continue
        break

    span = (f'<span class="term-tooltip">{term}'
            f'<span class="tooltip-content">{definition}</span></span>')
    return text[:idx] + span + text[idx + len(term):], True


def main() -> int:
    changed = 0

    # ---- dual-language tabs -------------------------------------------
    for fname, block_id, ts_id, ts_lang, ts_code in [
        ("c9_sections_a.py", "seam-py", "seam-ts", "typescript", SEAM_TS),
        ("c9_sections_b.py", "seam-py", "seam-ts", "typescript", SEAM_TS),
        ("c9_sections_b.py", "harm-py", "harm-ts", "typescript", HARM_TS),
        ("c9_sections_c.py", "phi-py", "phi-ts", "typescript", PHI_TS),
        ("c9_sections_termmap.py", "termmap-py", "termmap-ts", "typescript", TERMMAP_TS),
    ]:
        path = os.path.join(HERE, fname)
        text = io.open(path, encoding="utf-8").read()
        old_tabs, new_tabs, new_panel = tabify(block_id, "python", ts_id,
                                               ts_lang, ts_code)
        if old_tabs not in text:
            continue
        text = text.replace(old_tabs, new_tabs, 1)

        # Append the TS panel after the Python panel's closing div.
        anchor = f'id="{block_id}"><pre><code class="language-python">'
        start = text.index(anchor)
        end = text.index("</code></pre></div>", start) + len("</code></pre></div>")
        text = text[:end] + new_panel + text[end:]

        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        print(f"  tabs: {fname} :: {block_id} -> + {ts_id}")
        changed += 1

    # ---- tooltips ------------------------------------------------------
    for fname, term, definition in TOOLTIPS:
        path = os.path.join(HERE, fname)
        text = io.open(path, encoding="utf-8").read()
        text, did = add_tooltip(text, term, definition)
        if did:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            print(f"  tooltip: {fname} :: {term}")
            changed += 1

    print(f"{changed} edits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
