/**
 * Kafka contracts for the Prior Auth slice — mirrors `libs/events/src/lib/pa-events.ts`
 * (`@um-lite/events`). Kept inline in the app so the service stays runnable before the
 * Nx workspace path mapping is wired (same pattern as CreatePriorAuthDto mirroring
 * `@um-lite/domain`). `libs/events` remains the canonical source of truth.
 */

export const Topics = {
  PA_SUBMITTED: 'pa.submitted',
  PA_DECISIONED: 'pa.decisioned',
  PA_DEAD_LETTER: 'pa.dead-letter',
} as const;

export type Topic = (typeof Topics)[keyof typeof Topics];

/** Common envelope so every event is traceable and versioned. */
export interface EventEnvelope<T> {
  eventId: string; // UUID
  eventType: Topic;
  occurredAt: string; // ISO-8601
  correlationId: string; // ties events of one case together (= caseId)
  version: 1;
  payload: T;
}

export interface PaSubmittedPayload {
  caseId: string;
  memberId: string;
  providerId: string;
  procedureCode: string;
  diagnosisCode: string;
  requestedUnits: number;
}

export interface PaDecisionedPayload {
  caseId: string;
  decision: 'APPROVED' | 'DENIED' | 'PENDED';
  decidedBy: string;
  rationale?: string;
}
