"""Render a rules IR as a Camunda DMN decision table.

Refuses to emit in three cases, and each refusal is the point of the module:

  1. No hit policy stated. DMN defaults to UNIQUE, so an unstated policy on an
     overlapping table is a production error waiting for the first case that
     matches two rows.
  2. Unresolved overlaps. Flattening a first-match ladder throws the ordering
     away; if two rows can both match and nothing says which wins, the table
     does not mean what the ladder meant.
  3. No reachable denial output. In behavioral health the denial is the
     regulated event, and a table that can only approve or pend cannot produce
     one -- which is what mirroring the reference platform's table shape gets
     you.

A writer that emits anyway and leaves a warning produces a file that looks
finished. That is worse than a refusal, because the next person reads the file
and not the warning.
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

from rules_ir import review_interval


class DmnEmitError(RuntimeError):
    """The IR is not ready to be a decision table."""


_FEEL_OPS = {">=": ">=", "<=": "<=", ">": ">", "<": "<", "==": "=", "=": "=", "!=": "!="}


def preflight(ir: dict) -> list[str]:
    """Everything that would make this table wrong. Empty means ready."""
    problems: list[str] = []

    policy = (ir.get("hit_policy") or "").upper()
    if not policy:
        problems.append(
            "no hit policy stated. DMN defaults to UNIQUE; an unstated policy "
            "on an overlapping table fails at evaluation, on the first case "
            "that matches two rows.")
    elif policy not in {"FIRST", "UNIQUE", "PRIORITY", "ANY", "COLLECT"}:
        problems.append(f"hit policy {policy!r} is not a DMN hit policy")

    if policy and not (ir.get("hit_policy_justification") or "").strip():
        problems.append(
            "hit policy stated with no justification. Which policy reproduces a "
            "first-match ladder is a decision with consequences; record why.")

    unresolved = [o for o in ir.get("overlaps", []) if not o.get("resolution")]
    if unresolved:
        rows = "; ".join(" and ".join(o.get("rows", [])) for o in unresolved)
        problems.append(
            f"unresolved overlaps: {rows}. The usual fix is to tighten the lower "
            f"row with the negation of the upper one, so the exclusion that was "
            f"encoded as position becomes encoded as a condition.")

    committing = [b for b in ir.get("branches", []) if b.get("kind") == "committing"]
    if not committing:
        problems.append("no committing branches -- there are no rows to emit")

    outcomes = {(b.get("outputs") or {}).get("outcome") for b in committing}
    outcomes.discard(None)
    if "DENIED" not in outcomes:
        problems.append(
            "no rule can output DENIED. Denials are the regulated event in "
            "behavioral health and each must trace to an applied criterion. "
            "If the source engine deliberately PENDS instead of denying -- only "
            "a physician may issue an adverse determination -- record that as a "
            "separation-of-duties rule in the register rather than leaving the "
            "table unable to express a denial at all.")

    inputs = {str(i.get("name") or "") for i in ir.get("inputs", [])}
    if not any(n == "dx" or n.startswith("diagnosis") for n in inputs):
        problems.append(
            "no diagnosis input. The reference platform's table has none either, "
            "and mirroring that gives a level-of-care engine that cannot see what "
            "it is treating.")

    for b in committing:
        if not (b.get("condition") or "").strip():
            problems.append(f"row {b.get('id')} has no condition")
        if not (b.get("outputs") or {}):
            problems.append(f"row {b.get('id')} has no outputs")

    return problems


def to_feel(condition: str, variable: str) -> str:
    """One row's cell for one input variable, as a FEEL unary test.

    Returns "-" (any) when the condition does not constrain this variable.
    Compound conditions on the same variable become a range where they can be,
    and are otherwise rejected -- a cell this function cannot express honestly
    is a cell that must not be guessed at.
    """
    atoms = re.findall(
        rf"\b{re.escape(variable)}\s*(<=|>=|<|>|==|=|!=)\s*(-?\d+(?:\.\d+)?)", condition)
    if not atoms:
        return "-"
    if len(atoms) == 1:
        op, val = atoms[0]
        val = _num(val)
        return val if op in ("==", "=") else f"{_FEEL_OPS[op]}{val}"

    lows = [(_FEEL_OPS[o], _num(v)) for o, v in atoms if o in (">=", ">")]
    highs = [(_FEEL_OPS[o], _num(v)) for o, v in atoms if o in ("<=", "<")]
    if len(lows) == 1 and len(highs) == 1 and len(atoms) == 2:
        lo_op, lo = lows[0]
        hi_op, hi = highs[0]
        return f"[{lo}..{hi}{']' if hi_op == '<=' else ')'}" if lo_op == ">=" \
            else f"({lo}..{hi}{']' if hi_op == '<=' else ')'}"

    raise DmnEmitError(
        f"cannot express {condition!r} as a single FEEL cell for {variable!r}. "
        f"Split the row, or move the logic into a derived input -- do not guess "
        f"at a cell.")


def _num(v: str) -> str:
    f = float(v)
    return str(int(f)) if f.is_integer() else str(f)


def render(ir: dict, *, decision_id: str = "bh-loc-decision",
           name: str = "BH level of care") -> str:
    problems = preflight(ir)
    if problems:
        raise DmnEmitError(
            "refusing to emit a decision table:\n  - " + "\n  - ".join(problems))

    policy = ir["hit_policy"].upper()
    inputs = ir.get("inputs", [])
    committing = [b for b in ir.get("branches", []) if b.get("kind") == "committing"]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"',
        '             xmlns:camunda="http://camunda.org/schema/1.0/dmn"',
        f'             id="{decision_id}-definitions"',
        f'             name="{escape(name)}"',
        '             namespace="http://bridgeway.example/bh-um">',
        "",
        "  <!--",
        "    Generated from the rules IR. Read this next to db/03_PKG_LOC_RULES.sql.",
        "",
        f"    HIT POLICY: {policy}",
        f"    {_wrap(ir.get('hit_policy_justification', ''), 4)}",
        "",
        "    The legacy engine is a STATEFUL FIRST-MATCH LADDER: it mutates a",
        "    running score across branches and commits on the first branch that",
        "    decides. Branch ORDER is load-bearing there. This table has no",
        "    ordering, so the hit policy above carries what the ordering carried.",
        "",
        "    The score is a DERIVED INPUT, not a decision. The accumulating",
        "    branches that produce it are documented below and are NOT rows;",
        "    emitting one as a row is the most common way to get this wrong.",
        "  -->",
        "",
    ]

    accumulating = [b for b in ir.get("branches", []) if b.get("kind") == "accumulating"]
    if accumulating:
        lines.append("  <!-- Derived input `score`, accumulated before any row is matched:")
        for b in accumulating:
            lines.append(f"         {b.get('id'):<6} {b.get('condition'):<40} "
                         f"score {'+' if float(b.get('delta', 0)) >= 0 else ''}"
                         f"{b.get('delta')}")
        lines.append("  -->")
        lines.append("")

    lines.append(f'  <decision id="{decision_id}" name="{escape(name)}">')
    lines.append(f'    <decisionTable id="{decision_id}-table" hitPolicy="{policy}">')

    for i in inputs:
        var = i.get("name")
        label = i.get("label") or var
        typ = "string" if i.get("type") == "string" else "double"
        derived = (" <!-- DERIVED: %s -->" % _comment_safe(i.get("expression"))
                   if i.get("derived") else "")
        lines.append(f'      <input id="in-{var}" label="{escape(label)}">{derived}')
        lines.append(f'        <inputExpression id="ie-{var}" typeRef="{typ}">')
        lines.append(f"          <text>{escape(str(var))}</text>")
        lines.append("        </inputExpression>")
        lines.append("      </input>")

    for out_name, type_ref in (("outcome", "string"), ("granted_loc", "string"),
                               ("granted_units", "double"), ("interval_days", "double"),
                               ("reason_code", "string")):
        lines.append(f'      <output id="out-{out_name}" label="{out_name}" '
                     f'name="{out_name}" typeRef="{type_ref}" />')

    for b in committing:
        rid = b.get("id")
        cond = b.get("condition", "")
        out = b.get("outputs") or {}
        lines.append(f'      <rule id="rule-{escape(str(rid))}">')
        lines.append(f"        <description>{escape(str(b.get('note') or cond))}</description>")
        for i in inputs:
            cell = to_feel(cond, i.get("name"))
            lines.append(f'          <inputEntry id="ie-{rid}-{i.get("name")}">'
                         f"<text>{escape(cell)}</text></inputEntry>")
        loc = out.get("loc")
        lines.append(_out_entry(rid, "outcome", out.get("outcome"), quoted=True))
        lines.append(_out_entry(rid, "granted_loc", loc, quoted=True))
        lines.append(_out_entry(rid, "granted_units", out.get("units")))
        lines.append(_out_entry(
            rid, "interval_days",
            out.get("interval_days") if out.get("interval_days") is not None
            else review_interval(loc)))
        lines.append(_out_entry(rid, "reason_code", out.get("reason_code"), quoted=True))
        lines.append("      </rule>")

    lines.append("    </decisionTable>")
    lines.append("  </decision>")
    lines.append("</definitions>")
    return "\n".join(lines) + "\n"


def _out_entry(rule_id: str, name: str, value, *, quoted: bool = False) -> str:
    if value is None:
        text = "null"
    elif quoted:
        text = f'"{escape(str(value))}"'
    elif isinstance(value, str) and value.startswith("min("):
        # `min(requested, 10)` is a cap, not a constant. FEEL can express it.
        cap = value.rstrip(")").split(",")[-1].strip()
        text = f"min(requested_units, {cap})"
    else:
        text = escape(str(value))
    return f'          <outputEntry id="oe-{rule_id}-{name}"><text>{text}</text></outputEntry>'


def _comment_safe(text: str) -> str:
    """`--` cannot appear inside an XML comment.

    The justification prose is written for humans and uses double dashes freely,
    which produces a file that looks fine and does not parse. Caught by feeding
    the reference IR through the writer and running the output past a parser --
    which is why the tests parse the XML rather than grepping it.
    """
    return str(text).replace("--", "—")


def _wrap(text: str, indent: int) -> str:
    if not text:
        return "(no justification recorded)"
    pad = " " * indent
    words, line, out = _comment_safe(text).split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > 72:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    out.append(line)
    return ("\n" + pad).join(out)
