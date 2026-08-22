"""Trap 9 -- business logic hiding in JSP scriptlets and JSTL guards.

In a server-rendered application of this era the view is the last place a
decision is made before a human sees it, so decisions migrate there. Not by
design: because that is where someone was standing when the requirement
arrived.

`<c:if test="${sessionScope.roleMask ge 4}">` wrapped around a deny button IS
the "only a physician may issue an adverse determination" rule when nothing
re-checks it server-side -- and on three of this system's four call paths,
nothing does.

**The failure this file exists to prevent: relocating a rule from JSTL to
`*ngIf`.** That is the same rule, in the same layer, with a different spelling.
It looks like migration and is not.
"""

import os

import pytest

from screen_inventory import (API_OMISSION, COMPUTED_FIELD, DERIVED_VALUE,
                              FIELD_VISIBILITY, InventoryError,
                              ROLE_GATE_ACTION, ROLE_GATE_SCREEN, ROUTE_GUARD,
                              SERVICE_CHECK, Screen, ScreenInventory, ViewRule,
                              scan_jsp)

# conftest puts both solution/ and solution/evaluation/ on the path, so these
# resolve against whichever tree the suite is pointed at.
import reference_screen_inventory as RSI     # noqa: E402
import route_writer as RW                    # noqa: E402


@pytest.fixture(scope="module")
def inventory():
    return RSI.build()


# ------------------------------------------- the rules really are in there


def test_the_scanner_finds_rules_in_the_decision_template(legacy_root):
    """Detection is regex; judgement is the agent's."""
    jsp = open(os.path.join(legacy_root, "src", "main", "webapp", "WEB-INF",
                            "jsp", "decision.jsp"), encoding="utf-8").read()
    found = scan_jsp(jsp)
    assert found["role_condition_count"] >= 3
    assert found["scriptlet_count"] >= 1
    assert found["numeric_bitmask_tests"], (
        "expected at least one numeric comparison standing in for a bitwise "
        "role test -- JSTL has no bitwise operator")


def test_scriptlets_compute_values_that_exist_nowhere_else(legacy_root):
    jsp = open(os.path.join(legacy_root, "src", "main", "webapp", "WEB-INF",
                            "jsp", "decision.jsp"), encoding="utf-8").read()
    body = " ".join(scan_jsp(jsp)["scriptlets"])
    assert "allowedHours" in body, "the regulatory turnaround clock"
    assert "daysLeft" in body, "the continued-stay countdown"


def test_every_legacy_screen_yields_at_least_one_rule(inventory):
    for screen in inventory.screens:
        assert screen.rules, f"{screen.jsp} contributed no rules -- read it again"


def test_eleven_rules_have_no_server_side_enforcement(inventory):
    """The headline finding of phase 9B.

    A rule whose only enforcement is a template is not enforced. Each of these
    disappears in a mechanical port, and the disappearance is invisible until
    someone issues a determination they were not licensed to issue.
    """
    unenforced = inventory.unenforced_rules()
    assert len(unenforced) >= 8, (
        f"only {len(unenforced)} rules found with no server-side equivalent -- "
        f"the templates carry more than that")

    screens = {jsp for jsp, _r in unenforced}
    assert "decision.jsp" in screens
    assert "search.jsp" in screens


def test_the_search_screen_undoes_the_decision_screens_control(inventory):
    """One finding, not two.

    decision.jsp hides the clinical narrative from intake coordinators. The
    search screen lets any authenticated user full-text search the same column
    and has no role check at all.
    """
    search = inventory.by_jsp("search.jsp")
    rule = next(r for r in search.rules if "Clinical search" in r.rule)
    assert rule.unenforced
    assert "Hiding the link is the entire control" in rule.server_side_equivalent


def test_the_role_rule_routes_to_a_workflow_group(inventory):
    """Where a task encodes licensure, the candidate group IS the rule."""
    from screen_inventory import WORKFLOW_GROUP
    decision = inventory.by_jsp("decision.jsp")
    rule = next(r for r in decision.rules if "nurse may approve" in r.rule)
    assert rule.proposed_home == WORKFLOW_GROUP
    assert "2 of the 4 call paths" in rule.server_side_equivalent


def test_field_visibility_becomes_an_api_omission(inventory):
    """A guard that emits content and hides it is not a control.

    The legacy controller loads the narrative unconditionally; the template
    only hides it. The content is in the response body either way, one
    developer-tools panel from view.
    """
    detail = inventory.by_jsp("authDetail.jsp")
    rule = next(r for r in detail.rules if "must not read" in r.rule)
    assert rule.proposed_home == API_OMISSION
    assert "RENDERING, not" in rule.server_side_equivalent


# ------------------------------------------- a template is not a new home


@pytest.mark.parametrize("home", ["template-conditional", "*ngIf", "ngIf",
                                  "client-side", "css", "hidden", "v-if"])
def test_a_template_is_refused_as_a_relocation(home):
    """THE test this file exists for."""
    screen = Screen(jsp="decision.jsp", route="/auth/:id/decide", controller="x")
    with pytest.raises(InventoryError, match="not a relocation|where you found it"):
        screen.add_rule(ViewRule(
            kind=ROLE_GATE_ACTION,
            source='<c:if test="${sessionScope.roleMask ge 4}">',
            rule="only a physician may deny",
            server_side_equivalent="NONE",
            proposed_home=home))


