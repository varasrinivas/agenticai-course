import { Component, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

/**
 * Shared UI library (M22). A reusable Case Search box. Emits a `search` event with the query so the
 * host MFE decides how to fetch — the component owns the input + a11y, not the data source.
 */
@Component({
  selector: 'um-case-search',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form class="search" role="search" (submit)="emit($event)">
      <label class="sr-only" for="um-case-q">Search cases</label>
      <input id="um-case-q" name="q" type="search" [(ngModel)]="q"
             placeholder="Search by member, case id, procedure…" autocomplete="off" />
      <button type="submit">Search</button>
    </form>
  `,
  styles: [`
    .search { display: flex; gap: var(--um-space-2); font-family: var(--um-font); }
    input { flex: 1; padding: var(--um-space-2) var(--um-space-3); color: var(--um-ink);
      background: var(--um-card); border: 1px solid var(--um-line); border-radius: var(--um-radius); }
    input:focus-visible { outline: var(--um-focus); outline-offset: var(--um-focus-offset); }
    button { padding: var(--um-space-2) var(--um-space-4); cursor: pointer; color: #06121f;
      background: var(--um-accent); border: 0; border-radius: var(--um-radius); font-weight: 600; }
    button:focus-visible { outline: var(--um-focus); outline-offset: var(--um-focus-offset); }
    .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  `],
})
export class CaseSearchComponent {
  /** Emitted on submit with the trimmed query (signal output). */
  readonly search = output<string>();
  q = signal('');

  emit(e: Event): void {
    e.preventDefault();
    this.search.emit(this.q().trim());
  }
}
