package com.bridgeway.bhauth.dao;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

/**
 * The outbound "queue". A table and a cron job.
 *
 * <p>{@link #enqueue} is the fifth write in {@code AuthCaseService.submitAndDecide()}, and it is
 * inside that method's transaction. That is not an accident of layering — it is the property
 * that makes this system correct: a queue row exists if and only if the authorization it
 * describes was committed. There is no window in which a notification goes out for a decision
 * that was rolled back, and none in which a committed decision is never notified.</p>
 *
 * <p>This is a transactional outbox, built in 2011 by people who would not have called it
 * that.</p>
 *
 * <h3>Where it falls down</h3>
 *
 * <p>{@link #claimBatch} sets STATE to LOCKED and commits, then {@code poll_queue.sh} does its
 * work and calls {@link #markDone}. If the script dies in between, the row stays LOCKED forever:
 * there is no lease, no timeout, and no reaper. A human clears them on Monday, using the runbook
 * in {@code ops/README} that describes a menu option removed in 2014.</p>
 *
 * <h3>The payload</h3>
 *
 * <p>{@code PAYLOAD} is {@code VARCHAR2(4000)} and it carries the clinical narrative, truncated
 * to fit. This queue is read by the notification job, which emails the requesting provider's
 * office. The narrative is 42 CFR Part 2 content when the provider is a Part 2 program, and
 * nothing between this row and that mailbox checks a consent.</p>
 */
@Repository
public class QueueDao {

    @Autowired private JdbcTemplate jdbc;

    public void enqueue(long authId, String eventType, String payload) {
        jdbc.update(
            "INSERT INTO BH_AUTH_QUEUE (QUEUE_ID, AUTH_ID, EVENT_TYPE, PAYLOAD, STATE, "
          + "                           ENQUEUED_TS) "
          + "VALUES (SEQ_BH_QUEUE_ID.NEXTVAL, ?, ?, ?, 'NEW', SYSDATE)",
            authId, eventType, payload);
    }

    /**
     * Claim up to {@code limit} rows for this worker.
     *
     * <p>{@code SELECT ... FOR UPDATE SKIP LOCKED} does the right thing across concurrent
     * pollers. Only one poller has ever run.</p>
     */
    public int claimBatch(String workerId, int limit) {
        return jdbc.update(
            "UPDATE BH_AUTH_QUEUE SET STATE = 'LOCKED', LOCKED_BY = ? "
          + "WHERE QUEUE_ID IN ("
          + "  SELECT QUEUE_ID FROM ("
          + "    SELECT QUEUE_ID FROM BH_AUTH_QUEUE WHERE STATE = 'NEW' "
          + "    ORDER BY ENQUEUED_TS"
          + "  ) WHERE ROWNUM <= ?)",
            workerId, limit);
    }

    public List<Map<String, Object>> readClaimed(String workerId) {
        return jdbc.queryForList(
            "SELECT QUEUE_ID, AUTH_ID, EVENT_TYPE, PAYLOAD FROM BH_AUTH_QUEUE "
          + "WHERE STATE = 'LOCKED' AND LOCKED_BY = ? ORDER BY ENQUEUED_TS",
            workerId);
    }

    public void markDone(long queueId) {
        jdbc.update(
            "UPDATE BH_AUTH_QUEUE SET STATE = 'DONE', PROCESSED_TS = SYSDATE WHERE QUEUE_ID = ?",
            queueId);
    }

    /**
     * Mark a row failed.
     *
     * <p>There is no retry count and no dead-letter destination. FAILED is where a row goes to
     * be forgotten; the only recovery is a human setting it back to NEW by hand.</p>
     */
    public void markFailed(long queueId) {
        jdbc.update(
            "UPDATE BH_AUTH_QUEUE SET STATE = 'FAILED', PROCESSED_TS = SYSDATE "
          + "WHERE QUEUE_ID = ?", queueId);
    }

    /** Rows LOCKED for more than an hour. Nothing calls this. It was written for a runbook. */
    public List<Long> findStuck() {
        return jdbc.queryForList(
            "SELECT QUEUE_ID FROM BH_AUTH_QUEUE "
          + "WHERE STATE = 'LOCKED' AND ENQUEUED_TS < SYSDATE - (1/24)",
            Long.class);
    }
}
