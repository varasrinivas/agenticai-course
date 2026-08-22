"""The screen inventory, and the rules found inside views.

Phase 9B exists because of one thing: **in a server-rendered application of
this era, the view is the last place a decision is made before a human sees
it, so decisions migrate there.** Not by design -- because that is where
someone was standing when the requirement arrived.

A role check wrapped around a button IS the authorization rule when nothing
re-checks it server-side, and on three of this system's four call paths
nothing does. An agent that ports the screen as markup emits a component that
renders the deny button for everyone. It looks right. It passes any test
anyone writes for it. It is wrong in a way that shows up as an unlicensed
determination.

So this module refuses to record a rule without a **proposed new home**, and
refuses to accept a template conditional as that home. A rule reported without
one gets re-implemented as `*ngIf` in the new stack, which is where it was
found.

No SDK import: the inventory has to be constructible and testable without an
API key.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

# What kind of thing was found in the template.
ROLE_GATE_SCREEN = "role-gate-screen"      # a role decides whether the page is reachable
ROLE_GATE_ACTION = "role-gate-action"      # a role decides whether an action is offered
DERIVED_VALUE = "derived-value"            # a scriptlet computes something shown to a human
FIELD_VISIBILITY = "field-visibility"      # a role decides whether a field is rendered
NAVIGATION = "navigation"                  # a link or form target

RULE_KINDS = (ROLE_GATE_SCREEN, ROLE_GATE_ACTION, DERIVED_VALUE,
              FIELD_VISIBILITY, NAVIGATION)

# Where a rule is allowed to land.
ROUTE_GUARD = "route-guard"
SERVICE_CHECK = "service-check"
COMPUTED_FIELD = "computed-field"          # on the API response, not in the client
DECISION_INPUT = "decision-input"
API_OMISSION = "api-omission"              # the endpoint must not return the field
WORKFLOW_GROUP = "workflow-candidate-group"

HOMES = (ROUTE_GUARD, SERVICE_CHECK, COMPUTED_FIELD, DECISION_INPUT,
         API_OMISSION, WORKFLOW_GROUP)

#: Homes that are not homes. Moving a rule from JSTL to Angular's template
#: syntax has relocated nothing -- it is the same rule in the same layer with a
#: different spelling.
REJECTED_HOMES = {
    "template-conditional", "ngif", "*ngif", "client-side", "css",
    "hidden", "v-if", "jstl",
}


class InventoryError(ValueError):
    """A rule that would be lost, or relocated to somewhere that is not a home."""


@dataclass
class ViewRule:
    kind: str
    #: Quoted from the template, so a reviewer can find it.
    source: str
    #: What the rule actually says, in a sentence.
    rule: str
    #: Where the same rule is enforced server-side today, or "NONE".
    #: "NONE" is the finding: a rule whose only enforcement is client-side is
    #: not enforced.
    server_side_equivalent: str
    proposed_home: str
    note: str = ""

    def validate(self) -> None:
        # --------------------------------------------------------------------
        # TODO 29 (phase 9B) -- Refuse a rule that would be lost.
        #
        #   * no quoted source -- a reviewer has to be able to find the conditional
        #   * no stated server-side equivalent -- "NONE" is a finding and has to be
        #     said out loud
        #   * a proposed home that is a TEMPLATE. Moving a rule from JSTL to `*ngIf`
        #     is the same rule, in the same layer, with a different spelling.
        #
        # Verify: tests/test_view_rules_relocated.py
        # --------------------------------------------------------------------
        raise NotImplementedError("see the TODO above")

    @property
    def unenforced(self) -> bool:
        """True when the template is the only thing standing behind this rule."""
        return self.server_side_equivalent.strip().upper().startswith("NONE")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["unenforced"] = self.unenforced
        return d


@dataclass
class Screen:
    jsp: str
    route: str
    controller: str
    reachable_from: list[str] = field(default_factory=list)
    rules: list[ViewRule] = field(default_factory=list)
    #: Roles that may reach the route at all. Empty means public to any
    #: authenticated user, which is itself worth stating explicitly.
    required_roles: list[str] = field(default_factory=list)
    note: str = ""

    def add_rule(self, rule: ViewRule) -> ViewRule:
        rule.validate()
        self.rules.append(rule)
        return rule

    def unenforced_rules(self) -> list[ViewRule]:
        return [r for r in self.rules if r.unenforced]

    def to_dict(self) -> dict:
        return {
            "jsp": self.jsp, "route": self.route, "controller": self.controller,
            "reachable_from": self.reachable_from,
            "required_roles": self.required_roles,
            "note": self.note,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class ScreenInventory:
    screens: list[Screen] = field(default_factory=list)
    #: from -> to, as the legacy navigation graph.
    navigation: list[dict] = field(default_factory=list)

    def add(self, screen: Screen) -> Screen:
        if self.by_jsp(screen.jsp):
            raise InventoryError(f"{screen.jsp} is already in the inventory")
        self.screens.append(screen)
        return screen

    def by_jsp(self, jsp: str) -> Screen | None:
        return next((s for s in self.screens if s.jsp == jsp), None)

    def by_route(self, route: str) -> Screen | None:
        return next((s for s in self.screens if s.route == route), None)

    def routes(self) -> list[str]:
        return [s.route for s in self.screens]

    def all_rules(self) -> list[ViewRule]:
        return [r for s in self.screens for r in s.rules]

    def unenforced_rules(self) -> list[tuple[str, ViewRule]]:
        """Every rule whose only enforcement is a template.

        These are the ones that vanish in a mechanical port, and each one needs
        a `record_gap` entry as well as a route.
        """
        return [(s.jsp, r) for s in self.screens for r in s.unenforced_rules()]

    # -------------------------------------------------------- reachability

    def unreachable(self) -> list[str]:
        """Routes nothing links to.

        A route that is defined and not reachable is a screen that has
        disappeared, and it disappears silently -- the code is there, so a
        file-count check passes.
        """
        # --------------------------------------------------------------------
        # TODO 30 (phase 9B) -- Routes nothing links to.
        #
        # Defined is not reachable. A route nothing reaches is a screen that has
        # disappeared -- silently, because the code is there and a file count
        # passes.
        # --------------------------------------------------------------------
        raise NotImplementedError("see the TODO above")

    def problems(self) -> list[str]:
        out: list[str] = []
        for s in self.screens:
            if not s.route:
                out.append(f"{s.jsp} has no route")
        for route in self.unreachable():
            out.append(f"{route} is defined but nothing links to it")
        return out

    # ------------------------------------------------------------------ io

    def to_dict(self) -> dict:
        return {
            "screens": [s.to_dict() for s in self.screens],
            "navigation": self.navigation,
            "unenforced_rule_count": len(self.unenforced_rules()),
            "problems": self.problems(),
        }

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "ScreenInventory":
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        inv = cls(navigation=doc.get("navigation", []))
        for s in doc.get("screens", []):
            screen = Screen(
                jsp=s["jsp"], route=s["route"], controller=s.get("controller", ""),
                reachable_from=s.get("reachable_from", []),
                required_roles=s.get("required_roles", []),
                note=s.get("note", ""))
            for r in s.get("rules", []):
                screen.rules.append(ViewRule(
                    kind=r["kind"], source=r["source"], rule=r["rule"],
                    server_side_equivalent=r["server_side_equivalent"],
                    proposed_home=r["proposed_home"], note=r.get("note", "")))
            inv.screens.append(screen)
        return inv

    def render(self) -> str:
        lines = ["SCREEN INVENTORY", "=" * 72, ""]
        for s in self.screens:
            roles = ", ".join(s.required_roles) or "any authenticated user"
            lines.append(f"  {s.jsp:<20} -> {s.route}")
            lines.append(f"  {'':<20}    controller: {s.controller}")
            lines.append(f"  {'':<20}    roles     : {roles}")
            if s.reachable_from:
                lines.append(f"  {'':<20}    linked from: {', '.join(s.reachable_from)}")
            for r in s.rules:
                mark = "  *** UNENFORCED ***" if r.unenforced else ""
                lines.append(f"      [{r.kind}]{mark}")
                lines.append(f"        rule   : {r.rule}")
                lines.append(f"        source : {r.source}")
                lines.append(f"        today  : {r.server_side_equivalent}")
                lines.append(f"        -> home: {r.proposed_home}")
            lines.append("")

        unenforced = self.unenforced_rules()
        lines.append(f"-- RULES WITH NO SERVER-SIDE ENFORCEMENT ({len(unenforced)}) "
                     + "-" * 24)
        for jsp, rule in unenforced:
            lines.append(f"  {jsp}: {rule.rule}")
        lines.append("")
        lines.append("  These are the rules that vanish in a mechanical port. Each")
        lines.append("  needs a gap-register entry as well as a route.")
        lines.append("")

        for p in self.problems():
            lines.append(f"  * {p}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------
#
# The DETECTION is regex; the JUDGEMENT is the agent's. Finding
# `<c:if test="${sessionScope.roleMask ge 4}">` is a job for a pattern. Deciding
# that it means "only a physician may issue an adverse determination" -- and
# that the numeric comparison is standing in for a bitwise test -- is not.

_ROLE_COND = re.compile(
    r'<c:(?:if|when)\s+test="\$\{([^}]*(?:role|Role)[^}]*)\}"', re.I)
_SCRIPTLET = re.compile(r"<%(?!--|@|=)(.*?)%>", re.S)
_FORM = re.compile(r'<form[^>]*action="([^"]+)"[^>]*>', re.I)
_INCLUDE = re.compile(r'<jsp:include\s+page="([^"]+)"')


def scan_jsp(text: str) -> dict:
    """Candidate rule sites in one template. Detection only.

    Returns raw findings for an agent to interpret. It deliberately does NOT
    guess at what a conditional means -- a wrong interpretation recorded
    confidently is worse than a site flagged for reading.
    """
    role_conditions = _ROLE_COND.findall(text)
    scriptlets = [s.strip() for s in _SCRIPTLET.findall(text) if s.strip()]

    return {
        "role_conditions": role_conditions,
        "role_condition_count": len(role_conditions),
        # A numeric comparison against a bitmask is an APPROXIMATION of the
        # real test, and it is the permissive side of the divergence.
        "numeric_bitmask_tests": [c for c in role_conditions
                                  if re.search(r"\b(ge|gt|le|lt|>=|<=)\s*\d+", c)],
        "scriptlets": scriptlets,
        "scriptlet_count": len(scriptlets),
        "form_actions": _FORM.findall(text),
        "includes": _INCLUDE.findall(text),
    }
