package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.WorklistItem;
import com.bridgeway.bhauth.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * The worklist query. One SQL statement, and it is the work-distribution system.
 *
 * <p>There is no task engine here. No assignment, no claim, no ownership, no escalation. A
 * reviewer opens a page, this query runs, and whatever it returns is that reviewer's work.</p>
 *
 * <h3>Two role filters, in two places</h3>
 *
 * <p>{@link #forReviewer} filters by role in SQL: a nurse's worklist excludes cases already
 * pended for a physician, because a nurse cannot act on them. Then {@code worklist.jsp} filters
 * <em>again</em> in JSTL, hiding the action links on rows the viewer cannot work.</p>
 *
 * <p>The two filters do not agree. The SQL below excludes {@code PENDED} rows for a non-MD; the
 * JSP hides links on rows whose diagnosis needs a specialty the viewer lacks — a rule the SQL
 * knows nothing about. Neither is a superset of the other, which means the answer to "what work
 * is mine?" depends on which layer you ask.</p>
 *
 * <p>A port has to decide where that rule actually lives before it can move it.</p>
 */
@Repository
public class WorklistDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String BASE =
        "SELECT a.AUTH_ID, a.MEMBER_ID, m.LAST_NAME, a.REQUESTED_LOC, a.DIAGNOSIS_CODE, "
      + "       a.STATUS, a.URGENCY, a.SUBMITTED_TS, p.IS_PART2_PROGRAM, "
      + "       r.REVIEWED_LOC, r.NEXT_REVIEW_DUE, NVL(r.REVIEW_SEQ, 0) AS REVIEW_SEQ, "
      + "       TRUNC(NVL(r.NEXT_REVIEW_DUE, SYSDATE) - SYSDATE) AS DAYS_UNTIL_DUE "
      + "  FROM BH_AUTH a "
      + "  JOIN BH_MEMBER   m ON m.MEMBER_ID = a.MEMBER_ID "
      + "  JOIN BH_PROVIDER p ON p.BRIDGEWAY_PROV_ID = a.BRIDGEWAY_PROV_ID "
      + "  LEFT JOIN BH_LOC_REVIEW r ON r.AUTH_ID = a.AUTH_ID "
      + "       AND r.REVIEW_SEQ = (SELECT MAX(REVIEW_SEQ) FROM BH_LOC_REVIEW "
      + "                            WHERE AUTH_ID = a.AUTH_ID) ";

    /**
     * Everything this reviewer can act on, most urgent first.
     *
     * <p>Ordering: overdue continued stays, then expedited requests, then everything else by
     * submission date. {@code DAYS_UNTIL_DUE} is computed here with {@code TRUNC}, and computed
     * again in a scriptlet in {@code decision.jsp} using integer division on milliseconds. The
     * two round differently, so a case can sort as "due today" and display as "1 day".</p>
     */
    public List<WorklistItem> forReviewer(int roleMask) {
        boolean isMd = (roleMask & UserContext.ROLE_MD) == UserContext.ROLE_MD;

        StringBuilder sql = new StringBuilder(BASE);
        sql.append(" WHERE a.STATUS IN ('SUBMITTED','IN_REVIEW','PENDED','APPROVED') ");

        // A nurse cannot act on a case pended for an adverse determination, so it is hidden
        // rather than shown-and-refused. Physicians see everything.
        if (!isMd) {
            sql.append(" AND NOT (a.STATUS = 'PENDED' "
                     + "          AND a.DENIAL_REASON_CODE = 'CRITERIA_NOT_MET') ");
        }

        // An approved authorization only belongs on a worklist when its next review is near.
        sql.append(" AND (a.STATUS <> 'APPROVED' "
                 + "      OR (r.NEXT_REVIEW_DUE IS NOT NULL "
                 + "          AND r.NEXT_REVIEW_DUE <= SYSDATE + 2)) ");

        sql.append(" ORDER BY CASE WHEN r.NEXT_REVIEW_DUE < SYSDATE THEN 0 "
                 + "               WHEN a.URGENCY = 'EXPEDITED'     THEN 1 "
                 + "               ELSE 2 END, a.SUBMITTED_TS ");

        return jdbc.query(sql.toString(), MAPPER);
    }

    /** Continued stays due inside {@code withinDays}. Feeds the reminder job. */
    public List<WorklistItem> continuedStaysDue(int withinDays) {
        return jdbc.query(
            BASE + " WHERE a.STATUS = 'APPROVED' AND r.NEXT_REVIEW_DUE IS NOT NULL "
                 + "   AND r.NEXT_REVIEW_DUE <= SYSDATE + ? "
                 + "   AND r.OUTCOME NOT IN ('DISCHARGED','DENIED') "
                 + " ORDER BY r.NEXT_REVIEW_DUE",
            new Object[] { withinDays }, MAPPER);
    }

    private static final RowMapper<WorklistItem> MAPPER = new RowMapper<WorklistItem>() {
        @Override
        public WorklistItem mapRow(ResultSet rs, int rowNum) throws SQLException {
            WorklistItem w = new WorklistItem();
            w.setAuthId(rs.getLong("AUTH_ID"));
            w.setMemberId(rs.getString("MEMBER_ID"));
            w.setMemberLastName(rs.getString("LAST_NAME"));
            w.setRequestedLoc(rs.getString("REQUESTED_LOC"));
            w.setCurrentLoc(rs.getString("REVIEWED_LOC"));
            w.setDiagnosisCode(rs.getString("DIAGNOSIS_CODE"));
            w.setStatus(rs.getString("STATUS"));
            w.setUrgency(rs.getString("URGENCY"));
            w.setPart2Program("Y".equals(rs.getString("IS_PART2_PROGRAM")));
            w.setSubmittedTs(ts(rs, "SUBMITTED_TS"));
            w.setNextReviewDue(ts(rs, "NEXT_REVIEW_DUE"));
            w.setReviewSeq(rs.getInt("REVIEW_SEQ"));
            w.setDaysUntilDue(rs.getInt("DAYS_UNTIL_DUE"));
            return w;
        }
    };

    private static Date ts(ResultSet rs, String col) throws SQLException {
        java.sql.Timestamp t = rs.getTimestamp(col);
        return t == null ? null : new Date(t.getTime());
    }
}
