package com.umlite.casesvc.api;

import jakarta.validation.constraints.*;

/** Inbound payload from the intake service. DTO, deliberately separate from the entity. */
public record CreateCaseRequest(
        @NotBlank String memberId,
        @NotBlank String providerId,
        @NotBlank String procedureCode,
        @NotBlank String diagnosisCode,
        @Min(1) int requestedUnits,
        String notes
) { }
