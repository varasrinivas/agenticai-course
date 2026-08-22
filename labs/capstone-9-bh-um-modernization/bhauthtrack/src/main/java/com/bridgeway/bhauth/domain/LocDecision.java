package com.bridgeway.bhauth.domain;

/**
 * The result of a level-of-care evaluation.
 *
 * <p>Mirrors the {@code PKG_LOC_RULES.t_decision} PL/SQL record, field for field, by hand. There
 * is no code generation and nothing checks that the two stay aligned. When a field was added to
 * the record in 2015 this class was updated three weeks later, and for those three weeks the
 * value silently came back as the default.</p>
 *
 * <p>{@code rulePath} is the breadcrumb of branches the ladder took — {@code
 * "B2:cssrs=3(+3);B3:d1=3(+4);B5:d5|d6>=3(+2);B7a:score>=10&d1>=3=>3.7;"}. It is the closest
 * thing this system has to a decision rationale, it is displayed to reviewers, and it is not
 * persisted anywhere. <b>Anyone building a decision audit needs this string and will find it is
 * thrown away after the page renders.</b></p>
 */
public class LocDecision {

    private String outcome;        // APPROVED | PENDED | DENIED
    private String grantedLoc;     // ASAM level actually granted -- may differ from requested
    private int    grantedUnits;
    private int    intervalDays;   // continued-stay cadence for grantedLoc
    private String reasonCode;
    private String rulePath;

    public String getOutcome() { return outcome; }
    public void setOutcome(String outcome) { this.outcome = outcome; }

    public String getGrantedLoc() { return grantedLoc; }
    public void setGrantedLoc(String grantedLoc) { this.grantedLoc = grantedLoc; }

    public int getGrantedUnits() { return grantedUnits; }
    public void setGrantedUnits(int grantedUnits) { this.grantedUnits = grantedUnits; }

    public int getIntervalDays() { return intervalDays; }
    public void setIntervalDays(int intervalDays) { this.intervalDays = intervalDays; }

    public String getReasonCode() { return reasonCode; }
    public void setReasonCode(String reasonCode) { this.reasonCode = reasonCode; }

    public String getRulePath() { return rulePath; }
    public void setRulePath(String rulePath) { this.rulePath = rulePath; }

    @Override
    public String toString() {
        return "LocDecision[" + outcome + " loc=" + grantedLoc + " units=" + grantedUnits
                + " interval=" + intervalDays + " reason=" + reasonCode
                + " path=" + rulePath + "]";
    }
}
