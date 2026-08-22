package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * One row of the concurrent-review ladder. Maps onto BH_LOC_REVIEW.
 *
 * <p><b>This class is the shape of behavioral-health utilization management.</b> A medical
 * prior-auth case has one decision. A behavioral-health case has a sequence: {@code reviewSeq}
 * 1 is the initial determination and every row after it is a continued-stay review, each one
 * scheduling the next through {@code nextReviewDue}.</p>
 *
 * <p>{@code nextReviewDue} is a regulatory deadline. A residential authorization that is not
 * re-reviewed inside its interval is out of compliance, and nothing in this system enforces it —
 * the value is written here and a nightly query sorts the worklist on it. If nobody looks at the
 * worklist, nothing happens and nothing complains.</p>
 *
 * <p>{@code reviewerCredential} exists because of a 2015 audit finding (BHA-4102): the system
 * could show <em>who</em> reviewed but not whether they were licensed to issue the determination
 * they issued.</p>
 */
public class LocReview {

    private long   reviewId;
    private long   authId;
    private int    reviewSeq;              // 1 = initial, 2..n = continued stay
    private String reviewedLoc;
    private int    approvedUnits;
    private int    reviewIntervalDays;
    private Date   nextReviewDue;          // null once discharged -- the ladder is closed
    private String outcome;                // APPROVED|PENDED|DENIED|STEPPED_DOWN|DISCHARGED
    private String reviewerUserId;
    private String reviewerCredential;     // RN | LCSW | MD | MD_PSYCH | MD_ADDICTION
    private Date   reviewTs;

    /** True when this review is the initial determination rather than a continued stay. */
    public boolean isInitial() { return reviewSeq == 1; }

    public long getReviewId() { return reviewId; }
    public void setReviewId(long reviewId) { this.reviewId = reviewId; }

    public long getAuthId() { return authId; }
    public void setAuthId(long authId) { this.authId = authId; }

    public int getReviewSeq() { return reviewSeq; }
    public void setReviewSeq(int reviewSeq) { this.reviewSeq = reviewSeq; }

    public String getReviewedLoc() { return reviewedLoc; }
    public void setReviewedLoc(String reviewedLoc) { this.reviewedLoc = reviewedLoc; }

    public int getApprovedUnits() { return approvedUnits; }
    public void setApprovedUnits(int approvedUnits) { this.approvedUnits = approvedUnits; }

    public int getReviewIntervalDays() { return reviewIntervalDays; }
    public void setReviewIntervalDays(int d) { this.reviewIntervalDays = d; }

    public Date getNextReviewDue() { return nextReviewDue; }
    public void setNextReviewDue(Date nextReviewDue) { this.nextReviewDue = nextReviewDue; }

    public String getOutcome() { return outcome; }
    public void setOutcome(String outcome) { this.outcome = outcome; }

    public String getReviewerUserId() { return reviewerUserId; }
    public void setReviewerUserId(String reviewerUserId) { this.reviewerUserId = reviewerUserId; }

    public String getReviewerCredential() { return reviewerCredential; }
    public void setReviewerCredential(String c) { this.reviewerCredential = c; }

    public Date getReviewTs() { return reviewTs; }
    public void setReviewTs(Date reviewTs) { this.reviewTs = reviewTs; }
}
