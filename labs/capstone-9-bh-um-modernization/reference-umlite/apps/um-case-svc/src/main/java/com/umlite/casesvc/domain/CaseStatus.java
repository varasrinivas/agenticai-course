package com.umlite.casesvc.domain;

/** Lifecycle of a Prior Auth case (mirrors CaseStatus in @um-lite/domain). */
public enum CaseStatus {
    SUBMITTED, IN_REVIEW, APPROVED, DENIED, PENDED
}
