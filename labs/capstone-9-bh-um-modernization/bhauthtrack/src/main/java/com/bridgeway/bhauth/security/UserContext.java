package com.bridgeway.bhauth.security;

import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.SessionScope;

/**
 * The current user's identity and permissions.
 *
 * <p><b>This is the entire authorization model of BHAuthTrack.</b> There is no Spring Security,
 * no {@code @PreAuthorize}, no filter chain beyond {@link AuthFilter}, and no notion of a scope
 * or a permission. There is a session-scoped bean holding an integer, and every access decision
 * in the system is a bitwise test against it — written wherever the developer happened to need
 * it, in services, in controllers, and in JSTL.</p>
 *
 * <h3>The bitmask</h3>
 * <pre>
 *    1  BH_INTAKE        create and edit an authorization. NON-CLINICAL.
 *    2  BH_NURSE         review and APPROVE. May never deny.
 *    4  BH_MD            issue an adverse determination.
 *    8  BH_MD_PSYCH      psychiatric peer reviewer.
 *   16  BH_MD_ADDICTION  addiction-medicine peer reviewer.
 *   32  BH_ADMIN         user and consent administration.
 * </pre>
 *
 * <h3>Why the nurse/physician split exists</h3>
 *
 * <p>It is not a convenience. A nurse reviewer may approve a request but may never issue an
 * adverse determination — that is a separation of duties required by accreditation, and it is
 * why the {@code PENDED} status exists at all: it is the state a case sits in while it waits for
 * someone licensed to deny it. For substance-use and psychiatric level-of-care determinations
 * the reviewer is further expected to be same-specialty, which is why bits 8 and 16 exist
 * separately from bit 4.</p>
 *
 * <h3>The part that will hurt during a port</h3>
 *
 * <p>Note {@link #hasRole(int)}: it is a real bitwise test. Note now what {@code decision.jsp}
 * does — {@code <c:if test="${sessionScope.roleMask ge 4}">} — because JSTL has no bitwise
 * operator, so the view approximates the same rule with a <em>numeric comparison</em>. Those two
 * are not equivalent. A user with mask 3 (intake + nurse) fails {@code hasRole(4)} and also
 * fails {@code ge 4}, so the common cases agree. A user with mask 3 who is granted admin —
 * mask 35 — passes {@code ge 4} in the view and fails {@code hasRole(ROLE_MD)} in the service.
 * The view shows them a deny button that the service then refuses.</p>
 *
 * <p>Nobody has hit this in production because admins are not given clinical roles. It is still
 * two different implementations of one rule, which is the actual finding.</p>
 */
@Component
@SessionScope
public class UserContext {

    public static final int ROLE_INTAKE       = 1;
    public static final int ROLE_NURSE        = 2;
    public static final int ROLE_MD           = 4;
    public static final int ROLE_MD_PSYCH     = 8;
    public static final int ROLE_MD_ADDICTION = 16;
    public static final int ROLE_ADMIN        = 32;

    private String userId;
    private int    roleMask;
    private String credential;   // RN | LCSW | MD | MD_PSYCH | MD_ADDICTION -- from LDAP title
    private String ldapDn;

    /** The real test. Bitwise AND, as the mask intends. */
    public boolean hasRole(int role) {
        return (roleMask & role) == role;
    }

    /**
     * Whether this user may issue an adverse determination on the given diagnosis.
     *
     * <p>Added in 2014 after an incident. It is called from
     * {@code AuthCaseService.issueDenial()} and from {@code AuthController}, but NOT from the
     * batch importer or the SOAP endpoint, both of which reach the decision path by other
     * routes. Two of four call paths enforce this.</p>
     */
    public boolean mayDeny(String icd10) {
        if (!hasRole(ROLE_MD)) return false;
        if (icd10 == null) return true;
        if (isSubstanceUse(icd10)) return hasRole(ROLE_MD_ADDICTION);
        if (isPsychiatric(icd10))  return hasRole(ROLE_MD_PSYCH);
        return true;
    }

    /** F10–F19: mental and behavioural disorders due to psychoactive substance use. */
    private boolean isSubstanceUse(String icd10) {
        return icd10.length() >= 3 && icd10.charAt(0) == 'F'
                && icd10.compareTo("F10") >= 0 && icd10.compareTo("F20") < 0;
    }

    /** F20–F49: schizophrenia, mood, and anxiety disorders. */
    private boolean isPsychiatric(String icd10) {
        return icd10.length() >= 3 && icd10.charAt(0) == 'F'
                && icd10.compareTo("F20") >= 0 && icd10.compareTo("F50") < 0;
    }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public int getRoleMask() { return roleMask; }
    public void setRoleMask(int roleMask) { this.roleMask = roleMask; }

    public String getCredential() { return credential; }
    public void setCredential(String credential) { this.credential = credential; }

    public String getLdapDn() { return ldapDn; }
    public void setLdapDn(String ldapDn) { this.ldapDn = ldapDn; }
}
