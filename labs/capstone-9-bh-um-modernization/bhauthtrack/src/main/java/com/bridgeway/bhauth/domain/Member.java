package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * A member. Maps onto BH_MEMBER.
 *
 * <p><b>Two identifiers, and they are not interchangeable.</b></p>
 *
 * <ul>
 *   <li>{@code memberId} is <b>Bridgeway's</b> identifier. Bridgeway was the carve-out vendor;
 *       this is its own key, minted by its own enrolment process, and it is the primary key of
 *       every table in this system.</li>
 *   <li>{@code planMemberId} is the <b>health plan's</b> identifier. It is nullable, because the
 *       eligibility feed did not carry it until the 2014 rewrite. As of the last extract, 31% of
 *       members created before July 2014 still have it null.</li>
 * </ul>
 *
 * <p>Anything that crosses the boundary to the health plan must key on {@code planMemberId}.
 * Several reports join on {@code memberId} instead and have been quietly wrong since 2012. The
 * two formats overlap enough that a wrong join returns rows rather than erroring, which is why
 * nobody noticed.</p>
 *
 * @see <a href="file:../../../../../../db/schema_changes.txt">schema_changes.txt, BHA-1180</a>
 */
public class Member {

    private String memberId;
    private String planMemberId;
    private String lastName;
    private String firstName;
    private Date   dob;
    private String lineOfBusiness;     // COMMERCIAL | MEDICARE_ADV | MANAGED_MEDICAID
    private Date   eligibilityStart;
    private Date   eligibilityEnd;

    /**
     * True when this member cannot be resolved to the health plan at all.
     *
     * <p>Used by exactly one screen ({@code search.jsp}) to show a warning triangle. Nothing
     * blocks on it. An authorization for an unresolvable member processes normally and simply
     * cannot be reconciled downstream.</p>
     */
    public boolean isUnresolvedToPlan() {
        return planMemberId == null || planMemberId.trim().isEmpty();
    }

    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }

    public String getPlanMemberId() { return planMemberId; }
    public void setPlanMemberId(String planMemberId) { this.planMemberId = planMemberId; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public Date getDob() { return dob; }
    public void setDob(Date dob) { this.dob = dob; }

    public String getLineOfBusiness() { return lineOfBusiness; }
    public void setLineOfBusiness(String lineOfBusiness) { this.lineOfBusiness = lineOfBusiness; }

    public Date getEligibilityStart() { return eligibilityStart; }
    public void setEligibilityStart(Date d) { this.eligibilityStart = d; }

    public Date getEligibilityEnd() { return eligibilityEnd; }
    public void setEligibilityEnd(Date d) { this.eligibilityEnd = d; }
}
