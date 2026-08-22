#!/usr/bin/env python3
"""Generate starter/ from solution/.

    python solution/make_starter.py [--check]

Why generated rather than hand-written: a starter that drifts from its solution
teaches the wrong thing twice -- a student implements to a signature that no
longer exists, and the tests fail for a reason that is not their mistake. The
TODO text below is hand-authored; the stripping is mechanical, so the two stay
in step.

`--check` re-generates into a temporary directory and diffs, so CI can fail
when the starter is stale.

WHAT IS GUTTED AND WHAT IS GIVEN
Anything `tests/` exercises directly is the exercise, so it is gutted. Anything
that is plumbing -- a condition parser, session state, a tracer -- is given
whole, because writing it teaches nothing this capstone is about.
"""

from __future__ import annotations

import argparse
import ast
import filecmp
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
STARTER = os.path.join(LAB, "starter")


# ---------------------------------------------------------------------------
# The manifest. One entry per file: which symbols to hollow out, and the TODO
# a student reads in the gap.
#
# TODOs are numbered in the order a student should tackle them. The order
# matters: the two rule engines come first because the divergence test is what
# makes every later phase measurable.
# ---------------------------------------------------------------------------

GUT = {
    "rules_ir.py": {
        "evaluate_legacy": """\
TODO 1 -- Transcribe the legacy ladder.

Read db/03_PKG_LOC_RULES.sql alongside this function. It is a STATEFUL
FIRST-MATCH LADDER: it mutates a running score across branches, some
branches commit and return, others adjust and fall through, and branch
ORDER is load-bearing.

Keep the branch numbers in your comments. The one classification that
matters: branch 3's `dim1 >= 4` arm COMMITS, and its `dim1 == 3` arm
ACCUMULATES. One source branch, two kinds.

Then TODO 2: LocRulesService.evaluate() is a SECOND layer that runs after
this one has already returned. Call it from here. It can only downgrade or
pend, never upgrade -- reproduce that asymmetry.

Verify: tests/test_rules_hit_policy.py""",
        "_apply_java_layer": """\
TODO 2 -- The second rules layer.

src/main/java/com/bridgeway/bhauth/service/LocRulesService.java

Three adjustments, applied AFTER the ladder has committed:
  A  benefit cap      -- caps units WITHOUT changing the level
  B  frequency pend   -- and read the 2016 compliance note above it
  C  network step-down

It reads inputs the PL/SQL never saw, two of which live in other teams'
schemas. Skip this layer and three of twelve golden cases come back wrong
-- and wrong plausibly.""",
        "evaluate_ir": """\
TODO 3 -- Evaluate a flattened decision table under a hit policy.

This is what a DMN engine does. Handle FIRST, UNIQUE, PRIORITY, ANY and
COLLECT, and raise HitPolicyError when the policy is not stated at all --
DMN defaults to UNIQUE, so silence is a production error waiting for the
first case that matches two rows.

UNIQUE must raise when more than one row matches. That is the honest
failure: the table is telling you the ladder's ordering carried
information it does not.""",
        "_derive_inputs": """\
TODO 4 -- Compute the derived inputs.

The running score is an INPUT, not a decision. Apply every accumulating
branch in order, then the derived flags.

Emitting an accumulating branch as a table row is the most common way to
produce a table that is subtly and permanently wrong.""",
        "diff_engines": """\
TODO 5 -- Run every case through both engines and report disagreements.

A non-zero result on your first run is expected. Classify each one before
you change anything: hit-policy artefact, unconverted layer, misclassified
branch, or a deliberate correction.""",
        "covers_overlap": """\
TODO 6 -- Does this case set contain a case that trips the branch-7 overlap?

Without one, a clean divergence report proves nothing -- the single input
that distinguishes a hit-policy decision from a lucky guess is not being
tested. Walk the accumulating branches and check whether any case reaches
score >= 10 with dimension 1 >= 3.""",
    },

    "gap_register.py": {
        "GapEntry.validate": """\
TODO 7 -- Enforce the register's constraints IN CODE.

A prompt that says "must-not-port requires a named harm" is a request. A
tool that returns an error is a rule.

  * every verdict cites evidence
  * must-not-port REQUIRES a named harm -- if you cannot name what goes
    wrong and for whom, the verdict is `extend`
  * must-build-new REQUIRES a requirement -- without one it is a wish, and
    the synthesizer will defer it

Verify: tests/test_flag_classification.py""",
        "GapRegister.acceptance_problems": """\
TODO 8 -- Say why this register would not pass.

Return strings, not exceptions -- the coordinator reports them and halts,
and a list reads better in a report than a traceback.

Include the uncomfortable one: a register that is mostly `port-as-is`
means the architecture was read and the domain was not.""",
        "GapRegister.render": """\
TODO 9 -- Render the register for the human at the approval gate.

Order by how much a reader needs to see it: must-not-port first, then
must-build-new. Show the harm on every must-not-port.""",
    },

    "seam_map.py": {
        "Seam.validate": """\
TODO 10 -- Refuse a seam that would silently lose a guarantee.

Three refusals:
  * coupling is must-be-atomic  -> this seam cannot be cut here. Move it,
    or record it as rejected. Compensation is not available for every kind
    of write: you cannot un-hold protected content you have already held.
  * crosses a transaction with no replacement -> "we will write the second
    row right after" is not an answer
  * a replacement missing any of its five fields

Verify: tests/test_consent_atomicity.py""",
        "AtomicityReplacement.problems": """\
TODO 11 -- All five fields are required.

mechanism, window, observable, compensation, alarm.

An eventual consistency with no observable and no alarm is the same as no
guarantee, implemented with more moving parts.""",
        "SeamMap.problems": """\
TODO 12 -- Report every write with no recorded reason for being in the
transaction.

That column is the one most likely to be undocumented, and it is the one
that decides whether a pair can be split at all.""",
    },

    "hooks.py": {
        "looks_like_protected_content": """\
TODO 13 -- Detect clinical narrative by SHAPE, not by keyword.

A narrative does not announce itself. Matching on "alcohol" or "opioid"
catches the obvious cases and misses everything a clinician wrote in a
hurry.

Prose in clinical register, or a narrative field name next to prose. Be
deliberately over-eager: a gate that blocks a config comment is annoying;
one that passes a treatment record is an unlawful disclosure.

AND STATE THE LIMIT. This is defence in depth, not a proof. The control
that actually holds is that every fixture here is synthetic.

Verify: tests/test_no_phi_in_prompt.py""",
        "redact_narrative": """\
TODO 14 -- Replace narrative-shaped runs with a TAGGED marker.

Tagged, not removed. Silently removing it leads the model to conclude the
field is empty and report the clinical narrative as absent, which is the
opposite of the finding.

Watch the last sentence of a paragraph. A pattern requiring whitespace
after the final full stop leaves one clinical sentence standing, and one
sentence is a disclosure.""",
        "filter_tool_result": """\
TODO 15 -- Inspect a tool RESULT before it reaches the model.

A PreToolUse hook runs before the tool and cannot see what it returns, so
this guarantee lives at the boundary where the data actually appears.

Allowlisted synthetic fixture -> allowed through, but BUDGETED. An agent
reading the whole seed file accumulates a clinical record in its
transcript one tool call at a time.
Anything else -> redacted, and say which path was refused.""",
        "enforce_source_readonly": """\
TODO 16 -- Deny path traversal out of either source tree.

These servers expose no write tools, so this is defence in depth. What it
actually catches is `../`.

Both trees are EVIDENCE. A parity validator that diffs the port against a
tree the agent can reach outside of is diffing against a moving target.

Verify: tests/test_hooks_readonly.py""",
        "hitl_finalization_gate": """\
TODO 17 -- The agent cannot approve its own modernization.

Deny unless a human set the environment variable by passing --approve.
The agent reads that variable and has no way to write it; that asymmetry
IS the gate.

Return the briefing with the denial -- assembled from the artifacts, not
from the agent's summary of them. The agent's account of its own run is
the thing under review.

Verify: tests/test_hitl_gate.py""",
        "redact": """\
TODO 18 -- Strip credentials, then narrative.

Careful with greedy patterns: `\\S+` after `password=` eats the closing
quote and brace, and an audit log that will not parse is worse than none
-- it fails exactly when something interesting was happening.""",
    },

    "tools_emit.py": {
        "record_gap": """\
TODO 19 -- Append to the gap register, enforcing its constraints.

Return the constraint violation as an ERROR rather than accepting it with
a warning. A register that accepts a must-not-port with no harm is a
register whose most important verdict means nothing.""",
        "queue_manual_review": """\
TODO 20 -- Refuse to convert something, and say why.

Require a QUESTION. Queueing an item without stating what a human has to
decide produces a list nobody can act on.""",
        "eval_rules": """\
TODO 21 -- Run one case through either engine.

A HitPolicyError is not a crash to route around: it is the table
reporting that the ladder's ordering carried information it does not.
Return it as a finding.""",
    },

    "dmn_writer.py": {
        "preflight": """\
TODO 22 -- Refuse to emit a table that would be wrong.

  * no hit policy stated
  * an unresolved overlap
  * no reachable DENIED output -- denials are the regulated event here
  * no diagnosis input

A writer that emits anyway and leaves a warning produces a file that looks
finished, which is worse: the next person reads the file and not the
warning.

Verify: tests/test_dmn_can_deny.py""",
        "to_feel": """\
TODO 23 -- One row's cell for one input, as a FEEL unary test.

A cell constrains exactly ONE input. When a condition couples two -- like
`score >= 8 and not (score >= 10 and dim1 >= 3)` -- you cannot write it as
a cell at all.

RAISE rather than guessing. The honest fix is a named derived input, and
naming the overlap puts it on the face of the table instead of in the row
order.""",
    },

    "bpmn_writer.py": {
        "preflight": """\
TODO 24 -- Refuse a process that cannot express the domain.

  * does not loop -- an approved BH authorization re-enters review on its
    cadence
  * no timer -- the cadence is a regulatory deadline, and a reminder job is
    a hope with a cron expression
  * a timer with no escalation
  * a user task with no candidate group -- where the task encodes
    licensure, the candidate group IS the rule

Verify: tests/test_concurrent_review_loop.py""",
    },

    "validation.py": {
        "Check.suspect": """\
TODO 25 -- When should a CLEAN result not be trusted?

Not merely because it is clean: a good port comes back clean on all four
expected-non-zero checks, and treating that as a failure would mean the
reference answer could never pass -- which is how a check teaches people
to ignore it.

Clean is suspicious when the check COULD NOT HAVE FIRED: it scanned
nothing, or the inputs cannot exercise what it is for.""",
        "check_protected_content_leak": """\
TODO 26 -- Scan every emitted sink for the clinical field.

Logs, event payloads, search mappings, audit columns, error paths.

Two things that are easy to miss: a narrative column inside an audit table
spans lines, so a line-by-line scan will not see it; and a COMMENT naming
the field is how a developer warns the next one, so flagging it teaches
the wrong lesson.

Verify: tests/test_part2_leak.py""",
        "check_consent_atomicity": """\
TODO 27 -- Is the invariant ENFORCED, or does it merely happen to hold?

Two parts, and the second is the one that matters. If the two writes live
in different services with no compensation, the state is clean today and
reachable tomorrow. Report the mechanism, not just the count.""",
        "check_screen_coverage": """\
TODO 28 (phase 9B) -- Every legacy screen routable, every view rule relocated.

Match a route DECLARATION, not a substring: "member" appears in
`memberLastName` in half the components.

Also catch a numeric comparison against a role bitmask carried over from
JSTL -- that was the permissive side of the divergence.

Verify: tests/test_screen_coverage.py""",
    },

    "term_map.py": {
        "TermMapping.validate": """TODO 32 -- Refuse a mapping that would be unsafe to act on.

The two systems model the same domain and named it differently, in two
ways that carry OPPOSITE risks:

  * different name, same concept -- the risk is MISSING the mapping. It
    announces itself: the names differ, so somebody goes looking.
  * same name, different meaning -- the risk is ASSUMING the mapping. A
    1:1 map compiles, passes review, and deletes concurrent review.
    THIS ONE IS SILENT.

So refuse: a mapping with no cited evidence; a divergence with no stated
HOW; a divergence with no stated ACTION for the port. And an absent
counterpart cannot claim identical semantics.

Note that `same_semantics` has no default. That is deliberate -- a
name-identical pair recorded without answering it is exactly the failure
this map exists to prevent.

Verify: tests/test_term_mapping.py""",
        "TermMap.acceptance_problems": """TODO 33 -- Say why this term map would not pass.

The one that matters: a map with NO same-name-different-meaning entries
has compared spellings rather than semantics. Both systems use SUBMITTED,
IN_REVIEW, APPROVED, DENIED and PENDED; four of those five do not mean
the same thing on both sides.

Also require that every value in the donor's status enum is accounted
for -- the ones that match by name are precisely the ones that get mapped
without being read.""",
    },

    "screen_inventory.py": {
        "ViewRule.validate": """\
TODO 29 (phase 9B) -- Refuse a rule that would be lost.

  * no quoted source -- a reviewer has to be able to find the conditional
  * no stated server-side equivalent -- "NONE" is a finding and has to be
    said out loud
  * a proposed home that is a TEMPLATE. Moving a rule from JSTL to `*ngIf`
    is the same rule, in the same layer, with a different spelling.

Verify: tests/test_view_rules_relocated.py""",
        "ScreenInventory.unreachable": """\
TODO 30 (phase 9B) -- Routes nothing links to.

Defined is not reachable. A route nothing reaches is a screen that has
disappeared -- silently, because the code is there and a file count
passes.""",
    },

    "route_writer.py": {
        "preflight": """\
TODO 31 (phase 9B) -- Refuse a client that would lose a rule.

Two refusals carry this phase:
  * a rule relocated into a template is where it was found
  * a GUARD IS NOT THE ENFORCEMENT. It stops a reviewer reaching a screen
    they cannot act on, which is worth having. Anyone can still call the
    API directly, so every ACTION gate needs a server-side check too --
    and where phase 9A did not emit one, say so rather than guarding
    around it.""",
    },
}

