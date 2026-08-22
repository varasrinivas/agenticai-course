#!/usr/bin/env python3
"""Overlap analysis for a decision-table IR.

Bundled with the `rules-to-dmn` skill. Step 3 of the runbook.

Enumerates every pair of COMMITTING rows and reports pairs that can both match
the same input, with a concrete witness. Reasoning about overlap by inspection
misses pairs whose conditions are on different variables -- which is exactly the
pair that matters.

    python dmn_overlap.py --ir artifacts/rules_ir.json
    python dmn_overlap.py --ir artifacts/rules_ir.json --report artifacts/overlap.md
    python dmn_overlap.py --ir artifacts/rules_ir.json --json

Exit codes: 0 no unresolved overlaps, 1 unresolved overlaps found, 2 usage error.

An overlap is NOT a bug in the legacy code. In a first-match ladder, overlapping
conditions plus ordering IS the rule. It becomes a problem only when the
ordering is flattened away -- which is what emitting a DMN table does.
"""

import argparse
import itertools
import json
import re
import sys

# --------------------------------------------------------------------------
# Conditions are parsed rather than eval'd. The IR is a description of legacy
# rules, and legacy rules are not a language we should be executing.
# --------------------------------------------------------------------------

# `name op number`, joined by and/or, optionally parenthesised or negated.
ATOM = re.compile(r"""
    \s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)
    \s*(?P<op><=|>=|<|>|==|=|!=)
    \s*(?P<val>-?\d+(?:\.\d+)?)\s*
""", re.X)

OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,
    "<":  lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


class Unparseable(Exception):
    """The condition uses something this checker cannot model."""


def parse_condition(text):
    """Parse into a nested structure of ('and'|'or'|'not', ...) and atoms.

    Deliberately small. Anything it cannot parse raises, and the caller reports
    the row as unanalysable rather than silently treating it as non-overlapping
    -- a false 'no overlap' is the one answer this script must never give.
    """
    if not text or not text.strip():
        raise Unparseable("empty condition")

    s = text.strip()
    # Normalise a few dialects into one.
    s = re.sub(r"\bAND\b", "and", s)
    s = re.sub(r"\bOR\b", "or", s)
    s = re.sub(r"\bNOT\b", "not", s)
    s = s.replace("&&", " and ").replace("||", " or ").replace("!", " not ")

    tokens = _tokenise(s)
    node, rest = _parse_or(tokens)
    if rest:
        raise Unparseable(f"trailing tokens: {rest[:3]}")
    return node


