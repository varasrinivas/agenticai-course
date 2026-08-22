package com.meridian.ucc.legacy;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import javax.sql.DataSource;

/**
 * Legacy risk reporting DAO. Oracle-only SQL, JDBC, 2013 vintage.
 *
 * This file is INPUT to the `appsql-rewriter` subagent. Planted
 * Oracle-isms:
 *   - a call into the PKG_RISK_CALC package (packages do not exist in
 *     PostgreSQL -- the call target becomes schema-qualified function)
 *   - MERGE ... USING dual
 *   - ROWNUM paging with a BETWEEN, the two-level Oracle idiom
 *   - date arithmetic that returns a NUMBER of days in Oracle and an
 *     INTERVAL in PostgreSQL
 *   - TRUNC(SYSDATE) and ADD_MONTHS
 */
public class RiskReportDao {

    private final DataSource dataSource;

    public RiskReportDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Package call. In PostgreSQL this becomes
     *   SELECT pkg_risk_calc.score_debtor(?)
     * where pkg_risk_calc is a SCHEMA, not a package -- so the dotted
     * name survives, but only because the converter created a schema
     * with that exact name. That is a deliberate translation choice and
     * the plsql-converter must record it in the decision log.
     */
    public double scoreDebtor(String debtorName) throws SQLException {
        final String sql =
            "SELECT pkg_risk_calc.score_debtor(?) AS score FROM dual";

        try (Connection cn = dataSource.getConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, debtorName);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getDouble("score") : 0.0d;
            }
        }
    }

    /**
     * Classic Oracle two-level ROWNUM paging. The inner ROWNUM alias is
     * required because ROWNUM is assigned before ORDER BY. Rewriting
     * this as LIMIT/OFFSET is straightforward; recognising WHY it is
     * written this way is the part that needs a human or a careful agent.
     */
    public List<String> topDebtorsPaged(int pageStart, int pageEnd) throws SQLException {
        final String sql =
            "SELECT debtor_name FROM ( "
          + "  SELECT inner_q.*, ROWNUM AS rn FROM ( "
          + "    SELECT d.debtor_name, COUNT(*) AS filing_count "
          + "      FROM ucc_debtor d "
          + "      JOIN ucc_filing f ON f.filing_id = d.filing_id "
          + "     WHERE f.status = 'ACTIVE' "
          + "     GROUP BY d.debtor_name "
          + "     ORDER BY COUNT(*) DESC "
          + "  ) inner_q "
          + "  WHERE ROWNUM <= ? "
          + ") WHERE rn >= ?";

        List<String> out = new ArrayList<>();
        try (Connection cn = dataSource.getConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setInt(1, pageEnd);
            ps.setInt(2, pageStart);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    out.add(rs.getString("debtor_name"));
                }
            }
        }
        return out;
    }

    /**
     * Filings due to lapse in the next N days.
     *
     * `lapse_date - TRUNC(SYSDATE)` yields a NUMBER of days on Oracle.
     * On PostgreSQL the same expression yields an INTERVAL, so
     * `<= ?` against an int silently fails to compile. This is the kind
     * of difference that does not throw at translation time -- it throws
     * in production, six weeks later.
     */
    public List<String> lapsingSoon(int withinDays) throws SQLException {
        final String sql =
            "SELECT f.filing_number, "
          + "       f.lapse_date - TRUNC(SYSDATE) AS days_remaining "
          + "  FROM ucc_filing f "
          + " WHERE f.status = 'ACTIVE' "
          + "   AND f.lapse_date IS NOT NULL "
          + "   AND f.lapse_date BETWEEN TRUNC(SYSDATE) "
          + "                        AND TRUNC(SYSDATE) + ? "
          + " ORDER BY f.lapse_date";

        List<String> out = new ArrayList<>();
        try (Connection cn = dataSource.getConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setInt(1, withinDays);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    out.add(rs.getString("filing_number")
                            + " (" + rs.getInt("days_remaining") + "d)");
                }
            }
        }
        return out;
    }

    /** MERGE ... USING dual. Becomes INSERT ... ON CONFLICT DO UPDATE. */
    public void upsertStateSource(String code, String name, String format)
            throws SQLException {
        final String sql =
            "MERGE INTO state_sos_source t "
          + "USING (SELECT ? AS state_code FROM dual) s "
          + "   ON (t.state_code = s.state_code) "
          + " WHEN MATCHED THEN UPDATE SET t.state_name = ?, "
          + "                              t.feed_format = ?, "
          + "                              t.last_sync = SYSTIMESTAMP "
          + " WHEN NOT MATCHED THEN INSERT (state_code, state_name, feed_format, last_sync) "
          + "                       VALUES (?, ?, ?, SYSTIMESTAMP)";

        try (Connection cn = dataSource.getConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, code);
            ps.setString(2, name);
            ps.setString(3, format);
            ps.setString(4, code);
            ps.setString(5, name);
            ps.setString(6, format);
            ps.executeUpdate();
        }
    }
}
