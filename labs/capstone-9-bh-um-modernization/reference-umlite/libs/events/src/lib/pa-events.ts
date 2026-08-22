/**
 * Kafka contracts for the Prior Auth slice.
 * Phase 2 wires these in; they live here now so producers and consumers
 * share one source of truth (mirrors the EventHub/KaaS branch of the diagram).
 *
 * Event names are past-tense facts. Topics are namespaced by domain.
 */

export const Topics = {
  PA_SUBMITTED: 'pa.submitted',
  PA_DECISIONED: 'pa.decisioned',
  PA_DEAD_LETTER: 'pa.dead-letter',
} as const;

export type Topic = (typeof Topics)[keyof typeof Topics];

/** Common envelope so every event is traceable and versioned. */
export interface EventEnvelope<T> {
  eventId: string;        // UUID
  eventType: Topic;
  occurredAt: string;     // ISO-8601
  correlationId: string;  // ties events of one case together (= caseId)
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