def _tokenise(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c in "()":
            out.append(c); i += 1; continue
        m = ATOM.match(s, i)
        if m:
            out.append(("atom", m.group("var"), m.group("op"), float(m.group("val"))))
            i = m.end(); continue
        w = re.match(r"(and|or|not)\b", s[i:])
        if w:
            out.append(w.group(1)); i += w.end(); continue
        raise Unparseable(f"cannot tokenise at {s[i:i + 24]!r}")
    return out


def _parse_or(tk):
    node, tk = _parse_and(tk)
    while tk and tk[0] == "or":
        rhs, tk = _parse_and(tk[1:])
        node = ("or", node, rhs)
    return node, tk


def _parse_and(tk):
    node, tk = _parse_unary(tk)
    while tk and tk[0] == "and":
        rhs, tk = _parse_unary(tk[1:])
        node = ("and", node, rhs)
    return node, tk


def _parse_unary(tk):
    if not tk:
        raise Unparseable("unexpected end of condition")
    if tk[0] == "not":
        node, tk = _parse_unary(tk[1:])
        return ("not", node), tk
    if tk[0] == "(":
        node, tk = _parse_or(tk[1:])
        if not tk or tk[0] != ")":
            raise Unparseable("unbalanced parentheses")
        return node, tk[1:]
    if isinstance(tk[0], tuple) and tk[0][0] == "atom":
        return tk[0], tk[1:]
    raise Unparseable(f"unexpected token {tk[0]!r}")


def variables(node, acc=None):
    acc = set() if acc is None else acc
    if node[0] == "atom":
        acc.add(node[1])
    else:
        for child in node[1:]:
            variables(child, acc)
    return acc


def evaluate(node, env):
    if node[0] == "atom":
        _, var, op, val = node
        if var not in env:
            raise Unparseable(f"no value for {var}")
        return OPS[op](env[var], val)
    if node[0] == "and":
        return evaluate(node[1], env) and evaluate(node[2], env)
    if node[0] == "or":
        return evaluate(node[1], env) or evaluate(node[2], env)
    if node[0] == "not":
        return not evaluate(node[1], env)
    raise Unparseable(f"unknown node {node[0]}")


def candidate_values(nodes, var):
    """Boundary values for one variable, taken from every threshold it appears at.

    Testing at, just below and just above each threshold is enough: these are all
    inequalities on a single variable, so behaviour only changes at a boundary.
    """
    vals = set()
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if n[0] == "atom":
            if n[1] == var:
                v = n[3]
                vals.update({v - 1, v, v + 1})
        else:
            stack.extend(n[1:])
    if not vals:
        vals = {0}
    return sorted(vals)


def find_witness(a, b, cap=20000):
    """Concrete input satisfying both conditions, or None."""
    vars_ = sorted(variables(a) | variables(b))
    if not vars_:
        return None
    domains = [candidate_values([a, b], v) for v in vars_]
    total = 1
    for d in domains:
        total *= len(d)
    if total > cap:
        # Too large to enumerate. Say so rather than reporting "no overlap":
        # a false negative here is the failure mode that matters.
        raise Unparseable(f"search space {total} exceeds cap {cap}")
    for combo in itertools.product(*domains):
        env = dict(zip(vars_, combo))
        try:
            if evaluate(a, env) and evaluate(b, env):
                return env
        except Unparseable:
            continue
    return None


# --------------------------------------------------------------------------


def analyse(ir):
    committing = [b for b in ir.get("branches", []) if b.get("kind") == "committing"]
    parsed, unparseable = [], []
    for b in committing:
        try:
            parsed.append((b, parse_condition(b.get("condition", ""))))
        except Unparseable as e:
            unparseable.append((b, str(e)))

    overlaps, undecidable = [], []
    for (ba, na), (bb, nb) in itertools.combinations(parsed, 2):
        try:
            w = find_witness(na, nb)
        except Unparseable as e:
            undecidable.append((ba["id"], bb["id"], str(e)))
            continue
        if w is not None:
            overlaps.append({
                "rows": [ba["id"], bb["id"]],
                "witness": {k: (int(v) if float(v).is_integer() else v) for k, v in w.items()},
                "under_first": _out(ba),
                "under_unique": "ERROR - two rules matched",
                "under_collect": [_out(ba), _out(bb)],
            })
    return {
        "committing_rows": len(committing),
        "analysed": len(parsed),
        "overlaps": overlaps,
        "unparseable": [{"id": b["id"], "reason": r} for b, r in unparseable],
        "undecidable": [{"rows": [x, y], "reason": r} for x, y, r in undecidable],
    }


def _out(branch):
    o = branch.get("outputs", {})
    return o.get("loc") or o.get("outcome") or branch["id"]


def resolved_ids(ir):
    """Overlap pairs the IR already records a resolution for."""
    out = set()
    for o in ir.get("overlaps", []):
        if o.get("resolution"):
            out.add(frozenset(o.get("rows", [])))
    return out


def render(result, ir):
    resolved = resolved_ids(ir)
    lines = ["# Overlap analysis", ""]
    lines.append(f"- committing rows: {result['committing_rows']}")
    lines.append(f"- analysed: {result['analysed']}")
    lines.append(f"- declared hit policy: `{ir.get('hit_policy', 'NOT STATED')}`")
    lines.append("")

    if ir.get("hit_policy") in (None, "", "NOT STATED"):
        lines.append("**No hit policy declared.** DMN defaults to UNIQUE, so an unstated "
                     "policy on an overlapping table is a production error waiting for the "
                     "first case that matches two rows.")
        lines.append("")

    if result["unparseable"]:
        lines.append("## Rows that could not be analysed")
        lines.append("")
        lines.append("These are **not** cleared. A condition this checker cannot model is a "
                     "condition whose overlaps are unknown.")
        lines.append("")
        for u in result["unparseable"]:
            lines.append(f"- `{u['id']}`: {u['reason']}")
        lines.append("")

    if result["undecidable"]:
        lines.append("## Pairs left undecided")
        lines.append("")
        for u in result["undecidable"]:
            lines.append(f"- `{u['rows'][0]}` / `{u['rows'][1]}`: {u['reason']}")
        lines.append("")

    if not result["overlaps"]:
        lines.append("## Overlaps")
        lines.append("")
        lines.append("None found among the analysed rows.")
        lines.append("")
        lines.append("Before trusting that: does the golden set actually exercise the "
                     "boundary these rows sit on? A clean overlap report plus a clean "
                     "divergence report usually means the fixtures miss the case, not "
                     "that the conversion is perfect.")
        return "\n".join(lines)

    lines.append("## Overlaps")
    lines.append("")
    for o in result["overlaps"]:
        pair = frozenset(o["rows"])
        mark = " *(resolved in IR)*" if pair in resolved else " **-- UNRESOLVED**"
        lines.append(f"### `{o['rows'][0]}` and `{o['rows'][1]}`{mark}")
        lines.append("")
        wit = ", ".join(f"{k}={v}" for k, v in sorted(o["witness"].items()))
        lines.append(f"Both match when `{wit}`.")
        lines.append("")
        lines.append("| Hit policy | Result |")
        lines.append("|---|---|")
        lines.append(f"| `FIRST` | {o['under_first']} -- only if row order survives translation |")
        lines.append(f"| `UNIQUE` | {o['under_unique']} |")
        lines.append(f"| `COLLECT` | {', '.join(str(x) for x in o['under_collect'])} |")
        lines.append("| `PRIORITY` | whichever output the priority list ranks higher |")
        lines.append("")
        if pair not in resolved:
            lines.append("**Resolve this before emitting the table.** The usual fix is to "
                         "tighten the lower row with the negation of the upper one, so the "
                         "exclusion that was encoded as *position* becomes encoded as a "
                         "*condition*.")
            lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ir", required=True, help="Path to the rules IR JSON.")
    ap.add_argument("--report", help="Write a markdown report here.")
    ap.add_argument("--json", action="store_true", help="Emit the raw analysis as JSON.")
    args = ap.parse_args(argv)

    with open(args.ir, "r", encoding="utf-8") as fh:
        ir = json.load(fh)

    result = analyse(ir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        report = render(result, ir)
        print(report)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                fh.write(report + "\n")

    resolved = resolved_ids(ir)
    unresolved = [o for o in result["overlaps"] if frozenset(o["rows"]) not in resolved]
    blocked = unresolved or result["unparseable"] or result["undecidable"]
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
