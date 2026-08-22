import { Component, input } from '@angular/core';
import { NgClass } from '@angular/common';
import type { PriorAuthCase } from '@um-lite/domain';

/**
 * Shared UI library (Phase 4 / Track 4, M22). A reusable Task List: render Prior Auth cases with a
 * status badge. Standalone + signal input, so any micro-frontend (Worklist, Case Search) can drop it
 * in. Styling references the design tokens (M23) — no hard-coded colors.
 */
@Component({
  selector: 'um-task-list',
  standalone: true,
  imports: [NgClass],
  template: `
    <ul class="list" role="list">
      @for (c of cases(); track c.caseId) {
        <li class="row">
          <span class="id">{{ c.caseId.slice(0, 8) }}</span>
          <span class="member">{{ c.memberId }}</span>
          <span class="proc">{{ c.procedureCode }}</span>
          <span class="badge" [ngClass]="'s-' + c.status.toLowerCase()">{{ c.status }}</span>
        </li>
      } @empty {
        <li class="empty">No cases.</li>
      }
    </ul>
  `,
  styles: [`
    .list { list-style: none; margin: 0; padding: 0; font-family: var(--um-font); }
    .row { display: flex; align-items: center; gap: var(--um-space-3);
      padding: var(--um-space-3) var(--um-space-4); border-bottom: 1px solid var(--um-line); }
    .id { font-family: var(--um-mono); font-size: .82rem; color: var(--um-muted); flex: 0 0 80px; }
    .member, .proc { color: var(--um-ink); }
    .proc { flex: 1; color: var(--um-muted); }
    .badge { font-family: var(--um-mono); font-size: .72rem; padding: 2px 10px;
      border-radius: var(--um-radius-pill); color: #06121f; }
    .s-submitted { background: var(--um-status-submitted); }
    .s-in_review { background: var(--um-status-in-review); }
    .s-approved { background: var(--um-status-approved); }
    .s-denied { background: var(--um-status-denied); color: #fff; }
    .s-pended { background: var(--um-status-pended); }
    .empty { padding: var(--um-space-4); color: var(--um-muted); }
  `],
})
export class TaskListComponent {
  /** Cases to render (signal input — Angular 17.3+). */
  readonly cases = input<PriorAuthCase[]>([]);
}
