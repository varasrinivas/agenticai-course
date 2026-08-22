package com.umlite.casesvc.events;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/** Payload of pa.submitted — mirrors PaSubmittedPayload in @um-lite/events. */
@JsonIgnoreProperties(ignoreUnknown = true)
public record PaSubmittedPayload(
        String caseId,
        String memberId,
        String providerId,
        String procedureCode,
        String diagnosisCode,
        int requestedUnits
) { }
