"""Emit the routed, role-guarded client from the screen inventory.

The reference platform contributes almost nothing here: one unrouted form,
`@angular/router` declared as a dependency and never wired, and three shared
components exported and never imported. So most of this is written from the
framework's conventions rather than copied -- and the temptation to copy the
one thing that does exist is the risk.

Two refusals carry the phase:

  1. **A rule may not be relocated into a template.** Moving a JSTL guard to
     `*ngIf` has moved nothing; it is the same rule in the same layer with a
     different spelling. `preflight` rejects it.

  2. **A guard is not the enforcement.** A route guard stops a reviewer
     reaching a screen they cannot act on, which is a real improvement to the
     experience. Anyone can still call the API directly. Every rule that gates
     an ACTION needs a server-side check as well, and where phase 9A did not
     emit one, this module says so rather than assuming the guard covers it.
"""

from __future__ import annotations

import re

from screen_inventory import (API_OMISSION, COMPUTED_FIELD, DECISION_INPUT,
                              REJECTED_HOMES, ROUTE_GUARD, SERVICE_CHECK,
                              WORKFLOW_GROUP, ScreenInventory)


class RouteEmitError(RuntimeError):
    """The client would lose a rule, or re-implement it where it was found."""


#: Legacy role bitmask -> named role. The new client tests names, never
#: numbers: `roleMask >= 4` is an approximation JSTL was forced into because it
#: has no bitwise operator, and it is the PERMISSIVE side of the divergence --
#: a user with intake+admin (33) passes it and fails the real test.
ROLE_NAMES = {
    1: "bh-intake",
    2: "bh-nurse",
    4: "bh-physician",
    8: "bh-psychiatric-reviewer",
    16: "bh-addiction-medicine-reviewer",
    32: "bh-admin",
}


def preflight(inventory: ScreenInventory, *,
              server_side_checks: set[str] | None = None) -> list[str]:
    """Everything that would make this client wrong. Empty means ready."""
    problems: list[str] = []
    server_side_checks = server_side_checks or set()

    if not inventory.screens:
        problems.append("the inventory is empty -- there is nothing to emit")

    for screen in inventory.screens:
        if not screen.route:
            problems.append(f"{screen.jsp} has no route")
        if not screen.route.startswith("/"):
            problems.append(f"{screen.jsp}: route {screen.route!r} is not absolute")

    for route in inventory.unreachable():
        problems.append(
            f"{route} is defined but nothing links to it. A route nothing "
            f"reaches is a screen that has disappeared -- silently, because the "
            f"code is there and a file count passes.")

    for jsp, rule in [(s.jsp, r) for s in inventory.screens for r in s.rules]:
        home = rule.proposed_home.strip().lower()
        if home in REJECTED_HOMES:
            problems.append(
                f"{jsp}: {rule.rule!r} is proposed for {rule.proposed_home!r}, "
                f"which is where it was found.")

        # A guard improves the experience. It is not a control.
        if rule.proposed_home == ROUTE_GUARD and rule.kind == "role-gate-action":
            problems.append(
                f"{jsp}: {rule.rule!r} gates an ACTION and is proposed for a "
                f"route guard alone. Anyone can call the API directly; this "
                f"needs a server-side check too.")

        if rule.proposed_home == SERVICE_CHECK and rule.unenforced:
            if rule.rule not in server_side_checks:
                problems.append(
                    f"{jsp}: {rule.rule!r} has no server-side enforcement today "
                    f"and phase 9A did not emit one. The client cannot supply "
                    f"it -- report this rather than guarding around it.")

    return problems


def render_routes(inventory: ScreenInventory) -> str:
    """`app.routes.ts`. Real routes, because the donor has none to copy."""
    lines = [
        "import { Routes } from '@angular/router';",
        "import { roleGuard } from './core/role.guard';",
        "",
        "// Routes for every screen in the legacy inventory.",
        "//",
        "// The reference platform provides only provideHttpClient() and has no",
        "// router wired at all, so there is no shape to copy here -- this comes",
        "// from the framework's conventions and from the legacy navigation graph.",
        "//",
        "// A GUARD IS NOT THE ENFORCEMENT. It stops a reviewer reaching a screen",
        "// they cannot act on, which is worth having. The server-side check is",
        "// what makes the rule true.",
        "",
        "export const routes: Routes = [",
    ]
    for screen in inventory.screens:
        lines.append(f"  // {screen.jsp}")
        if screen.note:
            for chunk in _wrap(screen.note, 74):
                lines.append(f"  // {chunk}")
        path = screen.route.lstrip("/")
        component = _component_name(screen.jsp)
        lines.append(f"  {{")
        lines.append(f"    path: '{path}',")
        lines.append(f"    loadComponent: () => import('./features/{_slug(screen.jsp)}"
                     f"/{_slug(screen.jsp)}.component')")
        lines.append(f"      .then(m => m.{component}),")
        if screen.required_roles:
            roles = ", ".join(f"'{r}'" for r in screen.required_roles)
            lines.append(f"    canActivate: [roleGuard],")
            lines.append(f"    data: {{ roles: [{roles}] }},")
        lines.append(f"  }},")
    lines.append("  { path: '', redirectTo: 'worklist', pathMatch: 'full' },")
    lines.append("];")
    return "\n".join(lines) + "\n"


