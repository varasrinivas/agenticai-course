"""A very small condition language: `name op number`, joined by and/or/not.

Parsed, never `eval`'d. The IR describes rules recovered from a legacy system,
and that is untrusted input as far as this process is concerned -- it arrives
from a model's reading of somebody else's code. `eval` on it would be a remote
code execution bug wearing a convenience.

It is also deliberately small. Anything it cannot parse RAISES rather than
returning False, because a condition this module cannot model is a condition
whose behaviour is unknown, and silently treating unknown as "does not match"
is how an overlap analysis returns a confident wrong answer.

The bundled `rules-to-dmn` skill ships its own copy of this logic on purpose:
a skill has to be self-contained to be portable, and the duplication is the
price of that. If you change the grammar here, change it there too.
"""

from __future__ import annotations

import re

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


class ConditionError(RuntimeError):
    """The condition uses something this module cannot model."""


def parse(text: str):
    """Return a tree of ('and'|'or'|'not', ...) nodes and ('atom', var, op, val)."""
    if not text or not text.strip():
        raise ConditionError("empty condition")

    s = text.strip()
    s = re.sub(r"\bAND\b", "and", s)
    s = re.sub(r"\bOR\b", "or", s)
    s = re.sub(r"\bNOT\b", "not", s)
    s = s.replace("&&", " and ").replace("||", " or ").replace("!", " not ")

    node, rest = _parse_or(_tokenise(s))
    if rest:
        raise ConditionError(f"trailing tokens: {rest[:3]}")
    return node


def _tokenise(s: str) -> list:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            out.append(c)
            i += 1
            continue
        m = ATOM.match(s, i)
        if m:
            out.append(("atom", m.group("var"), m.group("op"), float(m.group("val"))))
            i = m.end()
            continue
        w = re.match(r"(and|or|not)\b", s[i:])
        if w:
            out.append(w.group(1))
            i += w.end()
            continue
        raise ConditionError(f"cannot tokenise at {s[i:i + 24]!r}")
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
        raise ConditionError("unexpected end of condition")
    if tk[0] == "not":
        node, tk = _parse_unary(tk[1:])
        return ("not", node), tk
    if tk[0] == "(":
        node, tk = _parse_or(tk[1:])
        if not tk or tk[0] != ")":
            raise ConditionError("unbalanced parentheses")
        return node, tk[1:]
    if isinstance(tk[0], tuple) and tk[0][0] == "atom":
        return tk[0], tk[1:]
    raise ConditionError(f"unexpected token {tk[0]!r}")


def variables(node, acc=None) -> set[str]:
    acc = set() if acc is None else acc
    if node[0] == "atom":
        acc.add(node[1])
    else:
        for child in node[1:]:
            variables(child, acc)
    return acc


def evaluate(node, env: dict) -> bool:
    if node[0] == "atom":
        _, var, op, val = node
        if var not in env:
            raise ConditionError(f"no value for {var}")
        return OPS[op](env[var], val)
    if node[0] == "and":
        return evaluate(node[1], env) and evaluate(node[2], env)
    if node[0] == "or":
        return evaluate(node[1], env) or evaluate(node[2], env)
    if node[0] == "not":
        return not evaluate(node[1], env)
    raise ConditionError(f"unknown node {node[0]}")
