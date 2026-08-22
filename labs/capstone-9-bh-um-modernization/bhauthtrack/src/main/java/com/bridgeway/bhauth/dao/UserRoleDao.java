package com.bridgeway.bhauth.dao;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

/**
 * Role masks and the Oracle session actor.
 *
 * <p>{@link #setSessionActor} is the mechanism {@code TRG_BH_AUTH_AUDIT} depends on to record
 * <em>who</em> changed an authorization. It sets an Oracle application context on the current
 * connection; the trigger reads it back with {@code SYS_CONTEXT}.</p>
 *
 * <p>That connection comes from a pool. {@link com.bridgeway.bhauth.security.AuthFilter} sets
 * the context once per HTTP request, on whichever connection is current at that moment. Any
 * later work in the same request that borrows a different connection runs with the context
 * unset, and the trigger falls back to {@code USER} — the schema owner. A meaningful share of
 * {@code BH_AUDIT_LOG} is therefore attributed to {@code BHAUTH_APP} rather than to a
 * person.</p>
 *
 * <p><b>This is the only actor-attribution mechanism in the system, and it is unreliable.</b>
 * Any port that promises an accounting of disclosures has to replace it rather than move
 * it.</p>
 */
@Repository
public class UserRoleDao {

    @Autowired private JdbcTemplate jdbc;

    /** Zero when the user has no row — see AuthFilter: a mask of 0 can read and nothing else. */
    public int findRoleMask(String userId) {
        Integer n = jdbc.queryForObject(
            "SELECT NVL(MAX(ROLE_MASK), 0) FROM BH_USER_ROLE "
          + "WHERE USER_ID = ? AND ACTIVE_FLAG = 'Y'",
            new Object[] { userId }, Integer.class);
        return n == null ? 0 : n;
    }

    public void setSessionActor(String userId) {
        jdbc.update("BEGIN DBMS_SESSION.SET_CONTEXT('BHAUTH_CTX', 'USER_ID', ?); END;", userId);
    }

    public List<Map<String, Object>> listActive() {
        return jdbc.queryForList(
            "SELECT USER_ID, ROLE_MASK, LDAP_DN FROM BH_USER_ROLE "
          + "WHERE ACTIVE_FLAG = 'Y' ORDER BY USER_ID");
    }

    /**
     * Grant or revoke by replacing the whole mask.
     *
     * <p>There is no history. The previous mask is overwritten, so there is no record of who
     * could do what on the day a given determination was made — which is precisely the question
     * an audit asks.</p>
     */
    public void setRoleMask(String userId, int roleMask) {
        jdbc.update("UPDATE BH_USER_ROLE SET ROLE_MASK = ? WHERE USER_ID = ?", roleMask, userId);
    }
}