#: Copied whole. Plumbing, not the lesson.
GIVEN = {
    "condition.py", "session.py", "config.py",
    "observability/__init__.py", "observability/tracer.py",
    "observability/metrics.py",
    "evaluation/golden_cases.json", "evaluation/test_cases.json",
    "evaluation/reference_rules_ir.json",
    "evaluation/reference_screen_inventory.py",
    "evaluation/reference_term_map.py",
    "evaluation/test_suite.py",
}

#: Copied whole, with a banner. The student edits these as they go.
COPIED_WITH_BANNER = {
    "tools_reference.py", "tools_legacy.py", "report.py", "coordinator.py",
    "hooks_cli.py",
}

#: Never copied into the starter.
SKIP = {
    "make_starter.py",
    "evaluation/build_reference_run.py",   # builds the reference answer
}


BANNER = """\
# =============================================================================
# GIVEN COMPLETE. Read it, do not rewrite it.
#
# This file is plumbing, not the lesson. Your work is in the files carrying
# numbered TODOs -- run `grep -rn "TODO [0-9]" starter/` to list them in order.
# =============================================================================
"""


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def gut_file(source: str, targets: dict[str, str]) -> tuple[str, int]:
    """Replace each named function body with its TODO. Returns (text, count)."""
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)

    #: qualified name -> node, so "GapEntry.validate" addresses a method.
    found: dict[str, ast.AST] = {}

    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found[f"{prefix}{child.name}"] = child
            elif isinstance(child, ast.ClassDef):
                walk(child, f"{prefix}{child.name}.")

    walk(tree)

    # Bottom-up, so earlier line numbers stay valid.
    edits = []
    for name, todo in targets.items():
        node = found.get(name)
        if node is None:
            raise KeyError(f"no such symbol: {name}")
        edits.append((node, todo))
    edits.sort(key=lambda e: e[0].lineno, reverse=True)

    for node, todo in edits:
        body = node.body
        # Keep a docstring if there is one; it is the contract.
        first = body[0]
        keep_docstring = (isinstance(first, ast.Expr)
                          and isinstance(first.value, ast.Constant)
                          and isinstance(first.value.value, str))
        # `lines` is 0-indexed, ast line numbers are 1-indexed. A docstring
        # occupies lines[first.lineno - 1 : first.end_lineno], so keeping it
        # means starting the replacement AT first.end_lineno -- subtracting one
        # more swallows the closing quotes and leaves a file that will not
        # parse.
        start = first.end_lineno if keep_docstring else first.lineno - 1
        end = body[-1].end_lineno

        pad = _indent_of(lines[body[0].lineno - 1])
        block = [f"{pad}# {'-' * 68}\n"]
        block += [f"{pad}# {ln}\n" if ln else f"{pad}#\n"
                  for ln in todo.splitlines()]
        block += [f"{pad}# {'-' * 68}\n",
                  f'{pad}raise NotImplementedError("see the TODO above")\n']

        lines[start:end] = block

    return "".join(lines), len(edits)


