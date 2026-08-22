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
    # --------------------------------------------------------------------
    # TODO 22 -- Refuse to emit a table that would be wrong.
    #
    #   * no hit policy stated
    #   * an unresolved overlap
    #   * no reachable DENIED output -- denials are the regulated event here
    #   * no diagnosis input
    #
    # A writer that emits anyway and leaves a warning produces a file that looks
    # finished, which is worse: the next person reads the file and not the
    # warning.
    #
    # Verify: tests/test_dmn_can_deny.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def to_feel(condition: str, variable: str) -> str:
    """One row's cell for one input variable, as a FEEL unary test.

    Returns "-" (any) when the condition does not constrain this variable.
    Compound conditions on the same variable become a range where they can be,
    and are otherwise rejected -- a cell this function cannot express honestly
    is a cell that must not be guessed at.
    """
    # --------------------------------------------------------------------
    # TODO 23 -- One row's cell for one input, as a FEEL unary test.
    #
    # A cell constrains exactly ONE input. When a condition couples two -- like
    # `score >= 8 and not (score >= 10 and dim1 >= 3)` -- you cannot write it as
    # a cell at all.
    #
    # RAISE rather than guessing. The honest fix is a named derived input, and
    # naming the overlap puts it on the face of the table instead of in the row
    # order.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


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
