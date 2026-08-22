import { Component, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import type { PriorAuthRequest } from '@um-lite/domain';

/**
 * Shared UI library (M22). A reusable Case Create form — the Prior Auth submission, extracted from
 * intake-ui so the Worklist MFE and the Intake MFE share one accessible form. Emits the typed request;
 * the host wires it to the intake service.
 */
@Component({
  selector: 'um-case-create',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form class="form" (submit)="emit($event)">
      @for (f of fields; track f.key) {
        <label class="field">
          <span class="lbl">{{ f.label }}</span>
          <input [name]="f.key" [(ngModel)]="model[f.key]" [attr.inputmode]="f.numeric ? 'numeric' : null" />
        </label>
      }
      <button type="submit">Submit prior auth</button>
    </form>
  `,
  styles: [`
    .form { display: grid; gap: var(--um-space-3); font-family: var(--um-font);
      background: var(--um-card); border: 1px solid var(--um-line);
      border-radius: var(--um-radius); padding: var(--um-space-6); }
    .field { display: grid; gap: var(--um-space-1); }
    .lbl { color: var(--um-muted); font-size: .85rem; }
    input { padding: var(--um-space-2) var(--um-space-3); color: var(--um-ink);
      background: var(--um-surface); border: 1px solid var(--um-line); border-radius: var(--um-radius); }
    input:focus-visible { outline: var(--um-focus); outline-offset: var(--um-focus-offset); }
    button { margin-top: var(--um-space-2); padding: var(--um-space-3) var(--um-space-4); cursor: pointer;
      color: #06121f; background: var(--um-accent); border: 0; border-radius: var(--um-radius); font-weight: 600; }
    button:focus-visible { outline: var(--um-focus); outline-offset: var(--um-focus-offset); }
  `],
})
export class CaseCreateComponent {
  /** Emitted with the typed Prior Auth request on submit. */
  readonly submitted = output<PriorAuthRequest>();

  readonly fields = [
    { key: 'memberId', label: 'Member ID', numeric: false },
    { key: 'providerId', label: 'Provider ID', numeric: false },
    { key: 'procedureCode', label: 'Procedure code (CPT)', numeric: false },
    { key: 'diagnosisCode', label: 'Diagnosis code (ICD-10)', numeric: false },
    { key: 'requestedUnits', label: 'Requested units', numeric: true },
  ] as const;

  model: Record<string, string> = {
    memberId: 'M1001', providerId: 'P2002',
    procedureCode: '27447', diagnosisCode: 'M17.11', requestedUnits: '1',
  };

  emit(e: Event): void {
    e.preventDefault();
    this.submitted.emit({
      memberId: this.model['memberId'],
      providerId: this.model['providerId'],
      procedureCode: this.model['procedureCode'],
      diagnosisCode: this.model['diagnosisCode'],
      requestedUnits: Number(this.model['requestedUnits']),
    });
  }
}