def build(dest: str) -> dict:
    if os.path.isdir(dest):
        shutil.rmtree(dest)

    stats = {"gutted": 0, "todos": 0, "given": 0, "copied": 0, "config": 0}

    for dirpath, dirnames, filenames in os.walk(HERE):
        dirnames[:] = [d for d in dirnames
                       if d not in {"__pycache__", ".pytest_cache"}]
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, HERE).replace(os.sep, "/")
            if rel in SKIP or name.endswith(".pyc"):
                continue

            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)

            if rel.startswith(".claude/") or rel == "CLAUDE.md":
                # The knowledge and control planes are given whole. Writing a
                # skill from a blank file teaches nothing; reading four good
                # ones and then writing a fifth teaches a lot.
                shutil.copy2(full, out)
                stats["config"] += 1
                continue

            if rel in GUT:
                with open(full, encoding="utf-8") as fh:
                    text = fh.read()
                gutted, n = gut_file(text, GUT[rel])
                with open(out, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(gutted)
                stats["gutted"] += 1
                stats["todos"] += n
                continue

            if rel in GIVEN:
                shutil.copy2(full, out)
                stats["given"] += 1
                continue

            if rel in COPIED_WITH_BANNER or name.endswith(".py"):
                with open(full, encoding="utf-8") as fh:
                    text = fh.read()
                stripped = text.lstrip()
                if stripped.startswith(('"""', "'''")):
                    quote = stripped[:3]
                    close = text.index(quote, text.index(quote) + 3) + 3
                    text = text[:close] + "\n\n" + BANNER + text[close:]
                else:
                    text = BANNER + text
                with open(out, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                stats["copied"] += 1
                continue

            shutil.copy2(full, out)
            stats["copied"] += 1

    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="fail if starter/ is stale rather than regenerating it")
    args = ap.parse_args(argv)

    if args.check:
        tmp = tempfile.mkdtemp()
        try:
            build(os.path.join(tmp, "starter"))
            diff = filecmp.dircmp(STARTER, os.path.join(tmp, "starter"))
            stale = bool(diff.left_only or diff.right_only or diff.diff_files)

            def walk(d):
                nonlocal stale
                if d.left_only or d.right_only or d.diff_files:
                    stale = True
                for sub in d.subdirs.values():
                    walk(sub)

            walk(diff)
            if stale:
                print("starter/ is STALE. Re-run: python solution/make_starter.py",
                      file=sys.stderr)
                return 1
            print("starter/ is up to date")
            return 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    stats = build(STARTER)
    print(f"wrote {STARTER}")
    print(f"  {stats['gutted']} files gutted, {stats['todos']} numbered TODOs")
    print(f"  {stats['given']} given whole, {stats['copied']} copied, "
          f"{stats['config']} agent/skill/command files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
