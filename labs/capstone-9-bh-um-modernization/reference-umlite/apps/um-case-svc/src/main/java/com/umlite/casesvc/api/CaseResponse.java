package com.umlite.casesvc.api;

import com.umlite.casesvc.domain.CaseStatus;
import com.umlite.casesvc.domain.PriorAuthCase;
import java.time.Instant;

/** What we return to clients. Maps the entity to a stable wire shape. */
public record CaseResponse(
        String caseId,
        String memberId,
        String providerId,
        String procedureCode,
        String diagnosisCode,
        int requestedUnits,
        CaseStatus status,
        Instant createdAt,
        Instant updatedAt
) {
    public static CaseResponse from(PriorAuthCase c) {
        return new CaseResponse(
                c.getId().toString(), c.getMemberId(), c.getProviderId(),
                c.getProcedureCode(), c.getDiagnosisCode(), c.getRequestedUnits(),
                c.getStatus(), c.getCreatedAt(), c.getUpdatedAt());
    }
}
