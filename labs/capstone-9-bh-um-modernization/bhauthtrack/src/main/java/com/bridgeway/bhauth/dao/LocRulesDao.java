package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.LocDecision;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Types;

/**
 * The bridge between Java and {@code PKG_LOC_RULES}.
 *
 * <p>Oracle PL/SQL records cannot cross the JDBC boundary, so {@link #callEvalLoc} does not call
 * {@code EVAL_LOC} directly. It calls an anonymous block that calls it and unpacks the record
 * into six scalar OUT parameters. The block is written out below as a string literal.</p>
 *
 * <p><b>Why that matters to a port.</b> This block is a second, undocumented copy of the
 * decision's field list. Add a field to {@code t_decision} and this file compiles, runs, and
 * silently omits it. That is exactly what happened when {@code rule_path} was added in 2015.</p>
 *
 * <p>The queries below {@link #callEvalLoc} feed {@code LocRulesService}'s Java-side
 * adjustments. Note that they are three separate round trips, executed after the PL/SQL has
 * already committed to an outcome. That ordering is what makes the Java layer able only to
 * downgrade, never to upgrade.</p>
 */
@Repository
public class LocRulesDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String EVAL_BLOCK =
        "BEGIN "
      + "  DECLARE r PKG_LOC_RULES.t_decision; "
      + "  BEGIN "
      + "    r := PKG_LOC_RULES.EVAL_LOC(?); "
      + "    ? := r.outcome; "
      + "    ? := r.granted_loc; "
      + "    ? := r.granted_units; "
      + "    ? := r.interval_days; "
      + "    ? := r.reason_code; "
      + "    ? := r.rule_path; "
      + "  END; "
      + "END;";

    public LocDecision callEvalLoc(final long authId) {
        return jdbc.execute(new org.springframework.jdbc.core.ConnectionCallback<LocDecision>() {
            @Override
            public LocDecision doInConnection(Connection con) throws SQLException {
                CallableStatement cs = null;
                try {
                    cs = con.prepareCall(EVAL_BLOCK);
                    cs.setLong(1, authId);
                    cs.registerOutParameter(2, Types.VARCHAR);   // outcome
                    cs.registerOutParameter(3, Types.VARCHAR);   // granted_loc
                    cs.registerOutParameter(4, Types.NUMERIC);   // granted_units
                    cs.registerOutParameter(5, Types.NUMERIC);   // interval_days
                    cs.registerOutParameter(6, Types.VARCHAR);   // reason_code
                    cs.registerOutParameter(7, Types.VARCHAR);   // rule_path
                    cs.execute();

                    LocDecision d = new LocDecision();
                    d.setOutcome(cs.getString(2));
                    d.setGrantedLoc(cs.getString(3));
                    d.setGrantedUnits(cs.getInt(4));
                    d.setIntervalDays(cs.getInt(5));
                    d.setReasonCode(cs.getString(6));
                    d.setRulePath(cs.getString(7));
                    return d;
                } finally {
                    if (cs != null) {
                        try { cs.close(); } catch (SQLException ignore) { }
                    }
                }
            }
        });
    }

    /**
     * Days of benefit left at this level of care in the current benefit year.
     *
     * <p>Reads the accumulator table maintained by the claims feed. If the feed has not run,
     * this returns yesterday's number and the cap in {@code LocRulesService} is applied against
     * stale data. There is no staleness check.</p>
     */
    public int remainingBenefitDays(String memberId, String loc) {
        Integer n = jdbc.queryForObject(
            "SELECT NVL(MAX(REMAINING_DAYS), 0) FROM BH_BENEFIT_ACCUM "
          + "WHERE MEMBER_ID = ? AND LOC_CATEGORY = ? AND BENEFIT_YEAR = "
          + "      TO_CHAR(SYSDATE,'YYYY')",
            new Object[] { memberId, locCategory(loc) }, Integer.class);
        return n == null ? 0 : n;
    }

    /**
     * Adverse determinations for this member in the rolling twelve months.
     *
     * <p>Feeds the frequency pend in {@code LocRulesService}. Note that it counts denials
     * <em>across all levels of care and all diagnoses</em>: three outpatient denials pend a
     * residential request. Whether that is intended is unrecorded.</p>
     */
    public int countDenialsInRollingYear(String memberId) {
        Integer n = jdbc.queryForObject(
            "SELECT COUNT(*) FROM BH_AUTH "
          + "WHERE MEMBER_ID = ? AND STATUS = 'DENIED' "
          + "  AND DECIDED_TS >= ADD_MONTHS(SYSDATE, -12)",
            new Object[] { memberId }, Integer.class);
        return n == null ? 0 : n;
    }

    /**
     * Whether any in-network facility at this level has an open bed.
     *
     * <p>Reads a table populated by a spreadsheet upload that the network team does on Mondays.
     * By Thursday it is fiction. The step-down in {@code LocRulesService} runs off it anyway.</p>
     */
    public boolean hasInNetworkCapacity(String loc) {
        Integer n = jdbc.queryForObject(
            "SELECT COUNT(*) FROM BH_FACILITY_CAPACITY c "
          + "JOIN BH_PROVIDER p ON p.BRIDGEWAY_PROV_ID = c.BRIDGEWAY_PROV_ID "
          + "WHERE c.LOC_LEVEL = ? AND c.OPEN_BEDS > 0 AND p.NETWORK_STATUS = 'IN'",
            new Object[] { loc }, Integer.class);
        return n != null && n > 0;
    }

    /** Benefit accumulators are tracked by category, not by ASAM level. */
    private String locCategory(String loc) {
        if (loc == null) return "OUTPATIENT";
        if ("4.0".equals(loc) || "3.7".equals(loc)) return "INPATIENT";
        if ("3.5".equals(loc) || "3.1".equals(loc)) return "RESIDENTIAL";
        if ("2.5".equals(loc)) return "PHP";
        if ("2.1".equals(loc)) return "IOP";
        return "OUTPATIENT";
    }
}
