import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

/** Minimal form that POSTs a prior auth to the NestJS intake service. */
@Component({
  selector: 'app-prior-auth-form',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div style="background:#fff;border:1px solid var(--line);border-radius:8px;padding:20px;">
      @for (f of fields; track f.key) {
        <label style="display:block;margin-bottom:12px;">
          <span style="display:block;color:var(--muted);font-size:13px;margin-bottom:4px;">{{ f.label }}</span>
          <input [(ngModel)]="model[f.key]" [name]="f.key"
                 style="width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:6px;" />
        </label>
      }
      <button (click)="submit()" [disabled]="busy()"
              style="background:var(--accent);color:#fff;border:0;border-radius:6px;padding:10px 16px;cursor:pointer;">
        {{ busy() ? 'Submitting…' : 'Submit prior auth' }}
      </button>

      @if (result()) {
        <pre style="margin-top:16px;background:#0f1722;color:#cfe3d6;padding:12px;border-radius:6px;overflow:auto;">{{ result() }}</pre>
      }
      @if (error()) {
        <p style="margin-top:16px;color:#b00020;">{{ error() }}</p>
      }
    </div>
  `,
})
export class PriorAuthFormComponent {
  private http = inject(HttpClient);
  private intakeUrl = 'http://localhost:3000/prior-auth';

  fields = [
    { key: 'memberId', label: 'Member ID' },
    { key: 'providerId', label: 'Provider ID' },
    { key: 'procedureCode', label: 'Procedure code (CPT)' },
    { key: 'diagnosisCode', label: 'Diagnosis code (ICD-10)' },
    { key: 'requestedUnits', label: 'Requested units' },
  ] as const;

  model: Record<string, string> = {
    memberId: 'M1001', providerId: 'P2002',
    procedureCode: '27447', diagnosisCode: 'M17.11', requestedUnits: '1',
  };

  busy = signal(false);
  result = signal<string | null>(null);
  error = signal<string | null>(null);

  submit() {
    this.busy.set(true);
    this.result.set(null);
    this.error.set(null);
    const body = { ...this.model, requestedUnits: Number(this.model['requestedUnits']) };
    this.http.post(this.intakeUrl, body).subscribe({
      next: (res) => { this.result.set(JSON.stringify(res, null, 2)); this.busy.set(false); },
      error: (e) => { this.error.set(e?.error?.message ?? 'Request failed — is the intake service running?'); this.busy.set(false); },
    });
  }
}
