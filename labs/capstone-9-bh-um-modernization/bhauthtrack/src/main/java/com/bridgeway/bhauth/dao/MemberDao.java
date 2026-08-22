package com.bridgeway.bhauth.dao;

import com.bridgeway.bhauth.domain.Member;
import com.bridgeway.bhauth.domain.Provider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * Members and providers. One DAO for both because in 2011 they were one screen.
 *
 * <h3>Read {@link #findByPlanMemberId} and {@link #findById} together</h3>
 *
 * <p>Two lookups, two different identifiers, and the difference is the entity-resolution trap.
 * {@code MEMBER_ID} is Bridgeway's carve-out key and is the primary key of everything in this
 * system. {@code PLAN_MEMBER_ID} is the health plan's key and is <em>nullable</em>.</p>
 *
 * <p>Everything internal joins on the first. Everything that crosses to the plan must use the
 * second — and roughly a third of pre-2014 members do not have one, so those authorizations
 * cannot be reconciled with the plan at all. They process normally. Nothing complains.</p>
 *
 * <p>The modern platform stores one opaque {@code member_id VARCHAR(32)} with no member table
 * and no foreign key, so it will accept either identifier without objecting. A port that maps
 * {@code MEMBER_ID → member_id} produces a system that matches by luck for the subset whose
 * formats happen to coincide.</p>
 */
@Repository
public class MemberDao {

    @Autowired private JdbcTemplate jdbc;

    private static final String MEMBER_COLS =
        "MEMBER_ID, PLAN_MEMBER_ID, LAST_NAME, FIRST_NAME, DOB, LINE_OF_BUSINESS, "
      + "ELIGIBILITY_START, ELIGIBILITY_END";

    /** By Bridgeway's identifier. This is what every internal join uses. */
    public Member findById(String memberId) {
        List<Member> rows = jdbc.query(
            "SELECT " + MEMBER_COLS + " FROM BH_MEMBER WHERE MEMBER_ID = ?",
            new Object[] { memberId }, MEMBER_MAPPER);
        return rows.isEmpty() ? null : rows.get(0);
    }

    /**
     * By the health plan's identifier.
     *
     * <p>Returns a list, not a single member, because {@code PLAN_MEMBER_ID} has no unique
     * constraint. Duplicates exist: the 2014 eligibility rewrite backfilled the column from a
     * match on name and date of birth, and twins share both.</p>
     */
    public List<Member> findByPlanMemberId(String planMemberId) {
        return jdbc.query(
            "SELECT " + MEMBER_COLS + " FROM BH_MEMBER WHERE PLAN_MEMBER_ID = ?",
            new Object[] { planMemberId }, MEMBER_MAPPER);
    }

    /** Members with no plan identifier at all. Roughly 31% of pre-July-2014 rows. */
    public List<Member> findUnresolvedToPlan() {
        return jdbc.query(
            "SELECT " + MEMBER_COLS + " FROM BH_MEMBER WHERE PLAN_MEMBER_ID IS NULL "
          + "ORDER BY ELIGIBILITY_START",
            MEMBER_MAPPER);
    }

    public List<Member> searchByName(String lastNameFragment) {
        return jdbc.query(
            "SELECT " + MEMBER_COLS + " FROM BH_MEMBER "
          + "WHERE UPPER(LAST_NAME) LIKE UPPER(?) || '%' AND ROWNUM <= 100 ORDER BY LAST_NAME",
            new Object[] { lastNameFragment }, MEMBER_MAPPER);
    }

    public Provider findProvider(String bridgewayProvId) {
        List<Provider> rows = jdbc.query(
            "SELECT BRIDGEWAY_PROV_ID, NPI, PROVIDER_NAME, NETWORK_STATUS, IS_PART2_PROGRAM "
          + "FROM BH_PROVIDER WHERE BRIDGEWAY_PROV_ID = ?",
            new Object[] { bridgewayProvId }, PROVIDER_MAPPER);
        return rows.isEmpty() ? null : rows.get(0);
    }

    private static final RowMapper<Member> MEMBER_MAPPER = new RowMapper<Member>() {
        @Override
        public Member mapRow(ResultSet rs, int rowNum) throws SQLException {
            Member m = new Member();
            m.setMemberId(rs.getString("MEMBER_ID"));
            m.setPlanMemberId(rs.getString("PLAN_MEMBER_ID"));
            m.setLastName(rs.getString("LAST_NAME"));
            m.setFirstName(rs.getString("FIRST_NAME"));
            m.setDob(ts(rs, "DOB"));
            m.setLineOfBusiness(rs.getString("LINE_OF_BUSINESS"));
            m.setEligibilityStart(ts(rs, "ELIGIBILITY_START"));
            m.setEligibilityEnd(ts(rs, "ELIGIBILITY_END"));
            return m;
        }
    };

    private static final RowMapper<Provider> PROVIDER_MAPPER = new RowMapper<Provider>() {
        @Override
        public Provider mapRow(ResultSet rs, int rowNum) throws SQLException {
            Provider p = new Provider();
            p.setBridgewayProvId(rs.getString("BRIDGEWAY_PROV_ID"));
            p.setNpi(rs.getString("NPI"));
            p.setProviderName(rs.getString("PROVIDER_NAME"));
            p.setNetworkStatus(rs.getString("NETWORK_STATUS"));
            p.setIsPart2Program(rs.getString("IS_PART2_PROGRAM"));
            return p;
        }
    };

    private static Date ts(ResultSet rs, String col) throws SQLException {
        java.sql.Timestamp t = rs.getTimestamp(col);
        return t == null ? null : new Date(t.getTime());
    }
}
