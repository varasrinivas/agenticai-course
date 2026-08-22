package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * A behavioral-health prior authorization. Maps 1:1 onto BH_AUTH.
 *
 * <p>There is no DTO layer in BHAuthTrack. This bean is bound straight from the request by
 * Spring's data binder, passed through the service layer, written to the database by the DAO,
 * and rendered by the JSP. One class, four responsibilities. That is normal for its era and it
 * is why field names leak into HTML form names, into SQL, and into eleven Crystal reports.</p>
 *
 * <p><b>{@code clinicalNarrative} is the important field.</b> It is the medical-necessity
 * evidence a reviewer actually reads, and when the requesting provider is a federally assisted
 * SUD program it is also 42 CFR Part 2 protected treatment content. Every path that touches it
 * — the log line in {@link com.bridgeway.bhauth.service.AuthCaseService}, the queue payload, the
 * audit trigger, the narrative block in {@code decision.jsp} — is a disclosure surface.</p>
 */
public class Auth {

    private long   authId;
    private String memberId;            // BRIDGEWAY carve-out id, NOT the plan's -- see BHA-1180
    private String bridgewayProvId;
    private String serviceCode;         // CPT or HCPCS
    private String diagnosisCode;       // ICD-10
    private String requestedLoc;        // ASAM level as a string: '1.0','2.1','2.5','3.1','3.5','3.7','4.0'
    private int    requestedUnits;      // days for residential, sessions for outpatient
    private String clinicalNarrative;
    private String status;
    private String urgency;             // STANDARD | EXPEDITED
    private String legacyOverride;      // 'Y'|'N' -- BHA-2291, undocumented. Do not guess.
    private Date   submittedTs;
    private Date   decidedTs;
    private String decidedBy;
    private String denialReasonCode;

    public long getAuthId() { return authId; }
    public void setAuthId(long authId) { this.authId = authId; }

    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }

    public String getBridgewayProvId() { return bridgewayProvId; }
    public void setBridgewayProvId(String bridgewayProvId) { this.bridgewayProvId = bridgewayProvId; }

    public String getServiceCode() { return serviceCode; }
    public void setServiceCode(String serviceCode) { this.serviceCode = serviceCode; }

    public String getDiagnosisCode() { return diagnosisCode; }
    public void setDiagnosisCode(String diagnosisCode) { this.diagnosisCode = diagnosisCode; }

    public String getRequestedLoc() { return requestedLoc; }
    public void setRequestedLoc(String requestedLoc) { this.requestedLoc = requestedLoc; }

    public int getRequestedUnits() { return requestedUnits; }
    public void setRequestedUnits(int requestedUnits) { this.requestedUnits = requestedUnits; }

    public String getClinicalNarrative() { return clinicalNarrative; }
    public void setClinicalNarrative(String clinicalNarrative) { this.clinicalNarrative = clinicalNarrative; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getUrgency() { return urgency; }
    public void setUrgency(String urgency) { this.urgency = urgency; }

    public String getLegacyOverride() { return legacyOverride; }
    public void setLegacyOverride(String legacyOverride) { this.legacyOverride = legacyOverride; }

    public Date getSubmittedTs() { return submittedTs; }
    public void setSubmittedTs(Date submittedTs) { this.submittedTs = submittedTs; }

    public Date getDecidedTs() { return decidedTs; }
    public void setDecidedTs(Date decidedTs) { this.decidedTs = decidedTs; }

    public String getDecidedBy() { return decidedBy; }
    public void setDecidedBy(String decidedBy) { this.decidedBy = decidedBy; }

    public String getDenialReasonCode() { return denialReasonCode; }
    public void setDenialReasonCode(String denialReasonCode) { this.denialReasonCode = denialReasonCode; }

    /**
     * NOTE: this deliberately does not include the narrative. Somebody added it in 2013, a
     * support engineer pasted an object dump into a ticket, and it had to be scrubbed from the
     * ticketing system. Leave it out.
     */
    @Override
    public String toString() {
        return "Auth[" + authId + " member=" + memberId + " svc=" + serviceCode
                + " dx=" + diagnosisCode + " reqLoc=" + requestedLoc
                + " status=" + status + "]";
    }
}
