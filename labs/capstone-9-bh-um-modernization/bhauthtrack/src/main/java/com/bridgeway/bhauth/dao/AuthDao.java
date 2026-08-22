package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.Auth;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.Clob;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * Authorizations. Hand-written SQL over {@link JdbcTemplate}.
 *
 * <p>There is no ORM here. The mapping between {@link Auth} and BH_AUTH is this file, and it is
 * maintained by hand — which is why the reconstruction in {@code 01_schema.sql} and the columns
 * named below are the two places to check when they disagree.</p>
 */
@Repository
public class AuthDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String COLS =
        "AUTH_ID, MEMBER_ID, BRIDGEWAY_PROV_ID, SERVICE_CODE, DIAGNOSIS_CODE, "
      + "REQUESTED_LOC, REQUESTED_UNITS, CLINICAL_NARRATIVE, STATUS, URGENCY, "
      + "LEGACY_OVERRIDE, SUBMITTED_TS, DECIDED_TS, DECIDED_BY, DENIAL_REASON_CODE";

    public long nextAuthId() {
        return jdbc.queryForObject("SELECT SEQ_BH_AUTH_ID.NEXTVAL FROM DUAL", Long.class);
    }

    public void insert(Auth a) {
        jdbc.update(
            "INSERT INTO BH_AUTH (" + COLS + ") "
          + "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            a.getAuthId(), a.getMemberId(), a.getBridgewayProvId(), a.getServiceCode(),
            a.getDiagnosisCode(), a.getRequestedLoc(), a.getRequestedUnits(),
            a.getClinicalNarrative(), a.getStatus(), a.getUrgency(),
            a.getLegacyOverride() == null ? "N" : a.getLegacyOverride(),
            a.getSubmittedTs(), a.getDecidedTs(), a.getDecidedBy(), a.getDenialReasonCode());
    }

    public Auth findById(long authId) {
        return jdbc.queryForObject(
            "SELECT " + COLS + " FROM BH_AUTH WHERE AUTH_ID = ?",
            new Object[] { authId }, MAPPER);
    }

    /**
     * Update status and stamp the decision.
     *
     * <p>Every call to this fires {@code TRG_BH_AUTH_AUDIT}, which copies the full old and new
     * clinical narrative into BH_AUDIT_LOG. An authorization touched twelve times over a
     * residential stay leaves twelve copies of the protected narrative in the audit table.</p>
     *
     * <p>There is no guard here on which transitions are legal. That check lives in
     * {@code AuthStatusService.advance()}, and this method can be — and from the batch importer
     * is — called without going through it.</p>
     */
    public void updateStatus(long authId, String status, String reasonCode, String actor) {
        boolean terminal = "APPROVED".equals(status) || "DENIED".equals(status);
        jdbc.update(
            "UPDATE BH_AUTH SET STATUS = ?, DENIAL_REASON_CODE = ?, "
          + "  DECIDED_TS = CASE WHEN ? = 1 THEN SYSDATE ELSE DECIDED_TS END, "
          + "  DECIDED_BY = CASE WHEN ? = 1 THEN ?      ELSE DECIDED_BY END "
          + "WHERE AUTH_ID = ?",
            status, reasonCode, terminal ? 1 : 0, terminal ? 1 : 0, actor, authId);
    }

    public void updateNarrative(long authId, String narrative) {
        jdbc.update("UPDATE BH_AUTH SET CLINICAL_NARRATIVE = ? WHERE AUTH_ID = ?",
                    narrative, authId);
    }

    public List<Auth> findByMember(String memberId) {
        return jdbc.query(
            "SELECT " + COLS + " FROM BH_AUTH WHERE MEMBER_ID = ? ORDER BY SUBMITTED_TS DESC",
            new Object[] { memberId }, MAPPER);
    }

    /**
     * Free-text search over the narrative.
     *
     * <p>Backs the "clinical" search box on {@code search.jsp}. It is a full CLOB scan with a
     * leading wildcard, it is not indexed, and it runs against the OLTP instance. It is also the
     * only way anyone can find a case they half-remember, so it stays.</p>
     *
     * <p>Note for a port: this is a <em>search over protected content</em> exposed to any
     * authenticated user, with no consent check and no role check. Reimplementing it on a search
     * index without adding one reproduces the flaw at higher throughput.</p>
     */
    public List<Auth> searchNarrative(String fragment) {
        return jdbc.query(
            "SELECT " + COLS + " FROM BH_AUTH "
          + "WHERE DBMS_LOB.INSTR(CLINICAL_NARRATIVE, ?) > 0 "
          + "  AND ROWNUM <= 200 ORDER BY SUBMITTED_TS DESC",
            new Object[] { fragment }, MAPPER);
    }

    public int countByStatus(String status) {
        return jdbc.queryForObject(
            "SELECT COUNT(*) FROM BH_AUTH WHERE STATUS = ?",
            new Object[] { status }, Integer.class);
    }

    private static final RowMapper<Auth> MAPPER = new RowMapper<Auth>() {
        @Override
        public Auth mapRow(ResultSet rs, int rowNum) throws SQLException {
            Auth a = new Auth();
            a.setAuthId(rs.getLong("AUTH_ID"));
            a.setMemberId(rs.getString("MEMBER_ID"));
            a.setBridgewayProvId(rs.getString("BRIDGEWAY_PROV_ID"));
            a.setServiceCode(rs.getString("SERVICE_CODE"));
            a.setDiagnosisCode(rs.getString("DIAGNOSIS_CODE"));
            a.setRequestedLoc(rs.getString("REQUESTED_LOC"));
            a.setRequestedUnits(rs.getInt("REQUESTED_UNITS"));
            a.setClinicalNarrative(readClob(rs.getClob("CLINICAL_NARRATIVE")));
            a.setStatus(rs.getString("STATUS"));
            a.setUrgency(rs.getString("URGENCY"));
            a.setLegacyOverride(rs.getString("LEGACY_OVERRIDE"));
            a.setSubmittedTs(toDate(rs, "SUBMITTED_TS"));
            a.setDecidedTs(toDate(rs, "DECIDED_TS"));
            a.setDecidedBy(rs.getString("DECIDED_BY"));
            a.setDenialReasonCode(rs.getString("DENIAL_REASON_CODE"));
            return a;
        }
    };

    private static String readClob(Clob clob) throws SQLException {
        if (clob == null) return null;
        long len = clob.length();
        // CLOBs here run to a few kilobytes at most. If one is larger than an int can hold,
        // something upstream is very wrong and truncating quietly would hide it.
        if (len > Integer.MAX_VALUE) {
            throw new SQLException("CLINICAL_NARRATIVE exceeds addressable length: " + len);
        }
        return clob.getSubString(1L, (int) len);
    }

    private static Date toDate(ResultSet rs, String col) throws SQLException {
        java.sql.Timestamp ts = rs.getTimestamp(col);
        return ts == null ? null : new Date(ts.getTime());
    }
}