def render_guard() -> str:
    """The role guard. Named roles, never a numeric comparison."""
    return """\
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SessionService } from './session.service';

/**
 * Route guard.
 *
 * NOTE WHAT THIS DOES NOT DO: it does not compare a number.
 *
 * The legacy views test `${sessionScope.roleMask ge 4}` because JSTL has no
 * bitwise operator, so a numeric comparison stands in for the real test. The
 * two agree for the common masks and diverge for combinations -- a user with
 * intake + admin (mask 33) passes `ge 4` and fails `hasRole(MD)`, so the view
 * offers a deny button the service then refuses.
 *
 * This tests named roles from the token, for what they are.
 *
 * AND IT IS NOT THE ENFORCEMENT. Anyone can call the API directly. Every
 * action this guard hides is also checked server-side; the guard is there so
 * the UI does not offer work a reviewer cannot do.
 */
export const roleGuard: CanActivateFn = (route) => {
  const session = inject(SessionService);
  const router = inject(Router);

  const required: string[] = route.data?.['roles'] ?? [];
  if (required.length === 0) {
    return true;
  }
  if (required.some(role => session.hasRole(role))) {
    return true;
  }
  return router.createUrlTree(['/worklist']);
};
"""


def render_environment() -> str:
    """No hardcoded URLs. The donor hardcodes http://localhost:3000."""
    return """\
export const environment = {
  production: false,
  // Configured, not hardcoded. The reference platform embeds
  // 'http://localhost:3000/prior-auth' in a component, which makes the client
  // unshippable to any environment but a laptop.
  intakeApiBase: import.meta.env?.['NG_APP_INTAKE_API'] ?? '/api/intake',
  caseApiBase: import.meta.env?.['NG_APP_CASE_API'] ?? '/api/case',
};
"""


def render_worklist_component(inventory: ScreenInventory) -> str:
    """The worklist, consuming the shared component rather than orphaning it.

    The reference platform exports TaskListComponent, CaseSearchComponent and
    CaseCreateComponent and imports none of them. Reproducing three orphans
    plus three bespoke replacements is how a shared library dies.
    """
    return """\
import { Component, inject, signal } from '@angular/core';
import { TaskListComponent } from '@bh-um-lite/ui';
import { WorklistService } from './worklist.service';
import { WorklistItem } from '@bh-um-lite/domain';

/**
 * The worklist. The application's home screen and its work-distribution
 * mechanism -- the legacy system has no task engine, and neither does the
 * reference platform.
 *
 * TaskListComponent comes from libs/ui, EXTENDED rather than forked: a
 * behavioral-health row carries a continued-stay sequence, a Part 2 marker and
 * an overdue state that a generic task list has no concept of.
 *
 * `overdue` is a FIELD ON THE RESPONSE, not a class the client derives. A
 * review past its deadline is a compliance state, so it is sorted and filtered
 * server-side; the legacy system computed it twice, in SQL and in a JSP
 * scriptlet, with different rounding.
 */
@Component({
  selector: 'bh-worklist',
  standalone: true,
  imports: [TaskListComponent],
  template: `
    <bh-task-list
      [items]="items()"
      [columns]="columns"
      (open)="open($event)">
    </bh-task-list>
  `,
})
export class WorklistComponent {
  private readonly service = inject(WorklistService);
  readonly items = signal<WorklistItem[]>([]);

  readonly columns = [
    { key: 'authId', label: 'Auth' },
    { key: 'memberLastName', label: 'Member' },
    { key: 'diagnosisCode', label: 'Dx' },
    { key: 'requestedLoc', label: 'Requested' },
    { key: 'currentLoc', label: 'Current' },
    { key: 'status', label: 'Status' },
    { key: 'daysUntilDue', label: 'Review due' },
  ];

  constructor() {
    // The server decides what is on this reviewer's list. The legacy system
    // filtered in SQL and again in the template, by two rules that did not
    // agree -- so "what work is mine?" had two answers depending on which
    // layer you asked.
    this.service.forCurrentReviewer().subscribe(items => this.items.set(items));
  }

  open(item: WorklistItem): void {
    // Continued stay routes to the review screen; an initial determination
    // routes to the decision screen. The distinction is reviewSeq > 1.
    const path = item.reviewSeq > 1
      ? ['/auth', item.authId, 'review']
      : ['/auth', item.authId, 'decide'];
    this.router.navigate(path);
  }
}
"""


