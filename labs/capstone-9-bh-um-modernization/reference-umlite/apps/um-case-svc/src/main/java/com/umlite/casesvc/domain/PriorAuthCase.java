package com.umlite.casesvc.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/** The Prior Auth case aggregate. Owned by this service, persisted to Postgres. */
@Entity
@Table(name = "prior_auth_case")
public class PriorAuthCase {

    // Application-assigned id: the REST path generates one; the event path carries the
    // caseId assigned upstream by intake (= the event correlationId). No @GeneratedValue.
    @Id
    private UUID id;

    @Column(nullable = false) private String memberId;
    @Column(nullable = false) private String providerId;
    @Column(nullable = false) private String procedureCode;
    @Column(nullable = false) private String diagnosisCode;
    @Column(nullable = false) private int requestedUnits;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CaseStatus status;

    @Column(nullable = false) private Instant createdAt;
    @Column(nullable = false) private Instant updatedAt;

    protected PriorAuthCase() { } // for JPA

    /** REST path (Phase 1): the service assigns a fresh id. */
    public PriorAuthCase(String memberId, String providerId, String procedureCode,
                         String diagnosisCode, int requestedUnits) {
        this(UUID.randomUUID(), memberId, providerId, procedureCode, diagnosisCode, requestedUnits);
    }

    /** Event path (Phase 2): the caseId is assigned upstream by intake (= correlationId). */
    public PriorAuthCase(UUID id, String memberId, String providerId, String procedureCode,
                         String diagnosisCode, int requestedUnits) {
        this.id = id;
        this.memberId = memberId;
        this.providerId = providerId;
        this.procedureCode = procedureCode;
        this.diagnosisCode = diagnosisCode;
        this.requestedUnits = requestedUnits;
        this.status = CaseStatus.SUBMITTED;
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    public UUID getId() { return id; }
    public String getMemberId() { return memberId; }
    public String getProviderId() { return providerId; }
    public String getProcedureCode() { return procedureCode; }
    public String getDiagnosisCode() { return diagnosisCode; }
    public int getRequestedUnits() { return requestedUnits; }
    public CaseStatus getStatus() { return status; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }

    public void transitionTo(CaseStatus next) {
        this.status = next;
        this.updatedAt = Instant.now();
    }
}
