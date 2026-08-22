/**
 * Shared Utilization Management domain types.
 * These cross the wire between the Angular UI, the NestJS intake service,
 * and (in mirrored Java form) the Spring case service. Keep them small and stable.
 */

/** What a provider submits to request prior authorization for a procedure. */
export interface PriorAuthRequest {
  memberId: string;
  providerId: string;
  /** CPT/HCPCS procedure code, e.g. "27447" (total knee replacement). */
  procedureCode: string;
  /** ICD-10 diagnosis code, e.g. "M17.11". */
  diagnosisCode: string;
  requestedUnits: number;
  notes?: string;
}

/** Lifecycle of a Prior Auth case. */
export enum CaseStatus {
  SUBMITTED = 'SUBMITTED',
  IN_REVIEW = 'IN_REVIEW',
  APPROVED = 'APPROVED',
  DENIED = 'DENIED',
  PENDED = 'PENDED',
}

/** What the case service returns once a case exists. */
export interface PriorAuthCase {
  caseId: string;
  memberId: string;
  providerId: string;
  procedureCode: string;
  diagnosisCode: string;
  requestedUnits: number;
  status: CaseStatus;
  createdAt: string; // ISO-8601
  updatedAt: string; // ISO-8601
}