def render_decision_component() -> str:
    """The determination screen -- where three legacy rules lived in JSTL."""
    return """\
import { Component, inject, input } from '@angular/core';
import { CaseService } from './case.service';
import { SessionService } from '../../core/session.service';

/**
 * The determination screen.
 *
 * THREE RULES USED TO LIVE IN THIS TEMPLATE. None of them is here now:
 *
 *  1. "Only a physician may deny; substance-use needs an addiction-medicine
 *     reviewer" -- now a server-side check in the case service AND a BPMN
 *     candidate group. `canDeny` below only decides whether to OFFER the
 *     action; the server decides whether it happens.
 *
 *  2. "Intake coordinators must not read the clinical narrative" -- now an
 *     API omission. The endpoint does not return the field to a caller
 *     without the clinical scope, so there is nothing here to hide. The
 *     legacy screen loaded it unconditionally and hid it with a conditional,
 *     which put the content in the response body either way.
 *
 *  3. The two clocks -- continued-stay countdown and regulatory turnaround --
 *     used to be computed in scriptlets in this file and NOWHERE ELSE in the
 *     codebase. They are now computed fields on the response, so reporting
 *     and the screen agree by construction rather than by coincidence.
 */
@Component({
  selector: 'bh-decision',
  standalone: true,
  template: `
    @if (case().part2Program) {
      <div class="part2-banner" role="note">
        <strong>42 CFR Part 2 &mdash; protected record.</strong>
        Redisclosure prohibited except as permitted by a consent naming the
        recipient. Consent on file: {{ case().consentScope }}.
      </div>
    }

    <!-- Computed server-side. Not derived here; see the class comment. -->
    <dl class="clocks">
      <dt>Next continued-stay review</dt>
      <dd [class.overdue]="case().reviewOverdue">{{ case().reviewDueLabel }}</dd>
      <dt>Regulatory turnaround</dt>
      <dd [class.overdue]="case().turnaroundBreached">{{ case().turnaroundLabel }}</dd>
    </dl>

    <!-- The narrative is absent from the response unless the caller is
         entitled to it, so there is no conditional here at all. -->
    @if (case().clinicalNarrative) {
      <pre class="narrative">{{ case().clinicalNarrative }}</pre>
    }

    <button type="button" (click)="approve()">Approve</button>
    <button type="button" (click)="pend()">Pend for additional clinical</button>

    @if (canDeny()) {
      <button type="button" class="btn-deny" (click)="deny()">
        Deny
      </button>
    } @else {
      <p class="note">
        Adverse determinations require a same-specialty physician reviewer.
      </p>
    }
  `,
})
export class DecisionComponent {
  readonly case = input.required<CaseDetail>();
  private readonly session = inject(SessionService);
  private readonly service = inject(CaseService);

  /**
   * Whether to OFFER the deny action. Not whether it is permitted -- the
   * service re-checks, on every call path, and refuses.
   *
   * Named roles, not a numeric comparison against a bitmask.
   */
  canDeny(): boolean {
    return this.session.hasRole(this.case().requiredReviewerRole);
  }

  deny(): void {
    this.service.deny(this.case().authId).subscribe();
  }

  approve(): void {
    this.service.approve(this.case().authId).subscribe();
  }

  pend(): void {
    this.service.pend(this.case().authId).subscribe();
  }
}
"""


def emit(inventory: ScreenInventory, write, *,
         server_side_checks: set[str] | None = None) -> list[str]:
    """Write the client. `write(relative_path, content)` does the writing.

    Returns the paths written. Raises rather than emitting a client that has
    lost a rule.
    """
    problems = preflight(inventory, server_side_checks=server_side_checks)
    if problems:
        raise RouteEmitError(
            "refusing to emit the client:\n  - " + "\n  - ".join(problems))

    base = "apps/bh-intake-ui/src/app"
    written = []
    for rel, content in (
        (f"{base}/app.routes.ts", render_routes(inventory)),
        (f"{base}/core/role.guard.ts", render_guard()),
        (f"{base}/../environments/environment.ts", render_environment()),
        (f"{base}/features/worklist/worklist.component.ts",
         render_worklist_component(inventory)),
        (f"{base}/features/decision/decision.component.ts",
         render_decision_component()),
    ):
        write(rel, content)
        written.append(rel)
    return written


# ---------------------------------------------------------------------------


def _slug(jsp: str) -> str:
    stem = jsp.rsplit("/", 1)[-1].removesuffix(".jsp")
    return re.sub(r"(?<!^)(?=[A-Z])", "-", stem).lower()


def _component_name(jsp: str) -> str:
    stem = jsp.rsplit("/", 1)[-1].removesuffix(".jsp")
    return stem[0].upper() + stem[1:] + "Component"


def _wrap(text: str, width: int) -> list[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out
