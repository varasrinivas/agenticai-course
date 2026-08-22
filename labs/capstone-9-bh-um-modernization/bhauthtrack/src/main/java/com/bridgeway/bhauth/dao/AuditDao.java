package com.bridgeway.bhauth.dao;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

/**
 * Reads BH_AUDIT_LOG. Nothing writes it from Java — {@code TRG_BH_AUTH_AUDIT} does that.
 *
 * <p>That division is worth noticing. The audit trail is produced by a database trigger, so it
 * captures every update to BH_AUTH regardless of which of the four call paths made it: the
 * controller, the batch importer, the SOAP endpoint, or a DBA at a SQL prompt. It is the only
 * mechanism in this system with that property.</p>
 *
 * <p>It is also why the audit trail cannot simply be lifted into a service. Move the writes into
 * application code and the coverage shrinks to the paths that were remembered.</p>
 *
 * <h3>What this DAO deliberately does not select</h3>
 *
 * <p>{@code OLD_NARRATIVE} and {@code NEW_NARRATIVE}. The trigger writes a full copy of the
 * clinical narrative on every update; the audit screen shows status transitions only, so the
 * column list below stops short of them. That is a convention in one query, not a control:
 * anything else with a database connection sees the whole table, including the Crystal reports
 * and the nightly extract.</p>
 *
 * <p><b>An audit table containing federally protected treatment content, with no consent scope
 * and no expiry, is one of the findings this system is here to produce.</b></p>
 */
@Repository
public class AuditDao {

    @Autowired private JdbcTemplate jdbc;

    /**
     * Status transitions for one authorization, oldest first. Narrative columns excluded.
     *
     * <p>The quoted lower-case aliases are not cosmetic. This returns a list of maps and the
     * JSP reads them as {@code ${e.actorUserId}}, which is a map lookup by exact key — Oracle's
     * default upper-casing would make every cell render blank. It is a JSP requirement leaking
     * into SQL, and there is nothing that would catch it breaking except looking at the page.</p>
     */
    public List<Map<String, Object>> findByAuth(long authId) {
        return jdbc.queryForList(
            "SELECT AUDIT_ID           AS \"auditId\", "
          + "       AUTH_ID            AS \"authId\", "
          + "       ACTION             AS \"action\", "
          + "       ACTOR_USER_ID      AS \"actorUserId\", "
          + "       ACTOR_ROLE_MASK    AS \"actorRoleMask\", "
          + "       OLD_STATUS         AS \"oldStatus\", "
          + "       NEW_STATUS         AS \"newStatus\", "
          + "       ACTION_TS          AS \"actionTs\" "
          + "FROM BH_AUDIT_LOG WHERE AUTH_ID = ? ORDER BY ACTION_TS, AUDIT_ID",
            authId);
    }

    /**
     * How many audit rows are attributed to the application account rather than to a person.
     *
     * <p>Written during the 2015 audit, run twice, and never put on a screen. The number was
     * uncomfortable and the finding was deferred.</p>
     */
    public int countUnattributed() {
        Integer n = jdbc.queryForObject(
            "SELECT COUNT(*) FROM BH_AUDIT_LOG WHERE ACTOR_USER_ID = USER", Integer.class);
        return n == null ? 0 : n;
    }

    /**
     * Rows whose narrative copy is non-empty.
     *
     * <p>Not called from anywhere. It exists because someone started to measure the problem in
     * 2016 and then left the company.</p>
     */
    public int countRowsHoldingNarrative() {
        Integer n = jdbc.queryForObject(
            "SELECT COUNT(*) FROM BH_AUDIT_LOG "
          + "WHERE (OLD_NARRATIVE IS NOT NULL AND DBMS_LOB.GETLENGTH(OLD_NARRATIVE) > 0) "
          + "   OR (NEW_NARRATIVE IS NOT NULL AND DBMS_LOB.GETLENGTH(NEW_NARRATIVE) > 0)",
            Integer.class);
        return n == null ? 0 : n;
    }
}
