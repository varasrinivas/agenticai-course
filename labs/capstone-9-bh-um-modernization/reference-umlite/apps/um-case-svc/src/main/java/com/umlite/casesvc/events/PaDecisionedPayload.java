package com.umlite.casesvc.events;

/** Payload of pa.decisioned — mirrors PaDecisionedPayload in @um-lite/events. */
public record PaDecisionedPayload(
        String caseId,
        String decision,    // APPROVED | DENIED | PENDED
        String decidedBy,
        String rationale
) { }
