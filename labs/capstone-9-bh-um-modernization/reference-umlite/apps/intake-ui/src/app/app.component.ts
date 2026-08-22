import { Component } from '@angular/core';
import { PriorAuthFormComponent } from './prior-auth-form/prior-auth-form.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [PriorAuthFormComponent],
  template: `
    <main style="max-width: 640px; margin: 48px auto; padding: 0 16px;">
      <h1 style="margin-bottom: 4px;">UM-Lite · Prior Auth Intake</h1>
      <p style="color: var(--muted); margin-top: 0;">
        Submit a request → it flows through the intake service to the case service.
      </p>
      <app-prior-auth-form></app-prior-auth-form>
    </main>
  `,
})
export class AppComponent {}
