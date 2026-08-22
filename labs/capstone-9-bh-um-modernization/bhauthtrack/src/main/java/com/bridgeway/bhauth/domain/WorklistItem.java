package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * One row of a reviewer's worklist. Not a table — the projection of a join, assembled by
 * {@code WorklistDao} and rendered by {@code worklist.jsp}.
 *
 * <p>The worklist is how work actually reaches a reviewer in this system. There is no task
 * engine, no assignment, no claim and no queue: a nightly query builds rows, the JSP renders
 * them role-filtered, and whoever opens a row first works it. Two reviewers opening the same row
 * both get the edit screen and the second save wins.</p>
 *
 * <p>{@code daysUntilDue} is derived, not stored, and it is derived twice — once here for
 * sorting and once again in a scriptlet in {@code decision.jsp} for display. The two use
 * different rounding.</p>
 */
public class WorklistItem {

    private long   authId;
    private String memberId;
    private String memberLastName;
    private String requestedLoc;
    private String currentLoc;
    private String status;
    private String urgency;
    private String diagnosisCode;
    private boolean part2Program;
    private Date   submittedTs;
    private Date   nextReviewDue;
    private int    reviewSeq;

    /**
     * Negative means overdue. Computed against the row's {@code nextReviewDue} at query time,
     * so a worklist left open on a screen overnight is showing yesterday's numbers.
     */
    private int daysUntilDue;

    /**
     * Continued stay rather than an initial determination. The distinction drives which screen
     * the row links to: {@code /auth/{id}/decide} for initial, {@code /auth/{id}/review} for
     * continued stay.
     */
    public boolean isContinuedStay() { return reviewSeq > 1; }

    public boolean isOverdue() { return daysUntilDue < 0; }

    public long getAuthId() { return authId; }
    public void setAuthId(long authId) { this.authId = authId; }

    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }

    public String getMemberLastName() { return memberLastName; }
    public void setMemberLastName(String n) { this.memberLastName = n; }

    public String getRequestedLoc() { return requestedLoc; }
    public void setRequestedLoc(String requestedLoc) { this.requestedLoc = requestedLoc; }

    public String getCurrentLoc() { return currentLoc; }
    public void setCurrentLoc(String currentLoc) { this.currentLoc = currentLoc; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getUrgency() { return urgency; }
    public void setUrgency(String urgency) { this.urgency = urgency; }

    public String getDiagnosisCode() { return diagnosisCode; }
    public void setDiagnosisCode(String diagnosisCode) { this.diagnosisCode = diagnosisCode; }

    public boolean isPart2Program() { return part2Program; }
    public void setPart2Program(boolean part2Program) { this.part2Program = part2Program; }

    public Date getSubmittedTs() { return submittedTs; }
    public void setSubmittedTs(Date submittedTs) { this.submittedTs = submittedTs; }

    public Date getNextReviewDue() { return nextReviewDue; }
    public void setNextReviewDue(Date nextReviewDue) { this.nextReviewDue = nextReviewDue; }

    public int getReviewSeq() { return reviewSeq; }
    public void setReviewSeq(int reviewSeq) { this.reviewSeq = reviewSeq; }

    public int getDaysUntilDue() { return daysUntilDue; }
    public void setDaysUntilDue(int daysUntilDue) { this.daysUntilDue = daysUntilDue; }
}
