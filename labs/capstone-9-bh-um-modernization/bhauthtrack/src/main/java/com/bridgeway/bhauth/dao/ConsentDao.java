package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.Consent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * 42 CFR Part 2 consents.
 *
 * <p>{@link #insert} is called from inside {@code AuthCaseService.submitAndDecide()}, in the same
 * transaction as the authorization write. That co-location is the point: an authorization for a
 * Part 2 program cannot exist in this database without its consent row, because both writes
 * commit together or neither does.</p>
 *
 * <p>Nothing else in the system enforces consent. There is no check before the queue payload is
 * built, before the narrative is logged, or before a Crystal report reads the view. The
 * transaction boundary is the whole control.</p>
 */
@Repository
public class ConsentDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String COLS =
        "CONSENT_ID, AUTH_ID, MEMBER_ID, RECIPIENT_NAME, RECIPIENT_TYPE, PURPOSE, SCOPE, "
      + "SIGNED_TS, EXPIRES_TS, REVOKED_TS, REDISCLOSURE_NOTICE_SENT";

    public void insert(Consent c) {
        long id = jdbc.queryForObject("SELECT SEQ_BH_CONSENT_ID.NEXTVAL FROM DUAL", Long.class);
        c.setConsentId(id);
        jdbc.update(
            "INSERT INTO BH_CONSENT (" + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            id, c.getAuthId(), c.getMemberId(), c.getRecipientName(), c.getRecipientType(),
            c.getPurpose(), c.getScope(), c.getSignedTs(), c.getExpiresTs(), c.getRevokedTs(),
            c.getRedisclosureNoticeSent() == null ? "N" : c.getRedisclosureNoticeSent());
    }

    /**
     * The consent governing one authorization, if any.
     *
     * <p>Returns null rather than throwing when there is none, and every caller treats null as
     * "carry on". Two months of 2012 UAT data has no consent rows at all because BHA-0311 was
     * applied to production before UAT.</p>
     */
    public Consent findByAuth(long authId) {
        List<Consent> rows = jdbc.query(
            "SELECT " + COLS + " FROM BH_CONSENT WHERE AUTH_ID = ? "
          + "ORDER BY SIGNED_TS DESC",
            new Object[] { authId }, MAPPER);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<Consent> findByMember(String memberId) {
        return jdbc.query(
            "SELECT " + COLS + " FROM BH_CONSENT WHERE MEMBER_ID = ? ORDER BY SIGNED_TS DESC",
            new Object[] { memberId }, MAPPER);
    }

    /**
     * Revoke a consent.
     *
     * <p>Sets a timestamp. It does not recall anything already disclosed, does not notify the
     * named recipient, and does not flag the authorizations that were decided while it was
     * active. A revocation in this system is a note to the future only.</p>
     */
    public void revoke(long consentId, String actor) {
        jdbc.update("UPDATE BH_CONSENT SET REVOKED_TS = SYSDATE WHERE CONSENT_ID = ?", consentId);
    }

    public void markNoticeSent(long consentId) {
        jdbc.update("UPDATE BH_CONSENT SET REDISCLOSURE_NOTICE_SENT = 'Y' WHERE CONSENT_ID = ?",
                    consentId);
    }

    /**
     * Authorizations from Part 2 programs that have no usable consent.
     *
     * <p>Written for a 2016 compliance request and run by hand roughly once a year. It is not on
     * a screen, not on a schedule, and not alerted on.</p>
     */
    public List<Long> findPart2AuthsWithoutUsableConsent() {
        return jdbc.queryForList(
            "SELECT a.AUTH_ID FROM BH_AUTH a "
          + "JOIN BH_PROVIDER p ON p.BRIDGEWAY_PROV_ID = a.BRIDGEWAY_PROV_ID "
          + "LEFT JOIN BH_CONSENT c ON c.AUTH_ID = a.AUTH_ID "
          + "   AND c.REVOKED_TS IS NULL AND c.EXPIRES_TS > SYSDATE "
          + "WHERE p.IS_PART2_PROGRAM = 'Y' AND c.CONSENT_ID IS NULL",
            Long.class);
    }

    private static final RowMapper<Consent> MAPPER = new RowMapper<Consent>() {
        @Override
        public Consent mapRow(ResultSet rs, int rowNum) throws SQLException {
            Consent c = new Consent();
            c.setConsentId(rs.getLong("CONSENT_ID"));
            c.setAuthId(rs.getLong("AUTH_ID"));
            c.setMemberId(rs.getString("MEMBER_ID"));
            c.setRecipientName(rs.getString("RECIPIENT_NAME"));
            c.setRecipientType(rs.getString("RECIPIENT_TYPE"));
            c.setPurpose(rs.getString("PURPOSE"));
            c.setScope(rs.getString("SCOPE"));
            c.setSignedTs(ts(rs, "SIGNED_TS"));
            c.setExpiresTs(ts(rs, "EXPIRES_TS"));
            c.setRevokedTs(ts(rs, "REVOKED_TS"));
            c.setRedisclosureNoticeSent(rs.getString("REDISCLOSURE_NOTICE_SENT"));
            return c;
        }
    };

    private static Date ts(ResultSet rs, String col) throws SQLException {
        java.sql.Timestamp t = rs.getTimestamp(col);
        return t == null ? null : new Date(t.getTime());
    }
}
