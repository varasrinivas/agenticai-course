"""Phase 9B -- every legacy screen has a reachable route.

The reference platform contributes one unrouted form. It declares
`@angular/router` as a dependency and never calls `provideRouter`; its three
shared components are exported and never imported; its service URL is
hardcoded to a laptop.

So there is no shape to copy, and copying the one thing that does exist is the
risk this phase has to survive.
"""

import os

import pytest

import validation
from screen_inventory import Screen, ScreenInventory, ViewRule

# conftest puts both solution/ and solution/evaluation/ on the path, so these
# resolve against whichever tree the suite is pointed at.
import reference_screen_inventory as RSI     # noqa: E402
import route_writer as RW                    # noqa: E402


@pytest.fixture(scope="module")
def inventory():
    return RSI.build()


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def emit_client(root, inventory):
    RW.emit(inventory, lambda rel, content: write(root, rel, content),
            server_side_checks=_all_service_rules(inventory))
    return root


def _all_service_rules(inventory):
    return {r.rule for r in inventory.all_rules()}


# ----------------------------------------------------------- the inventory


def test_all_seven_legacy_screens_are_inventoried(inventory, legacy_root):
    """Read from the filesystem, not from a list I typed."""
    jsp_dir = os.path.join(legacy_root, "src", "main", "webapp", "WEB-INF", "jsp")
    on_disk = {f for f in os.listdir(jsp_dir) if f.endswith(".jsp")}
    on_disk -= {"error.jsp"}          # reached via web.xml error-page, not a screen

    inventoried = {s.jsp for s in inventory.screens}
    assert inventoried == on_disk, (
        f"missing from the inventory: {sorted(on_disk - inventoried)}; "
        f"not on disk: {sorted(inventoried - on_disk)}")


def test_every_screen_has_a_route(inventory):
    for s in inventory.screens:
        assert s.route.startswith("/"), f"{s.jsp} has no absolute route"
    assert len(set(inventory.routes())) == len(inventory.screens), "duplicate routes"


def test_every_route_is_reachable(inventory):
    """Defined is not reachable. A route nothing links to is a screen that has
    disappeared -- silently, because the code is there and a file count
    passes."""
    assert inventory.unreachable() == []
    assert inventory.problems() == []


def test_the_reference_platform_has_no_router(reference_root):
    """The baseline this phase is measured against."""
    config = os.path.join(reference_root, "apps", "intake-ui", "src", "app",
                          "app.config.ts")
    text = open(config, encoding="utf-8").read()
    assert "provideHttpClient" in text
    assert "provideRouter" not in text, "the donor is expected to have no router"

    pkg = open(os.path.join(reference_root, "apps", "intake-ui", "package.json"),
               encoding="utf-8").read()
    assert "@angular/router" in pkg, (
        "the router IS a declared dependency -- installed and never wired. That "
        "gap is the finding, and inferring 'routing: present' from the manifest "
        "is the mistake.")


# --------------------------------------------------------------- the check


def test_a_client_with_no_router_is_caught(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-intake-ui/src/app/app.config.ts",
          "export const appConfig = { providers: [provideHttpClient()] };")
    c = validation.check_screen_coverage(root, {})
    assert any("no router wired" in f.detail for f in c.findings)


def test_a_missing_screen_is_caught(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    # Remove one route from the emitted file.
    routes = os.path.join(root, "apps/bh-intake-ui/src/app/app.routes.ts")
    text = open(routes, encoding="utf-8").read().replace(
        "path: 'member/:id/consent',", "path: 'somewhere-else',")
    open(routes, "w", encoding="utf-8").write(text)

    c = validation.check_screen_coverage(root, inventory.to_dict())
    assert any("consentAdmin.jsp" in f.where for f in c.findings)


def test_a_numeric_role_comparison_is_caught(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    write(root, "apps/bh-intake-ui/src/app/features/decision/bad.component.ts",
          "if (session.roleMask >= 4) { this.showDeny = true; }")
    c = validation.check_screen_coverage(root, inventory.to_dict())
    assert any("numeric role comparison" in f.detail for f in c.findings)


def test_a_hardcoded_service_url_is_caught(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    write(root, "apps/bh-intake-ui/src/app/case.service.ts",
          "const url = 'http://localhost:3000/prior-auth';")
    c = validation.check_screen_coverage(root, inventory.to_dict())
    assert any("hardcoded service URL" in f.detail for f in c.findings)


def test_orphaned_shared_components_are_caught(tmp_path):
    root = str(tmp_path)
    write(root, "apps/bh-intake-ui/src/app/app.routes.ts",
          "export const routes: Routes = [{ path: 'worklist' }];")
    c = validation.check_screen_coverage(root, {"screens": []})
    assert any("shared UI library is not imported" in f.detail for f in c.findings)


def test_the_reference_client_is_clean(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    c = validation.check_screen_coverage(root, inventory.to_dict())
    assert c.count == 0, [f.detail for f in c.findings]
    assert c.scanned >= 5


def test_the_check_reports_a_missing_client_rather_than_passing(tmp_path):
    c = validation.check_screen_coverage(str(tmp_path), {})
    assert c.count == 0
    assert "phase 9B did not run" in c.note


# ---------------------------------------------------------- what we emit


def test_the_emitted_routes_cover_every_screen(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    routes = open(os.path.join(root, "apps/bh-intake-ui/src/app/app.routes.ts"),
                  encoding="utf-8").read()
    for screen in inventory.screens:
        stem = screen.route.lstrip("/").split("/")[0]
        assert f"'{stem}" in routes, f"{screen.jsp} has no emitted route"


def test_the_emitted_guard_tests_named_roles_not_numbers(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    guard = open(os.path.join(root, "apps/bh-intake-ui/src/app/core/role.guard.ts"),
                 encoding="utf-8").read()
    assert "hasRole" in guard
    assert "roleMask" not in guard.split("*/")[-1], (
        "the guard body must not compare a bitmask numerically -- that is the "
        "approximation JSTL was forced into, and it is the permissive side")


def test_the_emitted_client_consumes_the_shared_library(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    worklist = open(os.path.join(
        root, "apps/bh-intake-ui/src/app/features/worklist/worklist.component.ts"),
        encoding="utf-8").read()
    assert "@bh-um-lite/ui" in worklist
    assert "TaskListComponent" in worklist


def test_the_emitted_client_configures_its_service_urls(tmp_path, inventory):
    root = emit_client(str(tmp_path), inventory)
    env = open(os.path.join(root, "apps/bh-intake-ui/src/environments/environment.ts"),
               encoding="utf-8").read()
    # The file WARNS about the donor's hardcoded URL by quoting it, so assert
    # on the code rather than on the explanation.
    code = "\n".join(line for line in env.splitlines()
                     if not line.lstrip().startswith(("//", "*", "/*")))
    assert "localhost" not in code, "a URL is hardcoded in the emitted config"
    assert "import.meta.env" in code or "process.env" in code
