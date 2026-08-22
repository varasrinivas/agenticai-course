package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * A 42 CFR Part 2 consent. Maps onto BH_CONSENT.
 *
 * <p>This is not a HIPAA authorization and the difference matters to anyone porting it. A HIPAA
 * disclosure for treatment, payment or operations does not require the patient's signature and
 * is bounded by "minimum necessary". A Part 2 consent has neither property:</p>
 *
 * <ul>
 *   <li>It <b>names the recipient</b>. Disclosing to a party this record does not name is the
 *       violation, however legitimate that party's interest.</li>
 *   <li>It <b>states a purpose</b> and a <b>scope</b>. {@code AUTH_DECISION_ONLY} means the
 *       determination may be disclosed and the narrative may not.</li>
 *   <li>It <b>expires</b>, and it can be <b>revoked</b>.</li>
 *   <li>The disclosure must carry a <b>redisclosure notice</b> — the recipient is bound too.</li>
 * </ul>
 *
 * <p>There is nothing in the modern platform that corresponds to any of this.</p>
 */
public class Consent {

    private long   consentId;
    private long   authId;
    private String memberId;
    private String recipientName;
    private String recipientType;             // HEALTH_PLAN | PROVIDER | FAMILY | LEGAL | OTHER
    private String purpose;
    private String scope;                     // FULL_RECORD | AUTH_DECISION_ONLY | DATES_OF_SERVICE_ONLY
    private Date   signedTs;
    private Date   expiresTs;
    private Date   revokedTs;
    private String redisclosureNoticeSent;    // 'Y' | 'N'

    /**
     * Whether this consent actually permits a disclosure right now.
     *
     * <p>Callers: {@code ConsentController} and {@code consentAdmin.jsp}. NOT called from
     * {@link com.bridgeway.bhauth.service.AuthCaseService} — the submit path captures consent
     * but never checks it, because in 2011 the assumption was that a request arriving from a
     * Part 2 program came with consent attached on paper. That assumption is the gap.</p>
     */
    public boolean isUsable(Date asOf) {
        if (revokedTs != null && !revokedTs.after(asOf)) return false;
        if (expiresTs == null || !expiresTs.after(asOf)) return false;
        return signedTs != null && !signedTs.after(asOf);
    }

    /** True when the narrative itself may leave this system under this consent. */
    public boolean permitsNarrative() {
        return "FULL_RECORD".equals(scope);
    }

    public long getConsentId() { return consentId; }
    public void setConsentId(long consentId) { this.consentId = consentId; }

    public long getAuthId() { return authId; }
    public void setAuthId(long authId) { this.authId = authId; }

    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }

    public String getRecipientName() { return recipientName; }
    public void setRecipientName(String recipientName) { this.recipientName = recipientName; }

    public String getRecipientType() { return recipientType; }
    public void setRecipientType(String recipientType) { this.recipientType = recipientType; }

    public String getPurpose() { return purpose; }
    public void setPurpose(String purpose) { this.purpose = purpose; }

    public String getScope() { return scope; }
    public void setScope(String scope) { this.scope = scope; }

    public Date getSignedTs() { return signedTs; }
    public void setSignedTs(Date signedTs) { this.signedTs = signedTs; }

    public Date getExpiresTs() { return expiresTs; }
    public void setExpiresTs(Date expiresTs) { this.expiresTs = expiresTs; }

    public Date getRevokedTs() { return revokedTs; }
    public void setRevokedTs(Date revokedTs) { this.revokedTs = revokedTs; }

    public String getRedisclosureNoticeSent() { return redisclosureNoticeSent; }
    public void setRedisclosureNoticeSent(String v) { this.redisclosureNoticeSent = v; }
}
