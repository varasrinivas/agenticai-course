package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.LocReview;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * The concurrent-review ladder.
 *
 * <p>{@link #maxSeq} plus one is how the next review sequence is chosen. That is a read followed
 * by a write with no lock between them, so two reviewers saving a continued stay on the same
 * authorization at the same moment both compute the same sequence and the second one violates
 * {@code UQ_BH_LOCREV_SEQ}. The user sees a stack trace. It happens perhaps twice a year and has
 * never been prioritised.</p>
 *
 * <p>Worth noting for a port: that unique constraint is the only thing preventing a corrupt
 * ladder. Move this table to a service whose database has no such constraint — the modern
 * platform's schema has zero foreign keys and no composite uniques — and the crash becomes
 * silent duplicate reviews instead.</p>
 */
@Repository
public class LocReviewDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String COLS =
        "REVIEW_ID, AUTH_ID, REVIEW_SEQ, REVIEWED_LOC, APPROVED_UNITS, REVIEW_INTERVAL_DAYS, "
      + "NEXT_REVIEW_DUE, OUTCOME, REVIEWER_USER_ID, REVIEWER_CREDENTIAL, REVIEW_TS";

    public void insert(LocReview r) {
        long id = jdbc.queryForObject("SELECT SEQ_BH_REVIEW_ID.NEXTVAL FROM DUAL", Long.class);
        r.setReviewId(id);
        jdbc.update(
            "INSERT INTO BH_LOC_REVIEW (" + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            id, r.getAuthId(), r.getReviewSeq(), r.getReviewedLoc(), r.getApprovedUnits(),
            r.getReviewIntervalDays(), r.getNextReviewDue(), r.getOutcome(),
            r.getReviewerUserId(), r.getReviewerCredential(), r.getReviewTs());
    }

    /** Zero when there are no reviews yet, so the initial determination is always sequence 1. */
    public int maxSeq(long authId) {
        Integer n = jdbc.queryForObject(
            "SELECT NVL(MAX(REVIEW_SEQ), 0) FROM BH_LOC_REVIEW WHERE AUTH_ID = ?",
            new Object[] { authId }, Integer.class);
        return n == null ? 0 : n;
    }

    public List<LocReview> findByAuth(long authId) {
        return jdbc.query(
            "SELECT " + COLS + " FROM BH_LOC_REVIEW WHERE AUTH_ID = ? ORDER BY REVIEW_SEQ",
            new Object[] { authId }, MAPPER);
    }

    /** The most recent review. Its {@code nextReviewDue} is what the clocks are computed from. */
    public LocReview findLatest(long authId) {
        List<LocReview> rows = jdbc.query(
            "SELECT " + COLS + " FROM BH_LOC_REVIEW WHERE AUTH_ID = ? "
          + "ORDER BY REVIEW_SEQ DESC",
            new Object[] { authId }, MAPPER);
        return rows.isEmpty() ? null : rows.get(0);
    }

    /**
     * Reviews that are due or overdue.
     *
     * <p>This query is the concurrent-review process. There is no timer and no scheduler
     * enforcing the cadence; there is this SELECT, run when the worklist page is opened. An
     * overdue residential review that nobody opens the worklist to see simply stays overdue.</p>
     */
    public List<LocReview> findDue(int withinDays) {
        return jdbc.query(
            "SELECT " + COLS + " FROM BH_LOC_REVIEW r "
          + "WHERE r.NEXT_REVIEW_DUE IS NOT NULL "
          + "  AND r.NEXT_REVIEW_DUE <= SYSDATE + ? "
          + "  AND r.OUTCOME NOT IN ('DISCHARGED','DENIED') "
          + "  AND r.REVIEW_SEQ = (SELECT MAX(REVIEW_SEQ) FROM BH_LOC_REVIEW "
          + "                       WHERE AUTH_ID = r.AUTH_ID) "
          + "ORDER BY r.NEXT_REVIEW_DUE",
            new Object[] { withinDays }, MAPPER);
    }

    private static final RowMapper<LocReview> MAPPER = new RowMapper<LocReview>() {
        @Override
        public LocReview mapRow(ResultSet rs, int rowNum) throws SQLException {
            LocReview r = new LocReview();
            r.setReviewId(rs.getLong("REVIEW_ID"));
            r.setAuthId(rs.getLong("AUTH_ID"));
            r.setReviewSeq(rs.getInt("REVIEW_SEQ"));
            r.setReviewedLoc(rs.getString("REVIEWED_LOC"));
            r.setApprovedUnits(rs.getInt("APPROVED_UNITS"));
            r.setReviewIntervalDays(rs.getInt("REVIEW_INTERVAL_DAYS"));
            r.setNextReviewDue(ts(rs, "NEXT_REVIEW_DUE"));
            r.setOutcome(rs.getString("OUTCOME"));
            r.setReviewerUserId(rs.getString("REVIEWER_USER_ID"));
            r.setReviewerCredential(rs.getString("REVIEWER_CREDENTIAL"));
            r.setReviewTs(ts(rs, "REVIEW_TS"));
            return r;
        }
    };

    private static Date ts(ResultSet rs, String col) throws SQLException {
        java.sql.Timestamp t = rs.getTimestamp(col);
        return t == null ? null : new Date(t.getTime());
    }
}
