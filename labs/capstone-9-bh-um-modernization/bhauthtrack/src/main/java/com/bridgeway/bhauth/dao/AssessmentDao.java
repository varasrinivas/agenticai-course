package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.Assessment;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * Instrument scores.
 *
 * <p>These rows are the <em>inputs</em> to {@code PKG_LOC_RULES.EVAL_LOC} — the package reads
 * them straight out of this table rather than being passed them. That is why the assessments
 * must be written before the rules engine is called, and why they are write 2 of five in
 * {@code AuthCaseService.submitAndDecide()} while the engine runs after.</p>
 *
 * <p>A port that turns the rules engine into a service taking a request object has to notice
 * that dependency and pass the dimensions explicitly. A port that keeps "read from the database"
 * has to notice that the database is now a different service's.</p>
 */
@Repository
public class AssessmentDao {

    @Autowired private JdbcTemplate jdbc;

    /**
     * Insert one ASAM dimension score.
     *
     * <p>No validation. Dimension is constrained to 1..6 by the table; score is not constrained
     * at all. The ladder treats a dimension-1 score of 4 or more as justifying medically managed
     * inpatient care, so a fat-fingered 40 approves ASAM 4.0 without comment. This has happened
     * at least once, in 2014, and was caught by the facility rather than by the system.</p>
     */
    public void insertAsamDimension(long authId, int dimension, int score) {
        jdbc.update(
            "INSERT INTO BH_ASSESSMENT (ASSESSMENT_ID, AUTH_ID, INSTRUMENT, DIMENSION, SCORE, "
          + "                           ASSESSED_TS) "
          + "VALUES (SEQ_BH_ASSESS_ID.NEXTVAL, ?, 'ASAM_DIM', ?, ?, SYSDATE)",
            authId, dimension, score);
    }

    public void insertInstrument(long authId, String instrument, int score) {
        jdbc.update(
            "INSERT INTO BH_ASSESSMENT (ASSESSMENT_ID, AUTH_ID, INSTRUMENT, DIMENSION, SCORE, "
          + "                           ASSESSED_TS) "
          + "VALUES (SEQ_BH_ASSESS_ID.NEXTVAL, ?, ?, NULL, ?, SYSDATE)",
            authId, instrument, score);
    }

    public List<Assessment> findByAuth(long authId) {
        return jdbc.query(
            "SELECT ASSESSMENT_ID, AUTH_ID, INSTRUMENT, DIMENSION, SCORE, ASSESSED_TS "
          + "FROM BH_ASSESSMENT WHERE AUTH_ID = ? ORDER BY INSTRUMENT, DIMENSION",
            new Object[] { authId }, MAPPER);
    }

    /** The six ASAM dimension scores as an array indexed 1..6; index 0 is unused. */
    public int[] asamDimensions(long authId) {
        final int[] dims = new int[7];
        jdbc.query(
            "SELECT DIMENSION, MAX(SCORE) AS SCORE FROM BH_ASSESSMENT "
          + "WHERE AUTH_ID = ? AND INSTRUMENT = 'ASAM_DIM' GROUP BY DIMENSION",
            new Object[] { authId },
            new org.springframework.jdbc.core.RowCallbackHandler() {
                @Override
                public void processRow(ResultSet rs) throws SQLException {
                    int d = rs.getInt("DIMENSION");
                    if (d >= 1 && d <= 6) dims[d] = rs.getInt("SCORE");
                }
            });
        return dims;
    }

    private static final RowMapper<Assessment> MAPPER = new RowMapper<Assessment>() {
        @Override
        public Assessment mapRow(ResultSet rs, int rowNum) throws SQLException {
            Assessment a = new Assessment();
            a.setAssessmentId(rs.getLong("ASSESSMENT_ID"));
            a.setAuthId(rs.getLong("AUTH_ID"));
            a.setInstrument(rs.getString("INSTRUMENT"));
            int dim = rs.getInt("DIMENSION");
            a.setDimension(rs.wasNull() ? null : Integer.valueOf(dim));
            a.setScore(rs.getInt("SCORE"));
            java.sql.Timestamp t = rs.getTimestamp("ASSESSED_TS");
            a.setAssessedTs(t == null ? null : new Date(t.getTime()));
            return a;
        }
    };
}