def test_a_rule_with_no_stated_server_side_equivalent_is_refused():
    """'NONE' is a finding and has to be said out loud."""
    screen = Screen(jsp="x.jsp", route="/x", controller="x")
    with pytest.raises(InventoryError, match="state the server-side equivalent"):
        screen.add_rule(ViewRule(
            kind=ROLE_GATE_ACTION, source="<c:if ...>", rule="a rule",
            server_side_equivalent="", proposed_home=SERVICE_CHECK))


def test_a_rule_with_no_quoted_source_is_refused():
    """A reviewer has to be able to find the conditional being described."""
    screen = Screen(jsp="x.jsp", route="/x", controller="x")
    with pytest.raises(InventoryError, match="quote the source"):
        screen.add_rule(ViewRule(
            kind=ROLE_GATE_ACTION, source="", rule="a rule",
            server_side_equivalent="NONE", proposed_home=SERVICE_CHECK))


def test_an_unknown_home_is_refused():
    screen = Screen(jsp="x.jsp", route="/x", controller="x")
    with pytest.raises(InventoryError, match="not in"):
        screen.add_rule(ViewRule(
            kind=ROLE_GATE_ACTION, source="<c:if ...>", rule="a rule",
            server_side_equivalent="NONE", proposed_home="somewhere"))


# --------------------------------------------------- the writer's refusals


def test_the_writer_refuses_an_action_rule_guarded_only_by_a_route():
    """A guard improves the experience. It is not a control.

    Anyone can call the API directly, so an action gate needs a server-side
    check as well.
    """
    inv = ScreenInventory()
    screen = inv.add(Screen(jsp="decision.jsp", route="/auth/:id/decide",
                            controller="x"))
    screen.add_rule(ViewRule(
        kind=ROLE_GATE_ACTION,
        source='<c:if test="${sessionScope.roleMask ge 4}">',
        rule="only a physician may deny",
        server_side_equivalent="NONE",
        proposed_home=ROUTE_GUARD))
    with pytest.raises(RW.RouteEmitError, match="route guard alone"):
        RW.emit(inv, lambda rel, content: None)


def test_the_writer_refuses_when_phase_9a_supplied_no_check():
    """The client cannot supply an enforcement the backend does not have.

    Reporting that is the correct behaviour; guarding around it and calling the
    rule migrated is not.
    """
    inv = ScreenInventory()
    screen = inv.add(Screen(jsp="search.jsp", route="/search", controller="x"))
    screen.add_rule(ViewRule(
        kind=ROLE_GATE_SCREEN,
        source='<c:if test="${sessionScope.roleMask ge 2}">',
        rule="clinical search is for clinical staff",
        server_side_equivalent="NONE -- SearchController has no role check",
        proposed_home=SERVICE_CHECK))
    with pytest.raises(RW.RouteEmitError, match="phase 9A did not emit one"):
        RW.emit(inv, lambda rel, content: None, server_side_checks=set())


def test_the_writer_refuses_an_unreachable_route():
    inv = ScreenInventory()
    inv.add(Screen(jsp="a.jsp", route="/a", controller="x", reachable_from=[]))
    inv.add(Screen(jsp="b.jsp", route="/b", controller="x",
                   reachable_from=["nowhere.jsp"]))
    with pytest.raises(RW.RouteEmitError, match="nothing links to it"):
        RW.emit(inv, lambda rel, content: None)


def test_the_writer_accepts_the_reference_inventory(inventory):
    written = RW.emit(inventory, lambda rel, content: None,
                      server_side_checks={r.rule for r in inventory.all_rules()})
    assert len(written) == 5


# --------------------------------------------- what the emitted code does


def test_the_emitted_decision_component_carries_no_role_conditional(inventory):
    """The three rules that lived in decision.jsp are not in its replacement."""
    emitted = {}
    RW.emit(inventory, lambda rel, content: emitted.__setitem__(rel, content),
            server_side_checks={r.rule for r in inventory.all_rules()})

    component = next(v for k, v in emitted.items() if "decision.component" in k)
    code = "\n".join(line for line in component.splitlines()
                     if not line.lstrip().startswith(("//", "*", "/*")))

    assert "roleMask" not in code, "the bitmask comparison was carried across"
    # The narrative is absent from the response unless the caller is entitled
    # to it, so there is no visibility conditional to write.
    assert "API omission" in component or "absent from the response" in component


def test_the_emitted_component_documents_where_each_rule_went(inventory):
    """A reader of the new code has to be able to find out where the rule is
    now. Otherwise the next port loses it again."""
    emitted = {}
    RW.emit(inventory, lambda rel, content: emitted.__setitem__(rel, content),
            server_side_checks={r.rule for r in inventory.all_rules()})
    component = next(v for k, v in emitted.items() if "decision.component" in k)

    assert "candidate group" in component
    assert "computed fields on the response" in component
    assert "NOWHERE ELSE" in component


def test_every_unenforced_rule_is_reported_for_the_gap_register(inventory):
    """Each rule with no server-side equivalent needs a register entry as well
    as a route -- it is a finding about the legacy system, not just work."""
    unenforced = inventory.unenforced_rules()
    assert unenforced
    for jsp, rule in unenforced:
        assert rule.proposed_home, f"{jsp}: {rule.rule} has no proposed home"
        assert rule.server_side_equivalent.upper().startswith("NONE")
