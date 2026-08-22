-- Transactional outbox (Phase 2 / M14). Events are written here in the same DB transaction as the
-- case change; OutboxPublisher polls unpublished rows and sends them to Kafka, then stamps published_at.
-- This avoids the dual-write problem: the event exists iff the business transaction committed.
CREATE TABLE outbox_event (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    topic        VARCHAR(64)   NOT NULL,
    event_key    VARCHAR(64)   NOT NULL,
    payload      VARCHAR(4000) NOT NULL,
    created_at   TIMESTAMPTZ   NOT NULL,
    published_at TIMESTAMPTZ
);

-- Partial index so the poller's "unpublished, oldest first" scan stays cheap as the table grows.
CREATE INDEX idx_outbox_unpublished ON outbox_event (id) WHERE published_at IS NULL;
